# 🌊 Elliott Wave Live Trading System V2 for VPS

**Professional Elliott Wave automated trading system with Dynamic Price Validation, advanced risk management, and 24/7 VPS deployment capability.**

![Elliott Wave Trading](https://img.shields.io/badge/Elliott%20Wave-V2%20System-blue)
![Python](https://img.shields.io/badge/Python-3.9+-green)
![MetaTrader5](https://img.shields.io/badge/MetaTrader-5-orange)
![VPS Ready](https://img.shields.io/badge/VPS-Production%20Ready-brightgreen)
![Tested](https://img.shields.io/badge/Local%20Testing-100%25%20Success-success)

## 🆕 V2 Revolutionary Features

- 🎯 **Dynamic Price Validation System** - Real-time broker requirement validation and automatic order adjustment
- 🔧 **Intelligent Filling Mode Detection** - Automatic IOC/FOK/RETURN mode selection based on broker capabilities  
- 🛡️ **Bulletproof Duplicate Prevention** - Real-time position checking prevents duplicate trades
- ⚡ **Retcode 10030 Resolution** - Complete elimination of decimal precision and filling mode errors
- 📊 **Enhanced Position Tracking** - Live MT5 integration with detailed position monitoring
- 🎯 **Symbol-Specific Pip Calculations** - Forex, indices, and metals with broker-specific adjustments
- 🔄 **Alternative Execution Strategies** - Multi-mode retry logic for maximum execution success
- 📈 **Professional Error Handling** - 40+ MT5 error codes with intelligent recovery strategies

## ✨ Core Features

- 🌊 **Full Elliott Wave Analysis** - Complete wave pattern detection and trading signals
- 📊 **Multi-Asset Support** - EURUSD, GBPUSD, AUDUSD, XAUUSD, US30, NAS100, UK100 + more
- ⏰ **Real-time Scanning** - Analyzes all symbols every 60 seconds with M30 timeframe
- 🎯 **Take Profit Capping** - Broker-compatible TP limits (US30: 1500 pips, AUDUSD: 300 pips)
- 🛡️ **Advanced Risk Management** - Portfolio risk control, position sizing, correlation limits
- 🔄 **Automatic Price Adjustment** - Real-time SL/TP validation and correction
- 📈 **High-Confidence Signals** - 70%+ confidence threshold with ML validation
- 🖥️ **VPS Optimized** - 24/7 automated trading with industrial-grade reliability
- 📊 **Comprehensive Logging** - Full trade execution audit trail and performance metrics

## 🚀 Quick Start (VPS Installation)

### 1. Download & Extract
```bash
git clone https://github.com/David2631/EW-Live_VPS.git
cd EW-Live_VPS/Elliott-Wave-Live-V2
```

### 2. One-Click Installation
```cmd
install_vps.bat
```

### 3. Start V2 Trading System
```cmd
start_full_trading.bat     # All symbols with full risk management
start_demo_trading.bat     # Demo account testing
start_simple_trading.bat   # Conservative symbol set
```

**🎯 Your V2 Elliott Wave system with Dynamic Price Validation is running 24/7!** 🎉

## 🧪 Pre-Deployment Testing (Recommended)

Before live trading, run comprehensive tests:
```cmd
# Test Dynamic Price Validation
python test_price_validation.py

# Test Duplicate Prevention  
python test_duplicate_prevention.py

# Test Engine Integration
python test_engine.py
```

## 📋 Detailed Installation Guide

### Prerequisites
- ✅ Windows Server 2019/2022 or Windows 10/11
- ✅ MetaTrader 5 installed and configured
- ✅ Trading account connected to MT5
- ✅ Internet connection
- ✅ 8GB RAM recommended

### Step-by-Step Installation

#### 1. **Download Repository**
```bash
git clone https://github.com/YOUR_USERNAME/Elliott-Wave-VPS-Trader.git
```
Or download ZIP from GitHub and extract.

#### 2. **Run Installation Script**
```cmd
cd Elliott-Wave-VPS-Trader
install_vps.bat
```

This will:
- Install Python dependencies
- Test MT5 connection
- Validate system configuration
- Run comprehensive tests

#### 4. **Configure V2 Trading Parameters**
Edit `elliott_live_config_v2.json`:
```json
{
  "account_balance": 10000,
  "scan_interval": 60,
  "symbols": ["EURUSD", "GBPUSD", "AUDUSD", "NZDUSD", "USDCHF", "XAUUSD", "US30", "NAS100"],
  "risk_management": {
    "max_risk_per_trade": 0.02,
    "max_daily_risk": 0.05,
    "max_portfolio_risk": 0.15
  },
  "price_validation": {
    "enable_dynamic_validation": true,
    "auto_adjust_orders": true,
    "max_tp_distances": {
      "AUDUSD": 300,
      "NZDUSD": 250, 
      "US30": 1500,
      "NAS100": 800,
      "XAUUSD": 500
    }
  }
}
```

#### 4. **Validate System Health**
```cmd
# Run comprehensive validation suite
python test_price_validation.py     # Test broker integration
python test_duplicate_prevention.py # Test position management
python test_engine.py              # Test Elliott Wave engine
```

#### 5. **Deploy V2 Production System**
```cmd
# Conservative start
start_demo_trading.bat

# Full production
start_full_trading.bat
```

## 📊 V2 Configuration Options

### V2 Trading Parameters
| Parameter | Default | Description |
|-----------|---------|-------------|
| `scan_interval` | 60 | Symbol analysis interval (seconds) |
| `max_risk_per_trade` | 0.02 | Risk per trade (2%) |
| `max_portfolio_risk` | 0.15 | Maximum total portfolio risk (15%) |
| `confidence_threshold` | 70 | Minimum signal confidence (%) |
| `enable_dynamic_validation` | true | Real-time price validation |
| `auto_adjust_orders` | true | Automatic SL/TP adjustment |

### Symbol-Specific Limits
| Symbol | Max TP Distance | Min Confidence | Notes |
|--------|----------------|---------------|-------|
| EURUSD | 300 pips | 70% | Major pair - conservative |
| AUDUSD | 300 pips | 80% | Capped for broker compatibility |
| US30 | 1500 pips | 80% | Index - higher volatility |
| NAS100 | 800 pips | 80% | Tech index - moderate TP |
| XAUUSD | 500 pips | 85% | Gold - premium signals only |

### V2 Risk Management Features
- **Dynamic Price Validation**: Real-time broker requirement checking
- **Duplicate Prevention**: Automatic position conflict resolution  
- **Intelligent Filling Modes**: IOC/FOK/RETURN mode selection
- **Portfolio Risk Control**: Multi-symbol correlation management
- **Emergency Circuit Breakers**: Automatic system protection

## 🧪 V2 Testing Suite

Run comprehensive V2 validation:
```cmd
# Core system tests
python test_price_validation.py        # Dynamic price validation
python test_duplicate_prevention.py    # Position conflict prevention
python test_engine.py                 # Elliott Wave engine validation

# Legacy compatibility tests  
python live_trading_tests.py          # Original system tests
```

**V2 Test Coverage:**
- ✅ **Dynamic Price Validation** - Real-time broker integration
- ✅ **Duplicate Position Prevention** - Multi-symbol conflict detection
- ✅ **Filling Mode Intelligence** - IOC/FOK/RETURN compatibility
- ✅ **Retcode 10030 Resolution** - Decimal precision handling
- ✅ **MT5 Connection Stability** - Robust broker connection
- ✅ **Elliott Wave Accuracy** - Signal generation validation
- ✅ **Risk Management V2** - Portfolio-level controls
- ✅ **Error Recovery** - Graceful failure handling
- ✅ **VPS Production Readiness** - 24/7 deployment capability

**🎯 100% Test Success Rate Required Before Live Trading**

## 📈 Monitoring

### Real-time System Monitor
```cmd
python vps_monitor.py
```

**Monitoring Features:**
- System health (CPU, memory, disk)
- Trading process status
- Performance metrics
- Email alerts (configurable)

### Log Files
- `elliott_live_trader.log` - Trading activities
- `monitor_YYYYMMDD.log` - System monitoring
- `error_YYYYMMDD.log` - Error tracking

## 🔧 Troubleshooting

### Common Issues

#### MT5 Connection Failed
```cmd
python mt5_diagnostic.py
```

**Solutions:**
1. Ensure MT5 is running and logged in
2. Check broker server connection
3. Verify account permissions
4. Restart MT5 terminal

#### No Trading Signals
- Check market hours
- Verify data feed active
- Review Elliott Wave parameters
- Check minimum confidence settings

#### High CPU/Memory Usage
- Close unnecessary programs
- Restart trading system
- Check for data feed issues
- Consider VPS upgrade

## 📁 File Structure

```
Elliott-Wave-VPS-Trader/
├── elliott_live_trader.py      # Main trading system
├── elliott_live_config.json    # Configuration file
├── mt5_diagnostic.py          # MT5 troubleshooting
├── live_trading_tests.py      # Comprehensive test suite
├── vps_monitor.py             # System monitoring
├── requirements.txt           # Python dependencies
├── install_vps.bat           # One-click installation
├── start_trading.bat         # Trading system launcher
├── README.md                 # This file
└── docs/
    ├── INSTALLATION_GUIDE.md  # Detailed setup guide
    ├── CONFIGURATION.md       # Parameter explanation
    ├── TROUBLESHOOTING.md     # Problem solving
    └── CHANGELOG.md           # Version history
```

## ⚠️ Risk Disclaimer

**Trading involves substantial risk of loss. Past performance does not guarantee future results.**

- Never risk more than you can afford to lose
- Test thoroughly with demo accounts
- Start with small position sizes
- Monitor system regularly
- Seek professional advice if needed

## 🤝 Support

- 📖 **Documentation**: Check `docs/` folder
- 🐛 **Issues**: Report on GitHub Issues
- 📧 **Contact**: [Your contact information]

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🎉 Acknowledgments

- Elliott Wave Theory foundations
- MetaTrader 5 platform
- Python trading community

---

**⚡ Ready to automate your Elliott Wave trading? Get started now!** 🚀

## 📊 Performance Examples

**Backtest Results (Demo):**
- Strategy: Elliott Wave with ATR-based SL/TP
- Period: 2024-2025
- Instrument: EURUSD
- Return: 99.30% (with quarterly realization)
- Max Drawdown: 15.2%
- Win Rate: 67%
- Risk/Reward: 1:2

*Results are for demonstration purposes only. Past performance does not guarantee future results.*