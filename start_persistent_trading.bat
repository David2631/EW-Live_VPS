@echo off
echo ========================================
echo Elliott Wave Persistent Trading
echo ========================================
echo This will run the trading system in background
echo even when you disconnect from VPS
echo ========================================

cd /d "C:\Users\Administrator\Documents\Elliott-Wave-VPS-Trader"

REM Activate virtual environment
call venv\Scripts\activate

REM Start trading with output redirection
echo Starting Elliott Wave Trading...
echo Logs will be saved to elliott_live_trader.log
echo Press Ctrl+C to stop

REM Run in background with log output
python start_multi_asset_trading.py > trading_output.log 2>&1

pause