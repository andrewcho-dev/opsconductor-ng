import { test, expect } from '@playwright/test';

test.describe('Dashboard Functionality', () => {
  test.beforeEach(async ({ page }) => {
    // Login as admin for full access
    await page.goto('/login');
    await page.locator('input[type="text"]').fill('admin');
    await page.locator('input[type="password"]').fill('admin123');
    await page.getByRole('button', { name: 'Sign In' }).click();
    await expect(page).toHaveURL('/');
  });

  test('should display all dashboard components', async ({ page }) => {
    // Main dashboard heading
    await expect(page.getByRole('heading', { name: 'Dashboard', level: 1 })).toBeVisible();
    
    // Service Health section
    await expect(page.getByRole('heading', { name: 'Service Health', level: 3 })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Refresh' })).toBeVisible();
    
    // Statistics cards (using regex patterns to be more flexible)
    await expect(page.getByRole('link', { name: /\d+ Users/ })).toBeVisible();
    await expect(page.getByRole('link', { name: /\d+ Credentials/ })).toBeVisible();
    await expect(page.getByRole('link', { name: /\d+ Targets/ })).toBeVisible();
    await expect(page.getByRole('link', { name: /\d+ Jobs/ })).toBeVisible();
    await expect(page.getByRole('link', { name: /\d+ Schedules/ })).toBeVisible();
    await expect(page.getByRole('link', { name: /\d+ Job Runs/ })).toBeVisible();
    
    // System Metrics section
    await expect(page.getByRole('heading', { name: 'System Metrics' })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Executor Status' })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Queue Statistics (24h)' })).toBeVisible();
    
    // Recent Activity section
    await expect(page.getByRole('heading', { name: 'Recent Activity' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'View All' })).toBeVisible();
    
    // Quick Actions section
    await expect(page.getByRole('heading', { name: 'Quick Actions' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Manage Users' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Add Credentials' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Add Targets' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Create Job' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Schedule Jobs' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'View Job History' })).toBeVisible();
    
    // System Information section
    await expect(page.getByRole('heading', { name: 'System Information' })).toBeVisible();
    await expect(page.getByText('Status: Online')).toBeVisible();
    await expect(page.getByText('Version: 1.0.0')).toBeVisible();
    await expect(page.getByText('Backend: Python FastAPI')).toBeVisible();
    await expect(page.getByText('Frontend: React TypeScript')).toBeVisible();
    await expect(page.getByText('Database: PostgreSQL')).toBeVisible();
    await expect(page.getByText('Executor: Python pywinrm')).toBeVisible();
  });

  test('should refresh service health status', async ({ page }) => {
    // Get initial timestamp
    const initialTimestamp = await page.locator('text=Last updated:').textContent();
    
    // Click refresh button
    await page.getByRole('button', { name: 'Refresh' }).click();
    
    // Wait for refresh to complete and verify timestamp changed
    await page.waitForTimeout(2000);
    const newTimestamp = await page.locator('text=Last updated:').textContent();
    expect(newTimestamp).not.toBe(initialTimestamp);
    
    // Verify services are still healthy
    const healthyServices = ['auth', 'credentials', 'users', 'jobs', 'scheduler', 'targets', 'executor'];
    for (const service of healthyServices) {
      await expect(page.locator(`text=${service}`)).toBeVisible();
      await expect(page.locator(`text=healthy`).first()).toBeVisible();
    }
  });

  test('should navigate using quick action links', async ({ page }) => {
    // Test Manage Users link
    await page.getByRole('link', { name: 'Manage Users' }).click();
    await expect(page).toHaveURL('/user-management');
    await page.goBack();
    
    // Test Add Credentials link
    await page.getByRole('link', { name: 'Add Credentials' }).click();
    await expect(page).toHaveURL('/credential-management');
    await page.goBack();
    
    // Test Add Targets link
    await page.getByRole('link', { name: 'Add Targets' }).click();
    await expect(page).toHaveURL('/targets-management');
    await page.goBack();
    
    // Test Create Job link
    await page.getByRole('link', { name: 'Create Job' }).click();
    await expect(page).toHaveURL('/job-management');
    await page.goBack();
    
    // Test Schedule Jobs link
    await page.getByRole('link', { name: 'Schedule Jobs' }).click();
    await expect(page).toHaveURL('/schedule-management');
    await page.goBack();
    
    // Test View Job History link
    await page.getByRole('link', { name: 'View Job History' }).click();
    await expect(page).toHaveURL('/job-runs');
    await page.goBack();
  });

  test('should navigate using statistics cards', async ({ page }) => {
    // Test Users card
    await page.getByRole('link', { name: /Users/ }).click();
    await expect(page).toHaveURL('/user-management');
    await page.goBack();
    
    // Test Credentials card
    await page.getByRole('link', { name: /Credentials/ }).click();
    await expect(page).toHaveURL('/credential-management');
    await page.goBack();
    
    // Test Targets card
    await page.getByRole('link', { name: /Targets/ }).click();
    await expect(page).toHaveURL('/targets-management');
    await page.goBack();
    
    // Test Jobs card
    await page.getByRole('link', { name: /Jobs/ }).click();
    await expect(page).toHaveURL('/job-management');
    await page.goBack();
    
    // Test Schedules card
    await page.getByRole('link', { name: /Schedules/ }).click();
    await expect(page).toHaveURL('/schedules');
    await page.goBack();
    
    // Test Job Runs card
    await page.getByRole('link', { name: /Job Runs/ }).click();
    await expect(page).toHaveURL('/job-runs');
    await page.goBack();
  });

  test('should display system metrics data', async ({ page }) => {
    // Executor Status
    await expect(page.getByText('Worker')).toBeVisible();
    await expect(page.getByText('Running')).toBeVisible();
    await expect(page.getByText('Enabled')).toBeVisible();
    await expect(page.getByText('Yes')).toBeVisible();
    await expect(page.getByText('Poll Interval')).toBeVisible();
    await expect(page.getByText('5s')).toBeVisible();
    
    // Queue Statistics
    await expect(page.getByText('Queued')).toBeVisible();
    await expect(page.getByText('Running')).toBeVisible();
    await expect(page.getByText('Succeeded')).toBeVisible();
    await expect(page.getByText('Failed')).toBeVisible();
  });
});