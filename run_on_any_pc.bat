@echo off
title ShrinkIO - Universal Setup and Launcher
echo ================================================================
echo   ShrinkIO - Automatic Setup and Run Script
echo ================================================================
echo.

:: Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python 3.10+ from python.org to run the backend.
    echo.
    pause
    exit /b
)

:: Check for Node.js
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js is not installed or not in PATH.
    echo Please install Node.js from nodejs.org to run the frontend.
    echo.
    pause
    exit /b
)

:: 1. Setup Backend
echo [1/3] Setting up Python Backend...
cd backend
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
    echo Installing backend dependencies...
    venv\Scripts\python.exe -m pip install -r requirements.txt
) else (
    echo Backend virtual environment already exists.
)
cd ..

:: 2. Setup Frontend
echo [2/3] Setting up React Frontend...
cd frontend
if not exist node_modules (
    echo Installing npm dependencies (this may take a minute)...
    call npm install
) else (
    echo Frontend dependencies already installed.
)
cd ..

:: 3. Launch App
echo [3/3] Starting servers...
echo.
echo Launching FastAPI Backend on http://127.0.0.1:8000 ...
start "ShrinkIO Backend" cmd /k "cd backend && venv\Scripts\python.exe run.py"

echo Launching Vite Frontend on http://127.0.0.1:5173 ...
start "ShrinkIO Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo ================================================================
echo   Setup complete! Servers are starting in separate windows.
echo   Open http://127.0.0.1:5173 in your browser once loaded.
echo ================================================================
echo.
pause
