# Verification Guide - 404 Cleanup

## Quick Verification Steps

### 1. Check Console (Most Important)
1. Open browser DevTools (F12)
2. Go to Console tab
3. Clear console
4. Navigate to each page:
   - `/` (AI Chat)
   - `/dashboard`
   - `/assets`
   - `/schedules`
   - `/infrastructure`

**Expected Result:** ✅ No 404 errors, no CORS errors, no AxiosErrors for jobs/runs

### 2. Check Navigation
Click through all menu items:
- ✅ AI Assistant → Should load
- ✅ Dashboard → Should load
- ✅ Schedules → Should show "Coming Soon" page
- ✅ Assets → Should load asset list
- ✅ Infrastructure → Should load
- ✅ Network Analysis → Should load
- ✅ AI Monitoring → Should load
- ✅ Notifications → Should load
- ✅ Templates → Should load
- ✅ Audit Logs → Should load
- ✅ Settings → Should load

**Expected Result:** ✅ All pages load, no broken links, no "History" menu

### 3. Check Deleted Files
Run this command to verify files are deleted:
```bash
ls -la /home/opsconductor/opsconductor-ng/frontend/src/components/SystemStats.tsx 2>&1
ls -la /home/opsconductor/opsconductor-ng/frontend/src/components/RecentActivity.tsx 2>&1
ls -la /home/opsconductor/opsconductor-ng/frontend/src/pages/JobRuns.tsx 2>&1
```

**Expected Result:** ✅ "No such file or directory" for all three

### 4. Check API Calls
In browser DevTools Network tab:
1. Clear network log
2. Refresh page
3. Filter by "jobs" or "runs"

**Expected Result:** ✅ No requests to `/api/v1/jobs` or `/api/v1/runs`

### 5. Check Schedules Page
1. Navigate to `/schedules`
2. Check console for errors
3. Verify "Coming Soon" message displays

**Expected Result:** ✅ Clean placeholder page, no API calls, no errors

### 6. Check AI Chat Stats
1. Navigate to `/` (AI Chat)
2. Look at header stats
3. Verify only "Assets" and "Schedules" pills show

**Expected Result:** ✅ No "Jobs" pill, no "Runs" pill

### 7. Check Dashboard
1. Navigate to `/dashboard`
2. Check stat cards
3. Verify no "Jobs" or "Recent Runs" cards

**Expected Result:** ✅ Only "Assets" and "Schedules" cards

---

## Detailed Console Check

### What You Should NOT See ❌
```
Failed to load resource: 404 (Not Found) - /api/v1/jobs
Failed to load resource: 404 (Not Found) - /api/v1/runs
Failed to load jobs: AxiosError
Access to XMLHttpRequest at 'http://...schedules' blocked by CORS
```

### What You SHOULD See ✅
```
(Clean console with no 404 errors)
```

---

## Network Tab Check

### Filter by "jobs"
**Expected:** No requests to `/api/v1/jobs`

### Filter by "runs"
**Expected:** No requests to `/api/v1/runs`

### Filter by "schedules"
**Expected:** No requests to `/api/v1/schedules`

---

## File System Check

Run these commands to verify cleanup:

```bash
# Check deleted files (should fail)
ls /home/opsconductor/opsconductor-ng/frontend/src/components/SystemStats.tsx
ls /home/opsconductor/opsconductor-ng/frontend/src/components/RecentActivity.tsx
ls /home/opsconductor/opsconductor-ng/frontend/src/pages/JobRuns.tsx

# Check updated files (should exist)
ls /home/opsconductor/opsconductor-ng/frontend/src/App.tsx
ls /home/opsconductor/opsconductor-ng/frontend/src/components/Navbar.tsx
ls /home/opsconductor/opsconductor-ng/frontend/src/pages/AIChat.tsx
ls /home/opsconductor/opsconductor-ng/frontend/src/pages/SchedulesPage.tsx

# Search for any remaining references (should be empty or only interface names)
grep -r "import.*SystemStats" /home/opsconductor/opsconductor-ng/frontend/src/
grep -r "import.*RecentActivity" /home/opsconductor/opsconductor-ng/frontend/src/
grep -r "import.*JobRuns" /home/opsconductor/opsconductor-ng/frontend/src/
```

---

## Success Criteria

### ✅ All Checks Pass
- [ ] No 404 errors in console
- [ ] No CORS errors in console
- [ ] No AxiosErrors for jobs/runs
- [ ] All navigation links work
- [ ] Schedules page shows "Coming Soon"
- [ ] AI Chat shows only Assets stat
- [ ] Dashboard shows only Assets and Schedules
- [ ] No "History" menu in navbar
- [ ] Deleted files don't exist
- [ ] No imports of deleted files

### ❌ If Any Check Fails
1. Check the console error message
2. Check the network tab for failed requests
3. Review the COMPLETE_404_CLEANUP.md document
4. Report the specific error

---

## Quick Test Script

Copy and paste this into your browser console on any page:

```javascript
// Check for 404 errors
const errors = [];
const originalFetch = window.fetch;
window.fetch = function(...args) {
  return originalFetch.apply(this, args).then(response => {
    if (response.status === 404 && (args[0].includes('jobs') || args[0].includes('runs'))) {
      errors.push(`404: ${args[0]}`);
      console.error('❌ Found 404 error:', args[0]);
    }
    return response;
  });
};

// Wait 5 seconds then check
setTimeout(() => {
  if (errors.length === 0) {
    console.log('✅ No 404 errors for jobs/runs detected!');
  } else {
    console.error('❌ Found errors:', errors);
  }
}, 5000);

console.log('Monitoring for 404 errors... (wait 5 seconds)');
```

---

## Troubleshooting

### Issue: Still seeing 404 errors
**Solution:** 
1. Hard refresh (Ctrl+Shift+R or Cmd+Shift+R)
2. Clear browser cache
3. Check if you're on the correct URL
4. Verify the frontend container restarted

### Issue: "History" menu still visible
**Solution:**
1. Verify Navbar.tsx was updated
2. Hard refresh the page
3. Check browser cache

### Issue: Schedules page shows old UI
**Solution:**
1. Verify SchedulesPage.tsx was replaced
2. Hard refresh the page
3. Rebuild frontend if needed

### Issue: AI Chat still shows "Jobs" stat
**Solution:**
1. Verify AIChat.tsx was updated
2. Hard refresh the page
3. Check browser cache

---

## Rollback (If Needed)

If something goes wrong, you can rollback using git:

```bash
cd /home/opsconductor/opsconductor-ng
git status
git diff
git checkout -- frontend/src/
```

**Note:** This will undo ALL changes. Only use if absolutely necessary.

---

## Next Steps After Verification

Once all checks pass:

1. ✅ Mark this cleanup as complete
2. ✅ Update project documentation
3. ✅ Decide on future job management approach (see COMPLETE_404_CLEANUP.md)
4. ✅ Continue with other features

---

**Status:** Ready for verification  
**Expected Time:** 5-10 minutes  
**Risk Level:** Low (only removed broken features)