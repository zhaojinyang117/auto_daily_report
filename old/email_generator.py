import os
from datetime import datetime
from gemini_processor import process_with_gemini
from config import Config


def generate_email(content: str) -> str:
    # 使用Gemini处理内容
    processed_content = process_with_gemini(content)

    # 从配置获取名字和电话
    config = Config()
    name = config.get("EMAIL_SIGNATURE_NAME")
    phone = config.get("EMAIL_SIGNATURE_PHONE")

    # 邮件模板
    email_template = """Hi teacher,
<正文>
{content}
</正文>
--
Best Regards,


{name} / Intern
 
Medalsoft International，Tianjin
T: 400 856 0080  |  M: {phone}
www.medalsoft.com  Check out our product Here 
 Digital Transformation & AIGC (Generative AI) Solutions  
"""

    return email_template.format(content=processed_content, name=name, phone=phone)


# 添加EmailGenerator类
class EmailGenerator:
    """邮件生成器类，用于生成邮件内容"""

    def __init__(self):
        """初始化EmailGenerator"""
        self.config = Config()

    def generate(self, content: str) -> tuple[str, str]:
        """生成邮件内容和主题

        Args:
            content: 处理后的内容

        Returns:
            tuple: (邮件主题, 邮件HTML内容)
        """
        # 生成邮件主题（标题）
        today = datetime.now().strftime("%Y-%m-%d")
        # 使用CONFIG中的USER_NAME作为名字
        name = self.config.get("USER_NAME")
        subject = f"{name} {today} 日报"

        # 生成邮件内容
        html_content = generate_email(content)

        return subject, html_content
