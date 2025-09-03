import { test, expect } from '@playwright/test';

test.describe('Discovery Management', () => {
  test.beforeEach(async ({ page }) => {
    // Login as admin for full access
    await page.goto('/login');
    await page.locator('input[type="text"]').fill('admin');
    await page.locator('input[type="password"]').fill('admin123');
    await page.getByRole('button', { name: 'Sign In' }).click();
    await page.getByRole('link', { name: 'Discovery' }).click();
    await expect(page).toHaveURL('/discovery');
  });

  test('should display discovery page with all components', async ({ page }) => {
    // Page heading and description
    await expect(page.getByRole('heading', { name: 'Target Discovery', level: 1 })).toBeVisible();
    await expect(page.getByText('Automatically discover Windows machines and other targets on your network')).toBeVisible();
    
    // Tab navigation buttons
    await expect(page.getByRole('button', { name: 'Discovery Jobs' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Discovered Targets' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Create Discovery Job' })).toBeVisible();
    
    // Discovery Jobs section
    await expect(page.getByRole('heading', { name: 'Discovery Jobs', level: 3 })).toBeVisible();
    await expect(page.getByRole('button', { name: 'New Discovery Job' })).toBeVisible();
  });

  test('should display discovery jobs table with headers', async ({ page }) => {
    // Table headers
    await expect(page.getByRole('columnheader', { name: 'Name' })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: 'Status' })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: 'Created' })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: 'Duration' })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: 'Results' })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: 'Actions' })).toBeVisible();
  });

  test('should display existing discovery job data', async ({ page }) => {
    // Check for the test discovery job
    await expect(page.getByText('Test Enhanced Network Range Job')).toBeVisible();
    await expect(page.getByText('completed')).toBeVisible();
    
    // Check results data
    await expect(page.getByText('Hosts: 0')).toBeVisible();
    await expect(page.getByText('Windows: 0')).toBeVisible();
    await expect(page.getByText('Linux: 0')).toBeVisible();
    
    // Check delete button exists
    await expect(page.getByRole('button', { name: 'Delete' })).toBeVisible();
  });

  test('should handle tab navigation', async ({ page }) => {
    // Test Discovery Jobs tab (should be active by default)
    await page.getByRole('button', { name: 'Discovery Jobs' }).click();
    await expect(page.getByRole('heading', { name: 'Discovery Jobs' })).toBeVisible();
    
    // Test Discovered Targets tab
    await page.getByRole('button', { name: 'Discovered Targets' }).click();
    // Wait for potential content change
    await page.waitForTimeout(500);
    
    // Test Create Discovery Job tab
    await page.getByRole('button', { name: 'Create Discovery Job' }).click();
    // Wait for potential content change
    await page.waitForTimeout(500);
  });

  test('should handle new discovery job creation', async ({ page }) => {
    // Click New Discovery Job button
    await page.getByRole('button', { name: 'New Discovery Job' }).click();
    
    // This would typically open a modal or form
    // The exact behavior depends on implementation
    await page.waitForTimeout(500);
  });

  test('should handle discovery job deletion', async ({ page }) => {
    // Set up dialog handler for confirmation
    page.on('dialog', async dialog => {
      expect(dialog.type()).toBe('confirm');
      expect(dialog.message()).toContain('delete');
      await dialog.dismiss(); // Don't actually delete in test
    });
    
    // Click delete button
    await page.getByRole('button', { name: 'Delete' }).click();
  });

  test('should display job duration and timing information', async ({ page }) => {
    // Check that duration is displayed
    await expect(page.getByText('2s')).toBeVisible(); // Duration
    
    // Check that creation date is displayed
    const createdDatePattern = /\d{1,2}\/\d{1,2}\/\d{4}, \d{1,2}:\d{2}:\d{2} [AP]M/;
    const dateElement = page.locator('td').filter({ hasText: createdDatePattern });
    await expect(dateElement).toBeVisible();
  });

  test('should show discovery results breakdown', async ({ page }) => {
    // Verify results are properly formatted
    const resultsCell = page.locator('td').filter({ hasText: 'Hosts:' });
    await expect(resultsCell).toBeVisible();
    
    // Check individual result components
    await expect(page.getByText('Hosts: 0')).toBeVisible();
    await expect(page.getByText('Windows: 0')).toBeVisible();
    await expect(page.getByText('Linux: 0')).toBeVisible();
  });

  test('should handle empty discovery results', async ({ page }) => {
    // The current test data shows 0 results for hosts, which is a valid empty state
    // Verify that zero results are handled gracefully
    await expect(page.getByText('Hosts: 0')).toBeVisible();
    
    // Verify the job still shows as completed successfully
    await expect(page.getByText('completed')).toBeVisible();
  });

  test('should maintain navigation state', async ({ page }) => {
    // Verify active navigation state
    await expect(page.getByRole('link', { name: 'Discovery' })).toHaveAttribute('class', /active/);
  });

  test('should navigate away and return successfully', async ({ page }) => {
    // Navigate to different page
    await page.getByRole('link', { name: 'Dashboard' }).click();
    await expect(page).toHaveURL('/');
    
    // Navigate back to discovery
    await page.getByRole('link', { name: 'Discovery' }).click();
    await expect(page).toHaveURL('/discovery');
    await expect(page.getByRole('heading', { name: 'Target Discovery' })).toBeVisible();
  });

  test('should handle discovered targets view', async ({ page }) => {
    // Switch to Discovered Targets tab
    await page.getByRole('button', { name: 'Discovered Targets' }).click();
    await page.waitForTimeout(1000);
    
    // This tab might show a different view - testing that the tab switch works
    // The actual content would depend on whether there are any discovered targets
  });

  test('should handle create discovery job workflow', async ({ page }) => {
    // Switch to Create Discovery Job tab
    await page.getByRole('button', { name: 'Create Discovery Job' }).click();
    await page.waitForTimeout(1000);
    
    // This would typically show a form for creating a new discovery job
    // Testing that the tab navigation works
  });

  test('should display job status correctly', async ({ page }) => {
    // Verify job status is displayed
    const statusCell = page.locator('td').filter({ hasText: 'completed' });
    await expect(statusCell).toBeVisible();
    
    // Status should be clearly readable
    const statusText = await statusCell.textContent();
    expect(statusText?.trim()).toBe('completed');
  });

  test('should show job name as clickable or informative', async ({ page }) => {
    // Job name should be displayed prominently
    const jobNameElement = page.getByText('Test Enhanced Network Range Job');
    await expect(jobNameElement).toBeVisible();
    
    // It might be a link or just styled text
    const jobNameTag = await jobNameElement.evaluate(el => el.tagName.toLowerCase());
    expect(['strong', 'a', 'span', 'td']).toContain(jobNameTag);
  });
});