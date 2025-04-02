# 自动日报生成器

一个基于Web的自动报告工具，用于自动生成和发送日报。

## 特点

- **多用户支持**：每个用户拥有独立的账户和设置
- **内容管理**：通过Web界面管理月度工作计划
- **自动提取**：根据日期自动提取当日工作内容
- **AI增强**：使用Gemini AI优化内容表述
- **邮件发送**：自动生成并发送格式化邮件
- **任务调度**：可配置的定时任务，按用户设置的时间自动发送
- **历史记录**：查看已发送邮件的历史记录和状态
- **亚克力UI**：现代化、美观的用户界面，支持自定义背景和透明度

## 技术栈

- **后端**: Django
- **前端**: Django 模板 + Bootstrap 5 + 轻量级JavaScript
- **数据库**: SQLite
- **AI**: Gemini API
- **部署**: Gunicorn + Nginx

## 系统要求

- Python 3.12
- 1C1G服务器即可运行（已优化）

## 安装和部署

1. 克隆仓库
```bash
git clone https://github.com/yourusername/auto_daily_report.git
cd auto_daily_report
```

2. 创建并激活虚拟环境
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# 或
.venv\Scripts\activate  # Windows
```

3. 安装依赖
```bash
# 使用更快的包管理器uv
uv sync
```

4. 配置环境变量
复制`.env.example`并重命名为`.env`，设置您的邮箱、API密钥等信息

5. 初始化数据库
```bash
python manage.py migrate
```

6. 创建超级用户
```bash
python manage.py createsuperuser
```

7. 运行开发服务器
```bash
python manage.py runserver
```

8. 访问网站
浏览器访问 http://127.0.0.1:8000

## 生产环境部署

请参考[部署文档](docs/deployment.md)了解如何在生产环境中部署。

## 许可证

[MIT License](LICENSE)
