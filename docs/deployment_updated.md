# 自动日报生成器部署指南

本文档详细介绍如何将自动日报生成器部署到生产环境，包括常见问题的解决方案和最佳实践。

## 系统要求

- 一台Linux服务器（推荐配置：1核1G或更高）
- Python 3.10+
- Nginx
- 互联网连接（用于访问Gemini API，如果使用AI功能）

## 部署方式

自动日报生成器提供两种部署方式：
1. **一键安装脚本**（推荐）：适合不熟悉Linux服务器配置的用户
2. **手动部署**：适合需要更精细控制部署过程的用户

## 一键安装（推荐）

### 准备工作

1. 确保您有一台运行Linux的服务器（支持Ubuntu、Debian、CentOS等主流发行版）
2. 确保您有root或sudo权限
3. 确保服务器可以访问互联网

### 安装步骤

1. 以root权限登录您的Linux服务器

2. 下载安装脚本：
```bash
curl -O https://raw.githubusercontent.com/zhaojinyang117/auto_daily_report/refs/heads/dev/install.sh
# 或者如果已经克隆了仓库，脚本就在项目根目录下
```

3. 添加执行权限：
```bash
chmod +x install.sh
```

4. 运行安装脚本：
```bash
sudo bash install.sh
```

5. 按照交互式提示完成配置：
   - 安装目录（默认为/var/www/auto_daily_report）
   - Git仓库地址
   - 环境变量配置（域名、API密钥、邮件设置等）
   - 管理员账户创建
   - HTTPS配置（可选）

### 安装过程说明

安装脚本会自动执行以下任务：
- 检测操作系统并安装必要的系统依赖
- 克隆和配置项目代码
- 使用uv创建Python虚拟环境并安装依赖
- 配置环境变量
- 初始化数据库和收集静态文件
- 设置Gunicorn服务
- 配置Nginx服务器
- 配置HTTPS（如果选择）
- 设置定时任务和日志轮转
- 测试安装并提供详细的使用说明

安装完成后，脚本会显示网站地址、管理后台地址和其他重要信息。

## 手动部署详细步骤

如果您希望手动部署或需要更精细地控制部署过程，以下是详细的步骤说明。

### 1. 准备服务器环境

```bash
# 更新系统包
sudo apt update && sudo apt upgrade -y

# 安装必要的系统依赖
sudo apt install -y python3-pip python3-venv nginx git curl
```

### 2. 克隆代码仓库

```bash
# 选择一个合适的目录
mkdir -p /home/alice
cd /home/alice

# 克隆代码仓库
git clone https://github.com/zhaojinyang117/auto_daily_report.git
cd auto_daily_report
```

### 3. 创建虚拟环境并安装依赖

推荐使用uv作为包管理器，它比pip更快、更可靠：

```bash
# 安装uv
curl -sSf https://install.python-uv.org | python3

# 创建虚拟环境
uv venv .venv

# 激活虚拟环境
source .venv/bin/activate

# 安装依赖
uv sync

# 确保安装gunicorn和其他必要依赖
uv pip install gunicorn django-cron django-widget-tweaks
```

如果您更习惯使用pip：

```bash
# 创建虚拟环境
python3 -m venv .venv

# 激活虚拟环境
source .venv/bin/activate

# 安装依赖
pip install -e .

# 安装gunicorn和其他必要依赖
pip install gunicorn django-cron django-widget-tweaks
```

### 4. 配置环境变量

```bash
# 创建.env文件
cp .env.example .env

# 编辑.env文件，配置必要的环境变量
nano .env
```

确保配置了以下环境变量：
```
# Django 配置
SECRET_KEY=django-insecure-aep1k9ctom)!@h&qkkn5pt_&p-5$8&b+mjj%xxh%(lc22jx4_t
DEBUG=False
ALLOWED_HOSTS=your-domain.com,localhost,127.0.0.1

# Gemini API配置
GEMINI_API_KEY=your_gemini_api_key_here

# 个人信息配置
USER_NAME=张三                     # 姓名（用于日报标题）
EMAIL_SIGNATURE_NAME=Zhang San    # 邮件签名显示的英文名
EMAIL_SIGNATURE_PHONE=+86 123 4567 8901  # 邮件签名显示的电话

# 邮件发送配置
EMAIL_FROM=your_email@example.com
EMAIL_PASSWORD=your_email_password_or_app_password
EMAIL_TO=recipient1@example.com,recipient2@example.com    # 用逗号分隔多个邮箱

# SMTP服务器配置
SMTP_SERVER=smtp.example.com        # SMTP服务器地址
SMTP_PORT=465                       # SSL端口（通常是465）

# 日志级别设置
LOG_LEVEL=INFO                      # 日志记录级别（DEBUG/INFO/WARNING/ERROR/CRITICAL）
```

