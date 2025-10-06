# How to Monitor Stress Tests

## What You'll See During Tests

### Memory Test Output

**Normal (Safe):**
```
✅ Session 15/30:
  Session size: 78.3 MB
  Total sessions size: 1174.5 MB
  Process memory: 1220.8 MB (59.6%)
  Memory increase: 1175.6 MB
```
→ Keep going, everything fine

**Warning (Watch Closely):**
```
🟡 Session 22/30:
  Session size: 78.3 MB
  Total sessions size: 1723.6 MB
  Process memory: 1780.2 MB (86.9%)
  Memory increase: 1735.0 MB

🟡 WARNING: Over 75% memory usage
```
→ Getting close to limit, but still safe

**Danger (Test Stops):**
```
🔴 Session 24/30:
  Session size: 78.3 MB
  Total sessions size: 1879.2 MB
  Process memory: 1924.8 MB (94.0%)
  Memory increase: 1879.6 MB

🔴 DANGER: Approaching 2GB limit!
  Stopped at 24 sessions for safety
  Current: 1924.8 MB / 2048 MB
```
→ Test stops automatically - found the limit!

**Crash (Unlikely, test stops before this):**
```
💥 MEMORY ERROR at session 28
  Error: Out of memory
```
→ System actually ran out of RAM

---

### Gemini API Test Output

**Normal (No Problems):**
```
RESULTS: Concurrent Burst
================================================================================
Duration: 8.3s
Total requests: 30
Successful: 30 (100.0%)
Failed: 0 (0.0%)

Response times:
  Average: 2.45s
  Min: 1.82s
  Max: 5.67s

RECOMMENDATIONS:
  ✅ No rate limits detected
  ✅ Can handle 30 requests in 8.3s
```
→ All good! No API limits hit

**Rate Limit Hit:**
```
RESULTS: Concurrent Burst
================================================================================
Duration: 12.5s
Total requests: 30
Successful: 25 (83.3%)
Failed: 5 (16.7%)

⚠️  RATE LIMIT ERRORS: 5

Errors by type:
  ResourceExhausted: 5

RECOMMENDATIONS:
  ⚠️  Hit rate limits!
  ✅ Safe concurrent limit: ~20 requests
```
→ Found the API limit! Use lower concurrency

---

## How to Run Tests Safely

### 1. Memory Test (Safe - Stops Automatically)

```bash
# Start conservative
python3 tests/stress_test_memory.py --sessions 20 --images 30

# If that passes, try workshop load
python3 tests/stress_test_memory.py --sessions 30 --images 30

# Can press Ctrl+C anytime to stop
```

**What to watch:**
- Green checkmarks ✅ = safe
- Yellow warnings 🟡 = getting close
- Red danger 🔴 = test stops automatically

**The test will STOP before crashing:**
- Stops at 1.8GB (90% of 2GB limit)
- You can Ctrl+C anytime
- No files written to disk

### 2. Gemini API Test (Uses Real API Quota)

```bash
# Start small to avoid wasting quota
python3 tests/stress_test_gemini.py --test burst --concurrent 10

# If no errors, try workshop load
python3 tests/stress_test_gemini.py --test burst --concurrent 30

# Full test (uses more quota)
python3 tests/stress_test_gemini.py --test ramp
```

**What to watch:**
- `Successful: X (100%)` = no API limits
- `RATE LIMIT ERRORS: X` = found limit
- `ResourceExhausted` = Google is throttling

**Cost of testing:**
- Each test prompt is tiny (~10 tokens)
- 30 requests ≈ 300 tokens ≈ $0.0001
- Very cheap to test

---

## Interpreting Final Results

### Memory Test Final Output

```
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

**What this means:**
- System can handle **24 sessions** max
- **Safe limit is ~19** (80% of max for safety margin)
- **Action:** Set `MAX_CONCURRENT_SESSIONS = 19` in app.py

---

### Gemini API Test Final Output

```
================================================================================
RECOMMENDATIONS:
  ⚠️  Hit rate limits!
  ✅ Safe concurrent limit: ~20 requests
```

**What this means:**
- API breaks at ~25 concurrent requests
- **Safe limit is 20**
- **Action:** Either:
  - Set `MAX_CONCURRENT_SESSIONS = 20`, OR
  - Enable slow mode by default (spreads requests over time)

---

## Decision Matrix

| Memory Result | API Result | Recommendation |
|--------------|-----------|----------------|
| ✅ Handles 30+ | ✅ Handles 30+ | Keep MAX_CONCURRENT_SESSIONS=30 |
| ✅ Handles 30+ | ⚠️ Fails at 25 | Set MAX=20, add slow mode warning |
| ⚠️ Fails at 20 | ✅ Handles 30+ | Set MAX=15 (memory is bottleneck) |
| ⚠️ Fails at 20 | ⚠️ Fails at 20 | Set MAX=15, enable slow mode default |

---

## If You Don't Want to Test

**Conservative Safe Fallback:**
```python
# app.py
MAX_CONCURRENT_SESSIONS = 15  # Very safe

# Announce at workshop:
# "Server supports 15 concurrent users"
# "Work in pairs or enable Slow Mode if you see errors"
```

This is guaranteed to work, but you might be able to support more.

---

## Quick Pre-Workshop Test (5 minutes)

If you're short on time, just run this:

```bash
# Quick memory check (10 sessions)
python3 tests/stress_test_memory.py --sessions 10 --images 30

# Quick API check (10 concurrent)
python3 tests/stress_test_gemini.py --test burst --concurrent 10
```

If both show ✅ green checkmarks → Probably fine for 30 students

---

## What the Tests DON'T Do

- ❌ Don't write files to disk (memory test is in-memory only)
- ❌ Don't affect your production sessions
- ❌ Don't modify any code
- ❌ Don't crash your system (stops before crash)
- ❌ Don't waste API quota (uses tiny test prompts)

**You can run them safely!**
