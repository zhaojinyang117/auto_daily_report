import logging
import random
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from reporter.models import EmailLog

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    为测试目的创建EmailLog记录

    用法:
    python manage.py test_email_log                     # 为所有用户创建随机日志记录
    python manage.py test_email_log --user=username     # 为特定用户创建记录
    python manage.py test_email_log --count=10          # 创建10条记录
    python manage.py test_email_log --days=7            # 创建过去7天的记录
    """

    help = "为测试目的创建EmailLog记录"

    def add_arguments(self, parser):
        """添加命令行参数"""
        parser.add_argument("--user", dest="username", help="指定用户名")
        parser.add_argument("--count", type=int, default=10, help="创建的记录数量")
        parser.add_argument("--days", type=int, default=7, help="记录跨越的天数")

    def handle(self, *args, **options):
        """命令处理入口"""
        username = options.get("username")
        count = options.get("count", 10)
        days = options.get("days", 7)

        # 获取需要创建记录的用户
        if username:
            try:
                users = [User.objects.get(username=username)]
                self.stdout.write(f"将为用户 {username} 创建测试记录")
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"用户 {username} 不存在"))
                return
        else:
            users = User.objects.all()
            self.stdout.write(f"将为所有用户({len(users)}个)创建测试记录")

        # 创建记录
        total_created = 0

        for user in users:
            # 每个用户创建count条记录
            logs_created = self.create_logs_for_user(user, count, days)
            total_created += logs_created
            self.stdout.write(
                f"为用户 {user.username} 创建了 {logs_created} 条测试记录"
            )

        self.stdout.write(self.style.SUCCESS(f"总共创建了 {total_created} 条测试记录"))

    def create_logs_for_user(self, user, count, days):
        """为指定用户创建EmailLog记录

        Args:
            user: 用户对象
            count: 记录数量
            days: 记录跨越的天数

        Returns:
            创建的记录数量
        """
        # 删除之前可能存在的测试记录
        old_test_logs = EmailLog.objects.filter(user=user, subject__startswith="[测试]")
        old_count = old_test_logs.count()
        if old_count > 0:
            old_test_logs.delete()
            self.stdout.write(f"删除了 {old_count} 条旧测试记录")

        # 创建新记录
        created_count = 0
        now = timezone.now()

        for i in range(count):
            # 随机状态
            status_choices = [
                EmailLog.STATUS_SUCCESS,
                EmailLog.STATUS_FAILED,
                EmailLog.STATUS_NO_CONTENT,
            ]
            status = random.choice(status_choices)

            # 随机时间（过去days天内）
            random_days = random.randint(0, days - 1)
            random_hours = random.randint(0, 23)
            random_minutes = random.randint(0, 59)
            timestamp = now - timedelta(
                days=random_days, hours=random_hours, minutes=random_minutes
            )

            # 创建日志记录
            log = EmailLog(
                user=user,
                send_timestamp=timestamp,
                status=status,
                subject=f"[测试] 日报: {timestamp.strftime('%Y-%m-%d')}",
            )

            # 根据状态设置不同字段
            if status == EmailLog.STATUS_SUCCESS:
                log.content_preview = f"这是一个测试日报内容预览，生成于 {timestamp.strftime('%Y-%m-%d %H:%M:%S')}。\n\n"
                log.content_preview += "1. 今天学习了Python的高级特性\n2. 完成了Django项目的模型设计\n3. 阅读了《流畅的Python》第5章"
            elif status == EmailLog.STATUS_FAILED:
                log.error_message = random.choice(
                    [
                        "SMTP服务器连接失败",
                        "邮箱密码不正确",
                        "发送超时",
                        "收件人地址格式不正确",
                        "API调用失败: 请求超时",
                    ]
                )
            elif status == EmailLog.STATUS_NO_CONTENT:
                log.error_message = "该日期没有学习内容记录"

            log.save()
            created_count += 1

        return created_count
 