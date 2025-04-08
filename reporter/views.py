from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic.edit import UpdateView, CreateView, DeleteView
from django.views.generic.list import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.utils import timezone
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse, HttpRequest
from django.contrib.auth.views import PasswordChangeView as BasePasswordChangeView
from .models import UserSettings, MonthlyPlan, EmailLog
from .forms import UserSettingsForm, MonthlyPlanForm
from .services import (
    send_user_report,
    EmailGenerator,
    EmailSender,
    extract_content_for_date,
)
from .utils import get_relative_date_content, get_date_range
import logging
import json
from datetime import datetime, timedelta

# 配置日志
logger = logging.getLogger(__name__)

# Create your views here.


@login_required
def home(request: HttpRequest) -> HttpResponse:
    """主页视图，需要登录才能访问

    Args:
        request: HTTP请求对象

    Returns:
        HTTP响应对象
    """

    # 获取当前月份的开始和结束日期
    today = timezone.now().date()
    first_day_of_month = today.replace(day=1)

    if today.month == 12:
        next_month = 1
        next_year = today.year + 1
    else:
        next_month = today.month + 1
        next_year = today.year

    last_day_of_month = datetime(next_year, next_month, 1).date() - timedelta(days=1)

    # 获取本月邮件统计
    monthly_emails = EmailLog.objects.filter(
        user=request.user,
        send_timestamp__date__gte=first_day_of_month,
        send_timestamp__date__lte=last_day_of_month,
    )
    monthly_emails_count = monthly_emails.count()

    # 获取总邮件统计
    total_emails_count = EmailLog.objects.filter(user=request.user).count()

    # 计算成功率
    success_count = EmailLog.objects.filter(
        user=request.user, status=EmailLog.STATUS_SUCCESS
    ).count()

    success_rate = 0
    if total_emails_count > 0:
        success_rate = int((success_count / total_emails_count) * 100)

    # 生成月度图表数据
    monthly_chart_data = []

    # 获取本月每天的邮件数量
    for day in range(1, today.day + 1):
        day_date = first_day_of_month.replace(day=day)
        count = EmailLog.objects.filter(
            user=request.user, send_timestamp__date=day_date
        ).count()

        monthly_chart_data.append({"day": day_date.strftime("%d"), "count": count})

    # 将图表数据转换为JSON
    monthly_chart_data_json = json.dumps(monthly_chart_data)

    context = {
        "monthly_emails_count": monthly_emails_count,
        "total_emails_count": total_emails_count,
        "success_rate": success_rate,
        "monthly_chart_data": monthly_chart_data_json,
    }

    return render(request, "reporter/home.html", context)


@login_required
def settings_view(request):
    """用户设置视图的函数形式，会重定向到基于类的视图"""
    return redirect("reporter:settings_update")


class UserSettingsUpdateView(LoginRequiredMixin, UpdateView):
    """用户设置更新视图"""

    model = UserSettings
    form_class = UserSettingsForm
    template_name = "reporter/user_settings_form.html"
    success_url = reverse_lazy("reporter:settings_update")

    def get_object(self, queryset=None):
        # 获取或创建当前用户的设置
        try:
            return self.request.user.settings
        except UserSettings.DoesNotExist:
            return UserSettings.objects.create(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # 添加已选择日期到上下文
        settings = self.get_object()
        if settings.send_days:
            context["selected_days"] = json.dumps(settings.send_days)
            logger.info(f"当前选择的日期: {settings.send_days}")
        else:
            context["selected_days"] = json.dumps([])
            logger.info("没有选择的日期")
        return context

    def form_valid(self, form):
        logger.info(f"表单数据: {form.cleaned_data}")
        if "send_days" in form.cleaned_data:
            logger.info(f"提交的send_days: {form.cleaned_data['send_days']}")
        if "send_days_input" in form.cleaned_data:
            logger.info(
                f"提交的send_days_input: {form.cleaned_data['send_days_input']}"
            )

        # 确保表单实例上的send_days值已设置
        if hasattr(form.instance, "send_days"):
            logger.info(f"表单实例的send_days值: {form.instance.send_days}")

        response = super().form_valid(form)

        # 更新后再次检查用户设置
        settings = UserSettings.objects.get(user=self.request.user)
        logger.info(f"保存后的send_days值: {settings.send_days}")

        messages.success(self.request, "设置已成功保存！")
        return response

    def form_invalid(self, form):
        logger.error(f"表单验证失败: {form.errors}")
        return super().form_invalid(form)


class MonthlyPlanListView(LoginRequiredMixin, ListView):
    """月度计划列表视图"""

    model = MonthlyPlan
    template_name = "reporter/monthlyplan_list.html"
    context_object_name = "plans"

    def get_queryset(self):
        # 只显示当前用户的计划
        return MonthlyPlan.objects.filter(user=self.request.user).order_by(
            "-year", "-month"
        )


class MonthlyPlanCreateView(LoginRequiredMixin, CreateView):
    """创建月度计划视图"""

    model = MonthlyPlan
    form_class = MonthlyPlanForm
    template_name = "reporter/monthlyplan_form.html"
    success_url = reverse_lazy("reporter:plan_list")

    def form_valid(self, form):
        form.instance.user = self.request.user

        # 检查是否已存在相同月份的计划
        year = form.cleaned_data.get("year")
        month = form.cleaned_data.get("month")
        existing_plan = MonthlyPlan.objects.filter(
            user=self.request.user, year=year, month=month
        ).first()

        if existing_plan:
            # 如果已存在，告知用户并提供选择
            messages.warning(
                self.request,
                f"{year}年{month}月的计划已存在。请编辑现有计划，或者选择不同的月份。",
            )
            return redirect("reporter:plan_update", pk=existing_plan.pk)

        messages.success(self.request, "月度计划已成功创建！")
        return super().form_valid(form)

    def get_initial(self):
        # 预设当前年月
        now = timezone.now()
        return {
            "year": now.year,
            "month": now.month,
        }


class MonthlyPlanUpdateView(LoginRequiredMixin, UpdateView):
    """更新月度计划视图"""

    model = MonthlyPlan
    form_class = MonthlyPlanForm
    template_name = "reporter/monthlyplan_form.html"
    success_url = reverse_lazy("reporter:plan_list")

    def get_queryset(self):
        # 只允许编辑当前用户的计划
        return MonthlyPlan.objects.filter(user=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, "月度计划已成功更新！")
        return super().form_valid(form)


class MonthlyPlanDeleteView(LoginRequiredMixin, DeleteView):
    """删除月度计划视图"""

    model = MonthlyPlan
    template_name = "reporter/monthlyplan_confirm_delete.html"
    success_url = reverse_lazy("reporter:plan_list")

    def get_queryset(self):
        # 只允许删除当前用户的计划
        return MonthlyPlan.objects.filter(user=self.request.user)

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "月度计划已成功删除！")
        return super().delete(request, *args, **kwargs)


