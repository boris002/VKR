# myproject/views/views.py
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from myproject.models.model import Match,FootballLiga,LeagueScore, HockeyLeague, HockeyMatch,TicketsFootball, TicketsHockey, TicketsType,BasketLeague,BasketMatch, Wallet, News, TypeSport, NewsForm # Импортируйте модель, соответствующую таблице Matches
from myproject.api_settings import API_HEADERS_Football, API_HEADERS_Hockey, API_HEADERS_Basket
import json
from django.utils import timezone
from datetime import datetime, date, timedelta
import requests
import logging
from django.shortcuts import render
from googletrans import Translator, LANGUAGES
from deep_translator import GoogleTranslator
from django.contrib import messages
from django.shortcuts import redirect
from threading import Thread
from django.core.exceptions import ObjectDoesNotExist

# Настройка логгера
logger = logging.getLogger(__name__)
custom_translations = {
    'Akhmat Grozny': 'Ахмат Грозный',
    'Fakel Voronezh': 'Факел Воронеж',
    'Krylya Sovetov': 'Крылья Советов',
    'Rubin': 'Рубин Казань',
    'Olimpiyskiy Stadion Fisht': 'Фишт арена Сочи'
    # Добавьте другие нестандартные переводы сюда
}

def translate_text(text, dest_language='ru'):
    # Проверяем, есть ли перевод в нашем словаре пользовательских переводов
    if text in custom_translations:
        return custom_translations[text]

    # Иначе пытаемся перевести через Google Translate
    try:
        translation = GoogleTranslator(source='auto', target=dest_language).translate(text)
        return translation if translation else text
    except Exception as e:
        print(f"Ошибка перевода: {e}")
        # В случае ошибки пытаемся транслитерировать
        return translit(text, 'ru', reversed=True)
def main_page(request):
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    
    # Получаем футбольные матчи, которые прошли вчера и сегодня
    football_matches = Match.objects.filter(
        league__in=FootballLiga.objects.all(),  # Фильтруем только по футбольным лигам
        match_date__date__in=[yesterday, today]  # Фильтруем по датам
    ).order_by('-match_date')[:5]
    
    
    Basket_matches = BasketMatch.objects.filter(
        league__in=BasketLeague.objects.all(),  # Фильтруем только по футбольным лигам
        match_date__date__in=[yesterday, today]  # Фильтруем по датам
    ).order_by('-match_date')[:5]

    Hockey_matches = HockeyMatch.objects.filter(
        league__in=HockeyLeague.objects.all(),  # Фильтруем только по футбольным лигам
        match_date__date__in=[yesterday, today]  # Фильтруем по датам
    ).order_by('-match_date')[:5]
    main_news = News.objects.filter(main=True).order_by('-Date')[:3]  # 3 последние главные новости
    main_news_ids = [news.id for news in main_news]  # Получаем ID главных новостей в Python

    if main_news_ids:
        other_news = News.objects.exclude(id__in=main_news_ids).order_by('-Date')  # Исключаем эти ID из других новостей
    else:
        other_news = News.objects.all().order_by('-Date') 
    context = {
        'football_matches': football_matches,
        'Hockey_matches': Hockey_matches,
        'Baskey_matches': Basket_matches,
        'main_news': main_news,
        'other_news': other_news
    }


    today = timezone.now().date()
    cutoff_date = timezone.make_aware(datetime(2024, 4, 11, 0, 0, 0))
    yesterday = today - timedelta(days=1)

    # Запуск потоков
    thread_today = Thread(target=update_matches_for_all_leagues, args=(today, cutoff_date))
    thread_yesterday = Thread(target=update_matches_for_all_leagues, args=(yesterday, cutoff_date))
    threadH_today = Thread(target=update_HockeyMatches_from_all_leagues, args=(today, cutoff_date))
    threadH_yesterday = Thread(target=update_HockeyMatches_from_all_leagues, args=(yesterday, cutoff_date))
    threadB_today = Thread(target=update_BasketMatches_from_api_all, args=(today, cutoff_date))
    threadB_yesterday = Thread(target=update_BasketMatches_from_api_all, args=(yesterday, cutoff_date))
    thread_today.start()
    thread_yesterday.start()
    threadH_today.start()
    threadH_yesterday.start()
    threadB_today.start()
    threadB_yesterday.start()
    return render(request, 'main.html', context)

@csrf_exempt
@require_http_methods(["GET", "POST", "OPTIONS"])


def matches_view(request, id):
    league = get_object_or_404(FootballLiga, pk=id)
    league_id = league.idFootball_liga
    league_name = league.name
    country = league.country
    today = timezone.now().date()
    teams = LeagueScore.objects.filter(league=league).order_by('-points')

    # Получение выбранной даты или текущей даты, если дата не была выбрана
    selected_date = request.GET.get('date', today.strftime('%Y-%m-%d'))
    selected_date_obj = datetime.strptime(selected_date, '%Y-%m-%d')
    selected_date_obj = timezone.make_aware(datetime.combine(selected_date_obj, datetime.min.time()))

    # Определение, находится ли выбранная дата в пределах последних 10 дней
    ten_days_ago = today - timedelta(days=10)

    matches = Match.objects.filter(league=league, match_date__date=selected_date_obj.date())
    cutoff_date = timezone.make_aware(datetime(2024, 4, 11, 0, 0, 0))

    # Если дата в пределах последних 10 дней или данных в базе нет, или они не учтены, делаем запрос к API
    if not matches.exists() or matches.filter(accounted=False).exists():
        update_matches_from_api(selected_date_obj, league, cutoff_date)
        matches = Match.objects.filter(league=league, match_date__date=selected_date_obj.date())

    # Проверка на принадлежность пользователя к группе "journalists"
    is_journalist = request.user.groups.filter(name='journalists').exists()
    #update_league_scores(matches, teams)

    return render(request, 'matches.html', {
        'matches': matches,
        'league': league,
        'league_name': league_name,
        'country': country,
        'selected_date': selected_date,
        'league_id': league_id,
        'teams': teams,
        'is_journalist': is_journalist,
    })




