# Docker 部署指南

本文档介绍如何使用 Docker 和 Docker Compose 部署自动日报生成器。

## 前提条件

- 安装 [Docker](https://docs.docker.com/get-docker/)
- 安装 [Docker Compose](https://docs.docker.com/compose/install/)

## 快速开始

1. 克隆仓库

```bash
git clone -b django https://github.com/yourusername/auto_daily_report.git
cd auto_daily_report
```

2. 配置环境变量

```bash
cp .env.docker .env
```

编辑 `.env` 文件，设置您的个人信息、API密钥和邮件配置。

3. 构建并启动容器

```bash
docker-compose up -d
```

4. 创建超级用户

```bash
docker-compose exec web python manage.py createsuperuser
```

5. 访问应用

浏览器访问 http://localhost:8000

## 容器说明

本项目使用两个容器：

- **web**: 运行Django Web应用
- **cron**: 运行定时任务

两个容器共享相同的代码库和数据库，但执行不同的任务。

## 数据持久化

以下数据通过卷挂载实现持久化：

- **数据库**: `./db.sqlite3:/app/db.sqlite3`
- **静态文件**: `./staticfiles:/app/staticfiles`
- **日志文件**: `./logs:/app/logs`

## 常见问题

### 1. 容器无法启动

检查日志：

```bash
docker-compose logs
```

### 2. 数据库迁移问题

执行迁移：

```bash
docker-compose exec web python manage.py migrate
```

### 3. 静态文件问题

重新收集静态文件：

```bash
docker-compose exec web python manage.py collectstatic --noinput
```

### 4. 修改配置后重启

修改 `.env` 文件后需要重启容器：

```bash
docker-compose down
docker-compose up -d
```

## 更新应用

当有新版本时，按以下步骤更新：

```bash
git pull
docker-compose down
docker-compose build
docker-compose up -d
```

## 备份数据

备份数据库：

```bash
cp db.sqlite3 db.sqlite3.backup.$(date +%Y%m%d)
```

## 完全卸载

删除所有容器和卷：

```bash
docker-compose down
```

如果需要删除数据库和日志：

```bash
rm -rf db.sqlite3 logs/*
```
