import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plagiat_project.settings')

try:
    from celery import Celery
    app = Celery('plagiat_project')
    app.config_from_object('django.conf:settings', namespace='CELERY')
    app.autodiscover_tasks()
except ImportError:
    app = None
