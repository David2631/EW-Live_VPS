"""
Test script for the new candle close timing system
"""
import datetime
import time

def wait_for_candle_close():
    """Wait until 5 seconds after the next minute starts (candle close + buffer)"""
    now = datetime.datetime.now()
    
    # Calculate next minute at :05 seconds
    next_minute = now.replace(second=0, microsecond=0) + datetime.timedelta(minutes=1)
    target_time = next_minute.replace(second=5)  # Wait until :05 seconds
    
    # Calculate wait time
    wait_seconds = (target_time - now).total_seconds()
    
    if wait_seconds > 0:
        print(f"⏰ Current time: {now.strftime('%H:%M:%S.%f')[:-3]}")
        print(f"⏰ Target time: {target_time.strftime('%H:%M:%S')}")
        print(f"⏰ Waiting {wait_seconds:.1f}s for next candle close")
        return wait_seconds
    else:
        # We're already past the target, wait for next cycle
        target_time += datetime.timedelta(minutes=1)
        wait_seconds = (target_time - datetime.datetime.now()).total_seconds()
        print(f"⏰ Current time: {now.strftime('%H:%M:%S.%f')[:-3]}")
        print(f"⏰ Target time: {target_time.strftime('%H:%M:%S')}")
        print(f"⏰ Waiting {wait_seconds:.1f}s for next candle close")
        return wait_seconds

if __name__ == "__main__":
    print("🧪 Testing Candle Close Timing Logic")
    print("=" * 50)
    
    for i in range(3):
        print(f"\nTest {i+1}:")
        wait_time = wait_for_candle_close()
        
        if wait_time < 10:  # Only wait if it's less than 10 seconds for testing
            time.sleep(wait_time + 0.1)  # Small buffer
            print(f"✅ Candle close reached at {datetime.datetime.now().strftime('%H:%M:%S.%f')[:-3]}")
        else:
            print(f"⏭️ Skipping wait (would be {wait_time:.1f}s)")
        
        time.sleep(1)  # Brief pause between tests