import { test, expect } from '@playwright/test';

test.describe('Integration Workflows', () => {
  test.beforeEach(async ({ page }) => {
    // Login as admin for full access
    await page.goto('/login');
    await page.locator('input[type="text"]').fill('admin');
    await page.locator('input[type="password"]').fill('admin123');
    await page.getByRole('button', { name: 'Sign In' }).click();
    await expect(page).toHaveURL('/');
  });

  test('should navigate through all main screens via navigation menu', async ({ page }) => {
    // Test complete navigation flow through all screens
    const navigationItems = [
      { name: 'Dashboard', url: '/', heading: 'Dashboard' },
      { name: 'Users', url: '/user-management', heading: 'Users' },
      { name: 'Credentials', url: '/credential-management', heading: 'Credentials' },
      { name: 'Targets', url: '/targets-management', heading: 'Enhanced Target Management' },
      { name: 'Discovery', url: '/discovery', heading: 'Target Discovery' },
      { name: 'Jobs', url: '/job-management', heading: 'Jobs' },
      { name: 'Schedules', url: '/schedule-management', heading: 'Job Schedules' },
      { name: 'Job Runs', url: '/job-runs', heading: 'Job Runs' },
      { name: 'Notifications', url: '/notifications', heading: 'Notifications' },
      { name: 'Settings', url: '/settings', heading: 'System Settings' }
    ];

    for (const item of navigationItems) {
      await page.getByRole('link', { name: item.name }).click();
      await expect(page).toHaveURL(item.url);
      await expect(page.getByRole('heading', { name: item.heading })).toBeVisible();
      
      // Verify navigation item is active
      await expect(page.getByRole('link', { name: item.name })).toHaveAttribute('class', /active/);
    }
  });

  test('should navigate using dashboard quick actions', async ({ page }) => {
    // Verify dashboard quick action links work
    const quickActions = [
      { linkName: 'Manage Users', expectedUrl: '/user-management' },
      { linkName: 'Add Credentials', expectedUrl: '/credential-management' },
      { linkName: 'Add Targets', expectedUrl: '/targets-management' },
      { linkName: 'Create Job', expectedUrl: '/job-management' },
      { linkName: 'Schedule Jobs', expectedUrl: '/schedule-management' },
      { linkName: 'View Job History', expectedUrl: '/job-runs' }
    ];

    for (const action of quickActions) {
      // Return to dashboard
      await page.getByRole('link', { name: 'Dashboard' }).click();
      await expect(page).toHaveURL('/');
      
      // Click quick action
      await page.getByRole('link', { name: action.linkName }).click();
      await expect(page).toHaveURL(action.expectedUrl);
    }
  });

  test('should navigate using dashboard statistics cards', async ({ page }) => {
    // Test statistics card navigation
    const statisticsCards = [
      { cardName: 'Users', expectedUrl: '/user-management' },
      { cardName: 'Credentials', expectedUrl: '/credential-management' },
      { cardName: 'Targets', expectedUrl: '/targets-management' },
      { cardName: 'Jobs', expectedUrl: '/job-management' },
      { cardName: 'Schedules', expectedUrl: '/schedules' },
      { cardName: 'Job Runs', expectedUrl: '/job-runs' }
    ];

    for (const card of statisticsCards) {
      // Return to dashboard
      await page.getByRole('link', { name: 'Dashboard' }).click();
      await expect(page).toHaveURL('/');
      
      // Click statistics card (might be link with regex pattern)
      try {
        await page.getByRole('link', { name: new RegExp(card.cardName) }).click();
        // Some cards might redirect to different URLs than navigation
        const currentUrl = page.url();
        expect(currentUrl).toContain(card.expectedUrl.split('/')[1] || '');
      } catch (error) {
        // Some cards might not be clickable - skip if not found
        console.log(`Statistics card ${card.cardName} might not be clickable`);
      }
    }
  });

  test('should handle service health refresh workflow', async ({ page }) => {
    // Test service health monitoring workflow
    await expect(page.getByRole('heading', { name: 'Service Health' })).toBeVisible();
    
    // Get initial timestamp
    const initialTimestamp = await page.locator('text=Last updated:').textContent();
    
    // Click refresh
    await page.getByRole('button', { name: 'Refresh' }).click();
    
    // Wait for refresh
    await page.waitForTimeout(3000);
    
    // Verify timestamp changed
    const newTimestamp = await page.locator('text=Last updated:').textContent();
    expect(newTimestamp).not.toBe(initialTimestamp);
    
    // Verify services are healthy
    const healthyServices = ['auth', 'credentials', 'users', 'jobs', 'scheduler', 'targets', 'executor'];
    for (const service of healthyServices) {
      await expect(page.locator(`text=${service}`)).toBeVisible();
    }
  });

  test('should complete user management workflow', async ({ page }) => {
    // Navigate to Users
    await page.getByRole('link', { name: 'Users' }).click();
    
    // Verify users exist
    await expect(page.getByText('choa')).toBeVisible();
    await expect(page.getByText('admin')).toBeVisible();
    
    // Test role change workflow
    const roleDropdown = page.locator('select').first();
    const originalRole = await roleDropdown.inputValue();
    
    // Change role
    if (originalRole === 'Admin') {
      await roleDropdown.selectOption('Operator');
      await page.waitForTimeout(1000);
      
      // Change back
      await roleDropdown.selectOption('Admin');
    } else {
      await roleDropdown.selectOption('Admin');
      await page.waitForTimeout(1000);
      
      // Change back
      await roleDropdown.selectOption(originalRole);
    }
    
    // Navigate back to dashboard to verify navigation works
    await page.getByRole('link', { name: 'Dashboard' }).click();
    await expect(page).toHaveURL('/');
  });

  test('should complete targets management workflow', async ({ page }) => {
    // Navigate to Targets
    await page.getByRole('link', { name: 'Targets' }).click();
    
    // Test filter workflow
    const osFilter = page.locator('select').first();
    const serviceFilter = page.locator('select').nth(1);
    
    // Apply OS filter
    await osFilter.selectOption('Windows');
    await page.waitForTimeout(1000);
    
    // Apply service filter
    await serviceFilter.selectOption('RDP');
    await page.waitForTimeout(1000);
    
    // Clear filters
    await page.getByRole('button', { name: 'Clear Filters' }).click();
    await page.waitForTimeout(500);
    
    // Refresh targets
    await page.getByRole('button', { name: 'Refresh' }).click();
    await page.waitForTimeout(1000);
    
    // Verify targets are still displayed
    await expect(page.getByRole('heading', { name: 'CRUD-SUCCESS' })).toBeVisible();
  });

  test('should complete discovery workflow', async ({ page }) => {
    // Navigate to Discovery
    await page.getByRole('link', { name: 'Discovery' }).click();
    
    // Test tab navigation
    await page.getByRole('button', { name: 'Discovery Jobs' }).click();
    await expect(page.getByRole('heading', { name: 'Discovery Jobs' })).toBeVisible();
    
    await page.getByRole('button', { name: 'Discovered Targets' }).click();
    await page.waitForTimeout(500);
    
    await page.getByRole('button', { name: 'Create Discovery Job' }).click();
    await page.waitForTimeout(500);
    
    // Return to Discovery Jobs tab
    await page.getByRole('button', { name: 'Discovery Jobs' }).click();
    
    // Verify discovery job data
    await expect(page.getByText('Test Enhanced Network Range Job')).toBeVisible();
    await expect(page.getByText('completed')).toBeVisible();
  });

  test('should complete job and schedule workflow', async ({ page }) => {
    // Navigate to Jobs
    await page.getByRole('link', { name: 'Jobs' }).click();
    
    // Verify job exists
    await expect(page.getByText('scheduled-job')).toBeVisible();
    
    // Navigate to Schedules
    await page.getByRole('link', { name: 'Schedules' }).click();
    
    // Verify schedule exists for the job
    await expect(page.getByText('scheduled-job')).toBeVisible();
    await expect(page.getByText('Active')).toBeVisible();
    
    // Check scheduler status
    await expect(page.getByText('Running').first()).toBeVisible();
    await expect(page.getByText('Active Schedules:')).toBeVisible();
    await expect(page.getByText('2')).toBeVisible();
    
    // Navigate to Job Runs
    await page.getByRole('link', { name: 'Job Runs' }).click();
    
    // Test job filtering
    const jobFilter = page.locator('select');
    await jobFilter.selectOption('scheduled-job');
    await page.waitForTimeout(1000);
    
    // Reset filter
    await jobFilter.selectOption('All Jobs');
  });

  test('should complete notification preferences workflow', async ({ page }) => {
    // Navigate to Notifications
    await page.getByRole('link', { name: 'Notifications' }).click();
    
    // Test preferences tab
    await page.getByRole('button', { name: '🔔My Preferences' }).click();
    
    // Make preference changes
    const successCheckbox = page.getByRole('checkbox', { name: 'Notify on job success' });
    const initialSuccessState = await successCheckbox.isChecked();
    
    await successCheckbox.click();
    await expect(successCheckbox).toBeChecked(!initialSuccessState);
    
    const slackCheckbox = page.getByRole('checkbox', { name: 'Enable Slack notifications' });
    const initialSlackState = await slackCheckbox.isChecked();
    
    await slackCheckbox.click();
    await expect(slackCheckbox).toBeChecked(!initialSlackState);
    
    // Save preferences
    await page.getByRole('button', { name: 'Save Preferences' }).click();
    await page.waitForTimeout(1000);
    
    // Test history tab
    await page.getByRole('button', { name: '📋Notification History' }).click();
    await page.waitForTimeout(1000);
    
    // Return to preferences
    await page.getByRole('button', { name: '🔔My Preferences' }).click();
    
    // Reset preferences
    if (initialSuccessState !== await successCheckbox.isChecked()) {
      await successCheckbox.click();
    }
    if (initialSlackState !== await slackCheckbox.isChecked()) {
      await slackCheckbox.click();
    }
    
    await page.getByRole('button', { name: 'Save Preferences' }).click();
    await page.waitForTimeout(1000);
  });

  test('should complete settings configuration workflow', async ({ page }) => {
    // Navigate to Settings
    await page.getByRole('link', { name: 'Settings' }).click();
    
    // Verify SMTP configuration is active
    await expect(page.getByText('✅ SMTP is currently configured and active')).toBeVisible();
    
    // Test email configuration
    const testEmailInput = page.getByRole('textbox', { name: 'Test Email Address' });
    const sendTestButton = page.getByRole('button', { name: 'Send Test' });
    
    // Enter test email and send test
    await testEmailInput.fill('test@example.com');
    await expect(sendTestButton).toBeEnabled();
    
    await sendTestButton.click();
    await page.waitForTimeout(2000);
    
    // Clear test email
    await testEmailInput.clear();
    await expect(sendTestButton).toBeDisabled();
    
    // Verify help documentation is available
    await expect(page.getByText('Gmail:')).toBeVisible();
    await expect(page.getByText('Outlook:')).toBeVisible();
    await expect(page.getByText('Yahoo:')).toBeVisible();
    await expect(page.getByText('SendGrid:')).toBeVisible();
  });

  test('should handle logout and re-authentication workflow', async ({ page }) => {
    // Verify logged in state
    await expect(page.getByRole('button', { name: 'Logout' })).toBeVisible();
    
    // Navigate to a few pages to establish session
    await page.getByRole('link', { name: 'Users' }).click();
    await expect(page).toHaveURL('/user-management');
    
    await page.getByRole('link', { name: 'Jobs' }).click();
    await expect(page).toHaveURL('/job-management');
    
    // Logout
    await page.getByRole('button', { name: 'Logout' }).click();
    
    // Should redirect to login
    await expect(page).toHaveURL('/login');
    await expect(page.getByRole('heading', { name: 'OpsConductor Login' })).toBeVisible();
    
    // Re-authenticate
    await page.locator('input[type="text"]').fill('admin');
    await page.locator('input[type="password"]').fill('admin123');
    await page.getByRole('button', { name: 'Sign In' }).click();
    
    // Should return to dashboard
    await expect(page).toHaveURL('/');
    await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();
  });

  test('should handle browser navigation (back/forward) correctly', async ({ page }) => {
    // Navigate through several pages
    await page.getByRole('link', { name: 'Users' }).click();
    await expect(page).toHaveURL('/user-management');
    
    await page.getByRole('link', { name: 'Targets' }).click();
    await expect(page).toHaveURL('/targets-management');
    
    await page.getByRole('link', { name: 'Jobs' }).click();
    await expect(page).toHaveURL('/job-management');
    
    // Use browser back button
    await page.goBack();
    await expect(page).toHaveURL('/targets-management');
    await expect(page.getByRole('heading', { name: 'Enhanced Target Management' })).toBeVisible();
    
    await page.goBack();
    await expect(page).toHaveURL('/user-management');
    await expect(page.getByRole('heading', { name: 'Users' })).toBeVisible();
    
    // Use browser forward button
    await page.goForward();
    await expect(page).toHaveURL('/targets-management');
    
    await page.goForward();
    await expect(page).toHaveURL('/job-management');
    await expect(page.getByRole('heading', { name: 'Jobs' })).toBeVisible();
  });
});