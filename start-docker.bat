@echo off
chcp 65001 >nul
title CVIS - Docker Compose Launcher
color 09

echo ===============================================================================
echo        CAMPUS VISION INTELLIGENCE SYSTEM (CVIS) — DOCKER LAUNCHER
echo ===============================================================================
echo.

where docker >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Docker was not found on your PATH. Please install Docker Desktop.
    pause
    exit /b 1
)

echo Starting CVIS multi-container stack via Docker Compose...
cd /d %~dp0infra
docker compose up -d --build

echo.
echo Waiting 5 seconds for containers to become healthy...
timeout /t 5 /nobreak >nul

start http://localhost:3000

echo.
echo ===============================================================================
echo   CVIS CONTAINERS RUNNING:
echo   - Web Frontend:  http://localhost:3000
echo   - Backend API:   http://localhost:8000/docs
echo   - ML Inference:  http://localhost:8001/api/v1/health
echo ===============================================================================
echo.
echo To view logs: cd infra ^&^& docker compose logs -f
echo To stop:      cd infra ^&^& docker compose down
echo.
pause
