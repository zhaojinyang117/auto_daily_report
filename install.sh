#!/bin/bash

# 自动日报生成器 - Linux一键部署安装脚本
# 此脚本会自动完成所有安装步骤，包括环境配置、依赖安装、服务设置等

# 显示彩色输出的函数
print_green() {
    echo -e "\033[32m$1\033[0m"
}

print_yellow() {
    echo -e "\033[33m$1\033[0m"
}

print_red() {
    echo -e "\033[31m$1\033[0m"
}

print_blue() {
    echo -e "\033[34m$1\033[0m"
}

# 检查是否以root权限运行
check_root() {
    if [ "$EUID" -ne 0 ]; then
        print_red "请以root权限运行此脚本"
        print_yellow "执行: sudo bash install.sh"
        exit 1
    fi
}

# 检测Linux发行版
detect_distro() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$NAME
        VER=$VERSION_ID
    else
        print_red "无法检测到Linux发行版，将尝试使用通用方法安装"
        OS="Unknown"
        VER="Unknown"
    fi
    print_blue "检测到操作系统: $OS $VER"
}

# 安装系统依赖
install_system_dependencies() {
    print_blue "正在安装系统依赖..."
    
    if [ -f /etc/debian_version ] || [ "$ID" == "ubuntu" ] || [ "$ID" == "debian" ]; then
        # Debian/Ubuntu系统
        apt update
        apt upgrade -y
        apt install -y python3 python3-pip python3-venv nginx git certbot python3-certbot-nginx curl
    elif [ -f /etc/redhat-release ] || [ "$ID" == "centos" ] || [ "$ID" == "fedora" ] || [ "$ID" == "rhel" ]; then
        # CentOS/RHEL/Fedora系统
        if [ "$ID" == "centos" ] && [ "$VER" == "7" ]; then
            # CentOS 7需要特殊处理
            yum update -y
            yum install -y epel-release
            yum install -y python3 python3-pip nginx git curl
            if ! command -v certbot &> /dev/null; then
                yum install -y certbot certbot-nginx
            fi
        else
            # CentOS 8+ / Fedora / RHEL
            dnf update -y
            dnf install -y python3 python3-pip nginx git curl certbot certbot-nginx
        fi
    else
        print_red "不支持的Linux发行版，请手动安装依赖"
        print_yellow "需要安装: Python 3.x, pip, venv, nginx, git, certbot"
        exit 1
    fi
    
    print_green "系统依赖安装完成"
}

