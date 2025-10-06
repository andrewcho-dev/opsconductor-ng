"""
Basic End-to-End Tests

Tests the core functionality after tool registry removal:
1. Login
2. Navigate to AI Chat
3. Send basic queries
4. Verify responses
"""

import os
import time
from pathlib import Path
from playwright.sync_api import sync_playwright, Page, expect

# Test configuration
BASE_URL = os.getenv('BASE_URL', 'http://localhost:3100')
TEST_USERNAME = os.getenv('TEST_USERNAME', 'admin')
TEST_PASSWORD = os.getenv('TEST_PASSWORD', 'admin')

# Directories
SCREENSHOT_DIR = Path(__file__).parent / 'screenshots'
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)


def login(page: Page):
    """Login to the application"""
    print(f"🔐 Logging in to {BASE_URL}...")
    page.goto(BASE_URL)
    
    # Wait for login form
    page.wait_for_selector('input[type="text"], input[name="username"]', timeout=15000)
    
    # Fill credentials
    page.fill('input[type="text"], input[name="username"]', TEST_USERNAME)
    page.fill('input[type="password"], input[name="password"]', TEST_PASSWORD)
    
    # Submit
    page.click('button[type="submit"]')
    
    # Wait for redirect
    page.wait_for_url('**/dashboard', timeout=15000)
    print("✅ Login successful")


def navigate_to_ai_chat(page: Page):
    """Navigate to AI Chat page"""
    print("🧭 Navigating to AI Chat...")
    
    # Check if already on AI Chat page
    if 'ai-chat' in page.url:
        print("✅ Already on AI Chat page")
        return
    
    # Try multiple selectors
    selectors = [
        'a[href="/ai-chat"]',
        'a[href*="ai-chat"]',
        'text=AI Chat',
        'text=Chat'
    ]
    
    for selector in selectors:
        try:
            element = page.locator(selector).first
            if element.count() > 0:
                element.click(timeout=5000)
                page.wait_for_url('**/ai-chat', timeout=5000)
                print("✅ Navigated to AI Chat")
                return
        except Exception:
            continue
    
    # Direct URL as fallback
    print("⚠️  Navigation link not found, trying direct URL...")
    page.goto(f"{BASE_URL}/ai-chat")
    page.wait_for_load_state('networkidle')
    print("✅ Navigated to AI Chat via direct URL")


def send_message(page: Page, message: str, timeout: int = 90000) -> str:
    """Send a message and wait for response"""
    print(f"📤 Sending message: \"{message}\"")
    start_time = time.time()
    
    # Find input field
    input_selectors = [
        'textarea[placeholder*="message" i]',
        'textarea[placeholder*="type" i]',
        'textarea',
        'input[type="text"]'
    ]
    
    input_element = None
    for selector in input_selectors:
        try:
            element = page.locator(selector).first
            if element.count() > 0 and element.is_visible():
                input_element = element
                break
        except Exception:
            continue
    
    if not input_element:
        raise Exception("Could not find input field")
    
    # Clear and fill input
    input_element.clear()
    input_element.fill(message)
    
    # Count messages before sending
    messages_before = page.locator('[class*="message"], .message').count()
    print(f"📊 Messages before: {messages_before}")
    
    # Find and click send button
    send_button_selectors = [
        'button[aria-label*="send" i]',
        'button:has-text("Send")',
        'button[type="submit"]'
    ]
    
    button_clicked = False
    for selector in send_button_selectors:
        try:
            button = page.locator(selector).first
            if button.count() > 0 and button.is_visible():
                button.click()
                button_clicked = True
                print("✅ Send button clicked")
                break
        except Exception:
            continue
    
    if not button_clicked:
        print("⚠️  Send button not found, trying Enter key...")
        input_element.press('Enter')
    
    # Wait for AI response
    print("⏳ Waiting for AI response...")
    page.wait_for_function(
        f"""
        () => {{
            const messages = document.querySelectorAll('[class*="message"], .message');
            return messages.length >= {messages_before + 2};
        }}
        """,
        timeout=timeout
    )
    
    response_time = (time.time() - start_time) * 1000
    print(f"✅ Response received in {response_time:.0f}ms")
    
    # Get the last message (AI response)
    all_messages = page.locator('[class*="message"], .message')
    last_message = all_messages.last
    response_text = last_message.text_content() or ''
    
    print(f"📥 Response preview: {response_text[:100]}...")
    
    return response_text


