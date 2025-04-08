import smtplib
import logging
import ssl
import re
from datetime import datetime, date
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from django.utils import timezone
from django.conf import settings
import google.generativeai as genai
from django.contrib.auth.models import User
from typing import Any, Dict, List, Optional, Tuple, Union
from reporter.models import MonthlyPlan, UserSettings, EmailLog
from reporter.utils import extract_content_for_date

# 配置日志
logger = logging.getLogger(__name__)


class GeminiProcessor:
    """使用Gemini API处理内容的服务类"""

    def __init__(
        self, api_key: str, use_client_proxy: bool = False, use_hf_proxy: bool = False, timeout: int = 15
    ) -> None:
        """初始化GeminiProcessor

        Args:
            api_key: Gemini API密钥
            use_client_proxy: 是否使用客户端代理
            use_hf_proxy: 是否使用HuggingFace代理
            timeout: API请求超时时间（秒）
        """
        self.api_key = api_key
        self.use_client_proxy = use_client_proxy
        self.use_hf_proxy = use_hf_proxy
        self.timeout = timeout

        # 配置API
        if self.use_client_proxy:
            # 使用客户端代理时，将向前端返回API请求所需信息，不在后端调用API
            self.use_backend_api = False
            self.model = None
        else:
            # 使用后端网络环境
            self.use_backend_api = True
            if self.use_hf_proxy:
                # 使用HuggingFace代理
                logger.info("使用HuggingFace代理访问Gemini API")
                # 这里不使用genai.configure，因为我们需要直接配置API URL
                self.model = None  # 我们将手动构建API请求
            else:
                # 使用Google官方API
                genai.configure(api_key=api_key)
                self.model = genai.GenerativeModel("gemini-2.0-flash")

    def format_learning_summary(self, content: str) -> Union[str, Dict[str, Any]]:
        """使用Gemini API优化学习总结

        Args:
            content: 原始学习内容

        Returns:
            优化后的内容或包含API调用信息的字典

        Raises:
            Exception: 当API调用失败时抛出异常
        """
        # 生成通用提示
        prompt = f"""
    请根据以下内容，总结今天的学习要点，要求：
    1. 内容要详细具体,对各个要点的可能内容进行猜测
    2. 用1、2、3...的形式列出，直接给出要点，不要加尊敬的领导/同事等问候语
    3. 每个要点后面加上<br><br>标签换行
    4. 每个点的要简洁一些,以正式邮件的格式列出，但不要加结束语如"此致敬礼"等
    5. 不要出现"待补充"、"后续内容"等不确定的表述
    6. 绝对不要出现诸如"好的，根据您提供的内容，今天的学习要点总结如下"这样的表述
    7. 不要出现"可能"、"推测"之类的词语
    8. 不要添加任何引言和结束语，直接开始列举要点

    原始内容：
    {content}
    """

        if not self.use_backend_api:
            # 当使用客户端代理时，返回API调用所需的信息
            logger.info("使用客户端代理模式，准备前端调用Gemini API所需信息")
            return {
                "use_client_proxy": True,
                "api_key": self.api_key,
                "prompt": prompt,
                "original_content": content,
                "model": "gemini-2.0-flash",
                "timeout": self.timeout,  # 添加超时参数传递给前端
                "use_hf_proxy": self.use_hf_proxy,  # 传递HuggingFace代理标志
            }

        # 使用后端API进行处理
        try:
            if self.use_hf_proxy:
                # 使用HuggingFace代理API
                logger.info("使用HuggingFace代理API进行请求")
                import requests
                import json
                
                # 设置请求超时时间
                request_timeout = self.timeout
                
                # 构建请求参数
                api_url = "https://apicheck-gemini.hf.space/hf/v1"
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}"
                }
                
                # 构建请求体，使用chat/completions接口格式
                payload = {
                    "model": "gemini-2.0-flash",
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                }
                
                # 发送请求
                response = requests.post(
                    f"{api_url}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=request_timeout
                )
                
                # 检查响应状态
                response.raise_for_status()
                
                # 解析响应，chat/completions接口的响应格式
                result = response.json()
                formatted_text = result["choices"][0]["message"]["content"]
            else:
                # 使用官方API
                request_options = {"timeout": self.timeout}
                response = self.model.generate_content(
                    prompt, request_options=request_options
                )
                formatted_text = response.text.strip()

            # 处理文本格式，与old/gemini_processor.py中的格式化方式保持一致
            # 确保每个数字编号后面有双换行
            for i in range(1, 10):
                formatted_text = formatted_text.replace(f"{i}. ", f"{i}. <br><br>")
                formatted_text = formatted_text.replace(f"{i}.", f"{i}. <br><br>")

            # 移除多余的换行（三个或更多的<br>）
            while "<br><br><br>" in formatted_text:
                formatted_text = formatted_text.replace("<br><br><br>", "<br><br>")

            return formatted_text
        except TimeoutError as e:
            # 专门处理超时错误
            logger.error(f"Gemini API请求超时: {e}")
            raise Exception(f"Gemini API请求超时 ({self.timeout}秒): {e}")
        except Exception as e:
            # 记录错误，但不默默地返回原始内容，而是重新抛出异常
            logger.error(f"Gemini API调用失败: {e}")
            raise Exception(f"Gemini API调用失败: {e}")


