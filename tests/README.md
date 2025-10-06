# Stress Testing for Workshop Readiness

These stress tests help find the actual limits of your infrastructure before Wednesday's workshop.

## Available Tests

### 1. Memory Exhaustion Test (`stress_test_memory.py`)

**Purpose**: Find how many concurrent sessions the server can handle before running out of RAM.

**What it tests:**
- Creates N simulated student sessions with M images each
- Monitors memory usage in real-time
- Finds crash point or safe limit

**Usage:**
```bash
# Test 30 concurrent sessions with 30 images each
python3 tests/stress_test_memory.py --sessions 30 --images 30

# Test different scenarios
python3 tests/stress_test_memory.py --sessions 20 --images 40
python3 tests/stress_test_memory.py --sessions 40 --images 20

# Clean up test files
python3 tests/stress_test_memory.py --cleanup
```

**Expected Output:**
```
MEMORY STRESS TEST
Sessions: 30, Images per session: 30
================================================================================

Initial memory: 45.2 MB

Session 1/30:
  Session size: 78.3 MB
  Total sessions size: 78.3 MB
  Process memory: 123.5 MB
  Memory increase: 78.3 MB

...

⚠️  WARNING: Approaching 2GB limit!
  Stopped at 24 sessions

================================================================================
FINAL RESULTS:
  Sessions created: 24
  Total session data: 1879.2 MB
  Final process memory: 1924.8 MB
  Memory overhead: 45.6 MB
================================================================================

RECOMMENDATIONS:
  ⚠️  Could not create all 30 sessions
  ✅ Safe limit: ~19 concurrent sessions
```

---

### 2. Gemini API Concurrency Test (`stress_test_gemini.py`)

**Purpose**: Find Gemini API rate limits and concurrent request capacity.

**What it tests:**
- Sends concurrent API requests
- Tests sustained load over time
- Ramps up concurrency to find breaking point

**Usage:**
```bash
# Run all tests
python3 tests/stress_test_gemini.py

# Run specific test
python3 tests/stress_test_gemini.py --test burst --concurrent 30
python3 tests/stress_test_gemini.py --test sustained --rate 10 --duration 60
python3 tests/stress_test_gemini.py --test ramp

# Custom parameters
python3 tests/stress_test_gemini.py --test burst --concurrent 50
```

**Test Types:**

**1. Burst Test**
- Sends N requests simultaneously
- Finds if concurrent requests trigger rate limits

**2. Sustained Load Test**
- Sends X requests/second for Y seconds
- Tests if sustained load triggers throttling

**3. Ramp-Up Test**
- Gradually increases concurrency (5→50)
- Finds exact breaking point

**Expected Output:**
```
================================================================================
TEST 1: Concurrent Burst
Sending 30 requests simultaneously...
================================================================================

================================================================================
RESULTS: Concurrent Burst
================================================================================
Duration: 8.3s
Total requests: 30
Successful: 27 (90.0%)
Failed: 3 (10.0%)

⚠️  RATE LIMIT ERRORS: 3

Errors by type:
  ResourceExhausted: 3

Response times:
  Average: 2.45s
  Min: 1.82s
  Max: 5.67s

Actual request rate: 3.6 req/s

================================================================================
RECOMMENDATIONS:
  ⚠️  Hit rate limits!
  ✅ Safe concurrent limit: ~20 requests
```

---

## How to Use These Tests

### Before Wednesday's Workshop

**Step 1: Test Memory Limits**
```bash
# Find safe concurrent session limit
python3 tests/stress_test_memory.py --sessions 30 --images 30
```

**Step 2: Test Gemini API Limits**
```bash
# Find API rate limits
python3 tests/stress_test_gemini.py --test ramp
```

**Step 3: Adjust Configuration**
Based on test results, update `app.py`:
```python
# If memory test showed safe limit of 20:
MAX_CONCURRENT_SESSIONS = 20

# If API test showed issues at 25 concurrent:
# Consider enabling slow mode by default or lowering limit
```

---

## Interpreting Results

### Memory Test Results

**Good:**
- ✅ Can handle 30+ sessions
- ✅ Memory usage <1.5GB
- **Action**: Keep MAX_CONCURRENT_SESSIONS=30

**Concerning:**
- ⚠️  Stops at 15-20 sessions
- ⚠️  Memory >1.8GB
- **Action**: Lower MAX_CONCURRENT_SESSIONS to 15

**Critical:**
- 💥 Crashes before 15 sessions
- 💥 Memory >1.9GB
- **Action**: Lower to 10, consider Redis

### Gemini API Test Results

**Good:**
- ✅ No rate limit errors
- ✅ All requests successful
- **Action**: Current setup is fine

**Concerning:**
- ⚠️  3-5 rate limit errors
- ⚠️  Breaking point at 25-30 concurrent
- **Action**: Lower limit to 20 or enable slow mode

**Critical:**
- 💥 Many rate limit errors
- 💥 Breaking point <20 concurrent
- **Action**: Enable slow mode by default, lower to 15

---

## Safe Fallback Configuration

If tests show issues, use this conservative config:

```python
# app.py
MAX_CONCURRENT_SESSIONS = 15  # Conservative limit

# Announce at workshop:
# "If you see errors, enable Slow Mode checkbox"
# "Work in pairs if needed"
```

---

## Notes

- **Memory test**: Run locally, similar to Render Standard instance
- **API test**: Uses your actual Gemini API key, will count toward quota
- **Both tests**: Can be interrupted with Ctrl+C
- **Cleanup**: Memory test creates no persistent files with `--cleanup`

---

## Quick Test Before Workshop

**5-Minute Pre-Flight Check:**
```bash
# Quick memory test (5 sessions)
python3 tests/stress_test_memory.py --sessions 5 --images 30

# Quick API burst test
python3 tests/stress_test_gemini.py --test burst --concurrent 10
```

If both pass → You're ready for Wednesday ✅
