@echo off
REM ================================================================
REM Elliott Wave V2 - VPS Installation & Start Script
REM ================================================================

echo 🚀 Elliott Wave V2 - VPS Installation Starting...
echo ================================================================

REM Stop any running instances
echo ⏹️ Stopping existing processes...
taskkill /f /im python.exe >nul 2>&1

REM Remove old installation
echo 🗑️ Removing old installation...
cd /d C:\
if exist "Elliott-Wave-VPS-Trader" (
    rmdir /s /q "Elliott-Wave-VPS-Trader"
)

REM Clone fresh repository
echo 📥 Cloning fresh repository...
git clone https://github.com/David2631/Elliott-Wave-VPS-Trader.git
if errorlevel 1 (
    echo ❌ Git clone failed! Please install Git first.
    pause
    exit /b 1
)

REM Navigate to directory
cd /d C:\Elliott-Wave-VPS-Trader\Elliott-Wave-Live-V2

REM Install dependencies
echo 📦 Installing Python dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ⚠️ Some dependencies failed, but continuing...
)

REM Check MT5 connection
echo 🔍 Testing MT5 connection...
python -c "import MetaTrader5 as mt5; print('✅ MT5 Library OK' if mt5.initialize() else '❌ MT5 Not Connected'); mt5.shutdown()"

echo ================================================================
echo 🎯 Installation Complete! Available start options:
echo ================================================================
echo 1. SIMPLE SYMBOLS (Demo-friendly):
echo    python elliott_wave_trader_v2.py --symbols symbols_simple.txt --thr 0.30
echo.
echo 2. DEMO SYMBOLS (Reduced set):
echo    python elliott_wave_trader_v2.py --symbols symbols_demo.txt --thr 0.30
echo.
echo 3. FULL SYMBOLS (All markets):
echo    python elliott_wave_trader_v2.py --symbols symbols.txt --thr 0.30
echo.
echo 4. AGGRESSIVE (No filters):
echo    python elliott_wave_trader_v2.py --symbols symbols_simple.txt --no-ml --no-ema
echo ================================================================

echo 📋 IMPORTANT: Ensure MT5 AutoTrading is enabled!
echo    Tools → Options → Expert Advisors → Allow automated trading
echo.

echo 🚀 Starting with SIMPLE SYMBOLS (recommended)...
echo Press Ctrl+C to stop, or close window to run in background
echo.

REM Start with simple symbols
python elliott_wave_trader_v2.py --symbols symbols_simple.txt --thr 0.30

pause