def update_matches_from_api(date, league, cutoff_date):
    current_time = timezone.now()
    matches_for_date = Match.objects.filter(league=league, match_date__date=date)
    #accounted_flag = matches_for_date.filter(accounted=0).exists()
        
    try:
        last_save_time = matches_for_date.latest('Save_time').Save_time
        time_since_last_save = current_time - last_save_time
    except Match.DoesNotExist:
        time_since_last_save = None
        
    if not matches_for_date or time_since_last_save is None or time_since_last_save > timedelta(minutes=5):
        print(f"Обращаемся к API для лиги {league.name} на дату {date}")
        api_url = f"https://v3.football.api-sports.io/fixtures?date={date.strftime('%Y-%m-%d')}"
        response = requests.get(api_url, headers=API_HEADERS_Football)
        if response.status_code == 200:
                api_matches = response.json().get('response', [])
                for match_data in api_matches:
                    if match_data['league']['name'] == league.name and match_data['league']['country'] == league.country:
                        home_team_translated = translate_text(match_data['teams']['home']['name'])
                        away_team_translated = translate_text(match_data['teams']['away']['name'])
                        home_team_logo = match_data['teams']['home']['logo']
                        away_team_logo = match_data['teams']['away']['logo']
                        stadium_name_translated = translate_text(match_data['fixture']['venue']['name'])
                        city_name_translated = translate_text(match_data['fixture']['venue']['city'])
                        match_date = datetime.strptime(match_data['fixture']['date'], '%Y-%m-%dT%H:%M:%S%z')
                        match_date += timedelta(hours=3)
                        new_score = f"{match_data['goals']['home']} - {match_data['goals']['away']}"

                        # Поиск существующих матчей без учета счета
                        existing_match = Match.objects.filter(
                            league=league,
                            match_date=match_date,
                            home_team=home_team_translated,
                            away_team=away_team_translated
                        ).first()

                        if existing_match:
                            # Обновление данных при необходимости
                            if existing_match.score != new_score or existing_match.home_team_logo != home_team_logo or existing_match.away_team_logo != away_team_logo:
                                existing_match.score = new_score
                                existing_match.win = determine_winner(match_data)
                                existing_match.Save_time = current_time  # Обновляем время сохранения
                                existing_match.save()
                                print(f"Обновлен матч: {existing_match}")
                        else:
                            # Создание нового матча, если он не найден
                            match = Match.objects.create(
                                league=league,
                                match_date=match_date,
                                home_team=home_team_translated,
                                away_team=away_team_translated,
                                home_team_logo=home_team_logo,
                                away_team_logo=away_team_logo,
                                score=new_score,
                                stadium_name=stadium_name_translated,
                                city_name=city_name_translated,
                                accounted=match_date < cutoff_date,
                                win=determine_winner(match_data)
                            )
                            print(f"Создан новый матч: {match}")
        else:
                print(f"Ошибка при подключении к API: {response.status_code}")

    else:
        print(f"Недавно были обновления для {league.name} на дату {date}, не обращаемся к API.")

          



def determine_winner(match_data):
    if match_data['teams']['home']['winner']:
        return translate_text(match_data['teams']['home']['name'])
    elif match_data['teams']['away']['winner']:
        return translate_text(match_data['teams']['away']['name'])
    elif match_data['goals']['home'] == match_data['goals']['away'] and match_data['goals']['home'] !='None':
        return 'Ничья'
    else:
        return 'Неопределено'

def match_details_view(request, league_id, match_id):
    # Получение лиги и матча по ID
    league = get_object_or_404(FootballLiga, pk=league_id)
    match = get_object_or_404(Match, pk=match_id, league=league)

    # Обработка данных о голах
    home_goals_list = match.Home_goals.split(',') if match.Home_goals else []
    home_times_list = match.time_Hgoals.split(',') if match.time_Hgoals else []
    away_goals_list = match.Away_goals.split(',') if match.Away_goals else []
    away_times_list = match.time_Agoals.split(',') if match.time_Agoals else []

    # Преобразование данных о матче в словарь для передачи в шаблон
    match_data = {
        'name': f"{match.home_team} vs {match.away_team}",
        'teams': {
            'home': {
                'name': match.home_team,
                'logo': match.home_team_logo
            },
            'away': {
                'name': match.away_team,
                'logo': match.away_team_logo
            }
        },
        'goals': {
            'home': match.score.split('-')[0].strip(),
            'away': match.score.split('-')[1].strip(),
            'home_details': list(zip(home_goals_list, home_times_list)),
            'away_details': list(zip(away_goals_list, away_times_list))
        },
        'fixture': {
            'venue': {
                'name': match.stadium_name if match.stadium_name else "Unknown Stadium",
                'city': match.city_name if match.city_name else "Unknown City"
            }
        },
        'date': match.match_date.strftime('%Y-%m-%d %H:%M')
    }

    return render(request, 'match_details.html', {
        'match': match_data,
        'league_name': league.name,
        'country': league.country
    })

