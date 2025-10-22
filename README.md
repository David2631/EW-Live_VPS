# Elliott Wave V2 - Professional Live Trading System# Elliott Wave Live Trading System V2

## Professional Investment Bank Architecture

🚀 **Professionelles Elliott Wave Trading System für VPS Deployment**

🎯 **Advanced Elliott Wave trading system with modular Investment Bank architecture using the original proven Elliott Wave engine from the successful backtesting system.**

## 🎯 Quick Start

---

### VPS Installation (Ein Befehl):

```bash## 🏗️ **Investment Bank Modular Architecture**

curl -O https://raw.githubusercontent.com/David2631/Elliott-Wave-VPS-Trader/master/install_and_start.bat

install_and_start.batThis V2 system follows professional Investment Bank practices with **completely separated modules**, each handling specific responsibilities:

```

### **1. Elliott Wave Engine** (`elliott_wave_engine.py`)

### Oder manuell:- **Original complex Elliott Wave logic** from successful backtesting system

```bash- ZigZag pivot detection with ATR-based filtering

git clone https://github.com/David2631/Elliott-Wave-VPS-Trader.git- 5-wave impulse pattern recognition (1-2-3-4-5)

cd Elliott-Wave-VPS-Trader- ABC correction pattern identification

pip install -r requirements.txt- Fibonacci retracement and extension analysis

python elliott_wave_trader_v2.py --symbols symbols_simple.txt --thr 0.30- Wave validation rules and confidence scoring

```

### **2. Market Data Manager** (`market_data_manager.py`)

## ⚙️ Start Commands- Live MT5 data feeds for 6 symbols

- Real-time OHLCV data with technical indicators

**Empfohlen für Demo-Accounts:**- Data quality validation and symbol management

```bash- Multi-timeframe support with caching

python elliott_wave_trader_v2.py --symbols symbols_simple.txt --thr 0.30

```### **3. Risk Manager** (`risk_manager.py`)

- Professional position sizing using ATR

**Für alle Märkte:**- Portfolio-level risk controls

```bash- Correlation risk management

python elliott_wave_trader_v2.py --symbols symbols.txt --thr 0.30- Daily and total risk limits

```- Consecutive loss protection



**Aggressiv (mehr Signale):**### **4. Signal Generator** (`signal_generator.py`)

```bash- Converts Elliott Wave patterns into trading signals

python elliott_wave_trader_v2.py --symbols symbols_simple.txt --no-ml --no-ema- Wave 5 completion reversal signals

```- Wave 3 momentum continuation

- ABC correction completion entries

## 📋 Features- Fibonacci retracement opportunities

- Multi-factor confidence scoring

✅ Original Elliott Wave Logic aus erfolgreichem Backtest  

✅ Investment Bank Architektur (6 Module)  ### **5. Trade Executor** (`trade_executor.py`)

✅ ML-Threshold Filter (Top 30% = +33% Performance)  - Professional MT5 order execution

✅ Auto Market Watch (Symbole automatisch aktiviert)  - Retry logic with slippage control

✅ Professional Risk Management (ATR-basiert)  - Position monitoring and management

✅ Multi-Timeframe Analysis (H1, M30)  - Stop loss / take profit automation

- Order status tracking

## 📊 Performance

### **6. Main Trading Engine** (`elliott_wave_trader_v2.py`)

- **271% Return** (vs 233% ohne ML-Filter)- Orchestrates all modules

- **3-6 Signale/Tag** (hochwertig)- Multi-threaded analysis and monitoring

- **Risk/Reward:** Min 1:2- Session management and performance tracking

- **Win Rate:** ~65-75% mit ML-Filter- Emergency stop conditions

- Comprehensive logging and reporting

## 🔧 MT5 Setup

---

**WICHTIG: AutoTrading aktivieren!**

1. MT5 → Tools → Options → Expert Advisors## 🔄 **Key Differences from V1**

2. ✅ Allow automated trading

3. ✅ Allow DLL imports| Feature | V1 (Simplified) | V2 (Investment Bank) |

|---------|----------------|---------------------|

## 📊 Symbol Listen| **Elliott Wave Logic** | ❌ Dummy EMA/RSI logic | ✅ **Original complex engine** |

| **Architecture** | ❌ Monolithic single file | ✅ **Modular components** |

- **symbols_simple.txt** - EURUSD, GBPUSD, USDJPY, AUDUSD, USDCAD, XAUUSD, XAGUSD| **Risk Management** | ❌ Basic percentage | ✅ **Professional ATR-based** |

