#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import requests
import logging
from datetime import datetime
from pathlib import Path

# 导入项目模块
try:
    from config import Config
    from logger import setup_logger
    from scraper import Scraper
    from gemini_processor import GeminiProcessor
    from email_generator import EmailGenerator
    from email_sender import EmailSender
except ImportError:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from config import Config
    from logger import setup_logger
    from scraper import Scraper
    from gemini_processor import GeminiProcessor
    from email_generator import EmailGenerator
    from email_sender import EmailSender


def is_github_actions():
    """检查是否在GitHub Actions环境中运行"""
    return os.environ.get("GITHUB_ACTIONS") == "true"


def setup_github_env():
    """从GitHub Secrets设置环境变量"""
    if not is_github_actions():
        logging.warning("不在GitHub Actions环境中运行，跳过GitHub环境设置")
        return

    # 映射GitHub Secrets到环境变量
    env_mapping = {
        "GEMINI_API_KEY": "GEMINI_API_KEY",
        "USER_NAME": "USER_NAME",
        "EMAIL_SIGNATURE_NAME": "EMAIL_SIGNATURE_NAME",
        "EMAIL_SIGNATURE_PHONE": "EMAIL_SIGNATURE_PHONE",
        "EMAIL_FROM": "EMAIL_FROM",
        "EMAIL_PASSWORD": "EMAIL_PASSWORD",
        "EMAIL_TO": "EMAIL_TO",
        "SMTP_SERVER": "SMTP_SERVER",
        "SMTP_PORT": "SMTP_PORT",
        "LOG_LEVEL": "LOG_LEVEL",
    }

    for env_var, secret_name in env_mapping.items():
        if secret_name in os.environ:
            os.environ[env_var] = os.environ[secret_name]
            logging.info(f"已从GitHub Secrets设置环境变量: {env_var}")
        else:
            logging.warning(f"GitHub Secrets中缺少: {secret_name}")


def main():
    """主函数"""
    # 设置日志
    script_dir = os.path.dirname(os.path.abspath(__file__))
    log_file = os.path.join(script_dir, "github_action.log")
    logger = setup_logger(log_file, console_level=logging.INFO)

    logger.info("===== GitHub Action自动日报生成器启动 =====")
    logger.info(f"运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        # 检查并设置GitHub环境
        if is_github_actions():
            logger.info("检测到GitHub Actions环境")
            setup_github_env()

        # 加载配置
        config = Config()

        # 获取学习内容
        logger.info("正在获取学习内容...")
        scraper = Scraper()
        content = scraper.get_content()

        if not content:
            logger.error("获取内容失败")
            sys.exit(1)

        logger.info(f"成功获取学习内容: {len(content)} 字符")

        # AI处理内容
        logger.info("正在使用Gemini处理内容...")
        processor = GeminiProcessor()
        processed_content = processor.process(content)

        if not processed_content:
            logger.error("AI处理内容失败")
            sys.exit(1)

        logger.info("Gemini处理完成")

        # 生成邮件
        logger.info("正在生成邮件...")
        generator = EmailGenerator()
        subject, html_content = generator.generate(processed_content)

        logger.info(f"邮件主题: {subject}")

        # 发送邮件
        logger.info("正在发送邮件...")
        sender = EmailSender()
        result = sender.send_email(subject, html_content)

        if result:
            logger.info("邮件发送成功")
        else:
            logger.error("邮件发送失败")
            sys.exit(1)

        logger.info("===== GitHub Action自动日报生成器任务完成 =====")

    except Exception as e:
        logger.exception(f"程序执行过程中发生错误: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
