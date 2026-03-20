import os
import sys
from django.apps import AppConfig


class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'

    def ready(self):
        argv_str = ' '.join(sys.argv)
        server_keywords = ['runserver', 'gunicorn', 'uvicorn', 'daphne']
        is_server = any(kw in argv_str for kw in server_keywords)
        if not is_server:
            return

        if 'runserver' in argv_str and os.environ.get('RUN_MAIN') != 'true':
            return

        from . import cron_scheduler
        cron_scheduler.start()
