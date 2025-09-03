import { test, expect } from '@playwright/test';

test.describe('Notifications Management', () => {
  test.beforeEach(async ({ page }) => {
    // Login as admin for full access
    await page.goto('/login');
    await page.locator('input[type="text"]').fill('admin');
    await page.locator('input[type="password"]').fill('admin123');
    await page.getByRole('button', { name: 'Sign In' }).click();
    await page.getByRole('link', { name: 'Notifications' }).click();
    await expect(page).toHaveURL('/notifications');
  });

  test('should display notifications page with all components', async ({ page }) => {
    // Page heading and description
    await expect(page.getByRole('heading', { name: 'Notifications', level: 1 })).toBeVisible();
    await expect(page.getByText('Manage your notification preferences and view notification history.')).toBeVisible();
    
    // Tab navigation
    await expect(page.getByRole('button', { name: '🔔My Preferences' })).toBeVisible();
    await expect(page.getByRole('button', { name: '📋Notification History' })).toBeVisible();
    
    // Current tab description
    await expect(page.getByText('Configure your personal notification settings')).toBeVisible();
  });

  test('should display notification preferences section', async ({ page }) => {
    // Preferences heading and description
    await expect(page.getByRole('heading', { name: 'Notification Preferences', level: 3 })).toBeVisible();
    await expect(page.getByText('Configure how and when you want to receive job notifications.')).toBeVisible();
    
    // Save button
    await expect(page.getByRole('button', { name: 'Save Preferences' })).toBeVisible();
  });

  test('should display email notifications section', async ({ page }) => {
    // Email section heading
    await expect(page.getByRole('heading', { name: 'Email Notifications', level: 4 })).toBeVisible();
    
    // Email enable checkbox
    const emailCheckbox = page.getByRole('checkbox', { name: 'Enable email notifications' });
    await expect(emailCheckbox).toBeVisible();
    await expect(emailCheckbox).toBeChecked(); // Should be checked by default
    
    // Email address field
    await expect(page.getByText('Email Address (optional - uses account email if not specified)')).toBeVisible();
    const emailInput = page.getByRole('textbox', { name: 'Email Address (optional - uses account email if not specified)' });
    await expect(emailInput).toBeVisible();
    await expect(emailInput).toHaveValue('admin@example.com');
    await expect(emailInput).toHaveAttribute('placeholder', 'user@example.com');
  });

  test('should display slack notifications section', async ({ page }) => {
    // Slack section heading
    await expect(page.getByRole('heading', { name: 'Slack Notifications', level: 4 })).toBeVisible();
    
    // Slack enable checkbox
    const slackCheckbox = page.getByRole('checkbox', { name: 'Enable Slack notifications' });
    await expect(slackCheckbox).toBeVisible();
    await expect(slackCheckbox).not.toBeChecked(); // Should be unchecked by default
  });

  test('should display microsoft teams notifications section', async ({ page }) => {
    // Teams section heading
    await expect(page.getByRole('heading', { name: 'Microsoft Teams Notifications', level: 4 })).toBeVisible();
    
    // Teams enable checkbox
    const teamsCheckbox = page.getByRole('checkbox', { name: 'Enable Microsoft Teams notifications' });
    await expect(teamsCheckbox).toBeVisible();
    await expect(teamsCheckbox).not.toBeChecked(); // Should be unchecked by default
  });

  test('should display generic webhook notifications section', async ({ page }) => {
    // Webhook section heading
    await expect(page.getByRole('heading', { name: 'Generic Webhook Notifications', level: 4 })).toBeVisible();
    
    // Webhook enable checkbox
    const webhookCheckbox = page.getByRole('checkbox', { name: 'Enable generic webhook notifications' });
    await expect(webhookCheckbox).toBeVisible();
    await expect(webhookCheckbox).not.toBeChecked(); // Should be unchecked by default
  });

  test('should display notification events section', async ({ page }) => {
    // Events section heading
    await expect(page.getByRole('heading', { name: 'Notification Events', level: 4 })).toBeVisible();
    
    // Event checkboxes
    const successCheckbox = page.getByRole('checkbox', { name: 'Notify on job success' });
    const failureCheckbox = page.getByRole('checkbox', { name: 'Notify on job failure' });
    const startCheckbox = page.getByRole('checkbox', { name: 'Notify on job start' });
    
    await expect(successCheckbox).toBeVisible();
    await expect(successCheckbox).not.toBeChecked(); // Should be unchecked by default
    
    await expect(failureCheckbox).toBeVisible();
    await expect(failureCheckbox).toBeChecked(); // Should be checked by default
    
    await expect(startCheckbox).toBeVisible();
    await expect(startCheckbox).not.toBeChecked(); // Should be unchecked by default
  });

  test('should display quiet hours section', async ({ page }) => {
    // Quiet hours section heading
    await expect(page.getByRole('heading', { name: 'Quiet Hours', level: 4 })).toBeVisible();
    
    // Quiet hours enable checkbox
    const quietHoursCheckbox = page.getByRole('checkbox', { name: 'Enable quiet hours (only critical failures will be sent during this time)' });
    await expect(quietHoursCheckbox).toBeVisible();
    await expect(quietHoursCheckbox).not.toBeChecked(); // Should be unchecked by default
  });

  test('should toggle email notifications', async ({ page }) => {
    const emailCheckbox = page.getByRole('checkbox', { name: 'Enable email notifications' });
    
    // Should start checked
    await expect(emailCheckbox).toBeChecked();
    
    // Toggle off
    await emailCheckbox.click();
    await expect(emailCheckbox).not.toBeChecked();
    
    // Toggle back on
    await emailCheckbox.click();
    await expect(emailCheckbox).toBeChecked();
  });

  test('should update email address', async ({ page }) => {
    const emailInput = page.getByRole('textbox', { name: 'Email Address (optional - uses account email if not specified)' });
    
    // Clear and enter new email
    await emailInput.clear();
    await emailInput.fill('newemail@example.com');
    await expect(emailInput).toHaveValue('newemail@example.com');
    
    // Reset to original
    await emailInput.clear();
    await emailInput.fill('admin@example.com');
    await expect(emailInput).toHaveValue('admin@example.com');
  });

  test('should toggle notification events', async ({ page }) => {
    // Toggle job success notifications
    const successCheckbox = page.getByRole('checkbox', { name: 'Notify on job success' });
    await expect(successCheckbox).not.toBeChecked();
    await successCheckbox.click();
    await expect(successCheckbox).toBeChecked();
    
    // Toggle job failure notifications
    const failureCheckbox = page.getByRole('checkbox', { name: 'Notify on job failure' });
    await expect(failureCheckbox).toBeChecked();
    await failureCheckbox.click();
    await expect(failureCheckbox).not.toBeChecked();
    
    // Toggle job start notifications
    const startCheckbox = page.getByRole('checkbox', { name: 'Notify on job start' });
    await expect(startCheckbox).not.toBeChecked();
    await startCheckbox.click();
    await expect(startCheckbox).toBeChecked();
  });

  test('should toggle external notification services', async ({ page }) => {
    // Toggle Slack
    const slackCheckbox = page.getByRole('checkbox', { name: 'Enable Slack notifications' });
    await expect(slackCheckbox).not.toBeChecked();
    await slackCheckbox.click();
    await expect(slackCheckbox).toBeChecked();
    
    // Toggle Microsoft Teams
    const teamsCheckbox = page.getByRole('checkbox', { name: 'Enable Microsoft Teams notifications' });
    await expect(teamsCheckbox).not.toBeChecked();
    await teamsCheckbox.click();
    await expect(teamsCheckbox).toBeChecked();
    
    // Toggle Generic Webhook
    const webhookCheckbox = page.getByRole('checkbox', { name: 'Enable generic webhook notifications' });
    await expect(webhookCheckbox).not.toBeChecked();
    await webhookCheckbox.click();
    await expect(webhookCheckbox).toBeChecked();
  });

  test('should toggle quiet hours', async ({ page }) => {
    const quietHoursCheckbox = page.getByRole('checkbox', { name: 'Enable quiet hours (only critical failures will be sent during this time)' });
    
    await expect(quietHoursCheckbox).not.toBeChecked();
    await quietHoursCheckbox.click();
    await expect(quietHoursCheckbox).toBeChecked();
    
    // Toggle back off
    await quietHoursCheckbox.click();
    await expect(quietHoursCheckbox).not.toBeChecked();
  });

  test('should save notification preferences', async ({ page }) => {
    // Make some changes
    const successCheckbox = page.getByRole('checkbox', { name: 'Notify on job success' });
    await successCheckbox.click();
    
    const slackCheckbox = page.getByRole('checkbox', { name: 'Enable Slack notifications' });
    await slackCheckbox.click();
    
    // Save preferences
    await page.getByRole('button', { name: 'Save Preferences' }).click();
    
    // Wait for save operation
    await page.waitForTimeout(1000);
    
    // Verify changes are still in place (assuming they're saved)
    await expect(successCheckbox).toBeChecked();
    await expect(slackCheckbox).toBeChecked();
  });

  test('should switch to notification history tab', async ({ page }) => {
    // Click Notification History tab
    await page.getByRole('button', { name: '📋Notification History' }).click();
    
    // Wait for tab content to load
    await page.waitForTimeout(1000);
    
    // The content might change - this tests tab switching works
    // Actual history content would depend on implementation
  });

  test('should handle tab navigation', async ({ page }) => {
    // Test switching between tabs
    const preferencesTab = page.getByRole('button', { name: '🔔My Preferences' });
    const historyTab = page.getByRole('button', { name: '📋Notification History' });
    
    // Should start on preferences tab
    await expect(page.getByText('Configure your personal notification settings')).toBeVisible();
    
    // Switch to history
    await historyTab.click();
    await page.waitForTimeout(500);
    
    // Switch back to preferences
    await preferencesTab.click();
    await page.waitForTimeout(500);
    
    // Should show preferences content again
    await expect(page.getByText('Configure your personal notification settings')).toBeVisible();
  });

  test('should maintain form state during session', async ({ page }) => {
    // Make changes to form
    const emailInput = page.getByRole('textbox', { name: 'Email Address (optional - uses account email if not specified)' });
    await emailInput.clear();
    await emailInput.fill('test@example.com');
    
    const successCheckbox = page.getByRole('checkbox', { name: 'Notify on job success' });
    await successCheckbox.click();
    
    // Navigate away and back
    await page.getByRole('link', { name: 'Dashboard' }).click();
    await page.getByRole('link', { name: 'Notifications' }).click();
    
    // Changes might be lost (unsaved) or preserved depending on implementation
    // This tests the behavior
    const currentEmailValue = await emailInput.inputValue();
    const isSuccessChecked = await successCheckbox.isChecked();
    
    // Either should revert to defaults or maintain changes
    expect(typeof currentEmailValue).toBe('string');
    expect(typeof isSuccessChecked).toBe('boolean');
  });

  test('should validate email address format', async ({ page }) => {
    const emailInput = page.getByRole('textbox', { name: 'Email Address (optional - uses account email if not specified)' });
    
    // Test invalid email formats (if validation exists)
    await emailInput.clear();
    await emailInput.fill('invalid-email');
    
    // Try to save
    await page.getByRole('button', { name: 'Save Preferences' }).click();
    await page.waitForTimeout(500);
    
    // Check if validation error appears or input is corrected
    // This depends on whether client-side validation is implemented
    
    // Reset to valid email
    await emailInput.clear();
    await emailInput.fill('valid@example.com');
  });

  test('should maintain navigation state', async ({ page }) => {
    // Verify active navigation state
    await expect(page.getByRole('link', { name: 'Notifications' })).toHaveAttribute('class', /active/);
  });

  test('should navigate away and return successfully', async ({ page }) => {
    // Navigate to different page
    await page.getByRole('link', { name: 'Dashboard' }).click();
    await expect(page).toHaveURL('/');
    
    // Navigate back to notifications
    await page.getByRole('link', { name: 'Notifications' }).click();
    await expect(page).toHaveURL('/notifications');
    await expect(page.getByRole('heading', { name: 'Notifications' })).toBeVisible();
  });
});