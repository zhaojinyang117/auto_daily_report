#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import webbrowser
from datetime import datetime
from pathlib import Path
from config import Config


class PreviewGenerator:
    """HTML预览生成器类，用于生成和显示日报HTML预览"""

    def __init__(self):
        """初始化PreviewGenerator"""
        # Use preview mode for configuration (doesn't require all email configs)
        self.config = Config(mode="preview")

    def generate_preview_html(self, subject: str, html_content: str) -> str:
        """生成完整的HTML预览文档

        Args:
            subject: 邮件主题
            html_content: 邮件HTML内容

        Returns:
            str: 完整的HTML文档内容
        """
        # 提取正文部分
        if "<正文>" in html_content and "</正文>" in html_content:
            content = html_content.split("<正文>")[1].split("</正文>")[0]
        else:
            content = html_content

        # 获取当前时间
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 创建完整的HTML文档
        preview_html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>日报预览 - {subject}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Microsoft YaHei', Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 800px;
            margin: 0 auto;
            background-color: white;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
            border-radius: 8px;
            overflow: hidden;
        }}
        .header {{
            background-color: #2c5aa0;
            color: white;
            padding: 20px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 24px;
        }}
        .header .time {{
            font-size: 14px;
            opacity: 0.9;
            margin-top: 5px;
        }}
        .content {{
            padding: 30px;
        }}
        .email-content {{
            background-color: #fafafa;
            border: 1px solid #e0e0e0;
            border-radius: 6px;
            padding: 20px;
            margin: 20px 0;
        }}
        .greeting {{
            font-family: '微软雅黑';
            color: black;
            font-size: 14pt;
            margin-bottom: 15px;
        }}
        .main-content {{
            font-family: '微软雅黑';
            color: black;
            font-size: 14pt;
            line-height: 1.8;
            margin: 20px 0;
        }}
        .signature {{
            font-family: 'Segoe UI';
            margin-top: 25px;
            padding-top: 15px;
            border-top: 1px solid #ddd;
        }}
        .signature .name {{
            color: black;
            font-weight: bold;
            font-size: 13pt;
        }}
        .signature .title {{
            color: blue;
            font-weight: bold;
            font-size: 11pt;
        }}
        .signature .company {{
            color: black;
            font-size: 10pt;
        }}
        .signature .location {{
            color: blue;
            font-weight: bold;
            font-size: 10pt;
        }}
        .signature .contact {{
            color: black;
            font-size: 10pt;
        }}
        .signature .website {{
            color: black;
            text-decoration: underline;
            font-size: 10pt;
        }}
        .signature .product {{
            color: black;
            font-style: italic;
            font-size: 10pt;
        }}
        .signature .product-link {{
            color: black;
            font-weight: bold;
            font-style: italic;
            text-decoration: underline;
            font-size: 10pt;
        }}
        .signature .tagline {{
            color: black;
            font-weight: bold;
            font-size: 11pt;
            background-color: lightblue;
            padding: 2px 4px;
            border-radius: 3px;
        }}
        .footer {{
            background-color: #f8f9fa;
            padding: 15px 30px;
            border-top: 1px solid #e0e0e0;
            font-size: 12px;
            color: #666;
            text-align: center;
        }}
        .preview-note {{
            background-color: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 4px;
            padding: 15px;
            margin-bottom: 20px;
            color: #856404;
        }}
        .preview-note strong {{
            color: #8b6914;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📧 日报预览</h1>
            <div class="time">生成时间: {current_time}</div>
        </div>
        
        <div class="content">
            <div class="preview-note">
                <strong>📋 预览说明:</strong> 这是您的日报邮件预览版本。邮件主题为: <strong>{subject}</strong>
            </div>
            
            <div class="email-content">
                <div class="greeting">Hi teacher,</div>
                
                <div class="main-content">
                    {content}
                </div>
                
                <div style="margin: 20px 0;">--</div>
                <div class="greeting">Best Regards,</div>
                
                <div class="signature">
                    <span class="name">{self.config.get("EMAIL_SIGNATURE_NAME", "示例姓名")}</span>
                    <span class="title"> / Intern</span><br>
                    <span class="company">Medalsoft International，</span>
                    <span class="location">Tianjin</span><br>
                    <span class="contact">T: 400 856 0080  |  M: {self.config.get("EMAIL_SIGNATURE_PHONE", "+86 138 0000 0000")}</span><br>
                    <span class="website">www.medalsoft.com</span>
                    <span class="product"> Check out our product </span>
                    <span class="product-link">Here</span><br>
                    <span class="tagline"> Digital Transformation & AIGC (Generative AI) Solutions</span>
                </div>
            </div>
        </div>
        
        <div class="footer">
            <p>这是自动生成的日报预览，仅供预览使用。实际发送的邮件可能会因邮件客户端的不同而有所差异。</p>
        </div>
    </div>
</body>
</html>"""
        return preview_html

    def save_preview(self, preview_html: str, filename: str = None) -> str:
        """保存预览HTML到文件

        Args:
            preview_html: 预览HTML内容
            filename: 保存的文件名，默认为None时使用时间戳

        Returns:
            str: 保存的文件路径
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"daily_report_preview_{timestamp}.html"
        
        # 使用/tmp目录避免提交到仓库
        preview_dir = Path("/tmp")
        preview_dir.mkdir(exist_ok=True)
        
        file_path = preview_dir / filename
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(preview_html)
        
        return str(file_path)

    def open_in_browser(self, file_path: str) -> bool:
        """在默认浏览器中打开预览文件

        Args:
            file_path: HTML文件路径

        Returns:
            bool: 是否成功打开
        """
        try:
            webbrowser.open(f"file://{file_path}")
            return True
        except Exception as e:
            print(f"无法打开浏览器: {e}")
            return False

    def generate_and_preview(self, subject: str, html_content: str, open_browser: bool = True) -> str:
        """生成预览并保存到文件，可选择是否在浏览器中打开

        Args:
            subject: 邮件主题
            html_content: 邮件HTML内容
            open_browser: 是否在浏览器中打开，默认为True

        Returns:
            str: 保存的文件路径
        """
        # 生成预览HTML
        preview_html = self.generate_preview_html(subject, html_content)
        
        # 保存到文件
        file_path = self.save_preview(preview_html)
        
        print(f"✅ 日报预览已生成: {file_path}")
        
        # 可选择在浏览器中打开
        if open_browser:
            if self.open_in_browser(file_path):
                print("🌐 预览已在默认浏览器中打开")
            else:
                print("❌ 无法在浏览器中打开预览文件")
                print(f"📁 您可以手动打开文件: {file_path}")
        else:
            print(f"📁 预览文件保存在: {file_path}")
        
        return file_path