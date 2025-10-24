#!/usr/bin/env python3
"""
Test Isolated Market Data - EXOTIC vs CACHED Symbols
============================================

Test MT5 Caching Behavior:
- Major Forex (CACHED): EURUSD, GBPUSD
- German Stocks (EXOTIC): BMWG.DE, DAIGn.DE  
- Crypto (VERY EXOTIC): BTCUSD

Author: David Elliott Wave Trading System
"""

import time
import json
import sys
import os
from datetime import datetime

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from market_data_manager import MarketDataManager
    print("✅ Market Data Manager imported successfully")
except ImportError as e:
    print(f"❌ Error importing Market Data Manager: {e}")
    sys.exit(1)

class ExoticSymbolTester:
    def __init__(self):
        self.mdm = MarketDataManager()
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'test_type': 'EXOTIC_vs_CACHED_symbols',
            'symbols_tested': {},
            'summary': {}
        }
        
        # Symbol Categories for Testing
        self.symbol_categories = {
            'MAJOR_FOREX_CACHED': ['EURUSD', 'GBPUSD'],
            'GERMAN_STOCKS_EXOTIC': ['BMWG.DE', 'DAIGn.DE'],
            'CRYPTO_VERY_EXOTIC': ['BTCUSD']
        }
    
    def test_single_symbol(self, symbol, category):
        """Test single symbol with detailed timing"""
        print(f"\n🔍 Testing {symbol} ({category})")
        
        results = {
            'symbol': symbol,
            'category': category,
            'attempts': [],
            'avg_fetch_time': 0,
            'data_quality': 'UNKNOWN',
            'mt5_status': 'UNKNOWN'
        }
        
        # Test 3x for average
        fetch_times = []
        for attempt in range(3):
            print(f"  Attempt {attempt + 1}/3...")
            
            start_time = time.perf_counter()
            try:
                data = self.mdm.get_live_data(symbol, timeframe=16385, bars=50)  # M15 timeframe
                fetch_time = time.perf_counter() - start_time
                
                if data is not None and not data.empty:
                    fetch_times.append(fetch_time)
                    attempt_result = {
                        'attempt': attempt + 1,
                        'fetch_time_seconds': round(fetch_time, 6),
                        'data_points': len(data),
                        'success': True,
                        'latest_price': float(data['close'].iloc[-1]) if 'close' in data.columns else 'N/A'
                    }
                    print(f"    ✅ Success: {fetch_time:.6f}s | {len(data)} bars | Price: {attempt_result['latest_price']}")
                else:
                    attempt_result = {
                        'attempt': attempt + 1,
                        'fetch_time_seconds': round(fetch_time, 6),
                        'success': False,
                        'error': 'No data returned'
                    }
                    print(f"    ❌ Failed: {fetch_time:.6f}s | No data")
                    
            except Exception as e:
                fetch_time = time.perf_counter() - start_time
                attempt_result = {
                    'attempt': attempt + 1,
                    'fetch_time_seconds': round(fetch_time, 6),
                    'success': False,
                    'error': str(e)
                }
                print(f"    ❌ Error: {fetch_time:.6f}s | {str(e)}")
            
            results['attempts'].append(attempt_result)
            time.sleep(0.5)  # Small delay between attempts
        
        # Calculate averages
        if fetch_times:
            results['avg_fetch_time'] = round(sum(fetch_times) / len(fetch_times), 6)
            results['data_quality'] = 'GOOD'
            results['mt5_status'] = 'CONNECTED'
        else:
            results['avg_fetch_time'] = 0
            results['data_quality'] = 'FAILED'
            results['mt5_status'] = 'FAILED'
        
        return results
    
    def run_exotic_test(self):
        """Run complete exotic symbol test"""
        print("🚀 Starting EXOTIC vs CACHED Symbol Test")
        print("=" * 60)
        
        # Test MT5 Connection first
        if not self.mdm.connect():
            print("❌ MT5 Connection failed!")
            return False
        
        print(f"✅ MT5 Connected - Account: Connected successfully")
        print()
        
        # Test each category
        for category, symbols in self.symbol_categories.items():
            print(f"\n📊 Testing Category: {category}")
            print("-" * 40)
            
            category_results = []
            for symbol in symbols:
                result = self.test_single_symbol(symbol, category)
                category_results.append(result)
                self.results['symbols_tested'][symbol] = result
            
            # Category Summary
            successful_tests = [r for r in category_results if r['data_quality'] == 'GOOD']
            if successful_tests:
                avg_time = sum(r['avg_fetch_time'] for r in successful_tests) / len(successful_tests)
                print(f"\n📈 {category} Summary:")
                print(f"   Success Rate: {len(successful_tests)}/{len(symbols)}")
                print(f"   Average Fetch Time: {avg_time:.6f}s")
                
                self.results['summary'][category] = {
                    'success_rate': f"{len(successful_tests)}/{len(symbols)}",
                    'avg_fetch_time': round(avg_time, 6),
                    'symbols_count': len(symbols)
                }
        
        # Final Analysis
        self.print_final_analysis()
        self.save_results()
        
        return True
    
    def print_final_analysis(self):
        """Print final analysis comparing categories"""
        print("\n" + "=" * 60)
        print("🎯 FINAL ANALYSIS - MT5 Caching Behavior")
        print("=" * 60)
        
        if not self.results['summary']:
            print("❌ No successful tests to analyze")
            return
        
        # Sort by average fetch time
        sorted_categories = sorted(
            self.results['summary'].items(),
            key=lambda x: x[1]['avg_fetch_time']
        )
        
        print("\n📊 Categories by Speed (Fastest → Slowest):")
        for i, (category, data) in enumerate(sorted_categories, 1):
            speed_indicator = "🟢 CACHED" if data['avg_fetch_time'] < 0.01 else "🔴 SERVER FETCH"
            print(f"{i}. {category}: {data['avg_fetch_time']:.6f}s {speed_indicator}")
        
        # MT5 Caching Conclusion
        fastest_time = sorted_categories[0][1]['avg_fetch_time']
        slowest_time = sorted_categories[-1][1]['avg_fetch_time']
        
        print(f"\n🔍 MT5 Caching Analysis:")
        print(f"   Fastest Category: {fastest_time:.6f}s")
        print(f"   Slowest Category: {slowest_time:.6f}s")
        print(f"   Speed Difference: {(slowest_time/fastest_time):.1f}x slower")
        
        if slowest_time > fastest_time * 2:
            print("   ✅ MT5 Caching CONFIRMED - Clear speed difference detected")
        else:
            print("   ❓ MT5 Caching UNCLEAR - Similar speeds across categories")
    
    def save_results(self):
        """Save results to JSON file"""
        filename = f"exotic_symbol_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(os.path.dirname(__file__), filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, indent=2, ensure_ascii=False)
            print(f"\n💾 Results saved to: {filename}")
        except Exception as e:
            print(f"❌ Error saving results: {e}")

def main():
    """Main execution function"""
    print("🎯 Elliott Wave Exotic Symbol Tester")
    print("Testing MT5 Caching: Major Forex vs German Stocks vs Crypto")
    print("=" * 60)
    
    tester = ExoticSymbolTester()
    
    try:
        success = tester.run_exotic_test()
        if success:
            print("\n✅ Exotic Symbol Test completed successfully!")
        else:
            print("\n❌ Exotic Symbol Test failed!")
            return 1
            
    except KeyboardInterrupt:
        print("\n\n⚠️ Test interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return 1
    finally:
        # Cleanup
        try:
            tester.mdm.disconnect()
            print("🔌 MT5 Connection closed")
        except:
            pass
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    print(f"\nTest completed with exit code: {exit_code}")
    sys.exit(exit_code)