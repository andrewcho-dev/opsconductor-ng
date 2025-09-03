import { test, expect } from '@playwright/test';

test.describe('Authentication System', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should display login page with all user credentials', async ({ page }) => {
    // Should redirect to login page
    await expect(page).toHaveURL('/login');
    await expect(page.getByRole('heading', { name: 'OpsConductor Login' })).toBeVisible();
    
    // Should show default credentials
    await expect(page.getByText('Admin: admin / admin123')).toBeVisible();
    await expect(page.getByText('Operator: operator / admin123')).toBeVisible();
    await expect(page.getByText('Viewer: viewer / admin123')).toBeVisible();
    
    // Should have login form
    await expect(page.locator('input[type="text"]')).toBeVisible();
    await expect(page.locator('input[type="password"]')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Sign In' })).toBeVisible();
  });

  test('should login successfully as admin', async ({ page }) => {
    await page.locator('input[type="text"]').fill('admin');
    await page.locator('input[type="password"]').fill('admin123');
    await page.getByRole('button', { name: 'Sign In' }).click();
    
    // Should redirect to dashboard
    await expect(page).toHaveURL('/');
    await expect(page.getByRole('heading', { name: 'Dashboard', level: 1 })).toBeVisible();
    
    // Should show admin navigation
    await expect(page.getByRole('link', { name: 'Users', exact: true })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Settings' })).toBeVisible();
  });

  test('should login successfully as operator', async ({ page }) => {
    await page.locator('input[type="text"]').fill('operator');
    await page.locator('input[type="password"]').fill('admin123');
    await page.getByRole('button', { name: 'Sign In' }).click();
    
    await expect(page).toHaveURL('/');
    await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();
  });

  test('should login successfully as viewer', async ({ page }) => {
    await page.locator('input[type="text"]').fill('viewer');
    await page.locator('input[type="password"]').fill('admin123');
    await page.getByRole('button', { name: 'Sign In' }).click();
    
    await expect(page).toHaveURL('/');
    await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();
  });

  test('should reject invalid credentials', async ({ page }) => {
    await page.locator('input[type="text"]').fill('invalid');
    await page.locator('input[type="password"]').fill('invalid');
    await page.getByRole('button', { name: 'Sign In' }).click();
    
    // Should remain on login page
    await expect(page).toHaveURL('/login');
  });

  test('should logout successfully', async ({ page }) => {
    // Login first
    await page.locator('input[type="text"]').fill('admin');
    await page.locator('input[type="password"]').fill('admin123');
    await page.getByRole('button', { name: 'Sign In' }).click();
    
    await expect(page).toHaveURL('/');
    
    // Logout
    await page.getByRole('button', { name: 'Logout' }).click();
    
    // Should redirect to login
    await expect(page).toHaveURL('/login');
    await expect(page.getByRole('heading', { name: 'OpsConductor Login' })).toBeVisible();
  });
});