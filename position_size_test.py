"""
Detaillierter Test der Positionsgrößenberechnung
Prüft verschiedene Szenarien und Edge Cases
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from elliott_live_trader import ElliottWaveLiveTrader
import MetaTrader5 as mt5

def test_position_sizing_detailed():
    """Test verschiedene Position Sizing Szenarien"""
    print("🧮 DETAILLIERTE POSITIONSGRÖSSENBERECHNUNG TESTS")
    print("=" * 60)
    
    trader = ElliottWaveLiveTrader()
    
    # Test Szenarien
    test_scenarios = [
        # (Account Balance, Risk%, Stop Distance Pips, Expected Lot Size Range)
        (10000, 0.02, 0.0050, "0.40-4.00"),    # $10k, 2% risk, 50 pips
        (10000, 0.01, 0.0100, "0.10-1.00"),    # $10k, 1% risk, 100 pips  
        (100000, 0.02, 0.0050, "4.00-40.00"),  # $100k, 2% risk, 50 pips
        (1000, 0.05, 0.0020, "0.01-2.50"),     # $1k, 5% risk, 20 pips
        (50000, 0.03, 0.0075, "2.00-20.00"),   # $50k, 3% risk, 75 pips
    ]
    
    print("\n📊 SZENARIEN TESTS:")
    print("Account | Risk% | Stop(pips) | Risk$ | Lot Size | Status")
    print("-" * 60)
    
    for balance, risk_pct, stop_distance, expected_range in test_scenarios:
        risk_amount = balance * risk_pct
        
        # Test ohne MT5 Connection (Fallback Berechnung)
        trader.mt5_connected = False
        lot_size_fallback = trader.calculate_position_size(risk_amount, stop_distance)
        
        # Test mit MT5 Connection (falls verfügbar)
        if mt5.initialize():
            trader.mt5_connected = True
            lot_size_mt5 = trader.calculate_position_size(risk_amount, stop_distance)
            mt5.shutdown()
        else:
            lot_size_mt5 = "N/A"
        
        # Validierung
        status = "✅ OK"
        if lot_size_fallback > 10.0:
            status = "⚠️  HIGH"
        elif lot_size_fallback < 0.01:
            status = "❌ LOW"
        
        print(f"${balance:6} | {risk_pct*100:4.1f}% | {stop_distance*10000:7.0f} | ${risk_amount:6.0f} | {lot_size_fallback:8.2f} | {status}")
        
        if lot_size_mt5 != "N/A":
            print(f"        |       |            |        | {lot_size_mt5:8.2f} | (MT5)")
    
    print("\n🔍 EDGE CASE TESTS:")
    
    # Edge Cases
    edge_cases = [
        ("Zero risk", 0, 0.0050),
        ("Tiny risk", 1, 0.0050), 
        ("Huge risk", 100000, 0.0001),
        ("Zero stop", 1000, 0),
        ("Tiny stop", 1000, 0.00001),
    ]
    
    for case_name, risk_amount, stop_distance in edge_cases:
        trader.mt5_connected = False
        try:
            lot_size = trader.calculate_position_size(risk_amount, stop_distance)
            status = "✅ Handled" if 0.01 <= lot_size <= 10.0 else f"⚠️  {lot_size:.4f}"
            print(f"{case_name:12}: Risk=${risk_amount:6}, Stop={stop_distance:.5f} → {lot_size:.4f} lots ({status})")
        except Exception as e:
            print(f"{case_name:12}: ❌ ERROR - {e}")
    
    print("\n🧪 REALISTISCHES TRADING SZENARIO:")
    print("EURUSD Trading mit €10.000 Account, 2% Risk")
    
    # Realistisches Szenario
    account_balance_eur = 10000
    risk_per_trade = 0.02  # 2%
    stop_loss_pips = 50    # 50 Pips Stop Loss
    stop_distance = 0.0050  # 50 pips für EURUSD
    
    risk_amount = account_balance_eur * risk_per_trade  # €200 Risk
    
    trader.mt5_connected = False
    calculated_lots = trader.calculate_position_size(risk_amount, stop_distance)
    
    # Manuelle Berechnung zur Verifikation
    # Für EURUSD: 1 Pip = €10 bei 1 Lot
    # Risk €200 ÷ (50 Pips × €10/Pip) = €200 ÷ €500 = 0.4 Lots
    expected_lots = risk_amount / (stop_loss_pips * 10)  # €10 pro Pip bei EURUSD
    
    print(f"Account Balance: €{account_balance_eur:,}")
    print(f"Risk per Trade: {risk_per_trade*100}% = €{risk_amount}")
    print(f"Stop Loss: {stop_loss_pips} pips")
    print(f"Expected Lot Size: {expected_lots:.2f} lots")
    print(f"Calculated Lot Size: {calculated_lots:.2f} lots")
    
    difference = abs(calculated_lots - expected_lots)
    if difference < 0.1:
        print("✅ CALCULATION CORRECT!")
    else:
        print(f"❌ CALCULATION ERROR! Difference: {difference:.2f}")
        return False
    
    print("\n💰 MONETARY VALIDATION:")
    actual_risk = calculated_lots * stop_loss_pips * 10  # €10 per pip
    print(f"Actual Risk with calculated lots: €{actual_risk:.2f}")
    print(f"Target Risk: €{risk_amount:.2f}")
    
    risk_difference = abs(actual_risk - risk_amount)
    if risk_difference < risk_amount * 0.1:  # Within 10%
        print("✅ RISK CALCULATION ACCURATE!")
        return True
    else:
        print(f"❌ RISK CALCULATION INACCURATE! Difference: €{risk_difference:.2f}")
        return False

if __name__ == "__main__":
    success = test_position_sizing_detailed()
    
    if success:
        print("\n🎉 POSITIONSBERECHNUNG FUNKTIONIERT KORREKT!")
    else:
        print("\n🚨 POSITIONSBERECHNUNG HAT PROBLEME!")
        
    print("\n" + "="*60)