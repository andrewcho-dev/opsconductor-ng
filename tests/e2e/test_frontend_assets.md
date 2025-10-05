# E2E Test: Assets Page Functionality

## Test Objective
Verify that the Assets page loads and displays asset data correctly.

## Prerequisites
- User is logged in
- At least one asset exists in the system

## Test Steps

### 1. Navigate to Assets Page
```
Tool: browser_click
Args: { "selector": "a[href='/assets']" }
Expected: Navigation to assets page
```

### 2. Wait for Asset Grid
```
Tool: browser_wait_for_selector
Args: { "selector": ".ag-root-wrapper", "timeout": 10000 }
Expected: AG Grid component loads
```

### 3. Count Assets in Grid
```
Tool: browser_evaluate
Args: { 
  "script": "document.querySelectorAll('.ag-row').length" 
}
Expected: Returns number > 0
```

### 4. Verify Grid Headers
```
Tool: browser_evaluate
Args: { 
  "script": "Array.from(document.querySelectorAll('.ag-header-cell-text')).map(h => h.textContent)" 
}
Expected: Returns array with headers like ["Name", "Type", "Status", etc.]
```

### 5. Get First Asset Name
```
Tool: browser_get_text
Args: { "selector": ".ag-row:first-child .ag-cell[col-id='name']" }
Expected: Returns asset name
```

### 6. Test Search Functionality
```
Tool: browser_fill
Args: { 
  "selector": "input[placeholder*='Search']", 
  "text": "server" 
}
Expected: Grid filters to show only matching assets
```

### 7. Verify Filtered Results
```
Tool: browser_evaluate
Args: { 
  "script": "document.querySelectorAll('.ag-row').length" 
}
Expected: Returns filtered count
```

### 8. Clear Search
```
Tool: browser_fill
Args: { 
  "selector": "input[placeholder*='Search']", 
  "text": "" 
}
Expected: Grid shows all assets again
```

### 9. Take Screenshot
```
Tool: browser_screenshot
Args: { 
  "path": "/home/opsconductor/opsconductor-ng/tests/e2e/screenshots/assets-page.png",
  "fullPage": true
}
Expected: Full page screenshot saved
```

## Success Criteria
- ✅ Assets page loads
- ✅ AG Grid displays assets
- ✅ Asset data is visible
- ✅ Search functionality works
- ✅ Grid updates on filter

## Failure Scenarios
- ❌ Grid doesn't load (check asset-service)
- ❌ No assets displayed (verify database has data)
- ❌ Search doesn't filter (check frontend logic)
- ❌ Grid errors (check console for JS errors)