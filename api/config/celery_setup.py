from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# Set the environment variable for Django configurations
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'api.config.settings.base')

app = Celery('api')

# Use the Django configuration for Celery
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load tasks from all registered modules in Django
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')