# 获取项目代码
clone_repository() {
    print_blue "正在获取项目代码..."
    
    # 确认安装目录
    read -e -p "请输入安装目录 [默认: /var/www/auto_daily_report]: " INSTALL_DIR
    INSTALL_DIR=${INSTALL_DIR:-/var/www/auto_daily_report}
    
    # 创建安装目录
    mkdir -p $(dirname "$INSTALL_DIR")
    
    # 检查目录是否已存在项目
    if [ -d "$INSTALL_DIR" ]; then
        read -p "目录 $INSTALL_DIR 已存在，是否覆盖? [y/N]: " OVERWRITE
        if [[ $OVERWRITE =~ ^[Yy]$ ]]; then
            rm -rf "$INSTALL_DIR"
        else
            print_yellow "将尝试使用现有目录"
        fi
    fi
    
    # 克隆仓库
    if [ ! -d "$INSTALL_DIR/.git" ]; then
        read -e -p "请输入Git仓库地址 [默认: https://github.com/zhaojinyang117/auto_daily_report.git]: " REPO_URL
        REPO_URL=${REPO_URL:-https://github.com/zhaojinyang117/auto_daily_report.git}
        
        # 添加分支选择
        read -e -p "请输入要克隆的分支名称 [默认: django]: " BRANCH_NAME
        BRANCH_NAME=${BRANCH_NAME:-django}
        
        print_yellow "正在克隆仓库 $REPO_URL 的 $BRANCH_NAME 分支..."
        
        # 使用 -b 参数指定分支
        git clone -b "$BRANCH_NAME" "$REPO_URL" "$INSTALL_DIR"
        
        if [ $? -ne 0 ]; then
            print_red "克隆仓库失败，请检查仓库地址和分支名称是否正确"
            exit 1
        fi
    else
        print_yellow "使用现有仓库目录"
        cd "$INSTALL_DIR"
        
        # 如果使用现有目录，询问是否切换分支
        read -p "是否要切换到特定分支? [y/N]: " SWITCH_BRANCH
        if [[ $SWITCH_BRANCH =~ ^[Yy]$ ]]; then
            # 获取当前分支
            CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
            print_yellow "当前分支: $CURRENT_BRANCH"
            
            # 获取远程所有分支
            git fetch --all
            
            # 列出所有可用分支
            print_yellow "可用的远程分支:"
            git branch -r | grep -v "\->" | sed "s/origin\///"
            
            # 询问要切换到哪个分支
            read -e -p "请输入要切换到的分支名称: " TARGET_BRANCH
            
            if [ ! -z "$TARGET_BRANCH" ]; then
                git checkout "$TARGET_BRANCH"
                if [ $? -ne 0 ]; then
                    # 如果直接切换失败，尝试创建跟踪分支
                    git checkout -b "$TARGET_BRANCH" "origin/$TARGET_BRANCH"
                    if [ $? -ne 0 ]; then
                        print_red "切换分支失败，将保持在当前分支"
                    else
                        print_green "已切换到分支: $TARGET_BRANCH"
                    fi
                else
                    print_green "已切换到分支: $TARGET_BRANCH"
                fi
            fi
        fi
        
        # 更新代码
        git pull
    fi
    
    cd "$INSTALL_DIR"
    print_green "项目代码获取完成，当前目录: $(pwd)"
    print_green "当前分支: $(git rev-parse --abbrev-ref HEAD)"
}

# 设置Python虚拟环境
setup_virtual_env() {
    print_blue "正在设置Python虚拟环境..."
    
    cd "$INSTALL_DIR"
    
    # 检查是否已安装uv
    if ! command -v uv &> /dev/null; then
        print_yellow "未检测到uv工具，正在安装..."
        curl -fsSL https://astral.sh/uv/install.sh | bash
        # 刷新PATH以便使用新安装的uv
        if [ -f "$HOME/.cargo/env" ]; then
            source "$HOME/.cargo/env"
        else
            export PATH="$HOME/.cargo/bin:$PATH"
        fi
    fi
    
    print_yellow "使用uv创建虚拟环境并安装依赖..."
    
    # 创建虚拟环境
    uv venv .venv
    
    # 激活虚拟环境
    source .venv/bin/activate
    
    # 安装依赖
    if [ -f requirements.txt ]; then
        uv sync -r requirements.txt
    elif [ -f pyproject.toml ]; then
        uv sync
    else
        uv pip install -e .
    fi
    
    # 安装gunicorn（如果依赖中未包含）
    if ! pip show gunicorn &> /dev/null; then
        print_yellow "正在安装gunicorn..."
        uv pip install gunicorn
    fi
    
    print_green "Python虚拟环境设置完成"
}

# 生成随机Django密钥
generate_django_secret_key() {
    python3 -c 'import secrets; print(secrets.token_urlsafe(50))'
}

# 配置环境变量
configure_env_variables() {
    print_blue "正在配置环境变量..."
    
    cd "$INSTALL_DIR"
    
    # 检查是否已存在.env文件
    if [ -f .env ]; then
        read -p ".env文件已存在，是否覆盖? [y/N]: " OVERWRITE_ENV
        if [[ ! $OVERWRITE_ENV =~ ^[Yy]$ ]]; then
            print_yellow "保留现有.env文件"
            return
        fi
    fi
    
    # 复制样例配置
    if [ -f .env.example ]; then
        cp .env.example .env
    else
        # 如果没有样例配置，创建一个新的
        cat > .env << EOF
# Django 配置
SECRET_KEY=$(generate_django_secret_key)
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1

# Gemini API配置
GEMINI_API_KEY=your_gemini_api_key_here

# 个人信息配置
USER_NAME=你的姓名                     # 姓名（用于日报标题）
EMAIL_SIGNATURE_NAME=YOUR_NAME_HERE    # 邮件签名显示的英文名
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
EOF
    fi
    
    # 交互式配置关键参数
    print_yellow "请配置以下关键参数:"
    
    # 配置服务器域名或IP
    read -e -p "输入服务器域名或IP地址（多个用逗号分隔）[默认: localhost,127.0.0.1]: " ALLOWED_HOSTS
    ALLOWED_HOSTS=${ALLOWED_HOSTS:-localhost,127.0.0.1}
    sed -i "s/ALLOWED_HOSTS=.*/ALLOWED_HOSTS=$ALLOWED_HOSTS/g" .env
    
    # Gemini API
    read -e -p "输入Gemini API密钥（留空则后续手动配置）: " GEMINI_KEY
    if [ ! -z "$GEMINI_KEY" ]; then
        sed -i "s/GEMINI_API_KEY=.*/GEMINI_API_KEY=$GEMINI_KEY/g" .env
    fi
    
    # 用户信息
    read -e -p "输入姓名（用于日报标题）: " USER_NAME
    if [ ! -z "$USER_NAME" ]; then
        sed -i "s/USER_NAME=.*/USER_NAME=$USER_NAME/g" .env
    fi
    
    read -e -p "输入邮件签名英文名: " EMAIL_SIG_NAME
    if [ ! -z "$EMAIL_SIG_NAME" ]; then
        sed -i "s/EMAIL_SIGNATURE_NAME=.*/EMAIL_SIGNATURE_NAME=$EMAIL_SIG_NAME/g" .env
    fi
    
    read -e -p "输入电话号码: " EMAIL_SIG_PHONE
    if [ ! -z "$EMAIL_SIG_PHONE" ]; then
        sed -i "s/EMAIL_SIGNATURE_PHONE=.*/EMAIL_SIGNATURE_PHONE=$EMAIL_SIG_PHONE/g" .env
    fi
    
    # 邮件配置
    read -e -p "输入发送邮箱地址: " EMAIL_FROM
    if [ ! -z "$EMAIL_FROM" ]; then
        sed -i "s/EMAIL_FROM=.*/EMAIL_FROM=$EMAIL_FROM/g" .env
    fi
    
    read -e -p "输入发送邮箱密码或应用专用密码: " EMAIL_PASSWORD
    if [ ! -z "$EMAIL_PASSWORD" ]; then
        sed -i "s/EMAIL_PASSWORD=.*/EMAIL_PASSWORD=$EMAIL_PASSWORD/g" .env
    fi
    
    read -e -p "输入收件人邮箱地址（多个用逗号分隔）: " EMAIL_TO
    if [ ! -z "$EMAIL_TO" ]; then
        sed -i "s/EMAIL_TO=.*/EMAIL_TO=$EMAIL_TO/g" .env
    fi
    
    read -e -p "输入SMTP服务器地址: " SMTP_SERVER
    if [ ! -z "$SMTP_SERVER" ]; then
        sed -i "s/SMTP_SERVER=.*/SMTP_SERVER=$SMTP_SERVER/g" .env
    fi
    
    read -e -p "输入SMTP端口 [默认: 465]: " SMTP_PORT
    SMTP_PORT=${SMTP_PORT:-465}
    sed -i "s/SMTP_PORT=.*/SMTP_PORT=$SMTP_PORT/g" .env
    
    print_green ".env文件配置完成"
}

# 初始化数据库
initialize_database() {
    print_blue "正在初始化数据库..."
    
    cd "$INSTALL_DIR"
    source .venv/bin/activate
    
    # 执行数据库迁移
    python manage.py migrate
    
    # 收集静态文件
    python manage.py collectstatic --noinput
    
    # 创建管理员用户
    print_yellow "创建管理员账户用于登录系统后台"
    python manage.py createsuperuser
    
    print_green "数据库初始化完成"
}

# 配置Gunicorn服务
setup_gunicorn() {
    print_blue "正在配置Gunicorn服务..."
    
    # 创建systemd服务文件
    cat > /etc/systemd/system/daily-reporter.service << EOF
[Unit]
Description=Daily Report Generator Gunicorn Daemon
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=$INSTALL_DIR
ExecStart=$INSTALL_DIR/.venv/bin/gunicorn \\
    --access-logfile - \\
    --workers 1 \\
    --bind unix:$INSTALL_DIR/daily_reporter.sock \\
    daily_reporter_project.wsgi:application
Environment="DJANGO_SETTINGS_MODULE=daily_reporter_project.settings"

[Install]
WantedBy=multi-user.target
EOF
    
    # 设置目录权限
    mkdir -p "$INSTALL_DIR/logs"
    chown -R www-data:www-data "$INSTALL_DIR"
    
    # 重新加载systemd配置
    systemctl daemon-reload
    
    # 启动并启用服务
    systemctl start daily-reporter
    systemctl enable daily-reporter
    
    print_green "Gunicorn服务配置完成，服务已启动"
}

# 配置Nginx
setup_nginx() {
    print_blue "正在配置Nginx..."
    
    # 获取服务器域名或IP
    SERVER_NAME=$(grep ALLOWED_HOSTS .env | cut -d '=' -f2 | cut -d ',' -f1)
    
    # 创建Nginx配置文件
    cat > /etc/nginx/sites-available/daily-reporter << EOF
server {
    listen 80;
    server_name $SERVER_NAME;

    location = /favicon.ico { access_log off; log_not_found off; }
    
    location /static/ {
        alias $INSTALL_DIR/staticfiles/;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:$INSTALL_DIR/daily_reporter.sock;
    }
}
EOF
    
    # 检查proxy_params文件是否存在
    if [ ! -f /etc/nginx/proxy_params ]; then
        cat > /etc/nginx/proxy_params << EOF
proxy_set_header Host \$http_host;
proxy_set_header X-Real-IP \$remote_addr;
proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
proxy_set_header X-Forwarded-Proto \$scheme;
EOF
    fi
    
    # 启用站点
    ln -sf /etc/nginx/sites-available/daily-reporter /etc/nginx/sites-enabled/
    
    # 检查Nginx配置
    nginx -t
    if [ $? -ne 0 ]; then
        print_red "Nginx配置测试失败，请检查配置"
        exit 1
    fi
    
    # 重启Nginx
    systemctl restart nginx
    
    print_green "Nginx配置完成，服务已重启"
}

# 配置HTTPS
setup_https() {
    print_blue "正在配置HTTPS..."
    
    read -p "是否配置HTTPS? [y/N]: " SETUP_HTTPS
    if [[ $SETUP_HTTPS =~ ^[Yy]$ ]]; then
        read -e -p "请输入域名 (例如 example.com): " DOMAIN_NAME
        
        if [ -z "$DOMAIN_NAME" ]; then
            print_yellow "未提供域名，跳过HTTPS配置"
            return
        fi
        
        print_yellow "正在使用Let's Encrypt获取SSL证书..."
        certbot --nginx -d "$DOMAIN_NAME" --non-interactive --agree-tos --email "webmaster@$DOMAIN_NAME" --redirect
        
        if [ $? -eq 0 ]; then
            print_green "HTTPS配置成功"
        else
            print_red "HTTPS配置失败，请稍后手动运行: certbot --nginx -d $DOMAIN_NAME"
        fi
    else
        print_yellow "跳过HTTPS配置"
    fi
}

# 设置cron任务
setup_cron_job() {
    print_blue "正在设置定时任务..."
    
    cd "$INSTALL_DIR"
    
    # 确保脚本有执行权限
    chmod +x scripts/daily_report_runner.sh
    chmod +x scripts/setup_cron.sh
    
    # 更新runner脚本中的项目路径
    sed -i "s|PROJECT_PATH=\"/path/to/auto_daily_report\"|PROJECT_PATH=\"$INSTALL_DIR\"|g" scripts/daily_report_runner.sh
    
    # 设置cron任务
    bash scripts/setup_cron.sh
    
    print_green "定时任务配置完成"
}

# 配置日志轮转
setup_log_rotation() {
    print_blue "正在配置日志轮转..."
    
    cat > /etc/logrotate.d/daily-reporter << EOF
$INSTALL_DIR/logs/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
}
$INSTALL_DIR/debug.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
}
EOF
    
    print_green "日志轮转配置完成"
}

