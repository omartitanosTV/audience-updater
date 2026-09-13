# Celery is optional for the standalone learning setup because the local
# management-command scheduler works without Redis. When Celery is installed,
# expose the app so the future integrated deployment can autodiscover tasks.
try:
    from .celery import app as celery_app
except ModuleNotFoundError:
    celery_app = None


__all__ = ("celery_app",)
