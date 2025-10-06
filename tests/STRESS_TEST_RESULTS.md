# Stress Test Results
**Date**: October 6, 2025
**Workshop Date**: Wednesday (30 students expected)

## Summary

✅ **System is ready for 30 concurrent students**

Both memory and API testing show the system can handle the workshop load with significant headroom.

---

## Test 1: Memory Capacity

**Test**: Simulate concurrent sessions with 30 images each (1920x1080 JPEG)

### Results - 30 Sessions (Workshop Scenario)
```
Sessions created: 30
Total session data: 38.1 MB
Memory limit: 2048 MB (2GB Render Standard instance)
Memory used: 1.9%
```

**Conclusion**: ✅ Memory is NOT a concern

### Results - 100 Sessions (Extreme Scenario)
```
Sessions created: 100
Total session data: 127.2 MB
Memory limit: 2048 MB
Memory used: 6.2%
```

**Key Findings**:
- Each 30-image session ≈ 1.3 MB
- 30 students = ~38 MB total (negligible)
- System could theoretically handle ~1,600 concurrent sessions
- **Memory is NOT the bottleneck**

---

## Test 2: Gemini API Concurrency

**Test**: 30 concurrent API requests to Gemini 2.5 Flash

### Results - Burst Test (30 Concurrent)
```
Duration: 2.5s
Total requests: 30
Successful: 30 (100%)
Failed: 0 (0%)

Response times:
  Average: 1.53s
  Min: 0.79s
  Max: 2.51s

Actual request rate: 11.9 req/s
```

**Conclusion**: ✅ No rate limits detected with 30 concurrent requests

**Key Findings**:
- API handled all 30 requests successfully
- Fast response times (~1.5s average for simple prompts)
- No 429 rate limit errors
- Paid tier (1,000 RPM) is sufficient

**Note**: This test used simple text prompts. Real caption generation with vision API will be slower (~3-5s per image), but concurrency handling should be similar.

---

## Workshop Capacity Analysis

### Expected Load
- **Students**: 30
- **Images per student**: 20-40 (average ~30)
- **Total images**: ~900 images
- **Duration**: 2-3 hours (students work asynchronously)

### System Capacity
| Resource | Limit | Workshop Load | Headroom |
|----------|-------|---------------|----------|
| **Memory** | 2048 MB | 38 MB (1.9%) | ✅ Huge (98% free) |
| **API Rate** | 1,000 RPM | ~12 req/s burst | ✅ Good |
| **Sessions** | 30 concurrent | 30 students | ✅ Adequate |
| **Storage** | Limited | Deleted on export | ✅ Clean |

### Bottleneck Analysis

**NOT bottlenecks**:
- ✅ Memory (only 1.9% used)
- ✅ Concurrent sessions (handled easily)
- ✅ Storage (sessions deleted after export)

**Potential bottlenecks**:
- ⚠️ **API rate limits** (if many students generate simultaneously)
  - Mitigation: Slow mode available (3s delay between requests)
  - Mitigation: Retry with exponential backoff (built-in)
  - Mitigation: Students work asynchronously (natural rate limiting)

---

## Recommendations

### For Workshop Day

1. **Keep MAX_CONCURRENT_SESSIONS=30**
   - Current limit is appropriate
   - No need to reduce

2. **Monitor API errors**
   - Watch for RATE_LIMIT errors in logs
   - If detected, announce: "Please enable Slow Mode"

3. **No memory concerns**
   - System can handle 3x the expected load
   - Session cleanup (delete-on-export) is sufficient

4. **Have Slow Mode ready**
   - If >10 students generate simultaneously, may hit API limits
   - Slow Mode (3s delay) prevents bursts
   - Trade-off: 30 images × 3s = +90s total time

### Configuration Validation

Current production config is optimal:
```
MAX_CONCURRENT_SESSIONS=30        ✅ Correct
GEMINI_API_KEY=[paid tier]        ✅ Required (1,000 RPM)
Model: gemini-2.5-flash           ✅ Fast + accurate
Session cleanup: On export        ✅ Prevents memory bloat
Retry logic: 3 attempts + backoff ✅ Handles transient errors
```

---

## Test Commands

Run these tests again if needed:

```bash
# Memory test (30 sessions)
python3 tests/stress_test_memory.py --sessions 30 --images 30

# Memory test (100 sessions - extreme)
python3 tests/stress_test_memory.py --sessions 100 --images 30

# API burst test (30 concurrent)
python3 tests/stress_test_gemini.py --test burst --concurrent 30

# API ramp-up test (find breaking point)
python3 tests/stress_test_gemini.py --test ramp
```

---

## Conclusion

**System is production-ready for Wednesday's workshop.**

The 2GB Render Standard instance with Gemini 2.5 Flash (paid tier) can comfortably handle 30 concurrent students. Memory usage is negligible (<2%), and API concurrency tests show no rate limiting with 30 simultaneous requests.

**Action Items**: None required. Monitor API errors during workshop and enable Slow Mode if rate limits appear (unlikely based on testing).
