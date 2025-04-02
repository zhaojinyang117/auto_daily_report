#!/bin/bash

# 获取脚本所在目录的绝对路径
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 设置时区为北京时间
export TZ='Asia/Shanghai'

# 检查虚拟环境是否存在
if [ ! -d "$SCRIPT_DIR/.venv" ]; then
    echo "未检测到uv虚拟环境，请先运行 setup_uv.sh 创建环境"
    exit 1
fi

# 检查是否有已存在的crontab任务
EXISTING_CRON=$(crontab -l 2>/dev/null | grep -c "$SCRIPT_DIR/.venv/bin/python $SCRIPT_DIR/main.py")

if [ "$EXISTING_CRON" -eq 0 ]; then
    echo "未检测到已存在的crontab任务，创建新任务..."
    
    # 创建临时文件来存储新的crontab内容
    TEMP_CRON=$(mktemp)
    
    # 获取当前crontab内容（如果有的话）
    crontab -l 2>/dev/null > "$TEMP_CRON" || echo "" > "$TEMP_CRON"
    
    # 添加注释
    echo "# auto_daily_report 任务 (uv环境) - 每周一至周五晚上8点执行" >> "$TEMP_CRON"
    # 添加主任务：每周一至周五晚上8点执行main.py，使用uv虚拟环境
    echo "0 20 * * 1-5 cd $SCRIPT_DIR && $SCRIPT_DIR/.venv/bin/python $SCRIPT_DIR/main.py" >> "$TEMP_CRON"
    
    # 安装新的crontab
    crontab "$TEMP_CRON"
    rm "$TEMP_CRON"
    
    echo "任务设置完成！"
    
    # 显示当前的crontab内容
    echo "当前crontab任务列表："
    crontab -l
else
    echo "检测到已存在的crontab任务，保持不变"
    echo "当前crontab任务列表："
    crontab -l
fi

echo "提示：运行 'crontab -l' 查看任务列表，'crontab -e' 编辑任务"
echo "注意：所有时间均为系统时间，请确保系统时区设置正确"
echo "系统使用crontab设置为每周一至周五晚上8点自动执行，无需额外更新任务" 