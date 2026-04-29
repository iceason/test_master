"""
Jenkins API integration helper.

Uses python-jenkins library. Install: pip install python-jenkins
"""
import logging
import time

logger = logging.getLogger(__name__)


class JenkinsClient:
    """Wrapper around python-jenkins for build plan integration."""

    def __init__(self, server_url, username=None, token=None):
        try:
            import jenkins
        except ImportError:
            raise ImportError(
                "python-jenkins is required. Install with: pip install python-jenkins"
            )
        self.server_url = server_url.rstrip('/')
        self._username = username
        self._token = token
        self.server = jenkins.Jenkins(
            self.server_url,
            username=username,
            password=token,
        )
        if username and token:
            import requests as _req
            auth = _req.auth.HTTPBasicAuth(username, token)
            self.server._session.auth = auth
            self.server.auth = auth
            self.server._auth_resolved = True
            self._prefetch_crumb(auth)

    def _prefetch_crumb(self, auth):
        """Pre-fetch CSRF crumb so python-jenkins never makes its own unauthenticated request."""
        import requests as _req
        try:
            resp = _req.get(
                f"{self.server_url}/crumbIssuer/api/json",
                auth=auth, timeout=10,
            )
            if resp.status_code == 200:
                self.server.crumb = resp.json()
            else:
                self.server.crumb = False
        except Exception:
            self.server.crumb = False

    # ------------------------------------------------------------------
    # Connection test
    # ------------------------------------------------------------------

    def ping(self):
        """Return Jenkins version string or raise on failure."""
        import requests as _requests
        auth = (self._username, self._token) if self._username else None
        resp = _requests.get(
            self.server_url, auth=auth, timeout=10, allow_redirects=False,
        )
        resp.raise_for_status()
        return resp.headers.get('X-Jenkins', 'unknown')

    # ------------------------------------------------------------------
    # Build operations
    # ------------------------------------------------------------------

    def trigger_build(self, job_name, parameters=None):
        """
        Trigger a Jenkins job and return the queue item number.
        Returns queue_id (int).
        """
        params = parameters if parameters else None
        queue_id = self.server.build_job(job_name, parameters=params)
        logger.info("Triggered Jenkins job %s, queue_id=%s", job_name, queue_id)
        return queue_id

    def get_build_number_from_queue(self, queue_id, timeout=120, poll_interval=3):
        """
        Poll the queue until the build starts and return build_number.
        """
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                item = self.server.get_queue_item(queue_id)
                executable = item.get('executable')
                if executable:
                    return executable['number']
            except Exception:
                pass
            time.sleep(poll_interval)
        raise TimeoutError(
            f"Build did not start within {timeout}s (queue_id={queue_id})"
        )

    def get_build_info(self, job_name, build_number):
        """Return build info dict from Jenkins."""
        return self.server.get_build_info(job_name, build_number)

    def is_build_running(self, job_name, build_number):
        """Check if the build is still running."""
        info = self.get_build_info(job_name, build_number)
        return info.get('building', False)

    def get_build_result(self, job_name, build_number):
        """Return build result string: SUCCESS / FAILURE / ABORTED / None (still running)."""
        info = self.get_build_info(job_name, build_number)
        return info.get('result')

    # ------------------------------------------------------------------
    # Logs
    # ------------------------------------------------------------------

    def get_build_console_output(self, job_name, build_number):
        """Return the full console output (log text) of a build."""
        return self.server.get_build_console_output(job_name, build_number)

    # ------------------------------------------------------------------
    # Reports / Artifacts
    # ------------------------------------------------------------------

    def get_build_test_report(self, job_name, build_number):
        """
        Return the JUnit test report if available.
        Calls /testReport/api/json on the build.
        Returns dict or None.
        """
        try:
            import requests
            url = (
                f"{self.server_url}/job/{job_name}/{build_number}"
                f"/testReport/api/json"
            )
            auth = None
            if self.server.auth:
                auth = self.server.auth
            resp = requests.get(url, auth=auth, timeout=30)
            if resp.status_code == 200:
                return resp.json()
        except Exception as e:
            logger.warning("Failed to fetch test report: %s", e)
        return None

    def stop_build(self, job_name, build_number):
        """Abort a running build."""
        self.server.stop_build(job_name, build_number)
        logger.info("Stopped Jenkins build %s #%s", job_name, build_number)

    # ------------------------------------------------------------------
    # Nodes (agents)
    # ------------------------------------------------------------------

    def get_nodes(self):
        """Return list of Jenkins nodes (agents)."""
        return self.server.get_nodes()

    def get_node_info(self, node_name):
        """Return info dict for a specific node."""
        return self.server.get_node_info(node_name)