class EmailGenerator:
    """生成邮件内容和主题的服务类"""

    def __init__(self, user_settings: UserSettings, target_date: date) -> None:
        """初始化EmailGenerator

        Args:
            user_settings: 用户设置实例
            target_date: 目标日期
        """
        self.user_settings = user_settings
        self.target_date = target_date

    def get_email_subject(self) -> str:
        """生成邮件标题

        Returns:
            邮件标题字符串
        """
        date_str = self.target_date.strftime("%Y-%m-%d")
        weekday_cn = ["一", "二", "三", "四", "五", "六", "日"][
            self.target_date.weekday()
        ]

        # 使用用户中文名，如果没有则使用默认名
        user_name = (
            self.user_settings.user_name
            if hasattr(self.user_settings, "user_name")
            else "学习报告"
        )

        return f"{user_name} {date_str} 星期{weekday_cn} 日报"

    def generate_email_html(self, content: str) -> str:
        """生成HTML格式的邮件内容

        Args:
            content: 邮件正文内容

        Returns:
            HTML格式的邮件内容
        """
        # 替换换行为HTML换行标签
        content_html = content

        # 获取姓名和电话信息
        name = self.user_settings.email_signature_name or ""
        phone = self.user_settings.email_signature_phone or ""

        # HTML邮件模板
        html_template = """<!DOCTYPE html>
        <html>
        <body>
            <div style="font-family: Arial, sans-serif; margin-bottom: 20px;">
                Hi teacher,<br>
                <div style="font-family: '微软雅黑'; color: black; font-size: 14pt;">
                {content}
                </div>
                --<br>
                Best Regards,<br><br>
            </div>
            <div style="font-family: 'Segoe UI';">
                <span style="color: black; font-weight: bold; font-size: 13pt;">{name}</span>
                <span style="color: blue; font-weight: bold; font-size: 11pt;"> / Intern</span><br>
                <span style="color: black; font-size: 10pt;">Medalsoft International，</span>
                <span style="color: blue; font-weight: bold; font-size: 10pt;">Tianjin</span><br>
                <span style="color: black; font-size: 10pt;">T: 400 856 0080  |  M: {phone}</span><br>
                <span style="color: black; text-decoration: underline; font-size: 10pt;">www.medalsoft.com</span>
                <span style="color: black; font-style: italic; font-size: 10pt;"> Check out our product </span>
                <span style="color: black; font-weight: bold; font-style: italic; text-decoration: underline; font-size: 10pt;">Here</span><br>
                <span style="color: black; font-weight: bold; font-size: 11pt; background-color: lightblue;"> Digital Transformation & AIGC (Generative AI) Solutions</span>
            </div>
        </body>
        </html>
        """

        return html_template.format(content=content_html, name=name, phone=phone)


