import requests
import logging
import os
import re
from datetime import datetime, timedelta, timezone

os.environ["GRPC_ENABLE_FORK_SUPPORT"] = "0"  # 禁用gRPC的fork支持

# 配置基本的日志
logging.basicConfig(level=logging.INFO)


def get_notion_content() -> str:
    try:
        # 使用GitHub raw文件链接
        url = "https://raw.githubusercontent.com/zhaojinyang117/auto_daily_report/refs/heads/main/study_today.txt"

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

        # 获取当前北京时间（UTC+8）
        utc_now = datetime.now(timezone.utc)
        beijing_now = utc_now + timedelta(hours=8)
        today = beijing_now.strftime("%Y-%m-%d")

        logging.info(f"当前北京时间: {beijing_now}, 日期: {today}")

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
    从月度计划表中提取特定日期的内容，如果找不到当前日期，则使用最近的日期内容

    Args:
        full_content: 完整的月度计划表内容
        date: 日期字符串，格式为YYYY-MM-DD

    Returns:
        str: 对应日期的内容或最近日期的内容
    """
    try:
        # 寻找日期标记
        start_tag = f"<{date}>"
        end_tag = f"</{date}>"

        # 提取对应日期的内容
        start_index = full_content.find(start_tag)

        # 如果找到当前日期的内容，直接返回
        if start_index != -1:
            start_index += len(start_tag)
            end_index = full_content.find(end_tag, start_index)

            if end_index == -1:
                end_index = len(full_content)

            return full_content[start_index:end_index].strip()

        # 如果找不到当前日期的内容，寻找最近的日期
        logging.warning(f"找不到日期 {date} 的内容，将查找最近的日期内容")

        # 使用正则表达式找出所有日期标签
        date_pattern = r"<(\d{4}-\d{2}-\d{2})>"
        all_dates = re.findall(date_pattern, full_content)

        if not all_dates:
            logging.warning("未找到任何日期标签，将使用默认内容")
            return "未找到任何日期内容，请检查月度计划表格式"

        # 将日期字符串转换为datetime对象进行比较
        target_date = datetime.strptime(date, "%Y-%m-%d")
        closest_date = None
        min_diff = float("inf")

        for d in all_dates:
            current_date = datetime.strptime(d, "%Y-%m-%d")
            diff = abs((target_date - current_date).days)

            if diff < min_diff:
                min_diff = diff
                closest_date = d

        logging.info(f"找到最近的日期: {closest_date}，相差{min_diff}天")

        # 使用最近的日期内容
        closest_start_tag = f"<{closest_date}>"
        closest_end_tag = f"</{closest_date}>"

        closest_start_index = full_content.find(closest_start_tag)
        closest_start_index += len(closest_start_tag)
        closest_end_index = full_content.find(closest_end_tag, closest_start_index)

        if closest_end_index == -1:
            closest_end_index = len(full_content)

        content = full_content[closest_start_index:closest_end_index].strip()
        return f"[使用{closest_date}的内容] {content}"

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
