"""
Celery Application Configuration
=================================
Uses Upstash Redis as the message broker.
Task results are stored in PostgreSQL via django-celery-results.
"""

import os

from celery import Celery

# Tell Celery to use Django's settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

# Create the Celery application
app = Celery("bookautomation")

# Load Celery config from Django settings (namespace prefix: CELERY_)
app.config_from_object("django.conf:settings", namespace="CELERY")

# Automatically discover tasks.py in all installed Django apps
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Diagnostic task to verify Celery worker is connected and running."""
    print(f"[DEBUG] Celery worker received task. Request: {self.request!r}")
