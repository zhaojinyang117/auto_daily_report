from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'reporter'

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', auth_views.LoginView.as_view(template_name='reporter/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='reporter:login'), name='logout'),
    path('settings/', views.UserSettingsUpdateView.as_view(), name='settings_update'),
    path('settings/view/', views.settings_view, name='settings'),
    
    # 月度计划相关URL
    path('plans/', views.MonthlyPlanListView.as_view(), name='plan_list'),
    path('plans/create/', views.MonthlyPlanCreateView.as_view(), name='plan_create'),
    path('plans/<int:pk>/update/', views.MonthlyPlanUpdateView.as_view(), name='plan_update'),
    path('plans/<int:pk>/delete/', views.MonthlyPlanDeleteView.as_view(), name='plan_delete'),
    path('extract/', views.extract_content_view, name='extract_content'),
    path('extract/<int:plan_id>/', views.extract_content_view, name='extract_content_by_plan'),
    
    # 发送报告
    path('send-report/', views.send_report, name='send_report'),
] 