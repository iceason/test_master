from unittest.mock import patch, Mock

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIRequestFactory

from . import build_tasks
from .models import BuildPlan, BuildExecution, DingTalkTemplate, ExecutorMachine
from .testing_views import BuildTriggerView, BuildTriggerNoTokenView


class DingTalkNotificationTests(TestCase):
    def _create_execution(self):
        plan = BuildPlan.objects.create(
            name='demo-plan',
            notification_config={},
        )
        return BuildExecution.objects.create(
            build_plan=plan,
            trigger_type='manual',
            triggered_by='tester',
            status='success',
        )

    @patch('api.build_tasks.time.time', return_value=1700000000)
    def test_build_dingtalk_signed_url(self, _mocked_time):
        signed = build_tasks._build_dingtalk_signed_url(
            'https://oapi.dingtalk.com/robot/send?access_token=abc',
            'test-secret'
        )
        self.assertIn('timestamp=1700000000000', signed)
        self.assertIn('&sign=', signed)

    def test_render_dingtalk_template_with_selected_template(self):
        execution = self._create_execution()
        tpl = DingTalkTemplate.objects.create(
            name='tpl-1',
            title_template='[{{status_upper}}] {{plan_name}}',
            body_template='计划: {{plan_name}} 状态: {{status_upper}}',
            is_active=True,
        )
        title, body = build_tasks._render_dingtalk_template(execution, template_id=tpl.id)
        self.assertIn('[SUCCESS] demo-plan', title)
        self.assertIn('计划: demo-plan', body)

    def test_send_notification_dispatches_dingtalk_path(self):
        execution = self._create_execution()
        execution.build_plan.notification_config = {
            'dingtalk': {
                'enabled': True,
                'group_ids': [1],
                'template_id': None,
            }
        }
        execution.build_plan.save(update_fields=['notification_config'])

        with patch('api.build_tasks._send_dingtalk_groups') as mocked_send:
            build_tasks._send_notification(execution)
            mocked_send.assert_called_once()


class RepeatBuildDispatchTests(TestCase):
    def test_dispatch_repeated_builds_continue_all_creates_n_executions(self):
        plan = BuildPlan.objects.create(
            name='repeat-plan',
            repeat_run_times=3,
            repeat_failure_policy='continue_all',
        )
        with patch('api.build_tasks._dispatch_build') as mocked_dispatch:
            result = build_tasks.dispatch_repeated_builds(
                plan=plan,
                repeat_run_times=3,
                failure_policy='continue_all',
                triggered_by='tester',
                trigger_type='manual',
            )
            self.assertEqual(result['mode'], 'parallel_dispatch')
            self.assertEqual(len(result['execution_ids']), 3)
            self.assertEqual(BuildExecution.objects.filter(build_plan=plan).count(), 3)
            self.assertEqual(mocked_dispatch.call_count, 3)

    def test_run_repeated_builds_sync_stop_on_first_fail(self):
        plan = BuildPlan.objects.create(
            name='repeat-stop-plan',
            repeat_run_times=3,
            repeat_failure_policy='stop_on_first_fail',
        )

        def fake_run_build_sync(execution_id):
            execution = BuildExecution.objects.get(id=execution_id)
            execution.status = 'failed'
            execution.finished_at = timezone.now()
            execution.save(update_fields=['status', 'finished_at'])

        with patch('api.build_tasks.run_build_sync', side_effect=fake_run_build_sync):
            result = build_tasks.run_repeated_builds_sync(
                plan_id=plan.id,
                triggered_by='tester',
                trigger_type='manual',
            )
            self.assertTrue(result['stopped_early'])
            self.assertEqual(len(result['execution_ids']), 1)
            self.assertEqual(BuildExecution.objects.filter(build_plan=plan).count(), 1)


class ExternalTriggerAndCallbackTests(TestCase):
    def test_build_trigger_supports_get_without_auth(self):
        machine = ExecutorMachine.objects.create(
            name='m1',
            hostname='localhost',
            ip_address='127.0.0.1',
            jenkins_url='http://jenkins.local',
        )
        plan = BuildPlan.objects.create(
            name='ext-trigger-plan',
            trigger_token='tok_get_123',
            status='active',
            executor_machine=machine,
            jenkins_job_name='demo-job',
        )
        factory = APIRequestFactory()
        request = factory.get(
            f'/api/build-trigger/{plan.trigger_token}/',
            {'triggered_by': 'tester_get', 'callback_url': 'https://example.com/callback'}
        )
        view = BuildTriggerView.as_view()

        with patch('api.build_tasks._dispatch_build') as mocked_dispatch:
            response = view(request, trigger_token=plan.trigger_token)
            self.assertEqual(response.status_code, 202)
            execution = BuildExecution.objects.get(id=response.data['execution_id'])
            self.assertEqual(execution.triggered_by, 'tester_get')
            self.assertEqual(execution.callback_url, 'https://example.com/callback')
            mocked_dispatch.assert_called_once()

    def test_send_external_callback_marks_notified(self):
        plan = BuildPlan.objects.create(name='callback-plan', notification_config={})
        execution = BuildExecution.objects.create(
            build_plan=plan,
            trigger_type='api',
            triggered_by='ext',
            callback_url='https://example.com/hook',
            status='success',
            started_at=timezone.now(),
            finished_at=timezone.now(),
        )

        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.text = 'ok'
        with patch('requests.post', return_value=mock_resp) as mocked_post:
            build_tasks._send_external_callback(execution)
            execution.refresh_from_db()
            self.assertTrue(execution.callback_notified)
            self.assertIn('HTTP 200', execution.callback_last_response)
            mocked_post.assert_called_once()

    def test_build_trigger_no_token_supports_get_by_plan_id(self):
        machine = ExecutorMachine.objects.create(
            name='m2',
            hostname='localhost',
            ip_address='127.0.0.2',
            jenkins_url='http://jenkins.local',
        )
        plan = BuildPlan.objects.create(
            name='ext-trigger-no-token-plan',
            status='active',
            executor_machine=machine,
            jenkins_job_name='demo-job-2',
        )
        factory = APIRequestFactory()
        request = factory.get(
            '/api/build-trigger/',
            {'plan_id': str(plan.id), 'triggered_by': 'tester_no_token_get'}
        )
        view = BuildTriggerNoTokenView.as_view()

        with patch('api.build_tasks._dispatch_build') as mocked_dispatch:
            response = view(request)
            self.assertEqual(response.status_code, 202)
            execution = BuildExecution.objects.get(id=response.data['execution_id'])
            self.assertEqual(execution.triggered_by, 'tester_no_token_get')
            mocked_dispatch.assert_called_once()
