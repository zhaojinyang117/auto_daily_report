from django import forms
from django.contrib.auth.models import User
from .models import UserSettings, MonthlyPlan


class UserSettingsForm(forms.ModelForm):
    """用户设置表单"""

    # 隐藏字段，用于存储日历选择的日期
    send_days_input = forms.CharField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = UserSettings
        fields = [
            "gemini_api_key",
            "use_client_proxy",
            "gemini_timeout",
            "email_signature_name",
            "email_signature_phone",
            "email_from",
            "email_password",
            "email_to",
            "smtp_server",
            "smtp_port",
            "send_time",
            "user_name",
            "is_active",
            "send_days",
        ]
        widgets = {
            "email_password": forms.PasswordInput(render_value=True),
            "gemini_api_key": forms.PasswordInput(render_value=True),
            "send_time": forms.TimeInput(attrs={"type": "time"}),
            # send_days字段在模板中手动处理，使用日历选择器
            "send_days": forms.HiddenInput(),
            "gemini_timeout": forms.NumberInput(
                attrs={"min": "5", "max": "60", "step": "1"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # 添加表单帮助文本
        self.fields[
            "gemini_api_key"
        ].help_text = "API密钥用于优化内容格式，请从Google AI Studio获取"
        self.fields[
            "use_client_proxy"
        ].help_text = "勾选后将使用浏览器的系统代理访问Gemini API"
        self.fields[
            "gemini_timeout"
        ].help_text = "API请求超时时间（5-60秒），如果请求经常超时，可以适当增加"
        self.fields["email_password"].help_text = "邮箱密码或授权码，用于SMTP认证"
        self.fields["smtp_server"].help_text = "例如：smtp.163.com, smtp.qq.com"
        self.fields["smtp_port"].help_text = "常用端口：25(非SSL), 465(SSL), 587(TLS)"
        self.fields["email_to"].help_text = "多个收件人请用逗号分隔"
        self.fields["send_time"].help_text = "设置自动发送报告的时间"
        self.fields["is_active"].help_text = "启用或禁用自动发送功能"

        # 设置初始值
        if self.instance and self.instance.pk and self.instance.send_days:
            self.fields["send_days_input"].initial = ",".join(
                map(str, self.instance.send_days)
            )
            print(f"初始化send_days_input: {self.fields['send_days_input'].initial}")

    def clean(self):
        cleaned_data = super().clean()
        # 从隐藏字段获取日期列表，转换为JSON格式存储
        send_days_input = cleaned_data.get("send_days_input", "")
        print(f"表单提交的send_days_input值: {send_days_input}")

        if send_days_input:
            # 将逗号分隔的字符串转换为列表
            days_list = [
                day.strip() for day in send_days_input.split(",") if day.strip()
            ]
            # 确保用户设置send_days字段的值
            cleaned_data["send_days"] = days_list
            # 直接设置表单实例的值，确保在save()时被保存
            self.instance.send_days = days_list
            print(f"处理后的send_days值: {days_list}")
        else:
            cleaned_data["send_days"] = []
            self.instance.send_days = []
            print("send_days设置为空列表")

        return cleaned_data


class MonthlyPlanForm(forms.ModelForm):
    """月度计划表单"""

    class Meta:
        model = MonthlyPlan
        fields = ["year", "month", "content"]
        widgets = {
            "content": forms.Textarea(attrs={"rows": 20, "class": "form-control"}),
            "year": forms.NumberInput(attrs={"class": "form-control"}),
            "month": forms.NumberInput(
                attrs={"class": "form-control", "min": 1, "max": 12}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 添加Bootstrap表单样式
        for field_name, field in self.fields.items():
            if isinstance(field.widget, (forms.TextInput, forms.NumberInput)):
                field.widget.attrs.update({"class": "form-control"})
            elif isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({"class": "form-control"})
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs.update({"class": "form-select"})
