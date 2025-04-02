from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic.edit import UpdateView, CreateView, DeleteView
from django.views.generic.list import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.utils import timezone
from django.http import HttpResponseRedirect, JsonResponse
from .models import UserSettings, MonthlyPlan
from .forms import UserSettingsForm, MonthlyPlanForm
from .services import send_user_report, EmailGenerator, EmailSender
from .utils import extract_content_for_date, get_relative_date_content
import logging
import json

# 配置日志
logger = logging.getLogger(__name__)

# Create your views here.


@login_required
def home(request):
    """主页视图，需要登录才能访问"""
    return render(request, "reporter/home.html")


@login_required
def settings_view(request):
    """用户设置视图的函数形式，会重定向到基于类的视图"""
    return redirect("reporter:settings_update")


class UserSettingsUpdateView(LoginRequiredMixin, UpdateView):
    """用户设置更新视图"""

    model = UserSettings
    form_class = UserSettingsForm
    template_name = "reporter/user_settings_form.html"
    success_url = reverse_lazy("reporter:home")

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
def send_report(request):
    """手动发送日报"""
    try:
        # 获取用户设置
        try:
            user_settings = UserSettings.objects.get(user=request.user)
            # 检查是否是AJAX请求
            is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

            # 获取日期信息
            specific_date = None
            date_str = request.GET.get("date")
            if date_str:
                try:
                    import datetime

                    specific_date = datetime.datetime.strptime(
                        date_str, "%Y-%m-%d"
                    ).date()
                    logger.info(f"使用指定日期: {specific_date}")
                except Exception as e:
                    logger.warning(f"日期格式转换错误: {e}")

            # 处理客户端代理模式下的POST请求(处理后的内容)
            if request.method == "POST" and is_ajax and user_settings.use_client_proxy:
                logger.info("收到客户端代理模式的POST请求，包含处理后的内容")

                # 获取处理后的内容
                processed_content = request.POST.get("processed_content")
                if not processed_content:
                    # 可能FormData有问题，尝试从请求体中获取
                    logger.warning(
                        "从POST参数中未找到processed_content，尝试从请求体中获取"
                    )
                    try:
                        import json

                        body = json.loads(request.body.decode("utf-8"))
                        processed_content = body.get("processed_content")
                    except Exception as e:
                        logger.error(f"解析请求体出错: {e}")

                if not processed_content:
                    logger.error("未能获取到处理后的内容")
                    return JsonResponse(
                        {"success": False, "message": "未能获取到处理后的内容，请重试"}
                    )

                # 从月度计划中提取原始内容，但不使用它
                try:
                    monthly_plan = MonthlyPlan.objects.get(
                        user=request.user,
                        year=specific_date.year,
                        month=specific_date.month,
                    )

                    # 提取内容，但我们不使用它，只是为了验证内容存在
                    content = extract_content_for_date(
                        monthly_plan.content, specific_date
                    )
                    if not content:
                        logger.warning(
                            f"在 {specific_date} 未找到学习内容，但仍然继续处理"
                        )
                except MonthlyPlan.DoesNotExist:
                    logger.warning(
                        f"未找到 {specific_date.year}年{specific_date.month}月 的月度计划，但仍然继续处理"
                    )

                # 检查邮箱配置是否完整
                if (
                    not user_settings.email_from
                    or not user_settings.email_password
                    or not user_settings.email_to
                    or not user_settings.smtp_server
                    or not user_settings.smtp_port
                ):
                    return JsonResponse(
                        {
                            "success": False,
                            "message": "邮箱配置不完整，请在设置中完成配置",
                        }
                    )

                # 生成邮件内容
                email_generator = EmailGenerator(user_settings, specific_date)
                subject = email_generator.get_email_subject()

                # 使用前端处理后的内容生成HTML邮件
                html_content = email_generator.generate_email_html(processed_content)

                # 发送邮件
                email_sender = EmailSender(user_settings)
                if email_sender.send_email(subject, html_content):
                    logger.info(
                        f"使用客户端处理内容成功发送邮件至 {user_settings.email_to}"
                    )
                    return JsonResponse(
                        {
                            "success": True,
                            "message": f"报告已成功发送至 {user_settings.email_to}",
                        }
                    )
                else:
                    logger.error("邮件发送失败")
                    return JsonResponse(
                        {"success": False, "message": "邮件发送失败。请检查邮箱设置。"}
                    )

            # 客户端代理模式下的GET请求处理
            elif user_settings.gemini_api_key and user_settings.use_client_proxy:
                # 客户端代理模式下，不直接发送邮件，重定向到提取内容页面
                if not is_ajax:
                    messages.info(
                        request, "使用客户端代理模式，请在内容页面手动处理并发送。"
                    )
                    return redirect("reporter:extract_content")
                else:
                    # 对于AJAX请求，通知前端处理内容
                    return JsonResponse(
                        {
                            "success": False,
                            "message": "需要客户端处理内容，请点击'使用Gemini处理'按钮",
                        }
                    )
        except UserSettings.DoesNotExist:
            pass

        # 如果不是客户端代理模式，则正常发送
        result = send_user_report(request.user, force_send=True)

        # 处理AJAX请求
        if is_ajax:
            return JsonResponse(
                {"success": result["success"], "message": result["message"]}
            )

        if result["success"]:
            messages.success(request, result["message"])
        else:
            messages.error(request, result["message"])
    except Exception as e:
        logger.exception("发送报告时发生错误")
        messages.error(request, f"发送报告时发生错误: {str(e)}")

        # 处理AJAX请求的错误
        is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"
        if is_ajax:
            return JsonResponse(
                {"success": False, "message": f"发送报告时发生错误: {str(e)}"}
            )

    # 重定向回来源页面或内容提取页面
    referer = request.META.get("HTTP_REFERER")
    return HttpResponseRedirect(
        referer if referer else reverse_lazy("reporter:extract_content")
    )
