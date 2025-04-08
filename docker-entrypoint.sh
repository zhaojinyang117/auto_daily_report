#!/bin/bash
set -e

# 创建虚拟环境路径（如果不存在）
mkdir -p .venv/lib/site-packages/django_cron

# 查找django_cron包的安装路径
DJANGO_CRON_PATH=$(python -c "import django_cron; print(django_cron.__path__[0])")
echo "Django Cron 路径: $DJANGO_CRON_PATH"

# 复制修复后的文件到django_cron包
echo "正在修复django_cron包..."
cp /tmp/fixed_django_cron_models.py $DJANGO_CRON_PATH/models.py
cp /tmp/fixed_django_cron_admin.py $DJANGO_CRON_PATH/admin.py
echo "django_cron包修复完成"

# 执行数据库迁移
echo "正在执行数据库迁移..."
python manage.py migrate

# 收集静态文件
echo "正在收集静态文件..."
python manage.py collectstatic --noinput

# 如果命令是runcrons，则执行cron任务
if [ "$1" = "python" ] && [ "$2" = "manage.py" ] && [ "$3" = "runcrons" ]; then
    echo "启动cron任务..."
    while true; do
        python manage.py runcrons
        echo "$(date): Cron tasks executed" >> /app/logs/cron.log
        sleep 300  # 每5分钟执行一次
    done
else
    # 执行传入的命令
    echo "启动Web服务..."
    exec "$@"
fi
