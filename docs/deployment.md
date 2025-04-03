# 生产环境部署指南

本文档详细介绍如何将自动日报生成器部署到生产环境。

## 快速部署（一键安装）

项目提供了一键安装脚本，可以自动完成所有部署步骤。这是推荐的部署方式，尤其适合不熟悉Linux服务器配置的用户。

### 使用一键安装脚本

1. 以root权限登录您的Linux服务器

2. 下载安装脚本：
```bash
curl -O https://raw.githubusercontent.com/zhaojinyang117/auto_daily_report/main/install.sh
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

脚本会自动执行以下任务：
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

### 故障排除

如果安装过程中遇到问题，脚本会提供详细的错误信息和排查建议。您也可以查看以下日志文件来排查问题：

- Gunicorn日志：`sudo journalctl -u daily-reporter`
- Nginx错误日志：`sudo cat /var/log/nginx/error.log`
- 应用日志：`cat /安装目录/debug.log`

## 手动部署详细步骤

如果您希望手动部署或需要更精细地控制部署过程，以下是详细的步骤说明。

## 系统要求

- 一台Linux服务器（建议配置：1核1G或更高）
- Python 3.12+
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
git clone https://github.com/zhaojinyang117/auto_daily_report.git
cd auto_daily_report
```

### 3. 创建虚拟环境并安装依赖

```bash
# 创建虚拟环境
python3 -m venv .venv

# 激活虚拟环境
source .venv/bin/activate

# 安装依赖
pip install -e .
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
- `ALLOWED_HOSTS`：应包含您的域名或服务器IP地址
- `GEMINI_API_KEY`：Gemini API的密钥（如果您使用AI功能）
- `USER_NAME`：姓名（用于日报标题）
- `EMAIL_SIGNATURE_NAME`：邮件签名显示的英文名
- `EMAIL_SIGNATURE_PHONE`：邮件签名显示的电话
- `EMAIL_FROM`：邮件发送地址
- `EMAIL_PASSWORD`：邮件密码或应用专用密码
- `EMAIL_TO`：收件人地址，多个用逗号分隔
- `SMTP_SERVER`：SMTP服务器地址
- `SMTP_PORT`：SMTP端口（通常是465用于SSL连接）
- `LOG_LEVEL`：日志记录级别（DEBUG/INFO/WARNING/ERROR/CRITICAL）

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
    --workers 1 \
    --bind unix:/var/www/auto_daily_report/daily_reporter.sock \
    daily_reporter_project.wsgi:application
Environment="DJANGO_SETTINGS_MODULE=daily_reporter_project.settings"

[Install]
WantedBy=multi-user.target
```

设置目录权限：

