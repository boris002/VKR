import schedule
import time
from .views.views import update_matches_from_api  # Импортируем функцию из вашего приложения Django

def run_schedule():
    # Запустить функцию обновления матчей каждые 30 минут
    schedule.every(30).minutes.do(update_matches_from_api)

    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == '__main__':
    run_schedule()
