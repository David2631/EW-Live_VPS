print("=== DEBUGGING IMPORT ISSUE ===")

# Test 1: Check signal generator import
try:
    from signal_generator import SignalGenerator
    sg = SignalGenerator()
    print(f"Signal Generator Elliott Engine: {type(sg.elliott_engine)}")
    print(f"Signal Generator Elliott Engine file: {sg.elliott_engine.__class__.__module__}")
except Exception as e:
    print(f"Signal Generator import error: {e}")

# Test 2: Check direct import
try:
    from elliott_wave_engine_original import Impulse, ABC
    i = Impulse(None, [1,2,3,4,5,6])
    a = ABC(None, [1,2,3,4])
    print(f"Direct Impulse type: {type(i)}")
    print(f"Direct Impulse has wave_3_end: {hasattr(i, 'wave_3_end')}")
    print(f"Direct ABC has a_end: {hasattr(a, 'a_end')}")
except Exception as e:
    print(f"Direct import error: {e}")

# Test 3: Check what's actually being created by signal generator
try:
    import pandas as pd
    data = pd.DataFrame({
        'open': [1.1000] * 100,
        'high': [1.1005] * 100, 
        'low': [1.0995] * 100,
        'close': [1.1002] * 100,
        'date': pd.date_range('2025-01-01', periods=100, freq='h')
    })
    
    result = sg.elliott_engine.analyze_waves(data)
    if result and result.get('impulses'):
        impulse = result['impulses'][0]
        print(f"Generated Impulse type: {type(impulse)}")  
        print(f"Generated Impulse module: {impulse.__class__.__module__}")
        print(f"Generated Impulse has wave_3_end: {hasattr(impulse, 'wave_3_end')}")
        print(f"Generated Impulse __dict__: {impulse.__dict__}")
    else:
        print("No impulses generated in test")
        
except Exception as e:
    print(f"Signal generator test error: {e}")
    import traceback
    traceback.print_exc()