"""
EMERGENCY SCRIPT: Fix Missing Stop Loss & Take Profit
Immediately fixes all Elliott Wave positions without SL/TP
"""

import MetaTrader5 as mt5
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def connect_mt5():
    """Connect to MT5"""
    if not mt5.initialize():
        error = mt5.last_error()
        logger.error(f"MT5 connection failed: {error}")
        return False
    
    account_info = mt5.account_info()
    if account_info:
        logger.info(f"Connected to MT5 account: {account_info.login}")
        return True
    return False

def calculate_emergency_sl_tp(position):
    """Calculate conservative SL/TP for position"""
    try:
        symbol_info = mt5.symbol_info(position.symbol)
        if not symbol_info:
            return None, None
        
        current_price = symbol_info.bid if position.type == 0 else symbol_info.ask
        point = symbol_info.point
        
        # Conservative SL/TP: 50 pips SL, 100 pips TP
        if position.type == 0:  # Buy position
            stop_loss = current_price - (50 * point * 10)
            take_profit = current_price + (100 * point * 10)
        else:  # Sell position
            stop_loss = current_price + (50 * point * 10)
            take_profit = current_price - (100 * point * 10)
        
        # Round to tick size
        tick_size = symbol_info.trade_tick_size
        stop_loss = round(stop_loss / tick_size) * tick_size
        take_profit = round(take_profit / tick_size) * tick_size
        
        return stop_loss, take_profit
        
    except Exception as e:
        logger.error(f"Error calculating SL/TP for {position.symbol}: {e}")
        return None, None

def set_sl_tp(position_id, symbol, sl, tp):
    """Set SL/TP for position"""
    try:
        request = {
            "action": mt5.TRADE_ACTION_SLTP,
            "position": position_id,
            "symbol": symbol,
            "sl": sl,
            "tp": tp,
            "magic": 202501,  # Elliott Wave magic number
            "comment": "Emergency_SLTP_Fix"
        }
        
        result = mt5.order_send(request)
        
        if result and result.retcode == mt5.TRADE_RETCODE_DONE:
            return True
        else:
            if result:
                logger.error(f"SL/TP set failed for {symbol}: {result.retcode}")
            else:
                error = mt5.last_error()
                logger.error(f"SL/TP set failed for {symbol}: {error}")
            return False
            
    except Exception as e:
        logger.error(f"Exception setting SL/TP for {symbol}: {e}")
        return False

def main():
    """Main execution"""
    print("🚨 EMERGENCY SL/TP FIX SCRIPT")
    print("=" * 40)
    
    if not connect_mt5():
        print("❌ Failed to connect to MT5")
        return
    
    # Get all positions
    positions = mt5.positions_get()
    if not positions:
        print("ℹ️  No positions found")
        mt5.shutdown()
        return
    
    elliott_positions = []
    missing_sl_tp = []
    
    for pos in positions:
        if pos.magic == 202501:  # Elliott Wave positions
            elliott_positions.append(pos)
            if pos.sl == 0.0 or pos.tp == 0.0:
                missing_sl_tp.append(pos)
    
    print(f"📊 Found {len(elliott_positions)} Elliott Wave positions")
    print(f"🚨 {len(missing_sl_tp)} positions missing SL/TP")
    
    if not missing_sl_tp:
        print("✅ All positions have SL/TP set!")
        mt5.shutdown()
        return
    
    print("\\n🔧 Fixing positions...")
    fixed_count = 0
    
    for pos in missing_sl_tp:
        print(f"\\n📍 {pos.symbol} (ID: {pos.ticket})")
        print(f"   Type: {'BUY' if pos.type == 0 else 'SELL'}")
        print(f"   Volume: {pos.volume}")
        print(f"   Current SL: {pos.sl}")
        print(f"   Current TP: {pos.tp}")
        
        # Calculate emergency SL/TP
        sl, tp = calculate_emergency_sl_tp(pos)
        
        if sl and tp:
            print(f"   New SL: {sl:.5f}")
            print(f"   New TP: {tp:.5f}")
            
            if set_sl_tp(pos.ticket, pos.symbol, sl, tp):
                print("   ✅ SL/TP set successfully!")
                fixed_count += 1
            else:
                print("   ❌ Failed to set SL/TP")
        else:
            print("   ❌ Could not calculate SL/TP")
    
    print(f"\\n✅ Fixed {fixed_count}/{len(missing_sl_tp)} positions")
    
    # Verify fixes
    print("\\n🔍 Verifying fixes...")
    updated_positions = mt5.positions_get()
    still_missing = 0
    
    for pos in updated_positions:
        if pos.magic == 202501 and (pos.sl == 0.0 or pos.tp == 0.0):
            still_missing += 1
            print(f"❌ {pos.symbol} still missing SL/TP")
    
    if still_missing == 0:
        print("✅ All Elliott Wave positions now have SL/TP!")
    else:
        print(f"⚠️  {still_missing} positions still missing SL/TP")
    
    mt5.shutdown()
    print("\\n🏁 Script completed")

if __name__ == "__main__":
    main()