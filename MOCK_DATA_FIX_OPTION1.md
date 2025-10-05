# Mock Data Fix - Option 1: Remove Workflow Pages

## Overview
This document provides step-by-step instructions to remove the Workflows and FlowRuns pages that contain mock data.

---

## Files to Modify

### 1. `/frontend/src/App.tsx`
Remove workflow-related routes.

**Lines to Remove**: 53-58

```typescript
// REMOVE THESE LINES:
{/* Workflows Routes */}
<Route path="/workflows" element={<Workflows />} />
<Route path="/workflows/:action" element={<Workflows />} />
<Route path="/workflows/:action/:id" element={<Workflows />} />
<Route path="/workflows/runs" element={<FlowRuns />} />
<Route path="/workflows/runs/:id" element={<FlowRuns />} />
<Route path="/schedules" element={<SchedulesPage />} />
```

**Also Remove Imports** (lines 12-13):
```typescript
// REMOVE THESE LINES:
import Workflows from './pages/Workflows';
import FlowRuns from './pages/FlowRuns';
```

---

### 2. `/frontend/src/components/Navbar.tsx`
Remove workflow menu items from the hamburger menu.

**Find and remove the "Operations" section** that contains Workflows submenu:

```typescript
// REMOVE THIS ENTIRE SECTION:
<div className="nav-divider"></div>
<div className="nav-section-header">Operations</div>
<div className="nav-menu-item-group">
  <div className="nav-menu-item">
    <span className="nav-icon">
      <GitBranch size={16} aria-hidden="true" />
    </span>
    Workflows
    <span className="nav-chevron">
      <ChevronDown size={14} aria-hidden="true" />
    </span>
  </div>
  <div className="nav-submenu">
    <Link to="/workflows" className="nav-submenu-item">
      Flow Management
    </Link>
    <Link to="/workflows/runs" className="nav-submenu-item">
      Flow Runs
    </Link>
    <Link to="/schedules" className="nav-submenu-item">
      Schedules
    </Link>
  </div>
</div>
```

**Note**: Keep the Schedules page if it's using real API data. If you want to keep Schedules, move it to a different section.

---

### 3. Delete Files

```bash
rm /home/opsconductor/opsconductor-ng/frontend/src/pages/Workflows.tsx
rm /home/opsconductor/opsconductor-ng/frontend/src/pages/FlowRuns.tsx
```

---

### 4. Optional: Update Home Page Dashboard Links

If the home page (AIChat.tsx or Dashboard.tsx) has links to workflows, update them:

**Find and fix**:
```typescript
// BEFORE:
<Link to="/jobs">0 Jobs</Link>
<Link to="/monitoring">0 Runs</Link>

// AFTER:
<Link to="/history/job-runs">0 Jobs</Link>
<Link to="/infrastructure">0 Runs</Link>
```

---

## Verification Steps

### 1. Check Routes
Navigate to these URLs and verify they redirect to home:
- http://localhost:3100/workflows → should redirect to `/`
- http://localhost:3100/workflows/runs → should redirect to `/`

### 2. Check Navigation
- Open hamburger menu
- Verify "Workflows" section is removed
- Verify no broken links

### 3. Check for Mock Data
```bash
cd /home/opsconductor/opsconductor-ng/frontend/src
grep -r "mockFlows\|mockRuns" .
# Should return no results
```

### 4. Check for TODO Comments
```bash
cd /home/opsconductor/opsconductor-ng/frontend/src
grep -r "TODO.*Prefect" .
# Should return no results
```

---

## Testing Checklist

- [ ] Application builds without errors
- [ ] No console errors in browser
- [ ] Navigation menu displays correctly
- [ ] All remaining routes work
- [ ] No mock data visible in UI
- [ ] No broken links in navigation

---

## Rollback Plan

If issues occur, restore from git:
```bash
git checkout HEAD -- frontend/src/App.tsx
git checkout HEAD -- frontend/src/components/Navbar.tsx
git checkout HEAD -- frontend/src/pages/Workflows.tsx
git checkout HEAD -- frontend/src/pages/FlowRuns.tsx
```

---

## Estimated Time
- Implementation: 30 minutes
- Testing: 15 minutes
- **Total: 45 minutes**

---

## Status
⏳ **READY TO IMPLEMENT** - Awaiting approval to proceed.