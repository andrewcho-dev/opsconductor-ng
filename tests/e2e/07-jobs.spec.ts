import { test, expect } from '@playwright/test';

test.describe('Job Management', () => {
  test.beforeEach(async ({ page }) => {
    // Login as admin for full access
    await page.goto('/login');
    await page.locator('input[type="text"]').fill('admin');
    await page.locator('input[type="password"]').fill('admin123');
    await page.getByRole('button', { name: 'Sign In' }).click();
    await page.getByRole('link', { name: 'Jobs' }).click();
    await expect(page).toHaveURL('/job-management');
  });

  test('should display jobs page with all components', async ({ page }) => {
    // Page heading and Create Job button
    await expect(page.getByRole('heading', { name: 'Jobs', level: 2 })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Create New Job' })).toBeVisible();
    
    // Table headers
    await expect(page.getByRole('columnheader', { name: 'ID' })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: 'Name' })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: 'Version' })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: 'Steps' })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: 'Status' })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: 'Created' })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: 'Actions' })).toBeVisible();
  });

  test('should display existing job data correctly', async ({ page }) => {
    // Verify the scheduled-job exists
    await expect(page.getByText('scheduled-job')).toBeVisible();
    
    // Check job details
    const jobRow = page.locator('tr').filter({ hasText: 'scheduled-job' });
    await expect(jobRow.getByText('2')).toBeVisible(); // ID
    await expect(jobRow.getByText('scheduled-job')).toBeVisible(); // Name
    await expect(jobRow.getByText('1')).toBeVisible(); // Version
    await expect(jobRow.getByText('1')).toBeVisible(); // Steps count
    await expect(jobRow.getByText('Active')).toBeVisible(); // Status
    
    // Check creation date pattern
    const datePattern = /\d{1,2}\/\d{1,2}\/\d{4}/;
    await expect(jobRow.locator('td').filter({ hasText: datePattern })).toBeVisible();
  });

  test('should show job action buttons', async ({ page }) => {
    // Verify action buttons exist for the job
    const jobRow = page.locator('tr').filter({ hasText: 'scheduled-job' });
    
    await expect(jobRow.getByRole('button', { name: 'Run' })).toBeVisible();
    await expect(jobRow.getByRole('button', { name: 'Edit' })).toBeVisible();
    await expect(jobRow.getByRole('button', { name: 'Delete' })).toBeVisible();
  });

  test('should handle run job action', async ({ page }) => {
    // Click Run button
    const runButton = page.getByRole('button', { name: 'Run' });
    await runButton.click();
    
    // Wait for potential response/feedback
    await page.waitForTimeout(1000);
    
    // This might redirect to job runs page, show a confirmation, etc.
    // The exact behavior depends on implementation
  });

  test('should handle edit job action', async ({ page }) => {
    // Click Edit button
    const editButton = page.getByRole('button', { name: 'Edit' });
    await editButton.click();
    
    // Wait for potential modal or navigation
    await page.waitForTimeout(1000);
    
    // This might open an edit modal, navigate to edit page, etc.
    // The exact behavior depends on implementation
  });

  test('should handle delete job action', async ({ page }) => {
    // Set up dialog handler for confirmation
    page.on('dialog', async dialog => {
      expect(dialog.type()).toBe('confirm');
      expect(dialog.message()).toContain('delete');
      await dialog.dismiss(); // Don't actually delete in test
    });
    
    // Click Delete button
    const deleteButton = page.getByRole('button', { name: 'Delete' });
    await deleteButton.click();
  });

  test('should handle create new job action', async ({ page }) => {
    // Click Create New Job button
    await page.getByRole('button', { name: 'Create New Job' }).click();
    
    // Wait for potential modal or navigation
    await page.waitForTimeout(1000);
    
    // This might open a job creation modal, navigate to job builder, etc.
    // The exact behavior depends on implementation
  });

  test('should display job version information', async ({ page }) => {
    // Verify version column shows version numbers
    const versionCell = page.locator('td').filter({ hasText: /^1$/ }).first();
    await expect(versionCell).toBeVisible();
    
    // Version should be numeric
    const versionText = await versionCell.textContent();
    expect(versionText?.trim()).toMatch(/^\d+$/);
  });

  test('should display job steps count', async ({ page }) => {
    // Verify steps column shows step count
    const stepsCell = page.locator('tr').filter({ hasText: 'scheduled-job' }).locator('td').nth(3);
    await expect(stepsCell).toHaveText('1');
    
    // Steps count should be numeric
    const stepsText = await stepsCell.textContent();
    expect(stepsText?.trim()).toMatch(/^\d+$/);
  });

  test('should display job status correctly', async ({ page }) => {
    // Verify status is displayed
    await expect(page.getByText('Active')).toBeVisible();
    
    // Status should be one of expected values
    const statusCell = page.locator('td').filter({ hasText: 'Active' });
    const statusText = await statusCell.textContent();
    const validStatuses = ['Active', 'Inactive', 'Paused', 'Draft'];
    expect(validStatuses).toContain(statusText?.trim());
  });

  test('should maintain table structure with no jobs', async ({ page }) => {
    // Even if we delete all jobs, table structure should remain
    const table = page.getByRole('table');
    await expect(table).toBeVisible();
    
    // Headers should always be present
    const headerRow = table.locator('thead tr');
    await expect(headerRow).toBeVisible();
    
    // Should have all expected headers
    const expectedHeaders = ['ID', 'Name', 'Version', 'Steps', 'Status', 'Created', 'Actions'];
    for (const header of expectedHeaders) {
      await expect(table.getByRole('columnheader', { name: header })).toBeVisible();
    }
  });

  test('should maintain navigation state', async ({ page }) => {
    // Verify active navigation state
    await expect(page.getByRole('link', { name: 'Jobs' })).toHaveAttribute('class', /active/);
  });

  test('should navigate away and return successfully', async ({ page }) => {
    // Navigate to different page
    await page.getByRole('link', { name: 'Dashboard' }).click();
    await expect(page).toHaveURL('/');
    
    // Navigate back to jobs
    await page.getByRole('link', { name: 'Jobs' }).click();
    await expect(page).toHaveURL('/job-management');
    await expect(page.getByRole('heading', { name: 'Jobs' })).toBeVisible();
  });

  test('should display job ID as numeric', async ({ page }) => {
    // Job ID should be numeric
    const idCell = page.locator('tr').filter({ hasText: 'scheduled-job' }).locator('td').first();
    const idText = await idCell.textContent();
    expect(idText?.trim()).toMatch(/^\d+$/);
    expect(parseInt(idText?.trim() || '0')).toBeGreaterThan(0);
  });

  test('should show job name as the primary identifier', async ({ page }) => {
    // Job name should be prominent and clearly visible
    const nameCell = page.locator('tr').filter({ hasText: 'scheduled-job' }).locator('td').nth(1);
    await expect(nameCell).toHaveText('scheduled-job');
    
    // Name should not be empty
    const nameText = await nameCell.textContent();
    expect(nameText?.trim()).toBeTruthy();
    expect(nameText?.trim().length).toBeGreaterThan(0);
  });

  test('should handle multiple jobs if they exist', async ({ page }) => {
    // Count number of job rows (excluding header)
    const jobRows = page.locator('tbody tr');
    const rowCount = await jobRows.count();
    
    expect(rowCount).toBeGreaterThan(0); // Should have at least the scheduled-job
    
    // Each job row should have all action buttons
    for (let i = 0; i < rowCount; i++) {
      const row = jobRows.nth(i);
      await expect(row.getByRole('button', { name: 'Run' })).toBeVisible();
      await expect(row.getByRole('button', { name: 'Edit' })).toBeVisible();
      await expect(row.getByRole('button', { name: 'Delete' })).toBeVisible();
    }
  });
});