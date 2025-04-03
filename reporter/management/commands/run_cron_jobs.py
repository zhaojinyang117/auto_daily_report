import logging
from django.core.management.base import BaseCommand
from django.core.management import call_command

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    手动运行所有注册的django-cron任务或指定任务

    用法:
    python manage.py run_cron_jobs         # 运行所有Cron作业
    python manage.py run_cron_jobs --job=reporter.send_daily_reports_job  # 运行指定作业
    """

    help = "手动执行django-cron任务"

    def add_arguments(self, parser):
        """添加命令行参数"""
        parser.add_argument(
            "--job",
            dest="job_code",
            help="要运行的特定作业代码，如不指定则运行所有作业",
        )

    def handle(self, *args, **options):
        """命令处理入口"""
        job_code = options.get("job_code")

        self.stdout.write(f"开始执行Cron作业...")

        if job_code:
            # 运行特定作业
            self.stdout.write(f"运行作业: {job_code}")
            try:
                # 直接调用runcrons命令
                call_command("runcrons", job_code, silent=False)
                self.stdout.write(self.style.SUCCESS(f"作业 {job_code} 执行完成"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"作业执行失败: {str(e)}"))
                logger.exception(f"作业 {job_code} 执行失败")
        else:
            # 运行所有作业
            self.stdout.write("运行所有作业...")
            try:
                # 直接调用runcrons命令
                call_command("runcrons", silent=False)
                self.stdout.write(self.style.SUCCESS(f"所有作业执行完成"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"作业执行失败: {str(e)}"))
                logger.exception("执行所有作业失败")

        self.stdout.write("Cron作业执行完成")
