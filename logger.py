import logging
from datetime import datetime
import os
from config import CONFIG


def setup_logger(log_file=None, console_level=logging.INFO):
    """设置日志记录器

    Args:
        log_file: 日志文件路径，如果为None则使用CONFIG中的配置
        console_level: 控制台日志级别
    """
    # 使用参数提供的日志文件或默认配置
    log_path = log_file if log_file else CONFIG["LOG_FILE"]

    # 确保日志目录存在
    log_dir = os.path.dirname(log_path)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # 创建文件处理器
    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setLevel(getattr(logging, CONFIG["LOG_LEVEL"]))

    # 创建控制台处理器
    console_handler = logging.StreamHandler()  # 同时输出到控制台
    console_handler.setLevel(console_level)

    # 设置格式
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # 配置根日志记录器
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)  # 设置为最低级别，让各处理器自行过滤
    logger.handlers = []  # 清除现有处理器
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


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
        with open(CONFIG["LOG_FILE"], "a", encoding="utf-8") as f:
            f.write(f"{message} - {current_time}\n")
            f.flush()  # 立即写入文件
            os.fsync(f.fileno())  # 确保写入磁盘

    except Exception as e:
        logging.error(f"写入日志失败: {str(e)}")
        raise


def get_latest_log():
    with open(CONFIG["LOG_FILE"], "r", encoding="utf-8") as f:
        lines = f.readlines()
        return lines[-1] if lines else "No logs found."
