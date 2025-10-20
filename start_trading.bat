@echo off
title Elliott Wave Live Trader

REM Activate virtual environment if it exists
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    echo ✅ Virtual environment activated
)

echo ========================================
echo Elliott Wave Live Trader - Starting...
echo ========================================
echo.

REM Check if config exists
if not exist "elliott_live_config.json" (
    echo ❌ Configuration file missing!
    echo Please ensure elliott_live_config.json exists
    echo.
    pause
    exit /b 1
)

REM Check MT5 connection
echo Checking MT5 connection...
python mt5_diagnostic.py >nul 2>&1
if errorlevel 1 (
    echo ⚠️  MT5 connection issues detected
    echo Please ensure MT5 is running and connected
    echo.
    pause
)

echo ✅ Starting Elliott Wave Live Trader...
echo.
echo 🚨 Press Ctrl+C to stop trading
echo.

:start
python elliott_live_trader.py
if errorlevel 1 (
    echo.
    echo ❌ Trading system stopped with error
    echo Restarting in 30 seconds...
    echo Press Ctrl+C to exit completely
    timeout /t 30
    goto start
) else (
    echo.
    echo ✅ Trading system stopped gracefully
    echo Restarting in 10 seconds...
    echo Press Ctrl+C to exit completely
    timeout /t 10
    goto start
)