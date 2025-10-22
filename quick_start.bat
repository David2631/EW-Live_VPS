@echo off
REM ================================================================
REM Elliott Wave V2 - Quick Start (für bereits installierte Version)
REM ================================================================

echo 🚀 Elliott Wave V2 - Quick Start
echo ================================================================

REM Stop existing processes
taskkill /f /im python.exe >nul 2>&1

REM Update repository
echo 📥 Updating repository...
cd /d C:\Elliott-Wave-VPS-Trader
git pull origin master

REM Navigate to Live V2
cd Elliott-Wave-Live-V2

REM Test MT5 connection
echo 🔍 Testing MT5 connection...
python -c "import MetaTrader5 as mt5; print('✅ MT5 Connected' if mt5.initialize() else '❌ MT5 Connection Failed'); mt5.shutdown()"

REM Check symbol availability
echo 🔍 Checking symbol availability...
python symbol_checker.py

echo ================================================================
echo 🎯 Select start option:
echo ================================================================
echo [1] SIMPLE SYMBOLS (EURUSD, GBPUSD, USDJPY, AUDUSD, USDCAD, XAUUSD, XAGUSD)
echo [2] DEMO SYMBOLS (EURUSD, XAUUSD, US30)  
echo [3] FULL SYMBOLS (All markets)
echo [4] AGGRESSIVE MODE (No ML filter)
echo ================================================================

set /p choice="Enter choice (1-4): "

if "%choice%"=="1" (
    echo 🎯 Starting with SIMPLE SYMBOLS...
    python elliott_wave_trader_v2.py --symbols symbols_simple.txt --thr 0.30
) else if "%choice%"=="2" (
    echo 🎯 Starting with DEMO SYMBOLS...
    python elliott_wave_trader_v2.py --symbols symbols_demo.txt --thr 0.30
) else if "%choice%"=="3" (
    echo 🎯 Starting with FULL SYMBOLS...
    python elliott_wave_trader_v2.py --symbols symbols.txt --thr 0.30
) else if "%choice%"=="4" (
    echo 🎯 Starting AGGRESSIVE MODE...
    python elliott_wave_trader_v2.py --symbols symbols_simple.txt --no-ml --no-ema
) else (
    echo ❌ Invalid choice. Starting with SIMPLE SYMBOLS...
    python elliott_wave_trader_v2.py --symbols symbols_simple.txt --thr 0.30
)

echo.
echo System stopped. Press any key to exit.
pause