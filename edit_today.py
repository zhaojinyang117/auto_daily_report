#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
今日日报快速编辑工具
使用方法: python edit_today.py
"""

import sys
import os
from daily_editor import interactive_edit_today

def main():
    """主函数"""
    print("🚀 启动今日日报编辑器...")
    
    try:
        interactive_edit_today()
    except KeyboardInterrupt:
        print("\n\n👋 用户取消操作，再见！")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 程序执行出错: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()