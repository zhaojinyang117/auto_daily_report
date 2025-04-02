from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic.edit import UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from .models import UserSettings
from .forms import UserSettingsForm

# Create your views here.

@login_required
def home(request):
    """主页视图，需要登录才能访问"""
    return render(request, 'reporter/home.html')

class UserSettingsUpdateView(LoginRequiredMixin, UpdateView):
    """用户设置更新视图"""
    model = UserSettings
    form_class = UserSettingsForm
    template_name = 'reporter/user_settings_form.html'
    success_url = reverse_lazy('reporter:settings')
    
    def get_object(self, queryset=None):
        # 获取或创建当前用户的设置
        obj, created = UserSettings.objects.get_or_create(user=self.request.user)
        return obj
    
    def form_valid(self, form):
        messages.success(self.request, '设置已成功保存！')
        return super().form_valid(form)

@login_required
def settings_view(request):
    """用户设置视图的函数形式，会重定向到基于类的视图"""
    return redirect('reporter:settings_update')