### 5. 初始化数据库

```bash
# 执行数据库迁移
python manage.py migrate

# 收集静态文件
python manage.py collectstatic --noinput

# 创建管理员用户
python manage.py createsuperuser
```

### 6. 配置Gunicorn服务

创建systemd服务文件：

```bash
sudo nano /etc/systemd/system/daily-reporter.service
```

添加以下内容（注意替换路径为您的实际安装路径）：

```ini
[Unit]
Description=Daily Report Generator Gunicorn Daemon
After=network.target

[Service]
User=root
Group=root
WorkingDirectory=/home/alice/auto_daily_report
ExecStart=/home/alice/auto_daily_report/.venv/bin/gunicorn \
    --access-logfile - \
    --workers 1 \
    --bind unix:/home/alice/auto_daily_report/daily_reporter.sock \
    daily_reporter_project.wsgi:application
Environment="DJANGO_SETTINGS_MODULE=daily_reporter_project.settings"

[Install]
WantedBy=multi-user.target
```

启动Gunicorn服务：

```bash
sudo systemctl daemon-reload
sudo systemctl start daily-reporter
sudo systemctl enable daily-reporter
```

### 7. 配置Nginx

创建Nginx配置文件：

```bash
sudo nano /etc/nginx/sites-available/daily-reporter
```

添加以下内容，替换`report.alicee.me`为您的域名：

```nginx
server {
    listen 80;
    server_name report.alicee.me;

    location = /favicon.ico { access_log off; log_not_found off; }
    
    location /static/ {
        alias /home/alice/auto_daily_report/staticfiles/;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/home/alice/auto_daily_report/daily_reporter.sock;
    }
}
```

启用配置并重启Nginx：

```bash
sudo ln -s /etc/nginx/sites-available/daily-reporter /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 8. 配置HTTPS（推荐）

使用Let's Encrypt设置HTTPS：

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d report.alicee.me
```

### 9. 设置定时任务

配置cron任务以定期运行发送报告的脚本：

```bash
# 确保脚本具有执行权限
chmod +x /home/alice/auto_daily_report/scripts/setup_django_cron.sh

# 配置cron任务
cd /home/alice/auto_daily_report
bash scripts/setup_django_cron.sh
```

这将设置一个每5分钟运行一次的cron任务，检查是否有需要发送的日报。

## 多用户支持

自动日报生成器支持多用户环境，每个用户有独立的设置内容和环境配置：

1. 通过管理后台创建新用户：
   - 访问 http://your-domain.com/admin/
   - 使用超级用户账号登录
   - 在 "Authentication and Authorization" > "Users" 中添加新用户

2. 通过命令行创建用户：
   ```bash
   source .venv/bin/activate
   python manage.py createsuperuser  # 创建超级用户
   # 或
   python manage.py shell -c "from django.contrib.auth.models import User; User.objects.create_user(username='testuser', password='password123')"  # 创建普通用户
   ```

3. 每个用户可以独立配置：
   - 邮箱设置
   - API密钥
   - 发送时间和日期
   - 月度计划内容

## 常见问题排查

### 1. 服务无法启动

检查Gunicorn日志：

```bash
sudo systemctl status daily-reporter
sudo journalctl -u daily-reporter
```

常见问题：
- 虚拟环境路径错误
- 工作目录不存在
- 权限问题
- 依赖缺失

### 2. 无法访问网站

检查Nginx配置和日志：

```bash
sudo nginx -t
sudo cat /var/log/nginx/error.log
```

常见问题：
- Nginx配置错误
- sock文件路径不匹配
- 防火墙阻止了80/443端口
- 域名DNS未正确解析

### 3. 定时任务不执行

检查cron日志：

```bash
grep CRON /var/log/syslog
tail -f /home/alice/auto_daily_report/logs/django_cron.log
```

检查cron任务是否正确设置：

```bash
crontab -l
```

### 4. 数据库迁移问题

如果遇到数据库迁移问题，可以尝试：

```bash
# 检查迁移状态
python manage.py showmigrations

# 如果有冲突，可以尝试重置特定应用的迁移
python manage.py migrate reporter zero
python manage.py makemigrations reporter
python manage.py migrate reporter
```

