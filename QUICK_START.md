# Elliott Wave VPS Trading System - Quick Installation Guide

## 🚀 One-Command Installation

### For VPS/Windows:
```cmd
git clone https://github.com/YOUR_USERNAME/Elliott-Wave-VPS-Trader.git
cd Elliott-Wave-VPS-Trader
install_vps.bat
```

### For Manual Installation:
1. Download ZIP from GitHub
2. Extract to `C:\Elliott-Trading\`
3. Run `install_vps.bat`

## 📋 Prerequisites Checklist

- [ ] ✅ Windows 10/11 or Windows Server 2019/2022
- [ ] ✅ Python 3.9+ installed
- [ ] ✅ MetaTrader 5 installed
- [ ] ✅ Broker account configured in MT5
- [ ] ✅ Internet connection
- [ ] ✅ 8GB RAM (recommended)

## ⚡ Quick Commands

**Install:** `install_vps.bat`
**Test:** `python live_trading_tests.py`  
**Start:** `start_trading.bat`
**Monitor:** `python vps_monitor.py`

## 🔧 Troubleshooting

**MT5 Connection Issues:**
```cmd
python mt5_diagnostic.py
```

**System Tests:**
```cmd
python live_trading_tests.py
```

## ⚠️ Important Notes

- ✅ **Test with demo account first!**
- ✅ **Start with small position sizes**
- ✅ **Monitor system for 24-48 hours**
- ✅ **Never risk more than you can afford to lose**

## 📞 Support

- GitHub Issues for bugs
- Documentation in `docs/` folder
- Trading logs in `*.log` files