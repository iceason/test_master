from __future__ import annotations

import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "TestCaseGenerator.settings")

# 延迟broker连接，避免启动时卡住
app = Celery("TestCaseGenerator", broker_connection_retry_on_startup=True)
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

