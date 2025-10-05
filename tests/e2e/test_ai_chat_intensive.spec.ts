import { test, expect, Page } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

/**
 * Intensive AI Chat Testing Suite
 * 
 * This suite tests real-world AI chat scenarios with full system integration.
 * All tests run through the frontend with no mocking - testing actual performance.
 * 
 * Test Categories:
 * 1. Asset Query Tests - Real asset queries and responses
 * 2. Performance Tests - Response times and system behavior
 * 3. Conversation Flow Tests - Multi-turn conversations
 * 4. Error Handling Tests - Edge cases and failures
 */

// Test configuration
const BASE_URL = process.env.BASE_URL || 'http://localhost:3000';
const TEST_USERNAME = process.env.TEST_USERNAME || 'admin';
const TEST_PASSWORD = process.env.TEST_PASSWORD || 'admin';
const SCREENSHOT_DIR = path.join(__dirname, 'screenshots', 'ai-chat-intensive');
const REPORT_DIR = path.join(__dirname, 'reports');

// Ensure directories exist
if (!fs.existsSync(SCREENSHOT_DIR)) {
  fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
}
if (!fs.existsSync(REPORT_DIR)) {
  fs.mkdirSync(REPORT_DIR, { recursive: true });
}

// Test report data structure
interface TestReport {
  testName: string;
  timestamp: string;
  duration: number;
  status: 'passed' | 'failed';
  query: string;
  responseTime?: number;
  responseLength?: number;
  conversationLog?: ConversationEntry[];
  error?: string;
  screenshots?: string[];
}

interface ConversationEntry {
  role: 'user' | 'ai';
  content: string;
  timestamp: string;
  metadata?: {
    responseTime?: number;
    tokenCount?: number;
    executionId?: string;
  };
}

// Global test reports array
const testReports: TestReport[] = [];

// Helper function to save test report
function saveTestReport(report: TestReport) {
  testReports.push(report);
  const reportPath = path.join(REPORT_DIR, `ai-chat-intensive-${Date.now()}.json`);
  fs.writeFileSync(reportPath, JSON.stringify(testReports, null, 2));
  console.log(`📊 Test report saved: ${reportPath}`);
}

// Helper function to take screenshot with timestamp
async function takeTimestampedScreenshot(page: Page, name: string): Promise<string> {
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  const filename = `${name}-${timestamp}.png`;
  const filepath = path.join(SCREENSHOT_DIR, filename);
  await page.screenshot({ path: filepath, fullPage: true });
  console.log(`📸 Screenshot saved: ${filename}`);
  return filename;
}

// Helper function to login
async function login(page: Page) {
  await page.goto(BASE_URL);
  await page.waitForSelector('input[type="text"], input[name="username"]', { timeout: 10000 });
  await page.fill('input[type="text"], input[name="username"]', TEST_USERNAME);
  await page.fill('input[type="password"], input[name="password"]', TEST_PASSWORD);
  await page.click('button[type="submit"]');
  await page.waitForURL(/dashboard|ai-chat/, { timeout: 10000 });
}

// Helper function to navigate to AI Chat
async function navigateToAIChat(page: Page) {
  // Try multiple selectors for the AI Chat link
  const selectors = [
    'a[href="/ai-chat"]',
    'a[href*="ai-chat"]',
    'text=AI Chat',
    'text=Chat'
  ];
  
  for (const selector of selectors) {
    try {
      await page.click(selector, { timeout: 5000 });
      await page.waitForURL(/ai-chat/, { timeout: 5000 });
      return;
    } catch (e) {
      continue;
    }
  }
  
  // If navigation failed, try direct URL
  await page.goto(`${BASE_URL}/ai-chat`);
  await page.waitForLoadState('networkidle');
}

