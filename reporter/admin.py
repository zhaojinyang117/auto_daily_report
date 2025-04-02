from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from .models import UserSettings, MonthlyPlan

# 不需要特殊注册，Django默认已经注册了User模型
# 但是可以添加一些自定义的显示字段或筛选等

# 注册用户设置模型
@admin.register(UserSettings)
class UserSettingsAdmin(admin.ModelAdmin):
    list_display = ('user', 'user_name', 'email_from', 'smtp_server', 'send_time', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('user__username', 'user_name', 'email_from')
    readonly_fields = ('user',)
    fieldsets = (
        ('用户信息', {
            'fields': ('user', 'user_name', 'email_signature_name', 'email_signature_phone')
        }),
        ('API设置', {
            'fields': ('gemini_api_key',)
        }),
        ('邮件设置', {
            'fields': ('email_from', 'email_password', 'email_to', 'smtp_server', 'smtp_port')
        }),
        ('发送设置', {
            'fields': ('send_time', 'is_active')
        })
    )

# 注册月度计划模型
@admin.register(MonthlyPlan)
class MonthlyPlanAdmin(admin.ModelAdmin):
    list_display = ('user', 'year', 'month', 'created_at', 'updated_at')
    list_filter = ('year', 'month', 'user')
    search_fields = ('user__username', 'content')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('基本信息', {
            'fields': ('user', 'year', 'month')
        }),
        ('计划内容', {
            'fields': ('content',)
        }),
        ('时间信息', {
            'fields': ('created_at', 'updated_at')
        })
    )