```bash
# 更改应用目录的所有者
sudo chown -R www-data:www-data /var/www/auto_daily_report

# 确保日志目录存在
mkdir -p /var/www/auto_daily_report/logs
sudo chown -R www-data:www-data /var/www/auto_daily_report/logs
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

添加以下内容，替换`example.com`为您的域名或服务器IP：

```nginx
server {
    listen 80;
    server_name example.com;

    location = /favicon.ico { access_log off; log_not_found off; }
    
    location /static/ {
        alias /var/www/auto_daily_report/staticfiles/;
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

使用Let's Encrypt设置HTTPS：

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d example.com
```

### 9. 设置定时任务

配置cron任务以定期运行发送报告的脚本：

```bash
# 确保脚本具有执行权限
chmod +x /var/www/auto_daily_report/scripts/daily_report_runner.sh
chmod +x /var/www/auto_daily_report/scripts/setup_cron.sh

# 配置cron任务
cd /var/www/auto_daily_report
bash scripts/setup_cron.sh
```

这将设置一个每15分钟运行一次的cron任务，检查是否有需要发送的日报。

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
/var/www/auto_daily_report/debug.log {
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
cp /var/www/auto_daily_report/db.sqlite3 /var/backups/daily-reporter/db.sqlite3.$(date +%Y%m%d)

# 压缩备份
gzip /var/backups/daily-reporter/db.sqlite3.$(date +%Y%m%d)
```

可以设置自动备份的cron任务：

```bash
# 编辑crontab
crontab -e

# 添加每天3:00进行备份的任务
0 3 * * * mkdir -p /var/backups/daily-reporter && cp /var/www/auto_daily_report/db.sqlite3 /var/backups/daily-reporter/db.sqlite3.$(date +\%Y\%m\%d) && gzip /var/backups/daily-reporter/db.sqlite3.$(date +\%Y\%m\%d)
```

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

检查runner脚本中的路径是否正确：

```bash
cat /var/www/auto_daily_report/scripts/daily_report_runner.sh
```

### 手动测试日报发送

要手动测试日报发送功能，可以执行以下命令：

```bash
cd /var/www/auto_daily_report
source .venv/bin/activate
python manage.py send_daily_reports --all
```

或者发送特定用户的日报：

```bash
python manage.py send_daily_reports --user=用户名
```

## 高级故障排除

在部署过程中，您可能会遇到一些常见问题。以下是一些高级故障排除技巧：

### 1. 非标准部署路径问题

如果您将应用部署在非标准路径（例如/home/user/auto_daily_report而不是/var/www/auto_daily_report），需要相应地调整所有配置文件中的路径。

#### Gunicorn服务文件路径错误

如果遇到类似以下错误：

```
Failed to locate executable /var/www/auto_daily_report/.venv/bin/gunicorn: No such file or directory
```

修改systemd服务文件中的所有路径以匹配您的实际部署路径：

```bash
sudo nano /etc/systemd/system/daily-reporter.service
```

```ini
[Service]
User=www-data
Group=www-data
WorkingDirectory=/home/user/auto_daily_report  # 修改为实际路径
ExecStart=/home/user/auto_daily_report/.venv/bin/gunicorn \  # 修改为实际路径
    --access-logfile - \
    --workers 1 \
    --bind unix:/home/user/auto_daily_report/daily_reporter.sock \  # 修改为实际路径
    daily_reporter_project.wsgi:application
```

然后重新加载并重启服务：

```bash
sudo systemctl daemon-reload
sudo systemctl restart daily-reporter
```

#### Nginx配置中的路径错误

同样，Nginx配置也需要调整：

```nginx
location /static/ {
    alias /home/user/auto_daily_report/staticfiles/;  # 修改为实际路径
}

location / {
    include proxy_params;
    proxy_pass http://unix:/home/user/auto_daily_report/daily_reporter.sock;  # 修改为实际路径
}
```

### 2. Django ALLOWED_HOSTS 设置问题

如果遇到DisallowedHost错误：

```
DisallowedHost at /
Invalid HTTP_HOST header: 'your-domain.com'. You may need to add 'your-domain.com' to ALLOWED_HOSTS.
```

需要在settings.py中正确设置ALLOWED_HOSTS：

```bash
nano /path/to/auto_daily_report/daily_reporter_project/settings.py
```

```python
# 注意语法，星号需要放在引号内
ALLOWED_HOSTS = ['your-domain.com', 'your-ip-address', 'localhost', '*']
```

不正确的语法示例（会导致错误）：
```python
ALLOWED_HOSTS = [*]  # 错误！星号必须放在引号内
```

修改后重启Gunicorn服务：
```bash
sudo systemctl restart daily-reporter
```

### 3. CSRF验证失败问题

如果使用HTTPS访问网站，但遇到CSRF验证失败：

```
CSRF验证失败. 请求被中断.
Reason given for failure: Origin checking failed - https://example.com does not match any trusted origins.
```

需要在settings.py中添加CSRF_TRUSTED_ORIGINS设置：

```python
CSRF_TRUSTED_ORIGINS = ['https://your-domain.com', 'http://your-domain.com']
```

如果还使用IP地址访问：
```python
CSRF_TRUSTED_ORIGINS = [
    'https://your-domain.com', 
    'http://your-domain.com',
    'http://your-ip-address',
    'https://your-ip-address'
]
```

### 4. 静态文件问题排查

#### JavaScript效果丢失

如果网站缺少JavaScript效果，可能是静态文件未正确收集或加载：

1. 检查staticfiles目录中是否有所需的JavaScript文件：
```bash
ls -la /path/to/auto_daily_report/staticfiles/reporter/js/
```

2. 确保settings.py中有正确的静态文件配置：
```python
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
```

3. 如果使用自定义静态文件目录，添加STATICFILES_DIRS设置：
```python
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]
```

4. 重新收集静态文件：
```bash
python manage.py collectstatic --clear --noinput
```

#### 静态文件收集警告

如果在运行collectstatic时看到类似这样的警告：
```
Found another file with the destination path 'reporter/js/script.js'. It will be ignored since only the first encountered file is collected.
```

这表明在多个位置定义了相同名称的静态文件。要解决此问题：

1. 找出重复的静态文件：
```bash
find /path/to/auto_daily_report -name "script.js"
```

2. 确保每个静态文件只在适当的位置定义一次
3. 明确定义STATICFILES_DIRS以避免歧义

### 5. 用户权限问题

如果遇到权限错误，确保应用目录和文件有正确的所有权和权限：

```bash
# 设置所有权
sudo chown -R www-data:www-data /path/to/auto_daily_report
sudo chown -R www-data:www-data /path/to/auto_daily_report/.venv

# 设置正确的权限
sudo chmod -R 755 /path/to/auto_daily_report/staticfiles
sudo chmod -R 755 /path/to/auto_daily_report/.venv/bin
```

### 6. 使用根用户（临时解决方案）

如果遇到权限问题且无法立即解决，可以临时将服务配置为使用root用户（**不推荐用于生产环境**）：

```ini
[Service]
User=root
Group=root
# 其他设置不变
```

然后重启服务：
```bash
sudo systemctl daemon-reload
sudo systemctl restart daily-reporter
```

### 7. Debug模式快速排查

为快速诊断问题，可以临时启用Django的DEBUG模式：

1. 在settings.py中设置：
```python
DEBUG = True
```

2. 重启Gunicorn服务：
```bash
sudo systemctl restart daily-reporter
```

3. 访问网站并查看详细错误信息
4. **重要**：排查完成后务必将DEBUG设置回False

### 8. 日志检查

详细检查各种日志以获取错误信息：

```bash
# Django/Gunicorn日志
sudo journalctl -u daily-reporter -n 100

# Nginx错误日志
sudo cat /var/log/nginx/error.log

# Django应用日志
cat /path/to/auto_daily_report/debug.log
``` 