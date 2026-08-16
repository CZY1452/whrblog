"""Celery 异步任务入口"""
import os

from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'whrblog.settings')

from core import tasks  # noqa: E402,F401  确保 core.tasks 任务注册进当前 app

app = Celery('whrblog')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()