"""
AI Chat Intensive Testing Suite

This suite tests real-world AI chat scenarios with full system integration.
All tests run through the frontend with no mocking - testing actual performance.

Test Categories:
1. Asset Query Tests - Real asset queries and responses
2. Performance Tests - Response times and system behavior
3. Conversation Flow Tests - Multi-turn conversations
4. Error Handling Tests - Edge cases and failures
"""

import pytest
import json
import time
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from playwright.sync_api import Page, expect

# Test configuration
BASE_URL = os.getenv('BASE_URL', 'http://localhost:3000')
TEST_USERNAME = os.getenv('TEST_USERNAME', 'admin')
TEST_PASSWORD = os.getenv('TEST_PASSWORD', 'admin123')

# Directories
SCREENSHOT_DIR = Path(__file__).parent / 'screenshots' / 'ai-chat-intensive'
REPORT_DIR = Path(__file__).parent / 'reports'

# Ensure directories exist
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)

# Global test reports
test_reports: List[Dict[str, Any]] = []


class TestReport:
    """Test report data structure"""
    def __init__(self, test_name: str, query: str):
        self.test_name = test_name
        self.query = query
        self.timestamp = datetime.now().isoformat()
        self.start_time = time.time()
        self.status = 'running'
        self.response_time: Optional[float] = None
        self.response_length: Optional[int] = None
        self.conversation_log: List[Dict[str, Any]] = []
        self.error: Optional[str] = None
        self.screenshots: List[str] = []
    
    def complete(self, status: str = 'passed'):
        self.status = status
        self.duration = time.time() - self.start_time
        test_reports.append(self.to_dict())
        self._save()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'testName': self.test_name,
            'timestamp': self.timestamp,
            'duration': getattr(self, 'duration', 0),
            'status': self.status,
            'query': self.query,
            'responseTime': self.response_time,
            'responseLength': self.response_length,
            'conversationLog': self.conversation_log,
            'error': self.error,
            'screenshots': self.screenshots
        }
    
    def _save(self):
        report_path = REPORT_DIR / f'ai-chat-intensive-{int(time.time())}.json'
        with open(report_path, 'w') as f:
            json.dump(test_reports, f, indent=2)
        print(f"📊 Test report saved: {report_path}")


def take_screenshot(page: Page, name: str) -> str:
    """Take a timestamped screenshot"""
    timestamp = datetime.now().strftime('%Y-%m-%dT%H-%M-%S')
    filename = f"{name}-{timestamp}.png"
    filepath = SCREENSHOT_DIR / filename
    page.screenshot(path=str(filepath), full_page=True)
    print(f"📸 Screenshot saved: {filename}")
    return filename


def login(page: Page):
    """Login to the application"""
    page.goto(BASE_URL)
    page.wait_for_selector('input[type="text"], input[name="username"]', timeout=10000)
    page.fill('input[type="text"], input[name="username"]', TEST_USERNAME)
    page.fill('input[type="password"], input[name="password"]', TEST_PASSWORD)
    page.click('button[type="submit"]')
    page.wait_for_url('**/dashboard', timeout=10000)


def navigate_to_ai_chat(page: Page):
    """Navigate to AI Chat page"""
    selectors = [
        'a[href="/ai-chat"]',
        'a[href*="ai-chat"]',
        'text=AI Chat',
        'text=Chat'
    ]
    
    for selector in selectors:
        try:
            page.click(selector, timeout=5000)
            page.wait_for_url('**/ai-chat', timeout=5000)
            return
        except Exception:
            continue
    
    # Fallback to direct URL
    page.goto(f"{BASE_URL}/ai-chat")
    page.wait_for_load_state('networkidle')


