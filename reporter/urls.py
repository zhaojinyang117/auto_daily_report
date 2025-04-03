from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .views import PasswordChangeView

app_name = "reporter"

urlpatterns = [
    path("", views.home, name="home"),
    path(
        "login/",
        auth_views.LoginView.as_view(template_name="reporter/login.html"),
        name="login",
    ),
    path(
        "logout/",
        auth_views.LogoutView.as_view(
            next_page="reporter:login",
            template_name="reporter/login.html",
            http_method_names=["get", "post"],
        ),
        name="logout",
    ),
    path("settings/", views.UserSettingsUpdateView.as_view(), name="settings_update"),
    path("settings/view/", views.settings_view, name="settings"),
    # 修改密码URL
    path(
        "password-change/",
        PasswordChangeView.as_view(),
        name="password_change",
    ),
    path(
        "password-change/done/",
        auth_views.PasswordChangeDoneView.as_view(
            template_name="reporter/password_change_done.html"
        ),
        name="password_change_done",
    ),
    # 月度计划相关URL
    path("plans/", views.MonthlyPlanListView.as_view(), name="plan_list"),
    path("plans/create/", views.MonthlyPlanCreateView.as_view(), name="plan_create"),
    path(
        "plans/<int:pk>/update/",
        views.MonthlyPlanUpdateView.as_view(),
        name="plan_update",
    ),
    path(
        "plans/<int:pk>/delete/",
        views.MonthlyPlanDeleteView.as_view(),
        name="plan_delete",
    ),
    path("extract/", views.extract_content_view, name="extract_content"),
    path(
        "extract/<int:plan_id>/",
        views.extract_content_view,
        name="extract_content_by_plan",
    ),
    # 发送报告
    path("send-report/", views.send_report, name="send_report"),
    path("email-history/", views.email_history, name="email_history"),
]
