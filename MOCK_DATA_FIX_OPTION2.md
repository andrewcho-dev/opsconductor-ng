# Mock Data Fix - Option 2: Integrate with Existing Job System

## Overview
This document provides step-by-step instructions to replace mock data in Workflows and FlowRuns pages with real API calls to the existing job system.

---

## Architecture Overview

### Current System
- **Backend**: automation-service provides `/api/v1/jobs` and `/api/v1/runs`
- **Frontend**: `jobApi` and `jobRunApi` in `services/api.ts`
- **Database**: Jobs and JobRuns tables exist

### Mapping Strategy
Map existing Job/JobRun concepts to Flow/FlowRun UI:
- Job → Flow (workflow definition)
- JobRun → FlowRun (workflow execution)

---

## Implementation Steps

### Step 1: Update Workflows.tsx

**File**: `/frontend/src/pages/Workflows.tsx`

**Replace lines 50-132** (the useEffect with mock data):

```typescript
useEffect(() => {
  const loadFlows = async () => {
    try {
      setLoading(true);
      
      // Fetch jobs from real API
      const response = await jobApi.list(0, 100);
      
      // Map jobs to flows
      const mappedFlows: Flow[] = response.jobs.map(job => ({
        id: job.id.toString(),
        name: job.name,
        description: job.description || '',
        status: job.is_active ? 'active' : 'paused',
        lastRun: job.last_run_at || null,
        nextRun: job.next_run_at || null,
        runCount: job.total_runs || 0,
        successRate: job.success_rate || 0,
        tags: job.tags || [],
        created: job.created_at,
        createdBy: job.created_by || 'system'
      }));
      
      setFlows(mappedFlows);
      
      // Fetch recent runs
      const runsResponse = await jobRunApi.list(0, 10);
      const mappedRuns: FlowRun[] = runsResponse.runs.map(run => ({
        id: run.id.toString(),
        flowId: run.job_id.toString(),
        flowName: run.job_name || 'Unknown Job',
        status: mapJobRunStatus(run.status),
        startTime: run.started_at,
        endTime: run.completed_at,
        duration: run.duration_seconds,
        triggeredBy: run.triggered_by || 'manual'
      }));
      
      setRecentRuns(mappedRuns);
    } catch (error) {
      console.error('Failed to load workflows:', error);
    } finally {
      setLoading(false);
    }
  };
  
  loadFlows();
}, []);

// Helper function to map job run status
const mapJobRunStatus = (status: string): 'running' | 'completed' | 'failed' | 'cancelled' | 'pending' => {
  const statusMap: Record<string, any> = {
    'running': 'running',
    'completed': 'completed',
    'success': 'completed',
    'failed': 'failed',
    'error': 'failed',
    'cancelled': 'cancelled',
    'canceled': 'cancelled',
    'pending': 'pending',
    'queued': 'pending'
  };
  return statusMap[status.toLowerCase()] || 'pending';
};
```

**Add import at top of file**:
```typescript
import { jobApi, jobRunApi } from '../services/api';
```

---

### Step 2: Update FlowRuns.tsx

**File**: `/frontend/src/pages/FlowRuns.tsx`

**Replace lines 51-190** (the useEffect with mock data):

```typescript
useEffect(() => {
  const loadRuns = async () => {
    try {
      setLoading(true);
      
      // Fetch runs from real API
      const response = await jobRunApi.list(0, 100);
      
      // Map job runs to flow runs
      const mappedRuns: FlowRun[] = response.runs.map(run => ({
        id: run.id.toString(),
        flowId: run.job_id.toString(),
        flowName: run.job_name || 'Unknown Job',
        status: mapJobRunStatus(run.status),
        startTime: run.started_at,
        endTime: run.completed_at,
        duration: run.duration_seconds,
        triggeredBy: run.triggered_by || 'manual',
        parameters: run.parameters || {},
        logs: run.logs || [],
        taskRuns: run.steps?.map(step => ({
          id: step.id.toString(),
          name: step.name,
          status: mapTaskStatus(step.status),
          startTime: step.started_at,
          endTime: step.completed_at,
          duration: step.duration_seconds
        })) || []
      }));
      
      setRuns(mappedRuns);
      
      // If viewing specific run, set it as selected
      if (id) {
        const run = mappedRuns.find(r => r.id === id);
        if (run) {
          setSelectedRun(run);
        }
      }
    } catch (error) {
      console.error('Failed to load flow runs:', error);
    } finally {
      setLoading(false);
    }
  };
  
  loadRuns();
}, [id]);

// Helper functions
const mapJobRunStatus = (status: string): 'running' | 'completed' | 'failed' | 'cancelled' | 'pending' | 'crashed' => {
  const statusMap: Record<string, any> = {
    'running': 'running',
    'completed': 'completed',
    'success': 'completed',
    'failed': 'failed',
    'error': 'failed',
    'crashed': 'crashed',
    'cancelled': 'cancelled',
    'canceled': 'cancelled',
    'pending': 'pending',
    'queued': 'pending'
  };
  return statusMap[status.toLowerCase()] || 'pending';
};

const mapTaskStatus = (status: string): 'running' | 'completed' | 'failed' | 'pending' | 'skipped' => {
  const statusMap: Record<string, any> = {
    'running': 'running',
    'completed': 'completed',
    'success': 'completed',
    'failed': 'failed',
    'error': 'failed',
    'pending': 'pending',
    'queued': 'pending',
    'skipped': 'skipped'
  };
  return statusMap[status.toLowerCase()] || 'pending';
};
```