# 测试安装
test_installation() {
    print_blue "正在测试安装..."
    
    # 检查Gunicorn服务状态
    systemctl status daily-reporter
    if [ $? -ne 0 ]; then
        print_red "Gunicorn服务未正常运行，请检查日志"
        systemctl status daily-reporter
        journalctl -u daily-reporter
    else
        print_green "Gunicorn服务运行正常"
    fi
    
    # 检查Nginx状态
    systemctl status nginx
    if [ $? -ne 0 ]; then
        print_red "Nginx服务未正常运行，请检查日志"
        systemctl status nginx
        cat /var/log/nginx/error.log
    else
        print_green "Nginx服务运行正常"
    fi
    
    # 检查静态文件是否正确收集
    if [ -d "$INSTALL_DIR/staticfiles" ]; then
        print_green "静态文件目录存在"
        # 检查静态文件数量
        STATIC_FILES_COUNT=$(find "$INSTALL_DIR/staticfiles" -type f | wc -l)
        if [ $STATIC_FILES_COUNT -gt 0 ]; then
            print_green "已收集 $STATIC_FILES_COUNT 个静态文件"
        else
            print_red "静态文件目录为空，可能未正确收集静态文件"
            print_yellow "尝试重新收集静态文件..."
            cd "$INSTALL_DIR"
            source .venv/bin/activate
            python manage.py collectstatic --noinput
        fi
        
        # 检查背景图片是否存在
        if [ ! -f "$INSTALL_DIR/staticfiles/background.jpg" ]; then
            print_yellow "未找到默认背景图片，尝试创建..."
            
            # 检查是否有默认图片可以复制
            if [ -f "$INSTALL_DIR/reporter/static/reporter/images/background.jpg" ]; then
                cp "$INSTALL_DIR/reporter/static/reporter/images/background.jpg" "$INSTALL_DIR/staticfiles/background.jpg"
                print_green "已从项目中复制背景图片"
            else
                # 如果没有默认图片，生成一个简单的纯色背景图片
                print_yellow "未找到源背景图片，正在生成默认背景..."
                if command -v convert &> /dev/null; then
                    # 使用ImageMagick生成背景图片
                    convert -size 1920x1080 gradient:white-lightblue "$INSTALL_DIR/staticfiles/background.jpg"
                    print_green "已生成默认背景图片"
                else
                    # 如果没有ImageMagick，下载一个简单的背景图片
                    if command -v curl &> /dev/null; then
                        curl -s -o "$INSTALL_DIR/staticfiles/background.jpg" "https://source.unsplash.com/random/1920x1080/?blue,minimal"
                        print_green "已下载默认背景图片"
                    else
                        print_red "无法创建默认背景图片，请稍后手动添加"
                    fi
                fi
            fi
            
            # 设置正确的权限
            chown www-data:www-data "$INSTALL_DIR/staticfiles/background.jpg"
            chmod 644 "$INSTALL_DIR/staticfiles/background.jpg"
        else
            print_green "默认背景图片已存在"
        fi
    else
        print_red "静态文件目录不存在，静态文件收集可能失败"
        print_yellow "尝试重新收集静态文件..."
        cd "$INSTALL_DIR"
        source .venv/bin/activate
        mkdir -p "$INSTALL_DIR/staticfiles"
        python manage.py collectstatic --noinput
    fi
    
    # 检查网站是否可访问
    SERVER_NAME=$(grep ALLOWED_HOSTS .env | cut -d '=' -f2 | cut -d ',' -f1)
    print_yellow "请在浏览器中访问: http://$SERVER_NAME"
    print_yellow "管理后台地址: http://$SERVER_NAME/admin/"
    
    # 测试cron任务
    print_yellow "正在测试cron任务..."
    bash scripts/daily_report_runner.sh
    if [ $? -eq 0 ]; then
        print_green "Cron任务测试成功"
    else
        print_red "Cron任务测试失败，请检查日志"
        cat "$INSTALL_DIR/logs/cron.log"
    fi
}

