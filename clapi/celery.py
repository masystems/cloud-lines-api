from __future__ import absolute_import, unicode_literals

import os
from celery import shared_task
from celery import Celery
from celery.schedules import crontab
from django.conf import settings

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clapi.settings')

app = Celery('clapi')
app.conf.enable_utc = True
app.conf.update(timezone='Europe/London')
app.config_from_object(settings, namespace='CELERY')
app.autodiscover_tasks()

app.conf.beat_schedule = {

}

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
