from __future__ import absolute_import, unicode_literals

# This code allows Celery to initialize with Django
from .celery_setup import app as celery_app

__all__ = ('celery_app',)
