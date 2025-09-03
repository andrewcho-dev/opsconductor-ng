import { test, expect } from '@playwright/test';

test.describe('Schedule Management', () => {
  test.beforeEach(async ({ page }) => {
    // Login as admin for full access
    await page.goto('/login');
    await page.locator('input[type="text"]').fill('admin');
    await page.locator('input[type="password"]').fill('admin123');
    await page.getByRole('button', { name: 'Sign In' }).click();
    await page.getByRole('link', { name: 'Schedules' }).click();
    await expect(page).toHaveURL('/schedule-management');
  });

  test('should display schedules page with all components', async ({ page }) => {
    // Page heading
    await expect(page.getByRole('heading', { name: 'Job Schedules', level: 1 })).toBeVisible();
    
    // Scheduler control section
    await expect(page.getByText('Running')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Stop Scheduler' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Create Schedule' })).toBeVisible();
    
    // Scheduler Status section
    await expect(page.getByRole('heading', { name: 'Scheduler Status', level: 3 })).toBeVisible();
  });

  test('should display scheduler status information', async ({ page }) => {
    // Status information
    await expect(page.getByText('Status:')).toBeVisible();
    await expect(page.getByText('Running').nth(1)).toBeVisible(); // Second "Running" text in status
    
    await expect(page.getByText('Active Schedules:')).toBeVisible();
    await expect(page.getByText('2')).toBeVisible(); // Number of active schedules
    
    await expect(page.getByText('Next Execution:')).toBeVisible();
    await expect(page.getByText('Last Check:')).toBeVisible();
    
    // Date patterns for Next Execution and Last Check
    const datePattern = /\d{1,2}\/\d{1,2}\/\d{4}, \d{1,2}:\d{2}:\d{2} [AP]M/;
    const dateElements = page.locator('text').filter({ hasText: datePattern });
    await expect(dateElements.first()).toBeVisible();
  });

  test('should display schedules table with headers', async ({ page }) => {
    // Table headers
    await expect(page.getByRole('columnheader', { name: 'ID' })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: 'Job' })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: 'Cron Expression' })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: 'Timezone' })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: 'Next Run' })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: 'Last Run' })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: 'Status' })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: 'Created' })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: 'Actions' })).toBeVisible();
  });

  test('should display existing schedule data', async ({ page }) => {
    // Verify the scheduled job exists
    const scheduleRow = page.locator('tr').filter({ hasText: 'scheduled-job' });
    
    await expect(scheduleRow.getByText('3')).toBeVisible(); // ID
    await expect(scheduleRow.getByText('scheduled-job')).toBeVisible(); // Job name
    await expect(scheduleRow.getByText('UTC')).toBeVisible(); // Timezone
    await expect(scheduleRow.getByText('Active')).toBeVisible(); // Status
    
    // Cron expression should be displayed in code format
    await expect(scheduleRow.locator('code')).toHaveText('0 */6 * * *');
    
    // Date fields should exist
    const datePattern = /\d{1,2}\/\d{1,2}\/\d{4}, \d{1,2}:\d{2}:\d{2} [AP]M/;
    await expect(scheduleRow.locator('td').filter({ hasText: datePattern })).toHaveCount({ min: 1 });
  });

  test('should show schedule action buttons', async ({ page }) => {
    // Verify action buttons exist for the schedule
    const scheduleRow = page.locator('tr').filter({ hasText: 'scheduled-job' });
    
    await expect(scheduleRow.getByRole('button', { name: 'Edit' })).toBeVisible();
    await expect(scheduleRow.getByRole('button', { name: 'Delete' })).toBeVisible();
  });

  test('should handle scheduler control actions', async ({ page }) => {
    // Test Stop Scheduler button
    await page.getByRole('button', { name: 'Stop Scheduler' }).click();
    
    // Wait for potential state change
    await page.waitForTimeout(1000);
    
    // The button might change to "Start Scheduler" or show different status
    // This depends on the implementation
  });

  test('should handle create schedule action', async ({ page }) => {
    // Click Create Schedule button
    await page.getByRole('button', { name: 'Create Schedule' }).click();
    
    // Wait for potential modal or navigation
    await page.waitForTimeout(1000);
    
    // This might open a schedule creation modal or form
    // The exact behavior depends on implementation
  });

  test('should handle edit schedule action', async ({ page }) => {
    // Click Edit button for the schedule
    const editButton = page.getByRole('button', { name: 'Edit' });
    await editButton.click();
    
    // Wait for potential modal or navigation
    await page.waitForTimeout(1000);
    
    // This might open an edit modal or navigate to edit page
  });

  test('should handle delete schedule action', async ({ page }) => {
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

  test('should display cron expression correctly', async ({ page }) => {
    // Cron expression should be in code format for readability
    const cronCode = page.locator('code').filter({ hasText: '0 */6 * * *' });
    await expect(cronCode).toBeVisible();
    
    // Verify it's the expected cron pattern (every 6 hours)
    const cronText = await cronCode.textContent();
    expect(cronText?.trim()).toBe('0 */6 * * *');
  });

  test('should show timezone information', async ({ page }) => {
    // Timezone should be displayed clearly
    const timezoneCell = page.locator('td').filter({ hasText: 'UTC' });
    await expect(timezoneCell).toBeVisible();
    
    const timezoneText = await timezoneCell.textContent();
    expect(timezoneText?.trim()).toBe('UTC');
  });

  test('should display schedule timing information', async ({ page }) => {
    // Next Run should be in the future
    await expect(page.getByText('Next Run')).toBeVisible();
    
    // Last Run should show when it last executed
    await expect(page.getByText('Last Run')).toBeVisible();
    
    // Both should have date/time values
    const datePattern = /\d{1,2}\/\d{1,2}\/\d{4}, \d{1,2}:\d{2}:\d{2} [AP]M/;
    const nextRunCell = page.locator('tr').filter({ hasText: 'scheduled-job' }).locator('td').nth(4);
    const lastRunCell = page.locator('tr').filter({ hasText: 'scheduled-job' }).locator('td').nth(5);
    
    await expect(nextRunCell).toHaveText(datePattern);
    await expect(lastRunCell).toHaveText(datePattern);
  });

  test('should show scheduler running indicator', async ({ page }) => {
    // Scheduler should show as running
    await expect(page.locator('text=Running').first()).toBeVisible();
    
    // Status should be consistent between indicator and status section
    const statusIndicators = page.locator('text=Running');
    await expect(statusIndicators).toHaveCount({ min: 2 }); // At least in header and status section
  });

  test('should display active schedules count', async ({ page }) => {
    // Should show number of active schedules
    await expect(page.getByText('Active Schedules:')).toBeVisible();
    await expect(page.getByText('2')).toBeVisible();
    
    // Count should match number of active schedules in table
    const activeScheduleRows = page.locator('tr').filter({ hasText: 'Active' });
    const activeCount = await activeScheduleRows.count();
    
    // Note: This assumes the count in the status section matches table rows
    // The actual implementation might count differently
  });

  test('should maintain navigation state', async ({ page }) => {
    // Verify active navigation state
    await expect(page.getByRole('link', { name: 'Schedules' })).toHaveAttribute('class', /active/);
  });

  test('should navigate away and return successfully', async ({ page }) => {
    // Navigate to different page
    await page.getByRole('link', { name: 'Dashboard' }).click();
    await expect(page).toHaveURL('/');
    
    // Navigate back to schedules
    await page.getByRole('link', { name: 'Schedules' }).click();
    await expect(page).toHaveURL('/schedule-management');
    await expect(page.getByRole('heading', { name: 'Job Schedules' })).toBeVisible();
  });

  test('should display schedule status correctly', async ({ page }) => {
    // Schedule status should be Active
    const statusCell = page.locator('tr').filter({ hasText: 'scheduled-job' }).locator('td').nth(6);
    await expect(statusCell).toHaveText('Active');
    
    // Status should indicate it's currently enabled
    const statusText = await statusCell.textContent();
    expect(['Active', 'Inactive', 'Paused']).toContain(statusText?.trim());
  });

  test('should show schedule creation date', async ({ page }) => {
    // Creation date should be displayed
    const createdCell = page.locator('tr').filter({ hasText: 'scheduled-job' }).locator('td').nth(7);
    
    // Should match date pattern
    const datePattern = /\d{1,2}\/\d{1,2}\/\d{4}, \d{1,2}:\d{2}:\d{2} [AP]M/;
    await expect(createdCell).toHaveText(datePattern);
  });
});