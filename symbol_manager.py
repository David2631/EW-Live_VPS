"""
Symbol Manager - Automatische Symbol-Parameter
Intelligente Erkennung und Anpassung aller Trading-Parameter pro Symbol
"""

import MetaTrader5 as mt5
from typing import Dict, Tuple
from dataclasses import dataclass
import re

@dataclass
class SymbolParameters:
    """Automatisch berechnete Symbol-Parameter"""
    symbol: str
    symbol_type: str  # 'forex_major', 'forex_minor', 'forex_exotic', 'metal', 'index', 'crypto', 'stock'
    pip_size: float
    min_lot: float
    max_lot: float
    lot_step: float
    tick_size: float
    tick_value: float
    
    # Automatisch berechnete Trading-Parameter
    max_spread_pips: float
    min_sl_pips: float
    max_sl_pips: float
    min_tp_pips: float
    max_tp_pips: float
    
    # Risk-Management Parameter
    volatility_factor: float
    liquidity_factor: float

class IntelligentSymbolManager:
    """Intelligente Symbol-Parameter-Verwaltung"""
    
    def __init__(self):
        self.symbol_cache = {}
        
        # Symbol-Kategorien für automatische Erkennung
        self.symbol_patterns = {
            'forex_major': ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD', 'USDCAD', 'NZDUSD'],
            'forex_minor': ['EURJPY', 'GBPJPY', 'EURGBP', 'EURAUD', 'EURCHF', 'AUDCHF', 'GBPCHF', 'CADJPY', 'AUDCAD', 'NZDCAD'],
            'forex_exotic': r'.*NOK|.*SEK|.*PLN|.*CZK|.*HUF|.*TRY|.*ZAR|.*MXN',
            'metal': ['XAUUSD', 'XAGUSD', 'GOLD', 'SILVER', 'GOLD.f', 'SILVER.f'],
            'index': r'.*30|.*100|.*500|.*225|.*50|GER40|UK100|FRA40|DAX|DOW|NASDAQ|SPX|FTSE|ESTX|CHINAA|HK50|AUS200|ESP35|SUI20|NE25',
            'index_future': r'.*\.f$',  # Futures auf Indizes wie DE30.f, US500.f
            'commodity': r'NGAS|USOIL|UKBRENT|WTI|BRENT',
            'commodity_future': r'(NGAS|USOIL|UKBRENT|WTI|BRENT)\.f$',
            'crypto': ['BTCUSD', 'ETHUSD', 'LTCUSD', 'XRPUSD', 'ADAUSD', 'BCHUSD', 'DOGUSD', 'DOTUSD', 'LNKUSD', 'ATOMUSD', 'AXSUSD', 'DOGEUSD', 'SOLUSD', 'UNIUSD', 'XLMUSD'],
            'stock_us': r'.*\.(OQ|N|P)$',  # US-Aktien mit Nasdaq (.OQ), NYSE (.N), oder ETFs (.P)
            'stock_de': r'.*\.DE$',  # Deutsche Aktien
            'stock_simple': r'^[A-Z]{1,5}$'  # Einfache Aktien-Ticker ohne Endung
        }
    
    def get_symbol_parameters(self, symbol: str) -> SymbolParameters:
        """Hole oder berechne Symbol-Parameter automatisch"""
        
        if symbol in self.symbol_cache:
            return self.symbol_cache[symbol]
        
        # MT5 Symbol-Info abrufen
        symbol_info = mt5.symbol_info(symbol)
        if not symbol_info:
            raise ValueError(f"Symbol {symbol} nicht verfügbar")
        
        # Symbol-Typ automatisch erkennen
        symbol_type = self._detect_symbol_type(symbol)
        
        # Pip-Größe automatisch berechnen
        pip_size = self._calculate_pip_size(symbol, symbol_info.digits)
        
        # Volatilität und Liquidität schätzen
        volatility_factor = self._estimate_volatility(symbol, symbol_type)
        liquidity_factor = self._estimate_liquidity(symbol, symbol_type)
        
        # Parameter automatisch berechnen
        max_spread = self._calculate_max_spread(symbol_type, volatility_factor, liquidity_factor)
        min_sl, max_sl = self._calculate_sl_range(symbol_type, volatility_factor)
        min_tp, max_tp = self._calculate_tp_range(symbol_type, volatility_factor)
        
        params = SymbolParameters(
            symbol=symbol,
            symbol_type=symbol_type,
            pip_size=pip_size,
            min_lot=symbol_info.volume_min,
            max_lot=symbol_info.volume_max,
            lot_step=symbol_info.volume_step,
            tick_size=symbol_info.point,
            tick_value=symbol_info.trade_tick_value,
            max_spread_pips=max_spread,
            min_sl_pips=min_sl,
            max_sl_pips=max_sl,
            min_tp_pips=min_tp,
            max_tp_pips=max_tp,
            volatility_factor=volatility_factor,
            liquidity_factor=liquidity_factor
        )
        
        self.symbol_cache[symbol] = params
        return params
    
    def _detect_symbol_type(self, symbol: str) -> str:
        """Automatische Symbol-Typ-Erkennung"""
        
        # Major Forex Pairs
        if symbol in self.symbol_patterns['forex_major']:
            return 'forex_major'
        
        # Minor Forex Pairs
        if symbol in self.symbol_patterns['forex_minor']:
            return 'forex_minor'
        
        # Exotic Forex Pairs (RegEx)
        if re.match(self.symbol_patterns['forex_exotic'], symbol):
            return 'forex_exotic'
        
        # Precious Metals
        if symbol in self.symbol_patterns['metal']:
            return 'metal'
        
        # US Stocks (mit .OQ, .N, .P Endungen)
        if re.match(self.symbol_patterns['stock_us'], symbol):
            return 'stock_us'
        
        # Deutsche Aktien (mit .DE Endung)
        if re.match(self.symbol_patterns['stock_de'], symbol):
            return 'stock_de'
        
        # Einfache Aktien-Ticker
        if re.match(self.symbol_patterns['stock_simple'], symbol):
            return 'stock_simple'
        
        # Commodity Futures
        if re.match(self.symbol_patterns['commodity_future'], symbol):
            return 'commodity_future'
        
        # Index Futures (mit .f Endung)
        if re.match(self.symbol_patterns['index_future'], symbol):
            return 'index_future'
        
        # Commodities
        if re.match(self.symbol_patterns['commodity'], symbol):
            return 'commodity'
        
        # Indices (RegEx)
        if re.match(self.symbol_patterns['index'], symbol):
            return 'index'
        
        # Cryptocurrencies
        if symbol in self.symbol_patterns['crypto']:
            return 'crypto'
        
        # Default: Forex Minor
        return 'forex_minor'
    
    def _calculate_pip_size(self, symbol: str, digits: int) -> float:
        """Automatische Pip-Größe-Berechnung"""
        
        # JPY Pairs haben andere Pip-Größe
        if 'JPY' in symbol:
            return 0.01 if digits == 3 else 0.001
        
        # Standard Forex
        if digits == 5:
            return 0.0001  # 4 Dezimalstellen + 1 Extra
        elif digits == 4:
            return 0.0001
        elif digits == 3:
            return 0.01
        elif digits == 2:
            return 0.01
        else:
            return 10 ** (-digits + 1)
    
    def _estimate_volatility(self, symbol: str, symbol_type: str) -> float:
        """Schätze Volatilität basierend auf Symbol-Typ"""
        
        volatility_map = {
            'forex_major': 1.0,      # Niedrige Volatilität
            'forex_minor': 1.3,      # Mittlere Volatilität
            'forex_exotic': 2.5,     # Hohe Volatilität
            'metal': 2.0,            # Hohe Volatilität
            'index': 1.5,            # Mittlere Volatilität
            'index_future': 1.6,     # Etwas höher als Spot-Indizes
            'commodity': 2.2,        # Hohe Volatilität
            'commodity_future': 2.4, # Noch höher als Spot-Commodities
            'crypto': 4.0,           # Sehr hohe Volatilität
            'stock_us': 1.8,         # US-Aktien: mittlere bis hohe Volatilität
            'stock_de': 1.7,         # Deutsche Aktien: etwas niedriger
            'stock_simple': 1.8      # Einfache Aktien
        }
        
        return volatility_map.get(symbol_type, 1.5)
    
    def _estimate_liquidity(self, symbol: str, symbol_type: str) -> float:
        """Schätze Liquidität basierend auf Symbol-Typ"""
        
        liquidity_map = {
            'forex_major': 1.0,      # Sehr hohe Liquidität
            'forex_minor': 0.8,      # Hohe Liquidität
            'forex_exotic': 0.3,     # Niedrige Liquidität
            'metal': 0.7,            # Mittlere Liquidität
            'index': 0.9,            # Hohe Liquidität
            'index_future': 0.8,     # Etwas niedriger als Spot-Indizes
            'commodity': 0.6,        # Mittlere Liquidität
            'commodity_future': 0.7, # Höher als Spot-Commodities
            'crypto': 0.6,           # Mittlere Liquidität
            'stock_us': 0.9,         # US-Aktien: sehr hohe Liquidität
            'stock_de': 0.7,         # Deutsche Aktien: mittlere Liquidität
            'stock_simple': 0.8      # Einfache Aktien
        }
        
        return liquidity_map.get(symbol_type, 0.5)
    
    def _calculate_max_spread(self, symbol_type: str, volatility: float, liquidity: float) -> float:
        """Berechne maximalen akzeptablen Spread"""
        
        base_spreads = {
            'forex_major': 3.0,
            'forex_minor': 8.0,
            'forex_exotic': 50.0,
            'metal': 30.0,
            'index': 1000.0,         # Indizes haben sehr breite Spreads
            'index_future': 1200.0,  # Futures etwas breiter
            'commodity': 40.0,       # Commodities moderate Spreads
            'commodity_future': 50.0,# Commodity Futures breiter
            'crypto': 200.0,         # Crypto spreads erhöht
            'stock_us': 3000.0,      # US-Aktien: deutlich höhere Spreads für CFDs
            'stock_de': 5000.0,      # Deutsche Aktien: noch größere Spreads
            'stock_simple': 4000.0   # Einfache Aktien
        }
        
        base = base_spreads.get(symbol_type, 20.0)
        
        # Anpassung basierend auf Volatilität und Liquidität
        volatility_adjustment = volatility * 1.5
        liquidity_adjustment = (2.0 - liquidity)  # Niedrigere Liquidität = höherer Spread
        
        return base * volatility_adjustment * liquidity_adjustment
    
    def _calculate_sl_range(self, symbol_type: str, volatility: float) -> Tuple[float, float]:
        """Berechne Stop-Loss-Bereich"""
        
        base_sl = {
            'forex_major': (20, 200),
            'forex_minor': (30, 300),
            'forex_exotic': (50, 500),
            'metal': (100, 1000),
            'index': (50, 2000),
            'index_future': (60, 2500),
            'commodity': (80, 800),
            'commodity_future': (100, 1000),
            'crypto': (200, 2000),
            'stock_us': (30, 400),       # US-Aktien: moderate Ranges
            'stock_de': (40, 500),       # Deutsche Aktien: etwas größer
            'stock_simple': (35, 450)    # Einfache Aktien
        }
        
        min_base, max_base = base_sl.get(symbol_type, (30, 300))
        
        # Volatilitäts-Anpassung
        min_sl = min_base * volatility
        max_sl = max_base * volatility
        
        return min_sl, max_sl
    
    def _calculate_tp_range(self, symbol_type: str, volatility: float) -> Tuple[float, float]:
        """Berechne Take-Profit-Bereich"""
        
        base_tp = {
            'forex_major': (30, 500),
            'forex_minor': (40, 800),
            'forex_exotic': (80, 1000),
            'metal': (200, 2000),
            'index': (100, 5000),
            'index_future': (120, 6000),
            'commodity': (150, 1500),
            'commodity_future': (180, 1800),
            'crypto': (500, 5000),
            'stock_us': (60, 800),       # US-Aktien: moderate TP
            'stock_de': (80, 1000),      # Deutsche Aktien: größere TP
            'stock_simple': (70, 900)    # Einfache Aktien
        }
        
        min_base, max_base = base_tp.get(symbol_type, (50, 500))
        
        # Volatilitäts-Anpassung
        min_tp = min_base * volatility
        max_tp = max_base * volatility
        
        return min_tp, max_tp
    
    def get_optimal_sl_tp(self, symbol: str, signal_strength: int, rr_ratio: float = 2.0) -> Tuple[float, float]:
        """Berechne optimale SL/TP basierend auf Signal-Stärke"""
        
        params = self.get_symbol_parameters(symbol)
        
        # Basis SL basierend auf Signal-Stärke
        strength_factor = {1: 1.5, 2: 1.2, 3: 1.0, 4: 0.8}.get(signal_strength, 1.0)
        
        base_sl = (params.min_sl_pips + params.max_sl_pips) / 2 * strength_factor
        
        # Sicherstellen, dass SL in gültigen Grenzen ist
        optimal_sl = max(params.min_sl_pips, min(base_sl, params.max_sl_pips))
        
        # TP basierend auf Risk-Reward-Ratio
        optimal_tp = optimal_sl * rr_ratio
        
        # TP in gültigen Grenzen halten
        optimal_tp = max(params.min_tp_pips, min(optimal_tp, params.max_tp_pips))
        
        return optimal_sl, optimal_tp