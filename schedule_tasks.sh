#!/bin/bash

# 获取脚本所在目录的绝对路径
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 检查at服务是否安装和运行
if ! command -v at &> /dev/null; then
    echo "正在安装at命令..."
    sudo apt-get update && sudo apt-get install -y at
fi

# 确保at服务运行
sudo systemctl start atd
sudo systemctl enable atd

# 设置时区为北京时间
export TZ='Asia/Shanghai'

# 创建每周五的更新任务函数
create_weekly_update() {
    # 获取下周五的日期
    NEXT_FRIDAY=$(date -d "next friday" +"%Y-%m-%d")
    echo "cd $SCRIPT_DIR && ./schedule_tasks.sh" | at "20:00 $NEXT_FRIDAY" 2>/dev/null
    echo "已设置下周五 $NEXT_FRIDAY 20:00 的自动更新任务"
}

# 检查是否已存在本程序的at任务
EXISTING_TASK=false
for job in $(atq | cut -f1); do
    if at -c "$job" | grep -q "main.py"; then
        EXISTING_TASK=true
        echo "检测到已存在的任务: $job (北京时间)"
        break
    fi
done

# 只在没有已存在任务时创建新任务
if [ "$EXISTING_TASK" = false ]; then
    echo "未检测到已存在的任务，创建新任务..."
    
    # 获取今天是星期几（0-6，0是周日）
    TODAY=$(date +%w)
    
    # 设置未来5个工作日的任务
    for i in {0..4}; do
        # 计算未来第i天是星期几
        FUTURE_DAY=$(( (TODAY + i) % 7 ))
        
        # 跳过周六和周日
        if [ $FUTURE_DAY -eq 0 ] || [ $FUTURE_DAY -eq 6 ]; then
            continue
        fi
        
        # 创建at命令（使用北京时间）
        if [ $i -eq 0 ]; then
            SCHEDULE="20:00 today"
        else
            SCHEDULE="20:00 tomorrow + $((i-1)) days"
        fi
        
        # 添加任务
        echo "export TZ='Asia/Shanghai' && cd $SCRIPT_DIR && python3 main.py" | at $SCHEDULE 2>/dev/null
        echo "已设置 $SCHEDULE 的任务 (北京时间)"
    done
    
    # 创建下周的更新任务
    create_weekly_update
    
    echo "任务设置完成！"
else
    echo "已存在任务，保持不变"
fi

# 显示所有任务
echo "当前任务列表 (北京时间)："
atq

echo "提示：运行 'atq' 查看任务列表，'atrm [任务号]' 删除特定任务"
echo "注意：所有时间均为北京时间"
echo "每周五会自动更新下周的任务" 