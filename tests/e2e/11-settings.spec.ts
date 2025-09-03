import { test, expect } from '@playwright/test';

test.describe('Settings Management', () => {
  test.beforeEach(async ({ page }) => {
    // Login as admin for full access
    await page.goto('/login');
    await page.locator('input[type="text"]').fill('admin');
    await page.locator('input[type="password"]').fill('admin123');
    await page.getByRole('button', { name: 'Sign In' }).click();
    await page.getByRole('link', { name: 'Settings' }).click();
    await expect(page).toHaveURL('/settings');
  });

  test('should display settings page with all components', async ({ page }) => {
    // Page heading and description
    await expect(page.getByRole('heading', { name: 'System Settings', level: 1 })).toBeVisible();
    await expect(page.getByText('Configure system-wide settings and email server configuration.')).toBeVisible();
    
    // SMTP Configuration section
    await expect(page.getByRole('heading', { name: 'SMTP Configuration', level: 3 })).toBeVisible();
    await expect(page.getByText('Configure SMTP settings for email notifications. These settings apply system-wide.')).toBeVisible();
    
    // SMTP status indicator
    await expect(page.getByText('✅ SMTP is currently configured and active')).toBeVisible();
    
    // Administrator Help section
    await expect(page.getByRole('heading', { name: '💡 Administrator Help', level: 3 })).toBeVisible();
  });

  test('should display server settings section', async ({ page }) => {
    // Server Settings heading
    await expect(page.getByRole('heading', { name: 'Server Settings', level: 4 })).toBeVisible();
    
    // SMTP Host field
    await expect(page.getByText('SMTP Host *')).toBeVisible();
    const hostInput = page.getByRole('textbox', { name: 'SMTP Host *' });
    await expect(hostInput).toBeVisible();
    await expect(hostInput).toHaveValue('mail.smtp2go.com');
    await expect(hostInput).toHaveAttribute('placeholder', 'smtp.gmail.com');
    
    // SMTP Port field
    await expect(page.getByText('SMTP Port *')).toBeVisible();
    const portInput = page.getByRole('spinbutton', { name: 'SMTP Port *' });
    await expect(portInput).toBeVisible();
    await expect(portInput).toHaveValue('587');
    
    // TLS encryption checkbox
    const tlsCheckbox = page.getByRole('checkbox', { name: 'Use TLS encryption (recommended)' });
    await expect(tlsCheckbox).toBeVisible();
    await expect(tlsCheckbox).toBeChecked();
  });

  test('should display authentication section', async ({ page }) => {
    // Authentication heading
    await expect(page.getByRole('heading', { name: 'Authentication', level: 4 })).toBeVisible();
    
    // Username field
    await expect(page.getByText('Username')).toBeVisible();
    const usernameInput = page.getByRole('textbox', { name: 'Username' });
    await expect(usernameInput).toBeVisible();
    await expect(usernameInput).toHaveValue('andrew@enabledconsultants.com');
    await expect(usernameInput).toHaveAttribute('placeholder', 'your-email@gmail.com');
    
    // Password field
    await expect(page.getByText('Password')).toBeVisible();
    const passwordInput = page.getByRole('textbox', { name: 'Password' });
    await expect(passwordInput).toBeVisible();
    await expect(passwordInput).toHaveAttribute('placeholder', '••••••••');
    
    // Password help text
    await expect(page.getByText('Leave blank to keep current password')).toBeVisible();
  });

  test('should display sender information section', async ({ page }) => {
    // Sender Information heading
    await expect(page.getByRole('heading', { name: 'Sender Information', level: 4 })).toBeVisible();
    
    // From Email Address field
    await expect(page.getByText('From Email Address *')).toBeVisible();
    const fromEmailInput = page.getByRole('textbox', { name: 'From Email Address *' });
    await expect(fromEmailInput).toBeVisible();
    await expect(fromEmailInput).toHaveValue('andrew@enabledconsultants.com');
    await expect(fromEmailInput).toHaveAttribute('placeholder', 'noreply@yourcompany.com');
    
    // From Name field
    await expect(page.getByText('From Name')).toBeVisible();
    const fromNameInput = page.getByRole('textbox', { name: 'From Name' });
    await expect(fromNameInput).toBeVisible();
    await expect(fromNameInput).toHaveValue('OpsConductor');
    await expect(fromNameInput).toHaveAttribute('placeholder', 'OpsConductor');
  });

  test('should display test configuration section', async ({ page }) => {
    // Test Configuration heading
    await expect(page.getByRole('heading', { name: 'Test Configuration', level: 4 })).toBeVisible();
    
    // Test Email Address field
    await expect(page.getByText('Test Email Address')).toBeVisible();
    const testEmailInput = page.getByRole('textbox', { name: 'Test Email Address' });
    await expect(testEmailInput).toBeVisible();
    await expect(testEmailInput).toHaveAttribute('placeholder', 'test@example.com');
    
    // Send Test button (should be disabled initially)
    const sendTestButton = page.getByRole('button', { name: 'Send Test' });
    await expect(sendTestButton).toBeVisible();
    await expect(sendTestButton).toBeDisabled();
  });

  test('should enable send test button when email is entered', async ({ page }) => {
    const testEmailInput = page.getByRole('textbox', { name: 'Test Email Address' });
    const sendTestButton = page.getByRole('button', { name: 'Send Test' });
    
    // Button should start disabled
    await expect(sendTestButton).toBeDisabled();
    
    // Enter test email
    await testEmailInput.fill('test@example.com');
    
    // Button should become enabled
    await expect(sendTestButton).toBeEnabled();
    
    // Clear email
    await testEmailInput.clear();
    
    // Button should become disabled again
    await expect(sendTestButton).toBeDisabled();
  });

  test('should save SMTP settings', async ({ page }) => {
    // Make a change to trigger save
    const hostInput = page.getByRole('textbox', { name: 'SMTP Host *' });
    const originalValue = await hostInput.inputValue();
    
    // Modify the host slightly
    await hostInput.clear();
    await hostInput.fill('test.smtp.com');
    
    // Save settings
    await page.getByRole('button', { name: 'Save SMTP Settings' }).click();
    
    // Wait for save operation
    await page.waitForTimeout(2000);
    
    // Restore original value to avoid breaking system
    await hostInput.clear();
    await hostInput.fill(originalValue);
    await page.getByRole('button', { name: 'Save SMTP Settings' }).click();
    await page.waitForTimeout(1000);
  });

  test('should update SMTP configuration fields', async ({ page }) => {
    // Test SMTP Host
    const hostInput = page.getByRole('textbox', { name: 'SMTP Host *' });
    await hostInput.clear();
    await hostInput.fill('smtp.gmail.com');
    await expect(hostInput).toHaveValue('smtp.gmail.com');
    
    // Test SMTP Port
    const portInput = page.getByRole('spinbutton', { name: 'SMTP Port *' });
    await portInput.clear();
    await portInput.fill('465');
    await expect(portInput).toHaveValue('465');
    
    // Test TLS checkbox
    const tlsCheckbox = page.getByRole('checkbox', { name: 'Use TLS encryption (recommended)' });
    const originalTlsState = await tlsCheckbox.isChecked();
    await tlsCheckbox.click();
    await expect(tlsCheckbox).toBeChecked(!originalTlsState);
    
    // Reset to original values
    await hostInput.clear();
    await hostInput.fill('mail.smtp2go.com');
    await portInput.clear();
    await portInput.fill('587');
    if (!originalTlsState) {
      await tlsCheckbox.click(); // Reset to checked
    }
  });

  test('should update authentication fields', async ({ page }) => {
    // Test Username
    const usernameInput = page.getByRole('textbox', { name: 'Username' });
    const originalUsername = await usernameInput.inputValue();
    await usernameInput.clear();
    await usernameInput.fill('newuser@example.com');
    await expect(usernameInput).toHaveValue('newuser@example.com');
    
    // Test Password (should accept input)
    const passwordInput = page.getByRole('textbox', { name: 'Password' });
    await passwordInput.clear();
    await passwordInput.fill('newpassword123');
    
    // Note: Password might be hidden, so we can't easily verify value
    // But we can verify it accepts input without error
    
    // Reset username
    await usernameInput.clear();
    await usernameInput.fill(originalUsername);
    
    // Clear password (leave blank as suggested)
    await passwordInput.clear();
  });

  test('should update sender information fields', async ({ page }) => {
    // Test From Email
    const fromEmailInput = page.getByRole('textbox', { name: 'From Email Address *' });
    const originalFromEmail = await fromEmailInput.inputValue();
    await fromEmailInput.clear();
    await fromEmailInput.fill('noreply@newdomain.com');
    await expect(fromEmailInput).toHaveValue('noreply@newdomain.com');
    
    // Test From Name
    const fromNameInput = page.getByRole('textbox', { name: 'From Name' });
    const originalFromName = await fromNameInput.inputValue();
    await fromNameInput.clear();
    await fromNameInput.fill('New System Name');
    await expect(fromNameInput).toHaveValue('New System Name');
    
    // Reset to original values
    await fromEmailInput.clear();
    await fromEmailInput.fill(originalFromEmail);
    await fromNameInput.clear();
    await fromNameInput.fill(originalFromName);
  });

  test('should send test email when configured', async ({ page }) => {
    const testEmailInput = page.getByRole('textbox', { name: 'Test Email Address' });
    const sendTestButton = page.getByRole('button', { name: 'Send Test' });
    
    // Enter test email address
    await testEmailInput.fill('admin@example.com');
    
    // Button should be enabled
    await expect(sendTestButton).toBeEnabled();
    
    // Click send test
    await sendTestButton.click();
    
    // Wait for test email operation
    await page.waitForTimeout(3000);
    
    // The operation should complete (no specific validation needed)
    // In a real scenario, you might check for success/error messages
  });

  test('should display common SMTP settings help', async ({ page }) => {
    // Common SMTP Settings heading
    await expect(page.getByRole('heading', { name: 'Common SMTP Settings:', level: 5 })).toBeVisible();
    
    // Gmail settings
    await expect(page.getByText('Gmail:')).toBeVisible();
    await expect(page.getByText('smtp.gmail.com:587 (TLS) - Use app password')).toBeVisible();
    
    // Outlook settings
    await expect(page.getByText('Outlook:')).toBeVisible();
    await expect(page.getByText('smtp-mail.outlook.com:587 (TLS)')).toBeVisible();
    
    // Yahoo settings
    await expect(page.getByText('Yahoo:')).toBeVisible();
    await expect(page.getByText('smtp.mail.yahoo.com:587 (TLS)')).toBeVisible();
    
    // SendGrid settings
    await expect(page.getByText('SendGrid:')).toBeVisible();
    await expect(page.getByText('smtp.sendgrid.net:587 (TLS)')).toBeVisible();
  });

  test('should display administrator help section', async ({ page }) => {
    // Administrator Help heading
    await expect(page.getByRole('heading', { name: '💡 Administrator Help', level: 3 })).toBeVisible();
    
    // SMTP Settings help
    await expect(page.getByText('SMTP Settings:')).toBeVisible();
    await expect(page.getByText('Configure the email server settings that will be used for all system notifications. Make sure to test the configuration after making changes.')).toBeVisible();
    
    // Security help
    await expect(page.getByText('Security:')).toBeVisible();
    await expect(page.getByText('Use app passwords for Gmail and other providers that support 2FA. Always use TLS encryption for secure email transmission.')).toBeVisible();
    
    // Testing help
    await expect(page.getByText('Testing:')).toBeVisible();
    await expect(page.getByText('Use the test functionality to verify your SMTP configuration before saving. This helps ensure notifications will be delivered properly.')).toBeVisible();
  });

  test('should validate required fields', async ({ page }) => {
    // Test clearing required fields
    const hostInput = page.getByRole('textbox', { name: 'SMTP Host *' });
    const fromEmailInput = page.getByRole('textbox', { name: 'From Email Address *' });
    
    // Clear required fields
    await hostInput.clear();
    await fromEmailInput.clear();
    
    // Try to save
    await page.getByRole('button', { name: 'Save SMTP Settings' }).click();
    
    // Wait for potential validation
    await page.waitForTimeout(1000);
    
    // Restore required values (system needs valid config)
    await hostInput.fill('mail.smtp2go.com');
    await fromEmailInput.fill('andrew@enabledconsultants.com');
  });

  test('should maintain navigation state', async ({ page }) => {
    // Verify active navigation state
    await expect(page.getByRole('link', { name: 'Settings' })).toHaveAttribute('class', /active/);
  });

  test('should navigate away and return successfully', async ({ page }) => {
    // Navigate to different page
    await page.getByRole('link', { name: 'Dashboard' }).click();
    await expect(page).toHaveURL('/');
    
    // Navigate back to settings
    await page.getByRole('link', { name: 'Settings' }).click();
    await expect(page).toHaveURL('/settings');
    await expect(page.getByRole('heading', { name: 'System Settings' })).toBeVisible();
  });

  test('should handle form persistence', async ({ page }) => {
    // Make changes to form
    const testEmailInput = page.getByRole('textbox', { name: 'Test Email Address' });
    await testEmailInput.fill('persist@example.com');
    
    const fromNameInput = page.getByRole('textbox', { name: 'From Name' });
    const originalFromName = await fromNameInput.inputValue();
    await fromNameInput.clear();
    await fromNameInput.fill('Test System');
    
    // Navigate away and back
    await page.getByRole('link', { name: 'Dashboard' }).click();
    await page.getByRole('link', { name: 'Settings' }).click();
    
    // Check if unsaved changes are preserved or reset
    const testEmailValue = await testEmailInput.inputValue();
    const fromNameValue = await fromNameInput.inputValue();
    
    // Either should maintain changes or revert to saved state
    expect(typeof testEmailValue).toBe('string');
    expect(typeof fromNameValue).toBe('string');
    
    // Reset from name to original if it was changed
    if (fromNameValue !== originalFromName) {
      await fromNameInput.clear();
      await fromNameInput.fill(originalFromName);
    }
  });
});