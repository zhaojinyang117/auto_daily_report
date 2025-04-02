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
    
    # 月度计划相关URL
    path('plans/', views.MonthlyPlanListView.as_view(), name='plan_list'),
    path('plans/create/', views.MonthlyPlanCreateView.as_view(), name='plan_create'),
    path('plans/<int:pk>/update/', views.MonthlyPlanUpdateView.as_view(), name='plan_update'),
    path('plans/<int:pk>/delete/', views.MonthlyPlanDeleteView.as_view(), name='plan_delete'),
    path('plans/extract/', views.extract_content_for_date, name='extract_content'),
    path('plans/<int:plan_id>/extract/', views.extract_content_for_date, name='extract_content_from_plan'),
] 