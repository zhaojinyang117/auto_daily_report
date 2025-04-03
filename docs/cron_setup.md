# Django-Cron 定时任务系统

## 概述

本项目使用 `django-cron` 包来管理定时任务，特别是日报的定时发送功能。这提供了一个与 Django 框架更紧密集成的方案，比外部系统 cron 任务更易于管理和监控。

## 工作原理

1. **任务定义**：所有定时任务都定义在 `reporter/cron.py` 文件中，作为 `CronJobBase` 的子类。

2. **执行频率**：每个任务都指定了执行频率（如每5分钟运行一次）。

3. **自动执行**：Django-Cron 通过 `python manage.py runcrons` 命令执行注册的任务，我们需要设置一个系统定时任务（如Linux的crontab）来定期运行这个命令。

4. **日志记录**：执行记录会保存在数据库中，便于跟踪和监控。

## 配置步骤

### 1. 安装依赖

确保 `django-cron` 已安装：

```bash
pip install django-cron
```

### 2. 配置 settings.py

`settings.py` 中已添加了必要的配置：

```python
INSTALLED_APPS = [
    # ...其他应用...
    'django_cron',
]

# Cron作业配置
CRON_CLASSES = [
    'reporter.cron.SendDailyReportsCronJob',
]

# Cron作业日志记录
DJANGO_CRON_DELETE_LOGS_OLDER_THAN = 7  # 删除7天以前的日志
```

### 3. 迁移数据库

首次设置需要执行数据库迁移，创建 django-cron 需要的表：

```bash
python manage.py migrate django_cron
```

### 4. 设置系统定时任务

要使 Django-Cron 自动运行，需要设置一个系统定时任务来定期执行 `runcrons` 命令。

对于 Linux/Unix 系统，编辑 crontab：

```bash
crontab -e
```

添加以下行（每5分钟执行一次）：

```
*/5 * * * * cd /path/to/project && /path/to/venv/bin/python manage.py runcrons > /dev/null 2>&1
```

对于 Windows 系统，使用任务计划程序创建一个每5分钟运行一次的任务，执行以下命令：

```
cd C:\path\to\project && C:\path\to\venv\Scripts\python.exe manage.py runcrons
```

## 手动运行任务

可以使用以下命令手动运行所有或特定的 Cron 任务：

```bash
# 运行所有配置的Cron任务
python manage.py run_cron_jobs

# 运行特定的Cron任务
python manage.py run_cron_jobs --job=reporter.send_daily_reports_job
```

也可以使用Django自带的runcrons命令：

```bash
# 运行所有任务
python manage.py runcrons

# 运行指定任务
python manage.py runcrons reporter.send_daily_reports_job
```

## 监控和日志

django-cron 会在数据库中记录每次任务执行的结果。可以在管理界面中查看，也可以通过以下方式查询：

```python
from django_cron.models import CronJobLog

# 获取最近10条日志
recent_logs = CronJobLog.objects.all().order_by('-start_time')[:10]

# 获取特定任务的日志
job_logs = CronJobLog.objects.filter(code='reporter.send_daily_reports_job').order_by('-start_time')

# 获取失败的任务日志
failed_logs = CronJobLog.objects.filter(is_success=False).order_by('-start_time')
```

## 故障排除

1. **任务不执行**
   - 检查系统crontab是否正确设置
   - 确认Django项目路径是否正确
   - 检查虚拟环境路径
   - 查看cron日志（通常在 `/var/log/syslog` 或 `/var/log/cron`）

2. **任务执行失败**
   - 查看Django日志文件
   - 检查数据库中的 `django_cron_cronjoblog` 表

3. **锁定问题**
   - 如果任务因为上一个实例仍在运行而被跳过，可能是任务执行时间过长
   - 可以调整锁定超时：`DJANGO_CRON_LOCK_TIME` 