@login_required
def extract_content_view(request, plan_id=None, specific_date=None):
    """提取特定日期的内容视图"""
    if not specific_date:
        specific_date = timezone.now().date()

    # 获取计划内容
    if plan_id:
        plan = get_object_or_404(MonthlyPlan, id=plan_id, user=request.user)
    else:
        try:
            # 尝试获取与日期匹配的月度计划
            plan = MonthlyPlan.objects.get(
                user=request.user, year=specific_date.year, month=specific_date.month
            )
        except MonthlyPlan.DoesNotExist:
            # 如果找不到当前月份的计划，尝试获取最新的计划
            plan = (
                MonthlyPlan.objects.filter(user=request.user)
                .order_by("-year", "-month")
                .first()
            )

    if not plan:
        return render(
            request,
            "reporter/extract_content.html",
            {
                "date": specific_date,
                "content": None,
                "plan": None,
                "error": "未找到月度计划",
            },
        )

    # 使用工具函数查找日期内容
    content, date_used = get_relative_date_content(plan.content, specific_date)

    if content:
        context = {
            "date": specific_date,
            "content": content,
            "plan": plan,
            "date_used": date_used,
        }

        # 如果使用的日期与请求的日期不同，添加提示
        if date_used != specific_date.strftime("%Y-%m-%d"):
            context["note"] = f"[使用{date_used}的内容]"

        # 检查是否需要使用Gemini处理内容
        # 获取用户设置
        try:
            user_settings = UserSettings.objects.get(user=request.user)
            if user_settings.gemini_api_key and user_settings.use_client_proxy:
                # 如果设置了API密钥且启用了客户端代理
                try:
                    from reporter.services import GeminiProcessor

                    gemini_processor = GeminiProcessor(
                        user_settings.gemini_api_key,
                        use_client_proxy=user_settings.use_client_proxy,
                        use_hf_proxy=user_settings.use_hf_proxy,
                    )
                    # 获取处理结果
                    result = gemini_processor.format_learning_summary(content)

                    # 检查结果是否为客户端代理模式的数据
                    if isinstance(result, dict) and result.get("use_client_proxy"):
                        # 将API数据添加到上下文，以便在模板中使用
                        import json

                        context["client_proxy_data"] = json.dumps(result)
                except Exception as e:
                    logger.exception(f"准备客户端代理数据时发生错误: {str(e)}")
        except UserSettings.DoesNotExist:
            pass  # 如果用户设置不存在，忽略Gemini处理

        return render(request, "reporter/extract_content.html", context)

    return render(
        request,
        "reporter/extract_content.html",
        {
            "date": specific_date,
            "content": None,
            "plan": plan,
            "error": "未找到合适的内容",
        },
    )