def create_jenkins_client(build_plan):
    """
    Factory: create a JenkinsClient from a BuildPlan's executor_machine.
    Returns None if Jenkins is not configured on the machine.
    """
    machine = build_plan.executor_machine
    if not machine or not machine.jenkins_url:
        return None
    return JenkinsClient(
        server_url=machine.jenkins_url,
        username=machine.jenkins_username or None,
        token=machine.jenkins_token or None,
    )


# ---------------------------------------------------------------------------
# Pipeline script & config.xml generation
# ---------------------------------------------------------------------------

import xml.sax.saxutils as saxutils
import re

REPORT_UPLOAD_MARK_START = '// [testmaster:auto-report-upload:start]'
REPORT_UPLOAD_MARK_END = '// [testmaster:auto-report-upload:end]'
_REPORT_UPLOAD_BLOCK_RE = re.compile(
    r'^[ \t]*// \[testmaster:auto-report-upload:start\][\s\S]*?^[ \t]*// \[testmaster:auto-report-upload:end\]\s*\n?',
    re.MULTILINE,
)


def _resolve_backend_base_url():
    try:
        from django.conf import settings
        url = getattr(settings, 'BACKEND_BASE_URL', '') or ''
        if url.strip():
            return url.strip().rstrip('/')
    except Exception:
        pass
    return 'http://127.0.0.1:8000'


def _find_matching_brace_naive(text, open_idx):
    """Return index of `}` matching `{` at open_idx, or None. Ignores strings (best-effort)."""
    if open_idx >= len(text) or text[open_idx] != '{':
        return None
    depth = 0
    i = open_idx
    n = len(text)
    while i < n:
        c = text[i]
        if c == "'":
            i += 1
            while i < n:
                if text[i] == '\\':
                    i += 2
                    continue
                if text[i] == "'":
                    i += 1
                    break
                i += 1
            continue
        if i <= n - 3 and text[i:i + 3] == "'''":
            i += 3
            while i < n - 2:
                if text[i:i + 3] == "'''":
                    i += 3
                    break
                i += 1
            continue
        if c == '{':
            depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return None


def strip_report_upload_markers(text):
    """Remove a previously injected TestMaster report upload block."""
    if not text:
        return ''
    return _REPORT_UPLOAD_BLOCK_RE.sub('', text)


def _build_report_upload_marked_inner(report_command, os_type='linux'):
    """Marked catchError + sh/bat body (inside post / always)."""
    inner_sh = _format_sh(report_command.strip(), os_type)
    return (
        f"            {REPORT_UPLOAD_MARK_START}\n"
        "            catchError(buildResult: 'SUCCESS', stageResult: 'FAILURE') {\n"
        f"{_indent(inner_sh, 16)}\n"
        "            }\n"
        f"            {REPORT_UPLOAD_MARK_END}"
    )


def finalize_jenkinsfile_for_plan(jenkinsfile_text, report_enabled, report_command, os_type='linux'):
    """
    Remove any prior auto block, then inject report upload into declarative `post { always { ... } }`
    when report_enabled and report_command are set. Idempotent for sync/save.
    """
    text = strip_report_upload_markers(jenkinsfile_text or '')
    cmd = (report_command or '').strip()
    if not report_enabled or not cmd:
        return text.rstrip() + '\n' if text.strip() else ''

    marked_inner = _build_report_upload_marked_inner(cmd, os_type)

    m = re.search(r'\bpipeline\s*\{', text)
    if not m:
        return text.rstrip() + '\n'

    pipeline_brace_open = m.end() - 1
    pipeline_brace_close = _find_matching_brace_naive(text, pipeline_brace_open)
    if pipeline_brace_close is None:
        return text.rstrip() + '\n'

    inner = text[pipeline_brace_open + 1:pipeline_brace_close]

    post_m = re.search(r'\bpost\s*\{', inner)
    if not post_m:
        abs_post_insert = pipeline_brace_close
        chunk = (
            "\n    post {\n"
            "        always {\n"
            f"{marked_inner}\n"
            "        }\n"
            "    }\n"
        )
        return text[:abs_post_insert] + chunk + text[abs_post_insert:]

    post_open_rel = post_m.end() - 1
    post_open_abs = pipeline_brace_open + 1 + post_open_rel
    post_close_abs = _find_matching_brace_naive(text, post_open_abs)
    if post_close_abs is None:
        return text.rstrip() + '\n'

    post_inner = text[post_open_abs + 1:post_close_abs]
    always_m = re.search(r'\balways\s*\{', post_inner)
    if always_m:
        always_open_rel = always_m.end() - 1
        always_open_abs = post_open_abs + 1 + always_open_rel
        insert_after = always_open_abs + 1
        chunk = '\n' + marked_inner
        return text[:insert_after] + chunk + text[insert_after:]

    insert_after = post_open_abs + 1
    chunk = (
        "\n        always {\n"
        f"{marked_inner}\n"
        "        }\n"
    )
    return text[:insert_after] + chunk + text[insert_after:]