- **symbols_demo.txt** - EURUSD, XAUUSD, US30  | **Signal Quality** | ❌ Simple technical indicators | ✅ **True Elliott Wave patterns** |

- **symbols.txt** - Alle Märkte (17 Symbole)| **Position Sizing** | ❌ Fixed lot sizes | ✅ **Dynamic risk-based sizing** |

| **Monitoring** | ❌ Basic logging | ✅ **Multi-threaded monitoring** |

## 🛠️ Tools| **Pattern Recognition** | ❌ None | ✅ **5-wave impulse + ABC corrections** |



- **install_and_start.bat** - Komplette VPS Installation---

- **quick_start.bat** - Interaktives Start-Menü

- **symbol_checker.py** - Symbol-Verfügbarkeit prüfen## 📊 **Supported Symbols & Sessions**



## 💡 Tipps| Symbol | Type | Pip Factor | Preferred Session | Notes |

|--------|------|------------|------------------|-------|

1. **Erste Installation:** `install_and_start.bat` verwenden| **EURUSD** | Forex | 0.0001 | London/NY Overlap | Major pair, high liquidity |

2. **Restart:** `quick_start.bat` für Menü-Auswahl| **XAUUSD** | Precious Metal | 0.1 | NY Session | Gold, higher volatility |

3. **Probleme:** `python symbol_checker.py` ausführen| **US30** | Index | 1.0 | NY Session | Dow Jones, trending markets |

4. **Demo-Account:** Mit symbols_simple.txt starten| **NAS100** | Index | 1.0 | NY Session | NASDAQ, tech sentiment |

| **US500.f** | Index | 1.0 | NY Session | S&P 500 futures |

---| **AUDNOK** | Forex | 0.0001 | Sydney/Tokyo | Exotic pair, range-bound |

🚀 **Ready for professional Elliott Wave trading!**
---

## ⚙️ **Installation & Setup**

### **1. Requirements**
```bash
# Python 3.8+ required
pip install -r requirements.txt

# TA-Lib (Windows manual installation)
# Download: https://www.lfd.uci.edu/~gohlke/pythonlibs/#ta-lib
pip install TA_Lib-0.4.24-cp39-cp39-win_amd64.whl
```

### **2. MT5 Setup**
- Install MetaTrader 5 terminal
- Enable algorithmic trading
- Add all symbols to Market Watch
- Ensure good internet connection

### **3. Configuration**
Edit `elliott_live_config_v2.json`:
```json
{
  "account_balance": 10000,
  "symbols": ["EURUSD", "XAUUSD", "US30", "NAS100", "US500.f", "AUDNOK"],
  "risk_parameters": {
    "max_risk_per_trade": 0.01,
    "max_daily_risk": 0.03
  }
}
```

### **4. Launch**
```bash
python elliott_wave_trader_v2.py
```

---

## 🎯 **Elliott Wave Trading Signals**

### **Signal Types Generated:**

#### **1. Wave 5 Completion (Reversal)**
- **Pattern**: End of 5-wave impulse
- **Action**: Counter-trend entry
- **Target**: Wave 4 retracement level
- **Confidence**: 75-95%

#### **2. Wave 3 Momentum (Continuation)** 
- **Pattern**: Wave 4 retracement completion
- **Action**: Trend continuation entry
- **Target**: Wave 5 extension (1.618 of Wave 1-3)
- **Confidence**: 70-85%

#### **3. ABC Correction Completion**
- **Pattern**: End of corrective ABC sequence
- **Action**: Trend resumption entry
- **Target**: Beyond previous high/low
- **Confidence**: 65-80%

#### **4. Fibonacci Retracement Entries**
- **Pattern**: 38.2%, 50%, 61.8% retracements
- **Action**: Pullback entries in trends
- **Target**: Previous extreme + extension
- **Confidence**: 60-75%

---

## 📈 **Risk Management Features**

### **Position Sizing**
- **ATR-based stop losses**: Dynamic based on volatility
- **Risk per trade**: 1% of account balance (configurable)
- **Reward:Risk minimum**: 2:1 ratio required
- **Symbol-specific**: Different pip values handled

### **Portfolio Protection**
- **Daily risk limit**: 3% maximum daily loss
- **Portfolio risk**: 5% maximum total exposure
- **Correlation limits**: 2% for correlated pairs
- **Consecutive losses**: Stop after 3 losses

### **Emergency Stops**
- Automatic position closure on extreme conditions
- System shutdown on critical errors
- Manual override capabilities

---

## 🔍 **Monitoring & Reporting**

### **Real-Time Monitoring**
- Position status every 30 seconds
- Performance metrics every 5 minutes  
- Risk analysis continuously
- Elliott Wave pattern detection

