# Workshop Capacity - Final Configuration

**Status**: ✅ PRODUCTION READY
**Last Updated**: October 6, 2025
**Workshop Date**: Wednesday

---

## TL;DR - System is Ready

**Tested capacity**: 40 concurrent uploads (100% success)
**Workshop needs**: 30 students
**Headroom**: 33% extra capacity
**Memory usage**: <40% under full load
**Gemini API**: No rate limits detected

✅ No changes needed before Wednesday.

---

## Final Production Configuration

### Render Instance
- **Type**: Standard (2GB RAM) - upgraded from 512MB Starter
- **Scaling**: 1 instance (manual scaling)
- **Cost**: $25/month

### Gunicorn Configuration
```bash
gunicorn app:app --workers 4 --threads 4 --timeout 300
```
- **Workers**: 4 processes
- **Threads**: 4 per worker
- **Capacity**: 16 concurrent requests
- **Timeout**: 300 seconds (5 minutes for caption generation)

### Environment Variables
```
MAX_CONCURRENT_SESSIONS=100
GEMINI_API_KEY=[configured - paid tier]
SECRET_ACCESS_CODE=kind_gemini_key
```

---

## What We Learned from Testing

### Initial Concerns (WRONG)
❌ "Memory will be an issue"
- Thought each session = 80MB
- Predicted 30 sessions = 2.4GB (would exceed 2GB RAM)

### Reality (CORRECT)
✅ Memory is NOT an issue
- Each session = 1.3-15 MB (depending on image sizes)
- 30 sessions = 437 MB (only 21% of RAM)
- Peak usage during testing: 600-700 MB (30-35%)

### The Real Bottleneck (FIXED)
**Problem**: Default Gunicorn config
- 1 worker × 1 thread = only 1 concurrent request
- System queued/rejected requests at 15+ concurrent

**Solution**: Optimized worker configuration
- 4 workers × 4 threads = 16 concurrent requests
- 100% success rate at 40 concurrent uploads

---

## Test Results Summary

### Upload Capacity Test
| Concurrent Students | Success Rate | Duration |
|---------------------|--------------|----------|
| 10 | 100% | 4.7s |
| 20 | 100% | 8.3s |
| **30** | **100%** | **14.0s** |
| 40 | 100% | 16.9s |

### Gemini API Test
- **30 concurrent vision API requests**: 100% success
- **Average response time**: 14.75s per image
- **Rate limit**: None detected (1,000 RPM limit, used ~64 RPM)

### Memory Usage
- **Baseline**: 500 MB (25%)
- **Peak (40 concurrent)**: 700 MB (35%)
- **Headroom**: 1.3 GB (65%)

---

## Workshop Day Monitoring

### Expected Behavior
- **Session count**: Will climb to ~30, then stabilize
- **Memory**: Should peak around 600-800 MB (30-40%)
- **Response times**: 10-15s per upload (30 images)
- **API calls**: ~900 total (30 students × 30 images)

### Warning Signs to Watch
⚠️ **If you see these in Render logs**:

1. **Memory near 100%**: Unlikely, but would see slower responses
2. **503 errors**: Means >100 concurrent sessions (shouldn't happen)
3. **Gemini rate limit (429)**: Means >1,000 requests/minute (very unlikely)

### Emergency Actions
If issues occur (unlikely based on testing):

1. **Enable Slow Mode**: Tell students to check "Slow Mode" checkbox
   - Adds 3s delay between API calls
   - Reduces rate from ~64 to ~20 req/min

2. **Restart Service**: Clears stuck sessions if counter is wrong
   - Render Dashboard → Manual Deploy → Restart

3. **Check Render Dashboard**: Look at Memory/CPU/Network graphs

---

## Why This Configuration Works

### 1. Worker Pool Math
- **16 concurrent request slots** (4 workers × 4 threads)
- **30 students** uploading → max ~30 simultaneous uploads
- Some requests queue briefly, but all complete successfully
- Tested at 40 concurrent = 100% success

### 2. Memory Efficiency
- **File-based sessions** (`/tmp/sessions/*.json`)
- Session data written to disk immediately
- RAM only holds active request processing
- 30 sessions = ~437 MB (real photos) or ~38 MB (test images)

### 3. Gemini API Headroom
- **Paid tier**: 1,000 RPM limit
- **Peak workshop load**: ~150-225 RPM (15-22% of limit)
- Students work asynchronously = natural rate limiting

### 4. Session Management
- **MAX_CONCURRENT_SESSIONS=100**: Artificial safety limit
- **Auto-cleanup**: Sessions deleted after export
- **1 instance**: No load balancing = accurate session tracking

---

## Historical Issues (RESOLVED)

### Issue 1: 503 "Server Busy" at 15 Concurrent ✅ FIXED
**Cause**:
- Default Gunicorn (1 worker) + MAX_CONCURRENT_SESSIONS=25
- Only 1 request processed at a time

**Fix**:
- Changed to 4 workers × 4 threads
- Increased MAX_CONCURRENT_SESSIONS to 100

### Issue 2: Multiple Instances Causing Session Tracking Issues ✅ FIXED
**Cause**:
- 2 instances with load balancing
- Each instance had separate `active_sessions` counter

**Fix**:
- Scaled to 1 instance (manual scaling)
- Single source of truth for session tracking

### Issue 3: Memory Concerns ✅ UNFOUNDED
**Cause**:
- Incorrect calculation (80MB per session)
- Didn't account for file-based storage

**Reality**:
- Sessions are 1-15 MB each, written to disk
- Memory usage is minimal (<40% under load)

---

## File Organization

### Documentation
- `docs/WORKSHOP_CAPACITY.md` (this file) - Capacity planning and config
- `tests/PRODUCTION_CAPACITY_TEST_RESULTS.md` - Detailed test results
- `tests/STRESS_TEST_RESULTS.md` - Initial stress test findings
- `WORKSHOP_MONITORING.md` - Live monitoring guide (root)

### Test Scripts
- `tests/hammer_test.py` - Production upload capacity test
- `tests/stress_test_gemini.py` - Gemini API concurrency test
- `tests/stress_test_memory.py` - Local memory simulation
- `tests/stress_test_live.py` - Full workflow test (not used)
- `tests/stress_test_infrastructure.py` - Infrastructure test (not used)

### Test Results Archive
All tests saved in `tests/` directory for future reference.

---

## For Future Reference

### If You Need to Scale Up
**More than 50 students**:
```bash
# Increase workers (more memory intensive)
gunicorn app:app --workers 8 --threads 2 --timeout 300

# Or increase threads (less memory, more concurrency)
gunicorn app:app --workers 4 --threads 8 --timeout 300
```

### If You Need to Scale Down
**Budget constraints**:
- Downgrade to Starter (512MB): Can handle ~10-15 students
- Reduce workers: `--workers 2 --threads 4` (8 concurrent)

### Memory Troubleshooting
If memory becomes an issue (unlikely):
1. Check session cleanup is working (delete-on-export)
2. Verify MAX_CONCURRENT_SESSIONS limit
3. Look for stuck sessions in `/tmp/sessions/`
4. Consider Redis for session storage (shared across instances)

---

## Cost Analysis

**Current setup**:
- Render Standard: $25/month
- Gemini API (paid tier): ~$0.001 per image caption
- Workshop cost: 900 images × $0.001 = ~$0.90

**Total monthly cost**: ~$26

**Value**: Saves 12-18 hours of manual caption work per workshop.

---

## Conclusion

The system is **production-ready and over-provisioned** for Wednesday's workshop. Testing confirms:

✅ Can handle 40 concurrent students (33% more than needed)
✅ Memory has 60% headroom under load
✅ Gemini API has 85% headroom at peak
✅ 100% success rate in all tests

**No changes needed. Good to go!** 🚀

---

**Configuration Date**: October 6, 2025
**Tested By**: Claude (stress tests + production verification)
**Approved By**: Prof. Gerd Kortuem
**Next Review**: After Wednesday's workshop
