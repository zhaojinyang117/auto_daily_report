import sys
import argparse
from datetime import datetime
from scraper import get_notion_content
from email_generator import generate_email, EmailGenerator
from email_sender import send_email
from logger import log_email_sent
from preview_generator import PreviewGenerator


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


def preview_job(open_browser=True):
    """预览任务函数"""
    try:
        print("🚀 开始生成日报预览...")
        
        # 检查是否可以正常获取内容和处理
        try:
            # 获取内容
            print("📖 正在获取学习内容...")
            content = get_notion_content()
            
            # 检查Gemini API配置
            from config import CONFIG
            if not CONFIG.get("GEMINI_API_KEY"):
                print("⚠️  未配置Gemini API密钥，使用示例内容进行预览")
                # 使用示例内容
                processed_content = """1. 学习了Python基础知识<br><br>
2. 完成了项目设计<br><br>
3. 研究了数据库设计<br><br>
4. 进行了API开发测试<br><br>"""
                
                # 手动创建邮件主题和内容
                from datetime import datetime
                from config import Config
                config = Config(mode="preview")
                today = datetime.now().strftime("%Y-%m-%d")
                name = config.get("USER_NAME", "示例用户")
                subject = f"{name} {today} 日报"
                
                # 创建HTML内容
                html_content = f"<正文>\n{processed_content}\n</正文>"
            else:
                # 使用EmailGenerator生成邮件主题和内容
                generator = EmailGenerator()
                subject, html_content = generator.generate(content)
            
        except Exception as e:
            print(f"⚠️  无法获取实际内容 ({str(e)})，使用示例内容进行预览")
            # 使用完全示例的内容
            from datetime import datetime
            from config import Config
            config = Config(mode="preview")
            today = datetime.now().strftime("%Y-%m-%d")
            name = config.get("USER_NAME", "示例用户")
            subject = f"{name} {today} 日报"
            
            html_content = """<正文>
1. 学习了Python基础知识和语法结构<br><br>
2. 完成了数据库设计和表结构规划<br><br>
3. 开发了RESTful API接口和文档<br><br>
4. 进行了单元测试和集成测试<br><br>
5. 学习了前端框架和用户界面设计<br><br>
</正文>"""
        
        print(f"📝 邮件主题: {subject}")
        
        # 生成预览
        preview_gen = PreviewGenerator()
        file_path = preview_gen.generate_and_preview(subject, html_content, open_browser)
        
        print("✨ 预览生成完成!")
        return file_path

    except Exception as e:
        print(f"❌ 预览生成失败: {str(e)}")
        sys.exit(1)


def main():
    """主程序入口，支持命令行参数"""
    parser = argparse.ArgumentParser(description='自动日报生成器 - 支持预览和发送功能')
    parser.add_argument('--preview', '-p', action='store_true', 
                       help='预览模式：生成HTML预览文件但不发送邮件')
    parser.add_argument('--no-browser', action='store_true',
                       help='预览模式下不自动打开浏览器')
    
    args = parser.parse_args()
    
    if args.preview:
        # 预览模式
        open_browser = not args.no_browser
        preview_job(open_browser)
    else:
        # 正常发送模式
        main_job()


if __name__ == "__main__":
    main()
