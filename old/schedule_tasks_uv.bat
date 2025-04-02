@echo off
setlocal

REM 获取脚本所在目录的绝对路径
set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

REM 检查虚拟环境是否存在
if not exist "%SCRIPT_DIR%\.venv" (
    echo 未检测到uv虚拟环境，请先运行 setup_uv.bat 创建环境
    exit /b 1
)

REM 检查是否已经设置了任务
schtasks /query /tn "AutoDailyReport" 2>nul
if %ERRORLEVEL% EQU 0 (
    echo 任务已存在，是否要重新创建？(Y/N)
    set /p CHOICE=
    if /i "%CHOICE%" NEQ "Y" (
        echo 保持现有任务不变
        exit /b 0
    )
    schtasks /delete /tn "AutoDailyReport" /f
)

echo 创建新的定时任务...

REM 创建每周一至周五晚上8点执行的任务
schtasks /create /tn "AutoDailyReport" /tr "%SCRIPT_DIR%\.venv\Scripts\python.exe %SCRIPT_DIR%\main.py" /sc weekly /d MON,TUE,WED,THU,FRI /st 20:00 /f

echo 任务设置完成！
echo 当前任务列表：
schtasks /query /tn "AutoDailyReport"

echo 提示：运行 'schtasks /query /tn "AutoDailyReport"' 查看任务详情
echo 注意：所有时间均为系统时间，请确保系统时区设置正确 