"""
Test Script for Dynamic Price Validation System
Tests the new price validator and enhanced trade executor locally
"""

import sys
import os
import logging
from datetime import datetime
import MetaTrader5 as mt5

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from price_validator import DynamicPriceValidator, ValidationResult
from signal_generator import TradingSignal, SignalType, SignalStrength
from elliott_wave_engine_original import Dir
from trade_executor import TradeExecutor
from risk_manager import PositionSize

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_price_validator():
    """Test the price validation module"""
    print("🔍 Testing Dynamic Price Validator...")
    
    validator = DynamicPriceValidator()
    
    # Test symbols with different characteristics
    test_cases = [
        {
            'symbol': 'EURUSD',
            'entry': 1.10000,
            'sl': 1.09900,  # 100 pips
            'tp': 1.10200   # 200 pips
        },
        {
            'symbol': 'US30',
            'entry': 46800.0,
            'sl': 46500.0,  # 300 points
            'tp': 48300.0   # 1500 points
        },
        {
            'symbol': 'XAUUSD',
            'entry': 2700.00,
            'sl': 2650.00,  # 500 points
            'tp': 2750.00   # 500 points
        },
        {
            'symbol': 'GBPUSD',
            'entry': 1.33000,
            'sl': 1.32700,  # 300 pips
            'tp': 1.33500   # 500 pips
        }
    ]
    
    for case in test_cases:
        print(f"\n📊 Testing {case['symbol']}:")
        print(f"   Entry: {case['entry']}")
        print(f"   Original SL: {case['sl']}")
        print(f"   Original TP: {case['tp']}")
        
        # Get symbol info
        symbol_info = validator.get_symbol_info(case['symbol'])
        if symbol_info:
            print(f"   Symbol Info: digits={symbol_info.digits}, point={symbol_info.point}, "
                  f"spread={symbol_info.spread}, stops_level={symbol_info.stops_level}")
        
        # Validate order
        validation = validator.validate_order(
            symbol=case['symbol'],
            entry_price=case['entry'],
            stop_loss=case['sl'],
            take_profit=case['tp']
        )
        
        print(f"   Validation: {'✅ Valid' if validation.is_valid else '❌ Invalid'}")
        if validation.adjusted_sl != case['sl']:
            print(f"   🔧 SL adjusted to: {validation.adjusted_sl} ({validation.pip_distance_sl:.1f} pips)")
        if validation.adjusted_tp != case['tp']:
            print(f"   🔧 TP adjusted to: {validation.adjusted_tp} ({validation.pip_distance_tp:.1f} pips)")
        
        if validation.error_message:
            print(f"   ❌ Error: {validation.error_message}")

def test_enhanced_trade_executor():
    """Test the enhanced trade executor with price validation"""
    print("\n🚀 Testing Enhanced Trade Executor...")
    
    executor = TradeExecutor()
    
    # Connect to MT5
    if not executor.connect():
        print("❌ Failed to connect to MT5")
        return
    
    print("✅ Connected to MT5")
    
    # Create test signals
    test_signals = [
        TradingSignal(
            symbol="EURUSD",
            signal_type=SignalType.BUY,
            strength=SignalStrength.STRONG,
            entry_price=1.10000,
            stop_loss=1.09950,  # Very tight - should be adjusted
            take_profit=1.10050,  # Very tight - should be adjusted
            confidence=80.0,
            wave_pattern="ABC",
            wave_direction=Dir.UP,
            current_wave="C",
            fibonacci_level=None,
            trend_alignment=True,
            momentum_confirmation=True,
            volume_confirmation=True,
            stop_loss_pips=5.0,
            take_profit_pips=5.0,
            reward_risk_ratio=1.0,
            timestamp=datetime.now(),
            reasoning="Test signal for price validation"
        ),
        TradingSignal(
            symbol="US30",
            signal_type=SignalType.SELL,
            strength=SignalStrength.STRONG,
            entry_price=46800.0,
            stop_loss=47100.0,  # 300 points
            take_profit=45300.0,  # 1500 points
            confidence=85.0,
            wave_pattern="Impulse",
            wave_direction=Dir.DOWN,
            current_wave="3",
            fibonacci_level=None,
            trend_alignment=True,
            momentum_confirmation=True,
            volume_confirmation=True,
            stop_loss_pips=300.0,
            take_profit_pips=1500.0,
            reward_risk_ratio=5.0,
            timestamp=datetime.now(),
            reasoning="Test signal for US30 validation"
        )
    ]
    
    for signal in test_signals:
        print(f"\n📋 Testing {signal.symbol} signal:")
        print(f"   Type: {signal.signal_type.value}")
        print(f"   Entry: {signal.entry_price}")
        print(f"   SL: {signal.stop_loss}")
        print(f"   TP: {signal.take_profit}")
        
        # Create dummy position size
        position_size = PositionSize(
            symbol=signal.symbol,
            lot_size=0.01,  # Very small for testing
            risk_amount=10.0,
            pip_value=1.0,
            stop_loss_pips=signal.stop_loss_pips,
            take_profit_pips=signal.take_profit_pips,
            reward_risk_ratio=signal.reward_risk_ratio,
            is_valid=True,
            reason="Test position"
        )
        
        # Test the execution (DRY RUN - don't actually execute)
        print("   🔍 Validating order parameters...")
        
        # Just test the validation part
        validation = executor.price_validator.validate_order(
            symbol=signal.symbol,
            entry_price=signal.entry_price,
            stop_loss=signal.stop_loss,
            take_profit=signal.take_profit
        )
        
        if validation.is_valid:
            print("   ✅ Order validation passed")
            if validation.adjusted_sl != signal.stop_loss:
                print(f"   🔧 SL would be adjusted to: {validation.adjusted_sl}")
            if validation.adjusted_tp != signal.take_profit:
                print(f"   🔧 TP would be adjusted to: {validation.adjusted_tp}")
        else:
            print(f"   ❌ Order validation failed: {validation.error_message}")

def test_symbol_info_debugging():
    """Test the symbol info debugging for retcode 10030 troubleshooting"""
    print("\n🔧 Testing Symbol Info Debugging...")
    
    executor = TradeExecutor()
    
    if not executor.connect():
        print("❌ Failed to connect to MT5")
        return
    
    # Test symbols that commonly have retcode 10030 issues
    problem_symbols = ['US30', 'NAS100', 'XAUUSD', 'GBPUSD']
    
    for symbol in problem_symbols:
        print(f"\n🔍 Debugging {symbol}:")
        executor._debug_symbol_info(symbol)
        executor._debug_order_filling_modes(symbol)

def main():
    """Main test function"""
    print("🧪 DYNAMIC PRICE VALIDATION SYSTEM - LOCAL TESTS")
    print("=" * 60)
    
    # Initialize MT5
    if not mt5.initialize():
        print("❌ Failed to initialize MT5")
        return
    
    try:
        # Run tests
        test_price_validator()
        test_enhanced_trade_executor()
        test_symbol_info_debugging()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS COMPLETED")
        
    except Exception as e:
        print(f"❌ Test error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        mt5.shutdown()

if __name__ == "__main__":
    main()