def football_view(request):
    # Предполагаем, что у футбола в TypeSport id = 1 или можно найти точное название 'football'
    football_type = TypeSport.objects.get(name='football')  # Ищем тип "football"
    football_news = News.objects.filter(type=football_type).order_by('-Date')[:10]  # Получаем последние 10 новостей по футболу

    leagues = FootballLiga.objects.filter(type__id=1).order_by('name')
    cups = FootballLiga.objects.filter(type__id=3).order_by('name')
    euro_cups = FootballLiga.objects.filter(type__id=2).order_by('name')

    return render(request, 'football.html', {
        'leagues': leagues,
        'euro_cups': euro_cups,
        'cups': cups,
        'football_news': football_news  # Добавляем новости в контекст
    })

def Hockey_view(request):
    Hockey_type = TypeSport.objects.get(name='Hockey')  # Ищем тип "football"
    Hockey_news = News.objects.filter(type=Hockey_type).order_by('-Date')[:10] 

    Hockey_leagues = HockeyLeague.objects.all().order_by('name')
    return render(request, 'Hockey.html', {'Hockey_leagues': Hockey_leagues, 'Hockey_news': Hockey_news})


def Basket_view(request):
    Basket_type = TypeSport.objects.get(name='Basket') 
    Basket_news = News.objects.filter(type=Basket_type).order_by('-Date')[:10] 
    Basket_leagues = BasketLeague.objects.all().order_by('name')
    return render(request, 'Basket.html', {'Basket_leagues': Basket_leagues, 'Basket_news': Basket_news})

def update_league_scores(matches, teams):
    for match in matches:
        if match.accounted or match.win == 'Неопределено':
            # Этот матч уже учтен или победитель не определен
            continue

        # Предполагается, что 'win' содержит либо 'Ничья', либо название победившей команды
        if match.win == 'Ничья':
            match.accounted = 1
            home_team = teams.get(name=match.home_team)
            away_team = teams.get(name=match.away_team)
            home_team.points += 1
            away_team.points += 1
            home_team.save()
            away_team.save()
        else:
            match.accounted = 1
            winning_team = teams.get(name=match.win)
            winning_team.points += 3
            winning_team.save()

        # Устанавливаем флаг, что матч учтен
        match.save()


def Hockey_matches_view(request, id):
    league = get_object_or_404(HockeyLeague, pk=id)
    league_id = league.id
    league_name = league.name
    today = timezone.now().date()
   #teams = LeagueScore.objects.filter(league=league).order_by('-points')

    # Получение выбранной даты или текущей даты, если дата не была выбрана
    selected_date = request.GET.get('date', today.strftime('%Y-%m-%d'))
    selected_date_obj = datetime.strptime(selected_date, '%Y-%m-%d')
    selected_date_obj = timezone.make_aware(datetime.combine(selected_date_obj, datetime.min.time()))

    # Определение, находится ли выбранная дата в пределах последних 10 дней
    ten_days_ago = today - timedelta(days=2)

    Hockey_matches = HockeyMatch.objects.filter(league=league, match_date__date=selected_date_obj.date())
    cutoff_date = timezone.make_aware(datetime(2024, 4, 11, 0, 0, 0))

    # Если дата в пределах последних 1 дней или данных в базе нет, или они не учтены, делаем запрос к API
    if not Hockey_matches.exists() or Hockey_matches.filter(accounted=False).exists():
        update_HockeyMatches_from_api(selected_date_obj, league, cutoff_date)
        Hockey_matches = HockeyMatch.objects.filter(league=league, match_date__date=selected_date_obj.date())

   
    #update_league_scores(matches, teams)

    return render(request, 'Hockey_Matches.html', {
        'Hockey_Matches': Hockey_matches,
        'league': league,
        'league_name': league_name,
        'selected_date': selected_date,
        'league_id': league_id,
    #'teams': teams,
    })

def determine_winner_Hockey(home_team, away_team, score):
    try:
        home_goals, away_goals = map(int, score.split(' - '))
        goal_difference = abs(home_goals - away_goals)  # Модуль разницы голов
        if home_goals > away_goals:
            return f"{home_team} Выиграл с разницей в  {goal_difference}"
        elif home_goals < away_goals:
            return f"{away_team} Выиграл с разницей в {goal_difference}"
        else:
            return 'Draw'
    except ValueError:
        return 'Неопределено'

