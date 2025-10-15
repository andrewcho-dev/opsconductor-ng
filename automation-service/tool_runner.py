"""
Unified Tool Runner v2 - Execute tools locally or via ai-pipeline

Responsibilities:
- Route tool execution based on source (local vs pipeline)
- Execute local tools directly in automation-service
- Proxy pipeline tools to ai-pipeline service
- Apply asset intelligence (auto-resolve connection profiles and credentials)
- Return consistent response format
- Propagate trace IDs end-to-end
- Redact secrets from logs
"""

import time
import uuid
import logging
import httpx
import socket
import subprocess
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

from config import config

logger = logging.getLogger(__name__)


class ToolRunner:
    """
    Unified Tool Runner - Execute tools locally or via pipeline
    """
    
    def __init__(self, asset_facade=None, secrets_manager=None):
        """
        Initialize tool runner
        
        Args:
            asset_facade: Asset façade for connection profile resolution
            secrets_manager: Secrets manager for credential lookup
        """
        self.asset_facade = asset_facade
        self.secrets_manager = secrets_manager
        self.http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0, connect=5.0),
            follow_redirects=True
        )
        logger.info("[ToolRunner] Initialized")
    
    async def execute(
        self,
        tool_name: str,
        tool_def: Dict[str, Any],
        parameters: Dict[str, Any],
        trace_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute a tool (local or pipeline)
        
        Args:
            tool_name: Tool name
            tool_def: Tool definition from registry
            parameters: Tool parameters
            trace_id: Optional trace ID
        
        Returns:
            Execution result: {success, output, error, duration_ms, trace_id, timestamp}
        """
        start_time = time.perf_counter()
        trace_id = trace_id or str(uuid.uuid4())
        
        logger.info(f"[ToolRunner] [{trace_id}] Executing tool: {tool_name}")
        
        try:
            # Apply asset intelligence for asset-aware tools
            if tool_name in ['windows_list_directory', 'asset_count', 'asset_search']:
                parameters = await self._apply_asset_intelligence(
                    tool_name, parameters, trace_id
                )
            
            # Route based on source
            source = tool_def.get('source', 'pipeline')
            
            if source == 'local':
                result = await self._execute_local(tool_name, tool_def, parameters, trace_id)
            else:
                result = await self._execute_pipeline(tool_name, parameters, trace_id)
            
            duration_ms = (time.perf_counter() - start_time) * 1000
            
            return {
                'success': result.get('success', True),
                'tool': tool_name,
                'output': result.get('output'),
                'error': result.get('error'),
                'duration_ms': round(duration_ms, 2),
                'trace_id': trace_id,
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'exit_code': result.get('exit_code'),
                'truncated': result.get('truncated', False),
                'redacted': result.get('redacted', False)
            }
            
        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.error(f"[ToolRunner] [{trace_id}] Execution failed: {e}")
            
            return {
                'success': False,
                'tool': tool_name,
                'error': str(e),
                'duration_ms': round(duration_ms, 2),
                'trace_id': trace_id,
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }
    
    async def _apply_asset_intelligence(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        trace_id: str
    ) -> Dict[str, Any]:
        """
        Apply asset intelligence: auto-resolve connection profiles and credentials
        
        Args:
            tool_name: Tool name
            parameters: Original parameters
            trace_id: Trace ID
        
        Returns:
            Enhanced parameters with connection profile and credentials
        
        Raises:
            Exception with code='missing_credentials' if credentials not found
        """
        params = parameters.copy()
        
        # Handle asset_count and asset_search (no credentials needed)
        if tool_name in ['asset_count', 'asset_search']:
            return params
        
        # Handle windows_list_directory
        if tool_name == 'windows_list_directory' and 'host' in params:
            host = params['host']
            logger.info(f"[ToolRunner] [{trace_id}] Resolving asset profile for host: {host}")
            
            # Get connection profile
            if self.asset_facade:
                try:
                    profile = await self.asset_facade.get_connection_profile(host)
                    
                    if profile.get('found'):
                        logger.info(f"[ToolRunner] [{trace_id}] Asset profile found: {profile.get('hostname')}")
                        
                        # Merge connection parameters from profile
                        if 'winrm' in profile:
                            params.setdefault('port', profile['winrm']['port'])
                            params.setdefault('use_ssl', profile['winrm']['use_ssl'])
                            if profile['winrm'].get('domain'):
                                params.setdefault('domain', profile['winrm']['domain'])
                    else:
                        logger.info(f"[ToolRunner] [{trace_id}] Host not found in asset database")
                except Exception as e:
                    logger.warning(f"[ToolRunner] [{trace_id}] Profile lookup failed: {e}")
            
            # Try to fetch credentials server-side
            if self.secrets_manager:
                try:
                    creds = self.secrets_manager.lookup_credential(host, 'winrm', accessed_by='tool-runner')
                    if creds:
                        logger.info(f"[ToolRunner] [{trace_id}] Credentials found for host (password masked)")
                        params.setdefault('username', creds['username'])
                        params.setdefault('password', creds['password'])
                        if creds.get('domain'):
                            params.setdefault('domain', creds['domain'])
                except Exception as e:
                    logger.warning(f"[ToolRunner] [{trace_id}] Credential lookup failed: {e}")
            
            # Check if we still need credentials
            if not params.get('username') or not params.get('password'):
                logger.warning(f"[ToolRunner] [{trace_id}] Missing credentials for windows_list_directory")
                raise Exception(
                    f"missing_credentials:host={host},purpose=winrm"
                )
        
        return params
    
    async def _execute_local(
        self,
        tool_name: str,
        tool_def: Dict[str, Any],
        parameters: Dict[str, Any],
        trace_id: str
    ) -> Dict[str, Any]:
        """
        Execute tool locally in automation-service
        
        Args:
            tool_name: Tool name
            tool_def: Tool definition
            parameters: Tool parameters
            trace_id: Trace ID
        
        Returns:
            Execution result
        """
        logger.info(f"[ToolRunner] [{trace_id}] Executing locally: {tool_name}")
        
        # Handle asset_count
        if tool_name == 'asset_count':
            if not self.asset_facade:
                raise Exception("Asset façade not initialized")
            
            result = await self.asset_facade.count_assets(
                os=parameters.get('os'),
                hostname=parameters.get('hostname'),
                ip=parameters.get('ip'),
                status=parameters.get('status'),
                environment=parameters.get('environment')
            )
            
            return {
                'success': True,
                'output': str(result),
                'exit_code': 0
            }
        
        # Handle asset_search
        elif tool_name == 'asset_search':
            if not self.asset_facade:
                raise Exception("Asset façade not initialized")
            
            result = await self.asset_facade.search_assets(
                os=parameters.get('os'),
                hostname=parameters.get('hostname'),
                ip=parameters.get('ip'),
                status=parameters.get('status'),
                environment=parameters.get('environment'),
                limit=parameters.get('limit', 50)
            )
            
            return {
                'success': True,
                'output': str(result),
                'exit_code': 0
            }
        
        # Handle shell_ping
        elif tool_name == 'shell_ping':
            host = parameters.get('host')
            count = parameters.get('count', 4)
            
            try:
                result = subprocess.run(
                    ['ping', '-c', str(count), host],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                return {
                    'success': result.returncode == 0,
                    'output': result.stdout,
                    'error': result.stderr if result.returncode != 0 else None,
                    'exit_code': result.returncode
                }
            except subprocess.TimeoutExpired:
                return {
                    'success': False,
                    'error': f"Ping timed out after 30 seconds",
                    'exit_code': 1
                }
        
        # Handle dns_lookup
        elif tool_name == 'dns_lookup':
            domain = parameters.get('domain')
            
            try:
                ip_addresses = socket.gethostbyname_ex(domain)[2]
                output = f"DNS lookup for {domain}:\n" + "\n".join(ip_addresses)
                
                return {
                    'success': True,
                    'output': output,
                    'exit_code': 0
                }
            except socket.gaierror as e:
                return {
                    'success': False,
                    'error': f"DNS lookup failed: {e}",
                    'exit_code': 1
                }
        
        # Handle tcp_port_check
        elif tool_name == 'tcp_port_check':
            host = parameters.get('host')
            port = parameters.get('port')
            
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                result = sock.connect_ex((host, port))
                sock.close()
                
                if result == 0:
                    output = f"Port {port} on {host} is OPEN"
                    success = True
                else:
                    output = f"Port {port} on {host} is CLOSED"
                    success = False
                
                return {
                    'success': success,
                    'output': output,
                    'exit_code': result
                }
            except Exception as e:
                return {
                    'success': False,
                    'error': f"Port check failed: {e}",
                    'exit_code': 1
                }
        
        # Handle http_check
        elif tool_name == 'http_check':
            url = parameters.get('url')
            
            try:
                response = await self.http_client.get(url, timeout=10.0)
                output = f"HTTP check for {url}:\nStatus: {response.status_code}\nTime: {response.elapsed.total_seconds():.2f}s"
                
                return {
                    'success': response.status_code < 400,
                    'output': output,
                    'exit_code': 0 if response.status_code < 400 else 1
                }
            except Exception as e:
                return {
                    'success': False,
                    'error': f"HTTP check failed: {e}",
                    'exit_code': 1
                }
        
        # Handle traceroute
        elif tool_name == 'traceroute':
            host = parameters.get('host')
            
            try:
                result = subprocess.run(
                    ['traceroute', '-m', '15', host],
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                return {
                    'success': result.returncode == 0,
                    'output': result.stdout,
                    'error': result.stderr if result.returncode != 0 else None,
                    'exit_code': result.returncode
                }
            except subprocess.TimeoutExpired:
                return {
                    'success': False,
                    'error': f"Traceroute timed out after 60 seconds",
                    'exit_code': 1
                }
        
        # Generic command_template executor for tools with command_template
        elif 'command_template' in tool_def:
            logger.info(f"[ToolRunner] [{trace_id}] Executing command_template for {tool_name}")
            
            # Apply default values from tool definition
            final_params = parameters.copy()
            for param_def in tool_def.get('parameters', []):
                param_name = param_def.get('name')
                if param_name and param_name not in final_params:
                    if 'default' in param_def:
                        final_params[param_name] = param_def['default']
                        logger.debug(f"[ToolRunner] [{trace_id}] Applied default for {param_name}: {param_def['default']}")
            
            # Render command template with parameters
            command = tool_def['command_template']
            for key, value in final_params.items():
                # Handle different types
                if isinstance(value, bool):
                    value_str = 'True' if value else 'False'
                elif value is None:
                    value_str = ''
                else:
                    value_str = str(value)
                    # Escape backslashes for Python strings (e.g., Windows paths)
                    value_str = value_str.replace('\\', '\\\\')
                command = command.replace(f'{{{key}}}', value_str)
            
            # Get timeout from tool def or use default
            timeout = tool_def.get('timeout_seconds', 30)
            
            try:
                result = subprocess.run(
                    ['bash', '-c', command],
                    capture_output=True,
                    text=True,
                    timeout=timeout
                )
                
                return {
                    'success': result.returncode == 0,
                    'output': result.stdout,
                    'error': result.stderr if result.returncode != 0 else None,
                    'exit_code': result.returncode
                }
            except subprocess.TimeoutExpired:
                return {
                    'success': False,
                    'error': f"Command timed out after {timeout} seconds",
                    'exit_code': 1
                }
            except Exception as e:
                return {
                    'success': False,
                    'error': f"Execution error: {str(e)}",
                    'exit_code': 1
                }
        
        else:
            raise Exception(f"Local execution not implemented for tool: {tool_name}")
    
    async def _execute_pipeline(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        trace_id: str
    ) -> Dict[str, Any]:
        """
        Execute tool via ai-pipeline
        
        Args:
            tool_name: Tool name
            parameters: Tool parameters
            trace_id: Trace ID
        
        Returns:
            Execution result from ai-pipeline
        """
        logger.info(f"[ToolRunner] [{trace_id}] Proxying to ai-pipeline: {tool_name}")
        
        # Redact secrets from logs
        safe_params = self._redact_secrets(parameters)
        logger.debug(f"[ToolRunner] [{trace_id}] Parameters: {safe_params}")
        
        try:
            url = f"{config.AI_PIPELINE_BASE_URL}/execute"
            
            response = await self.http_client.post(
                url,
                json={
                    'tool': tool_name,
                    'parameters': parameters,
                    'trace_id': trace_id
                },
                headers={'X-Trace-Id': trace_id}
            )
            
            if response.status_code >= 400:
                logger.error(
                    f"[ToolRunner] [{trace_id}] AI Pipeline error: "
                    f"status={response.status_code}"
                )
                return {
                    'success': False,
                    'error': f"AI Pipeline returned {response.status_code}: {response.text}"
                }
            
            result = response.json()
            return result
            
        except httpx.TimeoutException as e:
            logger.error(f"[ToolRunner] [{trace_id}] Timeout: {e}")
            return {
                'success': False,
                'error': "Request timed out"
            }
        except Exception as e:
            logger.error(f"[ToolRunner] [{trace_id}] Error: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _redact_secrets(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Redact secret parameters from logs"""
        safe_params = parameters.copy()
        secret_keys = ['password', 'secret', 'token', 'api_key', 'credential']
        
        for key in safe_params:
            if any(secret_key in key.lower() for secret_key in secret_keys):
                safe_params[key] = '***REDACTED***'
        
        return safe_params
    
    async def close(self):
        """Close HTTP client"""
        await self.http_client.aclose()