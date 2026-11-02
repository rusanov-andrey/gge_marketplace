import os

from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gge_marketplace.config.settings')

app = Celery('gge_marketplace')

app.config_from_object('django.conf:settings', namespace='CELERY')

# Автоматически находим задачи (tasks.py) во всех зарегистрированных приложениях (INSTALLED_APPS)
app.autodiscover_tasks()