def update_HockeyMatches_from_api(date, league, cutoff_date):
        current_time = timezone.now()
    
        matches_for_date = HockeyMatch.objects.filter(league=league, match_date__date=date)
        #accounted_flag = matches_for_date.filter(accounted=0).exists()
        
        try:
            last_save_time = matches_for_date.latest('Save_time').Save_time
            time_since_last_save = current_time - last_save_time
        except HockeyMatch.DoesNotExist:
            time_since_last_save = None
        
        if not matches_for_date or  time_since_last_save is None or time_since_last_save > timedelta(minutes=5):
            print(f"Обращаемся к API для лиги {league.name} на дату {date}")
            api_url = f"https://v1.hockey.api-sports.io/games?date={date.strftime('%Y-%m-%d')}"
            response = requests.get(api_url, headers=API_HEADERS_Hockey)
            if response.status_code == 200:
                api_matches = response.json().get('response', [])
                for match_data in api_matches:
                    if match_data['league']['name'] == league.name:
                        home_team_translated = translate_text(match_data['teams']['home']['name'])
                        away_team_translated = translate_text(match_data['teams']['away']['name'])
                        match_date = datetime.strptime(match_data['date'], '%Y-%m-%dT%H:%M:%S%z')
                        match_date += timedelta(hours=3)  
                        new_score = f"{match_data['scores']['home']} - {match_data['scores']['away']}"
                        win = determine_winner_Hockey(home_team_translated, away_team_translated, new_score)
                        
                        existing_match = HockeyMatch.objects.filter(
                            league=league,
                            home_team=home_team_translated,
                            away_team=away_team_translated,
                            match_date=match_date
                        ).first()

                        if existing_match:
                            # Обновляем только счет и статус accounted при необходимости
                            if existing_match.score != new_score:
                                existing_match.score = new_score
                                existing_match.accounted = match_date < cutoff_date
                                existing_match.Save_time = current_time  # Обновляем время сохранения
                                existing_match.win = win
                                existing_match.save()
                                print(f"Обновлен матч: {home_team_translated} против {away_team_translated} на {match_date.strftime('%Y-%m-%d')}")
                        else:
                            # Создаем новый матч, если он не найден
                            match = HockeyMatch.objects.create(
                                league=league,
                                home_team=home_team_translated,
                                home_team_logo=match_data['teams']['home']['logo'],
                                away_team=away_team_translated,
                                away_team_logo=match_data['teams']['away']['logo'],
                                match_date=match_date,
                                score=new_score,
                                first_period=match_data['periods'].get('first'),
                                second_period=match_data['periods'].get('second'),
                                third_period=match_data['periods'].get('third'),
                                overtimes=match_data['periods'].get('overtime'),
                                shotouts=match_data['periods'].get('penalties'),
                                accounted=match_date < cutoff_date,
                                win=win
                            )
                            print(f"Создан новый матч: {home_team_translated} против {away_team_translated} на {match_date.strftime('%Y-%m-%d')}")
            else:
                print(f"Ошибка при подключении к API: {response.status_code}")
        else:
            print(f"Недавно были обновления для {league.name} на дату {date}, не обращаемся к API.")

    
def tickets(request):
    current_date = datetime.now().date()
    football_matches = TicketsFootball.objects.filter(id_matches__match_date__gte=current_date)
    hockey_matches = TicketsHockey.objects.filter(id_matches__match_date__gte=current_date)
    ticket_types = TicketsType.objects.all()
    return render(request, 'tickets.html', {'football_matches': football_matches, 'hockey_matches': hockey_matches, 'ticket_types': ticket_types})

def buy_ticket(request):
    if request.method == 'POST':
        match_id = request.POST.get('match_id')
        quantity = int(request.POST.get('quantity'))
        payment_method = request.POST.get('payment_method')
        
        # Получаем информацию о матче
        try:
            football_match = TicketsFootball.objects.get(id=match_id)
        except TicketsFootball.DoesNotExist:
            football_match = None

        try:
            hockey_match = TicketsHockey.objects.get(id=match_id)
        except TicketsHockey.DoesNotExist:
            hockey_match = None

        if football_match:
            ticket = football_match
        elif hockey_match:
            ticket = hockey_match
        else:
            # Если матч не найден, выводим сообщение об ошибке
            messages.error(request, 'Матч не найден')
            return redirect('tickets')

        # Проверяем, есть ли у пользователя кошелек
        try:
            wallet = Wallet.objects.get(user=request.user)
        except Wallet.DoesNotExist:
            # Если у пользователя нет кошелька, создаем его со стандартным балансом
            wallet = Wallet.objects.create(user=request.user)

        # Проверяем, достаточно ли у пользователя средств для покупки билетов
        total_price = ticket.price * quantity
        if payment_method == 'wallet':
            if wallet.balance >= total_price:
                # Списываем сумму с кошелька и сохраняем новый баланс
                wallet.balance -= total_price
                wallet.save()

                # Уменьшаем количество доступных билетов
                ticket.quantity -= quantity
                ticket.save()

                # Здесь можете выполнить другие действия, например, создать запись о покупке билета в базе данных

                messages.success(request, 'Билеты успешно куплены')
            else:
                # Если у пользователя недостаточно средств, выводим сообщение об ошибке
                messages.error(request, 'Недостаточно средств на кошельке')
                return redirect('tickets')
        elif payment_method == 'card':
            # Здесь можете добавить обработку платежа с помощью карты
            # Предполагается, что здесь будет вызов соответствующего метода для оплаты с карты
            messages.success(request, 'Оплата с карты успешно произведена')
            # Уменьшаем количество доступных билетов
            ticket.quantity -= quantity
            ticket.save()
            # Здесь можете выполнить другие действия, например, создать запись о покупке билета в базе данных
            return redirect('tickets')
        else:
            # Если не выбран ни один метод оплаты, выводим сообщение об ошибке
            messages.error(request, 'Выберите метод оплаты')
            return redirect('tickets')

    return redirect('tickets')


