from elliott_wave_engine_original import ElliottEngine, Impulse, Dir, Pivot
import numpy as np

# Test direct ElliottEngine class
engine = ElliottEngine(0.02, 1.0, 3.0)

# Create test pivots manually
pivots = [
    Pivot(0, 1.1000, 'L'), 
    Pivot(1, 1.1100, 'H'),
    Pivot(2, 1.1050, 'L'),
    Pivot(3, 1.1150, 'H'), 
    Pivot(4, 1.1080, 'L'),
    Pivot(5, 1.1200, 'H')
]

close = np.array([1.1000, 1.1100, 1.1050, 1.1150, 1.1080, 1.1200])
atr = np.array([0.001, 0.002, 0.001, 0.002, 0.001, 0.002])

print("Testing direct ElliottEngine...")
impulses = engine.detect_impulses(pivots, close, atr)
print(f"Found {len(impulses)} impulses")

for i, impulse in enumerate(impulses):
    print(f"Impulse {i}:")
    print(f"  Type: {type(impulse)}")
    print(f"  Direction: {impulse.direction}")
    print(f"  Has confidence attr: {hasattr(impulse, 'confidence')}")  
    print(f"  Has wave_5_end attr: {hasattr(impulse, 'wave_5_end')}")
    if hasattr(impulse, 'confidence'):
        print(f"  Confidence: {impulse.confidence}")
    if hasattr(impulse, 'wave_5_end'):
        print(f"  Wave 5 end: {impulse.wave_5_end}")