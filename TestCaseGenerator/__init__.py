# Celery app - optional, only imported if Redis is available
try:
    from .celery import app as celery_app
    __all__ = ("celery_app",)
except Exception:
    # Celery not available or Redis not running
    celery_app = None
    __all__ = ()