def Basket_matches_view(request, id):
    league = get_object_or_404(BasketLeague, pk=id)
    league_id = league.id
    league_name = league.name
    league_coutry = league.country
    today = timezone.now().date()
   #teams = LeagueScore.objects.filter(league=league).order_by('-points')

    # Получение выбранной даты или текущей даты, если дата не была выбрана
    selected_date = request.GET.get('date', today.strftime('%Y-%m-%d'))
    selected_date_obj = datetime.strptime(selected_date, '%Y-%m-%d')
    selected_date_obj = timezone.make_aware(datetime.combine(selected_date_obj, datetime.min.time()))

    # Определение, находится ли выбранная дата в пределах последних 10 дней
    ten_days_ago = today - timedelta(days=2)

    Basket_matches = BasketMatch.objects.filter(league=league, match_date__date=selected_date_obj.date())
    cutoff_date = timezone.make_aware(datetime(2024, 4, 11, 0, 0, 0))

    # Если дата в пределах последних 1 дней или данных в базе нет, или они не учтены, делаем запрос к API
    if not Basket_matches.exists() :
        update_BasketMatches_from_api(selected_date_obj, league, cutoff_date)
        Basket_matches = BasketMatch.objects.filter(league=league, match_date__date=selected_date_obj.date())


    #update_league_scores(matches, teams)

    return render(request, 'Basket_Matches.html', {
        'Basket_Matches': Basket_matches,
        'league': league,
        'league_name': league_name,
        'country': league_coutry,
        'selected_date': selected_date,
        'league_id': league_id,
    #'teams': teams,
    })


def update_BasketMatches_from_api(date, league, cutoff_date):
        current_time = timezone.now()
    

        matches_for_date = BasketMatch.objects.filter(league=league, match_date__date=date)
        
        try:
            last_save_time = matches_for_date.latest('Save_time').Save_time
            time_since_last_save = current_time - last_save_time
        except BasketMatch.DoesNotExist:
            time_since_last_save = None
        
        if not matches_for_date or time_since_last_save is None or time_since_last_save > timedelta(minutes=5):
            print(f"Обращаемся к API для лиги {league.name} на дату {date}")
            api_url = f"https://v1.basketball.api-sports.io/games?date={date.strftime('%Y-%m-%d')}"
            response = requests.get(api_url, headers=API_HEADERS_Basket)
            if response.status_code == 200:
                api_matches = response.json().get('response', [])
                for match_data in api_matches:
                    if match_data['league']['name'] == league.name:
                        match_date = datetime.strptime(match_data['date'], '%Y-%m-%dT%H:%M:%S%z')
                        match_date += timedelta(hours=3)  
                        home_team_translated = translate_text(match_data['teams']['home']['name'])
                        away_team_translated = translate_text(match_data['teams']['away']['name'])
                        score = f"{match_data['scores']['home']['total']} - {match_data['scores']['away']['total']}"
                        first_quarter = f"{match_data['scores']['home']['quarter_1']} - {match_data['scores']['away']['quarter_1']}"
                        second_quarter = f"{match_data['scores']['home']['quarter_2']} - {match_data['scores']['away']['quarter_2']}"
                        third_quarter = f"{match_data['scores']['home']['quarter_3']} - {match_data['scores']['away']['quarter_3']}"
                        fourth_quarter = f"{match_data['scores']['home']['quarter_4']} - {match_data['scores']['away']['quarter_4']}"
                        overtimes = f"{match_data['scores']['home']['over_time']} - {match_data['scores']['away']['over_time']}"
                        win = determine_winner_Hockey(home_team_translated, away_team_translated, score)
                        accounted = match_date < cutoff_date

                        defaults = {
                            'home_team': home_team_translated,
                            'home_team_logo': match_data['teams']['home']['logo'],
                            'away_team': away_team_translated,
                            'away_team_logo': match_data['teams']['away']['logo'],
                            'score': score,
                            'first_quarter': first_quarter,
                            'second_quarter': second_quarter,
                            'third_quarter': third_quarter,
                            'fourth_quarter': fourth_quarter,
                            'overtimes': overtimes,
                            'accounted': accounted,
                            'win': win
                        }

                        existing_matches = BasketMatch.objects.filter(
                            league=league,
                            home_team=home_team_translated,
                            away_team=away_team_translated,
                            match_date=match_date,
                            score=score,
                        )

                        if existing_matches.exists():
                            match = existing_matches.first()
                            match.accounted = accounted
                            match.Save_time = current_time  # Обновляем время сохранения
                            match.save()
                            print(f"Обновлен матч: {home_team_translated} против {away_team_translated} на {match_date.strftime('%Y-%m-%d')}")
                        else:
                            match = BasketMatch.objects.create(
                                league=league,
                                home_team=home_team_translated,
                                home_team_logo=match_data['teams']['home']['logo'],
                                away_team=away_team_translated,
                                away_team_logo=match_data['teams']['away']['logo'],
                                match_date=match_date,
                                score=score,
                                first_quarter=first_quarter,
                                second_quarter=second_quarter,
                                third_quarter=third_quarter,
                                fourth_quarter=fourth_quarter,
                                overtimes=overtimes,
                                accounted=accounted,
                                win=win
                            )
                            print(f"Создан новый матч: {home_team_translated} против {away_team_translated} на {match_date.strftime('%Y-%m-%d')}")
            else:
                print(f"Ошибка при подключении к API: {response.status_code}")
        else:
            print(f"Недавно были обновления для {league.name} на дату {date}, не обращаемся к API.")


