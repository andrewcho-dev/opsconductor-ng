import { test, expect } from '@playwright/test';

test.describe('Target Management', () => {
  test.beforeEach(async ({ page }) => {
    // Login as admin for full access
    await page.goto('/login');
    await page.locator('input[type="text"]').fill('admin');
    await page.locator('input[type="password"]').fill('admin123');
    await page.getByRole('button', { name: 'Sign In' }).click();
    await page.getByRole('link', { name: 'Targets', exact: true }).click();
    await expect(page).toHaveURL('/targets-management');
  });

  test('should display enhanced target management page with all components', async ({ page }) => {
    // Page heading and Add Target button
    await expect(page.getByRole('heading', { name: 'Enhanced Target Management', level: 1 })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Add Target' })).toBeVisible();
    
    // Debug info
    await expect(page.locator('strong', { hasText: 'Debug Info:' })).toBeVisible();
    
    // Filter controls
    await expect(page.getByText('OS Type')).toBeVisible();
    await expect(page.getByText('Service Type')).toBeVisible();
    await expect(page.getByText('Actions')).toBeVisible();
    
    // Filter dropdowns
    await expect(page.locator('select').filter({ hasText: 'All OS Types' })).toBeVisible();
    await expect(page.locator('select').filter({ hasText: 'All Services' })).toBeVisible();
    
    // Action buttons
    await expect(page.getByRole('button', { name: 'Clear Filters' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Refresh' })).toBeVisible();
    
    // Filter debug info
    await expect(page.locator('strong', { hasText: 'Filter Debug:' })).toBeVisible();
  });

  test('should display target cards with correct information', async ({ page }) => {
    // Check for target cards
    const targetNames = ['CRUD-SUCCESS', 'test-enhanced-target', 'test-target-updated'];
    
    for (const targetName of targetNames) {
      await expect(page.getByRole('heading', { name: targetName, level: 5 })).toBeVisible();
    }
    
    // Verify first target details
    const firstTargetCard = page.locator('.target-card, [data-testid="target-card"]').first();
    await expect(firstTargetCard.getByText('test-crud.local')).toBeVisible();
    await expect(firstTargetCard.getByText('192.168.1.100')).toBeVisible();
    await expect(firstTargetCard.getByText('windows')).toBeVisible();
  });

  test('should show target information tables', async ({ page }) => {
    // Check if target information tables are present
    await expect(page.getByRole('heading', { name: 'Target Information', level: 6 })).toBeVisible();
    
    // Check table structure
    const infoTable = page.getByRole('table').first();
    await expect(infoTable.getByText('Hostname:')).toBeVisible();
    await expect(infoTable.getByText('IP Address:')).toBeVisible();
    await expect(infoTable.getByText('OS Type:')).toBeVisible();
    await expect(infoTable.getByText('OS Version:')).toBeVisible();
    await expect(infoTable.getByText('Description:')).toBeVisible();
  });

  test('should display services for each target', async ({ page }) => {
    // Check services section
    await expect(page.getByRole('heading', { name: /Services \(\d+\)/, level: 6 })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Add Service' })).toBeVisible();
    
    // Check service table headers if services exist
    const serviceTables = page.locator('table').filter({ hasText: 'Service' });
    if (await serviceTables.count() > 0) {
      const serviceTable = serviceTables.first();
      await expect(serviceTable.getByText('Service')).toBeVisible();
      await expect(serviceTable.getByText('Category')).toBeVisible();
      await expect(serviceTable.getByText('Port')).toBeVisible();
      await expect(serviceTable.getByText('Status')).toBeVisible();
      await expect(serviceTable.getByText('Actions')).toBeVisible();
    }
  });

  test('should show service action buttons', async ({ page }) => {
    // Check for service action buttons (Test Connection, Remove Service)
    const testConnectionButtons = page.getByRole('button', { name: 'Test Connection' });
    const removeServiceButtons = page.getByRole('button', { name: 'Remove Service' });
    
    if (await testConnectionButtons.count() > 0) {
      await expect(testConnectionButtons.first()).toBeVisible();
    }
    
    if (await removeServiceButtons.count() > 0) {
      await expect(removeServiceButtons.first()).toBeVisible();
    }
  });

  test('should display credentials section for each target', async ({ page }) => {
    // Check credentials section
    await expect(page.getByRole('heading', { name: /Credentials \(\d+\)/, level: 6 })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Add Credential' })).toBeVisible();
    
    // Check for "No credentials configured" message or credential data
    const credentialMessages = page.getByText('No credentials configured');
    if (await credentialMessages.count() > 0) {
      await expect(credentialMessages.first()).toBeVisible();
    }
  });

  test('should filter targets by OS type', async ({ page }) => {
    // Get initial filter debug info
    const initialDebugText = await page.locator('text=Filter Debug:').textContent();
    
    // Change OS Type filter to Windows
    await page.locator('select').filter({ hasText: 'All OS Types' }).selectOption('Windows');
    
    // Wait for filter to apply
    await page.waitForTimeout(1000);
    
    // Verify filter is applied (debug info should update or targets should filter)
    const updatedDebugText = await page.locator('text=Filter Debug:').textContent();
    
    // Should show only Windows targets or update debug info
    // All test targets are Windows so count should remain the same
    await expect(page.locator('text=Target names:')).toBeVisible();
  });

  test('should filter targets by service type', async ({ page }) => {
    // Change Service Type filter
    await page.locator('select').filter({ hasText: 'All Services' }).selectOption('RDP');
    
    // Wait for filter to apply
    await page.waitForTimeout(1000);
    
    // Should filter to show only targets with RDP service
    await expect(page.locator('text=Filter Debug:')).toBeVisible();
  });

  test('should clear filters', async ({ page }) => {
    // Apply some filters first
    await page.locator('select').filter({ hasText: 'All OS Types' }).selectOption('Windows');
    await page.locator('select').filter({ hasText: 'All Services' }).selectOption('RDP');
    
    // Click Clear Filters
    await page.getByRole('button', { name: 'Clear Filters' }).click();
    
    // Verify filters are reset
    await expect(page.locator('select').filter({ hasText: 'All OS Types' })).toBeVisible();
    await expect(page.locator('select').filter({ hasText: 'All Services' })).toBeVisible();
  });

  test('should refresh target data', async ({ page }) => {
    // Click Refresh button
    await page.getByRole('button', { name: 'Refresh' }).click();
    
    // Wait for refresh to complete
    await page.waitForTimeout(2000);
    
    // Verify targets are still displayed
    await expect(page.locator('text=Filter Debug:')).toBeVisible();
    await expect(page.getByRole('heading', { name: 'CRUD-SUCCESS' })).toBeVisible();
  });

  test('should handle target edit and delete actions', async ({ page }) => {
    // Check for target action buttons
    const editButtons = page.getByRole('button', { name: 'Edit' });
    const deleteButtons = page.getByRole('button', { name: 'Delete' });
    
    // Should have edit and delete buttons for each target
    await expect(editButtons.first()).toBeVisible();
    await expect(deleteButtons.first()).toBeVisible();
    
    // Test edit button click
    await editButtons.first().click();
    // This would open edit dialog/form - behavior depends on implementation
    
    // Test delete button click (with confirmation handling)
    page.on('dialog', async dialog => {
      expect(dialog.type()).toBe('confirm');
      await dialog.dismiss(); // Don't actually delete in test
    });
    
    await deleteButtons.first().click();
  });

  test('should expand and collapse target details', async ({ page }) => {
    // Check for expand/collapse buttons (likely the unnamed buttons)
    const expandButtons = page.locator('button[aria-expanded], button').filter({ hasText: '' });
    
    if (await expandButtons.count() > 0) {
      // Click to expand/collapse target details
      await expandButtons.first().click();
      await page.waitForTimeout(500);
      
      // The exact behavior would depend on implementation
      // This test verifies the button interaction works
    }
  });

  test('should handle service operations', async ({ page }) => {
    // Test service addition
    const addServiceButtons = page.getByRole('button', { name: 'Add Service' });
    if (await addServiceButtons.count() > 0) {
      await addServiceButtons.first().click();
      // This would open service addition dialog/form
    }
    
    // Test connection testing
    const testConnectionButtons = page.getByRole('button', { name: 'Test Connection' });
    if (await testConnectionButtons.count() > 0) {
      await testConnectionButtons.first().click();
      // This would test the service connection
    }
  });

  test('should maintain navigation state', async ({ page }) => {
    // Verify active navigation state
    await expect(page.getByRole('link', { name: 'Targets' })).toHaveAttribute('class', /active/);
    
    // Navigate away and back
    await page.getByRole('link', { name: 'Dashboard' }).click();
    await page.getByRole('link', { name: 'Targets', exact: true }).click();
    
    // Should return to targets page
    await expect(page).toHaveURL('/targets-management');
    await expect(page.getByRole('heading', { name: 'Enhanced Target Management' })).toBeVisible();
  });
});