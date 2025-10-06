import { test, expect, Page } from '@playwright/test';

/**
 * Basic End-to-End Tests
 * 
 * Tests the core functionality after tool registry removal:
 * 1. Login
 * 2. Navigate to AI Chat
 * 3. Send basic queries
 * 4. Verify responses
 */

const BASE_URL = process.env.BASE_URL || 'http://localhost:3100';
const TEST_USERNAME = process.env.TEST_USERNAME || 'admin';
const TEST_PASSWORD = process.env.TEST_PASSWORD || 'admin';

// Helper function to login
async function login(page: Page) {
  console.log(`🔐 Logging in to ${BASE_URL}...`);
  await page.goto(BASE_URL);
  
  // Wait for login form
  await page.waitForSelector('input[type="text"], input[name="username"]', { timeout: 15000 });
  
  // Fill credentials
  await page.fill('input[type="text"], input[name="username"]', TEST_USERNAME);
  await page.fill('input[type="password"], input[name="password"]', TEST_PASSWORD);
  
  // Submit
  await page.click('button[type="submit"]');
  
  // Wait for redirect to dashboard or ai-chat
  await page.waitForURL(/dashboard|ai-chat/, { timeout: 15000 });
  console.log('✅ Login successful');
}

// Helper function to navigate to AI Chat
async function navigateToAIChat(page: Page) {
  console.log('🧭 Navigating to AI Chat...');
  
  // Check if already on AI Chat page
  if (page.url().includes('ai-chat')) {
    console.log('✅ Already on AI Chat page');
    return;
  }
  
  // Try multiple selectors for the AI Chat link
  const selectors = [
    'a[href="/ai-chat"]',
    'a[href*="ai-chat"]',
    'text=AI Chat',
    'text=Chat',
    '[data-testid="ai-chat-link"]'
  ];
  
  for (const selector of selectors) {
    try {
      const element = page.locator(selector).first();
      if (await element.count() > 0) {
        await element.click({ timeout: 5000 });
        await page.waitForURL(/ai-chat/, { timeout: 5000 });
        console.log('✅ Navigated to AI Chat');
        return;
      }
    } catch (e) {
      continue;
    }
  }
  
  // If navigation failed, try direct URL
  console.log('⚠️  Navigation link not found, trying direct URL...');
  await page.goto(`${BASE_URL}/ai-chat`);
  await page.waitForLoadState('networkidle');
  console.log('✅ Navigated to AI Chat via direct URL');
}

// Helper function to send message and wait for response
async function sendMessage(page: Page, message: string, timeout: number = 90000): Promise<string> {
  console.log(`📤 Sending message: "${message}"`);
  const startTime = Date.now();
  
  // Find input field
  const inputSelectors = [
    'textarea[placeholder*="message" i]',
    'textarea[placeholder*="type" i]',
    'textarea',
    'input[type="text"]'
  ];
  
  let input = null;
  for (const selector of inputSelectors) {
    const element = page.locator(selector).first();
    if (await element.count() > 0 && await element.isVisible()) {
      input = element;
      break;
    }
  }
  
  if (!input) {
    throw new Error('Could not find input field');
  }
  
  // Clear and fill input
  await input.clear();
  await input.fill(message);
  
  // Count messages before sending
  const messagesBefore = await page.locator('[class*="message"], .message').count();
  console.log(`📊 Messages before: ${messagesBefore}`);
  
  // Find and click send button
  const sendButtonSelectors = [
    'button[aria-label*="send" i]',
    'button:has-text("Send")',
    'button[type="submit"]',
    'button:has(svg[class*="send" i])'
  ];
  
  let buttonClicked = false;
  for (const selector of sendButtonSelectors) {
    try {
      const button = page.locator(selector).first();
      if (await button.count() > 0 && await button.isVisible()) {
        await button.click();
        buttonClicked = true;
        console.log('✅ Send button clicked');
        break;
      }
    } catch (e) {
      continue;
    }
  }
  
  if (!buttonClicked) {
    console.log('⚠️  Send button not found, trying Enter key...');
    await input.press('Enter');
  }
  
  // Wait for AI response (at least 2 new messages: user + AI)
  console.log('⏳ Waiting for AI response...');
  await page.waitForFunction(
    (beforeCount) => {
      const messages = document.querySelectorAll('[class*="message"], .message');
      return messages.length >= beforeCount + 2;
    },
    messagesBefore,
    { timeout }
  );
  
  const responseTime = Date.now() - startTime;
  console.log(`✅ Response received in ${responseTime}ms`);
  
  // Get the last message (AI response)
  const allMessages = page.locator('[class*="message"], .message');
  const lastMessage = allMessages.last();
  const responseText = await lastMessage.textContent() || '';
  
  console.log(`📥 Response preview: ${responseText.substring(0, 100)}...`);
  
  return responseText;
}

