from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic.edit import UpdateView, CreateView, DeleteView
from django.views.generic.list import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.utils import timezone
from .models import UserSettings, MonthlyPlan
from .forms import UserSettingsForm, MonthlyPlanForm
import re

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

class MonthlyPlanListView(LoginRequiredMixin, ListView):
    """月度计划列表视图"""
    model = MonthlyPlan
    template_name = 'reporter/monthlyplan_list.html'
    context_object_name = 'plans'
    
    def get_queryset(self):
        # 只显示当前用户的计划
        return MonthlyPlan.objects.filter(user=self.request.user).order_by('-year', '-month')

class MonthlyPlanCreateView(LoginRequiredMixin, CreateView):
    """创建月度计划视图"""
    model = MonthlyPlan
    form_class = MonthlyPlanForm
    template_name = 'reporter/monthlyplan_form.html'
    success_url = reverse_lazy('reporter:plan_list')
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, '月度计划已成功创建！')
        return super().form_valid(form)
    
    def get_initial(self):
        # 预设当前年月
        now = timezone.now()
        return {
            'year': now.year,
            'month': now.month,
        }

class MonthlyPlanUpdateView(LoginRequiredMixin, UpdateView):
    """更新月度计划视图"""
    model = MonthlyPlan
    form_class = MonthlyPlanForm
    template_name = 'reporter/monthlyplan_form.html'
    success_url = reverse_lazy('reporter:plan_list')
    
    def get_queryset(self):
        # 只允许编辑当前用户的计划
        return MonthlyPlan.objects.filter(user=self.request.user)
    
    def form_valid(self, form):
        messages.success(self.request, '月度计划已成功更新！')
        return super().form_valid(form)

class MonthlyPlanDeleteView(LoginRequiredMixin, DeleteView):
    """删除月度计划视图"""
    model = MonthlyPlan
    template_name = 'reporter/monthlyplan_confirm_delete.html'
    success_url = reverse_lazy('reporter:plan_list')
    
    def get_queryset(self):
        # 只允许删除当前用户的计划
        return MonthlyPlan.objects.filter(user=self.request.user)
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, '月度计划已成功删除！')
        return super().delete(request, *args, **kwargs)

@login_required
def extract_content_for_date(request, plan_id=None, specific_date=None):
    """提取特定日期的内容"""
    if not specific_date:
        specific_date = timezone.now().date()
    
    # 获取计划内容
    if plan_id:
        plan = get_object_or_404(MonthlyPlan, id=plan_id, user=request.user)
    else:
        plan = MonthlyPlan.get_current_or_latest_plan(request.user)
    
    if not plan:
        return render(request, 'reporter/extract_content.html', {
            'date': specific_date,
            'content': None,
            'plan': None,
            'error': '未找到月度计划'
        })
    
    # 在计划内容中查找日期标记
    date_pattern = r'<(\d{4}-\d{2}-\d{2})>(.*?)</\1>'
    matches = re.findall(date_pattern, plan.content, re.DOTALL)
    
    if not matches:
        return render(request, 'reporter/extract_content.html', {
            'date': specific_date,
            'content': None,
            'plan': plan,
            'error': '未找到任何日期标记内容'
        })
    
    # 格式化目标日期
    target_date_str = specific_date.strftime('%Y-%m-%d')
    
    # 先尝试查找精确匹配的日期
    for date_str, content in matches:
        if date_str == target_date_str:
            return render(request, 'reporter/extract_content.html', {
                'date': specific_date,
                'content': content.strip(),
                'plan': plan,
                'date_used': date_str
            })
    
    # 如果没有精确匹配，查找最近的日期
    sorted_dates = sorted([(date_str, content) for date_str, content in matches], key=lambda x: x[0])
    
    if sorted_dates:
        closest_date_str, closest_content = sorted_dates[-1]
        return render(request, 'reporter/extract_content.html', {
            'date': specific_date,
            'content': closest_content.strip(),
            'plan': plan, 
            'date_used': closest_date_str,
            'note': f"[使用{closest_date_str}的内容]"
        })
    
    return render(request, 'reporter/extract_content.html', {
        'date': specific_date,
        'content': None,
        'plan': plan,
        'error': '未找到合适的内容'
    })
