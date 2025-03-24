import google.generativeai as genai
from config import CONFIG


def process_with_gemini(content: str) -> str:
    """处理内容并生成格式化的学习总结

    Args:
        content: 原始学习内容文本

    Returns:
        格式化的学习总结文本
    """
    genai.configure(api_key=CONFIG["GEMINI_API_KEY"])
    model = genai.GenerativeModel("gemini-2.0-flash-thinking-exp-01-21")

    prompt = f"""
    请根据以下内容，总结今天的学习要点，要求：
    1. 内容要详细具体,对各个要点的可能内容进行猜测
    2. 用1、2、3...的形式列出
    3. 每个要点后面加上<br><br>标签作为双换行
    4. 每个点的要简洁一些,以正式邮件的格式列出
    5. 不要出现"待补充"、"后续内容"等不确定的表述
    6. 绝对不要出现诸如"好的，根据您提供的内容，今天的学习要点总结如下"这样的表述
    7. 不要出现"可能"、"推测"之类的词语
    
    原始内容：
    {content}
    """

    response = model.generate_content(prompt)

    # 处理文本格式
    formatted_text = response.text.strip()

    # 确保每个数字编号后面有双换行
    for i in range(1, 10):
        formatted_text = formatted_text.replace(f"{i}. ", f"{i}. <br><br>")
        formatted_text = formatted_text.replace(f"{i}.", f"{i}. <br><br>")

    # 移除多余的换行（三个或更多的<br>）
    while "<br><br><br>" in formatted_text:
        formatted_text = formatted_text.replace("<br><br><br>", "<br><br>")

    return formatted_text


# 添加GeminiProcessor类
class GeminiProcessor:
    """Gemini处理器类，用于调用Gemini API处理内容"""

    def __init__(self):
        """初始化GeminiProcessor"""
        # 检查API密钥
        if not CONFIG["GEMINI_API_KEY"]:
            raise ValueError("未配置Gemini API密钥")

    def process(self, content: str) -> str:
        """处理内容并生成格式化的学习总结

        Args:
            content: 原始学习内容文本

        Returns:
            str: 格式化的学习总结文本
        """
        return process_with_gemini(content)