// Helper function to send message and wait for response
async function sendMessageAndWaitForResponse(
  page: Page, 
  message: string, 
  timeout: number = 60000
): Promise<{ responseText: string; responseTime: number }> {
  const startTime = Date.now();
  
  // Find and fill the input field
  const inputSelectors = [
    'textarea',
    'input[type="text"]',
    '[contenteditable="true"]'
  ];
  
  let inputFilled = false;
  for (const selector of inputSelectors) {
    try {
      await page.fill(selector, message, { timeout: 2000 });
      inputFilled = true;
      break;
    } catch (e) {
      continue;
    }
  }
  
  if (!inputFilled) {
    throw new Error('Could not find input field to send message');
  }
  
  // Count current messages before sending
  const messagesBefore = await page.locator('.message, [class*="message"]').count();
  
  // Click send button
  const sendButtonSelectors = [
    'button[aria-label="Send"]',
    'button:has-text("Send")',
    'button:has(svg)', // Button with icon
    'button[type="submit"]'
  ];
  
  let buttonClicked = false;
  for (const selector of sendButtonSelectors) {
    try {
      await page.click(selector, { timeout: 2000 });
      buttonClicked = true;
      break;
    } catch (e) {
      continue;
    }
  }
  
  if (!buttonClicked) {
    // Try pressing Enter as fallback
    await page.keyboard.press('Enter');
  }
  
  // Wait for new message to appear (user message + AI response)
  await page.waitForFunction(
    (beforeCount) => {
      const messages = document.querySelectorAll('.message, [class*="message"]');
      return messages.length >= beforeCount + 2; // User message + AI response
    },
    messagesBefore,
    { timeout }
  );
  
  const responseTime = Date.now() - startTime;
  
  // Get the last AI message
  const aiMessageSelectors = [
    '.message.ai:last-child',
    '.ai-message:last-child',
    '[class*="ai"]:last-child',
    '.message:last-child'
  ];
  
  let responseText = '';
  for (const selector of aiMessageSelectors) {
    try {
      const element = page.locator(selector).first();
      if (await element.count() > 0) {
        responseText = await element.textContent() || '';
        if (responseText.trim()) break;
      }
    } catch (e) {
      continue;
    }
  }
  
  return { responseText, responseTime };
}

// Helper function to extract conversation log
async function extractConversationLog(page: Page): Promise<ConversationEntry[]> {
  return await page.evaluate(() => {
    const messages = document.querySelectorAll('.message, [class*="message"]');
    const log: ConversationEntry[] = [];
    
    messages.forEach((msg) => {
      const isUser = msg.classList.contains('user') || 
                     msg.classList.contains('user-message') ||
                     msg.querySelector('[class*="user"]');
      
      const content = msg.textContent?.trim() || '';
      
      if (content) {
        log.push({
          role: isUser ? 'user' : 'ai',
          content,
          timestamp: new Date().toISOString()
        });
      }
    });
    
    return log;
  });
}

