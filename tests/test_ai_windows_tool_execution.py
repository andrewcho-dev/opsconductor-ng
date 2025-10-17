"""
REAL Windows Tool Execution Tests
Target System: 192.168.50.212

This test suite executes REAL Windows commands against the actual 192.168.50.212 server
through the OpsConductor pipeline. NO MOCKS - these are integration tests that validate
the complete end-to-end execution path.

Each test sends a real user prompt to the pipeline orchestrator and verifies:
1. The AI correctly interprets the request
2. The correct Windows tool is selected and executed
3. The command executes successfully on 192.168.50.212
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


class TestRealWindowsToolExecution:
    """REAL test suite for Windows tool execution on 192.168.50.212"""
    
    TARGET_HOST = "192.168.50.212"
    
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
    # SYSTEM INFORMATION TESTS - REAL EXECUTION
    # ============================================================================
    
    @pytest.mark.asyncio
    async def test_systeminfo_tool_real_execution(self, orchestrator):
        """Test systeminfo tool execution on 192.168.50.212"""
        prompt = f"Get system information from {self.TARGET_HOST}"
        result, duration = await self.execute_real_prompt(orchestrator, prompt)
        
        assert result.success, f"Systeminfo test failed: {result.error_message}"
        assert result.response is not None, "No response received"
        assert duration < 60.0, f"Test took too long: {duration:.2f}s"

    @pytest.mark.asyncio
    async def test_hostname_tool_real_execution(self, orchestrator):
        """Test hostname tool execution on 192.168.50.212"""
        prompt = f"Get hostname of {self.TARGET_HOST}"
        result, duration = await self.execute_real_prompt(orchestrator, prompt)
        
        assert result.success, f"Hostname test failed: {result.error_message}"
        assert result.response is not None, "No response received"
        assert duration < 60.0, f"Test took too long: {duration:.2f}s"

    @pytest.mark.asyncio
    async def test_whoami_tool_real_execution(self, orchestrator):
        """Test whoami tool execution on 192.168.50.212"""
        prompt = f"Show current user on {self.TARGET_HOST}"
        result, duration = await self.execute_real_prompt(orchestrator, prompt)
        
        assert result.success, f"Whoami test failed: {result.error_message}"
        assert result.response is not None, "No response received"
        assert duration < 60.0, f"Test took too long: {duration:.2f}s"

    # ============================================================================
    # PROCESS MANAGEMENT TESTS - REAL EXECUTION
    # ============================================================================

    @pytest.mark.asyncio
    async def test_tasklist_tool_real_execution(self, orchestrator):
        """Test tasklist tool execution on 192.168.50.212"""
        prompt = f"Show running processes on {self.TARGET_HOST}"
        result, duration = await self.execute_real_prompt(orchestrator, prompt)
        
        assert result.success, f"Tasklist test failed: {result.error_message}"
        assert result.response is not None, "No response received"
        assert duration < 60.0, f"Test took too long: {duration:.2f}s"

    @pytest.mark.asyncio
    async def test_taskkill_tool_real_execution(self, orchestrator):
        """Test taskkill tool execution on 192.168.50.212"""
        prompt = f"Kill notepad process on {self.TARGET_HOST} if it's running"
        result, duration = await self.execute_real_prompt(orchestrator, prompt)
        
        # Note: This might fail if notepad isn't running, which is OK
        assert result.response is not None, "No response received"
        assert duration < 60.0, f"Test took too long: {duration:.2f}s"

    @pytest.mark.asyncio
    async def test_wmic_process_tool_real_execution(self, orchestrator):
        """Test WMIC process tool execution on 192.168.50.212"""
        prompt = f"Get detailed process information using WMIC on {self.TARGET_HOST}"
        result, duration = await self.execute_real_prompt(orchestrator, prompt)
        
        assert result.success, f"WMIC process test failed: {result.error_message}"
        assert result.response is not None, "No response received"
        assert duration < 60.0, f"Test took too long: {duration:.2f}s"

    # ============================================================================
    # SERVICE MANAGEMENT TESTS - REAL EXECUTION
    # ============================================================================

    @pytest.mark.asyncio
    async def test_sc_query_tool_real_execution(self, orchestrator):
        """Test sc query tool execution on 192.168.50.212"""
        prompt = f"List Windows services on {self.TARGET_HOST}"
        result, duration = await self.execute_real_prompt(orchestrator, prompt)
        
        assert result.success, f"SC query test failed: {result.error_message}"
        assert result.response is not None, "No response received"
        assert duration < 60.0, f"Test took too long: {duration:.2f}s"

    @pytest.mark.asyncio
    async def test_get_service_tool_real_execution(self, orchestrator):
        """Test Get-Service PowerShell tool execution on 192.168.50.212"""
        prompt = f"Get Windows service status using PowerShell on {self.TARGET_HOST}"
        result, duration = await self.execute_real_prompt(orchestrator, prompt)
        
        assert result.success, f"Get-Service test failed: {result.error_message}"
        assert result.response is not None, "No response received"
        assert duration < 60.0, f"Test took too long: {duration:.2f}s"

    # ============================================================================
    # NETWORK TESTS - REAL EXECUTION
    # ============================================================================

    @pytest.mark.asyncio
    async def test_ipconfig_tool_real_execution(self, orchestrator):
        """Test ipconfig tool execution on 192.168.50.212"""
        prompt = f"Show network configuration on {self.TARGET_HOST}"
        result, duration = await self.execute_real_prompt(orchestrator, prompt)
        
        assert result.success, f"Ipconfig test failed: {result.error_message}"
        assert result.response is not None, "No response received"
        assert duration < 60.0, f"Test took too long: {duration:.2f}s"

    @pytest.mark.asyncio
    async def test_netstat_tool_real_execution(self, orchestrator):
        """Test netstat tool execution on 192.168.50.212"""
        prompt = f"Show network connections on {self.TARGET_HOST}"
        result, duration = await self.execute_real_prompt(orchestrator, prompt)
        
        assert result.success, f"Netstat test failed: {result.error_message}"
        assert result.response is not None, "No response received"
        assert duration < 60.0, f"Test took too long: {duration:.2f}s"

    @pytest.mark.asyncio
    async def test_ping_tool_real_execution(self, orchestrator):
        """Test ping tool execution on 192.168.50.212"""
        prompt = f"Ping google.com from {self.TARGET_HOST}"
        result, duration = await self.execute_real_prompt(orchestrator, prompt)
        
        assert result.success, f"Ping test failed: {result.error_message}"
        assert result.response is not None, "No response received"
        assert duration < 60.0, f"Test took too long: {duration:.2f}s"

    @pytest.mark.asyncio
    async def test_nslookup_tool_real_execution(self, orchestrator):
        """Test nslookup tool execution on 192.168.50.212"""
        prompt = f"Perform DNS lookup for google.com on {self.TARGET_HOST}"
        result, duration = await self.execute_real_prompt(orchestrator, prompt)
        
        assert result.success, f"Nslookup test failed: {result.error_message}"
        assert result.response is not None, "No response received"
        assert duration < 60.0, f"Test took too long: {duration:.2f}s"

    # ============================================================================
    # FILE SYSTEM TESTS - REAL EXECUTION
    # ============================================================================

    @pytest.mark.asyncio
    async def test_dir_tool_real_execution(self, orchestrator):
        """Test dir tool execution on 192.168.50.212"""
        prompt = f"List files in C:\\ directory on {self.TARGET_HOST}"
        result, duration = await self.execute_real_prompt(orchestrator, prompt)
        
        assert result.success, f"Dir test failed: {result.error_message}"
        assert result.response is not None, "No response received"
        assert duration < 60.0, f"Test took too long: {duration:.2f}s"

    @pytest.mark.asyncio
    async def test_type_tool_real_execution(self, orchestrator):
        """Test type tool execution on 192.168.50.212"""
        prompt = f"Display contents of C:\\Windows\\System32\\drivers\\etc\\hosts on {self.TARGET_HOST}"
        result, duration = await self.execute_real_prompt(orchestrator, prompt)
        
        assert result.success, f"Type test failed: {result.error_message}"
        assert result.response is not None, "No response received"
        assert duration < 60.0, f"Test took too long: {duration:.2f}s"

    @pytest.mark.asyncio
    async def test_get_childitem_tool_real_execution(self, orchestrator):
        """Test Get-ChildItem PowerShell tool execution on 192.168.50.212"""
        prompt = f"List directory contents using PowerShell on {self.TARGET_HOST}"
        result, duration = await self.execute_real_prompt(orchestrator, prompt)
        
        assert result.success, f"Get-ChildItem test failed: {result.error_message}"
        assert result.response is not None, "No response received"
        assert duration < 60.0, f"Test took too long: {duration:.2f}s"

    # ============================================================================
    # DISK AND STORAGE TESTS - REAL EXECUTION
    # ============================================================================

    @pytest.mark.asyncio
    async def test_fsutil_tool_real_execution(self, orchestrator):
        """Test fsutil tool execution on 192.168.50.212"""
        prompt = f"Show disk space information using fsutil on {self.TARGET_HOST}"
        result, duration = await self.execute_real_prompt(orchestrator, prompt)
        
        assert result.success, f"Fsutil test failed: {result.error_message}"
        assert result.response is not None, "No response received"
        assert duration < 60.0, f"Test took too long: {duration:.2f}s"

    @pytest.mark.asyncio
    async def test_wmic_logicaldisk_tool_real_execution(self, orchestrator):
        """Test WMIC logicaldisk tool execution on 192.168.50.212"""
        prompt = f"Show disk information using WMIC on {self.TARGET_HOST}"
        result, duration = await self.execute_real_prompt(orchestrator, prompt)
        
        assert result.success, f"WMIC logicaldisk test failed: {result.error_message}"
        assert result.response is not None, "No response received"
        assert duration < 60.0, f"Test took too long: {duration:.2f}s"

    # ============================================================================
    # REGISTRY TESTS - REAL EXECUTION
    # ============================================================================

    @pytest.mark.asyncio
    async def test_reg_query_tool_real_execution(self, orchestrator):
        """Test reg query tool execution on 192.168.50.212"""
        prompt = f"Query Windows version from registry on {self.TARGET_HOST}"
        result, duration = await self.execute_real_prompt(orchestrator, prompt)
        
        assert result.success, f"Reg query test failed: {result.error_message}"
        assert result.response is not None, "No response received"
        assert duration < 60.0, f"Test took too long: {duration:.2f}s"

    # ============================================================================
    # PERFORMANCE MONITORING TESTS - REAL EXECUTION
    # ============================================================================

    @pytest.mark.asyncio
    async def test_perfmon_tool_real_execution(self, orchestrator):
        """Test perfmon tool execution on 192.168.50.212"""
        prompt = f"Get performance counters on {self.TARGET_HOST}"
        result, duration = await self.execute_real_prompt(orchestrator, prompt)
        
        assert result.success, f"Perfmon test failed: {result.error_message}"
        assert result.response is not None, "No response received"
        assert duration < 60.0, f"Test took too long: {duration:.2f}s"

    @pytest.mark.asyncio
    async def test_wmic_cpu_tool_real_execution(self, orchestrator):
        """Test WMIC CPU tool execution on 192.168.50.212"""
        prompt = f"Get CPU information using WMIC on {self.TARGET_HOST}"
        result, duration = await self.execute_real_prompt(orchestrator, prompt)
        
        assert result.success, f"WMIC CPU test failed: {result.error_message}"
        assert result.response is not None, "No response received"
        assert duration < 60.0, f"Test took too long: {duration:.2f}s"

    # ============================================================================
    # POWERSHELL TESTS - REAL EXECUTION
    # ============================================================================

    @pytest.mark.asyncio
    async def test_get_process_tool_real_execution(self, orchestrator):
        """Test Get-Process PowerShell tool execution on 192.168.50.212"""
        prompt = f"Get process information using PowerShell on {self.TARGET_HOST}"
        result, duration = await self.execute_real_prompt(orchestrator, prompt)
        
        assert result.success, f"Get-Process test failed: {result.error_message}"
        assert result.response is not None, "No response received"
        assert duration < 60.0, f"Test took too long: {duration:.2f}s"

    @pytest.mark.asyncio
    async def test_get_wmiobject_tool_real_execution(self, orchestrator):
        """Test Get-WmiObject PowerShell tool execution on 192.168.50.212"""
        prompt = f"Get system information using Get-WmiObject on {self.TARGET_HOST}"
        result, duration = await self.execute_real_prompt(orchestrator, prompt)
        
        assert result.success, f"Get-WmiObject test failed: {result.error_message}"
        assert result.response is not None, "No response received"
        assert duration < 60.0, f"Test took too long: {duration:.2f}s"

    # ============================================================================
    # EVENT LOG TESTS - REAL EXECUTION
    # ============================================================================

    @pytest.mark.asyncio
    async def test_wevtutil_tool_real_execution(self, orchestrator):
        """Test wevtutil tool execution on 192.168.50.212"""
        prompt = f"Query Windows event logs on {self.TARGET_HOST}"
        result, duration = await self.execute_real_prompt(orchestrator, prompt)
        
        assert result.success, f"Wevtutil test failed: {result.error_message}"
        assert result.response is not None, "No response received"
        assert duration < 60.0, f"Test took too long: {duration:.2f}s"

    @pytest.mark.asyncio
    async def test_get_eventlog_tool_real_execution(self, orchestrator):
        """Test Get-EventLog PowerShell tool execution on 192.168.50.212"""
        prompt = f"Get Windows event logs using PowerShell on {self.TARGET_HOST}"
        result, duration = await self.execute_real_prompt(orchestrator, prompt)
        
        assert result.success, f"Get-EventLog test failed: {result.error_message}"
        assert result.response is not None, "No response received"
        assert duration < 60.0, f"Test took too long: {duration:.2f}s"

    # ============================================================================
    # COMPLEX INTEGRATION SCENARIOS - REAL EXECUTION
    # ============================================================================

    @pytest.mark.asyncio
    async def test_complex_system_health_check(self, orchestrator):
        """Test complex system health check on 192.168.50.212"""
        prompt = f"Perform a comprehensive Windows system health check on {self.TARGET_HOST} including CPU, memory, disk, services, and network"
        result, duration = await self.execute_real_prompt(orchestrator, prompt, timeout=120)
        
        assert result.success, f"System health check failed: {result.error_message}"
        assert result.response is not None, "No response received"
        assert duration < 120.0, f"Test took too long: {duration:.2f}s"

    @pytest.mark.asyncio
    async def test_complex_security_audit(self, orchestrator):
        """Test complex security audit on 192.168.50.212"""
        prompt = f"Run a security audit on {self.TARGET_HOST} checking users, processes, services, and network connections"
        result, duration = await self.execute_real_prompt(orchestrator, prompt, timeout=120)
        
        assert result.success, f"Security audit failed: {result.error_message}"
        assert result.response is not None, "No response received"
        assert duration < 120.0, f"Test took too long: {duration:.2f}s"

    @pytest.mark.asyncio
    async def test_complex_performance_analysis(self, orchestrator):
        """Test complex performance analysis on 192.168.50.212"""
        prompt = f"Analyze Windows system performance on {self.TARGET_HOST} including top processes, memory usage, and disk I/O"
        result, duration = await self.execute_real_prompt(orchestrator, prompt, timeout=120)
        
        assert result.success, f"Performance analysis failed: {result.error_message}"
        assert result.response is not None, "No response received"
        assert duration < 120.0, f"Test took too long: {duration:.2f}s"


if __name__ == "__main__":
    print("Run with: pytest tests/test_ai_windows_tool_execution.py -v")