def run_tests():
    """Run all basic e2e tests"""
    print("\n" + "="*80)
    print("🧪 BASIC END-TO-END TESTS")
    print("   Database as Single Source of Truth")
    print("="*80 + "\n")
    
    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = context.new_page()
        
        try:
            # Setup
            login(page)
            navigate_to_ai_chat(page)
            
            # Wait for chat interface
            page.wait_for_selector('textarea, input[type="text"]', timeout=10000)
            print("✅ Chat interface ready\n")
            
            # Test 1: Simple information request
            print("\n" + "-"*80)
            print("🧪 TEST 1: Simple information request")
            print("-"*80)
            response1 = send_message(page, "What can you help me with?")
            assert len(response1) > 0, "Response should not be empty"
            print("✅ Test 1 PASSED: Received non-empty response\n")
            page.screenshot(path=str(SCREENSHOT_DIR / 'test1-info-request.png'), full_page=True)
            
            time.sleep(2)  # Brief pause between tests
            
            # Test 2: Asset query - list all assets
            print("\n" + "-"*80)
            print("🧪 TEST 2: Asset query - list all assets")
            print("-"*80)
            response2 = send_message(page, "Show me all assets")
            assert len(response2) > 0, "Response should not be empty"
            assert any(word in response2.lower() for word in ['asset', 'server', 'host']), \
                "Response should mention assets"
            print("✅ Test 2 PASSED: Received asset-related response\n")
            page.screenshot(path=str(SCREENSHOT_DIR / 'test2-list-assets.png'), full_page=True)
            
            time.sleep(2)
            
            # Test 3: Asset query - filter by OS
            print("\n" + "-"*80)
            print("🧪 TEST 3: Asset query - filter by OS")
            print("-"*80)
            response3 = send_message(page, "Show me all Linux servers")
            assert len(response3) > 0, "Response should not be empty"
            print("✅ Test 3 PASSED: Received response for Linux servers query\n")
            page.screenshot(path=str(SCREENSHOT_DIR / 'test3-linux-servers.png'), full_page=True)
            
            time.sleep(2)
            
            # Test 4: System information query
            print("\n" + "-"*80)
            print("🧪 TEST 4: System information query")
            print("-"*80)
            response4 = send_message(page, "What is the system status?")
            assert len(response4) > 0, "Response should not be empty"
            print("✅ Test 4 PASSED: Received system status response\n")
            page.screenshot(path=str(SCREENSHOT_DIR / 'test4-system-status.png'), full_page=True)
            
            time.sleep(2)
            
            # Test 5: Multi-turn conversation
            print("\n" + "-"*80)
            print("🧪 TEST 5: Multi-turn conversation")
            print("-"*80)
            response5a = send_message(page, "How many assets do we have?")
            assert len(response5a) > 0, "First response should not be empty"
            print("✅ First message sent and received")
            
            time.sleep(2)
            
            response5b = send_message(page, "Can you show me more details about them?")
            assert len(response5b) > 0, "Second response should not be empty"
            print("✅ Second message sent and received")
            print("✅ Test 5 PASSED: Multi-turn conversation successful\n")
            page.screenshot(path=str(SCREENSHOT_DIR / 'test5-multi-turn.png'), full_page=True)
            
            # Summary
            print("\n" + "="*80)
            print("🎉 ALL TESTS PASSED!")
            print("="*80)
            print("\n✅ 5/5 tests passed")
            print(f"📸 Screenshots saved to: {SCREENSHOT_DIR}")
            print("\n")
            
        except Exception as e:
            print(f"\n❌ TEST FAILED: {e}")
            page.screenshot(path=str(SCREENSHOT_DIR / 'test-failure.png'), full_page=True)
            raise
        
        finally:
            browser.close()


if __name__ == '__main__':
    run_tests()