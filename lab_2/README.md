# Lab 2: Multithreaded HTTP Server

**Student Name:** Racovitsa Dumitru  
**Group:** FAF-233  
**Date:** October 2025

---

## Part 1: Performance Comparison Between Single-threaded and Multi-threaded Servers

### 1.1 Single-threaded Server Performance

**Test Setup:**
- Number of requests: 10
- Processing mode: Sequential

**Commands:**

Starting the server:
```bash
docker run -it --rm -p 8080:8080 -v $(pwd)/content:/srv/site \
  lab_2-http-server python server.py /srv/site --single-threaded
```

Running the test:

**Result Screenshot:**

![Single-threaded Performance](./img/single_threaded.png.png)

**Observed Result:** 10 requests completed in approximately 10 seconds (sequential processing)

---

### 1.2 Multi-threaded Server Performance

**Test Setup:**
- Number of requests: 10
- Processing mode: Concurrent

**Commands:**

Starting the server:
```bash
docker-compose up -d
```

Running the test:
```bash
python3 src/test_performance.py 10
```

**Result Screenshot:**

![Multi-threaded Performance](./img/multi_threaded.png.png)

**Observed Result:** 10 requests completed in approximately 1 second (concurrent processing)

**Performance Improvement:** ~10x faster than single-threaded approach

---

## Part 2: Hit Counter and Race Condition Analysis

### 2.1 Demonstrating the Race Condition

**Test Configuration:**
- Thread-safe counter: Disabled (`USE_THREAD_SAFE_COUNTER = False`)
- Number of requests: 100
- Execution mode: Concurrent

**Result Screenshots:**

![Race Condition - No Lock](./img/race_no_lock.png)

![Race Condition - No Lock 2](./img/race_no_lock2.png)

**Observed Result:** Counter displays significantly less than 100 hits due to race condition causing lost updates

---

### 2.2 Race Condition Code Analysis

**Problematic Code (maximum 4 lines):**

```python
old_value = request_counter[normalized]
time.sleep(0.01)
request_counter[normalized] = old_value + 1
```

**Explanation:** 
Multiple threads simultaneously read the same `old_value` before any thread completes its write operation, resulting in lost updates to the counter.

---

### 2.3 Solution: Thread-Safe Implementation

**Fixed Code with Lock:**

```python
with counter_lock:
    request_counter[normalized] += 1
```

**Test Configuration:**
- Thread-safe counter: Enabled (`USE_THREAD_SAFE_COUNTER = True`)
- Number of requests: 100
- Execution mode: Concurrent

**Result Screenshots:**

![Fixed with Lock](./img/race_lock.png)

![Fixed with Lock 2](./img/race_lock2.png)

**Observed Result:** Counter accurately displays exactly 100 hits (correct behavior)

---

## Part 3: Rate Limiting Implementation

### 3.1 Single Client Spam Test

**Server Configuration:**
- Rate limit threshold: 5 requests per second per IP
- Rate limiting algorithm: Sliding window

**Test Configuration:**
- Client request rate: 10 req/s (exceeds limit by 2x)
- Total requests: 30
- Expected behavior: Approximately 50% blocked

**Test Execution:**

```bash
python3 src/test_rate_limit.py
```

**Result Screenshots:**

![Rate Limiting Test](./img/rate_limit_test.png)

![429 Responses](./img/429.png)

---

### 3.2 Response Statistics and Analysis

**Single Client Results (10 req/s exceeds 5 req/s limit):**
- Successful requests (HTTP 200): ~50%
- Rate limited requests (HTTP 429): ~50%

**Analysis:** 
The client attempts to send 10 requests per second, but the server enforces a limit of 5 requests per second. Consequently, approximately half of the requests are blocked and receive 429 "Too Many Requests" responses, demonstrating effective rate limiting.

---

## Conclusion

### Key Achievements

This laboratory work successfully demonstrates three fundamental concepts in concurrent network programming:

1. **Multithreading Benefits:** 
   - Achieved approximately 10x performance improvement through concurrent request handling
   - Demonstrated clear advantage of multi-threaded architecture over single-threaded approach

2. **Race Condition Prevention:** 
   - Illustrated the critical importance of thread synchronization mechanisms (locks)
   - Showed how unsynchronized access to shared state leads to data corruption
   - Implemented proper locking to ensure data integrity

3. **Rate Limiting Implementation:** 
   - Developed thread-safe per-IP request throttling mechanism
   - Successfully prevented abuse scenarios while maintaining service availability
   - Utilized sliding window algorithm for accurate rate enforcement

### Technical Summary

All required features have been implemented successfully with appropriate thread safety mechanisms, including mutual exclusion locks for counter protection and rate limiter synchronization.
