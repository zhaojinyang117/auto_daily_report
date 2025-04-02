from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin

# 不需要特殊注册，Django默认已经注册了User模型
# 但是可以添加一些自定义的显示字段或筛选等
