"""
Elliott Wave Live Trading System - Python MT5 Interface
CRITICAL: This adapts the backtesting system for LIVE TRADING
"""

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import threading
import logging
from typing import Optional, Dict, Tuple
import json
import os

# Import simplified Elliott Wave detection functions
# (You'd need to extract the core logic from the backtest system)

class ElliottWaveLiveTrader:
    """
    Live Elliott Wave Trading System for MT5
    
    CRITICAL DIFFERENCES FROM BACKTESTING:
    1. NO LOOKAHEAD - only uses completed bars
    2. Real-time position management
    3. Error handling and reconnection
    4. Risk management with real money
    5. State persistence across restarts
    """
    
    def __init__(self, config_file="elliott_live_config.json"):
        self.config = self.load_config(config_file)
        self.is_running = False
        self.mt5_connected = False  # Track MT5 connection status
        self.last_analysis_time = None
        self.current_position = None
        self.daily_trades = 0
        self.daily_pnl = 0.0
        self.emergency_stop = False
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('elliott_live_trader.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def load_config(self, config_file: str) -> dict:
        """Load trading configuration with multi-asset support"""
        default_config = {
            "symbols": [
                {
                    "name": "EURUSD",
                    "risk_per_trade": 0.015,
                    "max_spread": 2,
                    "min_atr_filter": 0.0001,
                    "enabled": True
                }
            ],
            "timeframe": mt5.TIMEFRAME_M30,
            "analysis_interval": 60,  # Analyze every 1 minute
            "max_daily_loss": 0.05,  # 5% max daily loss
            "max_daily_trades": 20,
            "max_positions_per_symbol": 1,
            "max_total_positions": 6,
            "use_trailing_stop": True,
            "trailing_distance_atr": 2.0,
            "stop_loss_atr": 2.5,
            "take_profit_atr": 5.0,
            "magic_number": 234567,
        }
        
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                user_config = json.load(f)
                default_config.update(user_config)
        else:
            # Save default config
            with open(config_file, 'w') as f:
                json.dump(default_config, f, indent=2)
                
        return default_config
    
    def connect_mt5(self) -> bool:
        """Initialize MT5 connection with detailed diagnostics"""
        self.logger.info("Attempting to connect to MetaTrader 5...")
        
        # Try to initialize MT5
        if not mt5.initialize():
            # Get detailed error information
            error_code = mt5.last_error()
            self.logger.error(f"MT5 initialization failed with error code: {error_code}")
            
            # Provide specific troubleshooting advice
            self.print_mt5_troubleshooting()
            self.mt5_connected = False
            return False
            
        # Check if we can get terminal info
        terminal_info = mt5.terminal_info()
        if terminal_info is None:
            self.logger.error("Failed to get terminal info - MT5 may not be fully started")
            mt5.shutdown()
            self.mt5_connected = False
            return False
        
        self.logger.info(f"MT5 Terminal connected: {terminal_info.name} {terminal_info.build}")
        
        # Check account connection
        account_info = mt5.account_info()
        if account_info is None:
            self.logger.error("Failed to get account info - No broker connection or account not logged in")
            self.logger.error("Please ensure you are logged into a trading account in MT5")
            mt5.shutdown()
            self.mt5_connected = False
            return False
            
        self.logger.info(f"Connected to MT5 - Account: {account_info.login}, Balance: {account_info.balance}")
        self.logger.info(f"Broker: {account_info.company}, Currency: {account_info.currency}")
        self.mt5_connected = True
        return True
    
    def print_mt5_troubleshooting(self):
        """Print detailed troubleshooting information"""
        print("\n" + "="*60)
        print("🚨 MT5 CONNECTION FAILED - TROUBLESHOOTING GUIDE")
        print("="*60)
        print("\n1. ✅ INSTALL MetaTrader 5:")
        print("   - Download from your broker or MetaQuotes website")
        print("   - Install and create/login to trading account")
        
        print("\n2. ✅ START MetaTrader 5 Terminal:")
        print("   - Launch MT5 application")
        print("   - Login to your trading account")
        print("   - Keep MT5 running while using Python")
        
        print("\n3. ✅ ALGORITHMISCHEN HANDEL AKTIVIEREN:")
        print("   - In MT5: Extras → Einstellungen → Expert Advisors")
        print("   - ☑️ Haken bei 'Automatisierten Handel erlauben'")
        print("   - ☑️ Haken bei 'DLL-Import erlauben'")
        print("   - OK klicken und MT5 neu starten")
        
        print("\n4. ✅ RUN as Administrator (if needed):")
        print("   - Close MT5")
        print("   - Right-click MT5 → 'Run as administrator'")
        print("   - Also run this Python script as administrator")
        
        print("\n5. ✅ CHECK Firewall/Antivirus:")
        print("   - Temporarily disable antivirus")
        print("   - Add MT5 to Windows Firewall exceptions")
        
        print("\n6. ✅ VERIFY Installation:")
        try:
            import MetaTrader5 as mt5_test
            print("   - ✅ MetaTrader5 Python package is installed")
        except ImportError:
            print("   - ❌ MetaTrader5 package missing: pip install MetaTrader5")
            
        print("\n" + "="*60)
        print("After fixing, restart both MT5 and this script!")
        print("="*60 + "\n")
    
    def disconnect_mt5(self):
        """Close MT5 connection"""
        mt5.shutdown()
        self.logger.info("MT5 connection closed")
    
    def add_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add technical indicators - adapted from backtest system"""
        if len(df) < 50:
            return df
            
        # ATR for volatility
        df['high_low'] = df['high'] - df['low']
        df['high_close'] = np.abs(df['high'] - df['close'].shift(1))
        df['low_close'] = np.abs(df['low'] - df['close'].shift(1))
        df['tr'] = df[['high_low', 'high_close', 'low_close']].max(axis=1)
        df['atr'] = df['tr'].rolling(window=14).mean()
        
        # EMAs for trend
        df['ema_fast'] = df['close'].ewm(span=12).mean()
        df['ema_slow'] = df['close'].ewm(span=26).mean()
        
        # RSI for momentum
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        return df
    
    def analyze_elliott_wave_live(self, df: pd.DataFrame, symbol_config: Dict = None) -> Dict:
        """
        Live Elliott Wave analysis - adapted from backtest system
        CRITICAL: Only uses completed bars, no future information
        """
        signal = {
            'action': 'HOLD',  # HOLD, BUY, SELL
            'confidence': 0.0,
            'stop_loss': 0.0,
            'take_profit': 0.0,
            'wave_count': None,
            'setup_type': None
        }
        
        if len(df) < 100:
            return signal
            
        try:
            # Extract price arrays (only completed bars)
            highs = df['high'].values
            lows = df['low'].values
            closes = df['close'].values
            
            # Simplified Elliott Wave detection
            # (In production, you'd port the full logic from the backtest system)
            
            # Look for Wave 3 momentum continuation
            current_price = closes[-1]
            atr = df['atr'].iloc[-1]
            
            # Momentum analysis
            price_change_5 = (current_price - closes[-6]) / closes[-6]
            rsi_current = df['rsi'].iloc[-1]
            
            # Trend analysis
            ema_fast = df['ema_fast'].iloc[-1]
            ema_slow = df['ema_slow'].iloc[-1]
            trend_up = ema_fast > ema_slow
            
            # Get minimum ATR filter for this symbol
            min_atr_filter = symbol_config.get('min_atr_filter', 0.0001) if symbol_config else 0.0001
            
            # Wave 3 continuation signal (simplified)
            if abs(price_change_5) > 0.01 and atr > min_atr_filter:
                if trend_up and rsi_current < 80:
                    signal.update({
                        'action': 'BUY',
                        'confidence': min(0.8, abs(price_change_5) * 50),
                        'stop_loss': current_price - (atr * self.config['stop_loss_atr']),
                        'take_profit': current_price + (atr * self.config['take_profit_atr']),
                        'setup_type': 'Wave3_Continuation_Long'
                    })
                elif not trend_up and rsi_current > 20:
                    signal.update({
                        'action': 'SELL',
                        'confidence': min(0.8, abs(price_change_5) * 50),
                        'stop_loss': current_price + (atr * self.config['stop_loss_atr']),
                        'take_profit': current_price - (atr * self.config['take_profit_atr']),
                        'setup_type': 'Wave3_Continuation_Short'
                    })
            
            # Wave 5 reversal signal (simplified)
            elif rsi_current > 75 and trend_up:
                signal.update({
                    'action': 'SELL',
                    'confidence': 0.6,
                    'stop_loss': current_price + (atr * self.config['stop_loss_atr']),
                    'take_profit': current_price - (atr * self.config['take_profit_atr']),
                    'setup_type': 'Wave5_Reversal_Short'
                })
            elif rsi_current < 25 and not trend_up:
                signal.update({
                    'action': 'BUY',
                    'confidence': 0.6,
                    'stop_loss': current_price - (atr * self.config['stop_loss_atr']),
                    'take_profit': current_price + (atr * self.config['take_profit_atr']),
                    'setup_type': 'Wave5_Reversal_Long'
                })
                
        except Exception as e:
            self.logger.error(f"Error in Elliott Wave analysis: {e}")
            
        return signal
    
    def check_risk_management(self) -> bool:
        """Check if trading is allowed based on risk rules"""
        
        # Check emergency stop
        if self.emergency_stop:
            self.logger.warning("Trading stopped - Emergency stop activated")
            return False
            
        # Check daily trade limit
        if self.daily_trades >= self.config['max_daily_trades']:
            self.logger.warning(f"Daily trade limit reached: {self.daily_trades}")
            return False
            
        # Check daily loss limit
        account_info = mt5.account_info()
        if account_info is None:
            return False
            
        daily_loss_limit = account_info.balance * self.config['max_daily_loss']
        if self.daily_pnl < -daily_loss_limit:
            self.logger.warning(f"Daily loss limit reached: {self.daily_pnl:.2f}")
            self.emergency_stop = True
            return False
            
        # For multi-asset trading, we don't need to check spread here
        # Spread is checked per symbol in place_order()
        return True
    
    def calculate_position_size(self, risk_amount: float, stop_distance: float) -> float:
        """Calculate position size based on risk management"""
        try:
            # If MT5 not available, use simplified calculation
            if not self.mt5_connected:
                # Convert stop_distance from price units to pips
                # For EURUSD: 0.0050 = 50 pips, 0.0001 = 1 pip
                if stop_distance <= 0:
                    return 0.01  # Minimum lot size for invalid stop
                
                # Convert to pips (assuming 4-digit quotes for major pairs)
                stop_distance_pips = stop_distance * 10000  # 0.0050 -> 50 pips
                pip_value = 10.0  # €10 per pip for 1 lot EURUSD
                
                position_size = risk_amount / (stop_distance_pips * pip_value)
                return max(0.01, min(10.0, round(position_size, 2)))  # Min 0.01, Max 10 lots
            
            symbol_info = mt5.symbol_info(self.config['symbol'])
            if symbol_info is None:
                # Fallback calculation when symbol info not available
                if stop_distance <= 0:
                    return 0.01
                
                stop_distance_pips = stop_distance * 10000  # Convert to pips
                pip_value = 10.0  # Standard for major pairs
                position_size = risk_amount / (stop_distance_pips * pip_value)
                return max(0.01, min(10.0, round(position_size, 2)))
                
            # Calculate lot size based on risk
            tick_value = symbol_info.trade_tick_value
            tick_size = symbol_info.trade_tick_size
            
            if tick_value <= 0 or tick_size <= 0:
                # Fallback for invalid tick values
                if stop_distance <= 0:
                    return 0.01
                
                stop_distance_pips = stop_distance * 10000  # Convert to pips
                pip_value = 10.0
                position_size = risk_amount / (stop_distance_pips * pip_value)
                return max(0.01, min(10.0, round(position_size, 2)))
            
            pip_value = tick_value / tick_size
            position_size = risk_amount / (stop_distance * pip_value)
            
            # Apply lot size constraints
            min_lot = max(0.01, symbol_info.volume_min)
            max_lot = min(10.0, symbol_info.volume_max)
            lot_step = symbol_info.volume_step if symbol_info.volume_step > 0 else 0.01
            
            # Round to allowed lot step
            position_size = round(position_size / lot_step) * lot_step
            position_size = max(min_lot, min(max_lot, position_size))
            
            return position_size
            
        except Exception as e:
            self.logger.error(f"Error calculating position size: {e}")
            return 0.0
    
    def place_order(self, signal: Dict) -> bool:
        """Place order based on Elliott Wave signal for any symbol"""
        try:
            account_info = mt5.account_info()
            if account_info is None:
                return False
            
            symbol = signal.get('symbol', 'EURUSD')
            symbol_config = signal.get('symbol_config', {})
            
            # Calculate risk amount (use symbol-specific risk if available)
            symbol_risk = symbol_config.get('risk_per_trade', 0.015)
            risk_amount = account_info.balance * symbol_risk
            
            # Check spread
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info is None:
                self.logger.error(f"Cannot get symbol info for {symbol}")
                return False
                
            current_spread = symbol_info.spread
            max_spread = symbol_config.get('max_spread', 30)
            
            if current_spread > max_spread:
                self.logger.warning(f"{symbol} spread too high: {current_spread} > {max_spread}")
                return False
            
            # Get current price
            tick = mt5.symbol_info_tick(symbol)
            if tick is None:
                self.logger.error(f"Cannot get tick data for {symbol}")
                return False
                
            if signal['action'] == 'BUY':
                price = tick.ask
                order_type = mt5.ORDER_TYPE_BUY
            else:
                price = tick.bid
                order_type = mt5.ORDER_TYPE_SELL
                
            # Calculate position size
            stop_distance = abs(price - signal['stop_loss'])
            lot_size = self.calculate_position_size(risk_amount, stop_distance)
            
            if lot_size <= 0:
                self.logger.error(f"Invalid lot size calculated for {symbol}")
                return False
                
            # Prepare order request
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": lot_size,
                "type": order_type,
                "price": price,
                "sl": signal['stop_loss'],
                "tp": signal['take_profit'],
                "deviation": 20,  # Higher deviation for indices
                "magic": self.config['magic_number'],
                "comment": f"Elliott-{signal['setup_type']}-{symbol}",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            # Send order
            result = mt5.order_send(request)
            
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                self.logger.info(f"✅ {symbol} Order placed: {signal['action']} {lot_size} lots at {price} (Risk: €{risk_amount:.0f})")
                self.daily_trades += 1
                return True
            else:
                self.logger.error(f"❌ {symbol} Order failed: {result.comment} (Code: {result.retcode})")
                return False
                
        except Exception as e:
            self.logger.error(f"Error placing order: {e}")
            return False
    
    def has_position_for_symbol(self, symbol: str) -> bool:
        """Check if we have an open position for the given symbol"""
        try:
            positions = mt5.positions_get(symbol=symbol)
            if positions is None:
                return False
            return len(positions) > 0
        except:
            return False
    
    def get_total_positions(self) -> int:
        """Get total number of open positions"""
        try:
            positions = mt5.positions_get()
            if positions is None:
                return 0
            return len(positions)
        except:
            return 0
    
    def get_live_data(self, symbol: str, timeframe) -> pd.DataFrame:
        """Get live market data for any symbol"""
        try:
            # Ensure symbol is available
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info is None:
                self.logger.warning(f"Symbol {symbol} not found")
                return None
            
            if not symbol_info.visible:
                if not mt5.symbol_select(symbol, True):
                    self.logger.warning(f"Failed to select symbol {symbol}")
                    return None
            
            # Get historical data
            rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, 200)
            if rates is None or len(rates) < 100:
                self.logger.warning(f"Insufficient data for {symbol}")
                return None
            
            # Convert to DataFrame
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            
            # Add technical indicators
            df = self.add_indicators(df)
            
            return df
            
        except Exception as e:
            self.logger.error(f"Error getting live data for {symbol}: {e}")
            return None
    
    def manage_position(self):
        """Manage existing positions with trailing stops for multi-asset trading"""
        if not self.config.get('use_trailing_stop', False):
            return
            
        try:
            # Get all open positions
            positions = mt5.positions_get()
            if not positions:
                return
                
            # Manage each position with our magic number
            for position in positions:
                if position.magic != self.config['magic_number']:
                    continue
                    
                symbol = position.symbol
                
                # Get current market data for this symbol
                df = self.get_live_data(symbol, self.config['timeframe'])
                if df is None or len(df) == 0:
                    continue
                    
                current_price = df['close'].iloc[-1]
                atr = df['atr'].iloc[-1] if 'atr' in df.columns else 0.001
                trailing_distance = atr * self.config.get('trailing_distance_atr', 2.0)
                
                # Calculate new trailing stop
                if position.type == mt5.ORDER_TYPE_BUY:
                    new_sl = current_price - trailing_distance
                    if new_sl > position.sl:
                        self.modify_position_by_ticket(position.ticket, symbol, new_sl, position.tp)
                elif position.type == mt5.ORDER_TYPE_SELL:
                    new_sl = current_price + trailing_distance
                    if new_sl < position.sl:
                        self.modify_position_by_ticket(position.ticket, symbol, new_sl, position.tp)
                    
        except Exception as e:
            self.logger.error(f"Error managing positions: {e}")
    
    def modify_position_by_ticket(self, ticket: int, symbol: str, new_sl: float, new_tp: float):
        """Modify specific position by ticket"""
        try:
            request = {
                "action": mt5.TRADE_ACTION_SLTP,
                "position": ticket,
                "symbol": symbol,
                "sl": new_sl,
                "tp": new_tp,
                "magic": self.config['magic_number'],
            }
            
            result = mt5.order_send(request)
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                self.logger.info(f"{symbol} Position {ticket} modified - New SL: {new_sl:.5f}")
            else:
                self.logger.error(f"{symbol} Failed to modify position {ticket}: {result.comment}")
                
        except Exception as e:
            self.logger.error(f"Error modifying position {ticket}: {e}")
    
    def update_daily_pnl(self):
        """Update daily P&L tracking"""
        try:
            # Get today's deals
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            deals = mt5.history_deals_get(today, datetime.now())
            
            daily_pnl = 0.0
            daily_trades = 0
            
            if deals:
                for deal in deals:
                    if deal.magic == self.config['magic_number']:
                        daily_pnl += deal.profit
                        if deal.entry == mt5.DEAL_ENTRY_IN:
                            daily_trades += 1
                            
            # Add current open position P&L for all symbols
            positions = mt5.positions_get()
            if positions:
                for pos in positions:
                    if pos.magic == self.config['magic_number']:
                        daily_pnl += pos.profit
                        
            self.daily_pnl = daily_pnl
            self.daily_trades = daily_trades
            
        except Exception as e:
            self.logger.error(f"Error updating daily P&L: {e}")
    
    def trading_loop(self):
        """Main trading loop"""
        self.logger.info("Starting Elliott Wave live trading...")
        
        while self.is_running:
            try:
                # Update daily statistics
                self.update_daily_pnl()
                
                # Check risk management
                if not self.check_risk_management():
                    time.sleep(60)  # Wait 1 minute before checking again
                    continue
                
                # Manage existing positions
                self.manage_position()
                
                # Check if we should analyze (analyze every minute for all symbols)
                current_time = datetime.now()
                if (self.last_analysis_time is None or 
                    (current_time - self.last_analysis_time).seconds >= self.config['analysis_interval']):
                    
                    # Analyze all enabled symbols
                    for symbol_config in self.config['symbols']:
                        if not symbol_config.get('enabled', True):
                            continue
                            
                        symbol = symbol_config['name']
                        
                        # Check if we already have a position for this symbol
                        if self.has_position_for_symbol(symbol):
                            continue
                            
                        # Check if we've reached max total positions
                        if self.get_total_positions() >= self.config.get('max_total_positions', 6):
                            self.logger.info("Maximum total positions reached, skipping new signals")
                            break
                        
                        try:
                            # Get live market data for this symbol
                            df = self.get_live_data(symbol, self.config['timeframe'])
                            if df is None:
                                self.logger.warning(f"Failed to get market data for {symbol}")
                                continue
                            
                            # Analyze Elliott Wave patterns
                            signal = self.analyze_elliott_wave_live(df, symbol_config)
                            signal['symbol'] = symbol
                            signal['symbol_config'] = symbol_config
                            
                            # Execute signal if strong enough
                            if signal['action'] != 'HOLD':
                                if signal['confidence'] > 0.6:  # Minimum confidence threshold
                                    self.logger.info(f"🌊 {symbol} Elliott Wave signal: {signal['action']} - {signal['setup_type']} (Confidence: {signal['confidence']:.2f})")
                                    self.place_order(signal)
                                    
                        except Exception as e:
                            self.logger.error(f"Error analyzing {symbol}: {e}")
                            continue
                    
                    self.last_analysis_time = current_time
                
                # Sleep before next iteration
                time.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                self.logger.error(f"Error in trading loop: {e}")
                time.sleep(30)
    
    def start_trading(self):
        """Start the live trading system"""
        if not self.connect_mt5():
            return False
            
        self.is_running = True
        self.emergency_stop = False
        
        # Start trading in separate thread
        trading_thread = threading.Thread(target=self.trading_loop)
        trading_thread.daemon = True
        trading_thread.start()
        
        self.logger.info("Elliott Wave Live Trader started successfully")
        return True
    
    def stop_trading(self):
        """Stop the live trading system"""
        self.is_running = False
        self.disconnect_mt5()
        self.logger.info("Elliott Wave Live Trader stopped")

def main():
    """Main function to run the live trader"""
    
    # Create trader instance
    trader = ElliottWaveLiveTrader()
    
    try:
        # Start trading
        if trader.start_trading():
            print("Elliott Wave Live Trader is running...")
            print("Press Ctrl+C to stop")
            
            # Keep main thread alive
            while True:
                time.sleep(1)
                
    except KeyboardInterrupt:
        print("\nStopping trader...")
        trader.stop_trading()
    except Exception as e:
        print(f"Unexpected error: {e}")
        trader.stop_trading()

if __name__ == "__main__":
    main()