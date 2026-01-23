# Fixes and Optimizations

## ✅ Fixed Issues

### 1. **NULL `updated_at` and `last_snapshot_at` Fields**

**Problem:**
- `updated_at` was NULL because SQLAlchemy's `onupdate` only triggers when it detects a change
- `last_snapshot_at` was NULL if discovery never ran or failed

**Solution:**
- Now explicitly setting `updated_at = datetime.now(timezone.utc)` when:
  - Discovery runs (in `_run_discovery_and_respond`)
  - Artist is force-refreshed
- `last_snapshot_at` is always set when a snapshot is created

**Result:**
- Both fields will now be populated after discovery runs
- Existing artists will get these fields set on next refresh

---

### 2. **Slow Response Time**

**Why It's Slow:**
The discovery process makes **many sequential API calls**:

1. **Initial Discovery** (~7 calls):
   - 1 call: Get artist info
   - 1 call: Search playlists by artist name
   - 1 call: Get top tracks
   - 5 calls: Search playlists by each top track

2. **Verification** (up to 60 calls for 30 playlists):
   - For each candidate playlist:
     - 1 call: Get playlist details
     - 1 call: Get playlist tracks
   - Plus `time.sleep()` delays

**Total:** Potentially **~67 API calls** per discovery, with network latency and delays.

**Optimizations Applied:**
1. ✅ **Reduced verification limit**: Now verifies max 30 playlists instead of 50
2. ✅ **Reduced delays**: Changed `time.sleep(0.1)` to `0.05` seconds
3. ✅ **Early exit**: Stops verifying once we have enough playlists

**Expected Improvement:**
- **Before**: ~2-3 minutes (100+ calls × 0.1s delays + network time)
- **After**: ~1-2 minutes (60-70 calls × 0.05s delays + network time)
- **~30-40% faster**

---

## 📊 Response Time Breakdown

### Current Process (After Optimization):

```
1. Get Artist:              ~0.5s
2. Search by Artist:        ~0.5s
3. Get Top Tracks:          ~0.5s
4. Search by 5 Tracks:      ~2.5s (5 × 0.5s)
5. Verify 30 Playlists:     ~30s (30 × 2 calls × 0.5s)
6. Delays:                   ~1.5s (30 × 0.05s)
─────────────────────────────────────────────
Total:                      ~35-40 seconds
```

### Why It Can't Be Much Faster:

1. **API Rate Limits**: We must respect SoundCloud's rate limits
2. **Sequential Calls**: Each playlist must be verified individually
3. **Network Latency**: Each API call has network overhead
4. **Verification Required**: Can't skip verification (too many false positives)

---

## 🚀 Further Optimization Options (If Needed)

### Option 1: **Reduce Max Playlists**
```python
# In discovery.py, change:
max_playlists: int = 50  # → 20 or 30
```

### Option 2: **Parallel Verification** (Advanced)
- Use `asyncio` or `concurrent.futures` to verify multiple playlists simultaneously
- **Warning**: Must respect rate limits carefully
- **Benefit**: Could reduce verification time from 30s to ~10s

### Option 3: **Cache Playlist Data**
- Cache playlist details for a short time (5-10 minutes)
- Reduces redundant API calls
- **Benefit**: Faster subsequent requests

### Option 4: **Background Jobs**
- Run discovery in background (Celery, etc.)
- Return immediately with "processing" status
- Client polls for results
- **Benefit**: Non-blocking API

---

## 📝 Summary

**Fixed:**
- ✅ `updated_at` now always set when artist is updated
- ✅ `last_snapshot_at` now always set when snapshot is created

**Optimized:**
- ✅ Reduced verification from 50 to 30 playlists
- ✅ Reduced delays from 0.1s to 0.05s
- ✅ Added early exit when enough playlists found

**Expected Results:**
- Timestamps will be populated correctly
- Response time reduced by ~30-40%
- Still takes ~1-2 minutes (due to API call volume)

**Note:** The slow response is **expected** given the number of API calls required. This is a trade-off between:
- **Completeness**: Finding all playlists
- **Speed**: Fast response time

For production, consider implementing **background jobs** if response time is critical.
