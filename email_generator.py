import os
from datetime import datetime
from gemini_processor import process_with_gemini


def generate_email(content):
    # 使用Gemini处理内容
    processed_content = process_with_gemini(content)

    # 邮件模板
    email_template = """Hi teacher,
<正文>
{content}
</正文>
--
Best Regards,


JINYANG ZHAO / Intern
 
Medalsoft International，Tianjin
T: 400 856 0080  |  M: +86 183 1062 9060
www.medalsoft.com  Check out our product Here 
 Digital Transformation & AIGC (Generative AI) Solutions  
"""

    return email_template.format(content=processed_content)


# 添加EmailGenerator类
class EmailGenerator:
    """邮件生成器类，用于生成邮件内容"""

    def __init__(self):
        """初始化EmailGenerator"""
        pass

    def generate(self, content):
        """生成邮件内容和主题

        Args:
            content: 处理后的内容

        Returns:
            tuple: (邮件主题, 邮件HTML内容)
        """
        # 生成邮件主题（标题）
        today = datetime.now().strftime("%Y-%m-%d")
        subject = f"赵金洋 {today} 日报"

        # 生成邮件内容
        html_content = generate_email(content)

        return subject, html_content
