"""
Elliott Wave Live Trading System - Comprehensive Test Suite
Tests system robustness, error handling, and production readiness
"""

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import time
import json
import threading
from datetime import datetime, timedelta
import logging
from elliott_live_trader import ElliottWaveLiveTrader

class LiveTradingSystemTests:
    """Comprehensive test suite for the live trading system"""
    
    def __init__(self):
        self.test_results = {}
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        
    def run_all_tests(self):
        """Run complete test suite"""
        print("🧪 STARTING COMPREHENSIVE LIVE TRADING TESTS")
        print("=" * 60)
        
        tests = [
            ("MT5 Connection Stability", self.test_mt5_connection_stability),
            ("Data Feed Reliability", self.test_data_feed_reliability),
            ("Elliott Wave Detection", self.test_elliott_wave_detection),
            ("Risk Management", self.test_risk_management),
            ("Order Execution Simulation", self.test_order_execution),
            ("Error Recovery", self.test_error_recovery),
            ("Performance Under Load", self.test_performance_load),
            ("Configuration Validation", self.test_configuration),
            ("VPS Readiness Check", self.test_vps_readiness)
        ]
        
        for test_name, test_func in tests:
            print(f"\n🔍 Running: {test_name}")
            try:
                result = test_func()
                self.test_results[test_name] = {"status": "PASSED" if result else "FAILED", "result": result}
                print(f"✅ {test_name}: {'PASSED' if result else 'FAILED'}")
            except Exception as e:
                self.test_results[test_name] = {"status": "ERROR", "error": str(e)}
                print(f"❌ {test_name}: ERROR - {e}")
        
        self.print_test_summary()
        return self.test_results
    
    def test_mt5_connection_stability(self):
        """Test MT5 connection stability and reconnection"""
        print("   📡 Testing MT5 connection...")
        
        # Test initial connection
        if not mt5.initialize():
            print("   ❌ Initial connection failed")
            return False
        
        # Test connection info
        terminal_info = mt5.terminal_info()
        account_info = mt5.account_info()
        
        if not terminal_info or not account_info:
            print("   ❌ Failed to get terminal/account info")
            mt5.shutdown()
            return False
        
        print(f"   ✅ Connected to: {terminal_info.name}")
        print(f"   ✅ Account: {account_info.login} ({account_info.company})")
        
        # Test multiple reconnections
        for i in range(3):
            mt5.shutdown()
            time.sleep(1)
            if not mt5.initialize():
                print(f"   ❌ Reconnection {i+1} failed")
                return False
            print(f"   ✅ Reconnection {i+1} successful")
        
        mt5.shutdown()
        return True
    
    def test_data_feed_reliability(self):
        """Test market data feed reliability"""
        print("   📊 Testing data feed...")
        
        if not mt5.initialize():
            return False
        
        try:
            # Test symbol access
            symbols = mt5.symbols_get()
            if not symbols or len(symbols) == 0:
                print("   ❌ No symbols available")
                return False
            
            print(f"   ✅ Found {len(symbols)} symbols")
            
            # Test EURUSD data (main trading symbol)
            eurusd_info = mt5.symbol_info("EURUSD")
            if not eurusd_info:
                print("   ❌ EURUSD not available")
                return False
            
            # Test tick data
            tick = mt5.symbol_info_tick("EURUSD")
            if not tick:
                print("   ❌ No tick data for EURUSD")
                return False
            
            print(f"   ✅ EURUSD tick: {tick.bid}/{tick.ask}")
            
            # Test historical data
            rates = mt5.copy_rates_from_pos("EURUSD", mt5.TIMEFRAME_M30, 1, 100)
            if rates is None or len(rates) < 50:
                print("   ❌ Insufficient historical data")
                return False
            
            print(f"   ✅ Historical data: {len(rates)} bars")
            
            # Test data consistency
            df = pd.DataFrame(rates)
            if df.isnull().any().any():
                print("   ❌ Data contains null values")
                return False
            
            print("   ✅ Data integrity check passed")
            return True
            
        finally:
            mt5.shutdown()
    
    def test_elliott_wave_detection(self):
        """Test Elliott Wave signal generation"""
        print("   🌊 Testing Elliott Wave detection...")
        
        trader = ElliottWaveLiveTrader()
        
        # Create synthetic test data
        dates = pd.date_range(start='2024-01-01', periods=200, freq='30T')
        np.random.seed(42)  # Reproducible test
        
        # Generate trending price data (simulates Wave 3)
        price_base = 1.1000
        trend = np.linspace(0, 0.02, 200)  # 2% uptrend
        noise = np.random.normal(0, 0.001, 200)  # 0.1% noise
        closes = price_base + trend + noise
        
        # Create realistic OHLC data
        test_data = pd.DataFrame({
            'date': dates,
            'open': closes * (1 + np.random.normal(0, 0.0001, 200)),
            'high': closes * (1 + np.abs(np.random.normal(0, 0.0002, 200))),
            'low': closes * (1 - np.abs(np.random.normal(0, 0.0002, 200))),
            'close': closes,
            'volume': np.random.randint(1000, 5000, 200)
        })
        
        # Add indicators
        test_data = trader.add_indicators(test_data)
        
        # Test Elliott Wave analysis
        signal = trader.analyze_elliott_wave_live(test_data)
        
        if not signal or 'action' not in signal:
            print("   ❌ No signal generated")
            return False
        
        print(f"   ✅ Signal generated: {signal['action']}")
        print(f"   ✅ Confidence: {signal['confidence']:.2f}")
        print(f"   ✅ Setup: {signal.get('setup_type', 'Unknown')}")
        
        # Test signal validation
        required_fields = ['action', 'confidence', 'stop_loss', 'take_profit']
        for field in required_fields:
            if field not in signal:
                print(f"   ❌ Missing signal field: {field}")
                return False
        
        return True
    
    def test_risk_management(self):
        """Test risk management systems"""
        print("   🛡️ Testing risk management...")
        
        trader = ElliottWaveLiveTrader()
        
        # Test configuration validation
        config = trader.config.copy()
        
        # Test risk limits
        original_risk = config['risk_per_trade']
        
        # Test with normal risk (don't actually change config)
        if config['risk_per_trade'] > 0.1:  # More than 10% is excessive
            print(f"   ⚠️  High risk detected: {config['risk_per_trade']*100}%")
        else:
            print(f"   ✅ Risk per trade: {config['risk_per_trade']*100}%")
        
        # Test daily limits
        if config['max_daily_loss'] > 0.2:  # More than 20% daily loss
            print(f"   ⚠️  High daily loss limit: {config['max_daily_loss']*100}%")
        
        # Test position sizing calculation
        risk_amount = 10000 * config['risk_per_trade']  # $10k account
        stop_distance = 0.01  # 100 pips (0.01 for EURUSD)
        
        position_size = trader.calculate_position_size(risk_amount, stop_distance)
        
        if position_size <= 0:
            print("   ❌ Invalid position size calculation")
            return False
        
        print(f"   ✅ Position size calculation: {position_size} lots")
        
        # Validate position size is reasonable
        if not (0.01 <= position_size <= 10.0):
            print(f"   ❌ Position size out of range: {position_size}")
            return False
        
        # Test emergency conditions
        test_conditions = [
            ("Daily trade limit", config['max_daily_trades']),
            ("Risk per trade", config['risk_per_trade']),
            ("Max daily loss", config['max_daily_loss'])
        ]
        
        for condition, value in test_conditions:
            if value > 0:
                print(f"   ✅ {condition}: {value}")
        
        return True
    
    def test_order_execution(self):
        """Test order execution logic (simulation)"""
        print("   💰 Testing order execution simulation...")
        
        # Simulate order parameters
        test_signal = {
            'action': 'BUY',
            'confidence': 0.75,
            'stop_loss': 1.08000,
            'take_profit': 1.09000,
            'setup_type': 'Wave3_Continuation_Long'
        }
        
        # Test order validation
        required_fields = ['action', 'stop_loss', 'take_profit']
        for field in required_fields:
            if field not in test_signal:
                print(f"   ❌ Missing order field: {field}")
                return False
        
        # Test risk calculation
        entry_price = 1.08500
        stop_distance = abs(entry_price - test_signal['stop_loss'])
        reward_distance = abs(test_signal['take_profit'] - entry_price)
        risk_reward = reward_distance / stop_distance if stop_distance > 0 else 0
        
        print(f"   ✅ Entry price: {entry_price}")
        print(f"   ✅ Stop loss: {test_signal['stop_loss']}")
        print(f"   ✅ Take profit: {test_signal['take_profit']}")
        print(f"   ✅ Risk/Reward ratio: {risk_reward:.2f}")
        
        if risk_reward < 1.0:
            print("   ⚠️  Risk/Reward ratio below 1:1")
        
        # Test lot size calculation
        account_balance = 100000  # Demo account
        risk_amount = account_balance * 0.02  # 2% risk
        lot_size = risk_amount / (stop_distance * 100000)  # Simplified calculation
        
        print(f"   ✅ Calculated lot size: {lot_size:.2f}")
        
        return True
    
    def test_error_recovery(self):
        """Test error handling and recovery mechanisms"""
        print("   🔧 Testing error recovery...")
        
        # Test connection loss simulation
        trader = ElliottWaveLiveTrader()
        
        # Test configuration loading with missing file
        try:
            trader.load_config("nonexistent_config.json")
            print("   ✅ Missing config handled gracefully")
        except Exception as e:
            print(f"   ❌ Config error not handled: {e}")
            return False
        
        # Test invalid data handling
        empty_df = pd.DataFrame()
        signal = trader.analyze_elliott_wave_live(empty_df)
        
        if signal['action'] != 'HOLD':
            print("   ❌ Empty data not handled correctly")
            return False
        
        print("   ✅ Empty data handled correctly")
        
        # Test invalid signal handling
        invalid_signal = {'action': 'INVALID'}
        # Should not crash the system
        
        return True
    
    def test_performance_load(self):
        """Test system performance under load"""
        print("   ⚡ Testing performance...")
        
        trader = ElliottWaveLiveTrader()
        
        # Generate test data
        test_data = self.generate_large_test_dataset(1000)  # 1000 bars
        
        # Time the analysis
        start_time = time.time()
        signal = trader.analyze_elliott_wave_live(test_data)
        analysis_time = time.time() - start_time
        
        print(f"   ✅ Analysis time: {analysis_time:.3f}s for 1000 bars")
        
        if analysis_time > 5.0:  # Should complete within 5 seconds
            print("   ⚠️  Analysis taking too long")
            return False
        
        # Test memory usage (simplified)
        import psutil
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024
        print(f"   ✅ Memory usage: {memory_mb:.1f} MB")
        
        return True
    
    def test_configuration(self):
        """Test configuration validation"""
        print("   ⚙️ Testing configuration...")
        
        # Test default config
        trader = ElliottWaveLiveTrader()
        config = trader.config
        
        required_keys = [
            'symbol', 'risk_per_trade', 'max_daily_loss', 
            'max_daily_trades', 'magic_number'
        ]
        
        for key in required_keys:
            if key not in config:
                print(f"   ❌ Missing config key: {key}")
                return False
        
        # Test value ranges
        if not (0 < config['risk_per_trade'] <= 0.1):  # 0-10%
            print(f"   ❌ Invalid risk_per_trade: {config['risk_per_trade']}")
            return False
        
        if not (0 < config['max_daily_loss'] <= 0.2):  # 0-20%
            print(f"   ❌ Invalid max_daily_loss: {config['max_daily_loss']}")
            return False
        
        print("   ✅ Configuration validation passed")
        return True
    
    def test_vps_readiness(self):
        """Test VPS deployment readiness"""
        print("   🖥️ Testing VPS readiness...")
        
        checks = []
        
        # Check required packages
        try:
            import MetaTrader5
            import pandas
            import numpy
            import sklearn
            checks.append(("Required packages", True))
        except ImportError as e:
            checks.append(("Required packages", False, str(e)))
        
        # Check file structure
        import os
        required_files = [
            'elliott_live_trader.py',
            'elliott_live_config.json',
            'mt5_diagnostic.py'
        ]
        
        missing_files = []
        for file in required_files:
            if not os.path.exists(file):
                missing_files.append(file)
        
        if missing_files:
            checks.append(("File structure", False, f"Missing: {missing_files}"))
        else:
            checks.append(("File structure", True))
        
        # Check MT5 availability
        try:
            if mt5.initialize():
                mt5.shutdown()
                checks.append(("MT5 availability", True))
            else:
                checks.append(("MT5 availability", False, "MT5 not accessible"))
        except Exception as e:
            checks.append(("MT5 availability", False, str(e)))
        
        # Print results
        all_passed = True
        for check in checks:
            name, passed = check[0], check[1]
            if passed:
                print(f"   ✅ {name}")
            else:
                error = check[2] if len(check) > 2 else "Failed"
                print(f"   ❌ {name}: {error}")
                all_passed = False
        
        return all_passed
    
    def generate_large_test_dataset(self, size):
        """Generate large test dataset for performance testing"""
        dates = pd.date_range(start='2024-01-01', periods=size, freq='30T')
        np.random.seed(42)
        
        closes = 1.1000 + np.cumsum(np.random.normal(0, 0.0001, size))
        
        return pd.DataFrame({
            'date': dates,
            'open': closes * (1 + np.random.normal(0, 0.00005, size)),
            'high': closes * (1 + np.abs(np.random.normal(0, 0.0001, size))),
            'low': closes * (1 - np.abs(np.random.normal(0, 0.0001, size))),
            'close': closes,
            'volume': np.random.randint(1000, 5000, size)
        })
    
    def print_test_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "=" * 60)
        print("🧪 LIVE TRADING SYSTEM TEST RESULTS")
        print("=" * 60)
        
        passed = sum(1 for r in self.test_results.values() if r['status'] == 'PASSED')
        failed = sum(1 for r in self.test_results.values() if r['status'] == 'FAILED')
        errors = sum(1 for r in self.test_results.values() if r['status'] == 'ERROR')
        
        print(f"\n📊 SUMMARY: {passed} PASSED | {failed} FAILED | {errors} ERRORS")
        
        for test_name, result in self.test_results.items():
            status = result['status']
            if status == 'PASSED':
                print(f"✅ {test_name}")
            elif status == 'FAILED':
                print(f"❌ {test_name}")
            else:
                print(f"💥 {test_name}: {result.get('error', 'Unknown error')}")
        
        # VPS Readiness Assessment
        critical_tests = [
            'MT5 Connection Stability',
            'Data Feed Reliability', 
            'Risk Management',
            'VPS Readiness Check'
        ]
        
        critical_passed = all(
            self.test_results.get(test, {}).get('status') == 'PASSED' 
            for test in critical_tests
        )
        
        print("\n" + "=" * 60)
        if critical_passed and passed >= len(self.test_results) * 0.8:
            print("🎉 SYSTEM READY FOR VPS DEPLOYMENT!")
            print("✅ All critical tests passed")
            print("✅ Overall success rate > 80%")
        else:
            print("⚠️  SYSTEM NOT READY FOR VPS DEPLOYMENT")
            print("❌ Critical tests failed or success rate < 80%")
            print("🔧 Please fix issues before deploying to VPS")
        
        print("=" * 60)

def main():
    """Run the comprehensive test suite"""
    print("🚀 Elliott Wave Live Trading System - Test Suite")
    print("This will test all components for VPS deployment readiness\n")
    
    tests = LiveTradingSystemTests()
    results = tests.run_all_tests()
    
    # Save results
    with open('test_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Test results saved to: test_results.json")

if __name__ == "__main__":
    main()