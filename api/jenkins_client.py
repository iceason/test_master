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
        self.server = jenkins.Jenkins(
            self.server_url,
            username=username,
            password=token,
        )

    # ------------------------------------------------------------------
    # Connection test
    # ------------------------------------------------------------------

    def ping(self):
        """Return Jenkins version string or raise on failure."""
        return self.server.get_version()

    # ------------------------------------------------------------------
    # Build operations
    # ------------------------------------------------------------------

    def trigger_build(self, job_name, parameters=None):
        """
        Trigger a Jenkins job and return the queue item number.
        Returns queue_id (int).
        """
        queue_id = self.server.build_job(job_name, parameters=parameters or {})
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
    Factory: create a JenkinsClient from a BuildPlan instance.
    Returns None if Jenkins is not configured.
    """
    if not build_plan.jenkins_server_url or not build_plan.jenkins_job_name:
        return None
    creds = build_plan.jenkins_credentials or {}
    return JenkinsClient(
        server_url=build_plan.jenkins_server_url,
        username=creds.get('username'),
        token=creds.get('token'),
    )
