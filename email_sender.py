import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import CONFIG
import ssl
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.INFO)


def send_email(content):
    # 生成邮件标题
    today = datetime.now().strftime("%Y-%m-%d")
    subject = f"{CONFIG['USER_NAME']} {today} 日报"

    # 处理多个收件人
    recipients = [email.strip() for email in CONFIG["EMAIL_TO"].split(",")]

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = CONFIG["EMAIL_FROM"]
    msg["To"] = ", ".join(recipients)  # 用逗号和空格连接多个收件人

    # 创建HTML版本的邮件内容
    html = f"""
    <div style="font-family: '微软雅黑'; color: black; font-size: 14pt;">
        Hi teacher,<br>
        <div style="font-family: '微软雅黑'; color: black; font-size: 14pt;">
        {content.split("<正文>")[1].split("</正文>")[0]}
        </div>
        --<br>
        Best Regards,<br><br>
    </div>
    <div style="font-family: 'Segoe UI';">
        <span style="color: black; font-weight: bold; font-size: 13pt;">{CONFIG["EMAIL_SIGNATURE_NAME"]}</span>
        <span style="color: blue; font-weight: bold; font-size: 11pt;"> / Intern</span><br>
        <span style="color: black; font-size: 10pt;">Medalsoft International，</span>
        <span style="color: blue; font-weight: bold; font-size: 10pt;">Tianjin</span><br>
        <span style="color: black; font-size: 10pt;">T: 400 856 0080  |  M: {CONFIG["EMAIL_SIGNATURE_PHONE"]}</span><br>
        <span style="color: black; text-decoration: underline; font-size: 10pt;">www.medalsoft.com</span>
        <span style="color: black; font-style: italic; font-size: 10pt;"> Check out our product </span>
        <span style="color: black; font-weight: bold; font-style: italic; text-decoration: underline; font-size: 10pt;">Here</span><br>
        <span style="color: black; font-weight: bold; font-size: 11pt; background-color: lightblue;"> Digital Transformation & AIGC (Generative AI) Solutions</span>
    </div>
    """

    msg.attach(MIMEText(html, "html"))

    try:
        # 创建SSL上下文
        context = ssl.create_default_context()

        logging.info(
            f"正在连接SMTP服务器 {CONFIG['SMTP_SERVER']}:{CONFIG['SMTP_PORT']}..."
        )
        # 使用SSL连接发送邮件
        with smtplib.SMTP_SSL(
            CONFIG["SMTP_SERVER"], CONFIG["SMTP_PORT"], context=context
        ) as server:
            server.set_debuglevel(1)  # 启用调试模式
            logging.info(f"正在尝试登录账号 {CONFIG['EMAIL_FROM']}...")
            server.login(CONFIG["EMAIL_FROM"], CONFIG["EMAIL_PASSWORD"])
            logging.info("登录成功，正在发送邮件...")
            # 发送给所有收件人
            server.send_message(msg)
            logging.info(f"邮件发送成功！收件人: {', '.join(recipients)}")

    except smtplib.SMTPAuthenticationError as e:
        raise Exception(f"认证失败: {str(e)}\n请检查邮箱地址和授权码是否正确")
    except smtplib.SMTPConnectError as e:
        raise Exception(f"连接服务器失败: {str(e)}\n请检查服务器地址和端口是否正确")
    except Exception as e:
        raise Exception(f"发送邮件失败: {str(e)}")


# 添加EmailSender类
class EmailSender:
    """邮件发送器类，用于发送邮件"""

    def __init__(self):
        """初始化EmailSender"""
        # 验证必要的配置
        required_configs = [
            "EMAIL_FROM",
            "EMAIL_PASSWORD",
            "EMAIL_TO",
            "SMTP_SERVER",
            "SMTP_PORT",
            "EMAIL_SIGNATURE_NAME",
            "EMAIL_SIGNATURE_PHONE",
        ]
        for config_name in required_configs:
            if not CONFIG.get(config_name):
                raise ValueError(f"缺少必要的邮件配置项: {config_name}")

    def send_email(self, subject, html_content):
        """发送邮件

        Args:
            subject: 邮件主题
            html_content: 邮件HTML内容

        Returns:
            bool: 发送是否成功
        """
        try:
            # 处理多个收件人
            recipients = [email.strip() for email in CONFIG["EMAIL_TO"].split(",")]

            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = CONFIG["EMAIL_FROM"]
            msg["To"] = ", ".join(recipients)  # 用逗号和空格连接多个收件人

            # 提取正文部分
            if "<正文>" in html_content and "</正文>" in html_content:
                content = html_content.split("<正文>")[1].split("</正文>")[0]
            else:
                content = html_content

            # 创建HTML版本的邮件内容
            html = f"""
            <div style="font-family: '微软雅黑'; color: black; font-size: 14pt;">
                Hi teacher,<br>
                <div style="font-family: '微软雅黑'; color: black; font-size: 14pt;">
                {content}
                </div>
                --<br>
                Best Regards,<br><br>
            </div>
            <div style="font-family: 'Segoe UI';">
                <span style="color: black; font-weight: bold; font-size: 13pt;">{CONFIG["EMAIL_SIGNATURE_NAME"]}</span>
                <span style="color: blue; font-weight: bold; font-size: 11pt;"> / Intern</span><br>
                <span style="color: black; font-size: 10pt;">Medalsoft International，</span>
                <span style="color: blue; font-weight: bold; font-size: 10pt;">Tianjin</span><br>
                <span style="color: black; font-size: 10pt;">T: 400 856 0080  |  M: {CONFIG["EMAIL_SIGNATURE_PHONE"]}</span><br>
                <span style="color: black; text-decoration: underline; font-size: 10pt;">www.medalsoft.com</span>
                <span style="color: black; font-style: italic; font-size: 10pt;"> Check out our product </span>
                <span style="color: black; font-weight: bold; font-style: italic; text-decoration: underline; font-size: 10pt;">Here</span><br>
                <span style="color: black; font-weight: bold; font-size: 11pt; background-color: lightblue;"> Digital Transformation & AIGC (Generative AI) Solutions</span>
            </div>
            """

            msg.attach(MIMEText(html, "html"))

            # 创建SSL上下文
            context = ssl.create_default_context()

            logging.info(
                f"正在连接SMTP服务器 {CONFIG['SMTP_SERVER']}:{CONFIG['SMTP_PORT']}..."
            )
            # 使用SSL连接发送邮件
            with smtplib.SMTP_SSL(
                CONFIG["SMTP_SERVER"], CONFIG["SMTP_PORT"], context=context
            ) as server:
                server.set_debuglevel(1)  # 启用调试模式
                logging.info(f"正在尝试登录账号 {CONFIG['EMAIL_FROM']}...")
                server.login(CONFIG["EMAIL_FROM"], CONFIG["EMAIL_PASSWORD"])
                logging.info("登录成功，正在发送邮件...")
                # 发送给所有收件人
                server.send_message(msg)
                logging.info(f"邮件发送成功！收件人: {', '.join(recipients)}")

            return True

        except smtplib.SMTPAuthenticationError as e:
            logging.error(f"认证失败: {str(e)}\n请检查邮箱地址和授权码是否正确")
            return False
        except smtplib.SMTPConnectError as e:
            logging.error(f"连接服务器失败: {str(e)}\n请检查服务器地址和端口是否正确")
            return False
        except Exception as e:
            logging.error(f"发送邮件失败: {str(e)}")
            return False
