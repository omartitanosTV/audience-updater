import os

from celery import Celery


# Tell Celery which Django settings module belongs to this project
os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "audience_updater_web.settings",
)

# Reuse the same Celery pattern as the larger Audience Tool project
app = Celery("audience_updater")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
