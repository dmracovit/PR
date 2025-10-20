#!/usr/bin/env python3
import sys
import time
import threading
import requests
from collections import Counter, defaultdict

SERVER_URL = "http://127.0.0.1:8080"


def spam_requests(client_name, num_requests, interval, results_dict):
    print(f"[{client_name}] Starting: {num_requests} requests, {interval}s interval ({1/interval:.1f} req/s)")
    
    statuses = []
    start_time = time.time()
    
    for i in range(num_requests):
        try:
            response = requests.get(f"{SERVER_URL}/", timeout=5)
            statuses.append(response.status_code)
        except Exception as e:
            statuses.append(f"ERROR: {e}")
        
        if i < num_requests - 1:
            time.sleep(interval)
    
    total_time = time.time() - start_time
    
    status_counts = Counter(statuses)
    successful = status_counts.get(200, 0)
    rate_limited = status_counts.get(429, 0)
    
    results_dict[client_name] = {
        'total': num_requests,
        'time': total_time,
        'statuses': dict(status_counts),
        'successful': successful,
        'rate_limited': rate_limited,
        'rate': 1/interval
    }
    
    print(f"[{client_name}] Completed in {total_time:.2f}s")


def test_rate_limiting():
    print("=" * 60)
    print("RATE LIMITING TEST")
    print("=" * 60)
    print()
    
    results = {}
    threads = []
    
    thread_a = threading.Thread(
        target=spam_requests,
        args=("Client A (Spammer)", 50, 0.1, results)
    )
    
    thread_b = threading.Thread(
        target=spam_requests,
        args=("Client B (Normal)", 20, 0.25, results)
    )
    
    thread_a.start()
    thread_b.start()
    
    thread_a.join()
    thread_b.join()
    
    print()
    print("=" * 60)
    print("RESULTS SUMMARY")
    print("=" * 60)
    print()
    
    for client_name in sorted(results.keys()):
        data = results[client_name]
        print(f"{client_name}:")
        print(f"  Request rate: {data['rate']:.1f} req/s")
        print(f"  Total requests: {data['total']}")
        print(f"  Duration: {data['time']:.2f}s")
        print(f"  Actual throughput: {data['total']/data['time']:.2f} req/s")
        print()
        print(f"  Results:")
        print(f"    Successful (200): {data['successful']} ({data['successful']/data['total']*100:.1f}%)")
        print(f"    Rate limited (429): {data['rate_limited']} ({data['rate_limited']/data['total']*100:.1f}%)")
        
        other = {k: v for k, v in data['statuses'].items() if k not in [200, 429]}
        if other:
            print(f"    Other: {other}")
        print()
    
    print("=" * 60)


if __name__ == "__main__":
    print("This test simulates two clients with different request rates:")
    print("- Client A: 10 req/s (spammer - will be rate limited)")
    print("- Client B: 4 req/s (normal user - should work fine)")
    print()
    print("Note: Both clients are running from the same machine (same IP)")
    print("To test per-IP rate limiting, run this from different machines")
    print()
    input("Press Enter to start test...")
    print()
    
    test_rate_limiting()
