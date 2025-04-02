import logging
from datetime import datetime, time
from typing import Any, Dict, List, Optional

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Q

from reporter.models import UserSettings
from reporter.services import send_user_report

# 配置日志
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    发送每日报告的Django管理命令

    用法:
    python manage.py send_daily_reports         # 检查并发送当前时间窗口内应发送的报告
    python manage.py send_daily_reports --all   # 忽略时间设置，发送所有活跃用户的报告
    python manage.py send_daily_reports --user=username  # 发送指定用户的报告
    """

    help = "根据用户设置的时间发送每日报告"

    def add_arguments(self, parser):
        """添加命令行参数"""
        parser.add_argument(
            "--all",
            action="store_true",
            dest="all",
            help="发送所有活跃用户的报告，忽略时间设置",
        )
        parser.add_argument(
            "--user",
            dest="username",
            help="指定要发送报告的用户名",
        )

    def handle(self, *args, **options):
        """命令处理入口"""
        # 获取当前日期和时间
        now = timezone.now()
        current_time = now.time()
        current_date = now.date()

        # 记录开始执行
        self.stdout.write(f"开始执行日报发送任务: {now.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"开始执行日报发送任务: {now.strftime('%Y-%m-%d %H:%M:%S')}")

        # 处理单个用户的情况
        if options["username"]:
            self.process_specific_user(options["username"])
            return

        # 获取需要发送报告的用户
        if options["all"]:
            # 获取所有活跃用户
            users_to_process = self._get_all_active_users()
            self.stdout.write(f"将处理所有活跃用户: {len(users_to_process)}个")
        else:
            # 获取当前时间窗口需要发送的用户
            users_to_process = self._get_users_for_current_time(current_time)
            self.stdout.write(
                f"当前时间窗口({current_time.strftime('%H:%M')})内有{len(users_to_process)}个用户需要处理"
            )

        # 处理用户报告
        success_count = 0
        fail_count = 0

        for user in users_to_process:
            try:
                result = self.process_user_report(user)
                if result["success"]:
                    success_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f"用户[{user.username}]报告发送成功")
                    )
                else:
                    fail_count += 1
                    self.stdout.write(
                        self.style.WARNING(
                            f"用户[{user.username}]报告发送失败: {result['message']}"
                        )
                    )
            except Exception as e:
                fail_count += 1
                logger.exception(f"处理用户[{user.username}]报告时发生异常")
                self.stdout.write(
                    self.style.ERROR(f"处理用户[{user.username}]时发生错误: {str(e)}")
                )

        # 输出汇总信息
        self.stdout.write("-" * 50)
        self.stdout.write(
            f"任务完成，成功: {success_count}，失败: {fail_count}，总计: {len(users_to_process)}"
        )
        logger.info(
            f"日报发送任务完成，成功: {success_count}，失败: {fail_count}，总计: {len(users_to_process)}"
        )

    def process_specific_user(self, username: str) -> None:
        """处理特定用户的报告

        Args:
            username: 用户名
        """
        try:
            user = User.objects.get(username=username)

            # 检查用户是否有活跃的设置
            try:
                settings = UserSettings.objects.get(user=user)
                if not settings.is_active:
                    self.stdout.write(
                        self.style.WARNING(f"用户[{username}]的报告功能未激活")
                    )
                    return
            except UserSettings.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"用户[{username}]没有设置"))
                return

            # 发送报告
            result = self.process_user_report(user)

            if result["success"]:
                self.stdout.write(self.style.SUCCESS(f"用户[{username}]的报告发送成功"))
            else:
                self.stdout.write(
                    self.style.ERROR(
                        f"用户[{username}]的报告发送失败: {result['message']}"
                    )
                )

        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"用户[{username}]不存在"))

    def process_user_report(self, user: User) -> Dict[str, Any]:
        """处理单个用户的报告

        Args:
            user: 用户对象

        Returns:
            包含处理结果的字典
        """
        self.stdout.write(f"正在处理用户[{user.username}]的报告...")
        logger.info(f"开始为用户[{user.username}]生成发送报告")

        # 调用服务函数发送报告
        result = send_user_report(user)

        # 记录结果
        message = result["message"]
        if result["success"]:
            logger.info(f"用户[{user.username}]报告发送成功: {message}")
        else:
            logger.warning(f"用户[{user.username}]报告发送失败: {message}")

        return result

    def _get_all_active_users(self) -> List[User]:
        """获取所有活跃用户

        Returns:
            包含所有活跃用户的列表
        """
        return User.objects.filter(
            usersettings__is_active=True,
        ).distinct()

    def _get_users_for_current_time(self, current_time: time) -> List[User]:
        """获取当前时间窗口应该发送报告的用户

        当前策略:
        1. 用户设置必须是激活状态
        2. 用户设置的发送时间与当前小时相同
        3. 当前日期必须在用户的send_days设置中（如果设置了的话）

        Args:
            current_time: 当前时间

        Returns:
            应该在当前时间窗口处理的用户列表
        """
        # 获取当前日期
        today = timezone.now().date()
        current_day = str(today.day)

        # 查询条件：活跃用户且发送时间小时与当前时间相符
        base_query = Q(
            usersettings__is_active=True,
            usersettings__send_time__hour=current_time.hour,
        )

        # 添加send_days过滤条件
        # 获取所有符合基本条件的用户
        base_users = User.objects.filter(base_query).distinct()

        # 最终要发送的用户列表
        final_users = []

        for user in base_users:
            try:
                user_settings = UserSettings.objects.get(user=user)
                # 如果用户没有设置send_days或当前日期在send_days中，则添加到最终列表
                if (
                    not user_settings.send_days
                    or current_day in user_settings.send_days
                ):
                    final_users.append(user)
                    logger.info(f"用户[{user.username}]将在当前时间窗口接收报告")
                else:
                    logger.info(
                        f"用户[{user.username}]设置了send_days={user_settings.send_days}，当前日期{current_day}不在发送列表中，跳过"
                    )
            except UserSettings.DoesNotExist:
                # 理论上不会出现这种情况，因为base_query已经过滤过了
                logger.warning(f"用户[{user.username}]查询设置时出错，跳过该用户")
                continue

        return final_users