# 安装完成提示
installation_complete() {
    SERVER_NAME=$(grep ALLOWED_HOSTS .env | cut -d '=' -f2 | cut -d ',' -f1)
    
    print_green "\n============================================================"
    print_green "              自动日报生成器安装完成！                     "
    print_green "============================================================"
    print_green "网站地址: http://$SERVER_NAME"
    print_green "管理后台: http://$SERVER_NAME/admin/"
    print_green "安装目录: $INSTALL_DIR"
    print_green "日志目录: $INSTALL_DIR/logs/"
    print_green "============================================================"
    print_yellow "常用维护命令："
    print_yellow "  - 重启应用: sudo systemctl restart daily-reporter"
    print_yellow "  - 重启Nginx: sudo systemctl restart nginx"
    print_yellow "  - 查看应用日志: sudo journalctl -u daily-reporter"
    print_yellow "  - 查看Nginx日志: sudo cat /var/log/nginx/error.log"
    print_yellow "  - 手动执行日报: bash $INSTALL_DIR/scripts/daily_report_runner.sh"
    print_yellow "  - 查看定时任务: crontab -l"
    print_green "============================================================"
    print_green "如果您配置了HTTPS，请使用https://$SERVER_NAME访问"
    print_yellow "初次使用请登录管理后台完善配置，祝使用愉快！"
    print_green "============================================================"
}