def _escape_groovy(text):
    """Escape for Groovy single-quoted string."""
    return text.replace('\\', '\\\\').replace("'", "\\'")


def _escape_groovy_triple(text):
    """Escape for Groovy triple-single-quoted string context."""
    result = []
    consecutive_quotes = 0
    for ch in text:
        if ch == '\\':
            result.append('\\\\')
            consecutive_quotes = 0
        elif ch == "'":
            consecutive_quotes += 1
            if consecutive_quotes == 3:
                result.append("\\'")
                consecutive_quotes = 0
            else:
                result.append("'")
        else:
            consecutive_quotes = 0
            result.append(ch)
    if consecutive_quotes > 0:
        for i in range(len(result) - 1, -1, -1):
            if result[i] == "'":
                result[i] = "\\'"
                break
    return ''.join(result)


def _indent(text, n):
    """Indent each non-empty line by *n* spaces."""
    prefix = ' ' * n
    return '\n'.join(
        (prefix + line) if line.strip() else line
        for line in text.split('\n')
    )


def _format_sh(script, os_type='linux'):
    """Format a shell command for Jenkinsfile."""
    cmd = 'bat' if os_type == 'windows' else 'sh'
    lines = script.split('\n')
    if len(lines) == 1 and "'" not in script:
        return f"{cmd} '{_escape_groovy(script)}'"
    escaped = _escape_groovy_triple(script)
    if '\n' not in escaped:
        return f"{cmd} '''{escaped}'''"
    return f"{cmd} '''\n{_indent(escaped, 4)}\n'''"


def _build_stage_block(step, os_type='linux'):
    """Build a single stage block for a pipeline step."""
    name = step.get('name', 'Unnamed')
    script = step.get('script', 'echo "no script"')
    timeout_val = step.get('timeout', 120)
    on_failure = step.get('on_failure', 'stop')

    sh_cmd = _format_sh(script, os_type)
    body = f"timeout(time: {timeout_val}, unit: 'SECONDS') {{\n{_indent(sh_cmd, 4)}\n}}"

    if on_failure == 'retry':
        body = f"retry(2) {{\n{_indent(body, 4)}\n}}"
    elif on_failure == 'continue':
        body = f"catchError(buildResult: 'SUCCESS', stageResult: 'FAILURE') {{\n{_indent(body, 4)}\n}}"

    return (
        f"        stage('{_escape_groovy(name)}') {{\n"
        f"            steps {{\n"
        f"{_indent(body, 16)}\n"
        f"            }}\n"
        f"        }}"
    )