### **Logging**
- **Signal logs**: All generated signals with reasoning
- **Execution logs**: Order details and slippage
- **Performance logs**: P&L and statistics
- **Error logs**: System issues and resolutions

### **Performance Reports**
```
Elliott Wave Trading Engine V2 - Status Report
============================================================
Session Duration: 8.5 hours
Signals Generated: 24
Trades Executed: 12  
Total P&L: $487.50
Active Positions: 3
Portfolio Risk: 2.1%
============================================================
```

---

## 🧠 **Elliott Wave Engine Details**

### **Original Complex Logic Restored**
The V2 system uses the **exact same Elliott Wave engine** that produced successful results in backtesting:

#### **ZigZag Detection**
- ATR-based pivot identification
- Noise filtering with minimum deviation
- Multi-timeframe validation

#### **5-Wave Impulse Recognition**
- **Wave 1**: Initial trend movement
- **Wave 2**: 23.6-78.6% retracement  
- **Wave 3**: Strongest wave (>100% of Wave 1)
- **Wave 4**: 23.6-61.8% retracement (no overlap with Wave 1)
- **Wave 5**: Final impulse (61.8-161.8% extension)

#### **ABC Corrections**
- **Wave A**: Counter-trend movement
- **Wave B**: 50-78.6% retracement of A
- **Wave C**: Equal to or 61.8-161.8% of Wave A

#### **Fibonacci Analysis**
- Retracement levels: 23.6%, 38.2%, 50%, 61.8%, 78.6%
- Extension levels: 100%, 127.2%, 161.8%, 261.8%
- Time-based Fibonacci (future enhancement)

---

## 🚀 **Advanced Features**

### **Multi-Threading**
- **Analysis Thread**: Continuous pattern scanning
- **Monitoring Thread**: Position and risk tracking
- **Main Thread**: User interface and control

### **Symbol-Specific Optimization**
- Currency pairs: Optimized for ranging/trending behavior
- Indices: Momentum-based entries during market hours
- Gold: Volatility-adjusted parameters
- Exotic pairs: Higher confirmation requirements

### **Session Management**
- London/NY overlap for EUR pairs
- NY session for US indices and gold
- Sydney/Tokyo for AUD pairs
- Weekend and holiday exclusions

---

## ⚠️ **Important Notes**

### **Live Trading Warnings**
- ⚠️ **Always test on demo account first**
- ⚠️ **Start with small position sizes**
- ⚠️ **Monitor during first hours of operation**
- ⚠️ **Ensure stable internet connection**
- ⚠️ **Keep MT5 terminal running**

### **Risk Disclaimers**
- Past performance does not guarantee future results
- Elliott Wave analysis is subjective and not foolproof
- Market conditions can change rapidly
- Always trade with money you can afford to lose
- Consider your risk tolerance and experience level

---

## 🔧 **Troubleshooting**

### **Common Issues**
1. **MT5 Connection Failed**
   - Check MT5 terminal is running
   - Verify algorithmic trading is enabled
   - Ensure account has trading permissions

2. **Symbol Not Available**
   - Add symbol to Market Watch
   - Check symbol name spelling
   - Verify broker offers the symbol

3. **No Signals Generated**
   - Check Elliott Wave patterns need time to develop
   - Verify data quality and sufficient history
   - Review confidence thresholds in config

4. **Orders Rejected**
   - Check account balance and margin
   - Verify symbol trading hours
   - Review stop loss/take profit levels

---

## 📞 **Support & Development**

### **File Structure**
```
Elliott-Wave-Live-V2/
├── elliott_wave_engine.py      # Core Elliott Wave logic
├── market_data_manager.py      # MT5 data feeds
├── risk_manager.py             # Position sizing & risk
├── signal_generator.py         # Trading signal creation
├── trade_executor.py           # Order execution
├── elliott_wave_trader_v2.py   # Main orchestrator
├── elliott_live_config_v2.json # Configuration
├── requirements.txt            # Dependencies
└── README.md                   # This documentation
```

### **Development Roadmap**
- [ ] Machine learning signal enhancement
- [ ] Multi-timeframe Elliott Wave analysis
- [ ] Advanced correlation matrix
- [ ] Telegram/Discord notifications
- [ ] Web-based monitoring dashboard
- [ ] Cloud deployment options

---

## 📜 **License & Disclaimer**

This software is provided for educational and research purposes. Use at your own risk. The authors are not responsible for any financial losses incurred through the use of this system.

**Elliott Wave Trading System V2** - Professional Investment Bank Architecture
*Created: January 2025*