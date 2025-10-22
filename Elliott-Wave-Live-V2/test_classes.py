import sys
print('Reloading module...')
if 'elliott_wave_engine_original' in sys.modules:
    del sys.modules['elliott_wave_engine_original']
from elliott_wave_engine_original import Impulse, ABC, Dir
i = Impulse(Dir.UP, [1,2,3,4,5,6])
print('Wave 3 end:', i.wave_3_end)
print('Wave 5 end:', i.wave_5_end)
a = ABC(Dir.DOWN, [1,2,3,4])
print('A end:', a.a_end)
print('C end:', a.c_end)
print('Test complete!')