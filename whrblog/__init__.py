# App config is auto-discovered via whrblog/apps.py WhrblogAppConfig

from .celery import app as celery_app

__all__ = ('celery_app',)
