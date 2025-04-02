from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

# 初期使用Django内置的User模型，不需要自定义User模型
# 随后会添加更多模型，如UserSettings、MonthlyPlan等

# 用户设置模型
class UserSettings(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='settings')
    # 敏感信息，后续在应用层处理加密
    gemini_api_key = models.CharField(max_length=255, blank=True, null=True, verbose_name='Gemini API密钥')
    email_password = models.CharField(max_length=255, blank=True, null=True, verbose_name='邮箱密码')
    
    # 个人信息
    user_name = models.CharField(max_length=50, blank=True, null=True, verbose_name='用户中文名')
    email_signature_name = models.CharField(max_length=50, blank=True, null=True, verbose_name='邮件签名名称')
    email_signature_phone = models.CharField(max_length=50, blank=True, null=True, verbose_name='邮件签名电话')
    
    # 邮件设置
    email_from = models.EmailField(blank=True, null=True, verbose_name='发件人邮箱')
    email_to = models.TextField(blank=True, null=True, help_text='多个收件人用逗号分隔', verbose_name='收件人邮箱')
    smtp_server = models.CharField(max_length=100, blank=True, null=True, verbose_name='SMTP服务器')
    smtp_port = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(65535)],
        blank=True, 
        null=True, 
        verbose_name='SMTP端口'
    )
    send_time = models.TimeField(blank=True, null=True, verbose_name='发送时间')
    is_active = models.BooleanField(default=False, verbose_name='启用报告')
    
    class Meta:
        verbose_name = '用户设置'
        verbose_name_plural = '用户设置'
    
    def __str__(self):
        return f"{self.user.username}的设置"

# 月度计划模型
class MonthlyPlan(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='monthly_plans', verbose_name='用户')
    year = models.IntegerField(verbose_name='年份', validators=[MinValueValidator(2000), MaxValueValidator(2100)])
    month = models.IntegerField(
        verbose_name='月份', 
        validators=[MinValueValidator(1), MaxValueValidator(12)]
    )
    content = models.TextField(verbose_name='计划内容')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        verbose_name = '月度计划'
        verbose_name_plural = '月度计划'
        unique_together = ('user', 'year', 'month')
        ordering = ['-year', '-month']
    
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
            plans = cls.objects.filter(user=user).order_by('-year', '-month')
            if plans.exists():
                return plans.first()
            return None
