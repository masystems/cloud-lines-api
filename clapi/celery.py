from __future__ import absolute_import, unicode_literals
from celery import Celery
from django.conf import settings
import os
# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clapi.settings')

app = Celery('clapi')
app.conf.enable_utc = True
app.conf.update(timezone='Europe/London')
app.config_from_object(settings, namespace='CELERY')
app.autodiscover_tasks()

app.conf.beat_schedule = {

}
