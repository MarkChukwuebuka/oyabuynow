import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

app = Celery('core')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()


# app.conf.beat_schedule = {
#     'notify-due-loans-daily': {
#         'task': 'library.tasks.notify_due_loans',
#         'schedule': crontab(hour=1, minute=20),  # every day at 08:00
#     },
# }