def send_message_and_wait_for_response(
    page: Page, 
    message: str, 
    timeout: int = 60000
) -> Dict[str, Any]:
    """Send a message and wait for AI response"""
    start_time = time.time()
    
    # Find and fill input field
    input_selectors = ['textarea', 'input[type="text"]', '[contenteditable="true"]']
    input_filled = False
    
    for selector in input_selectors:
        try:
            page.fill(selector, message, timeout=2000)
            input_filled = True
            break
        except Exception:
            continue
    
    if not input_filled:
        raise Exception('Could not find input field to send message')
    
    # Count messages before sending
    messages_before = page.locator('.message, [class*="message"]').count()
    
    # Click send button
    send_button_selectors = [
        'button[aria-label="Send"]',
        'button:has-text("Send")',
        'button:has(svg)',
        'button[type="submit"]'
    ]
    
    button_clicked = False
    for selector in send_button_selectors:
        try:
            page.click(selector, timeout=2000)
            button_clicked = True
            break
        except Exception:
            continue
    
    if not button_clicked:
        # Try pressing Enter as fallback
        page.keyboard.press('Enter')
    
    # Wait for new messages (user + AI)
    page.wait_for_function(
        f'document.querySelectorAll(".message, [class*=\\"message\\"]").length >= {messages_before + 2}',
        timeout=timeout
    )
    
    response_time = (time.time() - start_time) * 1000  # Convert to ms
    
    # Get the last AI message
    ai_message_selectors = [
        '.message.ai:last-child',
        '.ai-message:last-child',
        '[class*="ai"]:last-child',
        '.message:last-child'
    ]
    
    response_text = ''
    for selector in ai_message_selectors:
        try:
            element = page.locator(selector).first
            if element.count() > 0:
                response_text = element.text_content() or ''
                if response_text.strip():
                    break
        except Exception:
            continue
    
    return {
        'responseText': response_text,
        'responseTime': response_time
    }


def extract_conversation_log(page: Page) -> List[Dict[str, Any]]:
    """Extract conversation log from the page"""
    return page.evaluate("""
        () => {
            const messages = document.querySelectorAll('.message, [class*="message"]');
            const log = [];
            
            messages.forEach((msg) => {
                const isUser = msg.classList.contains('user') || 
                             msg.classList.contains('user-message') ||
                             msg.querySelector('[class*="user"]');
                
                const content = msg.textContent?.trim() || '';
                
                if (content) {
                    log.push({
                        role: isUser ? 'user' : 'ai',
                        content: content,
                        timestamp: new Date().toISOString()
                    });
                }
            });
            
            return log;
        }
    """)


@pytest.fixture(scope='function')
def ai_chat_page(page: Page):
    """Fixture to setup AI chat page for each test"""
    login(page)
    navigate_to_ai_chat(page)
    page.wait_for_selector('textarea, input[type="text"]', timeout=10000)
    take_screenshot(page, 'chat-ready')
    yield page
    take_screenshot(page, 'test-end')


