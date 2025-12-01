@echo off
REM ============================================
REM 能源管理系统停止脚本
REM Energy Management System Stop Script
REM ============================================

echo ========================================
echo 能源管理系统停止中...
echo Energy Management System Stopping...
echo ========================================
echo.

REM 设置控制台编码为UTF-8
chcp 65001 >nul

REM 查找并关闭Python客户端进程
echo [信息] 正在停止Python数据采集客户端...
echo [INFO] Stopping Python data collection client...

for /f "tokens=2" %%a in ('tasklist /FI "WINDOWTITLE eq Python Client - Energy Management" /FO LIST ^| find "PID:"') do (
    set PID=%%a
    taskkill /PID %%a /T /F >nul 2>&1
    if not errorlevel 1 (
        echo [成功] Python客户端已停止 (PID: %%a^)
        echo [SUCCESS] Python client stopped (PID: %%a^)
    )
)

REM 查找并关闭Web应用进程
echo.
echo [信息] 正在停止Flask Web应用...
echo [INFO] Stopping Flask web application...

for /f "tokens=2" %%a in ('tasklist /FI "WINDOWTITLE eq Web App - Energy Management" /FO LIST ^| find "PID:"') do (
    set PID=%%a
    taskkill /PID %%a /T /F >nul 2>&1
    if not errorlevel 1 (
        echo [成功] Web应用已停止 (PID: %%a^)
        echo [SUCCESS] Web application stopped (PID: %%a^)
    )
)

REM 额外检查：关闭可能残留的Python进程
echo.
echo [信息] 检查残留进程...
echo [INFO] Checking for remaining processes...

REM 查找运行main.py的Python进程
for /f "tokens=2" %%a in ('wmic process where "commandline like '%%python_client\\main.py%%'" get processid /format:list ^| find "ProcessId"') do (
    set PID=%%a
    if not "%%a"=="" (
        taskkill /PID %%a /T /F >nul 2>&1
        if not errorlevel 1 (
            echo [清理] 已停止残留的Python客户端进程 (PID: %%a^)
            echo [CLEANUP] Stopped remaining Python client process (PID: %%a^)
        )
    )
)

REM 查找运行app.py的Python进程
for /f "tokens=2" %%a in ('wmic process where "commandline like '%%web_app\\app.py%%'" get processid /format:list ^| find "ProcessId"') do (
    set PID=%%a
    if not "%%a"=="" (
        taskkill /PID %%a /T /F >nul 2>&1
        if not errorlevel 1 (
            echo [清理] 已停止残留的Web应用进程 (PID: %%a^)
            echo [CLEANUP] Stopped remaining Web application process (PID: %%a^)
        )
    )
)

echo.
echo ========================================
echo 系统已停止
echo System stopped
echo ========================================
echo.
echo [信息] 所有进程已终止
echo [INFO] All processes terminated
echo.
echo [提示] 使用start_system.bat重新启动系统
echo [INFO] Use start_system.bat to restart the system
echo.
pause
