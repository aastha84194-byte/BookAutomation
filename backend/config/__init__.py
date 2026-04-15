"""
config package — imports Celery app so Django's
test runner and management commands pick it up automatically.
"""

from .celery import app as celery_app

__all__ = ("celery_app",)
