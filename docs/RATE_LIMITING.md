# Rate Limiting & Capacity Management

## Overview

The Image Metadata Generator includes built-in rate limiting to prevent server crashes when multiple users access the application simultaneously. This is critical for workshop scenarios where 15-30 students may use the tool at once.

---

## How It Works

### Session-Based Rate Limiting

The server tracks **active sessions** and enforces a configurable maximum:

```python
# In app.py
MAX_CONCURRENT_SESSIONS = 12  # Default for Render Starter (1GB RAM)
```

**Per-session memory usage**:
- 30 images × 2MB (base64) ≈ **80 MB per session**
- With 12 concurrent sessions: 12 × 80 MB = **960 MB** (safe for 1GB RAM)

### Session Lifecycle

1. **Upload**: Session created and registered in active tracker
2. **Active**: Session tracked with timestamp
3. **Timeout**: Sessions older than 30 minutes auto-removed from tracker
4. **Cleanup**: Expired sessions removed on every new request

### Capacity Check

Before accepting new uploads:

```python
if not is_capacity_available():
    return 503 "Server at capacity, please wait"
```

Users see:
```
⚠️ Server Busy

Server is currently at capacity (12/12 users).
Please wait 2-3 minutes and try again.

Active users: 12/12
```

---

## Configuration

### Environment Variable

Set in Render dashboard or `.env` file:

```bash
# Render Starter (1GB RAM)
MAX_CONCURRENT_SESSIONS=12

# Render Standard (2GB RAM)
MAX_CONCURRENT_SESSIONS=25

# Render Pro (8GB RAM)
MAX_CONCURRENT_SESSIONS=100
```

### Capacity by Plan

| Render Plan | RAM | Max Sessions | Cost/Month |
|-------------|-----|--------------|------------|
| Free        | 512 MB | 6 sessions | $0 |
| Starter     | 1 GB | 12 sessions | $7 |
| Standard    | 2 GB | 25 sessions | $25 |
| Pro         | 8 GB | 100 sessions | $85 |

---

## Workshop Scenarios

### Scenario 1: Free Tier (6 students max)
**Setup**:
```bash
MAX_CONCURRENT_SESSIONS=6
```

**Strategy**:
- Split 30 students into 5 groups of 6
- Run sessions 15 minutes apart
- Total workshop time: ~90 minutes

### Scenario 2: Starter Plan + Groups of 2 (15 pairs)
**Setup**:
```bash
MAX_CONCURRENT_SESSIONS=12
```

**Strategy**:
- 30 students work in pairs (15 sessions)
- First 12 pairs start immediately
- Remaining 3 pairs wait ~3 minutes
- Total workshop time: ~30 minutes

**Recommended for**:
- Workshops with unpredictable timing
- Budget-conscious deployment ($7/month)

### Scenario 3: Standard Plan (30 students)
**Setup**:
```bash
MAX_CONCURRENT_SESSIONS=25
```

**Strategy**:
- All 30 students can work individually
- First 25 start immediately
- Remaining 5 wait ~3 minutes
- Total workshop time: ~20 minutes

**Recommended for**:
- Intensive workshops
- Professional courses
- Best user experience

---

## API Endpoints

### Health Check (Monitor Capacity)

**Request**:
```bash
GET /api/health
```

**Response**:
```json
{
  "status": "healthy",
  "api_key_configured": true,
  "version": "1.0.0",
  "capacity": {
    "active_sessions": 8,
    "max_sessions": 12,
    "available": true,
    "utilization_percent": 66.7
  }
}
```

### Upload (Capacity Check)

**Request**:
```bash
POST /api/upload
Content-Type: multipart/form-data
```

**Response (503 when at capacity)**:
```json
{
  "success": false,
  "error": "server_busy",
  "message": "Server is currently at capacity (12/12 users). Please wait 2-3 minutes and try again.",
  "active_sessions": 12,
  "max_sessions": 12,
  "retry_after": 120
}
```

---

## Frontend Behavior

### On Page Load

```javascript
// Check capacity and show warning if >80% full
async function checkAPIHealth() {
    const response = await fetch('/api/health');
    const data = await response.json();

    if (data.capacity.utilization_percent > 80) {
        log(WARNING, `Server is ${utilization}% full. You may experience delays.`);
    }
}
```

### On Upload (Capacity Error)

```javascript
// Show user-friendly error with retry option
function showCapacityError(data) {
    // Display modal with:
    // - Current capacity: X/Y users
    // - Suggestion to wait 2-3 minutes
    // - "Retry Now" button
}
```

### Automatic Retry

Users can click "Retry Now" to reload the page and attempt upload again.

---

## Monitoring & Debugging

### Server Logs

