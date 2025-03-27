import logging
from scraper import extract_content_for_date, get_notion_content
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.INFO)


def test_extract_content():
    # 示例月度计划表内容
    sample_content = """<月度计划：2024-04>

<2024-04-01>
## 分组函数与原生查询
- **分组函数**：使用`annotate()`与`values()`结合来进行分组计算
</2024-04-01>

<2024-04-02>
## 修改记录
1. **基于模型对象的修改**：获取特定模型对象
</2024-04-02>
"""

    # 测试现有日期
    content_01 = extract_content_for_date(sample_content, "2024-04-01")
    print(f"2024-04-01的内容: \n{content_01}\n")

    # 测试现有日期
    content_02 = extract_content_for_date(sample_content, "2024-04-02")
    print(f"2024-04-02的内容: \n{content_02}\n")

    # 测试不存在的日期
    content_03 = extract_content_for_date(sample_content, "2024-04-03")
    print(f"2024-04-03的内容: \n{content_03}\n")

    # 当前日期测试
    today = datetime.now().strftime("%Y-%m-%d")
    content_today = extract_content_for_date(sample_content, today)
    print(f"今天({today})的内容: \n{content_today}\n")


def test_full_flow():
    """测试完整流程，从GitHub获取内容并提取当天内容"""
    try:
        print("开始测试完整流程...")
        print("=" * 50)
        content = get_notion_content()
        print("\n获取到最终内容:")
        print("=" * 50)
        print(content)
        print("=" * 50)
        print("测试完成")
    except Exception as e:
        print(f"测试失败: {str(e)}")


if __name__ == "__main__":
    # 测试提取函数
    print("测试提取函数:")
    print("=" * 50)
    test_extract_content()

    # 测试完整流程
    print("\n\n测试完整流程:")
    print("=" * 50)
    test_full_flow()