def Hockeymatch_details_view(request, league_id, match_id):
    # Получение лиги и матча по ID
    league = get_object_or_404(HockeyLeague, pk=league_id)
    match = get_object_or_404(HockeyMatch, pk=match_id, league=league)

    # Преобразование данных о матче в словарь для передачи в шаблон
    match_data = {
        'name': f"{match.home_team} vs {match.away_team}",
        'teams': {
            'home': {
                'name': match.home_team,
                'logo': match.home_team_logo
            },
            'away': {
                'name': match.away_team,
                'logo': match.away_team_logo
            }
        },
        'goals': {
            'home': match.score.split('-')[0].strip(),
            'away': match.score.split('-')[1].strip(),
            'home1': match.first_period.split('-')[0].strip(),
            'away1': match.first_period.split('-')[1].strip(),
            'home2': match.second_period.split('-')[0].strip(),
            'away2': match.second_period.split('-')[1].strip(),
            'home3': match.third_period.split('-')[0].strip(),
            'away3': match.third_period.split('-')[1].strip(),
        },
        'win': match.win,
        'date': match.match_date.strftime('%Y-%m-%d %H:%M')
    }

    return render(request, 'HockeyMatch_details.html', {
        'match': match_data,
        'league_name': league.name,
    })


def Basketmatch_details_view(request, league_id, match_id):
    # Получение лиги и матча по ID
    league = get_object_or_404(BasketLeague, pk=league_id)
    match = get_object_or_404(BasketMatch, pk=match_id, league=league)

    # Преобразование данных о матче в словарь для передачи в шаблон
    match_data = {
        'name': f"{match.home_team} vs {match.away_team}",
        'teams': {
            'home': {
                'name': match.home_team,
                'logo': match.home_team_logo
            },
            'away': {
                'name': match.away_team,
                'logo': match.away_team_logo
            }
        },
        'goals': {
            'home': match.score.split('-')[0].strip(),
            'away': match.score.split('-')[1].strip(),
            'home1': match.first_quarter.split('-')[0].strip(),
            'away1': match.first_quarter.split('-')[1].strip(),
            'home2': match.second_quarter.split('-')[0].strip(),
            'away2': match.second_quarter.split('-')[1].strip(),
            'home3': match.third_quarter.split('-')[0].strip(),
            'away3': match.third_quarter.split('-')[1].strip(),
            'home4': match.fourth_quarter.split('-')[0].strip(),
            'away4': match.fourth_quarter.split('-')[1].strip(),
        },
        'win': match.win,
        'date': match.match_date.strftime('%Y-%m-%d %H:%M')
    }

    return render(request, 'BasketMatch_details.html', {
        'match': match_data,
        'league_name': league.name,
        'country': league.country
    })



def update_matches_for_all_leagues(date, cutoff_date):
    current_time = timezone.now()
    
    for league in FootballLiga.objects.all():
        matches_for_date = Match.objects.filter(league=league, match_date__date=date)
        #accounted_flag = matches_for_date.filter(accounted=0).exists()
        
        try:
            last_save_time = matches_for_date.latest('Save_time').Save_time
            time_since_last_save = current_time - last_save_time
        except Match.DoesNotExist:
            time_since_last_save = None
        
        if not matches_for_date or  time_since_last_save is None or time_since_last_save > timedelta(minutes=5):
            print(f"Обращаемся к API для лиги {league.name} на дату {date}")
            api_url = f"https://v3.football.api-sports.io/fixtures?date={date.strftime('%Y-%m-%d')}"
            response = requests.get(api_url, headers=API_HEADERS_Football)

            if response.status_code == 200:
                api_matches = response.json().get('response', [])
                for match_data in api_matches:
                    # Допустим, API возвращает лигу в формате, который совпадает с вашими объектами FootballLiga.
                    if match_data['league']['name'] == league.name and match_data['league']['country'] == league.country:
                        # Предполагается, что функции translate_text и determine_winner существуют.
                        home_team_translated = translate_text(match_data['teams']['home']['name'])
                        away_team_translated = translate_text(match_data['teams']['away']['name'])
                        stadium_name_translated = translate_text(match_data['fixture']['venue']['name'])
                        city_name_translated = translate_text(match_data['fixture']['venue']['city'])
                        match_date = datetime.strptime(match_data['fixture']['date'], '%Y-%m-%dT%H:%M:%S%z')
                        match_date += timedelta(hours=3)
                        win = determine_winner(match_data)
                        new_score = f"{match_data['goals']['home']} - {match_data['goals']['away']}"

                        # Поиск существующих матчей без учета счета.
                        existing_match = Match.objects.filter(
                            league=league,
                            match_date=match_date,
                            home_team=home_team_translated,
                            away_team=away_team_translated
                        ).first()

                        if existing_match:
                            # Обновление данных при необходимости.
                            if existing_match.score != new_score:
                                existing_match.score = new_score
                                existing_match.win = win
                                existing_match.Save_time = current_time  # Обновляем время сохранения.
                                existing_match.save()
                                print(f"Обновлен матч: {existing_match}")
                        else:
                            # Создание нового матча.
                            Match.objects.create(
                                league=league,
                                match_date=match_date,
                                home_team=home_team_translated,
                                home_team_logo=match_data['teams']['home']['logo'],
                                away_team=away_team_translated,
                                away_team_logo=match_data['teams']['away']['logo'],
                                score=new_score,
                                stadium_name=stadium_name_translated,
                                city_name=city_name_translated,
                                accounted=True if match_date < cutoff_date else False,
                                win=win
                            )
                            print(f"Создан новый матч для лиги {league.name}")
            else:
                print(f"Ошибка при подключении к API: {response.status_code}")
        else:
            print(f"Недавно были обновления для {league.name} на дату {date}, не обращаемся к API.")

        



