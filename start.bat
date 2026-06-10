@echo off
set "ComSpec=C:\Windows\system32\cmd.exe"
set "COMSPEC=C:\Windows\system32\cmd.exe"
title Universal File & Image Compressor - Control Panel
echo ================================================================
echo   Universal File & Image Compressor Concurrency Startup Script
echo ================================================================
echo.

:: 1. Launch FastAPI Backend
echo [1/2] Starting FastAPI Backend on http://127.0.0.1:8000 ...
start "ShrinkIO Backend (FastAPI)" cmd /k "cd backend && venv\Scripts\python.exe run.py"

:: 2. Launch React Frontend (Vite)
echo [2/2] Starting React Frontend on http://127.0.0.1:5173 ...
start "ShrinkIO Frontend (Vite)" cmd /k "cd frontend && set \"PATH=C:\Users\chait\.gemini\antigravity\scratch\budget-planner\node-env\node-v20.11.1-win-x64;%PATH%\" && node node_modules/vite/bin/vite.js"

echo.
echo ================================================================
echo   All servers launched successfully!
echo   - Backend API: http://127.0.0.1:8000
echo   - Frontend UI: http://localhost:5173
echo   (Press Ctrl+C in their respective windows to stop the servers)
echo ================================================================
echo.
pause
