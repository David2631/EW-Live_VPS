@echo off
echo 🔍 CONFIG DEBUG - Elliott Wave Trader V2
echo.

cd /d "C:\Users\Administrator\Documents\EW-Live_VPS_v2"

echo 📋 Checking config file...
if exist elliott_live_config_v2.json (
    echo ✅ elliott_live_config_v2.json found
    type elliott_live_config_v2.json | findstr scan_interval
) else (
    echo ❌ elliott_live_config_v2.json NOT FOUND! Using default 60s!
)

echo.
echo 📊 Running with explicit config check...
python -c "
import json
try:
    with open('elliott_live_config_v2.json', 'r') as f:
        config = json.load(f)
    print(f'✅ Config loaded: scan_interval = {config.get(\"scan_interval\", \"NOT FOUND\")}')
except FileNotFoundError:
    print('❌ Config file not found - using defaults!')
except Exception as e:
    print(f'❌ Config error: {e}')
"

pause