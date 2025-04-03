#!/bin/bash

# django-cron定时任务设置脚本
# 此脚本设置系统cron任务，定期执行Django的runcrons命令

# 获取当前脚本所在的目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
# 获取项目根目录（脚本目录的上一级）
PROJECT_PATH="$( cd "$SCRIPT_DIR/.." && pwd )"
LOG_PATH="$PROJECT_PATH/logs"

echo "项目路径: $PROJECT_PATH"

# 创建日志目录
mkdir -p $LOG_PATH
echo "日志目录已创建: $LOG_PATH"

# 检测虚拟环境
if [ -d "$PROJECT_PATH/.venv" ]; then
    VENV_PATH="$PROJECT_PATH/.venv"
    PYTHON="$VENV_PATH/bin/python"
elif [ -d "$PROJECT_PATH/venv" ]; then
    VENV_PATH="$PROJECT_PATH/venv"
    PYTHON="$VENV_PATH/bin/python"
else
    # 尝试找到当前激活的虚拟环境
    if [ -n "$VIRTUAL_ENV" ]; then
        VENV_PATH="$VIRTUAL_ENV"
        PYTHON="$VENV_PATH/bin/python"
    else
        # 使用系统Python
        PYTHON=$(which python3 || which python)
        echo "警告：未检测到虚拟环境，将使用系统Python: $PYTHON"
    fi
fi

# 设置cron任务 - 每5分钟执行一次Django-Cron
CRON_JOB="*/5 * * * * cd $PROJECT_PATH && $PYTHON manage.py runcrons >> $LOG_PATH/django_cron.log 2>&1"

# 检查是否已存在相同的cron任务
EXISTING_CRON=$(crontab -l 2>/dev/null | grep -F "runcrons")

if [ -z "$EXISTING_CRON" ]; then
    # 添加到当前用户的crontab
    (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
    echo "Cron任务已添加: 每5分钟执行一次Django-Cron任务"
else
    echo "Django-Cron任务已存在，未进行修改"
fi

# 执行数据库迁移，确保django_cron表已创建
cd $PROJECT_PATH
$PYTHON manage.py migrate django_cron
echo "数据库迁移完成，django_cron表已创建"

echo "====================================================="
echo "设置完成！您的Django-Cron系统现已配置，将按计划运行。"
echo "日志文件将保存在: $LOG_PATH/django_cron.log"
echo ""
echo "要手动测试定时任务，请运行:"
echo "$PYTHON manage.py runcrons"
echo "或"
echo "$PYTHON manage.py run_cron_jobs"
echo "=====================================================" 


# 使用方法：

# 1. 使脚本可执行:
#    chmod +x scripts/setup_django_cron.sh

# 2. 执行脚本:
#    bash scripts/setup_django_cron.sh

# 设置脚本会自动处理：
# - 创建日志目录
# - 设置系统cron任务，每5分钟执行一次django-cron
# - 执行数据库迁移，创建必要的表
# - 添加cron任务到当前用户的crontab中 