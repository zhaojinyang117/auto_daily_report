from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from .models import UserSettings, MonthlyPlan, EmailLog
from django.utils.html import format_html
from django.urls import reverse

# 不需要特殊注册，Django默认已经注册了User模型
# 但是可以添加一些自定义的显示字段或筛选等


# 注册用户设置模型
@admin.register(UserSettings)
class UserSettingsAdmin(admin.ModelAdmin):
    list_display = ("user", "is_active", "user_name", "send_time")
    search_fields = ("user__username", "user_name")
    list_filter = ("is_active",)


# 注册月度计划模型
@admin.register(MonthlyPlan)
class MonthlyPlanAdmin(admin.ModelAdmin):
    list_display = ("user", "year", "month", "created_at", "updated_at")
    search_fields = ("user__username",)
    list_filter = ("year", "month")


@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    list_display = ("user", "send_timestamp", "status", "subject", "short_content")
    search_fields = ("user__username", "subject")
    list_filter = ("status", "send_timestamp")
    readonly_fields = (
        "user",
        "send_timestamp",
        "status",
        "subject",
        "content_preview",
        "error_message",
    )

    def has_add_permission(self, request):
        return False


# 注意：django_cron的模型已经在django_cron的admin.py中注册了，
# 这里不再重复注册，避免冲突
