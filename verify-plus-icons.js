const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({
    headless: true,
    args: ['--ignore-certificate-errors', '--ignore-ssl-errors']
  });
  
  const page = await browser.newPage();
  
  try {
    console.log('Navigating to application...');
    await page.goto('https://localhost', { 
      waitUntil: 'networkidle',
      timeout: 30000
    });
    
    console.log('Logging in...');
    await page.fill('input[type="text"]', 'admin');
    await page.fill('input[type="password"]', 'admin123');
    await page.click('button[type="submit"]');
    
    console.log('Waiting for dashboard...');
    await page.waitForSelector('.action-btn', { timeout: 15000 });
    
    console.log('Checking for Plus icons...');
    const plusIcons = await page.locator('svg[data-lucide="plus"]').count();
    
    console.log(`Found ${plusIcons} Plus icons on the dashboard`);
    
    if (plusIcons >= 3) {
      console.log('✅ VERIFICATION COMPLETE: Plus icons are visible on the dashboard');
      process.exit(0);
    } else {
      console.log('❌ VERIFICATION FAILED: Plus icons are not visible');
      process.exit(1);
    }
    
  } catch (error) {
    console.log('Error during verification:', error.message);
    process.exit(1);
  } finally {
    await browser.close();
  }
})();