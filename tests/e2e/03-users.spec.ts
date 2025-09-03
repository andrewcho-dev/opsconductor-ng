import { test, expect } from '@playwright/test';

test.describe('User Management', () => {
  test.beforeEach(async ({ page }) => {
    // Login as admin for full access
    await page.goto('/login');
    await page.locator('input[type="text"]').fill('admin');
    await page.locator('input[type="password"]').fill('admin123');
    await page.getByRole('button', { name: 'Sign In' }).click();
    await page.getByRole('link', { name: 'Users' }).click();
    await expect(page).toHaveURL('/user-management');
  });

  test('should display users page with all components', async ({ page }) => {
    // Page heading and Add User button
    await expect(page.getByRole('heading', { name: 'Users', level: 1 })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Add User' })).toBeVisible();
    
    // Table headers
    await expect(page.getByRole('columnheader', { name: 'ID' })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: 'Username' })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: 'Email' })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: 'Role' })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: 'Created' })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: 'Actions' })).toBeVisible();
    
    // Verify existing users are displayed
    await expect(page.getByText('choa')).toBeVisible();
    await expect(page.getByText('admin')).toBeVisible();
    await expect(page.getByText('andrew@enabledconsultants.com')).toBeVisible();
    await expect(page.getByText('admin@example.com')).toBeVisible();
  });

  test('should show role dropdowns for each user', async ({ page }) => {
    // Check that role dropdowns exist and have correct options
    const roleDropdowns = page.locator('select').filter({ hasText: 'Admin' });
    await expect(roleDropdowns.first()).toBeVisible();
    
    // Check dropdown options
    const firstDropdown = roleDropdowns.first();
    await expect(firstDropdown.locator('option[value="Viewer"]')).toHaveText('Viewer');
    await expect(firstDropdown.locator('option[value="Operator"]')).toHaveText('Operator');
    await expect(firstDropdown.locator('option[value="Admin"]')).toHaveText('Admin');
  });

  test('should have edit and delete buttons for each user', async ({ page }) => {
    // Check that each user row has Edit and Delete buttons
    const userRows = page.locator('tr').filter({ hasText: 'Edit' });
    await expect(userRows).toHaveCount(2); // Should have 2 users
    
    // Check first user's buttons
    const firstUserRow = userRows.first();
    await expect(firstUserRow.getByRole('button', { name: 'Edit' })).toBeVisible();
    await expect(firstUserRow.getByRole('button', { name: 'Delete' })).toBeVisible();
    
    // Check second user's buttons
    const secondUserRow = userRows.nth(1);
    await expect(secondUserRow.getByRole('button', { name: 'Edit' })).toBeVisible();
    await expect(secondUserRow.getByRole('button', { name: 'Delete' })).toBeVisible();
  });

  test('should change user role via dropdown', async ({ page }) => {
    // Find a role dropdown that's currently set to Admin
    const roleDropdown = page.locator('select').filter({ hasText: 'Admin' }).first();
    
    // Change role to Operator
    await roleDropdown.selectOption('Operator');
    
    // Wait for potential AJAX call
    await page.waitForTimeout(1000);
    
    // Verify role changed (assuming it updates immediately)
    await expect(roleDropdown).toHaveValue('Operator');
  });

  test('should handle edit button click', async ({ page }) => {
    // Click the first Edit button
    const editButton = page.getByRole('button', { name: 'Edit' }).first();
    await editButton.click();
    
    // This test verifies the click works - actual edit functionality
    // would depend on whether a modal opens or navigation occurs
    // We can expand this based on the actual behavior
  });

  test('should handle delete button click with confirmation', async ({ page }) => {
    // Click the first Delete button
    const deleteButton = page.getByRole('button', { name: 'Delete' }).first();
    
    // Set up dialog handler for confirmation
    page.on('dialog', async dialog => {
      expect(dialog.type()).toBe('confirm');
      expect(dialog.message()).toContain('delete');
      await dialog.dismiss(); // Don't actually delete in test
    });
    
    await deleteButton.click();
  });

  test('should open add user dialog/form when Add User is clicked', async ({ page }) => {
    // Click Add User button
    await page.getByRole('button', { name: 'Add User' }).click();
    
    // This test verifies the button click works
    // The actual behavior (modal, navigation, form) would need to be
    // verified based on the implementation
  });

  test('should display user data correctly in table', async ({ page }) => {
    // Verify specific user data is displayed correctly
    const chaRow = page.locator('tr').filter({ hasText: 'choa' });
    await expect(chaRow.getByText('choa')).toBeVisible();
    await expect(chaRow.getByText('andrew@enabledconsultants.com')).toBeVisible();
    await expect(chaRow.getByText('Admin')).toBeVisible();
    
    const adminRow = page.locator('tr').filter({ hasText: 'admin@example.com' });
    await expect(adminRow.getByText('admin')).toBeVisible();
    await expect(adminRow.getByText('admin@example.com')).toBeVisible();
    await expect(adminRow.getByText('Admin')).toBeVisible();
  });

  test('should maintain navigation state', async ({ page }) => {
    // Verify active navigation state
    await expect(page.getByRole('link', { name: 'Users' })).toHaveAttribute('class', /active/);
    
    // Navigate away and back
    await page.getByRole('link', { name: 'Dashboard' }).click();
    await page.getByRole('link', { name: 'Users' }).click();
    
    // Should return to users page
    await expect(page).toHaveURL('/user-management');
    await expect(page.getByRole('heading', { name: 'Users' })).toBeVisible();
  });
});