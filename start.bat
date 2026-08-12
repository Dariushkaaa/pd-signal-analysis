@echo off
title PD Signal Analysis
echo ========================================
echo PD Signal Analysis - Auto Start
echo ========================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed!
    echo Please download it from https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo Creating virtual environment (this may take a minute)...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install dependencies from file
echo Installing base dependencies...
pip install -r requirements.txt --quiet

REM Force install stable CPU version of PyTorch to avoid DLL errors
echo Installing stable CPU version of PyTorch (this may take 2-3 minutes)...
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu --quiet

REM Start server
echo.
echo ========================================
echo Server is starting...
echo Open your browser: http://localhost:8000
echo To stop, press Ctrl+C in this window
echo ========================================
echo.

cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

pause