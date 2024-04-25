from __future__ import absolute_import, unicode_literals
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')

import django
django.setup()

from celery import Celery, shared_task,signals
from celery.schedules import crontab
from datetime import datetime, timedelta
from redis import Redis  # Импорт Redis добавлен здесь
from .models.model import FootballLiga
from .views.views import update_matches_from_api
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)
app = Celery('myproject')

app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
def setup_periodic_tasks(sender, **kwargs):
    # Вызовите задачу немедленно при старте
    sender.send_task('myproject.celery.update_matches')
@shared_task
def update_matches():
    logger.debug("Starting update_matches task.")
    leagues = FootballLiga.objects.all()
    date = datetime.now().date()
    cutoff_date = datetime.now() - timedelta(minutes=30)
    if not leagues:
        logger.debug("No leagues found.")
    for league in leagues:
        logger.debug(f"Updating matches for league {league.id}")
        update_matches_from_api(date, league, cutoff_date)
    logger.debug("Finished update_matches task.")
    return 1  # Возвращение числа для подтверждения выполнения