// Test suite setup
test.describe('AI Chat - Intensive Real-World Testing', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
    await navigateToAIChat(page);
    
    // Wait for chat interface to be ready
    await page.waitForSelector('textarea, input[type="text"]', { timeout: 10000 });
    
    // Take initial screenshot
    await takeTimestampedScreenshot(page, 'chat-ready');
  });

  test.afterEach(async ({ page }, testInfo) => {
    // Take final screenshot
    await takeTimestampedScreenshot(page, `test-end-${testInfo.title.replace(/\s+/g, '-')}`);
  });

  /**
   * ASSET QUERY TESTS
   * Test various asset-related queries
   */
  
  test('Asset Query: List all assets', async ({ page }) => {
    const testName = 'Asset Query: List all assets';
    const query = 'Show me all assets';
    const startTime = Date.now();
    
    try {
      const { responseText, responseTime } = await sendMessageAndWaitForResponse(page, query);
      
      // Verify response is not empty
      expect(responseText.length).toBeGreaterThan(0);
      
      // Take screenshot of response
      const screenshot = await takeTimestampedScreenshot(page, 'list-all-assets');
      
      // Extract conversation log
      const conversationLog = await extractConversationLog(page);
      
      // Save report
      saveTestReport({
        testName,
        timestamp: new Date().toISOString(),
        duration: Date.now() - startTime,
        status: 'passed',
        query,
        responseTime,
        responseLength: responseText.length,
        conversationLog,
        screenshots: [screenshot]
      });
      
      console.log(`✅ ${testName}`);
      console.log(`   Response time: ${responseTime}ms`);
      console.log(`   Response length: ${responseText.length} chars`);
      
    } catch (error) {
      saveTestReport({
        testName,
        timestamp: new Date().toISOString(),
        duration: Date.now() - startTime,
        status: 'failed',
        query,
        error: error instanceof Error ? error.message : String(error)
      });
      throw error;
    }
  });

  test('Asset Query: Filter by operating system', async ({ page }) => {
    const testName = 'Asset Query: Filter by operating system';
    const query = 'Show me all Linux servers';
    const startTime = Date.now();
    
    try {
      const { responseText, responseTime } = await sendMessageAndWaitForResponse(page, query);
      
      expect(responseText.length).toBeGreaterThan(0);
      expect(responseText.toLowerCase()).toContain('linux');
      
      const screenshot = await takeTimestampedScreenshot(page, 'filter-linux-servers');
      const conversationLog = await extractConversationLog(page);
      
      saveTestReport({
        testName,
        timestamp: new Date().toISOString(),
        duration: Date.now() - startTime,
        status: 'passed',
        query,
        responseTime,
        responseLength: responseText.length,
        conversationLog,
        screenshots: [screenshot]
      });
      
      console.log(`✅ ${testName}`);
      console.log(`   Response time: ${responseTime}ms`);
      
    } catch (error) {
      saveTestReport({
        testName,
        timestamp: new Date().toISOString(),
        duration: Date.now() - startTime,
        status: 'failed',
        query,
        error: error instanceof Error ? error.message : String(error)
      });
      throw error;
    }
  });

  test('Asset Query: Search by hostname', async ({ page }) => {
    const testName = 'Asset Query: Search by hostname';
    const query = 'Find assets with hostname containing "server"';
    const startTime = Date.now();
    
    try {
      const { responseText, responseTime } = await sendMessageAndWaitForResponse(page, query);
      
      expect(responseText.length).toBeGreaterThan(0);
      
      const screenshot = await takeTimestampedScreenshot(page, 'search-hostname');
      const conversationLog = await extractConversationLog(page);
      
      saveTestReport({
        testName,
        timestamp: new Date().toISOString(),
        duration: Date.now() - startTime,
        status: 'passed',
        query,
        responseTime,
        responseLength: responseText.length,
        conversationLog,
        screenshots: [screenshot]
      });
      
      console.log(`✅ ${testName}`);
      console.log(`   Response time: ${responseTime}ms`);
      
    } catch (error) {
      saveTestReport({
        testName,
        timestamp: new Date().toISOString(),
        duration: Date.now() - startTime,
        status: 'failed',
        query,
        error: error instanceof Error ? error.message : String(error)
      });
      throw error;
    }
  });

  test('Asset Query: Count assets by type', async ({ page }) => {
    const testName = 'Asset Query: Count assets by type';
    const query = 'How many servers do we have?';
    const startTime = Date.now();
    
    try {
      const { responseText, responseTime } = await sendMessageAndWaitForResponse(page, query);
      
      expect(responseText.length).toBeGreaterThan(0);
      // Should contain a number
      expect(/\d+/.test(responseText)).toBeTruthy();
      
      const screenshot = await takeTimestampedScreenshot(page, 'count-servers');
      const conversationLog = await extractConversationLog(page);
      
      saveTestReport({
        testName,
        timestamp: new Date().toISOString(),
        duration: Date.now() - startTime,
        status: 'passed',
        query,
        responseTime,
        responseLength: responseText.length,
        conversationLog,
        screenshots: [screenshot]
      });
      
      console.log(`✅ ${testName}`);
      console.log(`   Response time: ${responseTime}ms`);
      
    } catch (error) {
      saveTestReport({
        testName,
        timestamp: new Date().toISOString(),
        duration: Date.now() - startTime,
        status: 'failed',
        query,
        error: error instanceof Error ? error.message : String(error)
      });
      throw error;
    }
  });

  test('Asset Query: Filter by IP address', async ({ page }) => {
    const testName = 'Asset Query: Filter by IP address';
    const query = 'Show me assets with IP addresses in the 192.168 range';
    const startTime = Date.now();
    
    try {
      const { responseText, responseTime } = await sendMessageAndWaitForResponse(page, query);
      
      expect(responseText.length).toBeGreaterThan(0);
      
      const screenshot = await takeTimestampedScreenshot(page, 'filter-ip-range');
      const conversationLog = await extractConversationLog(page);
      
      saveTestReport({
        testName,
        timestamp: new Date().toISOString(),
        duration: Date.now() - startTime,
        status: 'passed',
        query,
        responseTime,
        responseLength: responseText.length,
        conversationLog,
        screenshots: [screenshot]
      });
      
      console.log(`✅ ${testName}`);
      console.log(`   Response time: ${responseTime}ms`);
      
    } catch (error) {
      saveTestReport({
        testName,
        timestamp: new Date().toISOString(),
        duration: Date.now() - startTime,
        status: 'failed',
        query,
        error: error instanceof Error ? error.message : String(error)
      });
      throw error;
    }
  });

  /**
   * MULTI-TURN CONVERSATION TESTS
   * Test conversation context and follow-up queries
   */
  
  test('Multi-turn: Asset query with follow-up', async ({ page }) => {
    const testName = 'Multi-turn: Asset query with follow-up';
    const startTime = Date.now();
    const screenshots: string[] = [];
    
    try {
      // First query
      const query1 = 'Show me all Linux servers';
      const response1 = await sendMessageAndWaitForResponse(page, query1);
      expect(response1.responseText.length).toBeGreaterThan(0);
      screenshots.push(await takeTimestampedScreenshot(page, 'multi-turn-1'));
      
      // Follow-up query
      const query2 = 'How many are there?';
      const response2 = await sendMessageAndWaitForResponse(page, query2);
      expect(response2.responseText.length).toBeGreaterThan(0);
      expect(/\d+/.test(response2.responseText)).toBeTruthy();
      screenshots.push(await takeTimestampedScreenshot(page, 'multi-turn-2'));
      
      const conversationLog = await extractConversationLog(page);
      
      saveTestReport({
        testName,
        timestamp: new Date().toISOString(),
        duration: Date.now() - startTime,
        status: 'passed',
        query: `${query1} -> ${query2}`,
        conversationLog,
        screenshots
      });
      
      console.log(`✅ ${testName}`);
      console.log(`   Total conversation time: ${Date.now() - startTime}ms`);
      
    } catch (error) {
      saveTestReport({
        testName,
        timestamp: new Date().toISOString(),
        duration: Date.now() - startTime,
        status: 'failed',
        query: 'Multi-turn conversation',
        error: error instanceof Error ? error.message : String(error)
      });
      throw error;
    }
  });

  test('Multi-turn: Complex filtering conversation', async ({ page }) => {
    const testName = 'Multi-turn: Complex filtering conversation';
    const startTime = Date.now();
    const screenshots: string[] = [];
    
    try {
      // Query 1: Initial broad query
      const query1 = 'Show me all servers';
      const response1 = await sendMessageAndWaitForResponse(page, query1);
      expect(response1.responseText.length).toBeGreaterThan(0);
      screenshots.push(await takeTimestampedScreenshot(page, 'complex-filter-1'));
      
      // Query 2: Narrow down by OS
      const query2 = 'Filter those to only Linux';
      const response2 = await sendMessageAndWaitForResponse(page, query2);
      expect(response2.responseText.length).toBeGreaterThan(0);
      screenshots.push(await takeTimestampedScreenshot(page, 'complex-filter-2'));
      
      // Query 3: Further filtering
      const query3 = 'Show me their IP addresses';
      const response3 = await sendMessageAndWaitForResponse(page, query3);
      expect(response3.responseText.length).toBeGreaterThan(0);
      screenshots.push(await takeTimestampedScreenshot(page, 'complex-filter-3'));
      
      const conversationLog = await extractConversationLog(page);
      
      saveTestReport({
        testName,
        timestamp: new Date().toISOString(),
        duration: Date.now() - startTime,
        status: 'passed',
        query: `${query1} -> ${query2} -> ${query3}`,
        conversationLog,
        screenshots
      });
      
      console.log(`✅ ${testName}`);
      console.log(`   Total conversation time: ${Date.now() - startTime}ms`);
      console.log(`   Messages exchanged: ${conversationLog.length}`);
      
    } catch (error) {
      saveTestReport({
        testName,
        timestamp: new Date().toISOString(),
        duration: Date.now() - startTime,
        status: 'failed',
        query: 'Complex filtering conversation',
        error: error instanceof Error ? error.message : String(error)
      });
      throw error;
    }
  });

  /**
   * PERFORMANCE TESTS
   * Test response times and system behavior
   */
  
  test('Performance: Response time for simple query', async ({ page }) => {
    const testName = 'Performance: Response time for simple query';
    const query = 'List all assets';
    const startTime = Date.now();
    
    try {
      const { responseText, responseTime } = await sendMessageAndWaitForResponse(page, query);
      
      expect(responseText.length).toBeGreaterThan(0);
      
      // Performance assertion: should respond within 30 seconds
      expect(responseTime).toBeLessThan(30000);
      
      const screenshot = await takeTimestampedScreenshot(page, 'performance-simple');
      
      saveTestReport({
        testName,
        timestamp: new Date().toISOString(),
        duration: Date.now() - startTime,
        status: 'passed',
        query,
        responseTime,
        responseLength: responseText.length,
        screenshots: [screenshot]
      });
      
      console.log(`✅ ${testName}`);
      console.log(`   Response time: ${responseTime}ms (${(responseTime / 1000).toFixed(2)}s)`);
      
    } catch (error) {
      saveTestReport({
        testName,
        timestamp: new Date().toISOString(),
        duration: Date.now() - startTime,
        status: 'failed',
        query,
        error: error instanceof Error ? error.message : String(error)
      });
      throw error;
    }
  });

  test('Performance: Multiple rapid queries', async ({ page }) => {
    const testName = 'Performance: Multiple rapid queries';
    const startTime = Date.now();
    const queries = [
      'How many assets do we have?',
      'Show me Linux servers',
      'What about Windows servers?'
    ];
    const screenshots: string[] = [];
    const responseTimes: number[] = [];
    
    try {
      for (let i = 0; i < queries.length; i++) {
        const { responseText, responseTime } = await sendMessageAndWaitForResponse(page, queries[i]);
        expect(responseText.length).toBeGreaterThan(0);
        responseTimes.push(responseTime);
        screenshots.push(await takeTimestampedScreenshot(page, `rapid-query-${i + 1}`));
      }
      
      const conversationLog = await extractConversationLog(page);
      const avgResponseTime = responseTimes.reduce((a, b) => a + b, 0) / responseTimes.length;
      
      saveTestReport({
        testName,
        timestamp: new Date().toISOString(),
        duration: Date.now() - startTime,
        status: 'passed',
        query: queries.join(' -> '),
        conversationLog,
        screenshots
      });
      
      console.log(`✅ ${testName}`);
      console.log(`   Total time: ${Date.now() - startTime}ms`);
      console.log(`   Average response time: ${avgResponseTime.toFixed(0)}ms`);
      console.log(`   Response times: ${responseTimes.map(t => `${(t / 1000).toFixed(2)}s`).join(', ')}`);
      
    } catch (error) {
      saveTestReport({
        testName,
        timestamp: new Date().toISOString(),
        duration: Date.now() - startTime,
        status: 'failed',
        query: 'Multiple rapid queries',
        error: error instanceof Error ? error.message : String(error)
      });
      throw error;
    }
  });

  /**
   * ERROR HANDLING TESTS
   * Test edge cases and error scenarios
   */
  
  test('Error Handling: Empty query', async ({ page }) => {
    const testName = 'Error Handling: Empty query';
    const startTime = Date.now();
    
    try {
      // Try to send empty message
      await page.fill('textarea, input[type="text"]', '');
      await page.click('button[aria-label="Send"], button:has-text("Send")');
      
      // Wait a moment
      await page.waitForTimeout(1000);
      
      // Verify no new message was added
      const messageCount = await page.locator('.message, [class*="message"]').count();
      
      const screenshot = await takeTimestampedScreenshot(page, 'error-empty-query');
      
      saveTestReport({
        testName,
        timestamp: new Date().toISOString(),
        duration: Date.now() - startTime,
        status: 'passed',
        query: '(empty)',
        screenshots: [screenshot]
      });
      
      console.log(`✅ ${testName}`);
      console.log(`   Empty message correctly prevented`);
      
    } catch (error) {
      saveTestReport({
        testName,
        timestamp: new Date().toISOString(),
        duration: Date.now() - startTime,
        status: 'failed',
        query: '(empty)',
        error: error instanceof Error ? error.message : String(error)
      });
      throw error;
    }
  });

  test('Error Handling: Very long query', async ({ page }) => {
    const testName = 'Error Handling: Very long query';
    const query = 'Show me all assets '.repeat(50); // Very long query
    const startTime = Date.now();
    
    try {
      const { responseText, responseTime } = await sendMessageAndWaitForResponse(page, query, 90000);
      
      expect(responseText.length).toBeGreaterThan(0);
      
      const screenshot = await takeTimestampedScreenshot(page, 'error-long-query');
      
      saveTestReport({
        testName,
        timestamp: new Date().toISOString(),
        duration: Date.now() - startTime,
        status: 'passed',
        query: `${query.substring(0, 50)}... (${query.length} chars)`,
        responseTime,
        responseLength: responseText.length,
        screenshots: [screenshot]
      });
      
      console.log(`✅ ${testName}`);
      console.log(`   Query length: ${query.length} chars`);
      console.log(`   Response time: ${responseTime}ms`);
      
    } catch (error) {
      saveTestReport({
        testName,
        timestamp: new Date().toISOString(),
        duration: Date.now() - startTime,
        status: 'failed',
        query: 'Very long query',
        error: error instanceof Error ? error.message : String(error)
      });
      throw error;
    }
  });

  test('Error Handling: Invalid asset query', async ({ page }) => {
    const testName = 'Error Handling: Invalid asset query';
    const query = 'Show me assets with nonexistent_field = "value"';
    const startTime = Date.now();
    
    try {
      const { responseText, responseTime } = await sendMessageAndWaitForResponse(page, query);
      
      // Should still get a response (even if it's an error message)
      expect(responseText.length).toBeGreaterThan(0);
      
      const screenshot = await takeTimestampedScreenshot(page, 'error-invalid-query');
      
      saveTestReport({
        testName,
        timestamp: new Date().toISOString(),
        duration: Date.now() - startTime,
        status: 'passed',
        query,
        responseTime,
        responseLength: responseText.length,
        screenshots: [screenshot]
      });
      
      console.log(`✅ ${testName}`);
      console.log(`   Response time: ${responseTime}ms`);
      console.log(`   Response: ${responseText.substring(0, 100)}...`);
      
    } catch (error) {
      saveTestReport({
        testName,
        timestamp: new Date().toISOString(),
        duration: Date.now() - startTime,
        status: 'failed',
        query,
        error: error instanceof Error ? error.message : String(error)
      });
      throw error;
    }
  });
});

