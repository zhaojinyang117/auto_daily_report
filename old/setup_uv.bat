@echo off
echo 正在检查uv是否已安装...

where uv >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo 正在安装uv包管理器...
    powershell -Command "iwr -useb https://astral.sh/uv/install.ps1 | iex"
)

echo 正在创建虚拟环境并安装依赖...
uv venv .venv
call .venv\Scripts\activate.bat
uv pip install -r requirements.txt

echo 创建日志文件...
type nul > email_logs.txt

echo 环境设置完成！请使用 '.venv\Scripts\activate.bat' 激活环境 