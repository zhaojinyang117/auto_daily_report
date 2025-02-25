import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 配置字典
CONFIG = {
    # Gemini API配置
    "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY"),
    # Telegram配置
    "TELEGRAM_BOT_TOKEN": os.getenv("TELEGRAM_BOT_TOKEN"),
    "TELEGRAM_CHAT_ID": os.getenv("TELEGRAM_CHAT_ID"),
    # 个人信息配置
    "USER_NAME": os.getenv("USER_NAME", "赵金洋"),  # 添加默认值
    # 邮件配置
    "EMAIL_FROM": os.getenv("EMAIL_FROM"),
    "EMAIL_PASSWORD": os.getenv("EMAIL_PASSWORD"),
    "EMAIL_TO": os.getenv("EMAIL_TO"),
    # SMTP配置
    "SMTP_SERVER": os.getenv("SMTP_SERVER"),
    "SMTP_PORT": int(os.getenv("SMTP_PORT", "465")),  # 转换为整数
    # 日志配置
    "LOG_LEVEL": os.getenv("LOG_LEVEL", "INFO"),
    "LOG_FILE": os.getenv(
        "LOG_FILE", "alice studio_email_logs.txt"
    ),  # 添加日志文件配置
}

# 验证必要的配置
required_configs = [
    "EMAIL_FROM",
    "EMAIL_PASSWORD",
    "EMAIL_TO",
    "SMTP_SERVER",
    "SMTP_PORT",
    "USER_NAME",
    "LOG_FILE",  # 添加到必要配置列表
]

for config_name in required_configs:
    if not CONFIG.get(config_name):
        raise ValueError(f"缺少必要的配置项: {config_name}")
