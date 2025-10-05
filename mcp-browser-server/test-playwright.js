import { chromium } from 'playwright';

async function testPlaywright() {
  console.log('Starting Playwright test...');
  
  let browser;
  try {
    // Launch browser
    console.log('Launching Chromium browser...');
    browser = await chromium.launch({ headless: true });
    console.log('✓ Browser launched successfully');
    
    // Create a new page
    console.log('Creating new page...');
    const page = await browser.newPage();
    console.log('✓ Page created successfully');
    
    // Navigate to a test page
    console.log('Navigating to example.com...');
    await page.goto('https://example.com');
    console.log('✓ Navigation successful');
    
    // Get page title
    const title = await page.title();
    console.log(`✓ Page title: "${title}"`);
    
    // Take a screenshot
    console.log('Taking screenshot...');
    await page.screenshot({ path: 'test-screenshot.png' });
    console.log('✓ Screenshot saved as test-screenshot.png');
    
    // Get some content
    const heading = await page.textContent('h1');
    console.log(`✓ Page heading: "${heading}"`);
    
    console.log('\n✅ All tests passed! Playwright is working correctly.');
    
  } catch (error) {
    console.error('\n❌ Test failed:', error.message);
    process.exit(1);
  } finally {
    if (browser) {
      await browser.close();
      console.log('✓ Browser closed');
    }
  }
}

// Run the test
testPlaywright().catch(console.error);