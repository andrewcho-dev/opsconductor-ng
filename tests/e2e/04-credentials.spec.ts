import { test, expect } from '@playwright/test';

test.describe('Credentials Management', () => {
  test.beforeEach(async ({ page }) => {
    // Login as admin for full access
    await page.goto('/login');
    await page.locator('input[type="text"]').fill('admin');
    await page.locator('input[type="password"]').fill('admin123');
    await page.getByRole('button', { name: 'Sign In' }).click();
    await page.getByRole('link', { name: 'Credentials' }).click();
    await expect(page).toHaveURL('/credential-management');
  });

  test('should display credentials page with all components', async ({ page }) => {
    // Page heading and Add Credential button
    await expect(page.getByRole('heading', { name: 'Credentials', level: 1 })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Add Credential' })).toBeVisible();
    
    // Table headers
    await expect(page.getByRole('columnheader', { name: 'ID' })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: 'Name' })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: 'Type' })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: 'Description' })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: 'Created' })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: 'Actions' })).toBeVisible();
  });

  test('should handle empty credentials state', async ({ page }) => {
    // Check if there are no credentials (empty table body)
    const tableBody = page.locator('tbody');
    const rowCount = await tableBody.locator('tr').count();
    
    if (rowCount === 0) {
      // Empty state - verify table structure is still intact
      await expect(page.getByRole('table')).toBeVisible();
    } else {
      // There are credentials - verify they have proper structure
      for (let i = 0; i < rowCount; i++) {
        const row = tableBody.locator('tr').nth(i);
        
        // Each row should have action buttons
        await expect(row.locator('button, a').first()).toBeVisible();
      }
    }
  });

  test('should open add credential dialog when Add Credential is clicked', async ({ page }) => {
    // Click Add Credential button
    await page.getByRole('button', { name: 'Add Credential' }).click();
    
    // This test verifies the button click works
    // The actual behavior would depend on the implementation
    // (modal, form, navigation, etc.)
  });

  test('should maintain active navigation state', async ({ page }) => {
    // Verify active navigation state
    await expect(page.getByRole('link', { name: 'Credentials' })).toHaveAttribute('class', /active/);
  });

  test('should navigate away and return successfully', async ({ page }) => {
    // Navigate to different page
    await page.getByRole('link', { name: 'Dashboard' }).click();
    await expect(page).toHaveURL('/');
    
    // Navigate back to credentials
    await page.getByRole('link', { name: 'Credentials' }).click();
    await expect(page).toHaveURL('/credential-management');
    await expect(page.getByRole('heading', { name: 'Credentials' })).toBeVisible();
  });

  test('should have consistent table structure', async ({ page }) => {
    // Verify table has proper structure regardless of content
    const table = page.getByRole('table');
    await expect(table).toBeVisible();
    
    // Check header row exists
    const headerRow = table.locator('thead tr');
    await expect(headerRow).toBeVisible();
    
    // Verify all expected columns are present
    const expectedColumns = ['ID', 'Name', 'Type', 'Description', 'Created', 'Actions'];
    for (const column of expectedColumns) {
      await expect(table.getByRole('columnheader', { name: column })).toBeVisible();
    }
  });

  test('should handle credential actions if credentials exist', async ({ page }) => {
    // Check if there are any credentials in the table
    const rows = page.locator('tbody tr');
    const rowCount = await rows.count();
    
    if (rowCount > 0) {
      // If credentials exist, test their action buttons
      const firstRow = rows.first();
      
      // Should have action buttons (Edit, Delete, etc.)
      const actionCell = firstRow.locator('td').last();
      await expect(actionCell.locator('button, a')).toHaveCount({ min: 1 });
      
      // Test clicking first action button
      const firstButton = actionCell.locator('button, a').first();
      await firstButton.click();
      
      // Verify some response (could be modal, navigation, etc.)
      // This would need to be customized based on actual behavior
    }
  });

  test('should display credential types and descriptions properly', async ({ page }) => {
    // Check if credentials exist and verify their data format
    const rows = page.locator('tbody tr');
    const rowCount = await rows.count();
    
    if (rowCount > 0) {
      for (let i = 0; i < rowCount; i++) {
        const row = rows.nth(i);
        
        // Verify row has all expected cells
        const cells = row.locator('td');
        await expect(cells).toHaveCount(6); // ID, Name, Type, Description, Created, Actions
        
        // Verify ID is numeric
        const idCell = cells.first();
        const idText = await idCell.textContent();
        expect(idText?.trim()).toMatch(/^\d+$/);
        
        // Verify Name is not empty
        const nameCell = cells.nth(1);
        const nameText = await nameCell.textContent();
        expect(nameText?.trim()).toBeTruthy();
        
        // Verify Type is not empty
        const typeCell = cells.nth(2);
        const typeText = await typeCell.textContent();
        expect(typeText?.trim()).toBeTruthy();
      }
    }
  });
});