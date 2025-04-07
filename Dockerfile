FROM python:3.12-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# 安装uv包管理器
RUN pip install --no-cache-dir uv

# 复制项目文件
COPY . .

# 复制修复后的django_cron文件到临时目录
# 这些文件将在entrypoint.sh中被复制到正确的位置
COPY fixed_django_cron_models.py /tmp/
COPY fixed_django_cron_admin.py /tmp/

# 安装项目依赖
RUN uv pip install --no-cache-dir -e .

# 收集静态文件
RUN mkdir -p staticfiles

# 创建日志目录
RUN mkdir -p logs

# 暴露端口
EXPOSE 8000

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 添加启动脚本
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# 设置启动命令
ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "daily_reporter_project.wsgi:application"]
