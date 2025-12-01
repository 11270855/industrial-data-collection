@echo off
REM ============================================
REM 能源管理系统启动脚本
REM Energy Management System Startup Script
REM ============================================

echo ========================================
echo 能源管理系统启动中...
echo Energy Management System Starting...
echo ========================================
echo.

REM 设置控制台编码为UTF-8
chcp 65001 >nul

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到Python，请先安装Python 3.8或更高版本
    echo [ERROR] Python not found. Please install Python 3.8 or higher
    pause
    exit /b 1
)

REM 检查.env文件是否存在
if not exist .env (
    echo [警告] 未找到.env配置文件
    echo [WARNING] .env file not found
    if exist .env.example (
        echo [提示] 请复制.env.example为.env并配置参数
        echo [INFO] Please copy .env.example to .env and configure parameters
    )
    pause
    exit /b 1
)

REM 创建日志目录
if not exist logs mkdir logs
echo [信息] 日志目录已准备
echo [INFO] Log directory ready

REM 检查虚拟环境
if not exist .venv (
    echo [警告] 未找到虚拟环境，正在创建...
    echo [WARNING] Virtual environment not found, creating...
    python -m venv .venv
    if errorlevel 1 (
        echo [错误] 虚拟环境创建失败
        echo [ERROR] Failed to create virtual environment
        pause
        exit /b 1
    )
    echo [信息] 虚拟环境创建成功
    echo [INFO] Virtual environment created successfully
)

REM 激活虚拟环境
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo [错误] 虚拟环境激活失败
    echo [ERROR] Failed to activate virtual environment
    pause
    exit /b 1
)

REM 检查依赖是否安装
echo [信息] 检查Python依赖...
echo [INFO] Checking Python dependencies...
python -c "import opcua" >nul 2>&1
if errorlevel 1 (
    echo [警告] 依赖未安装，正在安装...
    echo [WARNING] Dependencies not installed, installing...
    pip install -r python_client\requirements.txt
    pip install -r web_app\requirements.txt
    if errorlevel 1 (
        echo [错误] 依赖安装失败
        echo [ERROR] Failed to install dependencies
        pause
        exit /b 1
    )
)

REM 检查数据库是否初始化
echo [信息] 检查数据库状态...
echo [INFO] Checking database status...
python -c "from python_client.database import DatabaseManager; import os; from dotenv import load_dotenv; load_dotenv(); db = DatabaseManager(); db.connect()" >nul 2>&1
if errorlevel 1 (
    echo [警告] 数据库未初始化或连接失败
    echo [WARNING] Database not initialized or connection failed
    echo [提示] 请运行: python python_client\init_database.py
    echo [INFO] Please run: python python_client\init_database.py
    pause
)

REM 检查是否已有进程在运行
echo [信息] 检查运行中的进程...
echo [INFO] Checking for running processes...

tasklist /FI "WINDOWTITLE eq Python Client - Energy Management" 2>nul | find /I "cmd.exe" >nul
if not errorlevel 1 (
    echo [警告] Python客户端已在运行
    echo [WARNING] Python client is already running
    set PYTHON_CLIENT_RUNNING=1
) else (
    set PYTHON_CLIENT_RUNNING=0
)

tasklist /FI "WINDOWTITLE eq Web App - Energy Management" 2>nul | find /I "cmd.exe" >nul
if not errorlevel 1 (
    echo [警告] Web应用已在运行
    echo [WARNING] Web application is already running
    set WEB_APP_RUNNING=1
) else (
    set WEB_APP_RUNNING=0
)

REM 启动Python数据采集客户端
if %PYTHON_CLIENT_RUNNING%==0 (
    echo.
    echo [信息] 启动Python数据采集客户端...
    echo [INFO] Starting Python data collection client...
    start "Python Client - Energy Management" cmd /k "call .venv\Scripts\activate.bat && python python_client\main.py >> logs\python_client.log 2>&1"
    timeout /t 2 /nobreak >nul
    echo [成功] Python客户端已启动
    echo [SUCCESS] Python client started
) else (
    echo [跳过] Python客户端已在运行
    echo [SKIP] Python client already running
)

REM 启动Flask Web应用
if %WEB_APP_RUNNING%==0 (
    echo.
    echo [信息] 启动Flask Web应用...
    echo [INFO] Starting Flask web application...
    start "Web App - Energy Management" cmd /k "call .venv\Scripts\activate.bat && python web_app\app.py >> logs\web_app.log 2>&1"
    timeout /t 3 /nobreak >nul
    echo [成功] Web应用已启动
    echo [SUCCESS] Web application started
) else (
    echo [跳过] Web应用已在运行
    echo [SKIP] Web application already running
)

echo.
echo ========================================
echo 系统启动完成！
echo System startup complete!
echo ========================================
echo.
echo [信息] Python客户端窗口: "Python Client - Energy Management"
echo [INFO] Python client window: "Python Client - Energy Management"
echo [信息] Web应用窗口: "Web App - Energy Management"
echo [INFO] Web application window: "Web App - Energy Management"
echo.
echo [访问] Web界面: http://localhost:5000
echo [ACCESS] Web interface: http://localhost:5000
echo.
echo [提示] 使用stop_system.bat停止系统
echo [INFO] Use stop_system.bat to stop the system
echo.
pause
