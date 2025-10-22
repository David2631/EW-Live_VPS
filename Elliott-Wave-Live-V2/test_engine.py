from elliott_wave_engine_original import ElliottWaveEngine, Dir
import pandas as pd
import numpy as np

# Test the engine directly
engine = ElliottWaveEngine()

# Create sample data
data = pd.DataFrame({
    'open': [1.1000, 1.1010, 1.1020, 1.1030, 1.1040] * 20,
    'high': [1.1005, 1.1015, 1.1025, 1.1035, 1.1045] * 20,
    'low': [1.0995, 1.1005, 1.1015, 1.1025, 1.1035] * 20,
    'close': [1.1002, 1.1012, 1.1022, 1.1032, 1.1042] * 20,
    'date': pd.date_range('2025-01-01', periods=100, freq='H')
})

print("Testing engine...")
try:
    result = engine.analyze_waves(data)
    if result:
        impulses = result.get('impulses', [])
        print(f"Found {len(impulses)} impulses")
        for i, impulse in enumerate(impulses[:3]):  # Test first 3
            print(f"Impulse {i}:")
            print(f"  Direction: {impulse.direction}")
            print(f"  Confidence: {getattr(impulse, 'confidence', 'MISSING!')}")  
            print(f"  Wave 5 end: {getattr(impulse, 'wave_5_end', 'MISSING!')}")
            print(f"  Wave 3 end: {getattr(impulse, 'wave_3_end', 'MISSING!')}")
    else:
        print("No patterns found")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()