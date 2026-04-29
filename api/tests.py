from unittest.mock import patch, Mock

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIRequestFactory

from . import build_tasks
from .models import BuildPlan, BuildExecution, DingTalkTemplate, ExecutorMachine
from .jenkins_client import build_pipeline_script
from .testing_views import (
    BuildTriggerView,
    BuildTriggerNoTokenView,
    build_default_report_command,
)


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

    def test_notification_context_allure_report_absolute_url(self):
        from django.test.utils import override_settings

        execution = self._create_execution()
        execution.report_type = 'allure'
        execution.report_url = '/media/reports/9/index.html'
        execution.save(update_fields=['report_type', 'report_url'])
        with override_settings(
            REPORT_PUBLIC_BASE_URL='https://tm.example.com',
            BACKEND_BASE_URL='',
        ):
            ctx = build_tasks._build_notification_context(execution)
        self.assertEqual(
            ctx['allure_report_url'],
            'https://tm.example.com/media/reports/9/index.html',
        )
        self.assertIn('Allure', ctx['allure_report_block'])
        self.assertIn('https://tm.example.com/media/reports/9/index.html', ctx['allure_report_block'])

    def test_notification_uses_frontend_base_for_allure_url(self):
        from django.test.utils import override_settings

        execution = self._create_execution()
        execution.report_type = 'allure'
        execution.report_url = '/media/reports/718/index.html'
        execution.save(update_fields=['report_type', 'report_url'])
        with override_settings(
            REPORT_PUBLIC_BASE_URL='',
            FRONTEND_BASE_URL='http://192.168.96.227:3334',
            BACKEND_BASE_URL='',
        ):
            ctx = build_tasks._build_notification_context(execution)
        self.assertEqual(
            ctx['allure_report_url'],
            'http://192.168.96.227:3334/media/reports/718/index.html',
        )

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

    def test_schedule_queues_when_report_upload_expected(self):
        """When report_enabled and Allure not yet uploaded, defer instead of immediate notify."""
        execution = self._create_execution()
        plan = execution.build_plan
        plan.report_enabled = True
        plan.save(update_fields=['report_enabled'])
        plan.notification_config = {
            'dingtalk': {'enabled': True, 'group_ids': [1], 'template_id': None},
        }
        plan.save(update_fields=['notification_config'])

        with patch('api.build_tasks.send_notification_when_report_ready.delay') as delayed:
            with patch('api.build_tasks._send_dingtalk_groups') as mocked_send:
                build_tasks.schedule_build_notifications(execution.id)
            delayed.assert_called_once_with(execution.id)
            mocked_send.assert_not_called()


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


