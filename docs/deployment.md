# 生产环境部署指南

本文档详细介绍如何将自动日报生成器部署到生产环境。

## 系统要求

- 一台1核1G（或更高配置）的Linux服务器
- Python 3.9+
- Nginx
- Systemd（用于服务管理）

## 部署步骤

### 1. 准备服务器环境

```bash
# 更新系统包
sudo apt update && sudo apt upgrade -y

# 安装必要的系统依赖
sudo apt install -y python3-pip python3-venv nginx git
```

### 2. 克隆代码仓库

```bash
# 选择一个合适的目录
mkdir -p /var/www
cd /var/www

# 克隆代码仓库
git clone https://github.com/yourusername/auto_daily_report.git
cd auto_daily_report
```

### 3. 创建虚拟环境并安装依赖

```bash
# 创建虚拟环境
python3 -m venv .venv

# 激活虚拟环境
source .venv/bin/activate

# 安装依赖（包括gunicorn）
pip install -e .

# 或者，如果服务器上安装了uv（可选但更快）
# pip install uv
# uv install -e .
```

### 4. 配置环境变量

```bash
# 创建.env文件
cp .env.example .env

# 编辑.env文件，配置必要的环境变量
nano .env
```

确保配置了以下环境变量：
- `SECRET_KEY`：Django的密钥，生产环境中应使用随机生成的强密钥
- `DEBUG`：生产环境中应设置为 `False`
- `ALLOWED_HOSTS`：应包含您的域名
- `GEMINI_API_KEY`：Gemini API的密钥（如果您使用AI功能）
- 邮件发送相关的配置

### 5. 初始化数据库

```bash
# 执行数据库迁移
python manage.py migrate

# 收集静态文件
python manage.py collectstatic

# 创建管理员用户
python manage.py createsuperuser
```

### 6. 配置Gunicorn服务

创建systemd服务文件：

```bash
sudo nano /etc/systemd/system/daily-reporter.service
```

添加以下内容：

```ini
[Unit]
Description=Daily Report Generator Gunicorn Daemon
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/auto_daily_report
ExecStart=/var/www/auto_daily_report/.venv/bin/gunicorn \
    --access-logfile - \
    --workers 2 \
    --bind unix:/var/www/auto_daily_report/daily_reporter.sock \
    daily_reporter_project.wsgi:application

[Install]
WantedBy=multi-user.target
```

启动Gunicorn服务：

```bash
sudo systemctl start daily-reporter
sudo systemctl enable daily-reporter
```

### 7. 配置Nginx

创建Nginx配置文件：

```bash
sudo nano /etc/nginx/sites-available/daily-reporter
```

添加以下内容，替换`example.com`为您的域名：

```nginx
server {
    listen 80;
    server_name example.com;

    location = /favicon.ico { access_log off; log_not_found off; }
    
    location /static/ {
        root /var/www/auto_daily_report;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/var/www/auto_daily_report/daily_reporter.sock;
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

建议使用Let's Encrypt设置HTTPS：

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d example.com
```

### 9. 设置Cron任务

设置cron任务以定期运行发送报告的脚本：

```bash
# 确保脚本具有执行权限
chmod +x /var/www/auto_daily_report/scripts/daily_report_runner.sh
chmod +x /var/www/auto_daily_report/scripts/setup_cron.sh

# 配置cron任务
cd /var/www/auto_daily_report
bash scripts/setup_cron.sh
```

### 10. 设置日志轮转

为防止日志文件过大，设置日志轮转：

```bash
sudo nano /etc/logrotate.d/daily-reporter
```

添加以下内容：

```
/var/www/auto_daily_report/logs/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
}
```

## 维护和更新

### 更新应用

当有新版本时，按以下步骤更新：

```bash
cd /var/www/auto_daily_report
git pull

# 激活虚拟环境
source .venv/bin/activate

# 更新依赖
pip install -e .

# 执行数据库迁移
python manage.py migrate

# 收集静态文件
python manage.py collectstatic

# 重启服务
sudo systemctl restart daily-reporter
```

### 备份数据库

定期备份SQLite数据库：

```bash
# 创建备份目录
mkdir -p /var/backups/daily-reporter

# 备份数据库
cp /var/www/auto_daily_report/db.sqlite3 /var/backups/daily-reporter/db.sqlite3.$(date +%Y%m%d)

# 压缩备份
gzip /var/backups/daily-reporter/db.sqlite3.$(date +%Y%m%d)
```

可以设置自动备份的cron任务：

```bash
# 编辑crontab
crontab -e

# 添加每天3:00进行备份的任务
0 3 * * * cp /var/www/auto_daily_report/db.sqlite3 /var/backups/daily-reporter/db.sqlite3.$(date +\%Y\%m\%d) && gzip /var/backups/daily-reporter/db.sqlite3.$(date +\%Y\%m\%d)
```

## 性能优化

对于1C1G服务器，可以考虑以下优化：

1. 减少Gunicorn的worker数量为1-2（配置中已设置为2）
2. 为数据库查询添加索引
3. 使用Whitenoise处理静态文件，减轻Nginx负担
4. 定期清理旧的日志和历史记录

## 常见问题排查

### 服务无法启动

检查Gunicorn日志：

```bash
sudo journalctl -u daily-reporter
```

### 无法访问网站

检查Nginx配置和日志：

```bash
sudo nginx -t
sudo cat /var/log/nginx/error.log
```

### 定时任务不执行

检查cron日志：

```bash
grep CRON /var/log/syslog
```

检查cron任务是否正确设置：

```bash
crontab -l
``` 