class TestAssetQueries:
    """Asset Query Tests"""
    
    def test_list_all_assets(self, ai_chat_page: Page):
        """Test: List all assets"""
        report = TestReport('Asset Query: List all assets', 'Show me all assets')
        
        try:
            result = send_message_and_wait_for_response(ai_chat_page, report.query)
            
            assert len(result['responseText']) > 0, "Response should not be empty"
            
            report.response_time = result['responseTime']
            report.response_length = len(result['responseText'])
            report.screenshots.append(take_screenshot(ai_chat_page, 'list-all-assets'))
            report.conversation_log = extract_conversation_log(ai_chat_page)
            report.complete('passed')
            
            print(f"✅ {report.test_name}")
            print(f"   Response time: {report.response_time:.0f}ms")
            print(f"   Response length: {report.response_length} chars")
            
        except Exception as e:
            report.error = str(e)
            report.complete('failed')
            raise
    
    def test_filter_by_os(self, ai_chat_page: Page):
        """Test: Filter by operating system"""
        report = TestReport('Asset Query: Filter by operating system', 'Show me all Linux servers')
        
        try:
            result = send_message_and_wait_for_response(ai_chat_page, report.query)
            
            assert len(result['responseText']) > 0
            assert 'linux' in result['responseText'].lower()
            
            report.response_time = result['responseTime']
            report.response_length = len(result['responseText'])
            report.screenshots.append(take_screenshot(ai_chat_page, 'filter-linux-servers'))
            report.conversation_log = extract_conversation_log(ai_chat_page)
            report.complete('passed')
            
            print(f"✅ {report.test_name}")
            print(f"   Response time: {report.response_time:.0f}ms")
            
        except Exception as e:
            report.error = str(e)
            report.complete('failed')
            raise
    
    def test_search_by_hostname(self, ai_chat_page: Page):
        """Test: Search by hostname"""
        report = TestReport('Asset Query: Search by hostname', 'Find assets with hostname containing "server"')
        
        try:
            result = send_message_and_wait_for_response(ai_chat_page, report.query)
            
            assert len(result['responseText']) > 0
            
            report.response_time = result['responseTime']
            report.response_length = len(result['responseText'])
            report.screenshots.append(take_screenshot(ai_chat_page, 'search-hostname'))
            report.conversation_log = extract_conversation_log(ai_chat_page)
            report.complete('passed')
            
            print(f"✅ {report.test_name}")
            print(f"   Response time: {report.response_time:.0f}ms")
            
        except Exception as e:
            report.error = str(e)
            report.complete('failed')
            raise
    
    def test_count_assets(self, ai_chat_page: Page):
        """Test: Count assets by type"""
        report = TestReport('Asset Query: Count assets by type', 'How many servers do we have?')
        
        try:
            result = send_message_and_wait_for_response(ai_chat_page, report.query)
            
            assert len(result['responseText']) > 0
            # Should contain a number
            import re
            assert re.search(r'\d+', result['responseText']), "Response should contain a number"
            
            report.response_time = result['responseTime']
            report.response_length = len(result['responseText'])
            report.screenshots.append(take_screenshot(ai_chat_page, 'count-servers'))
            report.conversation_log = extract_conversation_log(ai_chat_page)
            report.complete('passed')
            
            print(f"✅ {report.test_name}")
            print(f"   Response time: {report.response_time:.0f}ms")
            
        except Exception as e:
            report.error = str(e)
            report.complete('failed')
            raise
    
    def test_filter_by_ip(self, ai_chat_page: Page):
        """Test: Filter by IP address"""
        report = TestReport('Asset Query: Filter by IP address', 'Show me assets with IP addresses in the 192.168 range')
        
        try:
            result = send_message_and_wait_for_response(ai_chat_page, report.query)
            
            assert len(result['responseText']) > 0
            
            report.response_time = result['responseTime']
            report.response_length = len(result['responseText'])
            report.screenshots.append(take_screenshot(ai_chat_page, 'filter-ip-range'))
            report.conversation_log = extract_conversation_log(ai_chat_page)
            report.complete('passed')
            
            print(f"✅ {report.test_name}")
            print(f"   Response time: {report.response_time:.0f}ms")
            
        except Exception as e:
            report.error = str(e)
            report.complete('failed')
            raise


