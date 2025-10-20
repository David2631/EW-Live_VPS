"""
Trade Executor - Professional MT5 Order Management
Handles order execution, position management, and monitoring
"""

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import Optional, Dict, List, Tuple
from enum import Enum
import logging
from datetime import datetime, timedelta
import time

from signal_generator import TradingSignal, SignalType
from risk_manager import PositionSize

class OrderType(Enum):
    """MT5 order types"""
    BUY = mt5.ORDER_TYPE_BUY
    SELL = mt5.ORDER_TYPE_SELL
    BUY_LIMIT = mt5.ORDER_TYPE_BUY_LIMIT
    SELL_LIMIT = mt5.ORDER_TYPE_SELL_LIMIT
    BUY_STOP = mt5.ORDER_TYPE_BUY_STOP
    SELL_STOP = mt5.ORDER_TYPE_SELL_STOP

class OrderStatus(Enum):
    """Order execution status"""
    PENDING = "PENDING"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"
    PARTIAL = "PARTIAL"

@dataclass
class ExecutionResult:
    """Order execution result"""
    success: bool
    order_id: Optional[int]
    position_id: Optional[int]
    price: Optional[float]
    volume: float
    error_code: int
    error_message: str
    execution_time: datetime
    slippage_pips: float = 0.0

@dataclass
class Position:
    """Active position tracking"""
    position_id: int
    symbol: str
    type: str  # 'buy' or 'sell'
    volume: float
    open_price: float
    current_price: float
    stop_loss: float
    take_profit: float
    swap: float
    profit: float
    comment: str
    open_time: datetime
    
    # Elliott Wave context
    wave_pattern: str
    signal_confidence: float
    
    def update_current_price(self, price: float):
        """Update current price and recalculate profit"""
        self.current_price = price
        if self.type == 'buy':
            self.profit = (price - self.open_price) * self.volume * 100000  # Simplified
        else:
            self.profit = (self.open_price - price) * self.volume * 100000

