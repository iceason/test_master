"""
Lightweight in-process cron scheduler for build plans.

When Celery Beat is not available, this module provides a background daemon
thread that wakes up every 30 seconds and calls `check_cron_builds()` to
trigger any build plans whose cron expressions match the current time.

Usage: call `start()` once during Django app startup (see apps.py).
"""
import logging
import threading
import time

logger = logging.getLogger(__name__)

_started = False
_lock = threading.Lock()


def _run_loop():
    """Background loop: call check_cron_builds every 30 seconds."""
    time.sleep(10)
    logger.info("Cron scheduler thread started (interval=30s)")

    while True:
        try:
            from .build_tasks import check_cron_builds
            check_cron_builds()
        except Exception:
            logger.exception("Error in cron scheduler loop")
        time.sleep(30)


def start():
    """Start the scheduler thread (idempotent, at most one thread)."""
    global _started
    with _lock:
        if _started:
            return
        _started = True

    t = threading.Thread(target=_run_loop, name="cron-scheduler", daemon=True)
    t.start()
    logger.info("Cron scheduler thread launched")
