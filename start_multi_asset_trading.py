"""
Multi-Asset Elliott Wave Live Trading System Startup Script
Monitors all configured symbols every minute
"""

import time
from elliott_live_trader import ElliottWaveLiveTrader

def main():
    print("🌊 ELLIOTT WAVE MULTI-ASSET TRADING SYSTEM")
    print("=" * 60)
    print("📊 Scanning: EURUSD, XAUUSD, US30, US500.f, NAS100, AUDNOK")
    print("⏰ Analysis: Every 60 seconds")
    print("🎯 Max Positions: 6 simultaneous")
    print("🛡️ Risk per Symbol: 1.5%")
    print("=" * 60)
    
    # Initialize trader
    trader = ElliottWaveLiveTrader()
    
    # Show configuration
    print("📋 CONFIGURATION:")
    for symbol_config in trader.config['symbols']:
        if symbol_config.get('enabled', True):
            print(f"   ✅ {symbol_config['name']}: Risk {symbol_config['risk_per_trade']*100:.1f}%, "
                  f"Spread ≤{symbol_config['max_spread']}")
    
    print("\n🚀 Starting live trading...")
    print("🚨 Press Ctrl+C to stop\n")
    
    try:
        trader.start_trading()
        
        # Keep main thread alive
        while trader.is_running:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Stopping Elliott Wave trading system...")
        trader.stop_trading()
        print("✅ Trading stopped successfully")

if __name__ == "__main__":
    main()