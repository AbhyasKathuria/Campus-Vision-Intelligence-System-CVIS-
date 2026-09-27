@echo off
chcp 65001 >nul
title CVIS - Campus Vision Intelligence System Launcher
color 0B

echo ===============================================================================
echo        CAMPUS VISION INTELLIGENCE SYSTEM (CVIS) — LOCAL LAUNCHER
echo ===============================================================================
echo.
echo [1/5] Verifying environment runtimes...

where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python 3.12+ was not found on your PATH. Please install Python.
    pause
    exit /b 1
)

where npm >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Node.js / npm was not found on your PATH. Please install Node.js.
    pause
    exit /b 1
)

echo   - Python: OK
echo   - Node.js / npm: OK
echo.

echo [2/5] Initializing & seeding database with synthetic campus data...
set PYTHONPATH=%~dp0backend
python "%~dp0seed\seed_data.py"
if %ERRORLEVEL% NEQ 0 (
    echo [WARNING] Seed script encountered an issue, proceeding to launch services...
) else (
    echo   - Database initialized & seeded successfully.
)
echo.

echo [3/5] Starting ML Inference Microservice (Port 8001)...
start "CVIS - ML Microservice (8001)" cmd /k "cd /d %~dp0ml-service && python -m uvicorn app.main:app --host 127.0.0.1 --port 8001"

echo [4/5] Starting Backend API Gateway (Port 8000)...
start "CVIS - Backend Gateway (8000)" cmd /k "cd /d %~dp0backend && set PYTHONPATH=%~dp0backend && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000"

echo [5/5] Starting Frontend React Application (Port 3000)...
start "CVIS - Frontend (3000)" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo ===============================================================================
echo   CVIS SERVICES ARE STARTING:
echo   - Frontend:      http://localhost:3000
echo   - Backend API:   http://localhost:8000/docs
echo   - ML Inference:  http://localhost:8001/api/v1/health
echo ===============================================================================
echo.
echo Waiting 4 seconds before opening browser...
timeout /t 4 /nobreak >nul

start http://localhost:3000

echo.
echo CVIS is now running! 
echo Keep the service terminal windows open while testing.
echo To shut down all services, run stop.bat or close the windows.
echo.
pause
