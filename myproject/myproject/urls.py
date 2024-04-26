"""
URL configuration for myproject project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path
from .views.views import main_page, matches_view, football_view, match_details_view,Hockey_matches_view, Hockey_view, tickets,buy_ticket, Basket_view, Basket_matches_view,Hockeymatch_details_view,Basketmatch_details_view
from .views.auth_views import CustomLoginView, CustomLogoutView, RegisterView, profile_view
from django.contrib import admin

urlpatterns = [

    path('', main_page, name='main'),
    path('football/', football_view, name='football'), 
    path('matches/<int:id>/', matches_view, name='Matches'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
    path('register/', RegisterView.as_view(), name='register'),
    path('profile/', profile_view, name='profile'),
    path('match-details/<int:league_id>/<int:match_id>/', match_details_view, name='match_details'),
    path('Hockey/', Hockey_view, name='Hockey'), 
    path('Hockey_Matches/<int:id>/', Hockey_matches_view, name='Hockey_Matches'),
    path('tickets/',tickets, name='tickets'),
    path('buy_ticket/', buy_ticket, name='buy_ticket'),
    path('Basket/', Basket_view, name='Basket'), 
    path('Basket_Matches/<int:id>/', Basket_matches_view, name='Basket_Matches'),
    path('Hockeymatch-details/<int:league_id>/<int:match_id>/', Hockeymatch_details_view, name='HockeyMatch_details'),
    path('Basket-details/<int:league_id>/<int:match_id>/', Basketmatch_details_view, name='BasketMatch_details'),
    path('admin/', admin.site.urls),



]