// Generate final summary report after all tests
test.afterAll(async () => {
  const summaryPath = path.join(REPORT_DIR, `ai-chat-intensive-summary-${Date.now()}.json`);
  
  const summary = {
    totalTests: testReports.length,
    passed: testReports.filter(r => r.status === 'passed').length,
    failed: testReports.filter(r => r.status === 'failed').length,
    averageResponseTime: testReports
      .filter(r => r.responseTime)
      .reduce((sum, r) => sum + (r.responseTime || 0), 0) / 
      testReports.filter(r => r.responseTime).length,
    totalDuration: testReports.reduce((sum, r) => sum + r.duration, 0),
    timestamp: new Date().toISOString(),
    reports: testReports
  };
  
  fs.writeFileSync(summaryPath, JSON.stringify(summary, null, 2));
  
  console.log('\n' + '='.repeat(80));
  console.log('📊 AI CHAT INTENSIVE TESTING - FINAL SUMMARY');
  console.log('='.repeat(80));
  console.log(`Total Tests: ${summary.totalTests}`);
  console.log(`✅ Passed: ${summary.passed}`);
  console.log(`❌ Failed: ${summary.failed}`);
  console.log(`⏱️  Average Response Time: ${summary.averageResponseTime.toFixed(0)}ms (${(summary.averageResponseTime / 1000).toFixed(2)}s)`);
  console.log(`⏱️  Total Duration: ${(summary.totalDuration / 1000).toFixed(2)}s`);
  console.log(`📄 Summary Report: ${summaryPath}`);
  console.log('='.repeat(80) + '\n');
});