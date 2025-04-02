import os
import django

# 设置Django环境
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "daily_reporter_project.settings")
django.setup()

# 导入必要的模型
from django.contrib.auth.models import User
from reporter.models import UserSettings


def update_send_days():
    # 获取第一个用户
    user = User.objects.first()
    if not user:
        print("没有找到用户")
        return

    # 获取或创建用户设置
    settings, created = UserSettings.objects.get_or_create(user=user)

    # 更新send_days字段
    settings.send_days = ["1", "5", "10", "15", "20", "25"]
    settings.save()

    # 验证保存是否成功
    settings.refresh_from_db()
    print(f"用户: {user.username}")
    print(f"更新后的send_days: {settings.send_days}")


if __name__ == "__main__":
    update_send_days()
 