def update_HockeyMatches_from_all_leagues(date,cutoff_date):
    current_time = timezone.now()
    for league in HockeyLeague.objects.all():
        matches_for_date = HockeyMatch.objects.filter(league=league, match_date__date=date)
        #accounted_flag = matches_for_date.filter(accounted=0).exists()
        
        try:
            last_save_time = matches_for_date.latest('Save_time').Save_time
            time_since_last_save = current_time - last_save_time
        except HockeyMatch.DoesNotExist:
            time_since_last_save = None
        
        if not matches_for_date or  time_since_last_save is None or time_since_last_save > timedelta(minutes=5):
            print(f"Обращаемся к API для лиги {league.name} на дату {date}")
            api_url = f"https://v1.hockey.api-sports.io/games?date={date.strftime('%Y-%m-%d')}"
            response = requests.get(api_url, headers=API_HEADERS_Hockey)
            if response.status_code == 200:
                api_matches = response.json().get('response', [])
                for match_data in api_matches:
                    if match_data['league']['name'] == league.name:
                        home_team_translated = translate_text(match_data['teams']['home']['name'])
                        away_team_translated = translate_text(match_data['teams']['away']['name'])
                        match_date = datetime.strptime(match_data['date'], '%Y-%m-%dT%H:%M:%S%z')
                        match_date += timedelta(hours=3)  
                        new_score = f"{match_data['scores']['home']} - {match_data['scores']['away']}"
                        win = determine_winner_Hockey(home_team_translated, away_team_translated, new_score)
                        
                        existing_match = HockeyMatch.objects.filter(
                            league=league,
                            home_team=home_team_translated,
                            away_team=away_team_translated,
                            match_date=match_date
                        ).first()

                        if existing_match:
                            # Обновляем только счет и статус accounted при необходимости
                            if existing_match.score != new_score:
                                existing_match.score = new_score
                                existing_match.accounted = match_date < cutoff_date
                                existing_match.Save_time = current_time  # Обновляем время сохранения
                                existing_match.win = win
                                existing_match.save()
                                print(f"Обновлен матч: {home_team_translated} против {away_team_translated} на {match_date.strftime('%Y-%m-%d')}")
                        else:
                            # Создаем новый матч, если он не найден
                            match = HockeyMatch.objects.create(
                                league=league,
                                home_team=home_team_translated,
                                home_team_logo=match_data['teams']['home']['logo'],
                                away_team=away_team_translated,
                                away_team_logo=match_data['teams']['away']['logo'],
                                match_date=match_date,
                                score=new_score,
                                first_period=match_data['periods'].get('first'),
                                second_period=match_data['periods'].get('second'),
                                third_period=match_data['periods'].get('third'),
                                overtimes=match_data['periods'].get('overtime'),
                                shotouts=match_data['periods'].get('penalties'),
                                accounted=match_date < cutoff_date,
                                win=win
                            )
                            print(f"Создан новый матч: {home_team_translated} против {away_team_translated} на {match_date.strftime('%Y-%m-%d')}")
            else:
                print(f"Ошибка при подключении к API: {response.status_code}")
        else:
            print(f"Недавно были обновления для {league.name} на дату {date}, не обращаемся к API.")


