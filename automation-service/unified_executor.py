#!/usr/bin/env python3
"""
Unified Execution Framework
===========================

ALL tool executions follow the SAME procedural steps.
The "flavor" is determined by tool metadata, not hardcoded logic.

Universal Execution Pipeline:
1. Parse Tool Metadata
2. Resolve Parameters
3. Build Command/Request
4. Resolve Credentials
5. Establish Connection
6. Execute
7. Parse Results
8. Return Standardized Output
"""

import logging
import httpx
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum


# ============================================================================
# EXECUTION CONFIGURATION MODELS
# ============================================================================

class ExecutionType(str, Enum):
    """Type of execution"""
    COMMAND = "command"
    API = "api"
    QUERY = "query"
    SCRIPT = "script"


class ConnectionType(str, Enum):
    """Type of connection"""
    POWERSHELL = "powershell"
    SSH = "ssh"
    LOCAL = "local"
    HTTP = "http"
    HTTPS = "https"
    DATABASE = "database"
    GRPC = "grpc"
    IMPACKET = "impacket"


class CommandStrategy(str, Enum):
    """Strategy for building commands"""
    CMDLET = "cmdlet"  # PowerShell cmdlets: Get-Service -Name Spooler
    CLI = "cli"  # Standard CLI: ping -c 4 host
    SCRIPT = "script"  # Script execution: /path/to/script.sh args
    TEMPLATE = "template"  # Custom template
    API_CALL = "api_call"  # REST API call
    QUERY = "query"  # Database query


class ParameterFormat(str, Enum):
    """Format for command parameters"""
    POWERSHELL = "powershell"  # -ParameterName Value
    POSIX = "posix"  # --parameter-name value
    WINDOWS = "windows"  # /ParameterName Value
    CUSTOM = "custom"  # Custom format


@dataclass
class ExecutionConfig:
    """Execution configuration from tool metadata"""
    execution_type: ExecutionType
    connection_type: ConnectionType
    requires_credentials: bool
    requires_target_host: bool
    command_strategy: CommandStrategy
    parameter_format: ParameterFormat
    command_template: Optional[str] = None
    auto_fetch_credentials: bool = True
    required_credential_fields: List[str] = None
    optional_credential_fields: List[str] = None
    target_host_aliases: List[str] = None
    exclude_from_command: List[str] = None
    
    def __post_init__(self):
        if self.required_credential_fields is None:
            self.required_credential_fields = ["username", "password"]
        if self.optional_credential_fields is None:
            self.optional_credential_fields = []
        if self.target_host_aliases is None:
            self.target_host_aliases = ["host", "target_host", "computer_name", "server"]
        if self.exclude_from_command is None:
            self.exclude_from_command = [
                "host", "target_host", "computer_name", "server",
                "use_asset_credentials", "asset_id", "connection_type",
                "timeout", "username", "password", "domain"
            ]


# ============================================================================
# UNIFIED EXECUTOR
# ============================================================================

