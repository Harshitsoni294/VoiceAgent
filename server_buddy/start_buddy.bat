@echo off
echo Starting Buddy Server...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed or not in PATH.
    echo Please install Python 3.8 or higher.
    pause
    exit /b 1
)

REM Check if pip is available
pip --version >nul 2>&1
if errorlevel 1 (
    echo pip is not available.
    echo Please ensure pip is installed.
    pause
    exit /b 1
)

REM Install dependencies if requirements.txt exists
if exist requirements.txt (
    echo Installing dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo Failed to install dependencies.
        pause
        exit /b 1
    )
)

REM Check if .env file exists
if not exist .env (
    echo Warning: .env file not found.
    echo Please create .env file with your GOOGLE_API_KEY
    echo.
)

REM Start the server
echo Starting Buddy server on port 8001...
echo Press Ctrl+C to stop the server
echo.
python main.py

pause
