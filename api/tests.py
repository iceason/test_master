from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from . import build_tasks
from .models import BuildPlan, BuildExecution, DingTalkTemplate


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
