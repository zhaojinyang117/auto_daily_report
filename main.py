from datetime import datetime
from scraper import get_notion_content
from email_generator import generate_email
from email_sender import send_email
from logger import log_email_sent, setup_logger


def main_job():
    """主任务函数"""
    # 初始化日志系统
    setup_logger()

    try:
        # 获取内容
        log_email_sent("开始获取 Notion 内容...")
        content = get_notion_content()
        log_email_sent("成功获取 Notion 内容")

        # 生成邮件内容
        log_email_sent("开始生成邮件内容...")
        email_content = generate_email(content)
        log_email_sent("邮件内容生成完成")

        # 发送邮件
        log_email_sent("开始发送邮件...")
        send_email(email_content)
        log_email_sent("邮件发送成功")

    except Exception as e:
        # 记录错误日志
        error_message = f"任务执行失败: {str(e)}"
        log_email_sent(error_message)
        raise  # 重新抛出异常，确保错误不会被静默处理


if __name__ == "__main__":
    main_job()
