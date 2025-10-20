#!/usr/bin/env python3
import sys
import time
import threading
import requests
import os
import random
from collections import Counter

SERVER_URL = "http://127.0.0.1:8080"


def find_files(directory):
    files = []
    for root, _, filenames in os.walk(directory):
        for filename in filenames:
            rel_path = os.path.relpath(os.path.join(root, filename), directory)
            files.append("/" + rel_path.replace("\\", "/"))
    return files


def make_request(url, results, index):
    try:
        start = time.time()
        response = requests.get(url, timeout=15)
        elapsed = time.time() - start
        results[index] = {
            'status': response.status_code,
            'time': elapsed,
            'error': None,
            'url': url
        }
    except Exception as e:
        results[index] = {
            'status': None,
            'time': 0,
            'error': str(e),
            'url': url
        }


def test_concurrent_requests(num_requests=10, content_dir=None):
    files = []
    if content_dir:
        if not os.path.exists(content_dir):
            print(f"Error: Directory '{content_dir}' not found")
            return
        files = find_files(content_dir)
        if not files:
            print(f"Error: No files found in '{content_dir}'")
            return
        print(f"Found {len(files)} files in {content_dir}")
        print(f"Testing with {num_requests} concurrent requests to random files")
    else:
        print(f"Testing with {num_requests} concurrent requests to {SERVER_URL}/")
    
    print("=" * 60)
    
    results = [None] * num_requests
    threads = []
    
    start_time = time.time()
    
    for i in range(num_requests):
        if files:
            target_path = random.choice(files)
        else:
            target_path = "/"
        
        url = f"{SERVER_URL}{target_path}"
        thread = threading.Thread(target=make_request, args=(url, results, i))
        thread.daemon = True
        thread.start()
        threads.append(thread)
    
    for thread in threads:
        thread.join(timeout=20)
    
    total_time = time.time() - start_time
    
    status_counts = Counter()
    response_times = []
    errors = 0
    
    for result in results:
        if result is None:
            errors += 1
        elif result['error']:
            errors += 1
        else:
            status_counts[result['status']] += 1
            response_times.append(result['time'])
    
    print(f"\nRESULTS:")
    print(f"  Total requests: {num_requests}")
    print(f"  Total time: {total_time:.2f}s")
    print(f"  Throughput: {num_requests / total_time:.2f} req/s")
    print()
    
    print(f"  Status codes:")
    for status, count in sorted(status_counts.items()):
        print(f"    {status}: {count}")
    if errors > 0:
        print(f"    Errors: {errors}")
    print()
    
    if response_times:
        print(f"  Response times:")
        print(f"    Min: {min(response_times):.2f}s")
        print(f"    Max: {max(response_times):.2f}s")
        print(f"    Avg: {sum(response_times)/len(response_times):.2f}s")
    
    print()
    print("=" * 60)
    print()
    
    return total_time


def main():
    if len(sys.argv) < 2:
        print("Usage: python test_performance.py <num_requests> [content_dir]")
        print("Examples:")
        print("  python test_performance.py 10              # 10 requests to /")
        print("  python test_performance.py 100 content     # 100 requests to random files in content/")
        sys.exit(1)
    
    try:
        num_requests = int(sys.argv[1])
        content_dir = sys.argv[2] if len(sys.argv) > 2 else None
    except ValueError:
        print("Error: num_requests must be an integer")
        sys.exit(1)
    
    test_concurrent_requests(num_requests, content_dir)


if __name__ == "__main__":
    main()
