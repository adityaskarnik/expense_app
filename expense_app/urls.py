from django.urls import path
from . import views
from django.conf.urls import url, include
from django.contrib import admin
from .views import home, signup
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('home/', views.home, name='home'),
    path('expense_app/', views.index, name='index'),
    path('',auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    url(r'^login/',auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    url(r'^register/', signup),
    url(r'^logout/$', auth_views.LogoutView.as_view(template_name='logout.html'), name='logout'),
    path('databasequery/', views.ajax_loaddata, name='ajax_loaddata')
]