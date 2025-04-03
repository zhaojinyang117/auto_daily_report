#!/bin/bash

# 日报生成执行脚本 - 由cron调用
# 设置项目路径 - 请修改为您的实际项目路径
PROJECT_PATH="/path/to/auto_daily_report"

# 进入项目目录
cd $PROJECT_PATH

# 激活虚拟环境 (根据您的环境配置选择正确的虚拟环境路径)
if [ -d "$PROJECT_PATH/.venv" ]; then
    source $PROJECT_PATH/.venv/bin/activate
elif [ -d "$PROJECT_PATH/venv" ]; then
    source $PROJECT_PATH/venv/bin/activate
fi

# 加载环境变量
if [ -f "$PROJECT_PATH/.env" ]; then
    export $(grep -v '^#' $PROJECT_PATH/.env | xargs -0)
fi

# 设置Django环境
export DJANGO_SETTINGS_MODULE="daily_reporter_project.settings"

# 运行Django管理命令
uv run manage.py send_daily_reports

# 记录执行日志
echo "$(date): Daily report task executed" >> $PROJECT_PATH/logs/cron.log

# 退出虚拟环境
deactivate 