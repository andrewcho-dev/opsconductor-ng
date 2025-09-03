const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--ignore-certificate-errors']
  });
  
  const page = await browser.newPage();
  
  try {
    // Navigate to the login page
    await page.goto('https://localhost', { 
      waitUntil: 'networkidle0',
      timeout: 30000
    });
    
    // Login
    await page.type('input[type="text"]', 'admin');
    await page.type('input[type="password"]', 'admin123');
    await page.click('button[type="submit"]');
    
    // Wait for dashboard to load
    await page.waitForSelector('.action-btn', { timeout: 10000 });
    
    // Check for Plus icons in the action buttons
    const plusIcons = await page.$$eval('svg[data-lucide="plus"]', icons => icons.length);
    
    console.log(`Found ${plusIcons} Plus icons on the dashboard`);
    
    if (plusIcons >= 3) {
      console.log('✅ VERIFICATION COMPLETE: Plus icons are visible on the dashboard');
    } else {
      console.log('❌ VERIFICATION FAILED: Plus icons are not visible');
    }
    
  } catch (error) {
    console.log('Error during verification:', error.message);
  }
  
  await browser.close();
})();