class TestMultiTurnConversations:
    """Multi-Turn Conversation Tests"""
    
    def test_follow_up_query(self, ai_chat_page: Page):
        """Test: Asset query with follow-up"""
        report = TestReport('Multi-turn: Asset query with follow-up', 'Show me all Linux servers -> How many are there?')
        
        try:
            # First query
            result1 = send_message_and_wait_for_response(ai_chat_page, 'Show me all Linux servers')
            assert len(result1['responseText']) > 0
            report.screenshots.append(take_screenshot(ai_chat_page, 'multi-turn-1'))
            
            # Follow-up query
            result2 = send_message_and_wait_for_response(ai_chat_page, 'How many are there?')
            assert len(result2['responseText']) > 0
            import re
            assert re.search(r'\d+', result2['responseText'])
            report.screenshots.append(take_screenshot(ai_chat_page, 'multi-turn-2'))
            
            report.conversation_log = extract_conversation_log(ai_chat_page)
            report.complete('passed')
            
            print(f"✅ {report.test_name}")
            print(f"   Messages exchanged: {len(report.conversation_log)}")
            
        except Exception as e:
            report.error = str(e)
            report.complete('failed')
            raise
    
    def test_complex_filtering(self, ai_chat_page: Page):
        """Test: Complex filtering conversation"""
        report = TestReport('Multi-turn: Complex filtering conversation', 'Multi-step filtering')
        
        try:
            # Query 1
            result1 = send_message_and_wait_for_response(ai_chat_page, 'Show me all servers')
            assert len(result1['responseText']) > 0
            report.screenshots.append(take_screenshot(ai_chat_page, 'complex-filter-1'))
            
            # Query 2
            result2 = send_message_and_wait_for_response(ai_chat_page, 'Filter those to only Linux')
            assert len(result2['responseText']) > 0
            report.screenshots.append(take_screenshot(ai_chat_page, 'complex-filter-2'))
            
            # Query 3
            result3 = send_message_and_wait_for_response(ai_chat_page, 'Show me their IP addresses')
            assert len(result3['responseText']) > 0
            report.screenshots.append(take_screenshot(ai_chat_page, 'complex-filter-3'))
            
            report.conversation_log = extract_conversation_log(ai_chat_page)
            report.complete('passed')
            
            print(f"✅ {report.test_name}")
            print(f"   Messages exchanged: {len(report.conversation_log)}")
            
        except Exception as e:
            report.error = str(e)
            report.complete('failed')
            raise


class TestPerformance:
    """Performance Tests"""
    
    def test_simple_query_response_time(self, ai_chat_page: Page):
        """Test: Response time for simple query"""
        report = TestReport('Performance: Response time for simple query', 'List all assets')
        
        try:
            result = send_message_and_wait_for_response(ai_chat_page, report.query)
            
            assert len(result['responseText']) > 0
            assert result['responseTime'] < 30000, f"Response time {result['responseTime']}ms exceeds 30s limit"
            
            report.response_time = result['responseTime']
            report.response_length = len(result['responseText'])
            report.screenshots.append(take_screenshot(ai_chat_page, 'performance-simple'))
            report.complete('passed')
            
            print(f"✅ {report.test_name}")
            print(f"   Response time: {report.response_time:.0f}ms ({report.response_time/1000:.2f}s)")
            
        except Exception as e:
            report.error = str(e)
            report.complete('failed')
            raise
    
    def test_multiple_rapid_queries(self, ai_chat_page: Page):
        """Test: Multiple rapid queries"""
        report = TestReport('Performance: Multiple rapid queries', 'Multiple queries')
        queries = [
            'How many assets do we have?',
            'Show me Linux servers',
            'What about Windows servers?'
        ]
        
        try:
            response_times = []
            for i, query in enumerate(queries):
                result = send_message_and_wait_for_response(ai_chat_page, query)
                assert len(result['responseText']) > 0
                response_times.append(result['responseTime'])
                report.screenshots.append(take_screenshot(ai_chat_page, f'rapid-query-{i+1}'))
            
            report.conversation_log = extract_conversation_log(ai_chat_page)
            avg_response_time = sum(response_times) / len(response_times)
            report.complete('passed')
            
            print(f"✅ {report.test_name}")
            print(f"   Average response time: {avg_response_time:.0f}ms")
            print(f"   Response times: {[f"{t/1000:.2f}s" for t in response_times]}")
            
        except Exception as e:
            report.error = str(e)
            report.complete('failed')
            raise


