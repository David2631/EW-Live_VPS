@echo off
echo ========================================
echo Elliott Wave Windows Service Setup
echo ========================================

REM Check if NSSM is installed
where nssm >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ❌ NSSM not found. Installing NSSM...
    echo.
    echo Please download NSSM from: https://nssm.cc/download
    echo Extract nssm.exe to C:\Windows\System32\
    echo Then run this script again.
    pause
    exit /b 1
)

echo ✅ NSSM found. Setting up Elliott Wave Trading Service...

REM Set paths
set SERVICE_NAME=ElliottWaveTrading
set PYTHON_PATH=C:\Users\Administrator\Documents\Elliott-Wave-VPS-Trader\venv\Scripts\python.exe
set SCRIPT_PATH=C:\Users\Administrator\Documents\Elliott-Wave-VPS-Trader\start_multi_asset_trading.py
set WORK_DIR=C:\Users\Administrator\Documents\Elliott-Wave-VPS-Trader

REM Stop and remove existing service if it exists
nssm stop %SERVICE_NAME% >nul 2>nul
nssm remove %SERVICE_NAME% confirm >nul 2>nul

REM Install new service
echo Installing Windows Service...
nssm install %SERVICE_NAME% "%PYTHON_PATH%" "%SCRIPT_PATH%"
nssm set %SERVICE_NAME% AppDirectory "%WORK_DIR%"
nssm set %SERVICE_NAME% DisplayName "Elliott Wave Live Trading System"
nssm set %SERVICE_NAME% Description "Automated Elliott Wave trading for MT5"
nssm set %SERVICE_NAME% Start SERVICE_AUTO_START

REM Set up logging
nssm set %SERVICE_NAME% AppStdout "%WORK_DIR%\service_output.log"
nssm set %SERVICE_NAME% AppStderr "%WORK_DIR%\service_error.log"

echo ✅ Service installed successfully!
echo.
echo 📋 Service Management:
echo   Start:   nssm start %SERVICE_NAME%
echo   Stop:    nssm stop %SERVICE_NAME%
echo   Status:  nssm status %SERVICE_NAME%
echo   Remove:  nssm remove %SERVICE_NAME%
echo.
echo 🌊 Would you like to start the service now? (Y/N)
set /p choice=

if /i "%choice%"=="Y" (
    nssm start %SERVICE_NAME%
    echo ✅ Elliott Wave Trading Service started!
    echo 📊 The system will now run 24/7 even when you disconnect.
) else (
    echo ℹ️ Service created but not started.
    echo   Run 'nssm start %SERVICE_NAME%' to start trading.
)

echo.
echo 📝 Log files:
echo   Output: %WORK_DIR%\service_output.log
echo   Errors: %WORK_DIR%\service_error.log
echo   Trading: %WORK_DIR%\elliott_live_trader.log

pause