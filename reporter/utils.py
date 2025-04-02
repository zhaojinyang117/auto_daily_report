import re
from datetime import date
from typing import Optional


def extract_content_for_date(content: str, target_date: date) -> Optional[str]:
    """从月度计划内容中提取指定日期的内容

    Args:
        content: 月度计划的原始内容
        target_date: 要提取内容的目标日期

    Returns:
        提取到的内容，如果未找到则返回None
    """
    # 转换目标日期为字符串格式
    target_date_str = target_date.strftime('%Y-%m-%d')
    
    # 正则表达式匹配日期标记的内容
    # 匹配 <2023-01-01>内容</2023-01-01> 格式
    date_pattern = r'<(\d{4}-\d{2}-\d{2})>(.*?)</\1>'
    matches = re.findall(date_pattern, content, re.DOTALL)
    
    if not matches:
        return None
    
    # 尝试找到精确匹配的日期
    for date_str, date_content in matches:
        if date_str == target_date_str:
            return date_content.strip()
    
    # 如果没有找到精确匹配，可以实现其他策略
    # 例如，找到最近的日期内容
    # 这里仅返回None表示未找到
    return None


def get_relative_date_content(content: str, target_date: date) -> tuple[Optional[str], Optional[str]]:
    """从月度计划内容中查找目标日期或最近日期的内容

    Args:
        content: 月度计划的原始内容
        target_date: 要提取内容的目标日期

    Returns:
        元组(找到的内容, 使用的日期字符串)，如果未找到则返回(None, None)
    """
    # 转换目标日期为字符串格式
    target_date_str = target_date.strftime('%Y-%m-%d')
    
    # 正则表达式匹配日期标记的内容
    date_pattern = r'<(\d{4}-\d{2}-\d{2})>(.*?)</\1>'
    matches = re.findall(date_pattern, content, re.DOTALL)
    
    if not matches:
        return None, None
    
    # 尝试找到精确匹配的日期
    for date_str, date_content in matches:
        if date_str == target_date_str:
            return date_content.strip(), date_str
    
    # 如果没有精确匹配，找到最近的日期
    # 按日期排序所有匹配项
    sorted_dates = sorted(matches, key=lambda x: x[0])
    
    # 找到小于目标日期的最大日期
    prev_matches = [(d, c) for d, c in sorted_dates if d < target_date_str]
    if prev_matches:
        date_str, content = prev_matches[-1]
        return content.strip(), date_str
    
    # 如果没有较早的日期，返回最早的日期
    if sorted_dates:
        date_str, content = sorted_dates[0]
        return content.strip(), date_str
    
    return None, None