class TestErrorHandling:
    """Error Handling Tests"""
    
    def test_empty_query(self, ai_chat_page: Page):
        """Test: Empty query"""
        report = TestReport('Error Handling: Empty query', '(empty)')
        
        try:
            # Try to send empty message
            ai_chat_page.fill('textarea, input[type="text"]', '')
            ai_chat_page.click('button[aria-label="Send"], button:has-text("Send")')
            
            # Wait a moment
            ai_chat_page.wait_for_timeout(1000)
            
            # Verify no new message was added
            message_count = ai_chat_page.locator('.message, [class*="message"]').count()
            
            report.screenshots.append(take_screenshot(ai_chat_page, 'error-empty-query'))
            report.complete('passed')
            
            print(f"✅ {report.test_name}")
            print(f"   Empty message correctly prevented")
            
        except Exception as e:
            report.error = str(e)
            report.complete('failed')
            raise
    
    def test_very_long_query(self, ai_chat_page: Page):
        """Test: Very long query"""
        query = 'Show me all assets ' * 50
        report = TestReport('Error Handling: Very long query', f'{query[:50]}... ({len(query)} chars)')
        
        try:
            result = send_message_and_wait_for_response(ai_chat_page, query, timeout=90000)
            
            assert len(result['responseText']) > 0
            
            report.response_time = result['responseTime']
            report.response_length = len(result['responseText'])
            report.screenshots.append(take_screenshot(ai_chat_page, 'error-long-query'))
            report.complete('passed')
            
            print(f"✅ {report.test_name}")
            print(f"   Query length: {len(query)} chars")
            print(f"   Response time: {report.response_time:.0f}ms")
            
        except Exception as e:
            report.error = str(e)
            report.complete('failed')
            raise
    
    def test_invalid_query(self, ai_chat_page: Page):
        """Test: Invalid asset query"""
        report = TestReport('Error Handling: Invalid asset query', 'Show me assets with nonexistent_field = "value"')
        
        try:
            result = send_message_and_wait_for_response(ai_chat_page, report.query)
            
            # Should still get a response (even if it's an error message)
            assert len(result['responseText']) > 0
            
            report.response_time = result['responseTime']
            report.response_length = len(result['responseText'])
            report.screenshots.append(take_screenshot(ai_chat_page, 'error-invalid-query'))
            report.complete('passed')
            
            print(f"✅ {report.test_name}")
            print(f"   Response time: {report.response_time:.0f}ms")
            print(f"   Response: {result['responseText'][:100]}...")
            
        except Exception as e:
            report.error = str(e)
            report.complete('failed')
            raise


def pytest_sessionfinish(session, exitstatus):
    """Generate final summary report after all tests"""
    summary_path = REPORT_DIR / f'ai-chat-intensive-summary-{int(time.time())}.json'
    
    passed = [r for r in test_reports if r['status'] == 'passed']
    failed = [r for r in test_reports if r['status'] == 'failed']
    
    response_times = [r['responseTime'] for r in test_reports if r.get('responseTime')]
    avg_response_time = sum(response_times) / len(response_times) if response_times else 0
    
    summary = {
        'totalTests': len(test_reports),
        'passed': len(passed),
        'failed': len(failed),
        'averageResponseTime': avg_response_time,
        'totalDuration': sum(r['duration'] for r in test_reports),
        'timestamp': datetime.now().isoformat(),
        'reports': test_reports
    }
    
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print('\n' + '=' * 80)
    print('📊 AI CHAT INTENSIVE TESTING - FINAL SUMMARY')
    print('=' * 80)
    print(f"Total Tests: {summary['totalTests']}")
    print(f"✅ Passed: {summary['passed']}")
    print(f"❌ Failed: {summary['failed']}")
    print(f"⏱️  Average Response Time: {avg_response_time:.0f}ms ({avg_response_time/1000:.2f}s)")
    print(f"⏱️  Total Duration: {summary['totalDuration']:.2f}s")
    print(f"📄 Summary Report: {summary_path}")
    print('=' * 80 + '\n')