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
    "USER_NAME": os.getenv("USER_NAME"),
    "EMAIL_SIGNATURE_NAME": os.getenv("EMAIL_SIGNATURE_NAME"),
    "EMAIL_SIGNATURE_PHONE": os.getenv("EMAIL_SIGNATURE_PHONE"),
    # 邮件配置
    "EMAIL_FROM": os.getenv("EMAIL_FROM"),
    "EMAIL_PASSWORD": os.getenv("EMAIL_PASSWORD"),
    "EMAIL_TO": os.getenv("EMAIL_TO"),
    # SMTP配置
    "SMTP_SERVER": os.getenv("SMTP_SERVER"),
    "SMTP_PORT": int(os.getenv("SMTP_PORT", "465")),  # 转换为整数
    # 日志配置
    "LOG_LEVEL": os.getenv("LOG_LEVEL", "INFO"),  # 保留默认值
    "LOG_FILE": os.getenv("LOG_FILE", "alice studio_email_logs.txt"),  # 保留默认值
}

# 验证必要的配置
required_configs = [
    "EMAIL_FROM",
    "EMAIL_PASSWORD",
    "EMAIL_TO",
    "SMTP_SERVER",
    "SMTP_PORT",
    "USER_NAME",
    "EMAIL_SIGNATURE_NAME",
    "EMAIL_SIGNATURE_PHONE",
]

for config_name in required_configs:
    if not CONFIG.get(config_name):
        raise ValueError(f"缺少必要的配置项: {config_name}")


# 添加Config类
class Config:
    """配置类，用于提供配置访问接口"""

    def __init__(self):
        """初始化配置"""
        self.config = CONFIG

    def get(self, key, default=None):
        """获取配置值"""
        return self.config.get(key, default)

    def __getattr__(self, name):
        """通过属性方式访问配置"""
        return self.config.get(name)
