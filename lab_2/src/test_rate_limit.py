#!/usr/bin/env python3
import sys
import time
import requests
from collections import Counter

SERVER_URL = "http://127.0.0.1:8080"


def test_single_client_spam():
    print("=" * 60)
    print("SINGLE CLIENT RATE LIMIT TEST")
    print("=" * 60)
    print()
    print("Configuration:")
    print("  Rate limit: 5 req/s per IP")
    print("  Test: 30 requests at 10 req/s (double the limit)")
    print()
    print("Expected result:")
    print("  ~50% successful (200)")
    print("  ~50% rate limited (429)")
    print()
    print("=" * 60)
    print()
    
    statuses = []
    start_time = time.time()
    
    print("Sending requests...")
    for i in range(30):
        try:
            response = requests.get(f"{SERVER_URL}/", timeout=5)
            status = response.status_code
            statuses.append(status)
            
            symbol = "✓" if status == 200 else "✗"
            print(f"  Request {i+1:2d}: {status} {symbol}")
            
        except Exception as e:
            statuses.append(f"ERROR")
            print(f"  Request {i+1:2d}: ERROR - {e}")
        
        if i < 29:
            time.sleep(0.1)  # 10 req/s
    
    total_time = time.time() - start_time
    
    print()
    print("=" * 60)
    print("RESULTS")
    print("=" * 60)
    print()
    
    status_counts = Counter(statuses)
    successful = status_counts.get(200, 0)
    rate_limited = status_counts.get(429, 0)
    errors = sum(1 for s in statuses if isinstance(s, str))
    
    print(f"Total requests: 30")
    print(f"Duration: {total_time:.2f}s")
    print(f"Actual rate: {30/total_time:.2f} req/s")
    print()
    print(f"Results:")
    print(f"  Successful (200):    {successful:2d} ({successful/30*100:5.1f}%)")
    print(f"  Rate limited (429):  {rate_limited:2d} ({rate_limited/30*100:5.1f}%)")
    if errors:
        print(f"  Errors:              {errors:2d} ({errors/30*100:5.1f}%)")
    print()
    
    print("Interpretation:")
    if rate_limited >= 10:
        print("  ✓ Rate limiting is working correctly!")
        print("  ✓ Server blocked excessive requests from this IP")
    else:
        print("  ✗ Rate limiting may not be working as expected")
        print("  ✗ Expected more 429 responses")
    
    print()
    print("=" * 60)


def test_burst_then_normal():
    print("=" * 60)
    print("BURST RECOVERY TEST")
    print("=" * 60)
    print()
    print("Phase 1: Burst 10 requests immediately (trigger rate limit)")
    print("Phase 2: Wait 2 seconds")
    print("Phase 3: Send 5 more requests at normal rate")
    print()
    print("=" * 60)
    print()
    
    statuses = []
    
    # Phase 1: Burst
    print("Phase 1: Bursting 10 requests...")
    for i in range(10):
        response = requests.get(f"{SERVER_URL}/", timeout=5)
        status = response.status_code
        statuses.append(('burst', status))
        symbol = "✓" if status == 200 else "✗"
        print(f"  Burst {i+1:2d}: {status} {symbol}")
    
    # Phase 2: Wait
    print()
    print("Phase 2: Waiting 2 seconds for rate limit to reset...")
    time.sleep(2)
    
    # Phase 3: Normal
    print()
    print("Phase 3: Sending 5 requests at 4 req/s (under limit)...")
    for i in range(5):
        response = requests.get(f"{SERVER_URL}/", timeout=5)
        status = response.status_code
        statuses.append(('normal', status))
        symbol = "✓" if status == 200 else "✗"
        print(f"  Normal {i+1}: {status} {symbol}")
        if i < 4:
            time.sleep(0.25)
    
    print()
    print("=" * 60)
    print("RESULTS")
    print("=" * 60)
    print()
    
    burst_statuses = [s for phase, s in statuses if phase == 'burst']
    normal_statuses = [s for phase, s in statuses if phase == 'normal']
    
    burst_200 = burst_statuses.count(200)
    burst_429 = burst_statuses.count(429)
    normal_200 = normal_statuses.count(200)
    normal_429 = normal_statuses.count(429)
    
    print(f"Burst phase (10 requests immediately):")
    print(f"  Successful (200):   {burst_200:2d} ({burst_200/10*100:5.1f}%)")
    print(f"  Rate limited (429): {burst_429:2d} ({burst_429/10*100:5.1f}%)")
    print()
    
    print(f"Normal phase (5 requests at 4 req/s after cooldown):")
    print(f"  Successful (200):   {normal_200:2d} ({normal_200/5*100:5.1f}%)")
    print(f"  Rate limited (429): {normal_429:2d} ({normal_429/5*100:5.1f}%)")
    print()
    
    print("Interpretation:")
    if burst_429 >= 5 and normal_200 >= 4:
        print("  ✓ Rate limiting works correctly!")
        print("  ✓ Burst was blocked, normal traffic allowed after cooldown")
    else:
        print("  ⚠ Unexpected behavior")
    
    print()
    print("=" * 60)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "burst":
        test_burst_then_normal()
    else:
        test_single_client_spam()
        
        print()
        print("TIP: Run 'python3 src/test_rate_limit_simple.py burst' to test recovery")