class UnifiedExecutor:
    """
    Unified execution engine that works for ALL tool types.
    No hardcoded tool-specific logic - everything driven by metadata.
    """
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
    
    # ========================================================================
    # STAGE 1: PARSE TOOL METADATA
    # ========================================================================
    
    def parse_execution_config(self, tool_definition: Dict[str, Any]) -> ExecutionConfig:
        """
        Parse execution configuration from tool metadata.
        
        Priority order:
        1. Check for simplified metadata from plan (requires_credentials, tool_metadata)
        2. Check for full execution metadata structure
        3. Fall back to inference from platform/category/name
        """
        # PRIORITY 1: Check for simplified metadata from plan (enriched by planner)
        # This is the NEW way - the planner enriches steps with tool metadata
        if "requires_credentials" in tool_definition or "tool_metadata" in tool_definition:
            self.logger.info("✅ Using tool metadata from plan (enriched by planner)")
            tool_metadata = tool_definition.get("tool_metadata", {})
            
            # If we have full tool_metadata, use it
            if tool_metadata:
                connection_meta = tool_metadata.get("connection", {})
                builder_meta = tool_metadata.get("command_builder", {})
                cred_meta = tool_metadata.get("credentials", {})
                param_meta = tool_metadata.get("parameters", {})
                
                return ExecutionConfig(
                    execution_type=ExecutionType(tool_metadata.get("type", "command")),
                    connection_type=ConnectionType(connection_meta.get("type", "local")),
                    requires_credentials=connection_meta.get("requires_credentials", False),
                    requires_target_host=connection_meta.get("requires_target_host", False),
                    command_strategy=CommandStrategy(builder_meta.get("strategy", "cli")),
                    parameter_format=ParameterFormat(builder_meta.get("parameter_format", "posix")),
                    command_template=builder_meta.get("template"),
                    auto_fetch_credentials=cred_meta.get("auto_fetch", True),
                    required_credential_fields=cred_meta.get("required_fields", ["username", "password"]),
                    optional_credential_fields=cred_meta.get("optional_fields", []),
                    target_host_aliases=param_meta.get("target_host_aliases", None),
                    exclude_from_command=param_meta.get("exclude_from_command", None)
                )
            else:
                # We only have requires_credentials flag - infer the rest
                self.logger.info(f"⚠️  Only requires_credentials flag available, inferring rest")
                config = self._infer_execution_config(tool_definition)
                # Override requires_credentials with the value from the plan
                config.requires_credentials = tool_definition.get("requires_credentials", False)
                return config
        
        # PRIORITY 2: Check for full execution metadata structure (OLD way)
        execution_meta = tool_definition.get("execution", {})
        if execution_meta:
            self.logger.info("Using full execution metadata structure")
            connection_meta = execution_meta.get("connection", {})
            builder_meta = execution_meta.get("command_builder", {})
            cred_meta = execution_meta.get("credentials", {})
            param_meta = execution_meta.get("parameters", {})
            
            return ExecutionConfig(
                execution_type=ExecutionType(execution_meta.get("type", "command")),
                connection_type=ConnectionType(connection_meta.get("type", "local")),
                requires_credentials=connection_meta.get("requires_credentials", False),
                requires_target_host=connection_meta.get("requires_target_host", False),
                command_strategy=CommandStrategy(builder_meta.get("strategy", "cli")),
                parameter_format=ParameterFormat(builder_meta.get("parameter_format", "posix")),
                command_template=builder_meta.get("template"),
                auto_fetch_credentials=cred_meta.get("auto_fetch", True),
                required_credential_fields=cred_meta.get("required_fields", ["username", "password"]),
                optional_credential_fields=cred_meta.get("optional_fields", []),
                target_host_aliases=param_meta.get("target_host_aliases", None),
                exclude_from_command=param_meta.get("exclude_from_command", None)
            )
        
        # PRIORITY 3: Fall back to inference (LAST RESORT)
        self.logger.info("⚠️  No metadata available, inferring from tool name/platform")
        return self._infer_execution_config(tool_definition)
    
    def _infer_execution_config(self, tool_definition: Dict[str, Any]) -> ExecutionConfig:
        """
        Infer execution configuration from tool platform/category/name.
        This provides backward compatibility for tools without execution metadata.
        """
        tool_name = tool_definition.get("tool_name", "")
        platform = tool_definition.get("platform", "").lower()
        category = tool_definition.get("category", "").lower()
        
        # Impacket tools (check first, before PowerShell)
        if tool_name in ["windows-impacket-executor", "windows-psexec", "PSExec"] or "impacket" in tool_name.lower():
            return ExecutionConfig(
                execution_type=ExecutionType.COMMAND,
                connection_type=ConnectionType.IMPACKET,
                requires_credentials=True,
                requires_target_host=True,
                command_strategy=CommandStrategy.CLI,
                parameter_format=ParameterFormat.WINDOWS
            )
        
        # Windows PowerShell Cmdlets and Windows tools
        elif (platform == "windows" or 
            "windows" in tool_name.lower() or
            tool_name.startswith(("Get-", "Set-", "Start-", "Stop-", "Restart-", 
                                 "Test-", "Measure-", "Register-", "Invoke-"))):
            return ExecutionConfig(
                execution_type=ExecutionType.COMMAND,
                connection_type=ConnectionType.POWERSHELL,
                requires_credentials=True,
                requires_target_host=True,
                command_strategy=CommandStrategy.CMDLET,
                parameter_format=ParameterFormat.POWERSHELL
            )
        
        # Linux commands
        elif platform == "linux":
            return ExecutionConfig(
                execution_type=ExecutionType.COMMAND,
                connection_type=ConnectionType.SSH,
                requires_credentials=True,
                requires_target_host=True,
                command_strategy=CommandStrategy.CLI,
                parameter_format=ParameterFormat.POSIX
            )
        
        # Database tools
        elif platform == "database" or category == "database":
            return ExecutionConfig(
                execution_type=ExecutionType.QUERY,
                connection_type=ConnectionType.DATABASE,
                requires_credentials=True,
                requires_target_host=True,
                command_strategy=CommandStrategy.QUERY,
                parameter_format=ParameterFormat.POSIX
            )
        
        # API tools
        elif category == "api" or "api" in tool_name.lower():
            return ExecutionConfig(
                execution_type=ExecutionType.API,
                connection_type=ConnectionType.HTTP,
                requires_credentials=True,
                requires_target_host=True,
                command_strategy=CommandStrategy.API_CALL,
                parameter_format=ParameterFormat.CUSTOM
            )
        
        # Network tools (usually local execution)
        elif category == "network":
            return ExecutionConfig(
                execution_type=ExecutionType.COMMAND,
                connection_type=ConnectionType.LOCAL,
                requires_credentials=False,
                requires_target_host=False,
                command_strategy=CommandStrategy.CLI,
                parameter_format=ParameterFormat.POSIX
            )
        
        # Default: local command execution
        else:
            return ExecutionConfig(
                execution_type=ExecutionType.COMMAND,
                connection_type=ConnectionType.LOCAL,
                requires_credentials=False,
                requires_target_host=False,
                command_strategy=CommandStrategy.CLI,
                parameter_format=ParameterFormat.POSIX
            )
    
    # ========================================================================
    # STAGE 2: RESOLVE PARAMETERS
    # ========================================================================
    
    def resolve_parameters(
        self, 
        parameters: Dict[str, Any], 
        config: ExecutionConfig
    ) -> Dict[str, Any]:
        """
        Resolve and normalize parameters.
        Extract target_host, separate command parameters from metadata.
        """
        resolved = parameters.copy()
        
        # Extract target host from various aliases
        target_host = None
        for alias in config.target_host_aliases:
            if alias in resolved:
                target_host = resolved[alias]
                break
        
        if target_host:
            resolved["_target_host"] = target_host
        
        return resolved
    
    # ========================================================================
    # STAGE 3: BUILD COMMAND/REQUEST
    # ========================================================================
    
    def build_command(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        config: ExecutionConfig
    ) -> str:
        """
        Build command/request based on strategy and parameter format.
        This is the universal command builder.
        """
        if config.command_strategy == CommandStrategy.CMDLET:
            return self._build_cmdlet_command(tool_name, parameters, config)
        
        elif config.command_strategy == CommandStrategy.CLI:
            return self._build_cli_command(tool_name, parameters, config)
        
        elif config.command_strategy == CommandStrategy.SCRIPT:
            return self._build_script_command(tool_name, parameters, config)
        
        elif config.command_strategy == CommandStrategy.TEMPLATE:
            return self._build_template_command(tool_name, parameters, config)
        
        elif config.command_strategy == CommandStrategy.QUERY:
            return self._build_query_command(tool_name, parameters, config)
        
        elif config.command_strategy == CommandStrategy.API_CALL:
            return self._build_api_command(tool_name, parameters, config)
        
        else:
            # Fallback: simple command with parameters
            return f"{tool_name} {' '.join(str(v) for v in parameters.values() if v)}"
    
    def _build_cmdlet_command(
        self, 
        tool_name: str, 
        parameters: Dict[str, Any], 
        config: ExecutionConfig
    ) -> str:
        """Build PowerShell cmdlet command: Get-Service -Name Spooler"""
        # Check if there's an explicit command parameter
        if "command" in parameters:
            return parameters["command"]
        
        command_parts = [tool_name]
        
        for param_name, param_value in parameters.items():
            # Skip excluded parameters
            if param_name in config.exclude_from_command or param_name.startswith("_"):
                continue
            
            # Convert to PowerShell parameter format
            ps_param_name = f"-{param_name.replace('_', '').title()}"
            
            # Handle different value types
            if isinstance(param_value, bool):
                if param_value:
                    command_parts.append(ps_param_name)
            elif isinstance(param_value, list):
                command_parts.append(f"{ps_param_name} {','.join(str(v) for v in param_value)}")
            elif isinstance(param_value, str):
                if ' ' in param_value:
                    command_parts.append(f"{ps_param_name} '{param_value}'")
                else:
                    command_parts.append(f"{ps_param_name} {param_value}")
            else:
                command_parts.append(f"{ps_param_name} {param_value}")
        
        return " ".join(command_parts)
    
    def _build_cli_command(
        self, 
        tool_name: str, 
        parameters: Dict[str, Any], 
        config: ExecutionConfig
    ) -> str:
        """Build standard CLI command: ping -c 4 host"""
        # Check if there's an explicit command parameter
        if "command" in parameters:
            return parameters["command"]
        
        command_parts = [tool_name]
        
        for param_name, param_value in parameters.items():
            if param_name in config.exclude_from_command or param_name.startswith("_"):
                continue
            
            # POSIX format: --parameter-name value or -p value
            if config.parameter_format == ParameterFormat.POSIX:
                if len(param_name) == 1:
                    flag = f"-{param_name}"
                else:
                    flag = f"--{param_name.replace('_', '-')}"
                
                if isinstance(param_value, bool):
                    if param_value:
                        command_parts.append(flag)
                else:
                    command_parts.append(f"{flag} {param_value}")
            
            # Windows format: /ParameterName Value
            elif config.parameter_format == ParameterFormat.WINDOWS:
                flag = f"/{param_name}"
                if isinstance(param_value, bool):
                    if param_value:
                        command_parts.append(flag)
                else:
                    command_parts.append(f"{flag} {param_value}")
        
        return " ".join(command_parts)
    
    def _build_script_command(
        self, 
        tool_name: str, 
        parameters: Dict[str, Any], 
        config: ExecutionConfig
    ) -> str:
        """Build script execution command"""
        script_path = parameters.get("script_path", tool_name)
        args = [str(v) for k, v in parameters.items() 
                if k not in config.exclude_from_command and k != "script_path"]
        return f"{script_path} {' '.join(args)}"
    
    def _build_template_command(
        self, 
        tool_name: str, 
        parameters: Dict[str, Any], 
        config: ExecutionConfig
    ) -> str:
        """Build command from template"""
        if not config.command_template:
            return self._build_cli_command(tool_name, parameters, config)
        
        # Simple template substitution
        template = config.command_template
        template = template.replace("{{tool_name}}", tool_name)
        
        for key, value in parameters.items():
            template = template.replace(f"{{{{{key}}}}}", str(value))
        
        return template
    
    def _build_query_command(
        self, 
        tool_name: str, 
        parameters: Dict[str, Any], 
        config: ExecutionConfig
    ) -> str:
        """Build database query"""
        return parameters.get("query", parameters.get("command", ""))
    
    def _build_api_command(
        self, 
        tool_name: str, 
        parameters: Dict[str, Any], 
        config: ExecutionConfig
    ) -> str:
        """Build API request (returns endpoint/method info as string)"""
        method = parameters.get("method", "GET")
        endpoint = parameters.get("endpoint", "/")
        return f"{method} {endpoint}"
    
    # ========================================================================
    # STAGE 4: RESOLVE CREDENTIALS
    # ========================================================================
    
    async def resolve_credentials(
        self,
        parameters: Dict[str, Any],
        config: ExecutionConfig,
        target_host: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Universal credential resolution with three fallback mechanisms:
        1. Explicit asset_id
        2. Auto-fetch by target_host
        3. Explicit username/password
        """
        if not config.requires_credentials:
            print(f"🔑 DEBUG: Credentials not required by config", flush=True)
            self.logger.info("🔑 Credentials not required by config")
            return None
        
        print(f"🔑 DEBUG: Resolving credentials: use_asset_credentials={parameters.get('use_asset_credentials')}, asset_id={parameters.get('asset_id')}, username={parameters.get('username')}", flush=True)
        self.logger.info(f"🔑 Resolving credentials: use_asset_credentials={parameters.get('use_asset_credentials')}, asset_id={parameters.get('asset_id')}, username={parameters.get('username')}")
        
        # 1. Explicit asset_id
        if parameters.get("use_asset_credentials") and parameters.get("asset_id"):
            print(f"🔑 DEBUG: Fetching credentials for asset_id={parameters['asset_id']}", flush=True)
            self.logger.info(f"🔑 Fetching credentials for asset_id={parameters['asset_id']}")
            return await self._fetch_credentials_by_asset_id(parameters["asset_id"])
        
        # 2. Auto-fetch by target_host
        if config.auto_fetch_credentials and target_host and not parameters.get("username"):
            credentials = await self._fetch_credentials_by_host(target_host)
            if credentials:
                return credentials
        
        # 3. Explicit credentials
        if parameters.get("username") or parameters.get("password"):
            credentials = {
                "username": parameters.get("username"),
                "password": parameters.get("password")
            }
            for optional_field in config.optional_credential_fields:
                if optional_field in parameters:
                    credentials[optional_field] = parameters[optional_field]
            return credentials
        
        return None
    
    async def _fetch_credentials_by_asset_id(self, asset_id: str) -> Optional[Dict[str, Any]]:
        """Fetch credentials from asset service by asset ID"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"http://asset-service:3002/{asset_id}/credentials",
                    timeout=10.0
                )
                if response.status_code == 200:
                    cred_data = response.json()
                    if cred_data.get("success"):
                        asset_creds = cred_data.get("data", {})
                        credentials = {
                            "username": asset_creds.get("username"),
                            "password": asset_creds.get("password")
                        }
                        if asset_creds.get("domain"):
                            credentials["domain"] = asset_creds.get("domain")
                        self.logger.info(f"✅ Fetched credentials for asset {asset_id}")
                        return credentials
        except Exception as e:
            self.logger.error(f"Error fetching credentials for asset {asset_id}: {e}")
        return None
    
    async def _fetch_credentials_by_host(self, target_host: str) -> Optional[Dict[str, Any]]:
        """Auto-fetch credentials by querying asset service for host IP"""
        try:
            async with httpx.AsyncClient() as client:
                # Query asset service to find asset by IP
                response = await client.post(
                    "http://asset-service:3002/execute-plan",
                    json={
                        "execution_id": "auto-cred-fetch",
                        "plan": {
                            "steps": [{
                                "tool": "asset-query",
                                "inputs": {"filters": {"ip_address": target_host}}
                            }]
                        },
                        "tenant_id": "default",
                        "actor_id": 1
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    step_results = result.get("step_results", [])
                    if step_results and step_results[0].get("status") == "completed":
                        assets = step_results[0].get("output", {}).get("assets", [])
                        if assets:
                            asset_id = assets[0].get("asset_id")
                            self.logger.info(f"🔍 Found asset {asset_id} for IP {target_host}")
                            return await self._fetch_credentials_by_asset_id(asset_id)
        except Exception as e:
            self.logger.error(f"Error auto-fetching credentials for {target_host}: {e}")
        return None
    
    # ========================================================================
    # MAIN EXECUTION METHOD
    # ========================================================================
    
    async def execute_tool(
        self,
        tool_definition: Dict[str, Any],
        parameters: Dict[str, Any],
        service_instance: Any
    ) -> Tuple[str, Optional[str], str, Optional[Dict[str, Any]]]:
        """
        Universal tool execution - works for ANY tool type.
        
        Returns:
            Tuple of (command, target_host, connection_type, credentials)
        """
        tool_name = tool_definition.get("tool_name", "unknown")
        
        # STAGE 1: Parse tool metadata
        config = self.parse_execution_config(tool_definition)
        self.logger.info(f"📋 Execution config: {config.connection_type.value} / {config.command_strategy.value}")
        
        # STAGE 2: Resolve parameters
        resolved_params = self.resolve_parameters(parameters, config)
        target_host = resolved_params.get("_target_host")
        
        # STAGE 3: Build command
        command = self.build_command(tool_name, resolved_params, config)
        self.logger.info(f"🔨 Built command: {command}")
        
        # STAGE 4: Resolve credentials
        credentials = await self.resolve_credentials(resolved_params, config, target_host)
        if credentials:
            self.logger.info(f"🔑 Resolved credentials: username={credentials.get('username')}")
        
        return (
            command,
            target_host,
            config.connection_type.value,
            credentials
        )
# --- Stage A selector integration (non-invasive) -----------------------------
async def selector_candidate_preview(intent: str, k: int = 5, trace_id: str = ""):
    """
    Thin wrapper so the executor can fetch Stage A candidates.
    Returns a list of dicts: {key,name,short_desc}
    """
    from pipeline.selector_adapter import get_selector_candidates  # local import avoids cycles
    return await get_selector_candidates(intent, k=k, trace_id=trace_id)
