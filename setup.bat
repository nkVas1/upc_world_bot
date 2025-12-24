@echo off
REM UPC World Bot setup script for Windows

echo 🚀 UPC World Bot Setup
echo ======================
echo.

REM Check Python version
python --version > nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python 3.11+ from https://www.python.org
    exit /b 1
)

REM Create virtual environment
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat
echo ✓ Virtual environment activated

REM Install dependencies
echo Installing dependencies...
pip install -q -r requirements.txt
echo ✓ Dependencies installed

REM Setup .env
if not exist ".env" (
    echo Creating .env from template...
    copy .env.example .env
    echo ⚠️  Please edit .env with your settings
)

REM Create logs directory
if not exist "logs" mkdir logs
echo ✓ Logs directory created

REM Check Docker (optional)
docker --version > nul 2>&1
if errorlevel 0 (
    echo ✓ Docker found
) else (
    echo ⚠️  Docker not found (optional but recommended)
)

echo.
echo ✅ Setup complete!
echo.
echo Next steps:
echo 1. Edit .env with your settings
echo 2. Run database migrations: python -m alembic upgrade head
echo 3. Start the bot: python -m bot.main
echo.
