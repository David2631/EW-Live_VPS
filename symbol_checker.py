#!/usr/bin/env python3
"""
MT5 Symbol Availability Checker
Prüft welche Symbole verfügbar sind und erweitert Market Watch automatisch
"""

import MetaTrader5 as mt5
import logging
from typing import List, Dict

def check_symbol_availability(symbols: List[str]) -> Dict[str, dict]:
    """
    Check symbol availability and add to Market Watch if needed
    
    Returns:
        Dict with symbol status and info
    """
    if not mt5.initialize():
        logging.error("MT5 initialization failed")
        return {}
    
    results = {}
    
    for symbol in symbols:
        symbol = symbol.strip()
        if not symbol or symbol.startswith('#'):
            continue
            
        print(f"🔍 Checking {symbol}...")
        
        # Check if symbol exists
        symbol_info = mt5.symbol_info(symbol)
        
        if symbol_info is None:
            # Try alternative symbol formats
            alternatives = [
                symbol,
                symbol + ".raw",
                symbol + "-",
                symbol.replace(".", ""),
            ]
            
            for alt in alternatives:
                symbol_info = mt5.symbol_info(alt)
                if symbol_info:
                    print(f"  ✅ Found alternative: {alt}")
                    symbol = alt
                    break
        
        if symbol_info is None:
            print(f"  ❌ {symbol} - NOT AVAILABLE")
            results[symbol] = {
                'available': False,
                'error': 'Symbol not found'
            }
            continue
        
        # Check if symbol is visible in Market Watch
        if not symbol_info.visible:
            print(f"  📋 Adding {symbol} to Market Watch...")
            if mt5.symbol_select(symbol, True):
                print(f"  ✅ {symbol} added to Market Watch")
            else:
                print(f"  ⚠️ Failed to add {symbol} to Market Watch")
        
        # Get current tick to verify data
        tick = mt5.symbol_info_tick(symbol)
        
        if tick is None:
            print(f"  ⚠️ {symbol} - No price data")
            results[symbol] = {
                'available': True,
                'has_data': False,
                'info': symbol_info._asdict()
            }
        else:
            print(f"  ✅ {symbol} - Bid: {tick.bid}, Ask: {tick.ask}")
            results[symbol] = {
                'available': True,
                'has_data': True,
                'info': symbol_info._asdict(),
                'current_price': {
                    'bid': tick.bid,
                    'ask': tick.ask,
                    'time': tick.time
                }
            }
    
    mt5.shutdown()
    return results

def update_market_data_manager():
    """Update MarketDataManager to handle symbol availability"""
    
    class SymbolManager:
        """Enhanced symbol management with auto-discovery"""
        
        def __init__(self):
            self.available_symbols = {}
            self.symbol_cache = {}
        
        def validate_and_prepare_symbols(self, symbol_list: List[str]) -> List[str]:
            """Validate symbols and prepare Market Watch"""
            
            print("🔍 Validating symbols and preparing Market Watch...")
            
            valid_symbols = []
            results = check_symbol_availability(symbol_list)
            
            for symbol, data in results.items():
                if data['available'] and data.get('has_data', False):
                    valid_symbols.append(symbol)
                    print(f"✅ {symbol} - Ready for trading")
                else:
                    print(f"❌ {symbol} - Skipped (not available or no data)")
            
            print(f"\n📊 Summary: {len(valid_symbols)}/{len(symbol_list)} symbols ready")
            return valid_symbols
        
        def get_alternative_symbols(self, symbol: str) -> List[str]:
            """Get alternative symbol names to try"""
            
            alternatives = [
                symbol,
                symbol + ".raw",
                symbol + ".",
                symbol.replace(".", ""),
                symbol.replace("-", ""),
            ]
            
            # Forex specific alternatives
            if len(symbol) == 6 and symbol.isalpha():
                alternatives.extend([
                    symbol + "m",
                    symbol + ".m",
                    symbol.lower(),
                    symbol.upper()
                ])
            
            # Index alternatives
            if symbol.startswith("US"):
                alternatives.extend([
                    symbol.replace("US", "US100"),
                    symbol.replace("US", "NAS100"),
                    symbol + ".cash",
                    symbol + ".f"
                ])
            
            return list(set(alternatives))

def main():
    """Test symbol availability"""
    
    print("🚀 MT5 Symbol Availability Checker")
    print("=" * 50)
    
    # Test with different symbol lists
    symbol_files = [
        'symbols_simple.txt',
        'symbols_demo.txt', 
        'symbols.txt'
    ]
    
    for file_name in symbol_files:
        try:
            print(f"\n📋 Testing {file_name}...")
            
            with open(file_name, 'r') as f:
                symbols = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            
            results = check_symbol_availability(symbols)
            
            available = sum(1 for r in results.values() if r['available'] and r.get('has_data', False))
            total = len(results)
            
            print(f"📊 {file_name}: {available}/{total} symbols available with data")
            
        except FileNotFoundError:
            print(f"⚠️ {file_name} not found")
        except Exception as e:
            print(f"❌ Error testing {file_name}: {e}")

if __name__ == "__main__":
    main()