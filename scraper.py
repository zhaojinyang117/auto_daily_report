import requests
import logging
import os

os.environ["GRPC_ENABLE_FORK_SUPPORT"] = "0"  # 禁用gRPC的fork支持

# 配置基本的日志
logging.basicConfig(level=logging.INFO)


def get_notion_content():
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
        content = response.text.strip()

        if not content:
            raise ValueError("获取的内容为空")

        # 确保内容包含正文标签
        if "<正文>" not in content or "</正文>" not in content:
            content = f"<正文>{content}</正文>"

        logging.info("\n获取到的内容: %s", content[:200])
        return content

    except requests.RequestException as e:
        raise Exception(f"获取GitHub内容失败: {str(e)}")
    except Exception as e:
        raise Exception(f"处理内容失败: {str(e)}")
