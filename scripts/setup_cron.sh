#!/bin/bash

# cron任务设置脚本 - 只需运行一次以设置cron任务

# 获取当前脚本所在的目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
# 获取项目根目录（脚本目录的上一级）
PROJECT_PATH="$( cd "$SCRIPT_DIR/.." && pwd )"
SCRIPT_PATH="$PROJECT_PATH/scripts"
LOG_PATH="$PROJECT_PATH/logs"

echo "项目路径: $PROJECT_PATH"

# 创建日志目录
mkdir -p $LOG_PATH
echo "日志目录已创建: $LOG_PATH"

# 确保daily_report_runner.sh存在
if [ ! -f "$SCRIPT_PATH/daily_report_runner.sh" ]; then
    echo "错误: $SCRIPT_PATH/daily_report_runner.sh 文件不存在"
    exit 1
fi

# 更新daily_report_runner.sh中的项目路径
sed -i "s|PROJECT_PATH=\"/path/to/auto_daily_report\"|PROJECT_PATH=\"$PROJECT_PATH\"|g" $SCRIPT_PATH/daily_report_runner.sh
echo "已更新runner脚本中的项目路径"

# 添加执行权限
chmod +x $SCRIPT_PATH/daily_report_runner.sh
echo "已为runner脚本添加执行权限"

# 设置cron任务 - 每15分钟执行一次检查
# 您可以根据需要修改执行频率
CRON_JOB="*/15 * * * * $SCRIPT_PATH/daily_report_runner.sh"

# 检查是否已存在相同的cron任务
EXISTING_CRON=$(crontab -l 2>/dev/null | grep -F "$SCRIPT_PATH/daily_report_runner.sh")

if [ -z "$EXISTING_CRON" ]; then
    # 添加到当前用户的crontab
    (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
    echo "Cron任务已添加: 每15分钟执行一次日报检查任务"
else
    echo "Cron任务已存在，未进行修改"
fi

echo "====================================================="
echo "设置完成！您的自动日报系统现已配置，将按计划运行。"
echo "日志文件将保存在: $LOG_PATH/cron.log"
echo ""
echo "要手动测试脚本，请运行:"
echo "bash $SCRIPT_PATH/daily_report_runner.sh"
echo "=====================================================" 


# 使用方法：

# 1. 部署到Linux服务器后，首先确保脚本有执行权限：
#    ```bash
#    chmod +x scripts/setup_cron.sh
#    chmod +x scripts/daily_report_runner..sh
#    chmod +x scripts/daily_report_runner. bash scripts/setup_cron.sh
#    ```

# 3. 如果需要手动测试，可以直接运行：
#    ```bash
#    bash scripts/daily_report_runner.sh
#    ```

# 设置脚本会自动处理：
# - 创建日志目录
# - 更新执行脚本中的项目路径
# - 添加cron任务到当前用户的crontab中

# 这样，您的Django应用就会每15分钟检查一次是否有需要发送的日报，并根据用户设置的时间和日期执行发送操作。