```bash
# When session registered
[INFO] Session abc123 registered. Active sessions: 8/12

# When capacity reached
[WARNING] Server at capacity: 12/12 active sessions

# When session expires
[INFO] Removed expired session abc123 from active tracker
```

### Debug Console (Frontend)

In browser debug panel:
```
[INFO] Server capacity: 8/12 sessions (66.7% utilized)
[WARNING] Server is 83.3% full. You may experience delays.
[ERROR] Server at capacity: 12/12 users active
```

### Health Check Monitoring

```bash
# Check capacity from command line
curl https://your-app.onrender.com/api/health | jq '.capacity'

# Output:
{
  "active_sessions": 8,
  "max_sessions": 12,
  "available": true,
  "utilization_percent": 66.7
}
```

---

## Limitations & Trade-offs

### Current Implementation

**Pros**:
- ✅ Prevents server crashes
- ✅ Simple in-memory tracking (no database needed)
- ✅ User-friendly error messages
- ✅ Configurable per deployment

**Cons**:
- ❌ In-memory tracker resets on server restart
- ❌ No queue system (users must manually retry)
- ❌ 30-minute timeout may be too aggressive for slow users

### Not Implemented (Future Enhancements)

1. **Queue System**:
   - Put overflow users in queue
   - Notify when capacity available
   - Requires Redis/database

2. **Per-User API Keys**:
   - Each student uses own Gemini key
   - Removes API rate limit bottleneck
   - Requires key management

3. **Persistent Session Tracking**:
   - Track sessions in database
   - Survive server restarts
   - Requires PostgreSQL/Redis

---

## Troubleshooting

### Issue: All users see "Server Busy" immediately

**Cause**: `MAX_CONCURRENT_SESSIONS` set too low or not set

**Fix**:
```bash
# In Render dashboard → Environment
MAX_CONCURRENT_SESSIONS=12  # For Starter plan

# Or in .env for local
echo "MAX_CONCURRENT_SESSIONS=12" >> .env
```

### Issue: Users stuck in "waiting" loop

**Cause**: Sessions not expiring (timeout too long)

**Fix**: Reduce `SESSION_TIMEOUT_MINUTES` in `app.py`:
```python
SESSION_TIMEOUT_MINUTES = 15  # Shorter timeout
```

### Issue: Server crashes despite rate limiting

**Cause**: `MAX_CONCURRENT_SESSIONS` too high for available RAM

**Fix**: Calculate safe limit:
```
Safe limit = (RAM in MB × 0.8) / 80 MB per session

Examples:
- 512 MB: (512 × 0.8) / 80 = 5 sessions
- 1 GB (1024 MB): (1024 × 0.8) / 80 = 10 sessions
- 2 GB (2048 MB): (2048 × 0.8) / 80 = 20 sessions
```

### Issue: Rate limit too strict (rejecting valid users)

**Cause**: Session cleanup not running

**Fix**: Verify cleanup logic:
```bash
# Check logs for cleanup messages
[INFO] Removed expired session abc123 from active tracker
```

If missing, restart server to reset in-memory tracker.

---

## Best Practices

### For Workshop Instructors

1. **Test capacity before workshop**:
   ```bash
   # Set MAX_CONCURRENT_SESSIONS low for testing
   MAX_CONCURRENT_SESSIONS=2

   # Try uploading from 3 different browsers
   # Verify 3rd browser gets "Server Busy" message
   ```

2. **Monitor capacity during workshop**:
   - Open `/api/health` in browser tab
   - Refresh periodically to check utilization
   - Warn students if >80% full

3. **Have backup plan**:
   - If server at capacity, split students into groups
   - Provide estimated wait time (2-3 minutes)
   - Consider temporary upgrade to Standard plan

### For Deployment

1. **Set appropriate limit**:
   ```bash
   # Render Starter → 12 sessions
   # Render Standard → 25 sessions
   # Don't exceed 80% of calculated capacity
   ```

2. **Add monitoring alerts** (optional):
   ```bash
   # Use Render metrics or external monitoring
   # Alert when utilization > 90%
   ```

3. **Document for students**:
   - Explain "Server Busy" message in tutorial
   - Provide retry instructions
   - Set expectations for wait times

---

## Code Reference

### Backend Implementation

- **Rate limiting logic**: [app.py:52-115](../app.py#L52-L115)
- **Capacity check**: [app.py:178-189](../app.py#L178-L189)
- **Health endpoint**: [app.py:124-148](../app.py#L124-L148)

### Frontend Implementation

- **Capacity error handling**: [static/js/app.js:175-179](../static/js/app.js#L175-L179)
- **Error display**: [static/js/app.js:136-161](../static/js/app.js#L136-L161)
- **Health check**: [static/js/app.js:110-134](../static/js/app.js#L110-L134)

---

**Last Updated**: October 2025 (v1.0)
