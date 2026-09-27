@echo off
chcp 65001 >nul
title CVIS - Stop All Services
color 0C

echo ===============================================================================
echo        CAMPUS VISION INTELLIGENCE SYSTEM (CVIS) — SHUTDOWN UTILITY
echo ===============================================================================
echo.
echo Stopping CVIS background processes (Uvicorn, Node)...

taskkill /FI "WINDOWTITLE eq CVIS - ML Microservice (8001)*" /T /F >nul 2>nul
taskkill /FI "WINDOWTITLE eq CVIS - Backend Gateway (8000)*" /T /F >nul 2>nul
taskkill /FI "WINDOWTITLE eq CVIS - Frontend (3000)*" /T /F >nul 2>nul

echo.
echo [OK] All CVIS service windows have been terminated.
timeout /t 2 /nobreak >nul
exit /b 0
