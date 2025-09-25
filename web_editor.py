#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
简单的Web界面日报编辑器
提供基于浏览器的今日内容编辑功能
"""

import os
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import json
from daily_editor import DailyEditor
import logging

class DailyEditorHandler(BaseHTTPRequestHandler):
    """处理日报编辑的HTTP请求"""
    
    def __init__(self, *args, **kwargs):
        self.editor = DailyEditor()
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """处理GET请求"""
        if self.path == '/' or self.path == '/edit':
            self.serve_edit_page()
        elif self.path == '/api/today':
            self.get_today_content()
        else:
            self.send_error(404, "页面未找到")
    
    def do_POST(self):
        """处理POST请求"""
        if self.path == '/api/update':
            self.update_today_content()
        else:
            self.send_error(404, "API未找到")
    
    def serve_edit_page(self):
        """提供编辑页面"""
        try:
            today, content = self.editor.get_today_content()
            
            html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>今日日报编辑器 - {today}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Microsoft YaHei', sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            text-align: center;
            margin-bottom: 30px;
        }}
        .date {{
            color: #666;
            text-align: center;
            margin-bottom: 20px;
        }}
        textarea {{
            width: 100%;
            min-height: 300px;
            padding: 15px;
            border: 2px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
            font-family: 'Consolas', 'Monaco', monospace;
            line-height: 1.5;
            resize: vertical;
        }}
        textarea:focus {{
            border-color: #007cba;
            outline: none;
        }}
        .button-group {{
            margin-top: 20px;
            text-align: center;
        }}
        button {{
            padding: 12px 24px;
            margin: 0 10px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 16px;
            transition: background-color 0.3s;
        }}
        .btn-primary {{
            background-color: #007cba;
            color: white;
        }}
        .btn-primary:hover {{
            background-color: #005a87;
        }}
        .btn-secondary {{
            background-color: #6c757d;
            color: white;
        }}
        .btn-secondary:hover {{
            background-color: #545b62;
        }}
        .message {{
            padding: 10px;
            margin: 10px 0;
            border-radius: 4px;
            display: none;
        }}
        .message.success {{
            background-color: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }}
        .message.error {{
            background-color: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }}
        .help-text {{
            color: #666;
            font-size: 14px;
            margin-top: 10px;
        }}
        .current-content {{
            background-color: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 4px;
            padding: 15px;
            margin-bottom: 20px;
        }}
        .current-content h3 {{
            margin-top: 0;
            color: #495057;
        }}
        .current-content pre {{
            background-color: white;
            padding: 10px;
            border-radius: 4px;
            overflow-x: auto;
            white-space: pre-wrap;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📝 今日日报编辑器</h1>
        <div class="date">编辑日期: <strong>{today}</strong></div>
        
        <div class="current-content">
            <h3>📋 当前内容:</h3>
            <pre>{content if content else '(今日暂无内容)'}</pre>
        </div>
        
        <form id="editForm">
            <textarea id="content" name="content" placeholder="请输入{today}的学习内容...">{content}</textarea>
            <div class="help-text">
                💡 提示: 支持Markdown格式，建议使用以下结构：<br>
                - 学习内容标题<br>
                - 具体学习点1<br>
                - 具体学习点2
            </div>
            
            <div class="message" id="message"></div>
            
            <div class="button-group">
                <button type="button" class="btn-primary" onclick="saveContent()">💾 保存更新</button>
                <button type="button" class="btn-secondary" onclick="previewContent()">👁️ 预览</button>
                <button type="button" class="btn-secondary" onclick="location.reload()">🔄 重置</button>
            </div>
        </form>
    </div>

    <script>
        function showMessage(text, type) {{
            const messageEl = document.getElementById('message');
            messageEl.textContent = text;
            messageEl.className = 'message ' + type;
            messageEl.style.display = 'block';
            
            if (type === 'success') {{
                setTimeout(() => {{
                    messageEl.style.display = 'none';
                }}, 3000);
            }}
        }}
        
        function saveContent() {{
            const content = document.getElementById('content').value;
            const date = '{today}';
            
            if (!content.trim()) {{
                showMessage('内容不能为空！', 'error');
                return;
            }}
            
            // 显示保存中状态
            showMessage('正在保存...', 'success');
            
            fetch('/api/update', {{
                method: 'POST',
                headers: {{
                    'Content-Type': 'application/json',
                }},
                body: JSON.stringify({{
                    date: date,
                    content: content
                }})
            }})
            .then(response => response.json())
            .then(data => {{
                if (data.success) {{
                    showMessage('✅ 保存成功！', 'success');
                    // 3秒后刷新页面显示最新内容
                    setTimeout(() => {{
                        location.reload();
                    }}, 2000);
                }} else {{
                    showMessage('❌ 保存失败: ' + data.message, 'error');
                }}
            }})
            .catch(error => {{
                showMessage('❌ 网络错误: ' + error.message, 'error');
            }});
        }}
        
        function previewContent() {{
            const content = document.getElementById('content').value;
            if (!content.trim()) {{
                showMessage('内容为空，无法预览', 'error');
                return;
            }}
            
            // 在新窗口中显示预览
            const previewWindow = window.open('', '_blank');
            previewWindow.document.write(`
                <html>
                    <head>
                        <title>内容预览 - {today}</title>
                        <style>
                            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; padding: 20px; max-width: 800px; margin: 0 auto; }}
                            pre {{ background: #f5f5f5; padding: 15px; border-radius: 4px; white-space: pre-wrap; }}
                        </style>
                    </head>
                    <body>
                        <h1>📋 内容预览</h1>
                        <p><strong>日期:</strong> {today}</p>
                        <hr>
                        <pre>${{content}}</pre>
                        <hr>
                        <button onclick="window.close()">关闭预览</button>
                    </body>
                </html>
            `);
        }}
        
        // 自动保存功能（可选）
        let autoSaveTimer;
        document.getElementById('content').addEventListener('input', function() {{
            clearTimeout(autoSaveTimer);
            autoSaveTimer = setTimeout(() => {{
                // 可以在这里添加自动保存到本地存储的功能
                localStorage.setItem('daily_content_draft_{today}', this.value);
            }}, 1000);
        }});
        
        // 页面加载时恢复草稿（如果有）
        window.addEventListener('load', function() {{
            const draft = localStorage.getItem('daily_content_draft_{today}');
            if (draft && draft !== document.getElementById('content').value) {{
                if (confirm('发现未保存的草稿，是否恢复？')) {{
                    document.getElementById('content').value = draft;
                }}
            }}
        }});
    </script>
</body>
</html>
            """
            
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(html.encode('utf-8'))
            
        except Exception as e:
            self.send_error(500, f"服务器错误: {str(e)}")
    
    def get_today_content(self):
        """获取今日内容的API"""
        try:
            today, content = self.editor.get_today_content()
            
            response = {
                'success': True,
                'date': today,
                'content': content
            }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
            
        except Exception as e:
            self.send_error(500, f"获取内容失败: {str(e)}")
    
    def update_today_content(self):
        """更新今日内容的API"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            date = data.get('date')
            content = data.get('content')
            
            if not date or not content:
                raise ValueError("日期和内容不能为空")
            
            # 更新内容
            self.editor.update_daily_content(date, content)
            
            response = {
                'success': True,
                'message': f'{date}的内容已成功更新'
            }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
            
        except Exception as e:
            response = {
                'success': False,
                'message': str(e)
            }
            
            self.send_response(500)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
    
    def log_message(self, format, *args):
        """重写日志方法，避免过多输出"""
        pass


def start_web_editor(port=8000):
    """启动Web编辑器服务"""
    try:
        server_address = ('localhost', port)
        httpd = HTTPServer(server_address, DailyEditorHandler)
        
        print(f"""
🌟 今日日报Web编辑器已启动！

📍 访问地址: http://localhost:{port}
🛠️  编辑界面: http://localhost:{port}/edit

💡 使用说明:
   - 在浏览器中打开上述地址
   - 编辑今日的学习内容
   - 点击保存按钮更新内容
   - 支持预览和自动保存草稿功能

⌨️  按 Ctrl+C 停止服务
        """)
        
        httpd.serve_forever()
        
    except KeyboardInterrupt:
        print("\n👋 Web编辑器服务已停止")
    except Exception as e:
        print(f"❌ 启动Web编辑器失败: {str(e)}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='今日日报Web编辑器')
    parser.add_argument('--port', '-p', type=int, default=8000, help='服务端口号 (默认: 8000)')
    
    args = parser.parse_args()
    start_web_editor(args.port)