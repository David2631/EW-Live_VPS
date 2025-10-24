@echo off
echo 🔍 MARKET DATA DEBUG TEST
echo.
echo Testing if system actually fetches market data...
echo.

cd /d "C:\Users\Administrator\Documents\EW-Live_VPS_v2"

echo 📊 Running single symbol test with DEBUG logging...
python -c "
import logging
logging.basicConfig(level=logging.DEBUG, format='%%(asctime)s - %%(name)s - %%(levelname)s - %%(message)s')

from market_data_manager import MarketDataManager
import MetaTrader5 as mt5

print('🔗 Testing market data connection...')
market_data = MarketDataManager()

# Test single symbol
symbol = 'EURUSD'
print(f'📊 Testing {symbol}...')
df = market_data.get_live_data(symbol, mt5.TIMEFRAME_M30, 50)

if df is not None:
    print(f'✅ SUCCESS: Got {len(df)} bars for {symbol}')
    print(f'📈 Latest data: {df.tail(1)}')
else:
    print(f'❌ FAILED: No data for {symbol}')

print('🔚 Test complete')
"

pause