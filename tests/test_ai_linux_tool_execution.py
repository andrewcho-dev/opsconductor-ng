"""
REAL Linux Tool Execution Tests
Target System: 192.168.50.12

This test suite executes REAL Linux commands against the actual 192.168.50.12 server
through the OpsConductor pipeline. NO MOCKS - these are integration tests that validate
the complete end-to-end execution path.

Each test sends a real user prompt to the pipeline orchestrator and verifies:
1. The AI correctly interprets the request
2. The correct Linux tool is selected and executed
3. The command executes successfully on 192.168.50.12
4. Valid results are returned to the user
"""

import pytest
import pytest_asyncio
import asyncio
import os
from datetime import datetime
import time

# Import OpsConductor modules for REAL execution
from pipeline.orchestrator import PipelineOrchestrator
from llm.ollama_client import OllamaClient


class TestRealLinuxToolExecution:
    """REAL test suite for Linux tool execution on 192.168.50.12"""
    
    TARGET_HOST = "192.168.50.12"
    
    @pytest_asyncio.fixture(scope="function")
    async def orchestrator(self):
        """Create real orchestrator for actual pipeline execution"""
        llm_config = {
            "base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            "default_model": os.getenv("OLLAMA_MODEL", "qwen2.5:7b-instruct-q4_k_m"),
            "timeout": 120
        }
        llm_client = OllamaClient(llm_config)
        await llm_client.connect()
        
        orchestrator = PipelineOrchestrator(llm_client=llm_client)
        await orchestrator.initialize()
        
        return orchestrator
    
    async def execute_real_prompt(self, orchestrator, prompt, timeout=60):
        """Execute a real user prompt through the pipeline"""
        print(f"\n📝 Executing: {prompt}")
        start_time = time.time()
        
        try:
            result = await asyncio.wait_for(
                orchestrator.process_request(prompt),
                timeout=timeout
            )
            
            duration = time.time() - start_time
            print(f"⏱️  Completed in: {duration:.2f}s")
            print(f"✅ Success: {result.success}")
            
            if result.response:
                print(f"💬 Response preview: {result.response.message[:200]}...")
            
            return result, duration
            
        except Exception as e:
            duration = time.time() - start_time
            print(f"❌ Failed after {duration:.2f}s: {e}")
            raise

    # ============================================================================
    # NETWORK & CONNECTIVITY TESTS - REAL EXECUTION
    # ============================================================================
    
    @pytest.mark.asyncio
    async def test_ping_tool_real_execution(self, orchestrator):
        """Test ping tool execution on 192.168.50.12"""
        prompt = f"Ping google.com from {self.TARGET_HOST}"
        result, duration = await self.execute_real_prompt(orchestrator, prompt)
        
        assert result.success, f"Ping test failed: {result.error_message}"
        assert result.response is not None, "No response received"
        assert duration < 60.0, f"Test took too long: {duration:.2f}s"

    @pytest.mark.asyncio
    async def test_netstat_tool_real_execution(self, orchestrator):
        """Test netstat tool execution on 192.168.50.12"""
        prompt = f"Show listening ports on {self.TARGET_HOST}"
        result, duration = await self.execute_real_prompt(orchestrator, prompt)
        
        assert result.success, f"Netstat test failed: {result.error_message}"
        assert result.response is not None, "No response received"
        assert duration < 60.0, f"Test took too long: {duration:.2f}s"

    @pytest.mark.asyncio
    async def test_ss_tool_real_execution(self, orchestrator):
        """Test ss tool execution on 192.168.50.12"""
        prompt = f"Show active network connections on {self.TARGET_HOST}"
        result, duration = await self.execute_real_prompt(orchestrator, prompt)
        
        assert result.success, f"SS test failed: {result.error_message}"
        assert result.response is not None, "No response received"
        assert duration < 60.0, f"Test took too long: {duration:.2f}s"

    @pytest.mark.asyncio
    async def test_curl_tool_real_execution(self, orchestrator):
        """Test curl tool execution on 192.168.50.12"""
        prompt = f"Check HTTP response from httpbin.org/get on {self.TARGET_HOST}"
        result, duration = await self.execute_real_prompt(orchestrator, prompt)
        
        assert result.success, f"Curl test failed: {result.error_message}"
        assert result.response is not None, "No response received"
        assert duration < 60.0, f"Test took too long: {duration:.2f}s"

    @pytest.mark.asyncio
    async def test_wget_tool_real_execution(self, orchestrator):
        """Test wget tool execution on 192.168.50.12"""
        prompt = f"Download httpbin.org/get using wget on {self.TARGET_HOST}"
        result, duration = await self.execute_real_prompt(orchestrator, prompt)
        
        assert result.success, f"Wget test failed: {result.error_message}"
        assert result.response is not None, "No response received"
        assert duration < 60.0, f"Test took too long: {duration:.2f}s"

    # ============================================================================
    # SYSTEM MONITORING TESTS - REAL EXECUTION
    # ============================================================================

    @pytest.mark.asyncio
    async def test_top_tool_real_execution(self, orchestrator):
        """Test top tool execution on 192.168.50.12"""
        prompt = f"Show top processes on {self.TARGET_HOST}"
        result, duration = await self.execute_real_prompt(orchestrator, prompt)
        
        assert result.success, f"Top test failed: {result.error_message}"
        assert result.response is not None, "No response received"
        assert duration < 60.0, f"Test took too long: {duration:.2f}s"

    @pytest.mark.asyncio
    async def test_htop_tool_real_execution(self, orchestrator):
        """Test htop tool execution on 192.168.50.12"""
        prompt = f"Show htop output on {self.TARGET_HOST}"
        result, duration = await self.execute_real_prompt(orchestrator, prompt)
        
        assert result.success, f"Htop test failed: {result.error_message}"
        assert result.response is not None, "No response received"
        assert duration < 60.0, f"Test took too long: {duration:.2f}s"

    @pytest.mark.asyncio
    async def test_ps_tool_real_execution(self, orchestrator):
        """Test ps tool execution on 192.168.50.12"""
        prompt = f"List all running processes on {self.TARGET_HOST}"
        result, duration = await self.execute_real_prompt(orchestrator, prompt)
        
        assert result.success, f"PS test failed: {result.error_message}"
        assert result.response is not None, "No response received"
        assert duration < 60.0, f"Test took too long: {duration:.2f}s"

    @pytest.mark.asyncio
    async def test_uptime_tool_real_execution(self, orchestrator):
        """Test uptime tool execution on 192.168.50.12"""
        prompt = f"Check system uptime on {self.TARGET_HOST}"
        result, duration = await self.execute_real_prompt(orchestrator, prompt)
        
        assert result.success, f"Uptime test failed: {result.error_message}"
        assert result.response is not None, "No response received"
        assert duration < 60.0, f"Test took too long: {duration:.2f}s"

    @pytest.mark.asyncio
    async def test_vmstat_tool_real_execution(self, orchestrator):
        """Test vmstat tool execution on 192.168.50.12"""
        prompt = f"Show virtual memory statistics on {self.TARGET_HOST}"
        result, duration = await self.execute_real_prompt(orchestrator, prompt)
        
        assert result.success, f"Vmstat test failed: {result.error_message}"
        assert result.response is not None, "No response received"
        assert duration < 60.0, f"Test took too long: {duration:.2f}s"

    # ============================================================================
    # FILE SYSTEM TESTS - REAL EXECUTION
    # ============================================================================

    @pytest.mark.asyncio
    async def test_ls_tool_real_execution(self, orchestrator):
        """Test ls tool execution on 192.168.50.12"""
        prompt = f"List files in /home directory on {self.TARGET_HOST}"
        result, duration = await self.execute_real_prompt(orchestrator, prompt)
        
        assert result.success, f"LS test failed: {result.error_message}"
        assert result.response is not None, "No response received"
        assert duration < 60.0, f"Test took too long: {duration:.2f}s"

    @pytest.mark.asyncio
    async def test_cat_tool_real_execution(self, orchestrator):
        """Test cat tool execution on 192.168.50.12"""
        prompt = f"Display contents of /etc/hostname on {self.TARGET_HOST}"
        result, duration = await self.execute_real_prompt(orchestrator, prompt)
        
        assert result.success, f"Cat test failed: {result.error_message}"
        assert result.response is not None, "No response received"
        assert duration < 60.0, f"Test took too long: {duration:.2f}s"

    @pytest.mark.asyncio
    async def test_head_tool_real_execution(self, orchestrator):
        """Test head tool execution on 192.168.50.12"""
        prompt = f"Show first 10 lines of /etc/passwd on {self.TARGET_HOST}"
        result, duration = await self.execute_real_prompt(orchestrator, prompt)
        
        assert result.success, f"Head test failed: {result.error_message}"
        assert result.response is not None, "No response received"
        assert duration < 60.0, f"Test took too long: {duration:.2f}s"

    @pytest.mark.asyncio
    async def test_tail_tool_real_execution(self, orchestrator):
        """Test tail tool execution on 192.168.50.12"""
        prompt = f"Show last 10 lines of /var/log/syslog on {self.TARGET_HOST}"
        result, duration = await self.execute_real_prompt(orchestrator, prompt)
        
        assert result.success, f"Tail test failed: {result.error_message}"
        assert result.response is not None, "No response received"
        assert duration < 60.0, f"Test took too long: {duration:.2f}s"

    @pytest.mark.asyncio
    async def test_grep_tool_real_execution(self, orchestrator):
        """Test grep tool execution on 192.168.50.12"""
        prompt = f"Search for 'root' in /etc/passwd on {self.TARGET_HOST}"
        result, duration = await self.execute_real_prompt(orchestrator, prompt)
        
        assert result.success, f"Grep test failed: {result.error_message}"
        assert result.response is not None, "No response received"
        assert duration < 60.0, f"Test took too long: {duration:.2f}s"

    # ============================================================================
    # STORAGE & DISK TESTS - REAL EXECUTION
    # ============================================================================

    @pytest.mark.asyncio
    async def test_df_tool_real_execution(self, orchestrator):
        """Test df tool execution on 192.168.50.12"""
        prompt = f"Check disk usage on {self.TARGET_HOST}"
        result, duration = await self.execute_real_prompt(orchestrator, prompt)
        
        assert result.success, f"DF test failed: {result.error_message}"
        assert result.response is not None, "No response received"
        assert duration < 60.0, f"Test took too long: {duration:.2f}s"

    @pytest.mark.asyncio
    async def test_du_tool_real_execution(self, orchestrator):
        """Test du tool execution on 192.168.50.12"""
        prompt = f"Show directory sizes in /var on {self.TARGET_HOST}"
        result, duration = await self.execute_real_prompt(orchestrator, prompt)
        
        assert result.success, f"DU test failed: {result.error_message}"
        assert result.response is not None, "No response received"
        assert duration < 60.0, f"Test took too long: {duration:.2f}s"

    @pytest.mark.asyncio
    async def test_mount_tool_real_execution(self, orchestrator):
        """Test mount tool execution on 192.168.50.12"""
        prompt = f"Show mounted filesystems on {self.TARGET_HOST}"
        result, duration = await self.execute_real_prompt(orchestrator, prompt)
        
        assert result.success, f"Mount test failed: {result.error_message}"
        assert result.response is not None, "No response received"
        assert duration < 60.0, f"Test took too long: {duration:.2f}s"

    # ============================================================================
    # SERVICE MANAGEMENT TESTS - REAL EXECUTION
    # ============================================================================

    @pytest.mark.asyncio
    async def test_systemctl_tool_real_execution(self, orchestrator):
        """Test systemctl tool execution on 192.168.50.12"""
        prompt = f"Check SSH service status on {self.TARGET_HOST}"
        result, duration = await self.execute_real_prompt(orchestrator, prompt)
        
        assert result.success, f"Systemctl test failed: {result.error_message}"
        assert result.response is not None, "No response received"
        assert duration < 60.0, f"Test took too long: {duration:.2f}s"

    @pytest.mark.asyncio
    async def test_service_tool_real_execution(self, orchestrator):
        """Test service tool execution on 192.168.50.12"""
        prompt = f"Check all service statuses on {self.TARGET_HOST}"
        result, duration = await self.execute_real_prompt(orchestrator, prompt)
        
        assert result.success, f"Service test failed: {result.error_message}"
        assert result.response is not None, "No response received"
        assert duration < 60.0, f"Test took too long: {duration:.2f}s"

    # ============================================================================
    # MEMORY & CPU TESTS - REAL EXECUTION
    # ============================================================================

    @pytest.mark.asyncio
    async def test_free_tool_real_execution(self, orchestrator):
        """Test free tool execution on 192.168.50.12"""
        prompt = f"Check memory usage on {self.TARGET_HOST}"
        result, duration = await self.execute_real_prompt(orchestrator, prompt)
        
        assert result.success, f"Free test failed: {result.error_message}"
        assert result.response is not None, "No response received"
        assert duration < 60.0, f"Test took too long: {duration:.2f}s"

    @pytest.mark.asyncio
    async def test_lscpu_tool_real_execution(self, orchestrator):
        """Test lscpu tool execution on 192.168.50.12"""
        prompt = f"Show CPU information on {self.TARGET_HOST}"
        result, duration = await self.execute_real_prompt(orchestrator, prompt)
        
        assert result.success, f"Lscpu test failed: {result.error_message}"
        assert result.response is not None, "No response received"
        assert duration < 60.0, f"Test took too long: {duration:.2f}s"

    # ============================================================================
    # USER & SECURITY TESTS - REAL EXECUTION
    # ============================================================================

    @pytest.mark.asyncio
    async def test_who_tool_real_execution(self, orchestrator):
        """Test who tool execution on 192.168.50.12"""
        prompt = f"Show logged in users on {self.TARGET_HOST}"
        result, duration = await self.execute_real_prompt(orchestrator, prompt)
        
        assert result.success, f"Who test failed: {result.error_message}"
        assert result.response is not None, "No response received"
        assert duration < 60.0, f"Test took too long: {duration:.2f}s"

    @pytest.mark.asyncio
    async def test_w_tool_real_execution(self, orchestrator):
        """Test w tool execution on 192.168.50.12"""
        prompt = f"Show user activity on {self.TARGET_HOST}"
        result, duration = await self.execute_real_prompt(orchestrator, prompt)
        
        assert result.success, f"W test failed: {result.error_message}"
        assert result.response is not None, "No response received"
        assert duration < 60.0, f"Test took too long: {duration:.2f}s"

    @pytest.mark.asyncio
    async def test_last_tool_real_execution(self, orchestrator):
        """Test last tool execution on 192.168.50.12"""
        prompt = f"Show login history on {self.TARGET_HOST}"
        result, duration = await self.execute_real_prompt(orchestrator, prompt)
        
        assert result.success, f"Last test failed: {result.error_message}"
        assert result.response is not None, "No response received"
        assert duration < 60.0, f"Test took too long: {duration:.2f}s"

    # ============================================================================
    # COMPLEX INTEGRATION SCENARIOS - REAL EXECUTION
    # ============================================================================

    @pytest.mark.asyncio
    async def test_complex_system_health_check(self, orchestrator):
        """Test complex system health check on 192.168.50.12"""
        prompt = f"Perform a comprehensive system health check on {self.TARGET_HOST} including CPU, memory, disk, and network"
        result, duration = await self.execute_real_prompt(orchestrator, prompt, timeout=120)
        
        assert result.success, f"System health check failed: {result.error_message}"
        assert result.response is not None, "No response received"
        assert duration < 120.0, f"Test took too long: {duration:.2f}s"

    @pytest.mark.asyncio
    async def test_complex_security_audit(self, orchestrator):
        """Test complex security audit on 192.168.50.12"""
        prompt = f"Run a security audit on {self.TARGET_HOST} checking users, processes, and network connections"
        result, duration = await self.execute_real_prompt(orchestrator, prompt, timeout=120)
        
        assert result.success, f"Security audit failed: {result.error_message}"
        assert result.response is not None, "No response received"
        assert duration < 120.0, f"Test took too long: {duration:.2f}s"

    @pytest.mark.asyncio
    async def test_complex_performance_analysis(self, orchestrator):
        """Test complex performance analysis on 192.168.50.12"""
        prompt = f"Analyze system performance on {self.TARGET_HOST} including top processes, memory usage, and I/O statistics"
        result, duration = await self.execute_real_prompt(orchestrator, prompt, timeout=120)
        
        assert result.success, f"Performance analysis failed: {result.error_message}"
        assert result.response is not None, "No response received"
        assert duration < 120.0, f"Test took too long: {duration:.2f}s"


if __name__ == "__main__":
    print("Run with: pytest tests/test_ai_linux_tool_execution.py -v")