class AllurePipelineIntegrationTests(TestCase):
    def test_build_pipeline_script_uses_parameterized_execution_id(self):
        script = build_pipeline_script(
            steps=[{'name': 'Run Tests', 'script': 'echo ok', 'timeout': 60, 'on_failure': 'stop'}],
            report_enabled=True,
            report_results_dir='results-custom',
            report_command='echo report',
            build_plan_id=99,
        )
        self.assertIn("parameters {", script)
        self.assertIn("string(name: 'EXECUTION_ID'", script)
        self.assertIn('EXECUTION_ID = "${params.EXECUTION_ID}"', script)
        self.assertIn("BUILD_PLAN_ID = '99'", script)
        self.assertIn("BACKEND_BASE_URL = '", script)
        self.assertIn("post {", script)
        self.assertIn("always {", script)
        self.assertIn('// [testmaster:auto-report-upload:start]', script)

    def test_build_jenkins_params_includes_execution_id(self):
        plan = BuildPlan.objects.create(name='params-plan')
        execution = BuildExecution.objects.create(build_plan=plan, status='pending')
        params = build_tasks._build_jenkins_params(plan, execution)
        self.assertEqual(params['EXECUTION_ID'], str(execution.id))

    @patch('api.build_tasks.create_jenkins_client')
    @patch('api.build_tasks.sync_jenkins_job')
    @patch('api.build_tasks._poll_build')
    @patch('api.build_tasks._fetch_report')
    @patch('api.build_tasks._send_notification')
    @patch('api.build_tasks._send_external_callback')
    def test_run_build_sync_retries_after_parameterized_400(
        self,
        mocked_callback,
        mocked_notify,
        mocked_fetch_report,
        mocked_poll,
        mocked_sync_job,
        mocked_create_client,
    ):
        plan = BuildPlan.objects.create(name='retry-plan', jenkins_job_name='retry-plan-job')
        execution = BuildExecution.objects.create(build_plan=plan, status='pending')

        first_client = Mock()
        first_client.trigger_build.side_effect = Exception("400 Client Error: buildWithParameters")
        second_client = Mock()
        second_client.trigger_build.return_value = 123
        second_client.get_build_number_from_queue.return_value = 8
        second_client.get_build_console_output.return_value = 'ok'

        mocked_create_client.side_effect = [first_client, second_client]

        build_tasks.run_build_sync(execution.id)

        mocked_sync_job.assert_called_once_with(plan)
        second_client.trigger_build.assert_called_once()
        execution.refresh_from_db()
        self.assertEqual(execution.jenkins_build_number, 8)

    def test_default_report_command_matches_linux(self):
        cmd = build_default_report_command('linux', 'custom-results')
        self.assertIn('if [ -d "$REPORT_DIR" ]', cmd)
        self.assertIn('zip -r report.zip "$REPORT_DIR"', cmd)
        self.assertIn('curl -f -X POST -F "report=@report.zip"', cmd)
        self.assertIn('$BACKEND_BASE_URL/api/upload-report/$EXECUTION_ID/', cmd)
        self.assertIn('REPORT_DIR="custom-results"', cmd)
        self.assertIn('skip report upload', cmd)

    def test_default_report_command_matches_windows(self):
        cmd = build_default_report_command('windows', 'custom-results')
        self.assertIn('if exist "%REPORT_DIR%"', cmd)
        self.assertIn("Compress-Archive", cmd)
        self.assertIn('curl.exe -f -X POST -F "report=@report.zip"', cmd)
        self.assertIn('%BACKEND_BASE_URL%/api/upload-report/%EXECUTION_ID%/', cmd)
        self.assertIn('set "REPORT_DIR=custom-results"', cmd)
        self.assertIn('skip report upload', cmd)

    def test_pipeline_job_xml_contains_execution_id_parameter_definition(self):
        from .jenkins_client import build_pipeline_job_xml
        xml = build_pipeline_job_xml(
            steps=[],
            os_type='windows',
            description='demo',
        )
        self.assertIn('<hudson.model.ParametersDefinitionProperty>', xml)
        self.assertIn('<name>EXECUTION_ID</name>', xml)

    def test_finalize_injects_post_into_custom_jenkinsfile(self):
        from .jenkins_client import finalize_jenkinsfile_for_plan
        custom = (
            "pipeline {\n"
            "    agent any\n"
            "    stages {\n"
            "        stage('x') { steps { sh 'echo 1' } }\n"
            "    }\n"
            "}\n"
        )
        out = finalize_jenkinsfile_for_plan(
            custom,
            report_enabled=True,
            report_command='curl -f -X POST -F "report=@r.zip" "$U/"',
            os_type='linux',
        )
        self.assertIn('// [testmaster:auto-report-upload:start]', out)
        self.assertIn('post {', out)
        self.assertIn('always {', out)

    def test_finalize_idempotent(self):
        from .jenkins_client import finalize_jenkinsfile_for_plan
        custom = (
            "pipeline {\n"
            "    agent any\n"
            "    stages {\n"
            "        stage('x') { steps { sh 'echo 1' } }\n"
            "    }\n"
            "}\n"
        )
        once = finalize_jenkinsfile_for_plan(
            custom,
            report_enabled=True,
            report_command='echo up',
            os_type='linux',
        )
        twice = finalize_jenkinsfile_for_plan(
            once,
            report_enabled=True,
            report_command='echo up',
            os_type='linux',
        )
        self.assertEqual(once.count('// [testmaster:auto-report-upload:start]'), 1)
        self.assertEqual(twice.count('// [testmaster:auto-report-upload:start]'), 1)