### 5. 静态文件问题

如果静态文件无法加载：

```bash
# 重新收集静态文件
python manage.py collectstatic --clear --noinput

# 检查权限
sudo chown -R root:root /home/alice/auto_daily_report/staticfiles
sudo chmod -R 755 /home/alice/auto_daily_report/staticfiles
```

### 6. 邮件发送问题

如果邮件无法发送：

1. 检查SMTP设置是否正确
2. 确认邮箱密码或应用专用密码是否有效
3. 检查服务器是否能连接到SMTP服务器
4. 查看日志中的具体错误信息

### 7. Gemini API问题

如果Gemini API调用失败：

1. 确认API密钥是否正确
2. 检查服务器所在地区是否支持Gemini API
3. 考虑使用客户端代理模式，将API调用转移到前端

## 维护和更新

### 更新应用

当有新版本时，按以下步骤更新：

```bash
cd /home/alice/auto_daily_report
git pull

# 激活虚拟环境
source .venv/bin/activate

# 更新依赖
uv sync  # 如果使用uv
# 或
pip install -e .  # 如果使用pip

# 执行数据库迁移
python manage.py migrate

# 收集静态文件
python manage.py collectstatic --noinput

# 重启服务
sudo systemctl restart daily-reporter
```

### 备份数据库

定期备份SQLite数据库：

```bash
# 创建备份目录
mkdir -p /var/backups/daily-reporter

# 备份数据库
cp /home/alice/auto_daily_report/db.sqlite3 /var/backups/daily-reporter/db.sqlite3.$(date +%Y%m%d)

# 压缩备份
gzip /var/backups/daily-reporter/db.sqlite3.$(date +%Y%m%d)
```

可以设置自动备份的cron任务：

```bash
# 编辑crontab
crontab -e

# 添加每天3:00进行备份的任务
0 3 * * * mkdir -p /var/backups/daily-reporter && cp /home/alice/auto_daily_report/db.sqlite3 /var/backups/daily-reporter/db.sqlite3.$(date +\%Y\%m\%d) && gzip /var/backups/daily-reporter/db.sqlite3.$(date +\%Y\%m\%d)
```

## 性能优化

对于大多数用例，默认配置已经足够。但如果您有更高的性能需求：

1. 增加Gunicorn工作进程数（对于1核服务器，建议保持为1）：
```ini
ExecStart=/home/alice/auto_daily_report/.venv/bin/gunicorn \
    --workers 2 \  # 增加工作进程数
    --threads 2 \  # 每个工作进程的线程数
    --bind unix:/home/alice/auto_daily_report/daily_reporter.sock \
    daily_reporter_project.wsgi:application
```

2. 配置Nginx缓存静态文件：
```nginx
location /static/ {
    alias /home/alice/auto_daily_report/staticfiles/;
    expires 30d;
    add_header Cache-Control "public, max-age=2592000";
}
```

## 安全建议

1. 定期更新系统和依赖：
```bash
sudo apt update && sudo apt upgrade -y
source .venv/bin/activate
uv sync  # 或 pip install -e .
```

2. 使用强密码和不同的密码：
   - Django管理员账户
   - 数据库
   - 邮箱账户

3. 限制SSH访问：
```bash
sudo nano /etc/ssh/sshd_config
# 设置 PermitRootLogin no
# 设置 PasswordAuthentication no
sudo systemctl restart sshd
```

4. 配置防火墙：
```bash
sudo apt install -y ufw
sudo ufw allow ssh
sudo ufw allow http
sudo ufw allow https
sudo ufw enable
```

## 故障恢复

如果系统出现严重问题，可以使用以下步骤恢复：

1. 从备份恢复数据库：
```bash
gunzip /var/backups/daily-reporter/db.sqlite3.20250407.gz
cp /var/backups/daily-reporter/db.sqlite3.20250407 /home/alice/auto_daily_report/db.sqlite3
chown root:root /home/alice/auto_daily_report/db.sqlite3
```

2. 重新部署应用：
```bash
cd /home/alice
rm -rf auto_daily_report
git clone https://github.com/zhaojinyang117/auto_daily_report.git
cd auto_daily_report
# 然后按照安装步骤重新配置
```

## 结论

自动日报生成器是一个功能强大且易于部署的工具，适合个人和团队使用。通过本文档的指导，您应该能够成功部署并维护这个系统。

如果您在部署过程中遇到任何问题，请查阅项目的GitHub仓库或提交issue获取帮助。
