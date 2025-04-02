from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'reporter'

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', auth_views.LoginView.as_view(template_name='reporter/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='reporter:login'), name='logout'),
    path('settings/', views.settings_view, name='settings'),
    path('settings/update/', views.UserSettingsUpdateView.as_view(), name='settings_update'),
] 