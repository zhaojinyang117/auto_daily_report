import requests
import logging
import os
from datetime import datetime

os.environ["GRPC_ENABLE_FORK_SUPPORT"] = "0"  # 禁用gRPC的fork支持

# 配置基本的日志
logging.basicConfig(level=logging.INFO)


def get_notion_content() -> str:
    try:
        # 使用GitHub raw文件链接
        url = "https://raw.githubusercontent.com/zhaojinyang117/auto_daily_report/refs/heads/dev/study_today.txt"

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/plain",
        }

        response = requests.get(url, headers=headers)
        response.raise_for_status()

        # 获取内容
        full_content = response.text.strip()

        if not full_content:
            raise ValueError("获取的内容为空")

        # 获取当前日期
        today = datetime.now().strftime("%Y-%m-%d")

        # 提取当天的内容
        content = extract_content_for_date(full_content, today)

        # 始终添加正文标签包装内容
        content = f"<正文>\n{content}\n</正文>"

        logging.info("\n获取到的内容: %s", content[:200])
        return content

    except requests.RequestException as e:
        raise Exception(f"获取GitHub内容失败: {str(e)}")
    except Exception as e:
        raise Exception(f"处理内容失败: {str(e)}")


def extract_content_for_date(full_content: str, date: str) -> str:
    """
    从月度计划表中提取特定日期的内容

    Args:
        full_content: 完整的月度计划表内容
        date: 日期字符串，格式为YYYY-MM-DD

    Returns:
        str: 对应日期的内容
    """
    try:
        # 寻找日期标记
        start_tag = f"<{date}>"
        end_tag = f"</{date}>"

        # 提取对应日期的内容
        start_index = full_content.find(start_tag)
        if start_index == -1:
            logging.warning(f"找不到日期 {date} 的内容，将使用默认内容")
            return "今日学习内容暂未设置"

        start_index += len(start_tag)
        end_index = full_content.find(end_tag, start_index)

        if end_index == -1:
            end_index = len(full_content)

        return full_content[start_index:end_index].strip()
    except Exception as e:
        logging.error(f"提取日期内容时出错: {str(e)}")
        return "提取日期内容时出错"


# 添加Scraper类
class Scraper:
    """内容获取器类，用于从各种来源获取内容"""

    def __init__(self):
        """初始化Scraper"""
        logging.info("初始化内容获取器")

    def get_content(self) -> str:
        """获取内容

        Returns:
            str: 获取到的内容
        """
        logging.info("开始获取内容...")
        return get_notion_content()
