#!/usr/bin/env python3
"""
Test Duplicate Position Prevention
Ensures no duplicate trades are executed for same symbol
"""

import sys
import os
import logging
from datetime import datetime

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from trade_executor import TradeExecutor
from signal_generator import TradingSignal, SignalType
from risk_manager import PositionSize

def setup_logging():
    """Setup logging for testing"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def test_duplicate_prevention():
    """Test duplicate position prevention logic"""
    print("🧪 Testing Duplicate Position Prevention...")
    print("=" * 60)
    
    # Initialize trade executor
    executor = TradeExecutor()
    
    if not executor.connect():
        print("❌ Failed to connect to MT5")
        return False
    
    print("✅ Connected to MT5")
    
    # Test 1: Check existing positions loading
    print("\n📍 Test 1: Loading existing positions...")
    executor._load_existing_positions()
    
    if executor.active_positions:
        print(f"Found {len(executor.active_positions)} existing positions:")
        for pos_id, position in executor.active_positions.items():
            print(f"  - {position.symbol}: {position.volume} lots (ID: {pos_id})")
    else:
        print("  No existing positions found")
    
    # Test 2: Check duplicate detection for various symbols
    print("\n🔍 Test 2: Testing duplicate detection...")
    test_symbols = ['EURUSD', 'GBPUSD', 'AUDUSD', 'US30', 'XAUUSD', 'NAS100']
    
    for symbol in test_symbols:
        has_position = executor._has_existing_position(symbol)
        status = "🔴 HAS POSITION" if has_position else "🟢 NO POSITION"
        print(f"  {symbol}: {status}")
    
    # Test 3: Simulate trade execution attempts
    print("\n⚡ Test 3: Simulating trade execution attempts...")
    
    # Create dummy signal and position size
    from elliott_wave_engine_original import Dir
    from signal_generator import SignalStrength
    dummy_signal = TradingSignal(
        symbol="US30",
        signal_type=SignalType.SELL,
        strength=SignalStrength.STRONG,
        entry_price=46600.0,
        stop_loss=46900.0,
        take_profit=45100.0,
        confidence=85.0,
        wave_pattern="Impulse Wave 3",
        wave_direction=Dir.DOWN,
        current_wave="Wave 3",
        fibonacci_level=None,
        trend_alignment=True,
        momentum_confirmation=True,
        volume_confirmation=True,
        stop_loss_pips=300.0,
        take_profit_pips=1500.0,
        reward_risk_ratio=5.0,
        timestamp=datetime.now(),
        reasoning="Test signal for duplicate prevention"
    )
    
    dummy_position_size = PositionSize(
        symbol="US30",
        lot_size=0.1,
        risk_amount=100.0,
        stop_loss_pips=300.0,
        take_profit_pips=1500.0,
        reward_risk_ratio=5.0,
        pip_value=1.0,
        is_valid=True,
        reason="Test position"
    )
    
    # Try to execute trade
    print(f"\n🎯 Attempting to execute {dummy_signal.symbol} trade...")
    result = executor.execute_signal(dummy_signal, dummy_position_size)
    
    if result.success:
        print(f"✅ Trade executed: {dummy_signal.symbol}")
    else:
        print(f"❌ Trade blocked: {result.error_message}")
        if "already exists" in result.error_message:
            print("  ✅ Duplicate prevention working correctly!")
        else:
            print(f"  ⚠️ Unexpected error: {result.error_message}")
    
    # Test 4: Monitor current positions
    print("\n📊 Test 4: Current position status...")
    status = executor.monitor_positions()
    print(f"Total Positions: {status['total_positions']}")
    print(f"Long Positions: {status['long_positions']}")
    print(f"Short Positions: {status['short_positions']}")
    print(f"Total P&L: ${status['total_profit']:.2f}")
    
    executor.disconnect()
    print("\n✅ Test completed successfully!")
    return True

if __name__ == "__main__":
    setup_logging()
    test_duplicate_prevention()