**Add import at top of file**:
```typescript
import { jobRunApi } from '../services/api';
```

---

### Step 3: Add Action Handlers

Both files need real action handlers for buttons like "Run Now", "Edit", "Delete".

**Add to Workflows.tsx**:

```typescript
const handleRunNow = async (flowId: string) => {
  try {
    await jobApi.run(parseInt(flowId), {});
    // Reload flows to update status
    window.location.reload();
  } catch (error) {
    console.error('Failed to run workflow:', error);
    alert('Failed to run workflow');
  }
};

const handleEdit = (flowId: string) => {
  navigate(`/workflows/edit/${flowId}`);
};

const handleDelete = async (flowId: string) => {
  if (!window.confirm('Are you sure you want to delete this workflow?')) {
    return;
  }
  
  try {
    await jobApi.delete(parseInt(flowId));
    // Reload flows
    window.location.reload();
  } catch (error) {
    console.error('Failed to delete workflow:', error);
    alert('Failed to delete workflow');
  }
};

const handlePause = async (flowId: string) => {
  try {
    const job = flows.find(f => f.id === flowId);
    if (job) {
      await jobApi.update(parseInt(flowId), { is_active: false });
      window.location.reload();
    }
  } catch (error) {
    console.error('Failed to pause workflow:', error);
    alert('Failed to pause workflow');
  }
};

const handleResume = async (flowId: string) => {
  try {
    const job = flows.find(f => f.id === flowId);
    if (job) {
      await jobApi.update(parseInt(flowId), { is_active: true });
      window.location.reload();
    }
  } catch (error) {
    console.error('Failed to resume workflow:', error);
    alert('Failed to resume workflow');
  }
};
```

**Update button onClick handlers** in the table:

```typescript
<button onClick={() => handleRunNow(flow.id)}>Run Now</button>
<button onClick={() => handleEdit(flow.id)}>Edit</button>
<button onClick={() => handleDelete(flow.id)}>Delete</button>
{flow.status === 'active' ? (
  <button onClick={() => handlePause(flow.id)}>Pause</button>
) : (
  <button onClick={() => handleResume(flow.id)}>Resume</button>
)}
```

---

### Step 4: Update Navigation Labels (Optional)

If you want to keep the "Workflows" terminology, no changes needed.

If you want to align with backend terminology:

**File**: `/frontend/src/components/Navbar.tsx`

```typescript
// Change "Workflows" to "Jobs" or "Automation"
<div className="nav-menu-item">
  <span className="nav-icon">
    <GitBranch size={16} aria-hidden="true" />
  </span>
  Jobs  {/* Changed from "Workflows" */}
  <span className="nav-chevron">
    <ChevronDown size={14} aria-hidden="true" />
  </span>
</div>
```

---

### Step 5: Update Type Definitions

Check if Job and JobRun types in `/frontend/src/types/index.ts` have all required fields.

**Required Job fields**:
- id, name, description, is_active
- last_run_at, next_run_at, total_runs, success_rate
- tags, created_at, created_by

**Required JobRun fields**:
- id, job_id, job_name, status
- started_at, completed_at, duration_seconds
- triggered_by, parameters, logs, steps

If any fields are missing, add them to the type definitions.

---

## Testing Steps

### 1. Backend Verification
Ensure automation-service is running and has data:

```bash
# Check if automation-service is healthy
curl http://localhost:3000/api/health/automation-service

# Check if jobs exist
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:3000/api/v1/jobs

# Check if runs exist
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:3000/api/v1/runs
```

### 2. Frontend Testing
1. Navigate to http://localhost:3100/workflows
2. Verify real job data is displayed (not mock data)
3. Click "Run Now" on a job - verify it executes
4. Navigate to http://localhost:3100/workflows/runs
5. Verify real run data is displayed
6. Click "View Details" on a run - verify details load

### 3. Verify No Mock Data
```bash
cd /home/opsconductor/opsconductor-ng/frontend/src
grep -r "mockFlows\|mockRuns" .
# Should return no results
```

---

## Potential Issues & Solutions

### Issue 1: Missing Fields in API Response
**Symptom**: Some fields are undefined in the UI

**Solution**: Add default values in the mapping:
```typescript
successRate: job.success_rate || 0,
tags: job.tags || [],
```

### Issue 2: Different Status Values
**Symptom**: Status badges show incorrect colors

**Solution**: Update `mapJobRunStatus` function to handle all backend status values

### Issue 3: No Data Available
**Symptom**: Empty tables

**Solution**: 
1. Check if automation-service is running
2. Create test jobs using the API or UI
3. Add "No data" message in the UI

---

## Rollback Plan

If issues occur:
```bash
git checkout HEAD -- frontend/src/pages/Workflows.tsx
git checkout HEAD -- frontend/src/pages/FlowRuns.tsx
```

---

## Estimated Time
- Implementation: 3-4 hours
- Testing: 1-2 hours
- Bug fixes: 1-2 hours
- **Total: 5-8 hours**

---

## Benefits
- ✅ No mock data
- ✅ Real workflow functionality
- ✅ Leverages existing backend
- ✅ No new services needed
- ✅ Unified job/workflow management

---

## Status
⏳ **READY TO IMPLEMENT** - Awaiting approval to proceed.