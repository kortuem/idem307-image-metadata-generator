# Workshop Day Monitoring Guide (Wednesday)

## What to Watch in Render Logs

### Normal Operation (Good!)

```
[10:46:57] INFO: Generating caption for image.jpg with context: TU Delft hall
[10:46:57] INFO: Using shared API key (access code matched)
[10:46:57] INFO: Using Gemini model: gemini-2.5-flash
[10:47:07] INFO: ✓ Generated caption for image.jpg: TU Delft hall with...
```
→ Everything working normally

### Warning Signs to Watch For

#### 1. Rate Limit Errors (API Overload)
```
[10:47:15] ERROR: ⚠️ RATE LIMIT ERROR (attempt 1/3): 429 Resource exhausted
[10:47:15] WARNING: Retrying in 1s...
[10:47:16] ERROR: ⚠️ RATE LIMIT ERROR (attempt 2/3): 429 Resource exhausted
[10:47:18] WARNING: Retrying in 2s...
[10:47:20] INFO: ✓ Generated caption for image.jpg: TU Delft hall with...
```
→ **What it means:** Hitting API rate limits, but retries are working
→ **Action:**
- If you see this frequently, announce: "Please enable Slow Mode checkbox"
- Watch if it resolves after students enable slow mode

#### 2. Service Unavailable (Google's Side)
```
[10:48:30] ERROR: ⚠️ SERVICE UNAVAILABLE (attempt 1/3): 503 Service unavailable
[10:48:30] WARNING: Retrying in 1s...
```
→ **What it means:** Gemini API temporarily down (Google's problem, not yours)
→ **Action:** Wait, retries will handle it. If persistent, tell students to wait 5 min.

#### 3. Server Capacity Errors (Your Side - Memory)
```
[10:50:15] ERROR: Server at capacity (30 concurrent sessions). Please try again.
10.201.139.5 - - [06/Oct/2025:10:50:15 +0000] "POST /api/upload" 503
```
→ **What it means:** MAX_CONCURRENT_SESSIONS limit hit
→ **Action:**
- Tell students: "Server is full, please wait 2-3 minutes for others to finish"
- Monitor if it clears up as students download ZIPs

#### 4. Complete API Failure (Critical)
```
[10:52:45] ERROR: 💥 FAILED after 3 attempts - Error: RATE_LIMIT
```
→ **What it means:** All retries exhausted, request failed
→ **Action:**
- If 1-2 failures: Students can retry, probably transient
- If many failures: Stop workshop, investigate

---

## Render Dashboard Metrics to Monitor

### Memory Tab

**Good:**
```
Memory: 450 MB / 2048 MB (22%)
```
→ Plenty of room

**Warning:**
```
Memory: 1600 MB / 2048 MB (78%)
```
→ Getting full but still safe

**Critical:**
```
Memory: 1900 MB / 2048 MB (93%)
```
→ **Action:** Tell students to download ZIPs to free up sessions

### CPU Tab

**Normal:**
```
CPU: 5-15%
```
→ Expected (API does the work, not CPU)

**High (Unusual):**
```
CPU: 80-100%
```
→ Something wrong, shouldn't happen with this app

---

## Error Categories and Actions

| Error Type | Log Pattern | Severity | Action |
|-----------|-------------|----------|--------|
| **Rate Limit** | `⚠️ RATE LIMIT ERROR` | Medium | Enable slow mode |
| **Service Unavailable** | `⚠️ SERVICE UNAVAILABLE` | Low | Wait, Google will recover |
| **Server Error** | `⚠️ SERVER ERROR` | Medium | Check Render status page |
| **Capacity** | `Server at capacity` | Medium | Students wait or work in pairs |
| **Complete Failure** | `💥 FAILED after 3 attempts` | High | Investigate immediately |

---

## Workshop Announcements Based on Logs

### If you see Rate Limit errors:
**Say:** "If you're seeing errors, please check the 'Slow Mode' checkbox. This adds a small delay and helps prevent overload."

### If you see Capacity errors:
**Say:** "Server is at capacity. Please wait 2-3 minutes for others to finish downloading, then try again."

### If you see Service Unavailable:
**Say:** "Google's API is temporarily down. Please wait 5 minutes and try again. This is Google's issue, not ours."

### If Memory is >85%:
**Say:** "If you've downloaded your ZIP, you can close your browser to free up server memory for others."

---

## Quick Diagnosis Commands

### Check active sessions:
Look in logs for:
```
[TIME] INFO: 30 active sessions (MAX_CONCURRENT_SESSIONS=30)
```

### Check error rate:
Count error lines:
```
grep "ERROR" recent-logs.txt | wc -l
```

If you see >10 errors in 1 minute → Problem

### Check which students are affected:
Look for pattern:
```
grep "FAILED" recent-logs.txt
```
See which session IDs are failing

---

## Emergency Actions

### If everything is failing:

1. **Check Render Status**: https://status.render.com
   - If Render is down, nothing you can do

2. **Check Gemini Status**: Try manual API call
   - If Gemini is down, wait for Google

3. **Restart Service** (last resort):
   - Render Dashboard → Manual Deploy → Deploy latest commit
   - Takes 2-3 minutes
   - All active sessions will be lost

### If only some students failing:

1. **Ask them to enable Slow Mode** ✅
2. **Ask them to use their own API key** (backup plan)
3. **Ask them to wait and retry**

---

## Success Metrics

**Workshop is going well if:**
- ✅ Most logs show: `✓ Generated caption`
- ✅ Few or no `ERROR` messages
- ✅ Memory stays <80%
- ✅ Students successfully download ZIPs

**Workshop has issues if:**
- ❌ Many `💥 FAILED` messages
- ❌ Many `503` HTTP responses
- ❌ Memory >90%
- ❌ Students can't upload/download

---

## What Each Student Session Looks Like

**Complete successful flow:**
```
[TIME] INFO: Session abc123... created (1 active sessions)
[TIME] INFO: Saved 30 images to session abc123...
[TIME] INFO: Generating caption for image1.jpg with context: TU Delft hall
[TIME] INFO: ✓ Generated caption for image1.jpg: TU Delft hall with...
[TIME] INFO: Generating caption for image2.jpg with context: TU Delft hall
[TIME] INFO: ✓ Generated caption for image2.jpg: TU Delft hall featuring...
...
[TIME] INFO: Deleted session abc123... after export (freed ~80MB)
```

**Duration:** ~4-8 minutes per student

---

## Pre-Workshop Checklist

1. ✅ Open Render Dashboard → Metrics tab
2. ✅ Open Render Dashboard → Logs tab
3. ✅ Check initial memory: Should be ~50MB
4. ✅ Test with 1-2 images yourself
5. ✅ Ready to monitor!

---

## Post-Workshop Cleanup

After workshop, check:
```bash
# No sessions should remain
ls /tmp/sessions/
# Should be empty or only very recent files
```

If old sessions remain:
```bash
# Clean up manually
rm /tmp/sessions/*.json
```
