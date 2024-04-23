# myproject/views/views.py
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from myproject.models.model import Match,FootballLiga,LeagueScore, HockeyLeague, HockeyMatch,TicketsFootball, TicketsHockey, TicketsType,BasketLeague,BasketMatch  # Импортируйте модель, соответствующую таблице Matches
from myproject.api_settings import API_HEADERS_Football, API_HEADERS_Hockey, API_HEADERS_Basket
import json
from django.utils import timezone
from datetime import datetime, date, timedelta
import requests
import logging
from django.shortcuts import render
from googletrans import Translator, LANGUAGES
from deep_translator import GoogleTranslator

# Настройка логгера
logger = logging.getLogger(__name__)
custom_translations = {
    'Akhmat Grozny': 'Ахмат Грозный',
    'Fakel Voronezh': 'Факел Воронеж',
    'Krylya Sovetov': 'Крылья Советов',
    'Rubin': 'Рубин Казань',
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
    return render(request, 'main.html')

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

    elif selected_date_obj.date() >= today:
        matches = Match.objects.filter(league=league, match_date__date=selected_date_obj.date())
        update_matches_from_api(selected_date_obj, league, cutoff_date)
    #update_league_scores(matches, teams)

    return render(request, 'matches.html', {
        'matches': matches,
        'league': league,
        'league_name': league_name,
        'country': country,
        'selected_date': selected_date,
        'league_id': league_id,
        'teams': teams,
    })
def update_matches_from_api(date, league, cutoff_date):
    api_url = f"https://v3.football.api-sports.io/fixtures?date={date.strftime('%Y-%m-%d')}"
    response = requests.get(api_url, headers=API_HEADERS_Football)

    if response.status_code == 200:
        api_matches = response.json().get('response', [])

        for match_data in api_matches:
            if match_data['league']['name'] == league.name and match_data['league']['country'] == league.country:
                home_team_translated = translate_text(match_data['teams']['home']['name'])
                away_team_translated = translate_text(match_data['teams']['away']['name'])
                stadium_name_translated = translate_text(match_data['fixture']['venue']['name'])
                city_name_translated = translate_text(match_data['fixture']['venue']['city'])
                match_date = datetime.strptime(match_data['fixture']['date'], '%Y-%m-%dT%H:%M:%S%z') + timedelta(hours=3)
                
                # Обработать изменение дня
                if match_date.hour >= 21:
                    match_date += timedelta(days=1)               
                win = determine_winner(match_data)

                # Используем filter для поиска матчей с теми же атрибутами
                existing_matches = Match.objects.filter(
                    league=league,
                    match_date=match_date,
                    home_team=home_team_translated,
                    away_team=away_team_translated,
                    stadium_name=stadium_name_translated,
                    city_name=city_name_translated,
                    score=f"{match_data['goals']['home']} - {match_data['goals']['away']}",
                    win=win
                )

                # Если найден матч, обновляем его, иначе создаем новый
                if existing_matches.exists():
                    match = existing_matches.first()
                    match.accounted = True if match_date < cutoff_date else False
                    match.save()
                    print(f"Обновлен матч: {match}")
                else:
                    match = Match.objects.create(
                        league=league,
                        match_date=match_date,
                        home_team=home_team_translated,
                        home_team_logo=match_data['teams']['home']['logo'],
                        away_team=away_team_translated,
                        away_team_logo=match_data['teams']['away']['logo'],
                        score=f"{match_data['goals']['home']} - {match_data['goals']['away']}",
                        stadium_name=stadium_name_translated,
                        city_name=city_name_translated,
                        accounted=True if match_date < cutoff_date else False,
                        win=win
                    )
                    print(f"Создан матч: {match}")
    else:
        print(f"Ошибка при подключении к API: {response.status_code}")


def determine_winner(match_data):
    if match_data['teams']['home']['winner']:
        return translate_text(match_data['teams']['home']['name'])
    elif match_data['teams']['away']['winner']:
        return translate_text(match_data['teams']['away']['name'])
    elif match_data['goals']['home'] == match_data['goals']['away'] and match_data['goals']['home'] !='null':
        return 'Ничья'
    else:
        return 'Неопределено'

def match_details_view(request, league_id, match_id):
    # Получение лиги и матча по ID
    league = get_object_or_404(FootballLiga, pk=league_id)
    match = get_object_or_404(Match, pk=match_id, league=league)

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
            'away': match.score.split('-')[1].strip()
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
    football_ligas = FootballLiga.objects.all().order_by('name')
    return render(request, 'football.html', {'football_ligas': football_ligas})

def Hockey_view(request):
    Hockey_leagues = HockeyLeague.objects.all().order_by('name')
    return render(request, 'Hockey.html', {'Hockey_leagues': Hockey_leagues})


def Basket_view(request):
    Basket_leagues = BasketLeague.objects.all().order_by('name')
    return render(request, 'Basket.html', {'Basket_leagues': Basket_leagues})

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

# Добавьте вызов функции update_league_scores в ваш view после того, как получены и обновлены матчи
# Вам нужно будет также передать teams в функцию обновления матчей из API,
# чтобы там также могли быть обновлены результаты и очки



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

    elif selected_date_obj.date() >= today:
        Hockey_matches = HockeyMatch.objects.filter(league=league, match_date__date=selected_date_obj.date())
        update_HockeyMatches_from_api(selected_date_obj, league, cutoff_date)
    
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
    api_url = f"https://v1.hockey.api-sports.io/games?date={date.strftime('%Y-%m-%d')}"
    response = requests.get(api_url, headers=API_HEADERS_Hockey)
    if response.status_code == 200:
        api_matches = response.json().get('response', [])
        for match_data in api_matches:
            if match_data['league']['name'] == league.name:
                home_team_translated = translate_text(match_data['teams']['home']['name'])
                away_team_translated = translate_text(match_data['teams']['away']['name'])
                match_date = datetime.strptime(match_data['date'], '%Y-%m-%dT%H:%M:%S%z') + timedelta(hours=3)
                
                # Обработать изменение дня
                if match_date.hour >= 21:
                    match_date += timedelta(days=1)  
                score = f"{match_data['scores']['home']} - {match_data['scores']['away']}"
                win = determine_winner_Hockey(home_team_translated, away_team_translated, score)

                accounted = match_date < cutoff_date

                defaults = {
                    'home_team': home_team_translated,
                    'home_team_logo': match_data['teams']['home']['logo'],
                    'away_team': away_team_translated,
                    'away_team_logo': match_data['teams']['away']['logo'],
                    'score': score,
                    'first_period': match_data['periods'].get('first'),
                    'second_period': match_data['periods'].get('second'),
                    'third_period': match_data['periods'].get('third'),
                    'overtimes': match_data['periods'].get('overtime'),
                    'shotouts': match_data['periods'].get('penalties'),
                    'accounted': accounted,
                    'win': win
                }

                existing_matches = HockeyMatch.objects.filter(
                    league=league,
                    home_team=home_team_translated,
                    away_team=away_team_translated,
                    match_date=match_date,
                    score=score,
                )

                if existing_matches.exists():
                    match = existing_matches.first()
                    match.accounted = accounted
                    match.save()
                    print(f"Обновлен матч: {home_team_translated} против {away_team_translated} на {match_date.strftime('%Y-%m-%d')}")
                else:
                    match = HockeyMatch.objects.create(
                        league=league,
                        home_team=home_team_translated,
                        home_team_logo=match_data['teams']['home']['logo'],
                        away_team=away_team_translated,
                        away_team_logo=match_data['teams']['away']['logo'],
                        match_date=match_date,
                        score=score,
                        first_period=match_data['periods'].get('first'),
                        second_period=match_data['periods'].get('second'),
                        third_period=match_data['periods'].get('third'),
                        overtimes=match_data['periods'].get('overtime'),
                        shotouts=match_data['periods'].get('penalties'),
                        accounted=accounted,
                        win=win
                    )
                    print(f"Создан матч: {home_team_translated} против {away_team_translated} на {match_date.strftime('%Y-%m-%d')}")
    else:
        print(f"Ошибка при подключении к API: {response.status_code}")
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
        if wallet.balance >= total_price:
            # Списываем сумму с кошелька и сохраняем новый баланс
            wallet.balance -= total_price
            wallet.save()

            # Здесь можете выполнить другие действия, например, создать запись о покупке билета в базе данных

            messages.success(request, 'Билеты успешно куплены')
        else:
            # Если у пользователя недостаточно средств, выводим сообщение об ошибке
            messages.error(request, 'Недостаточно средств на кошельке')

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
    if not Basket_matches.exists() or Basket_matches.filter(accounted=False).exists():
        update_BasketMatches_from_api(selected_date_obj, league, cutoff_date)
        Basket_matches = BasketMatch.objects.filter(league=league, match_date__date=selected_date_obj.date())

    elif selected_date_obj.date() >= today:
        Basket_matches = BasketMatche.objects.filter(league=league, match_date__date=selected_date_obj.date())
        update_BasketMatches_from_api(selected_date_obj, league, cutoff_date)
    
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
    api_url = f"https://v1.basketball.api-sports.io/games?date={date.strftime('%Y-%m-%d')}"
    response = requests.get(api_url, headers=API_HEADERS_Basket)
    if response.status_code == 200:
        api_matches = response.json().get('response', [])
        for match_data in api_matches:
            if match_data['league']['name'] == league.name:
                home_team_translated = translate_text(match_data['teams']['home']['name'])
                away_team_translated = translate_text(match_data['teams']['away']['name'])
                match_date = datetime.strptime(match_data['date'], '%Y-%m-%dT%H:%M:%S%z') + timedelta(hours=3)
                
                # Обработать изменение дня
                if match_date.hour >= 21:
                    match_date += timedelta(days=1)  
                score = f"{match_data['scores']['home']['total']} - {match_data['scores']['away']['total']}"
                first_quarter =f"{match_data['scores']['home']['quarter_1']} - {match_data['scores']['away']['quarter_1']}"
                second_quarter =f"{match_data['scores']['home']['quarter_2']} - {match_data['scores']['away']['quarter_2']}"
                third_quarter =f"{match_data['scores']['home']['quarter_3']} - {match_data['scores']['away']['quarter_3']}"
                fourth_quarter =f"{match_data['scores']['home']['quarter_4']} - {match_data['scores']['away']['quarter_4']}"
                overtimes =f"{match_data['scores']['home']['over_time']} - {match_data['scores']['away']['over_time']}"
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
                        first_quarter = first_quarter,
                        second_quarter= second_quarter,
                        third_quarter= third_quarter,
                        fourth_quarter = fourth_quarter,
                        overtimes = overtimes,
                        accounted=accounted,
                        win=win
                    )
                    print(f"Создан матч: {home_team_translated} против {away_team_translated} на {match_date.strftime('%Y-%m-%d')}")
    else:
        print(f"Ошибка при подключении к API: {response.status_code}")

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