# 处理异常终止
handle_exit() {
    print_red "\n安装被中断，请检查以上错误信息"
    print_yellow "您可以修复问题后重新运行此脚本"
    exit 1
}

# 主函数
main() {
    # 设置捕获异常终止
    trap handle_exit ERR
    
    print_blue "===== 自动日报生成器部署与管理脚本 ====="
    print_yellow "请选择操作类型:"
    echo "1) 安装系统"
    echo "2) 卸载系统"
    read -p "请输入选项 [1-2]: " OPERATION_TYPE
    
    # 检查root权限
    check_root
    
    # 根据选择的操作类型执行不同的功能
    case $OPERATION_TYPE in
        1)
            install_system
            ;;
        2)
            uninstall_system
            ;;
        *)
            print_red "无效的选择，请输入1或2"
            exit 1
            ;;
    esac
}

# 安装系统
install_system() {
    print_blue "===== 开始安装自动日报生成器 ====="
    
    # 检测Linux发行版
    detect_distro
    
    # 安装系统依赖
    install_system_dependencies
    
    # 获取项目代码
    clone_repository
    
    # 设置Python虚拟环境
    setup_virtual_env
    
    # 配置环境变量
    configure_env_variables
    
    # 初始化数据库
    initialize_database
    
    # 配置Gunicorn服务
    setup_gunicorn
    
    # 配置Nginx
    setup_nginx
    
    # 配置HTTPS
    setup_https
    
    # 设置cron任务
    setup_cron_job
    
    # 配置日志轮转
    setup_log_rotation
    
    # 测试安装
    test_installation
    
    # 安装完成提示
    installation_complete
}

