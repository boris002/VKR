from django.db import models
from django.contrib.auth.models import User

class FootballLiga(models.Model):
    idFootball_liga = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    country = models.CharField(max_length=255)

    class Meta:
        db_table = 'football_liga'  # Указание Django использовать конкретное имя таблицы
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
    Save_time = models.DateTimeField(auto_now=True)  # Если время матча тоже важно


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
    class Meta:
        db_table = 'Basket_matches'  # Указываем явное имя таблицы
        verbose_name = 'Basket_Match'
        verbose_name_plural = 'Basket_Matches'

    def __str__(self):
        return f"{self.home_team} vs {self.away_team} on {self.match_date.strftime('%Y-%m-%d')}"
