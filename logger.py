import logging
from datetime import datetime
import os
from config import CONFIG

def setup_logger():
    """设置日志记录器"""
    # 确保日志目录存在
    log_dir = os.path.dirname(CONFIG["LOG_FILE"])
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # 配置日志格式
    logging.basicConfig(
        level=getattr(logging, CONFIG["LOG_LEVEL"]),
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(CONFIG["LOG_FILE"], encoding='utf-8'),
            logging.StreamHandler()  # 同时输出到控制台
        ]
    )

def log_email_sent(message: str):
    """记录邮件发送日志

    Args:
        message: 要记录的日志消息
    """
    try:
        # 获取当前时间
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 确保日志目录存在
        log_dir = os.path.dirname(CONFIG["LOG_FILE"])
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        # 追加写入日志
        with open(CONFIG["LOG_FILE"], 'a', encoding='utf-8') as f:
            f.write(f"{message} - {current_time}\n")
            f.flush()  # 立即写入文件
            os.fsync(f.fileno())  # 确保写入磁盘
            
    except Exception as e:
        logging.error(f"写入日志失败: {str(e)}")
        raise

def get_latest_log():
    with open(CONFIG['LOG_FILE'], 'r', encoding='utf-8') as f:
        lines = f.readlines()
        return lines[-1] if lines else "No logs found." 