# 卸载系统
uninstall_system() {
    print_blue "===== 开始卸载自动日报生成器 ====="
    
    # 确认卸载
    print_red "警告：卸载将删除所有相关配置和数据！"
    read -p "确认要卸载系统吗？这将删除所有相关数据和配置 [y/N]: " CONFIRM_UNINSTALL
    if [[ ! $CONFIRM_UNINSTALL =~ ^[Yy]$ ]]; then
        print_yellow "卸载操作已取消"
        exit 0
    fi
    
    # 获取安装目录
    read -e -p "请输入当前安装目录 [默认: /var/www/auto_daily_report]: " INSTALL_DIR
    INSTALL_DIR=${INSTALL_DIR:-/var/www/auto_daily_report}
    
    if [ ! -d "$INSTALL_DIR" ]; then
        print_red "目录 $INSTALL_DIR 不存在，请确认安装目录"
        exit 1
    fi
    
    print_blue "正在停止服务..."
    
    # 停止并禁用服务
    if systemctl is-active --quiet daily-reporter; then
        systemctl stop daily-reporter
        systemctl disable daily-reporter
        print_green "已停止并禁用Gunicorn服务"
    else
        print_yellow "Gunicorn服务未运行"
    fi
    
    # 删除systemd服务文件
    if [ -f /etc/systemd/system/daily-reporter.service ]; then
        rm -f /etc/systemd/system/daily-reporter.service
        systemctl daemon-reload
        print_green "已删除systemd服务文件"
    fi
    
    print_blue "正在删除Nginx配置..."
    
    # 删除Nginx配置
    if [ -f /etc/nginx/sites-enabled/daily-reporter ]; then
        rm -f /etc/nginx/sites-enabled/daily-reporter
        print_green "已删除Nginx站点链接"
    fi
    
    if [ -f /etc/nginx/sites-available/daily-reporter ]; then
        rm -f /etc/nginx/sites-available/daily-reporter
        print_green "已删除Nginx站点配置"
    fi
    
    # 重启Nginx
    if systemctl is-active --quiet nginx; then
        systemctl restart nginx
        print_green "已重启Nginx服务"
    fi
    
    print_blue "正在删除定时任务..."
    
    # 删除cron任务
    if crontab -l 2>/dev/null | grep -q "$INSTALL_DIR"; then
        (crontab -l 2>/dev/null | grep -v "$INSTALL_DIR") | crontab -
        print_green "已删除相关cron任务"
    else
        print_yellow "未找到相关cron任务"
    fi
    
    # 删除日志轮转配置
    if [ -f /etc/logrotate.d/daily-reporter ]; then
        rm -f /etc/logrotate.d/daily-reporter
        print_green "已删除日志轮转配置"
    fi
    
    print_blue "正在清理项目文件..."
    
    # 备份数据库（可选）
    read -p "是否要备份数据库？[Y/n]: " BACKUP_DB
    if [[ ! $BACKUP_DB =~ ^[Nn]$ ]]; then
        BACKUP_FILE="/tmp/daily_reporter_db_backup_$(date +%Y%m%d%H%M%S).sqlite3"
        if [ -f "$INSTALL_DIR/db.sqlite3" ]; then
            cp "$INSTALL_DIR/db.sqlite3" "$BACKUP_FILE"
            print_green "数据库已备份到: $BACKUP_FILE"
        else
            print_yellow "未找到数据库文件，跳过备份"
        fi
    fi
    
    # 删除项目文件
    read -p "是否删除整个项目目录？[y/N]: " DELETE_DIR
    if [[ $DELETE_DIR =~ ^[Yy]$ ]]; then
        rm -rf "$INSTALL_DIR"
        print_green "已删除项目目录: $INSTALL_DIR"
    else
        print_yellow "已保留项目目录"
    fi
    
    print_green "\n============================================================"
    print_green "              自动日报生成器卸载完成！                     "
    print_green "============================================================"
    print_yellow "已完成以下操作："
    print_yellow "  - 停止并移除服务"
    print_yellow "  - 删除Nginx配置"
    print_yellow "  - 删除cron定时任务"
    print_yellow "  - 删除日志轮转配置"
    if [[ ! $BACKUP_DB =~ ^[Nn]$ ]] && [ -f "$BACKUP_FILE" ]; then
        print_yellow "  - 备份数据库到: $BACKUP_FILE"
    fi
    if [[ $DELETE_DIR =~ ^[Yy]$ ]]; then
        print_yellow "  - 删除项目目录"
    fi
    print_green "============================================================"
}

# 执行主函数
main 