@login_required
def send_report(request: HttpRequest) -> HttpResponse:
    """手动触发发送报告"""
    logger.info(
        f"收到发送报告请求，方法: {request.method}, 内容类型: {request.content_type}"
    )

    # 查看POST数据
    if request.method == "POST":
        logger.info(f"POST数据: {request.POST}")
        logger.info(f"POST包含processed_content: {'processed_content' in request.POST}")
        logger.info(f"请求头: {dict(request.headers)}")

    try:
        # 检查是否是POST请求且包含processed_content（来自客户端代理处理）
        if request.method == "POST" and "processed_content" in request.POST:
            logger.info("收到客户端代理处理后的内容，准备发送邮件")

            # 获取处理后的内容
            processed_content = request.POST.get("processed_content")
            logger.info(
                f"收到处理后内容，长度: {len(processed_content) if processed_content else 0}"
            )

            # 获取日期参数（如果有的话）
            specific_date = None
            date_str = request.GET.get("date")
            if date_str:
                try:
                    specific_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                    logger.info(f"使用指定日期: {specific_date}")
                except Exception as e:
                    logger.warning(f"日期格式转换错误: {e}")

            # 获取用户设置
            try:
                user_settings = UserSettings.objects.get(user=request.user)

                # 生成邮件内容
                email_generator = EmailGenerator(
                    user_settings, specific_date or timezone.now().date()
                )
                subject = email_generator.get_email_subject()
                html_content = email_generator.generate_email_html(processed_content)

                # 发送邮件
                email_sender = EmailSender(user_settings)
                if email_sender.send_email(subject, html_content):
                    # 记录成功日志
                    content_preview = processed_content
                    if content_preview and len(content_preview) > 500:
                        content_preview = content_preview[:500] + "..."

                    EmailLog.objects.create(
                        user=request.user,
                        status=EmailLog.STATUS_SUCCESS,
                        subject=subject,
                        content_preview=content_preview,
                    )

                    logger.info("邮件发送成功")

                    # AJAX请求返回JSON响应
                    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                        return JsonResponse(
                            {
                                "success": True,
                                "message": f"报告已成功发送至 {user_settings.email_to}",
                            }
                        )

                    # 非AJAX请求重定向并显示成功消息
                    messages.success(
                        request, f"报告已成功发送至 {user_settings.email_to}"
                    )
                    return redirect("reporter:home")
                else:
                    # 邮件发送失败
                    error_msg = "邮件发送失败，请检查邮箱设置"
                    logger.error(error_msg)

                    # 记录失败日志
                    EmailLog.objects.create(
                        user=request.user,
                        status=EmailLog.STATUS_FAILED,
                        subject=subject,
                        error_message=error_msg,
                    )

                    # AJAX请求返回JSON错误响应
                    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                        return JsonResponse({"success": False, "message": error_msg})

                    # 非AJAX请求显示错误消息
                    messages.error(request, error_msg)
            except UserSettings.DoesNotExist:
                # 设置不存在
                error_msg = "用户设置不存在，请先完成设置"
                logger.error(error_msg)

                # AJAX请求返回JSON错误响应
                if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                    return JsonResponse({"success": False, "message": error_msg})

                # 非AJAX请求显示错误消息
                messages.error(request, error_msg)
        else:
            # 非POST请求，直接调用服务函数
            result = send_user_report(request.user, force_send=True)
            logger.info(f"调用send_user_report结果: {result}")

            if result["success"]:
                messages.success(request, result["message"])
            else:
                if "client_proxy_data" in result:
                    # 需要客户端处理的情况，重定向到内容提取页面
                    return redirect("reporter:extract_content")
                messages.error(request, result["message"])
    except Exception as e:
        logger.exception(f"发送报告时发生错误: {e}")
        error_msg = f"发送报告时出错：{str(e)}"

        # AJAX请求返回JSON错误响应
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"success": False, "message": error_msg})

        # 非AJAX请求显示错误消息
        messages.error(request, error_msg)

    return redirect("reporter:home")


@login_required
def email_history(request: HttpRequest) -> HttpResponse:
    """显示邮件发送历史记录

    Args:
        request: HTTP请求对象

    Returns:
        HTTP响应对象
    """
    # 获取查询参数
    days = request.GET.get("days", "7")  # 默认显示7天
    try:
        days = int(days)
        if days <= 0:
            days = 7
    except ValueError:
        days = 7

    # 计算日期范围
    end_date = timezone.now()
    start_date = end_date - timedelta(days=days)

    # 获取历史记录
    logs = EmailLog.objects.filter(
        user=request.user, send_timestamp__gte=start_date, send_timestamp__lte=end_date
    ).order_by("-send_timestamp")

    # 统计数据
    stats = {
        "total": logs.count(),
        "success": logs.filter(status=EmailLog.STATUS_SUCCESS).count(),
        "failed": logs.filter(status=EmailLog.STATUS_FAILED).count(),
        "no_content": logs.filter(status=EmailLog.STATUS_NO_CONTENT).count(),
    }

    context = {
        "logs": logs,
        "stats": stats,
        "days": days,
        "start_date": start_date,
        "end_date": end_date,
    }

    return render(request, "reporter/email_history.html", context)


class PasswordChangeView(LoginRequiredMixin, BasePasswordChangeView):
    """密码修改视图"""

    template_name = "reporter/password_change_form.html"
    success_url = reverse_lazy("reporter:password_change_done")

    def form_valid(self, form):
        messages.success(self.request, "密码已成功修改！")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "密码修改失败，请检查输入！")
        return super().form_invalid(form)
