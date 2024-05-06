from django.db import models
from django.contrib.auth.models import User
from django import forms
from django.conf import settings

class TypeLeague(models.Model):
    id = models.AutoField(primary_key=True)
    type = models.CharField(max_length=255, db_column='Type')  # Указание имени колонки, если оно отличается от имени поля

    class Meta:
        db_table = 'type_league'  # Указание Django использовать конкретное имя таблицы
        verbose_name = 'Type of League'
        verbose_name_plural = 'Types of Leagues'

    def __str__(self):
        return self.type

class FootballLiga(models.Model):
    idFootball_liga = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    country = models.CharField(max_length=255)
    type = models.ForeignKey(TypeLeague, on_delete=models.CASCADE, null=True, blank=True, db_column='type_id')  # Добавление внешнего ключа

    class Meta:
        db_table = 'football_liga'
        verbose_name = 'Football Liga'
        verbose_name_plural = 'Football Ligas'

    def __str__(self):
        return self.name

class Match(models.Model):
    id = models.AutoField(primary_key=True)
    league = models.ForeignKey(
        FootballLiga, on_delete=models.CASCADE, related_name='matches', db_column='idFootball_liga'
    )
    match_date = models.DateTimeField()  # Если время матча тоже важно
    home_team = models.CharField(max_length=255)
    home_team_logo = models.URLField(max_length=1024, blank=True, null=True)  # Для логотипа домашней команды
    away_team = models.CharField(max_length=255)
    away_team_logo = models.URLField(max_length=1024, blank=True, null=True)  # Для логотипа гостевой команды
    score = models.CharField(max_length=10, blank=True, null=True)  # Счёт может быть пустым до окончания матча
    stadium_name = models.CharField(max_length=255, blank=True, null=True)
    city_name = models.CharField(max_length=255, blank=True, null=True)
    accounted = models.BooleanField(default=False)
    win = models.CharField(max_length=255, blank=True, null=True)
    Save_time = models.DateTimeField(auto_now=True)
    Home_goals = models.CharField(max_length=255)
    Away_goals = models.CharField(max_length=255)
    time_Hgoals = models.CharField(max_length=255)
    time_Agoals = models.CharField(max_length=255)


    class Meta:
        db_table = 'Matches'  # Указываем явное имя таблицы
        verbose_name = 'Match'
        verbose_name_plural = 'Matches'

    def __str__(self):
        return f"{self.home_team} vs {self.away_team} on {self.match_date.strftime('%Y-%m-%d')}"
class LeagueScore(models.Model):
    league = models.ForeignKey(FootballLiga , 
        on_delete=models.CASCADE, 
        related_name='league_scores'  # Это имя, которое используется для доступа к очкам лиги из объекта лиги
    )
    name = models.CharField(max_length=255)
    points = models.IntegerField(default=0)
    class Meta:
        db_table = 'league_scores'  # Указание Django использовать конкретное имя таблицы
        verbose_name = 'leagues scores'
        verbose_name_plural = 'leagues scores'

    def __str__(self):
        return self.name

class HockeyLeague(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)

    class Meta:
        db_table = 'Hockey_league'  # Указание Django использовать конкретное имя таблицы
        verbose_name = 'Hockey league'
        verbose_name_plural = 'Hockey leagues'

    def __str__(self):
        return self.name


class HockeyMatch(models.Model):
    id = models.AutoField(primary_key=True)
    league = models.ForeignKey(
        HockeyLeague, on_delete=models.CASCADE, related_name='Hockey_matches', db_column='Hockeyleague_id'
    )
    match_date = models.DateTimeField()  # Если время матча тоже важно
    home_team = models.CharField(max_length=255)
    home_team_logo = models.URLField(max_length=1024, blank=True, null=True)  # Для логотипа домашней команды
    away_team = models.CharField(max_length=255)
    away_team_logo = models.URLField(max_length=1024, blank=True, null=True)  # Для логотипа гостевой команды
    score = models.CharField(max_length=10, blank=True, null=True)  # Счёт может быть пустым до окончания матча
    first_period = models.CharField(max_length=10, blank=True, null=True) 
    second_period = models.CharField(max_length=10, blank=True, null=True) 
    third_period = models.CharField(max_length=10, blank=True, null=True)
    overtimes = models.CharField(max_length=10, blank=True, null=True) 
    shotouts = models.CharField(max_length=10, blank=True, null=True) 
    accounted = models.BooleanField(default=False)
    win = models.CharField(max_length=255, blank=True, null=True)
    Save_time = models.DateTimeField(auto_now=True)
    Home_goals = models.CharField(max_length=255)
    Away_goals = models.CharField(max_length=255)
    time_Hgoals = models.CharField(max_length=255)
    time_Agoals = models.CharField(max_length=255)
    Score_in_serias = models.CharField(max_length=255)


    class Meta:
        db_table = 'Hockey_matches'  # Указываем явное имя таблицы
        verbose_name = 'Hockey_Match'
        verbose_name_plural = 'Hockey_Matches'

    def __str__(self):
        return f"{self.home_team} vs {self.away_team} on {self.match_date.strftime('%Y-%m-%d')}"


class TicketsType(models.Model):
    name = models.CharField(max_length=255)

    class Meta:
        db_table = 'tickets_type'
        verbose_name = "Ticket Type"
        verbose_name_plural = "Ticket Types"

    def __str__(self):
        return self.name

class TicketsFootball(models.Model):
    idFootball_liga = models.ForeignKey(FootballLiga, on_delete=models.CASCADE, db_column='idfootball_liga')
    id_matches = models.ForeignKey(Match, on_delete=models.CASCADE, db_column='id_matches')
    id_type = models.ForeignKey(TicketsType, on_delete=models.CASCADE,db_column='id_type')
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = 'tickets_football'
        verbose_name = "Football Ticket"
        verbose_name_plural = "Football Tickets"

    def __str__(self):
        return f"{self.idFootball_liga} - {self.id_matches}"