// Test suite
test.describe('Basic End-to-End Tests (Database as Single Source of Truth)', () => {
  
  test.beforeEach(async ({ page }) => {
    await login(page);
    await navigateToAIChat(page);
    
    // Wait for chat interface to be ready
    await page.waitForSelector('textarea, input[type="text"]', { timeout: 10000 });
    console.log('✅ Chat interface ready');
  });

  test('Test 1: Simple information request', async ({ page }) => {
    console.log('\n🧪 TEST 1: Simple information request');
    
    const response = await sendMessage(page, 'What can you help me with?');
    
    // Verify response is not empty
    expect(response.length).toBeGreaterThan(0);
    console.log('✅ Test 1 passed: Received non-empty response');
    
    // Take screenshot
    await page.screenshot({ path: 'tests/e2e/screenshots/test1-info-request.png', fullPage: true });
  });

  test('Test 2: Asset query - list all assets', async ({ page }) => {
    console.log('\n🧪 TEST 2: Asset query - list all assets');
    
    const response = await sendMessage(page, 'Show me all assets');
    
    // Verify response mentions assets
    expect(response.length).toBeGreaterThan(0);
    expect(response.toLowerCase()).toMatch(/asset|server|host/);
    console.log('✅ Test 2 passed: Received asset-related response');
    
    // Take screenshot
    await page.screenshot({ path: 'tests/e2e/screenshots/test2-list-assets.png', fullPage: true });
  });

  test('Test 3: Asset query - filter by OS', async ({ page }) => {
    console.log('\n🧪 TEST 3: Asset query - filter by OS');
    
    const response = await sendMessage(page, 'Show me all Linux servers');
    
    // Verify response is relevant
    expect(response.length).toBeGreaterThan(0);
    console.log('✅ Test 3 passed: Received response for Linux servers query');
    
    // Take screenshot
    await page.screenshot({ path: 'tests/e2e/screenshots/test3-linux-servers.png', fullPage: true });
  });

  test('Test 4: System information query', async ({ page }) => {
    console.log('\n🧪 TEST 4: System information query');
    
    const response = await sendMessage(page, 'What is the system status?');
    
    // Verify response
    expect(response.length).toBeGreaterThan(0);
    console.log('✅ Test 4 passed: Received system status response');
    
    // Take screenshot
    await page.screenshot({ path: 'tests/e2e/screenshots/test4-system-status.png', fullPage: true });
  });

  test('Test 5: Multi-turn conversation', async ({ page }) => {
    console.log('\n🧪 TEST 5: Multi-turn conversation');
    
    // First message
    const response1 = await sendMessage(page, 'How many assets do we have?');
    expect(response1.length).toBeGreaterThan(0);
    console.log('✅ First message sent and received');
    
    // Wait a bit between messages
    await page.waitForTimeout(2000);
    
    // Second message (follow-up)
    const response2 = await sendMessage(page, 'Can you show me more details about them?');
    expect(response2.length).toBeGreaterThan(0);
    console.log('✅ Second message sent and received');
    
    console.log('✅ Test 5 passed: Multi-turn conversation successful');
    
    // Take screenshot
    await page.screenshot({ path: 'tests/e2e/screenshots/test5-multi-turn.png', fullPage: true });
  });
});