class TradeExecutor:
    """
    Professional trade execution engine
    Handles all MT5 order management and position tracking
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.mt5_connected = False
        self.active_positions = {}  # position_id -> Position
        self.pending_orders = {}    # order_id -> order_info
        
        # Execution settings
        self.max_slippage = 3.0     # Maximum slippage in pips
        self.retry_attempts = 3     # Number of retry attempts
        self.retry_delay = 1.0      # Delay between retries (seconds)
        
        # Magic number for Elliott Wave EA
        self.magic_number = 202501  # Elliott Wave 2025-01
    
    def connect(self) -> bool:
        """Connect to MT5 terminal"""
        try:
            if not mt5.initialize():
                error = mt5.last_error()
                self.logger.error(f"MT5 initialization failed: {error}")
                return False
            
            # Verify connection
            account_info = mt5.account_info()
            if account_info is None:
                self.logger.error("Failed to get account info")
                mt5.shutdown()
                return False
            
            self.mt5_connected = True
            self.logger.info(f"Trade Executor connected to account {account_info.login}")
            
            # Load existing positions
            self._load_existing_positions()
            
            return True
            
        except Exception as e:
            self.logger.error(f"MT5 connection error: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from MT5"""
        if self.mt5_connected:
            mt5.shutdown()
            self.mt5_connected = False
            self.logger.info("Trade Executor disconnected")
    
    def execute_signal(self, signal: TradingSignal, position_size: PositionSize) -> ExecutionResult:
        """
        Execute trading signal with proper risk management
        
        Args:
            signal: Trading signal from signal generator
            position_size: Position size from risk manager
        """
        try:
            if not self.mt5_connected:
                return ExecutionResult(
                    success=False, order_id=None, position_id=None, price=None,
                    volume=0, error_code=-1, error_message="MT5 not connected",
                    execution_time=datetime.now()
                )
            
            if not position_size.is_valid:
                return ExecutionResult(
                    success=False, order_id=None, position_id=None, price=None,
                    volume=0, error_code=-1, error_message=f"Invalid position size: {position_size.reason}",
                    execution_time=datetime.now()
                )
            
            # Prepare order request
            if signal.signal_type == SignalType.BUY:
                order_type = mt5.ORDER_TYPE_BUY
                price = signal.entry_price
            elif signal.signal_type == SignalType.SELL:
                order_type = mt5.ORDER_TYPE_SELL
                price = signal.entry_price
            else:
                return ExecutionResult(
                    success=False, order_id=None, position_id=None, price=None,
                    volume=0, error_code=-1, error_message=f"Unsupported signal type: {signal.signal_type}",
                    execution_time=datetime.now()
                )
            
            # Create order request
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": signal.symbol,
                "volume": position_size.lot_size,
                "type": order_type,
                "price": price,
                "sl": signal.stop_loss,
                "tp": signal.take_profit,
                "deviation": int(self.max_slippage),
                "magic": self.magic_number,
                "comment": f"EW_{signal.wave_pattern}_{signal.current_wave}",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            # Execute order with retries
            result = self._execute_order_with_retry(request)
            
            if result.success:
                # Track position
                position = self._create_position_record(signal, position_size, result)
                if position:
                    self.active_positions[position.position_id] = position
                    self.logger.info(f"✅ Position opened: {signal.symbol} {signal.signal_type.value} "
                                   f"{position_size.lot_size} lots at {result.price:.5f}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Order execution error: {e}")
            return ExecutionResult(
                success=False, order_id=None, position_id=None, price=None,
                volume=0, error_code=-1, error_message=f"Execution error: {e}",
                execution_time=datetime.now()
            )
    
    def _execute_order_with_retry(self, request: Dict) -> ExecutionResult:
        """Execute order with retry logic"""
        
        for attempt in range(self.retry_attempts):
            try:
                result = mt5.order_send(request)
                
                if result is None:
                    error = mt5.last_error()
                    self.logger.warning(f"Order attempt {attempt + 1} failed: {error}")
                    if attempt < self.retry_attempts - 1:
                        time.sleep(self.retry_delay)
                        continue
                    return ExecutionResult(
                        success=False, order_id=None, position_id=None, price=None,
                        volume=request['volume'], error_code=error[0] if error else -1,
                        error_message=error[1] if error else "Unknown error",
                        execution_time=datetime.now()
                    )
                
                if result.retcode == mt5.TRADE_RETCODE_DONE:
                    # Calculate slippage
                    slippage_pips = self._calculate_slippage(request['price'], result.price, request['symbol'])
                    
                    return ExecutionResult(
                        success=True,
                        order_id=result.order,
                        position_id=result.order,  # In MT5, often same as order ID
                        price=result.price,
                        volume=result.volume,
                        error_code=result.retcode,
                        error_message="Success",
                        execution_time=datetime.now(),
                        slippage_pips=slippage_pips
                    )
                
                else:
                    error_msg = self._get_retcode_description(result.retcode)
                    self.logger.warning(f"Order attempt {attempt + 1} failed: {error_msg}")
                    
                    if attempt < self.retry_attempts - 1:
                        time.sleep(self.retry_delay)
                        continue
                    
                    return ExecutionResult(
                        success=False, order_id=None, position_id=None, price=None,
                        volume=request['volume'], error_code=result.retcode,
                        error_message=error_msg, execution_time=datetime.now()
                    )
                    
            except Exception as e:
                self.logger.error(f"Order execution exception: {e}")
                if attempt < self.retry_attempts - 1:
                    time.sleep(self.retry_delay)
                    continue
                
                return ExecutionResult(
                    success=False, order_id=None, position_id=None, price=None,
                    volume=request['volume'], error_code=-1,
                    error_message=f"Exception: {e}", execution_time=datetime.now()
                )
        
        return ExecutionResult(
            success=False, order_id=None, position_id=None, price=None,
            volume=request['volume'], error_code=-1,
            error_message="All retry attempts failed", execution_time=datetime.now()
        )
    
    def close_position(self, position_id: int, reason: str = "Manual close") -> ExecutionResult:
        """Close an existing position"""
        try:
            if position_id not in self.active_positions:
                return ExecutionResult(
                    success=False, order_id=None, position_id=position_id, price=None,
                    volume=0, error_code=-1, error_message="Position not found",
                    execution_time=datetime.now()
                )
            
            position = self.active_positions[position_id]
            
            # Get current price
            tick = mt5.symbol_info_tick(position.symbol)
            if tick is None:
                return ExecutionResult(
                    success=False, order_id=None, position_id=position_id, price=None,
                    volume=0, error_code=-1, error_message="Failed to get current price",
                    execution_time=datetime.now()
                )
            
            # Determine close price and order type
            if position.type == 'buy':
                close_price = tick.bid
                order_type = mt5.ORDER_TYPE_SELL
            else:
                close_price = tick.ask
                order_type = mt5.ORDER_TYPE_BUY
            
            # Create close request
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": position.symbol,
                "volume": position.volume,
                "type": order_type,
                "position": position_id,
                "price": close_price,
                "deviation": int(self.max_slippage),
                "magic": self.magic_number,
                "comment": f"Close_{reason}",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            # Execute close order
            result = self._execute_order_with_retry(request)
            
            if result.success:
                # Remove from active positions
                del self.active_positions[position_id]
                self.logger.info(f"🔒 Position closed: {position.symbol} {position.type} "
                               f"{position.volume} lots at {result.price:.5f} - {reason}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Position close error: {e}")
            return ExecutionResult(
                success=False, order_id=None, position_id=position_id, price=None,
                volume=0, error_code=-1, error_message=f"Close error: {e}",
                execution_time=datetime.now()
            )
    
    def update_position_sl_tp(self, position_id: int, new_sl: Optional[float] = None, 
                             new_tp: Optional[float] = None) -> bool:
        """Update stop loss and take profit for existing position"""
        try:
            if position_id not in self.active_positions:
                self.logger.warning(f"Position {position_id} not found for SL/TP update")
                return False
            
            position = self.active_positions[position_id]
            
            request = {
                "action": mt5.TRADE_ACTION_SLTP,
                "symbol": position.symbol,
                "position": position_id,
                "sl": new_sl if new_sl is not None else position.stop_loss,
                "tp": new_tp if new_tp is not None else position.take_profit,
            }
            
            result = mt5.order_send(request)
            
            if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                # Update local tracking
                if new_sl is not None:
                    position.stop_loss = new_sl
                if new_tp is not None:
                    position.take_profit = new_tp
                
                self.logger.info(f"📊 Updated SL/TP for {position.symbol}: SL={new_sl}, TP={new_tp}")
                return True
            else:
                error_msg = self._get_retcode_description(result.retcode) if result else "Unknown error"
                self.logger.error(f"Failed to update SL/TP: {error_msg}")
                return False
                
        except Exception as e:
            self.logger.error(f"SL/TP update error: {e}")
            return False
    
    def get_position_status(self, position_id: int) -> Optional[Position]:
        """Get current position status"""
        if position_id in self.active_positions:
            position = self.active_positions[position_id]
            
            # Update current price
            tick = mt5.symbol_info_tick(position.symbol)
            if tick:
                if position.type == 'buy':
                    position.update_current_price(tick.bid)
                else:
                    position.update_current_price(tick.ask)
            
            return position
        return None
    
    def get_all_positions(self) -> Dict[int, Position]:
        """Get all active positions"""
        # Update current prices for all positions
        for position in self.active_positions.values():
            tick = mt5.symbol_info_tick(position.symbol)
            if tick:
                if position.type == 'buy':
                    position.update_current_price(tick.bid)
                else:
                    position.update_current_price(tick.ask)
        
        return self.active_positions.copy()
    
    def monitor_positions(self) -> Dict[str, any]:
        """Monitor all positions and return status summary"""
        total_positions = len(self.active_positions)
        total_profit = sum(pos.profit for pos in self.active_positions.values())
        
        # Count by type
        long_positions = sum(1 for pos in self.active_positions.values() if pos.type == 'buy')
        short_positions = total_positions - long_positions
        
        # Find positions near SL/TP
        positions_near_sl = []
        positions_near_tp = []
        
        for pos in self.active_positions.values():
            if pos.type == 'buy':
                if pos.current_price <= pos.stop_loss * 1.002:  # Within 0.2%
                    positions_near_sl.append(pos.symbol)
                if pos.current_price >= pos.take_profit * 0.998:  # Within 0.2%
                    positions_near_tp.append(pos.symbol)
            else:
                if pos.current_price >= pos.stop_loss * 0.998:
                    positions_near_sl.append(pos.symbol)
                if pos.current_price <= pos.take_profit * 1.002:
                    positions_near_tp.append(pos.symbol)
        
        return {
            'total_positions': total_positions,
            'long_positions': long_positions,
            'short_positions': short_positions,
            'total_profit': total_profit,
            'positions_near_sl': positions_near_sl,
            'positions_near_tp': positions_near_tp,
            'last_update': datetime.now()
        }
    
    def _load_existing_positions(self):
        """Load existing MT5 positions into tracking"""
        try:
            positions = mt5.positions_get()
            if positions:
                for pos in positions:
                    if pos.magic == self.magic_number:  # Only Elliott Wave positions
                        position = Position(
                            position_id=pos.ticket,
                            symbol=pos.symbol,
                            type='buy' if pos.type == 0 else 'sell',
                            volume=pos.volume,
                            open_price=pos.price_open,
                            current_price=pos.price_current,
                            stop_loss=pos.sl,
                            take_profit=pos.tp,
                            swap=pos.swap,
                            profit=pos.profit,
                            comment=pos.comment,
                            open_time=datetime.fromtimestamp(pos.time),
                            wave_pattern="Unknown",  # Can't recover from comment
                            signal_confidence=0.0
                        )
                        self.active_positions[pos.ticket] = position
                
                self.logger.info(f"Loaded {len(self.active_positions)} existing Elliott Wave positions")
                
        except Exception as e:
            self.logger.error(f"Error loading existing positions: {e}")
    
    def _create_position_record(self, signal: TradingSignal, position_size: PositionSize, 
                               result: ExecutionResult) -> Optional[Position]:
        """Create position record from signal and execution result"""
        try:
            return Position(
                position_id=result.position_id,
                symbol=signal.symbol,
                type='buy' if signal.signal_type == SignalType.BUY else 'sell',
                volume=position_size.lot_size,
                open_price=result.price,
                current_price=result.price,
                stop_loss=signal.stop_loss,
                take_profit=signal.take_profit,
                swap=0.0,
                profit=0.0,
                comment=f"EW_{signal.wave_pattern}_{signal.current_wave}",
                open_time=result.execution_time,
                wave_pattern=signal.wave_pattern,
                signal_confidence=signal.confidence
            )
        except Exception as e:
            self.logger.error(f"Error creating position record: {e}")
            return None
    
    def _calculate_slippage(self, requested_price: float, executed_price: float, symbol: str) -> float:
        """Calculate slippage in pips"""
        if 'JPY' in symbol:
            return (executed_price - requested_price) * 100
        elif symbol in ['XAUUSD']:
            return (executed_price - requested_price) * 10
        elif symbol.startswith('US') or symbol in ['NAS100']:
            return executed_price - requested_price
        else:
            return (executed_price - requested_price) * 10000
    
    def _get_retcode_description(self, retcode: int) -> str:
        """Get human-readable description of MT5 return code"""
        retcode_descriptions = {
            mt5.TRADE_RETCODE_DONE: "Request completed",
            mt5.TRADE_RETCODE_REQUOTE: "Requote",
            mt5.TRADE_RETCODE_REJECT: "Request rejected",
            mt5.TRADE_RETCODE_CANCEL: "Request canceled",
            mt5.TRADE_RETCODE_PLACED: "Order placed",
            mt5.TRADE_RETCODE_MARKET_CLOSED: "Market closed",
            mt5.TRADE_RETCODE_NO_MONEY: "Insufficient funds",
            mt5.TRADE_RETCODE_PRICE_CHANGED: "Price changed",
            mt5.TRADE_RETCODE_PRICE_OFF: "Off quotes",
            mt5.TRADE_RETCODE_INVALID_STOPS: "Invalid stops",
            mt5.TRADE_RETCODE_TRADE_DISABLED: "Trade disabled",
            mt5.TRADE_RETCODE_INVALID_VOLUME: "Invalid volume",
            mt5.TRADE_RETCODE_CONNECTION: "No connection",
            mt5.TRADE_RETCODE_ONLY_REAL: "Only real accounts allowed",
            mt5.TRADE_RETCODE_LIMIT_ORDERS: "Orders limit reached",
            mt5.TRADE_RETCODE_LIMIT_VOLUME: "Volume limit reached",
            mt5.TRADE_RETCODE_INVALID_ORDER: "Invalid order",
            mt5.TRADE_RETCODE_POSITION_CLOSED: "Position closed",
        }
        return retcode_descriptions.get(retcode, f"Unknown retcode: {retcode}")

if __name__ == "__main__":
    # Test trade executor
    logging.basicConfig(level=logging.INFO)
    
    executor = TradeExecutor()
    if executor.connect():
        print("🔗 Trade Executor connected")
        
        # Monitor existing positions
        status = executor.monitor_positions()
        print(f"📊 Positions: {status['total_positions']} "
              f"(Long: {status['long_positions']}, Short: {status['short_positions']})")
        print(f"💰 Total P&L: {status['total_profit']:.2f}")
        
        executor.disconnect()
    else:
        print("❌ Failed to connect Trade Executor")