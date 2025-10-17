# core/urls.py
from django.urls import path
from . import views

app_name = 'core'


urlpatterns = [
    path('', views.index, name='index'),
    path('app/', views.app, name='app'),
    path('api/campaigns/', views.campaigns, name='campaigns'),
    path('api/stats/', views.stats, name='stats'),
    path('api/user-donations/', views.user_donations, name='user_donations'),
    path('api/record-donation/', views.record_donation, name='record_donation'),
    path('api/update-sub-account/', views.update_sub_account, name='update_sub_account'),
    path('api/check-permission/', views.check_permission, name='check_permission'),
]