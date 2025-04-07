import logging
from datetime import time
from typing import List, Optional
import pytz

from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Q
from django_cron import CronJobBase, Schedule
from django.conf import settings

from reporter.models import UserSettings
from reporter.services import send_user_report

# 配置日志
logger = logging.getLogger(__name__)


class SendDailyReportsCronJob(CronJobBase):
    """
    使用django-cron框架的每日报告定时任务

    此作业会检查当前时间窗口内需要发送报告的用户，并为他们生成和发送报告。
    作业每5分钟运行一次，确保能够捕获所有的预定时间。
    """

    RUN_EVERY_MINS = 5  # 每5分钟运行一次

    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = "reporter.send_daily_reports_job"  # 用于在数据库中标识作业的唯一代码

    def do(self):
        """
        执行定时任务的方法，由django-cron框架自动调用

        此方法检查当前时间窗口内需要发送报告的用户，并执行发送操作。
        成功时返回True，并记录统计信息。
        """
        # 获取当前日期和时间（使用设置的时区）
        now = timezone.now()
        local_now = now.astimezone(pytz.timezone(settings.TIME_ZONE))
        current_time = local_now.time()
        current_date = local_now.date()

        # 记录开始执行
        logger.info(f"开始执行日报发送任务: {local_now.strftime('%Y-%m-%d %H:%M:%S')}")

        # 获取当前时间窗口需要发送的用户
        users_to_process = self._get_users_for_current_time(current_time)
        logger.info(
            f"当前时间窗口({current_time.strftime('%H:%M')})内有{len(users_to_process)}个用户需要处理"
        )

        # 处理用户报告
        success_count = 0
        fail_count = 0

        for user in users_to_process:
            try:
                result = self._process_user_report(user)
                if result["success"]:
                    success_count += 1
                    logger.info(f"用户[{user.username}]报告发送成功")
                else:
                    fail_count += 1
                    logger.warning(
                        f"用户[{user.username}]报告发送失败: {result['message']}"
                    )
            except Exception as e:
                fail_count += 1
                logger.exception(f"处理用户[{user.username}]报告时发生异常: {str(e)}")

        # 输出汇总信息
        logger.info(
            f"日报发送任务完成，成功: {success_count}，失败: {fail_count}，总计: {len(users_to_process)}"
        )

        # 返回操作结果
        return True

    def _process_user_report(self, user: User):
        """处理单个用户的报告"""
        logger.info(f"开始为用户[{user.username}]生成发送报告")

        # 调用服务函数发送报告，标记为定时发送
        result = send_user_report(user, is_scheduled=True)

        # 记录结果
        message = result["message"]
        if result["success"]:
            logger.info(f"用户[{user.username}]报告发送成功: {message}")
        else:
            logger.warning(f"用户[{user.username}]报告发送失败: {message}")

        return result

    def _get_users_for_current_time(self, current_time: time) -> List[User]:
        """获取当前时间窗口应该发送报告的用户

        当前策略:
        1. 用户设置必须是激活状态
        2. 用户设置的发送时间与当前小时相同
        3. 当前日期必须在用户的send_days设置中（如果设置了的话）
        4. 当前分钟必须在用户设置的发送时间的分钟到分钟+5的范围内

        Args:
            current_time: 当前时间

        Returns:
            应该在当前时间窗口处理的用户列表
        """
        # 获取当前日期（使用设置的时区）
        now = timezone.now()
        local_now = now.astimezone(pytz.timezone(settings.TIME_ZONE))
        today = local_now.date()
        current_day = str(today.day)
        local_hour = local_now.hour
        local_minute = local_now.minute

        logger.info(f"UTC时间: {now}, 本地时间: {local_now}, 本地小时: {local_hour}, 本地分钟: {local_minute}")

        # 查询条件：活跃用户且发送时间小时与当前本地时间相符
        base_query = Q(
            settings__is_active=True,
            settings__send_time__hour=local_hour,
        )

        # 获取所有符合基本条件的用户
        base_users = User.objects.filter(base_query).distinct()

        # 最终要发送的用户列表
        final_users = []

        for user in base_users:
            try:
                user_settings = UserSettings.objects.get(user=user)

                # 检查当前分钟是否在用户设置的发送时间的分钟到分钟+5的范围内
                user_minute = user_settings.send_time.minute
                # 如果当前分钟不在用户设置的发送时间的分钟到分钟+5的范围内，则跳过
                if not (user_minute <= local_minute < user_minute + 5):
                    logger.info(
                        f"用户[{user.username}]设置的发送时间分钟为{user_minute}，当前分钟{local_minute}不在发送时间窗口内，跳过"
                    )
                    continue

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