def update_BasketMatches_from_api_all(date, cutoff_date):
    current_time = timezone.now()
    
    for league in BasketLeague.objects.all():
        matches_for_date = BasketMatch.objects.filter(league=league, match_date__date=date)
        
        try:
            last_save_time = matches_for_date.latest('Save_time').Save_time
            time_since_last_save = current_time - last_save_time
        except BasketMatch.DoesNotExist:
            time_since_last_save = None
        
        if not matches_for_date or time_since_last_save is None or time_since_last_save > timedelta(minutes=5):
            print(f"Обращаемся к API для лиги {league.name} на дату {date}")
            api_url = f"https://v1.basketball.api-sports.io/games?date={date.strftime('%Y-%m-%d')}"
            response = requests.get(api_url, headers=API_HEADERS_Basket)
            if response.status_code == 200:
                api_matches = response.json().get('response', [])
                for match_data in api_matches:
                    if match_data['league']['name'] == league.name:
                        match_date = datetime.strptime(match_data['date'], '%Y-%m-%dT%H:%M:%S%z')
                        match_date += timedelta(hours=3)  
                        home_team_translated = translate_text(match_data['teams']['home']['name'])
                        away_team_translated = translate_text(match_data['teams']['away']['name'])
                        score = f"{match_data['scores']['home']['total']} - {match_data['scores']['away']['total']}"
                        first_quarter = f"{match_data['scores']['home']['quarter_1']} - {match_data['scores']['away']['quarter_1']}"
                        second_quarter = f"{match_data['scores']['home']['quarter_2']} - {match_data['scores']['away']['quarter_2']}"
                        third_quarter = f"{match_data['scores']['home']['quarter_3']} - {match_data['scores']['away']['quarter_3']}"
                        fourth_quarter = f"{match_data['scores']['home']['quarter_4']} - {match_data['scores']['away']['quarter_4']}"
                        overtimes = f"{match_data['scores']['home']['over_time']} - {match_data['scores']['away']['over_time']}"
                        win = determine_winner_Hockey(home_team_translated, away_team_translated, score)
                        accounted = match_date < cutoff_date

                        defaults = {
                            'home_team': home_team_translated,
                            'home_team_logo': match_data['teams']['home']['logo'],
                            'away_team': away_team_translated,
                            'away_team_logo': match_data['teams']['away']['logo'],
                            'score': score,
                            'first_quarter': first_quarter,
                            'second_quarter': second_quarter,
                            'third_quarter': third_quarter,
                            'fourth_quarter': fourth_quarter,
                            'overtimes': overtimes,
                            'accounted': accounted,
                            'win': win
                        }

                        existing_matches = BasketMatch.objects.filter(
                            league=league,
                            home_team=home_team_translated,
                            away_team=away_team_translated,
                            match_date=match_date,
                            score=score,
                        )

                        if existing_matches.exists():
                            match = existing_matches.first()
                            match.accounted = accounted
                            match.Save_time = current_time  # Обновляем время сохранения
                            match.save()
                            print(f"Обновлен матч: {home_team_translated} против {away_team_translated} на {match_date.strftime('%Y-%m-%d')}")
                        else:
                            match = BasketMatch.objects.create(
                                league=league,
                                home_team=home_team_translated,
                                home_team_logo=match_data['teams']['home']['logo'],
                                away_team=away_team_translated,
                                away_team_logo=match_data['teams']['away']['logo'],
                                match_date=match_date,
                                score=score,
                                first_quarter=first_quarter,
                                second_quarter=second_quarter,
                                third_quarter=third_quarter,
                                fourth_quarter=fourth_quarter,
                                overtimes=overtimes,
                                accounted=accounted,
                                win=win
                            )
                            print(f"Создан новый матч: {home_team_translated} против {away_team_translated} на {match_date.strftime('%Y-%m-%d')}")
            else:
                print(f"Ошибка при подключении к API: {response.status_code}")
        else:
            print(f"Недавно были обновления для {league.name} на дату {date}, не обращаемся к API.")



def edit_league_details(request, league_id):
    league = get_object_or_404(FootballLiga, pk=league_id)
    selected_date = request.GET.get('matchDate')  # Get the date from GET request

    if request.method == 'POST':
        # Handling form submission
        matches = Match.objects.filter(league=league)
        for match in matches:
            match.score = request.POST.get(f'score_{match.id}', match.score)
            match.Home_goals = request.POST.get(f'home_goals_{match.id}', match.Home_goals)
            match.Away_goals = request.POST.get(f'away_goals_{match.id}', match.Away_goals)
            match.time_Hgoals = request.POST.get(f'time_Hgoals_{match.id}', 0)
            match.time_Agoals = request.POST.get(f'time_Agoals_{match.id}', 0)
            match.save()

        teams = LeagueScore.objects.filter(league=league)
        for team in teams:
            team.points = int(request.POST.get(f'points_{team.id}', team.points))
            team.save()

        return redirect(f'edit?league_id={league_id}&matchDate={selected_date}')  # Redirect to keep the filter

    else:
        if selected_date:
            matches = Match.objects.filter(league=league, match_date__date=datetime.strptime(selected_date, '%Y-%m-%d'))
        else:
            matches = Match.objects.filter(league=league)
        teams = LeagueScore.objects.filter(league=league).order_by('-points')

        return render(request, 'edit.html', {
            'league': league,
            'matches': matches,
            'teams': teams,
            'selected_date': selected_date or ""  # Pass back to template to maintain state
        })

def news_view(request):
    news_list = News.objects.all().order_by('-Date')  # Получаем все новости, отсортированные по дате
    return render(request, 'news.html', {'news_list': news_list})


def create_news(request):
    if request.method == 'POST':
        form = NewsForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('news')  # Перенаправление на список новостей после создания
    else:
        form = NewsForm()
    return render(request, 'create_news.html', {'form': form})


def news_detail_view(request, news_id):
    # Получаем одну новость по ID
    news = get_object_or_404(News, id=news_id)
    return render(request, 'news-detail.html', {'news': news})

def edit_news(request, news_id):
    news = get_object_or_404(News, id=news_id)
    if request.method == 'POST':
        form = NewsForm(request.POST, request.FILES, instance=news)
        if form.is_valid():
            form.save()
            return redirect('news')  # Вернуть пользователя к списку новостей после сохранения изменений
    else:
        form = NewsForm(instance=news)
    return render(request, 'edit_news.html', {'form': form})

def delete_news(request, news_id):
    if request.method == 'POST':
        news = get_object_or_404(News, pk=news_id)
        news.delete()
        return redirect('news')
    else:
        # Handle GET request (if any)
        pass