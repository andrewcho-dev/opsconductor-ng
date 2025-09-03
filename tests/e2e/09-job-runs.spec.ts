import { test, expect } from '@playwright/test';

test.describe('Job Runs Management', () => {
  test.beforeEach(async ({ page }) => {
    // Login as admin for full access
    await page.goto('/login');
    await page.locator('input[type="text"]').fill('admin');
    await page.locator('input[type="password"]').fill('admin123');
    await page.getByRole('button', { name: 'Sign In' }).click();
    await page.getByRole('link', { name: 'Job Runs' }).click();
    await expect(page).toHaveURL('/job-runs');
  });

  test('should display job runs page with all components', async ({ page }) => {
    // Page heading and Create Job link
    await expect(page.getByRole('heading', { name: 'Job Runs', level: 1 })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Create New Job' })).toBeVisible();
    
    // Filter section
    await expect(page.getByText('Filter by Job:')).toBeVisible();
    await expect(page.locator('select')).toBeVisible(); // Job filter dropdown
  });

  test('should display job filter dropdown with options', async ({ page }) => {
    // Job filter dropdown should exist
    const jobFilterDropdown = page.locator('select');
    await expect(jobFilterDropdown).toBeVisible();
    
    // Should have "All Jobs" option selected by default
    await expect(jobFilterDropdown.locator('option[selected]')).toHaveText('All Jobs');
    
    // Should have specific job options
    await expect(jobFilterDropdown.locator('option').filter({ hasText: 'scheduled-job' })).toBeVisible();
    
    // Verify all options
    const allJobsOption = jobFilterDropdown.locator('option').filter({ hasText: 'All Jobs' });
    const scheduledJobOption = jobFilterDropdown.locator('option').filter({ hasText: 'scheduled-job' });
    
    await expect(allJobsOption).toBeVisible();
    await expect(scheduledJobOption).toBeVisible();
  });

  test('should display job runs table with headers', async ({ page }) => {
    // Table headers
    await expect(page.getByRole('columnheader', { name: 'ID' })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: 'Job' })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: 'Status' })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: 'Requested By' })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: 'Queued' })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: 'Started' })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: 'Finished' })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: 'Duration' })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: 'Actions' })).toBeVisible();
  });

  test('should show no job runs message when empty', async ({ page }) => {
    // Should display "No job runs found" message
    await expect(page.getByText('No job runs found')).toBeVisible();
    
    // The message should be in a table cell
    const noRunsCell = page.locator('td').filter({ hasText: 'No job runs found' });
    await expect(noRunsCell).toBeVisible();
  });

  test('should filter jobs using dropdown', async ({ page }) => {
    // Test filtering by specific job
    const jobFilterDropdown = page.locator('select');
    
    // Select specific job
    await jobFilterDropdown.selectOption('scheduled-job');
    
    // Wait for filter to apply
    await page.waitForTimeout(1000);
    
    // Verify dropdown selection changed
    await expect(jobFilterDropdown).toHaveValue('scheduled-job');
    
    // Reset to All Jobs
    await jobFilterDropdown.selectOption('All Jobs');
    await page.waitForTimeout(500);
    
    // Should show all jobs again
    await expect(jobFilterDropdown).toHaveValue('All Jobs');
  });

  test('should navigate to create new job', async ({ page }) => {
    // Click Create New Job link
    await page.getByRole('link', { name: 'Create New Job' }).click();
    
    // Should navigate to jobs page
    await expect(page).toHaveURL('/jobs');
  });

  test('should handle job runs data when available', async ({ page }) => {
    // If job runs exist in the future, this test will validate their display
    const jobRunRows = page.locator('tbody tr').filter({ hasNotText: 'No job runs found' });
    const runCount = await jobRunRows.count();
    
    if (runCount > 0) {
      // Test first job run row
      const firstRun = jobRunRows.first();
      
      // Should have ID (numeric)
      const idCell = firstRun.locator('td').first();
      const idText = await idCell.textContent();
      expect(idText?.trim()).toMatch(/^\d+$/);
      
      // Should have job name
      const jobCell = firstRun.locator('td').nth(1);
      const jobText = await jobCell.textContent();
      expect(jobText?.trim()).toBeTruthy();
      
      // Should have status
      const statusCell = firstRun.locator('td').nth(2);
      const statusText = await statusCell.textContent();
      const validStatuses = ['Queued', 'Running', 'Completed', 'Failed', 'Cancelled'];
      expect(validStatuses).toContain(statusText?.trim());
      
      // Should have requested by
      const requestedByCell = firstRun.locator('td').nth(3);
      const requestedByText = await requestedByCell.textContent();
      expect(requestedByText?.trim()).toBeTruthy();
      
      // Should have action buttons
      const actionsCell = firstRun.locator('td').last();
      await expect(actionsCell.locator('button, a')).toHaveCount({ min: 1 });
    }
  });

  test('should maintain table structure even when empty', async ({ page }) => {
    // Table should always exist
    const table = page.getByRole('table');
    await expect(table).toBeVisible();
    
    // Headers should always be present
    const headerRow = table.locator('thead tr');
    await expect(headerRow).toBeVisible();
    
    // Should have all expected headers
    const expectedHeaders = ['ID', 'Job', 'Status', 'Requested By', 'Queued', 'Started', 'Finished', 'Duration', 'Actions'];
    for (const header of expectedHeaders) {
      await expect(table.getByRole('columnheader', { name: header })).toBeVisible();
    }
    
    // Body should exist (either with data or "No job runs found")
    const tableBody = table.locator('tbody');
    await expect(tableBody).toBeVisible();
  });

  test('should handle job run actions when runs exist', async ({ page }) => {
    // This test will be relevant when job runs exist
    const jobRunRows = page.locator('tbody tr').filter({ hasNotText: 'No job runs found' });
    const runCount = await jobRunRows.count();
    
    if (runCount > 0) {
      const firstRun = jobRunRows.first();
      const actionsCell = firstRun.locator('td').last();
      
      // Common actions might include: View Details, Cancel, Retry, Delete
      const actionButtons = actionsCell.locator('button, a');
      const buttonCount = await actionButtons.count();
      
      if (buttonCount > 0) {
        // Test clicking first action
        await actionButtons.first().click();
        await page.waitForTimeout(500);
        
        // This would depend on what the action does
        // (view details modal, navigation, etc.)
      }
    }
  });

  test('should show job run timing information when available', async ({ page }) => {
    const jobRunRows = page.locator('tbody tr').filter({ hasNotText: 'No job runs found' });
    const runCount = await jobRunRows.count();
    
    if (runCount > 0) {
      const firstRun = jobRunRows.first();
      
      // Queued time
      const queuedCell = firstRun.locator('td').nth(4);
      const queuedText = await queuedCell.textContent();
      
      // Started time
      const startedCell = firstRun.locator('td').nth(5);
      const startedText = await startedCell.textContent();
      
      // Finished time
      const finishedCell = firstRun.locator('td').nth(6);
      const finishedText = await finishedCell.textContent();
      
      // Duration
      const durationCell = firstRun.locator('td').nth(7);
      const durationText = await durationCell.textContent();
      
      // These might be empty or contain datetime/duration values
      // depending on job run status
      expect(typeof queuedText).toBe('string');
      expect(typeof startedText).toBe('string');
      expect(typeof finishedText).toBe('string');
      expect(typeof durationText).toBe('string');
    }
  });

  test('should maintain navigation state', async ({ page }) => {
    // Verify active navigation state
    await expect(page.getByRole('link', { name: 'Job Runs' })).toHaveAttribute('class', /active/);
  });

  test('should navigate away and return successfully', async ({ page }) => {
    // Navigate to different page
    await page.getByRole('link', { name: 'Dashboard' }).click();
    await expect(page).toHaveURL('/');
    
    // Navigate back to job runs
    await page.getByRole('link', { name: 'Job Runs' }).click();
    await expect(page).toHaveURL('/job-runs');
    await expect(page.getByRole('heading', { name: 'Job Runs' })).toBeVisible();
  });

  test('should handle job run status filtering', async ({ page }) => {
    // Test filtering by different job types
    const jobFilterDropdown = page.locator('select');
    
    // Get all available options
    const options = jobFilterDropdown.locator('option');
    const optionCount = await options.count();
    
    // Test each option
    for (let i = 0; i < optionCount; i++) {
      const option = options.nth(i);
      const optionValue = await option.getAttribute('value');
      const optionText = await option.textContent();
      
      if (optionValue && optionText) {
        await jobFilterDropdown.selectOption(optionValue);
        await page.waitForTimeout(500);
        
        // Verify selection
        await expect(jobFilterDropdown).toHaveValue(optionValue);
      }
    }
    
    // Reset to All Jobs
    await jobFilterDropdown.selectOption('All Jobs');
  });

  test('should provide clear empty state messaging', async ({ page }) => {
    // When no job runs exist, should provide helpful message
    await expect(page.getByText('No job runs found')).toBeVisible();
    
    // Should provide way to create jobs
    await expect(page.getByRole('link', { name: 'Create New Job' })).toBeVisible();
    
    // Link should work
    const createJobLink = page.getByRole('link', { name: 'Create New Job' });
    await expect(createJobLink).toHaveAttribute('href', '/jobs');
  });
});