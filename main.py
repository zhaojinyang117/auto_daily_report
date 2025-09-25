from datetime import datetime
from scraper import get_notion_content
from email_generator import generate_email
from email_sender import send_email
from logger import log_email_sent
import sys
import argparse


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


def show_help():
    """显示帮助信息"""
    help_text = """
🚀 自动日报生成器

📋 使用方法:
  python main.py                 # 运行日报生成和发送（默认）
  python main.py --edit          # 编辑今日内容（命令行模式）
  python main.py --web-edit      # 启动Web编辑器
  python main.py --help          # 显示此帮助信息

✨ 新功能 - 今日内容编辑:
  现在您可以只编辑今天的内容，而不需要编辑整个月度计划文件！
  
  🖥️  命令行编辑: python main.py --edit
  🌐 Web界面编辑: python main.py --web-edit
  
💡 优势:
  - 只修改当日部分，优化编辑体验
  - 自动备份原文件
  - 支持预览功能
  - Web界面更加直观易用
    """
    print(help_text)


def main():
    """主入口函数"""
    parser = argparse.ArgumentParser(description='自动日报生成器', add_help=False)
    parser.add_argument('--edit', action='store_true', help='编辑今日内容（命令行）')
    parser.add_argument('--web-edit', action='store_true', help='启动Web编辑器')
    parser.add_argument('--help', action='store_true', help='显示帮助信息')
    parser.add_argument('--port', '-p', type=int, default=8000, help='Web编辑器端口号')
    
    args = parser.parse_args()
    
    if args.help:
        show_help()
        return
    
    if args.edit:
        # 命令行编辑模式
        try:
            from daily_editor import interactive_edit_today
            interactive_edit_today()
        except ImportError:
            print("❌ 无法导入编辑模块，请检查daily_editor.py文件")
        except Exception as e:
            print(f"❌ 编辑失败: {str(e)}")
        return
    
    if args.web_edit:
        # Web编辑模式  
        try:
            from web_editor import start_web_editor
            start_web_editor(args.port)
        except ImportError:
            print("❌ 无法导入Web编辑模块，请检查web_editor.py文件")
        except Exception as e:
            print(f"❌ 启动Web编辑器失败: {str(e)}")
        return
    
    # 默认行为：运行日报生成任务
    main_job()


if __name__ == "__main__":
    main()
