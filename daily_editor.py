#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
日报编辑模块
提供只编辑当日内容的优化体验，而不需要编辑整个月度计划文件
"""

import os
import re
import logging
import tempfile
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
import requests


class DailyEditor:
    """日报编辑器，专门用于编辑当日内容"""
    
    def __init__(self, github_url: str = None):
        """
        初始化日报编辑器
        
        Args:
            github_url: GitHub raw文件URL，如果为None则使用默认URL
        """
        self.github_url = github_url or "https://raw.githubusercontent.com/zhaojinyang117/auto_daily_report/refs/heads/main/study_today.txt"
        self.local_file_path = "study_today.txt"
        logging.basicConfig(level=logging.INFO)
        
    def get_beijing_date(self) -> str:
        """获取当前北京时间的日期字符串"""
        utc_now = datetime.now(timezone.utc)
        beijing_now = utc_now + timedelta(hours=8)
        return beijing_now.strftime("%Y-%m-%d")
    
    def fetch_monthly_content(self) -> str:
        """从GitHub获取完整的月度计划内容"""
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/plain",
            }
            
            response = requests.get(self.github_url, headers=headers)
            response.raise_for_status()
            
            content = response.text.strip()
            if not content:
                raise ValueError("获取的月度计划内容为空")
                
            return content
            
        except requests.RequestException as e:
            raise Exception(f"获取GitHub内容失败: {str(e)}")
    
    def extract_daily_content(self, full_content: str, date: str) -> Tuple[str, int, int]:
        """
        提取指定日期的内容以及其在原文中的位置
        
        Args:
            full_content: 完整的月度计划内容
            date: 日期字符串，格式为YYYY-MM-DD
            
        Returns:
            tuple: (日期内容, 开始位置, 结束位置)
        """
        start_tag = f"<{date}>"
        end_tag = f"</{date}>"
        
        start_index = full_content.find(start_tag)
        if start_index == -1:
            return "", -1, -1
            
        content_start = start_index + len(start_tag)
        end_index = full_content.find(end_tag, content_start)
        
        if end_index == -1:
            # 如果没有找到结束标签，找到下一个日期标签或文件结尾
            next_date_pattern = r"<\d{4}-\d{2}-\d{2}>"
            match = re.search(next_date_pattern, full_content[content_start:])
            if match:
                end_index = content_start + match.start()
            else:
                end_index = len(full_content)
        
        daily_content = full_content[content_start:end_index].strip()
        return daily_content, start_index, end_index + len(end_tag) if end_tag in full_content[end_index:end_index+len(end_tag)] else end_index
    
    def get_today_content(self) -> Tuple[str, str]:
        """
        获取今日的学习内容
        
        Returns:
            tuple: (今日日期, 今日内容)
        """
        today = self.get_beijing_date()
        full_content = self.fetch_monthly_content()
        daily_content, _, _ = self.extract_daily_content(full_content, today)
        
        if not daily_content:
            logging.warning(f"未找到{today}的内容")
            
        return today, daily_content
    
    def update_daily_content(self, date: str, new_content: str, save_local: bool = True) -> str:
        """
        更新指定日期的内容
        
        Args:
            date: 要更新的日期
            new_content: 新的内容
            save_local: 是否保存到本地文件
            
        Returns:
            str: 更新后的完整月度计划内容
        """
        # 获取原始内容
        full_content = self.fetch_monthly_content()
        
        # 提取当前日期的内容和位置
        old_content, start_index, end_index = self.extract_daily_content(full_content, date)
        
        if start_index == -1:
            # 如果日期不存在，需要创建新的日期条目
            return self._create_new_date_entry(full_content, date, new_content, save_local)
        
        # 构建新的日期条目
        start_tag = f"<{date}>"
        end_tag = f"</{date}>"
        new_date_entry = f"{start_tag}\n{new_content.strip()}\n{end_tag}"
        
        # 替换原有内容
        updated_content = (
            full_content[:start_index] + 
            new_date_entry + 
            full_content[end_index:]
        )
        
        if save_local:
            self._save_to_local_file(updated_content)
            
        logging.info(f"已更新{date}的内容")
        return updated_content
    
    def _create_new_date_entry(self, full_content: str, date: str, new_content: str, save_local: bool) -> str:
        """为新日期创建条目"""
        # 找到合适的插入位置（按日期顺序）
        date_pattern = r"<(\d{4}-\d{2}-\d{2})>"
        dates_in_content = []
        
        for match in re.finditer(date_pattern, full_content):
            dates_in_content.append((match.group(1), match.start()))
        
        # 按日期排序
        dates_in_content.sort(key=lambda x: x[0])
        
        target_date = datetime.strptime(date, "%Y-%m-%d")
        insert_position = len(full_content)  # 默认插入到末尾
        
        # 找到应该插入的位置
        for existing_date, position in dates_in_content:
            existing_date_obj = datetime.strptime(existing_date, "%Y-%m-%d")
            if target_date < existing_date_obj:
                insert_position = position
                break
        
        # 构建新的日期条目
        start_tag = f"<{date}>"
        end_tag = f"</{date}>"
        new_date_entry = f"\n{start_tag}\n{new_content.strip()}\n{end_tag}\n"
        
        # 插入新内容
        updated_content = (
            full_content[:insert_position] + 
            new_date_entry + 
            full_content[insert_position:]
        )
        
        if save_local:
            self._save_to_local_file(updated_content)
            
        logging.info(f"已创建{date}的新条目")
        return updated_content
    
    def _save_to_local_file(self, content: str):
        """保存内容到本地文件"""
        try:
            with open(self.local_file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            logging.info(f"内容已保存到本地文件: {self.local_file_path}")
        except Exception as e:
            logging.error(f"保存本地文件失败: {str(e)}")
            raise
    
    def create_backup(self) -> str:
        """创建月度计划文件的备份"""
        try:
            full_content = self.fetch_monthly_content()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"study_today_backup_{timestamp}.txt"
            
            with open(backup_filename, 'w', encoding='utf-8') as f:
                f.write(full_content)
                
            logging.info(f"备份文件已创建: {backup_filename}")
            return backup_filename
            
        except Exception as e:
            logging.error(f"创建备份失败: {str(e)}")
            raise
    
    def preview_update(self, date: str, new_content: str) -> str:
        """
        预览更新后的内容，不实际保存
        
        Args:
            date: 要更新的日期
            new_content: 新的内容
            
        Returns:
            str: 更新后的完整内容（仅用于预览）
        """
        return self.update_daily_content(date, new_content, save_local=False)


def interactive_edit_today():
    """交互式编辑今日内容的命令行接口"""
    editor = DailyEditor()
    
    try:
        # 获取今日内容
        today, current_content = editor.get_today_content()
        
        print(f"\n=== 今日日报编辑器 ({today}) ===")
        print(f"\n当前内容:")
        print("-" * 50)
        if current_content:
            print(current_content)
        else:
            print("(今日暂无内容)")
        print("-" * 50)
        
        # 询问是否要编辑
        choice = input(f"\n是否要编辑{today}的内容? (y/n): ").lower().strip()
        
        if choice != 'y':
            print("操作已取消")
            return
        
        # 创建备份
        print("\n正在创建备份...")
        backup_file = editor.create_backup()
        
        # 编辑内容
        print(f"\n请输入{today}的新内容 (输入完成后按Ctrl+D或输入'END'结束):")
        lines = []
        try:
            while True:
                try:
                    line = input()
                    if line.strip() == 'END':
                        break
                    lines.append(line)
                except EOFError:
                    break
        except KeyboardInterrupt:
            print("\n操作已取消")
            return
        
        new_content = '\n'.join(lines)
        
        if not new_content.strip():
            print("内容为空，操作已取消")
            return
        
        # 预览更新
        print(f"\n=== 预览更新后的{today}内容 ===")
        print("-" * 50)
        print(new_content)
        print("-" * 50)
        
        # 确认更新
        confirm = input(f"\n确认更新{today}的内容? (y/n): ").lower().strip()
        
        if confirm == 'y':
            editor.update_daily_content(today, new_content)
            print(f"\n✅ {today}的内容已成功更新！")
            print(f"📁 备份文件: {backup_file}")
        else:
            print("更新已取消")
            
    except Exception as e:
        print(f"\n❌ 操作失败: {str(e)}")


if __name__ == "__main__":
    interactive_edit_today()