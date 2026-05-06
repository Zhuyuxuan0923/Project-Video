@echo off
chcp 65001 >nul
title AI Drama Studio

echo =============================================
echo   AI Drama Studio - 一键启动
echo =============================================
echo.

REM 启动 Redis（如果有 Docker）
where docker >nul 2>&1
if %errorlevel% equ 0 (
    echo [*] 启动 Redis...
    docker compose -f "%~dp0docker-compose.yml" up -d
    timeout /t 3 >nul
) else (
    echo [!] 未检测到 Docker，请确保 Redis 已在 localhost:6379 运行
)

REM 启动 Worker（监听全部队列）
echo [*] 启动 Celery Worker...
start "Celery Worker" cmd /c "cd /d \"%~dp0\" && python cli.py worker --type all && pause"

REM 等待 Worker 就绪
timeout /t 2 >nul

REM 启动 Web UI
echo [*] 启动 Web UI...
echo.
echo   浏览器打开: http://localhost:8080
echo   按 Ctrl+C 停止
echo.
cd /d "%~dp0"
python cli.py web

pause