class EmailSender:
    """发送邮件的服务类"""

    def __init__(self, user_settings: UserSettings) -> None:
        """初始化EmailSender

        Args:
            user_settings: 用户设置实例
        """
        self.from_email = user_settings.email_from
        self.password = user_settings.email_password
        self.to_emails = (
            [email.strip() for email in user_settings.email_to.split(",")]
            if user_settings.email_to
            else []
        )
        self.smtp_server = user_settings.smtp_server
        self.smtp_port = user_settings.smtp_port
        self.use_ssl = user_settings.smtp_port == 465  # 465端口使用SSL

    def send_email(self, subject: str, html_content: str) -> bool:
        """发送邮件

        Args:
            subject: 邮件标题
            html_content: HTML格式的邮件内容

        Returns:
            是否发送成功
        """
        if not self.from_email or not self.password or not self.to_emails:
            logger.error("邮件配置不完整")
            return False

        if not self.smtp_server or not self.smtp_port:
            logger.error("SMTP服务器配置不完整")
            return False

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self.from_email
        msg["To"] = ", ".join(self.to_emails)

        # 添加HTML内容
        msg.attach(MIMEText(html_content, "html"))

        try:
            if self.use_ssl:
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL(
                    self.smtp_server, self.smtp_port, context=context
                ) as server:
                    server.login(self.from_email, self.password)
                    server.sendmail(self.from_email, self.to_emails, msg.as_string())
            else:
                with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                    server.starttls()
                    server.login(self.from_email, self.password)
                    server.sendmail(self.from_email, self.to_emails, msg.as_string())
            logger.info(f"邮件发送成功: {subject} 发送至 {', '.join(self.to_emails)}")
            return True
        except Exception as e:
            logger.error(f"邮件发送失败: {e}")
            return False