def build_pipeline_script(
    steps, os_type='linux', node_label=None,
    git_repo_url='', git_branch='main', workspace_cleanup=True,
    report_enabled=False, report_results_dir='allure-results', report_command='',
    webhook_url='', build_plan_id=None,
    environment_variables=None,
    git_credential_id='',
):
    """
    Generate a Declarative Pipeline (Jenkinsfile) script string.
    Used by both the config.xml generator and the preview API.
    """
    if node_label:
        agent_block = f"    agent {{ label '{_escape_groovy(node_label)}' }}"
    else:
        agent_block = "    agent any"

    env_values = {}
    if environment_variables:
        for ev in environment_variables:
            key = re.sub(r'[^A-Za-z0-9_]', '_', ev.get('key', '').strip())
            value = ev.get('value', '')
            if not key:
                continue
            env_values[key] = str(value)
    env_values.setdefault('BACKEND_BASE_URL', _resolve_backend_base_url())
    if build_plan_id is not None:
        env_values.setdefault('BUILD_PLAN_ID', str(build_plan_id))
    env_values.setdefault('EXECUTION_ID', '__PARAM_EXECUTION_ID__')

    env_block = ""
    if env_values:
        env_lines = []
        for key, value in env_values.items():
            if value == '__PARAM_EXECUTION_ID__':
                env_lines.append(f'        {key} = "${{params.EXECUTION_ID}}"')
            else:
                env_lines.append(f"        {key} = '{_escape_groovy(value)}'")
        env_block = "    environment {\n" + "\n".join(env_lines) + "\n    }"

    parameters_block = (
        "    parameters {\n"
        "        string(name: 'EXECUTION_ID', defaultValue: '', description: 'BuildExecution ID from TestMaster')\n"
        "    }"
    )

    stage_blocks = []

    if git_repo_url:
        body_lines = []
        if workspace_cleanup:
            body_lines.append("                    cleanWs()")
        git_args = [
            f"url: '{_escape_groovy(git_repo_url)}'",
            f"branch: '{_escape_groovy(git_branch)}'",
        ]
        if git_credential_id:
            git_args.append(f"credentialsId: '{_escape_groovy(git_credential_id)}'")
        body_lines.append("                    git(")
        for i, arg in enumerate(git_args):
            comma = "," if i < len(git_args) - 1 else ""
            body_lines.append(f"                        {arg}{comma}")
        body_lines.append("                    )")
        stage_blocks.append(
            f"        stage('Git Checkout') {{\n"
            f"            steps {{\n"
            + "\n".join(body_lines) + "\n"
            f"            }}\n"
            f"        }}"
        )

    if not steps:
        cmd = 'bat' if os_type == 'windows' else 'sh'
        stage_blocks.append(
            f"        stage('Default') {{\n"
            f"            steps {{\n"
            f"                {cmd} 'echo \"No build steps configured.\"'\n"
            f"            }}\n"
            f"        }}"
        )
    else:
        for step in steps:
            stage_blocks.append(_build_stage_block(step, os_type))

    report_post_lines = []
    if report_enabled and report_command:
        marked_inner = _build_report_upload_marked_inner(report_command.strip(), os_type)
        report_post_lines = [
            '    post {',
            '        always {',
            marked_inner,
            '        }',
            '    }',
        ]

    parts = ['pipeline {']
    parts.append(agent_block)
    parts.append('')
    parts.append(parameters_block)
    if env_block:
        parts.append('')
        parts.append(env_block)
    parts.append('')
    parts.append('    stages {')
    for i, sb in enumerate(stage_blocks):
        parts.append(sb)
        if i < len(stage_blocks) - 1:
            parts.append('')
    parts.append('    }')
    if report_post_lines:
        parts.append('')
        parts.extend(report_post_lines)
    parts.append('}')
    return '\n'.join(parts) + '\n'


def build_pipeline_job_xml(
    steps, os_type='linux', node_label=None, description='',
    git_repo_url='', git_branch='main', workspace_cleanup=True,
    report_enabled=False, report_results_dir='allure-results', report_command='',
    webhook_url='', build_plan_id=None,
    environment_variables=None,
    raw_jenkinsfile='',
    git_credential_id='',
):
    """
    Generate a Jenkins Pipeline job config.xml (<flow-definition>).
    If raw_jenkinsfile is provided, use it directly instead of generating.
    """
    escaped_desc = saxutils.escape(description)
    if raw_jenkinsfile:
        pipeline_script = finalize_jenkinsfile_for_plan(
            raw_jenkinsfile,
            report_enabled=report_enabled,
            report_command=report_command or '',
            os_type=os_type,
        )
    else:
        pipeline_script = build_pipeline_script(
            steps=steps, os_type=os_type, node_label=node_label,
            git_repo_url=git_repo_url, git_branch=git_branch,
            workspace_cleanup=workspace_cleanup,
            report_enabled=report_enabled, report_results_dir=report_results_dir, report_command=report_command,
            webhook_url=webhook_url, build_plan_id=build_plan_id,
            environment_variables=environment_variables,
            git_credential_id=git_credential_id,
        )
    escaped_script = saxutils.escape(pipeline_script)
    param_props_xml = (
        '  <properties>\n'
        '    <hudson.model.ParametersDefinitionProperty>\n'
        '      <parameterDefinitions>\n'
        '        <hudson.model.StringParameterDefinition>\n'
        '          <name>EXECUTION_ID</name>\n'
        '          <description>BuildExecution ID from TestMaster</description>\n'
        '          <defaultValue></defaultValue>\n'
        '          <trim>false</trim>\n'
        '        </hudson.model.StringParameterDefinition>\n'
        '      </parameterDefinitions>\n'
        '    </hudson.model.ParametersDefinitionProperty>\n'
        '  </properties>\n'
    )

    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<flow-definition plugin="workflow-job">\n'
        f'  <description>{escaped_desc}</description>\n'
        '  <keepDependencies>false</keepDependencies>\n'
        f'{param_props_xml}'
        '  <definition class="org.jenkinsci.plugins.workflow.cps.CpsFlowDefinition" plugin="workflow-cps">\n'
        f'    <script>{escaped_script}</script>\n'
        '    <sandbox>true</sandbox>\n'
        '  </definition>\n'
        '  <triggers/>\n'
        '  <disabled>false</disabled>\n'
        '</flow-definition>'
    )