class TicketsHockey(models.Model):
    idHockey_league = models.ForeignKey(HockeyLeague, on_delete=models.CASCADE, db_column='idHockey_league')
    id_matches = models.ForeignKey(HockeyMatch, on_delete=models.CASCADE, db_column='id_matches')
    id_type = models.ForeignKey(TicketsType, on_delete=models.CASCADE, db_column='id_type')
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = 'tickets_hockey'
        verbose_name = "Hockey Ticket"
        verbose_name_plural = "Hockey Tickets"

    def __str__(self):
        return f"{self.idHockey_league} - {self.id_matches}"

class FootballTicketPurchase(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    ticket = models.ForeignKey(TicketsFootball, on_delete=models.CASCADE)

    class Meta:
        db_table = 'football_ticket_purchases'
        verbose_name = "Football Ticket Purchase"
        verbose_name_plural = "Football Ticket Purchases"

    def __str__(self):
        return f"{self.user.username} - {self.ticket}"

class HockeyTicketPurchase(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    ticket = models.ForeignKey(TicketsHockey, on_delete=models.CASCADE)

    class Meta:
        db_table = 'hockey_ticket_purchases'
        verbose_name = "Hockey Ticket Purchase"
        verbose_name_plural = "Hockey Ticket Purchases"

    def __str__(self):
        return f"{self.user.username} - {self.ticket}"
class Wallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    class Meta:
        db_table = 'wallet'
       
    def __str__(self):
        return f"{self.user.username}'s Wallet"

class BasketLeague(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    country = models.CharField(max_length=255)

    class Meta:
        db_table = 'Basket_league'  # Указание Django использовать конкретное имя таблицы
        verbose_name = 'Basket league'
        verbose_name_plural = 'Basket leagues'

    def __str__(self):
        return self.name


class BasketMatch(models.Model):
    id = models.AutoField(primary_key=True)
    league = models.ForeignKey(
        BasketLeague, on_delete=models.CASCADE, related_name='Basket_matches', db_column='Basketleague_id'
    )
    match_date = models.DateTimeField()  # Если время матча тоже важно
    home_team = models.CharField(max_length=255)
    home_team_logo = models.URLField(max_length=1024, blank=True, null=True)  # Для логотипа домашней команды
    away_team = models.CharField(max_length=255)
    away_team_logo = models.URLField(max_length=1024, blank=True, null=True)  # Для логотипа гостевой команды
    score = models.CharField(max_length=10, blank=True, null=True)  # Счёт может быть пустым до окончания матча
    first_quarter = models.CharField(max_length=10, blank=True, null=True) 
    second_quarter = models.CharField(max_length=10, blank=True, null=True) 
    third_quarter = models.CharField(max_length=10, blank=True, null=True)
    fourth_quarter = models.CharField(max_length=10, blank=True, null=True)
    overtimes = models.CharField(max_length=10, blank=True, null=True) 
    accounted = models.BooleanField(default=False)
    win = models.CharField(max_length=255, blank=True, null=True)
    Save_time = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'Basket_matches'  # Указываем явное имя таблицы
        verbose_name = 'Basket_Match'
        verbose_name_plural = 'Basket_Matches'

    def __str__(self):
        return f"{self.home_team} vs {self.away_team} on {self.match_date.strftime('%Y-%m-%d')}"


class News(models.Model):
    country = models.CharField(max_length=255, null=True, blank=True)
    title = models.CharField(max_length=255)
    content = models.TextField()
    image = models.ImageField(upload_to='news_images/', null=True, blank=True)
    type = models.ForeignKey('TypeSport', on_delete=models.CASCADE, null=True, db_column='type_id')
    main = models.BooleanField(default=False)
    Date = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'news'
        verbose_name = 'News'
        verbose_name_plural = 'News'

    def __str__(self):
        return self.title

class TypeSport(models.Model):
    name = models.CharField(max_length=255)

    class Meta:
        db_table = 'type_sport'
        verbose_name = 'Type of Sport'
        verbose_name_plural = 'Types of Sports'

    def __str__(self):
        return self.name


class NewsForm(forms.ModelForm):
    class Meta:
        model = News
        fields = ['country', 'title', 'content', 'image', 'type', 'main']

class HockeyStandings(models.Model):
    league = models.ForeignKey('HockeyLeague', on_delete=models.CASCADE, related_name='standings', db_column='league_id')
    division = models.ForeignKey('HockeyDivision', on_delete=models.CASCADE, related_name='standings', db_column='division_id')
    name = models.CharField(max_length=255)
    points = models.IntegerField()

    def __str__(self):
        return f"{self.name} ({self.points} points)"

    class Meta:
        db_table = 'hockey_standings'
        verbose_name = 'Hockey Standing'
        verbose_name_plural = 'Hockey Standings'
        ordering = ['points']

class HockeyDivision(models.Model):
    league = models.ForeignKey('HockeyLeague', on_delete=models.CASCADE, related_name='divisions', db_column='league_id')
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'hockey_division'
        verbose_name = 'Hockey Division'
        verbose_name_plural = 'Hockey Divisions'
        ordering = ['name']


class LeagueStatistic(models.Model):
    league = models.ForeignKey(FootballLiga, on_delete=models.CASCADE, db_column='league_id')
    player_name = models.CharField(max_length=255, null=True)
    goal = models.IntegerField(default=0)

    class Meta:
        db_table = 'league_statistic'

    def __str__(self):
        return f"{self.league.name} - {self.player_name}"