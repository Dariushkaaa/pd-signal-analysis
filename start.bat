@echo off
echo ========================================
echo PD Signal Analysis - Автозапуск
echo ========================================
echo.

REM Проверка Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ОШИБКА] Python не установлен!
    echo Скачайте с https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Создание виртуального окружения (если нет)
if not exist "venv" (
    echo Создание виртуального окружения...
    python -m venv venv
)

REM Активация виртуального окружения
call venv\Scripts\activate.bat

REM Установка зависимостей
echo Установка зависимостей...
pip install -r requirements.txt --quiet

REM Запуск сервера
echo.
echo Запуск сервера...
echo Откройте браузер: http://localhost:8000
echo Для остановки нажмите Ctrl+C
echo.

cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

pause