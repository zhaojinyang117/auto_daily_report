from datetime import datetime
from scraper import get_notion_content
from email_generator import generate_email
from email_sender import send_email
from logger import log_email_sent


def main_job():
    """主任务函数"""
    try:
        # 获取内容
        content = get_notion_content()

        # 生成邮件内容
        email_content = generate_email(content)

        # 发送邮件
        send_email(email_content)

        # 记录成功日志
        log_message = "邮件发送成功"
        log_email_sent(log_message)

    except Exception as e:
        # 记录错误日志
        error_message = f"发送失败: {str(e)}"
        log_email_sent(error_message)


if __name__ == "__main__":
    main_job()
