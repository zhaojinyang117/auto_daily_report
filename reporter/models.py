from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

# 初期使用Django内置的User模型，不需要自定义User模型
# 随后会添加更多模型，如UserSettings、MonthlyPlan等


# 用户设置模型
class UserSettings(models.Model):
    """用户设置模型，存储用户的API密钥和邮件设置"""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="settings")

    # API设置
    gemini_api_key = models.CharField(
        max_length=100, blank=True, null=True, help_text="Gemini API密钥"
    )
    use_client_proxy = models.BooleanField(
        default=False, help_text="使用客户端代理访问Gemini API"
    )
    use_hf_proxy = models.BooleanField(
        default=True, help_text="使用HuggingFace代理绕过Gemini地域限制"
    )
    gemini_timeout = models.IntegerField(
        default=15, help_text="Gemini API请求超时时间（秒）"
    )

    # 邮件签名
    email_signature_name = models.CharField(
        max_length=50, blank=True, null=True, help_text="邮件签名姓名"
    )
    email_signature_phone = models.CharField(
        max_length=20, blank=True, null=True, help_text="邮件签名电话"
    )

    # 邮件发送配置
    email_from = models.EmailField(blank=True, null=True, help_text="发件人邮箱")
    email_password = models.CharField(
        max_length=100, blank=True, null=True, help_text="邮箱密码/授权码"
    )
    email_to = models.CharField(
        max_length=200, blank=True, null=True, help_text="收件人邮箱，多个用逗号分隔"
    )

    # SMTP服务器设置
    smtp_server = models.CharField(
        max_length=100, blank=True, null=True, help_text="SMTP服务器地址"
    )
    smtp_port = models.IntegerField(blank=True, null=True, help_text="SMTP服务器端口")

    # 报告配置
    send_time = models.TimeField(blank=True, null=True, help_text="每日发送时间")
    user_name = models.CharField(
        max_length=50, blank=True, null=True, help_text="用户中文名，用于邮件标题"
    )
    is_active = models.BooleanField(default=False, help_text="是否启用自动发送")

    # 发送日期配置 (JSON格式存储，例如: ["1","5","10","15","20","25"])
    send_days = models.JSONField(
        blank=True,
        null=True,
        default=list,
        help_text="每月需要发送报告的日期，JSON数组格式",
    )

    class Meta:
        verbose_name = "用户设置"
        verbose_name_plural = "用户设置"

    def __str__(self):
        return f"{self.user.username}的设置"


# 月度计划模型
class MonthlyPlan(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="monthly_plans",
        verbose_name="用户",
    )
    year = models.IntegerField(
        verbose_name="年份",
        validators=[MinValueValidator(2000), MaxValueValidator(2100)],
    )
    month = models.IntegerField(
        verbose_name="月份", validators=[MinValueValidator(1), MaxValueValidator(12)]
    )
    content = models.TextField(verbose_name="计划内容")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        verbose_name = "月度计划"
        verbose_name_plural = "月度计划"
        unique_together = ("user", "year", "month")
        ordering = ["-year", "-month"]

    def __str__(self):
        return f"{self.user.username}的{self.year}年{self.month}月计划"

    @classmethod
    def get_current_or_latest_plan(cls, user):
        """获取当前月份的计划，如果不存在则返回最近的计划"""
        now = timezone.now()
        current_year, current_month = now.year, now.month

        # 尝试获取当前月份的计划
        try:
            return cls.objects.get(user=user, year=current_year, month=current_month)
        except cls.DoesNotExist:
            # 如果不存在，尝试获取最近的计划
            plans = cls.objects.filter(user=user).order_by("-year", "-month")
            if plans.exists():
                return plans.first()
            return None


# 邮件日志模型
class EmailLog(models.Model):
    """邮件发送日志模型，记录邮件发送历史"""

    # 状态选项
    STATUS_SUCCESS = "Success"
    STATUS_FAILED = "Failed"
    STATUS_NO_CONTENT = "No Content"

    STATUS_CHOICES = [
        (STATUS_SUCCESS, "成功"),
        (STATUS_FAILED, "失败"),
        (STATUS_NO_CONTENT, "无内容"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="email_logs",
        verbose_name="用户",
    )
    send_timestamp = models.DateTimeField(auto_now_add=True, verbose_name="发送时间")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_SUCCESS,
        verbose_name="状态",
    )
    subject = models.CharField(max_length=200, blank=True, verbose_name="邮件主题")
    content_preview = models.TextField(blank=True, verbose_name="内容预览")
    error_message = models.TextField(blank=True, null=True, verbose_name="错误信息")
    is_scheduled = models.BooleanField(default=False, null=True, blank=True, verbose_name="定时发送")

    class Meta:
        verbose_name = "邮件日志"
        verbose_name_plural = "邮件日志"
        ordering = ["-send_timestamp"]

    def __str__(self):
        return f"{self.user.username}的邮件 - {self.send_timestamp.strftime('%Y-%m-%d %H:%M')} - {self.get_status_display()}"

    @property
    def short_content(self):
        """返回内容的简短预览"""
        if not self.content_preview:
            return ""
        if len(self.content_preview) > 100:
            return f"{self.content_preview[:100]}..."
        return self.content_preview
