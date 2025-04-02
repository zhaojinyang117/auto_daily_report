from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator

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
