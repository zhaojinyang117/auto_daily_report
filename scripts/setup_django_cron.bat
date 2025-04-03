@echo off
REM Django-Cron Windows 设置脚本
REM 此脚本为Windows系统设置定时任务，运行Django的runcrons命令

echo Django-Cron Windows 设置脚本

REM 获取项目路径
set SCRIPT_DIR=%~dp0
set PROJECT_PATH=%SCRIPT_DIR%..
cd %PROJECT_PATH%

REM 创建日志目录
if not exist "logs" mkdir logs
echo 日志目录已创建: %PROJECT_PATH%\logs

REM 检测Python环境
if exist ".venv\Scripts\python.exe" (
    set PYTHON=.venv\Scripts\python.exe
) else if exist "venv\Scripts\python.exe" (
    set PYTHON=venv\Scripts\python.exe
) else (
    set PYTHON=python
    echo 警告：未检测到虚拟环境，将使用系统Python
)

REM 任务名称
set TASK_NAME=DjangoAutoReportCron

REM 检查是否已经设置了任务
schtasks /query /tn "%TASK_NAME%" >nul 2>&1
if %errorlevel% == 0 (
    echo 任务已存在，是否要重新创建？(Y/N)
    set /p CHOICE=
    if /i "%CHOICE%" neq "Y" (
        echo 保持现有任务不变
        goto END
    )
    
    REM 删除现有任务
    schtasks /delete /tn "%TASK_NAME%" /f
)

echo 创建新的定时任务...

REM 创建每5分钟执行一次的任务
schtasks /create /tn "%TASK_NAME%" /tr "cmd.exe /c cd /d %PROJECT_PATH% && %PYTHON% manage.py runcrons >> logs\django_cron.log 2>&1" /sc minute /mo 5 /ru System

echo 任务设置完成！
echo 当前任务列表：
schtasks /query /tn "%TASK_NAME%"

REM 执行数据库迁移，确保django_cron表已创建
%PYTHON% manage.py migrate django_cron
echo 数据库迁移完成，django_cron表已创建

echo =====================================================
echo 设置完成！您的Django-Cron系统现已配置，将按计划运行。
echo 日志文件将保存在: %PROJECT_PATH%\logs\django_cron.log
echo.
echo 要手动测试定时任务，请运行:
echo %PYTHON% manage.py runcrons
echo 或
echo %PYTHON% manage.py run_cron_jobs
echo =====================================================

echo 提示：运行 'schtasks /query /tn "%TASK_NAME%"' 查看任务详情

:END
pause 