# ---------------------------------------------------------------------------
# Sync helpers
# ---------------------------------------------------------------------------

def _diagnose_jenkins_connection(url, username=None, token=None):
    """Try a raw HTTP request to diagnose connection issues."""
    try:
        import requests
        auth = (username, token) if username else None
        resp = requests.get(url, auth=auth, timeout=10, allow_redirects=False)
        if resp.status_code == 401:
            return f"Jenkins 认证失败 (HTTP 401)。请检查用户名和 Token 是否正确。"
        if resp.status_code == 403:
            return f"Jenkins 访问被拒绝 (HTTP 403)。请确认：1) 使用 API Token 而非密码；2) 用户具有足够权限。可在 Jenkins → 用户 → 设置 → API Token 中生成。"
        if resp.status_code >= 500:
            return f"Jenkins 服务器错误 (HTTP {resp.status_code})。请检查 Jenkins 服务状态、插件兼容性或 Script Security 设置。"
        return None
    except Exception as e:
        return f"无法连接到 Jenkins: {e}"


def sync_jenkins_job(plan):
    """
    Create or update the Jenkins Pipeline job for the given BuildPlan.
    Returns the config.xml string on success, raises on failure.
    """
    machine = plan.executor_machine
    if not machine or not machine.jenkins_url:
        raise ValueError("执行机未配置 Jenkins 信息")

    client = JenkinsClient(
        server_url=machine.jenkins_url,
        username=machine.jenkins_username or None,
        token=machine.jenkins_token or None,
    )
    job_name = plan.name
    steps = list(
        plan.steps.order_by('order').values('name', 'script', 'timeout', 'on_failure')
    )
    node_label = machine.jenkins_node_name or None
    os_type = machine.os_type or 'linux'
    description = (
        f"[Test Master] {plan.description}"
        if plan.description
        else "[Test Master] Auto-managed build plan"
    )

    raw_jenkinsfile = getattr(plan, 'jenkinsfile_text', '') or ''

    webhook_base_url = ''

    config_xml = build_pipeline_job_xml(
        steps=steps,
        os_type=os_type,
        node_label=node_label,
        description=description,
        git_repo_url=getattr(plan, 'git_repo_url', '') or '',
        git_branch=getattr(plan, 'git_branch', 'main') or 'main',
        workspace_cleanup=getattr(plan, 'workspace_cleanup', True),
        report_enabled=getattr(plan, 'report_enabled', False),
        report_results_dir=getattr(plan, 'report_results_dir', 'allure-results') or 'allure-results',
        report_command=getattr(plan, 'report_command', '') or '',
        webhook_url=webhook_base_url,
        build_plan_id=plan.id,
        environment_variables=getattr(plan, 'environment_variables', None) or [],
        raw_jenkinsfile=raw_jenkinsfile,
        git_credential_id=getattr(plan, 'git_credential_id', '') or '',
    )

    try:
        version = client.ping()
        logger.info("Jenkins connection OK, version: %s", version)
    except ConnectionError as e:
        diag = _diagnose_jenkins_connection(
            machine.jenkins_url, machine.jenkins_username, machine.jenkins_token
        )
        raise ConnectionError(diag or str(e))
    except Exception as e:
        diag = _diagnose_jenkins_connection(
            machine.jenkins_url, machine.jenkins_username, machine.jenkins_token
        )
        if diag:
            raise ConnectionError(diag)
        raise

    try:
        if client.server.job_exists(job_name):
            client.server.reconfig_job(job_name, config_xml)
            logger.info("Reconfigured Jenkins job: %s", job_name)
        else:
            client.server.create_job(job_name, config_xml)
            logger.info("Created Jenkins job: %s", job_name)
    except Exception as e:
        err_str = str(e)
        if '500' in err_str:
            raise RuntimeError(
                f"Jenkins 返回 500 错误。可能原因：\n"
                f"1. Pipeline 脚本被 Script Security 插件拦截\n"
                f"2. 缺少必要的 Jenkins 插件\n"
                f"3. Jenkins 内部错误\n"
                f"原始错误: {err_str}"
            )
        raise

    if not plan.jenkins_job_name:
        plan.jenkins_job_name = job_name
        plan.save(update_fields=['jenkins_job_name'])

    return config_xml
