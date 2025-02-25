import os
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