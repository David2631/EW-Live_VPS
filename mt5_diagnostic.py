"""
MT5 Connection Diagnostic Tool
Hilft bei der Diagnose von MetaTrader5 Python Verbindungsproblemen
"""

import sys
import os
from datetime import datetime

def check_mt5_installation():
    """Check if MT5 Python package is installed"""
    print("🔍 Checking MetaTrader5 Python package...")
    try:
        import MetaTrader5 as mt5
        print("✅ MetaTrader5 package is installed")
        return True
    except ImportError as e:
        print(f"❌ MetaTrader5 package not found: {e}")
        print("💡 Install with: pip install MetaTrader5")
        return False

def check_mt5_terminal():
    """Check MT5 terminal connection"""
    print("\n🔍 Checking MetaTrader5 Terminal connection...")
    
    try:
        import MetaTrader5 as mt5
        
        # Try to initialize
        print("📡 Attempting to initialize MT5...")
        if not mt5.initialize():
            error = mt5.last_error()
            print(f"❌ MT5 initialization failed with error: {error}")
            return False
        
        print("✅ MT5 initialized successfully!")
        
        # Get terminal info
        terminal_info = mt5.terminal_info()
        if terminal_info:
            print(f"✅ Terminal: {terminal_info.name} Build {terminal_info.build}")
            print(f"   Path: {terminal_info.path}")
            print(f"   Data Path: {terminal_info.data_path}")
        else:
            print("⚠️  Could not get terminal info")
        
        # Get account info
        account_info = mt5.account_info()
        if account_info:
            print(f"✅ Account: {account_info.login}")
            print(f"   Company: {account_info.company}")
            print(f"   Currency: {account_info.currency}")
            print(f"   Balance: {account_info.balance}")
            print(f"   Margin: {account_info.margin}")
        else:
            print("❌ No account info - not logged in to trading account")
            mt5.shutdown()
            return False
        
        # Test symbol access
        print("\n🔍 Testing symbol access...")
        symbols = mt5.symbols_get()
        if symbols:
            print(f"✅ Found {len(symbols)} symbols")
            # Show first few symbols
            for symbol in symbols[:5]:
                print(f"   - {symbol.name}: {symbol.description}")
        else:
            print("⚠️  No symbols found")
        
        # Test market data
        print("\n🔍 Testing market data access...")
        eurusd_info = mt5.symbol_info("EURUSD")
        if eurusd_info:
            print("✅ EURUSD symbol info accessible")
            tick = mt5.symbol_info_tick("EURUSD")
            if tick:
                print(f"   Current price: {tick.bid}/{tick.ask}")
            else:
                print("⚠️  Could not get current price")
        else:
            print("⚠️  EURUSD symbol not found (may not be available on this broker)")
        
        mt5.shutdown()
        return True
        
    except Exception as e:
        print(f"❌ Error during MT5 testing: {e}")
        return False

def print_troubleshooting_guide():
    """Print comprehensive troubleshooting guide"""
    print("\n" + "="*70)
    print("🛠️  COMPLETE MT5 SETUP TROUBLESHOOTING GUIDE")
    print("="*70)
    
    print("\n📋 STEP 1: Install MetaTrader 5 Terminal")
    print("   1. Download MT5 from your broker or https://www.metatrader5.com/")
    print("   2. Install MT5 application")
    print("   3. Create trading account or login with existing credentials")
    print("   4. Ensure you can see live prices and account balance")
    
    print("\n📋 STEP 2: Algorithmischen Handel aktivieren (DEUTSCHE MT5 VERSION)")
    print("   1. In MT5: Extras → Einstellungen → Expert Advisors")
    print("   2. ☑️ Haken bei 'Automatisierten Handel erlauben'")
    print("   3. ☑️ Haken bei 'DLL-Import erlauben'") 
    print("   4. ☑️ Haken bei 'WebRequest für aufgelistete URL erlauben' (optional)")
    print("   5. OK klicken")
    print("   6. MetaTrader 5 NEU STARTEN")
    
    print("\n📋 STEP 3: Install Python Package")
    print("   1. Open Command Prompt/PowerShell as Administrator")
    print("   2. Run: pip install MetaTrader5")
    print("   3. Verify: python -c \"import MetaTrader5; print('OK')\"")
    
    print("\n📋 STEP 4: Run Both as Administrator (if needed)")
    print("   1. Close MT5 completely")
    print("   2. Right-click MT5 shortcut → 'Run as administrator'")
    print("   3. Login to your account")
    print("   4. Run Python script as administrator too")
    
    print("\n📋 STEP 5: Check Windows Security")
    print("   1. Windows Defender:")
    print("      - Add MT5 folder to exclusions")
    print("      - Add Python script folder to exclusions")
    print("   2. Firewall:")
    print("      - Allow MT5 through Windows Firewall")
    print("      - Allow Python through Windows Firewall")
    
    print("\n📋 STEP 6: Verify Demo vs Live Account")
    print("   1. Start with DEMO account for testing")
    print("   2. Ensure account is 'Connected' (green icon in MT5)")
    print("   3. Check if you can place manual trades in MT5")
    
    print("\n📋 STEP 7: Common Error Solutions")
    print("   • 'No module named MetaTrader5':")
    print("     → pip install MetaTrader5")
    print("   • 'MT5 initialization failed':")
    print("     → MT5 not running or algorithmic trading disabled")
    print("   • 'Failed to get account info':")
    print("     → Not logged into broker account")
    print("   • 'Access denied':")
    print("     → Run as administrator")
    
    print("\n" + "="*70)
    print("🎯 After following these steps, test again with:")
    print("   python mt5_diagnostic.py")
    print("="*70)

def main():
    """Main diagnostic function"""
    print("🚀 MetaTrader5 Python Connection Diagnostic")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*50)
    
    # Check Python package
    if not check_mt5_installation():
        print_troubleshooting_guide()
        return
    
    # Check MT5 terminal connection
    if not check_mt5_terminal():
        print_troubleshooting_guide()
        return
    
    print("\n🎉 ALL CHECKS PASSED!")
    print("✅ MetaTrader5 Python integration is working correctly")
    print("🚀 You can now run the Elliott Wave Live Trader!")
    
    print("\n💡 Next steps:")
    print("   1. Configure elliott_live_config.json")
    print("   2. Test on demo account first")
    print("   3. Run: python elliott_live_trader.py")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Diagnostic cancelled by user")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        print("Please report this error for further assistance")
    
    input("\nPress Enter to exit...")