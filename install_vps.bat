@echo off
echo ========================================
echo Elliott Wave Live Trader - Installation
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.9+ from https://python.org
    echo.
    pause
    exit /b 1
)

echo ✅ Python detected
echo.

REM Create virtual environment (optional but recommended)
echo Creating virtual environment...
python -m venv venv
if errorlevel 1 (
    echo WARNING: Could not create virtual environment
    echo Continuing with system Python...
) else (
    echo ✅ Virtual environment created
    call venv\Scripts\activate.bat
)

echo.
echo Installing Python packages...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install requirements
    pause
    exit /b 1
)

echo ✅ Python packages installed
echo.

echo Checking MT5 installation...
python mt5_diagnostic.py
if errorlevel 1 (
    echo WARNING: MT5 connection issues detected
    echo Please ensure MT5 is installed and running
    echo Configure your broker account in MT5 first
    echo.
)

echo.
echo Running comprehensive system tests...
python live_trading_tests.py
if errorlevel 1 (
    echo WARNING: Some tests failed
    echo Check the output above for issues
    echo.
)

echo.
echo ========================================
echo Installation Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Configure MT5 with your broker account
echo 2. Update elliott_live_config.json with your settings
echo 3. Test with: python live_trading_tests.py
echo 4. Start trading: start_trading.bat
echo.
echo ⚠️  IMPORTANT: Test with demo account first!
echo.
pause