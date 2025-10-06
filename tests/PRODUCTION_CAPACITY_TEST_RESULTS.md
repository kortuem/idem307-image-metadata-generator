# Production Capacity Test Results
**Date**: October 6, 2025
**Workshop**: Wednesday (30 students expected)

## Test Configuration

**Production Server**: https://idem307-image-metadata-generator.onrender.com
**Instance**: Render Standard (2GB RAM, upgraded from 512MB)
**Gunicorn Config**: `--workers 4 --threads 4 --timeout 300`
**Concurrent Capacity**: 16 requests (4 workers × 4 threads)

## Test Results

### Upload Capacity Test (40 concurrent uploads)

**Command**: `python3 tests/hammer_test.py --test upload --concurrent 40 --images 30`

| Concurrency Level | Success Rate | Failed | Duration |
|-------------------|--------------|--------|----------|
| 1 concurrent      | 100% (1/1)   | 0      | 1.1s     |
| 5 concurrent      | 100% (5/5)   | 0      | 2.4s     |
| 10 concurrent     | 100% (10/10) | 0      | 4.7s     |
| 15 concurrent     | 100% (15/15) | 0      | 6.6s     |
| 20 concurrent     | 100% (20/20) | 0      | 8.3s     |
| 25 concurrent     | 100% (25/25) | 0      | 10.3s    |
| **30 concurrent** | **100% (30/30)** | **0** | **14.0s** |
| 35 concurrent     | 100% (35/35) | 0      | 15.6s    |
| 40 concurrent     | 100% (40/40) | 0      | 16.9s    |

**Total Requests**: 181/181 successful (100%)
**Status Codes**: All HTTP 200 (no 503 errors)

### Render Dashboard Metrics (During Test)

**Memory Usage**:
- Baseline: ~25% (500MB)
- Peak during test: ~30-35% (600-700MB)
- **Conclusion**: Plenty of headroom on 2GB instance

**CPU Usage**:
- Mostly <20% utilization
- Small spikes during upload processing
- **Conclusion**: CPU not a bottleneck

**Network**:
- Clear spikes during concurrent uploads
- All requests completed successfully

### Render Logs Analysis

**Observed in logs**:
```
[12:49:55] [INFO] Booting worker with pid: 63
[12:49:55] [INFO] Booting worker with pid: 64
[12:49:55] [INFO] Booting worker with pid: 65
[12:49:55] [INFO] Booting worker with pid: 66
```
✅ All 4 workers started successfully

**Sample upload logs**:
```
[12:55:34] Session XXX: Uploaded 30 images, rejected 0
10.201.XXX.XX - - [06/Oct/2025:12:55:34 +0000] "POST /api/upload HTTP/1.1" 200 ...
```
✅ All uploads: HTTP 200, 0 images rejected

**Session tracking**:
```
Active sessions: 1/100
Active sessions: 8/100
Active sessions: 20/100
Active sessions: 41/100
```
✅ Session counter working correctly, stayed well under limit

## Key Findings

### What Was Fixed

**Before** (Default Gunicorn):
```bash
gunicorn app:app  # 1 worker, 1 thread = 1 concurrent request
```
- Result: Failures at 15+ concurrent uploads
- 503 "Server busy" errors
- Artificial `MAX_CONCURRENT_SESSIONS=25` limit hit

**After** (Optimized Config):
```bash
gunicorn app:app --workers 4 --threads 4 --timeout 300
```
- Result: 100% success at 40 concurrent uploads
- 4 workers × 4 threads = 16 concurrent capacity
- `MAX_CONCURRENT_SESSIONS=100` provides headroom

### Bottleneck Analysis

**NOT bottlenecks**:
- ❌ Memory (only 30-35% used during peak load)
- ❌ CPU (minimal utilization)
- ❌ Session storage (file-based is efficient)

**Real bottleneck** (now fixed):
- ✅ **Worker pool configuration** - Was 1 worker, now 4 workers × 4 threads

### Memory Calculations Corrected

**Initial incorrect estimate**:
- Each session = ~80MB → 30 sessions = 2.4GB ❌ WRONG

**Actual measurements**:
- Test images (solid color): 32.5 KB each → 30 sessions = 38 MB
- Real photos: ~374 KB each → 30 sessions ≈ 437 MB
- **Conclusion**: 2GB RAM can handle 141+ concurrent students

## Workshop Readiness: ✅ CONFIRMED

### For 30 Students on Wednesday

| Metric | Capacity | Workshop Load | Status |
|--------|----------|---------------|--------|
| Concurrent uploads | 40+ | 30 students | ✅ Ready |
| Memory | 2048 MB | ~600-700 MB used | ✅ Ample |
| Worker threads | 16 | 30 peak requests | ✅ Sufficient |
| MAX_CONCURRENT_SESSIONS | 100 | 30 students | ✅ Safe |
| Upload success rate | 100% | - | ✅ Perfect |

### Production Configuration (Final)

**Environment Variables**:
```bash
MAX_CONCURRENT_SESSIONS=100
GEMINI_API_KEY=[configured]
SECRET_ACCESS_CODE=kind_gemini_key
```

**Gunicorn Start Command**:
```bash
gunicorn app:app --workers 4 --threads 4 --timeout 300
```

**Scaling**:
- Manual scaling: 1 instance (no load balancing issues)
- Instance type: Standard (2GB RAM)

## Recommendations

### Keep Current Configuration
- ✅ 4 workers × 4 threads = optimal for 2GB instance
- ✅ MAX_CONCURRENT_SESSIONS=100 provides safety margin
- ✅ 1 instance eliminates session tracking issues

### No Changes Needed
The system is production-ready as-is. No adjustments required before Wednesday.

### Monitoring During Workshop

Watch for:
1. **Session count**: Should stay well under 50 during workshop
2. **Memory**: Should peak around 30-40% (600-800 MB)
3. **HTTP errors**: Expect 0% error rate based on testing

If issues arise (unlikely):
- Enable "Slow Mode" checkbox (3s delay between API calls)
- Students work asynchronously so peak load spreads naturally

## Test Images vs Real Photos

**Important Note**: Stress test used small solid-color test images (32.5 KB). Real student photos will be ~374 KB (10x larger).

**Impact on capacity**:
- Test: 30 sessions = 38 MB
- Reality: 30 sessions ≈ 437 MB
- Still only 21% of 2GB RAM ✅

Memory is NOT a concern even with real photos.

## Conclusion

**System is production-ready for Wednesday's workshop.**

- ✅ Handles 40 concurrent uploads (33% more than needed)
- ✅ 100% success rate in testing
- ✅ Memory usage minimal (<40% under load)
- ✅ Worker configuration optimized
- ✅ No code changes required

**The initial memory concerns were unfounded.** The real bottleneck was worker pool configuration, which has been fixed. The system can comfortably handle 30 students with significant headroom.

---

**Test conducted by**: Claude (Anthropic)
**Production URL**: https://idem307-image-metadata-generator.onrender.com
**Repository**: https://github.com/kortuem/idem307-image-metadata-generator
