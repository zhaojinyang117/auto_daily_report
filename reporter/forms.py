from django import forms
from django.contrib.auth.models import User
from .models import UserSettings, MonthlyPlan

class UserSettingsForm(forms.ModelForm):
    class Meta:
        model = UserSettings
        exclude = ['user']
        widgets = {
            'gemini_api_key': forms.PasswordInput(render_value=True),
            'email_password': forms.PasswordInput(render_value=True),
            'send_time': forms.TimeInput(attrs={'type': 'time'}),
            'email_to': forms.Textarea(attrs={'rows': 3}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 添加Bootstrap表单样式
        for field_name, field in self.fields.items():
            if isinstance(field.widget, (forms.TextInput, forms.EmailInput, forms.PasswordInput, forms.NumberInput, forms.TimeInput)):
                field.widget.attrs.update({'class': 'form-control'})
            elif isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({'class': 'form-control'})
            elif isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-check-input'})
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs.update({'class': 'form-select'})

class MonthlyPlanForm(forms.ModelForm):
    class Meta:
        model = MonthlyPlan
        fields = ['year', 'month', 'content']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 15, 'placeholder': '使用如下格式输入月度计划：\n\n<月度计划：YYYY-MM>\n\n<YYYY-MM-DD>\n今日学习内容\n</YYYY-MM-DD>\n\n<YYYY-MM-DD>\n今日学习内容\n</YYYY-MM-DD>'}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 添加Bootstrap表单样式
        for field_name, field in self.fields.items():
            if isinstance(field.widget, (forms.TextInput, forms.NumberInput)):
                field.widget.attrs.update({'class': 'form-control'})
            elif isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({'class': 'form-control'})
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs.update({'class': 'form-select'}) 