def send_user_report(
    user: User,
    specific_date: Optional[date] = None,
    force_send: bool = False,
    timeout: Optional[int] = None,
    is_scheduled: bool = False,
) -> Dict[str, Any]:
    """为指定用户发送报告

    Args:
        user: 用户对象
        specific_date: 指定日期，如果为None则使用当前日期
        force_send: 是否强制发送，忽略激活状态
        timeout: Gemini API请求超时时间（秒），如果为None则使用用户设置中的值

    Returns:
        包含状态和消息的字典
    """
    # 使用指定日期或当前日期
    target_date = specific_date or date.today()

    # 检查是否为工作日（0-4为周一至周五，5-6为周末）
    is_workday = target_date.weekday() < 5

    try:
        # 获取用户设置
        try:
            user_settings = UserSettings.objects.get(user=user)
        except UserSettings.DoesNotExist:
            # 记录日志
            EmailLog.objects.create(
                user=user,
                status=EmailLog.STATUS_FAILED,
                error_message="用户设置不存在。请先完成设置。",
                is_scheduled=is_scheduled,
            )
            return {"success": False, "message": "用户设置不存在。请先完成设置。"}

        # 检查用户设置是否激活（如果不是强制发送）
        if not force_send and not user_settings.is_active:
            # 记录日志
            EmailLog.objects.create(
                user=user,
                status=EmailLog.STATUS_FAILED,
                error_message="报告功能未激活。请在设置中激活。",
                is_scheduled=is_scheduled,
            )
            return {"success": False, "message": "报告功能未激活。请在设置中激活。"}

        # 检查是否是用户设置的发送日期
        # 如果是手动指定的日期或强制发送，则跳过此检查
        if not force_send and specific_date is None and user_settings.send_days:
            day_of_month = str(target_date.day)
            if day_of_month not in user_settings.send_days:
                # 记录日志
                error_msg = f"当前日期({target_date.strftime('%Y-%m-%d')})不在设置的发送日期列表中。"
                EmailLog.objects.create(
                    user=user, status=EmailLog.STATUS_FAILED, error_message=error_msg, is_scheduled=is_scheduled
                )
                return {
                    "success": False,
                    "message": error_msg,
                }

        # 获取对应月份的月度计划
        try:
            monthly_plan = MonthlyPlan.objects.get(
                user=user, year=target_date.year, month=target_date.month
            )
        except MonthlyPlan.DoesNotExist:
            # 记录日志
            error_msg = f"未找到 {target_date.year}年{target_date.month}月 的月度计划。"
            EmailLog.objects.create(
                user=user, status=EmailLog.STATUS_FAILED, error_message=error_msg, is_scheduled=is_scheduled
            )
            return {
                "success": False,
                "message": error_msg,
            }

        # 提取特定日期的内容
        content = extract_content_for_date(monthly_plan.content, target_date)
        if not content:
            # 记录日志
            error_msg = f"在 {target_date} 未找到学习内容。"
            EmailLog.objects.create(
                user=user, status=EmailLog.STATUS_NO_CONTENT, error_message=error_msg, is_scheduled=is_scheduled
            )
            return {"success": False, "message": error_msg}

        # 检查邮箱配置是否完整
        if (
            not user_settings.email_from
            or not user_settings.email_password
            or not user_settings.email_to
            or not user_settings.smtp_server
            or not user_settings.smtp_port
        ):
            # 记录日志
            error_msg = "邮箱配置不完整，请在设置中完成配置。"
            EmailLog.objects.create(
                user=user, status=EmailLog.STATUS_FAILED, error_message=error_msg, is_scheduled=is_scheduled
            )
            return {"success": False, "message": error_msg}

        # 使用Gemini处理内容（如有API密钥）
        processed_content = content  # 默认使用原始内容
        gemini_error = None  # 记录Gemini处理错误

        if user_settings.gemini_api_key:
            try:
                logger.info("开始使用Gemini处理内容...")
                # 使用用户设置的超时时间，如果未指定则使用默认值
                api_timeout = (
                    timeout if timeout is not None else user_settings.gemini_timeout
                )
                logger.info(f"Gemini API超时时间设置为: {api_timeout}秒")

                gemini_processor = GeminiProcessor(
                    user_settings.gemini_api_key,
                    use_client_proxy=user_settings.use_client_proxy,
                    use_hf_proxy=user_settings.use_hf_proxy,
                    timeout=api_timeout,
                )
                processed_result = gemini_processor.format_learning_summary(content)

                # 检查结果是否为客户端代理模式的API信息
                if isinstance(processed_result, dict) and processed_result.get(
                    "use_client_proxy"
                ):
                    # 如果是客户端代理模式，返回API调用信息
                    # 记录日志
                    error_msg = "需要客户端代理调用API，请使用前端工具完成此操作"
                    EmailLog.objects.create(
                        user=user,
                        status=EmailLog.STATUS_FAILED,
                        error_message=error_msg,
                        is_scheduled=is_scheduled,
                    )
                    return {
                        "success": False,
                        "message": error_msg,
                        "client_proxy_data": processed_result,
                    }

                # 否则是处理后的内容字符串
                processed_content = processed_result
                logger.info("Gemini处理内容完成")
            except Exception as e:
                error_message = f"Gemini处理失败: {e}"
                logger.error(error_message)
                # 记录错误信息
                gemini_error = error_message

                # 考虑用户可能不希望在处理失败时发送原始内容
                # 这里仍使用原始内容，但在日志和邮件标题中标记
                processed_content = content
        else:
            # 没有API密钥，使用原始内容
            logger.warning("未配置Gemini API密钥，使用原始内容")

        # 生成邮件内容
        email_generator = EmailGenerator(user_settings, target_date)

        # 获取邮件标题（不再在标题中添加标记）
        subject = email_generator.get_email_subject()

        html_content = email_generator.generate_email_html(processed_content)

        # 发送邮件
        email_sender = EmailSender(user_settings)
        if email_sender.send_email(subject, html_content):
            # 记录成功日志
            # 获取内容预览
            content_preview = processed_content
            if len(content_preview) > 500:
                content_preview = content_preview[:500] + "..."

            # 创建日志记录
            log_entry = EmailLog.objects.create(
                user=user,
                status=EmailLog.STATUS_SUCCESS,
                subject=subject,
                content_preview=content_preview,
                is_scheduled=is_scheduled,
            )

            # 如果有Gemini错误，记录在日志中
            if gemini_error:
                log_entry.error_message = gemini_error
                log_entry.save()

            return {
                "success": True,
                "message": f"报告已成功发送至 {user_settings.email_to}"
                + (" [使用原始内容]" if gemini_error else ""),
            }
        else:
            # 记录失败日志
            error_msg = "邮件发送失败。请检查邮箱设置。"
            EmailLog.objects.create(
                user=user,
                status=EmailLog.STATUS_FAILED,
                subject=subject,
                error_message=error_msg,
                is_scheduled=is_scheduled,
            )
            return {"success": False, "message": error_msg}

    except Exception as e:
        logger.exception(f"发送报告时发生错误: {e}")
        # 记录异常日志
        error_msg = f"发送报告时发生错误: {str(e)}"
        try:
            EmailLog.objects.create(
                user=user, status=EmailLog.STATUS_FAILED, error_message=error_msg, is_scheduled=is_scheduled
            )
        except Exception as log_error:
            logger.exception(f"记录邮件日志失败: {log_error}")

        return {"success": False, "message": error_msg}
