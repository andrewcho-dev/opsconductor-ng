"""
Stage C Planner - Main Orchestrator

The main planner that coordinates all planning components to create
comprehensive, safe, executable step-by-step plans.
"""

import os
import time
import threading
import logging
import httpx
import re
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

from ...schemas.decision_v1 import DecisionV1
from ...schemas.selection_v1 import SelectionV1
from ...schemas.plan_v1 import PlanV1, ExecutionPlan, ExecutionMetadata
from ...cache.cache_manager import CacheManager

from .step_generator import StepGenerator
from .dependency_resolver import DependencyResolver, DependencyError
from .safety_planner import SafetyPlanner
from .resource_planner import ResourcePlanner

logger = logging.getLogger(__name__)


class PlanningError(Exception):
    """Raised when planning fails"""
    pass


class StageCPlanner:
    """
    Main Stage C Planner orchestrator.
    
    This class coordinates all planning components to create comprehensive
    execution plans with proper sequencing, safety measures, and resource allocation.
    
    Responsibilities:
    - Orchestrate step generation, dependency resolution, and safety planning
    - Create complete Plan v1 output with all required components
    - Handle planning errors and provide fallback strategies
    - Integrate with LLM for intelligent planning when available
    - Validate and optimize execution plans
    """
    
    def __init__(self, llm_client=None):
        """
        Initialize the Stage C Planner.
        
        Args:
            llm_client: Optional LLM client for intelligent planning
        """
        self.llm_client = llm_client
        
        # Initialize planning components
        self.step_generator = StepGenerator()
        self.dependency_resolver = DependencyResolver()
        self.safety_planner = SafetyPlanner()
        self.resource_planner = ResourcePlanner()
        
        # Initialize cache manager
        cache_enabled = os.getenv("CACHE_ENABLED", "true").lower() == "true"
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self.cache_manager = CacheManager(redis_url=redis_url, enabled=cache_enabled)
        self.cache_ttl = int(os.getenv("CACHE_TTL_STAGE_C", "3600"))  # 1 hour default
        
        # Initialize tool catalog service for fetching tool details
        from ...services.tool_catalog_service import ToolCatalogService
        self.tool_catalog = ToolCatalogService()
        
        # Initialize asset service URL for credential lookup
        self.asset_service_url = os.getenv("ASSET_SERVICE_URL", "http://localhost:8003")
        
        # Planning statistics (thread-safe)
        self._stats_lock = threading.Lock()
        self.stats = {
            "plans_created": 0,
            "total_processing_time_ms": 0,
            "average_processing_time_ms": 0,
            "errors_encountered": 0,
            "llm_calls_made": 0,
            "fallback_plans_used": 0
        }
    
    async def create_plan(
        self, 
        decision: DecisionV1, 
        selection: SelectionV1,
        sop_snippets: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> PlanV1:
        """
        Create a comprehensive execution plan.
        
        Args:
            decision: Decision from Stage A
            selection: Selection from Stage B
            sop_snippets: Optional SOP procedure snippets
            context: Optional context including conversation history
            
        Returns:
            Complete Plan v1 with execution steps, safety measures, and metadata
            
        Raises:
            PlanningError: If planning fails and no fallback is possible
        """
        start_time = time.time()
        
        try:
            # Check cache first
            cache_key = self.cache_manager.generate_stage_c_key(
                action=decision.intent.action,
                entities=[e.dict() if hasattr(e, 'dict') else e for e in decision.entities],
                tools=[tool.tool_name for tool in selection.selected_tools]
            )
            logger.info(f"🔍 CACHE: Stage C checking cache with key: {cache_key}")
            cached_plan = self.cache_manager.get(cache_key)
            logger.info(f"🔍 CACHE: Stage C result: {cached_plan is not None}")
            
            if cached_plan:
                # Cache HIT! Return cached plan with updated metadata
                cache_time = time.time() - start_time
                logger.info(f"✅ Stage C cache HIT for action: {decision.intent.action} ({cache_time*1000:.1f}ms)")
                
                # Update plan with new timestamp and processing time
                cached_plan["timestamp"] = datetime.now().isoformat()
                cached_plan["processing_time_ms"] = int(cache_time * 1000)
                
                # Add cache hit indicator to metadata
                if "execution_metadata" in cached_plan and cached_plan["execution_metadata"]:
                    if "risk_factors" not in cached_plan["execution_metadata"]:
                        cached_plan["execution_metadata"]["risk_factors"] = []
                    if "cache_hit" not in cached_plan["execution_metadata"]["risk_factors"]:
                        cached_plan["execution_metadata"]["risk_factors"].append("cache_hit")
                
                return PlanV1(**cached_plan)
            
            # Cache MISS - proceed with planning
            logger.info(f"❌ Stage C cache MISS for action: {decision.intent.action}")
            
            # Generate execution steps
            logger.info("📝 Generating execution steps...")
            steps = await self._generate_execution_steps(decision, selection, context)
            
            # Check if we have any steps to work with
            if not steps:
                raise PlanningError("No execution steps could be generated from the provided selection")
            
            logger.info(f"✅ Generated {len(steps)} execution steps")
            for i, step in enumerate(steps, 1):
                step_dict = step if isinstance(step, dict) else step.dict() if hasattr(step, 'dict') else {}
                tool_name = step_dict.get('tool', step_dict.get('type', 'unknown'))
                description = step_dict.get('description', 'No description')
                logger.info(f"   {i}. {tool_name}: {description[:80]}")
            
            # Resolve dependencies and optimize sequencing
            logger.info("🔗 Resolving dependencies and optimizing sequence...")
            ordered_steps = self._resolve_dependencies(steps)
            logger.info(f"✅ Steps ordered for execution")
            
            # Create safety measures
            safety_checks = self._create_safety_measures(
                ordered_steps, decision, selection
            )
            
            # Plan resources and observability
            observability, metadata = self._plan_resources(
                ordered_steps, decision, selection
            )
            
            # Create execution plan
            execution_plan = ExecutionPlan(
                steps=ordered_steps,
                safety_checks=safety_checks,
                rollback_plan=[],  # Rollback functionality removed
                observability=observability
            )
            
            # Create final plan
            processing_time_ms = max(1, int((time.time() - start_time) * 1000))
            
            plan = PlanV1(
                plan=execution_plan,
                execution_metadata=metadata,
                timestamp=datetime.now().isoformat(),
                processing_time_ms=processing_time_ms
            )
            
            # Cache the plan for future requests
            plan_dict = plan.dict()
            self.cache_manager.set(cache_key, plan_dict, ttl=self.cache_ttl)
            logger.info(f"✅ Stage C cached plan with key: {cache_key} (TTL: {self.cache_ttl}s)")
            
            # Update statistics
            self._update_stats(processing_time_ms, success=True)
            
            return plan
            
        except Exception as e:
            # Update error statistics
            self._update_stats(max(1, int((time.time() - start_time) * 1000)), success=False)
            
            # FAIL FAST: No fallbacks! OpsConductor requires AI-BRAIN to function
            raise PlanningError(
                f"Stage C planning failed - OpsConductor requires AI-BRAIN (LLM) to function: {str(e)}"
            )
    
    async def _generate_execution_steps(
        self, 
        decision: DecisionV1, 
        selection: SelectionV1,
        context: Optional[Dict[str, Any]] = None
    ) -> List:
        """Generate execution steps from decision and selection"""
        try:
            # ALWAYS use LLM for intelligent step generation if available
            if self.llm_client:
                logger.info("🧠 Stage C using LLM for intelligent planning (NO RULES!)")
                return await self._generate_steps_with_llm(decision, selection, context)
            else:
                # No LLM available - fail fast
                logger.error("❌ Stage C: No LLM client available - FAILING FAST")
                raise PlanningError("LLM is required for Stage C planning - OpsConductor cannot function without AI-BRAIN")
        
        except Exception as e:
            # FAIL FAST: OpsConductor requires AI-BRAIN to function
            logger.error(f"❌ Stage C: LLM planning failed - {str(e)}")
            raise PlanningError(f"AI-BRAIN (LLM) unavailable for Stage C - OpsConductor cannot function without LLM: {str(e)}")
    
    def _resolve_dependencies(self, steps) -> List:
        """Resolve step dependencies and create proper execution order"""
        try:
            # Validate dependencies first
            is_valid, errors = self.dependency_resolver.validate_dependencies(steps)
            if not is_valid:
                raise DependencyError(f"Dependency validation failed: {'; '.join(errors)}")
            
            # Resolve dependencies and order steps
            ordered_steps = self.dependency_resolver.resolve_dependencies(steps)
            
            return ordered_steps
            
        except DependencyError as e:
            # Try to fix common dependency issues
            fixed_steps = self._fix_dependency_issues(steps)
            return self.dependency_resolver.resolve_dependencies(fixed_steps)
    
    def _create_safety_measures(
        self, 
        steps, 
        decision: DecisionV1, 
        selection: SelectionV1
    ) -> List:
        """Create comprehensive safety checks"""
        return self.safety_planner.create_safety_plan(steps, decision, selection)
    
    def _plan_resources(
        self, 
        steps, 
        decision: DecisionV1, 
        selection: SelectionV1
    ) -> Tuple:
        """Plan resources, observability, and execution metadata"""
        return self.resource_planner.create_resource_plan(steps, decision, selection)
    
    async def _generate_steps_with_llm(
        self, 
        decision: DecisionV1, 
        selection: SelectionV1,
        context: Optional[Dict[str, Any]] = None
    ) -> List:
        """Generate steps using LLM for intelligent planning"""
        from ...schemas.plan_v1 import ExecutionStep
        from llm.client import LLMRequest
        import json
        
        self._increment_stat("llm_calls_made")
        
        # Look up credentials for any IP addresses in the request
        credentials_map = await self._lookup_credentials_from_context(decision, context)
        
        # Add credentials to context for prompt building
        if context is None:
            context = {}
        context["credentials_map"] = credentials_map
        
        # Build the system prompt with schema knowledge
        system_prompt = self._build_planning_system_prompt()
        
        # Build the user prompt with decision and selection context
        user_prompt = self._build_planning_user_prompt(decision, selection, context)
        
        # Create LLM request
        llm_request = LLMRequest(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.1,  # Low temperature for consistent planning
            max_tokens=2000
        )
        
        # Get response from LLM
        response = await self.llm_client.generate(llm_request)
        
        # Parse the response into execution steps
        steps = self._parse_llm_planning_response(response.content, selection)
        
        return steps
    
    def _fix_dependency_issues(self, steps) -> List:
        """Attempt to fix common dependency issues"""
        fixed_steps = []
        
        for step in steps:
            # Create a copy of the step
            fixed_step = step.model_copy()
            
            # Remove self-dependencies
            fixed_step.depends_on = [
                dep for dep in fixed_step.depends_on 
                if dep != step.id
            ]
            
            # Remove invalid wildcard dependencies that don't match any steps
            valid_deps = []
            for dep in fixed_step.depends_on:
                if '*' in dep:
                    # Check if wildcard matches any step
                    matches = self.dependency_resolver._resolve_wildcard_dependency(dep, steps)
                    if matches:
                        valid_deps.append(dep)
                else:
                    # Keep direct dependencies (will be validated later)
                    valid_deps.append(dep)
            
            fixed_step.depends_on = valid_deps
            fixed_steps.append(fixed_step)
        
        return fixed_steps
    
    def _extract_ip_addresses(self, text: str) -> List[str]:
        """
        Extract IP addresses from text using regex.
        
        Args:
            text: Text to search for IP addresses
            
        Returns:
            List of IP addresses found
        """
        # IPv4 pattern
        ipv4_pattern = r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b'
        return re.findall(ipv4_pattern, text)
    
    async def _lookup_credentials_for_host(self, ip_address: str) -> Optional[Dict[str, Any]]:
        """
        Query the asset service to find credentials for a given IP address.
        
        Args:
            ip_address: IP address to look up
            
        Returns:
            Dictionary with credential information if found, None otherwise
        """
        try:
            logger.info(f"🔍 Looking up credentials for host: {ip_address}")
            
            async with httpx.AsyncClient(timeout=5.0) as client:
                # Query asset service with search parameter (searches name, hostname, description)
                # We'll use the IP as search term
                response = await client.get(
                    f"{self.asset_service_url}/",
                    params={"search": ip_address, "limit": 10}
                )
                
                if response.status_code != 200:
                    logger.warning(f"Asset service returned status {response.status_code}")
                    return None
                
                data = response.json()
                # Asset service returns: {"success": true, "data": {"assets": [...], "total": ...}}
                assets = data.get("data", {}).get("assets", [])
                
                # Find exact match by IP address
                matching_asset = None
                for asset in assets:
                    if asset.get("ip_address") == ip_address:
                        matching_asset = asset
                        break
                
                if not matching_asset:
                    logger.info(f"No asset found for IP: {ip_address}")
                    return None
                
                # Check if asset has credentials
                if not matching_asset.get("has_credentials"):
                    logger.info(f"Asset found for {ip_address} but has no credentials")
                    return None
                
                # Get full asset credentials (including decrypted password)
                asset_id = matching_asset.get("id")
                creds_response = await client.get(f"{self.asset_service_url}/{asset_id}/credentials")
                
                if creds_response.status_code != 200:
                    logger.warning(f"Failed to get asset credentials for ID {asset_id}")
                    return None
                
                creds_data = creds_response.json()
                credentials = creds_data.get("data", {})
                
                # Note: We don't log the actual password for security
                logger.info(f"✅ Found credentials for {ip_address}: username={credentials.get('username')}, os_type={credentials.get('os_type')}")
                
                return credentials
                
        except httpx.TimeoutException:
            logger.warning(f"Timeout querying asset service for {ip_address}")
            return None
        except Exception as e:
            logger.error(f"Error looking up credentials for {ip_address}: {str(e)}")
            return None
    
    async def _lookup_credentials_from_context(
        self, 
        decision: DecisionV1, 
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Look up credentials for all IP addresses mentioned in the user query and entities.
        
        Args:
            decision: Decision from Stage A
            context: Optional context including conversation history
            
        Returns:
            Dictionary mapping IP addresses to their credentials
        """
        credentials_map = {}
        
        # Extract IP addresses from user query
        ip_addresses = self._extract_ip_addresses(decision.original_request)
        
        # Extract IP addresses from entities
        for entity in decision.entities:
            entity_dict = entity.dict() if hasattr(entity, 'dict') else entity
            entity_value = entity_dict.get('value', '')
            if entity_value:
                ip_addresses.extend(self._extract_ip_addresses(str(entity_value)))
        
        # Extract IP addresses from conversation history
        if context and "conversation_history" in context:
            conversation_history = context["conversation_history"]
            if conversation_history:
                ip_addresses.extend(self._extract_ip_addresses(conversation_history))
        
        # Remove duplicates
        ip_addresses = list(set(ip_addresses))
        
        if not ip_addresses:
            logger.info("No IP addresses found in request")
            return credentials_map
        
        logger.info(f"Found {len(ip_addresses)} IP address(es) in request: {ip_addresses}")
        
        # Look up credentials for each IP
        for ip in ip_addresses:
            creds = await self._lookup_credentials_for_host(ip)
            if creds:
                credentials_map[ip] = creds
        
        return credentials_map

    def _update_stats(self, processing_time_ms: int, success: bool) -> None:
        """Update planning statistics (thread-safe)"""
        with self._stats_lock:
            self.stats["plans_created"] += 1
            self.stats["total_processing_time_ms"] += processing_time_ms
            self.stats["average_processing_time_ms"] = (
                self.stats["total_processing_time_ms"] // self.stats["plans_created"]
            )
            
            if not success:
                self.stats["errors_encountered"] += 1
    
    def _increment_stat(self, stat_name: str, amount: int = 1) -> None:
        """Thread-safe increment of a specific statistic"""
        with self._stats_lock:
            self.stats[stat_name] += amount
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of the planner (thread-safe)"""
        with self._stats_lock:
            stats_copy = self.stats.copy()
        
        return {
            "stage_c_planner": "healthy",
            "component": "stage_c_planner",
            "statistics": stats_copy,
            "components": {
                "step_generator": "operational",
                "dependency_resolver": "operational", 
                "safety_planner": "operational",
                "resource_planner": "operational"
            },
            "llm_integration": "available" if self.llm_client else "disabled"
        }
    
    def validate_plan(self, plan: PlanV1) -> Tuple[bool, List[str]]:
        """
        Validate a generated plan for completeness and safety.
        
        Args:
            plan: Plan to validate
            
        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []
        
        # Validate plan structure
        if not plan.plan.steps:
            issues.append("Plan contains no execution steps")
        
        # Validate step dependencies
        step_ids = {step.id for step in plan.plan.steps}
        for step in plan.plan.steps:
            for dep in step.depends_on:
                if '*' not in dep and dep not in step_ids:
                    issues.append(f"Step {step.id} depends on non-existent step {dep}")
        
        # Validate safety checks
        if not plan.plan.safety_checks:
            issues.append("Plan contains no safety checks")
        
        # Validate rollback procedures for destructive operations
        rollback_step_ids = {rb.step_id for rb in plan.plan.rollback_plan}
        for step in plan.plan.steps:
            if self._is_destructive_operation(step):
                if step.id not in rollback_step_ids:
                    issues.append(f"Destructive step {step.id} has no rollback procedure")
        
        # Validate execution metadata
        if plan.execution_metadata.total_estimated_time <= 0:
            issues.append("Invalid total estimated time")
        
        return len(issues) == 0, issues
    
    def _is_destructive_operation(self, step) -> bool:
        """
        Determine if a step represents a destructive operation that needs rollback.
        
        Args:
            step: ExecutionStep to check
            
        Returns:
            True if the operation is destructive and needs rollback
        """
        tool = step.tool
        
        # Check systemctl operations
        if tool == "systemctl":
            action = step.inputs.get("action", "status")
            # Only start, stop, restart, enable, disable are destructive
            destructive_actions = {"start", "stop", "restart", "enable", "disable", "reload"}
            return action in destructive_actions
        
        # File operations are generally destructive
        if tool in {"file_manager", "config_manager"}:
            return True
        
        # Docker operations can be destructive
        if tool == "docker":
            action = step.inputs.get("action", "list")
            # Only certain docker actions are destructive
            destructive_actions = {"start", "stop", "restart", "remove", "create", "build"}
            return action in destructive_actions
        
        # Network tools can be destructive if they modify configuration
        if tool == "network_tools":
            action = step.inputs.get("action", "status")
            destructive_actions = {"configure", "restart", "modify"}
            return action in destructive_actions
        
        # Read-only tools are not destructive
        readonly_tools = {"ps", "journalctl", "info_display"}
        return tool not in readonly_tools
    
    def optimize_plan(self, plan: PlanV1) -> PlanV1:
        """
        Optimize an execution plan for better performance and safety.
        
        Args:
            plan: Plan to optimize
            
        Returns:
            Optimized plan
        """
        # Create optimized copy
        optimized_plan = plan.model_copy()
        
        # Optimize step ordering for parallel execution
        parallel_groups = self.dependency_resolver.identify_parallel_groups(plan.plan.steps)
        
        # Update execution order based on parallel groups
        execution_order = 1
        for group in parallel_groups:
            for step in group:
                # Find the step in optimized plan and update its order
                for opt_step in optimized_plan.plan.steps:
                    if opt_step.id == step.id:
                        opt_step.execution_order = execution_order
                        break
            execution_order += 1
        
        # Add optimization metadata
        optimized_plan.execution_metadata.risk_factors.append("plan_optimized")
        
        return optimized_plan
    
    def _build_planning_system_prompt(self) -> str:
        """Build the system prompt for LLM-based planning with schema knowledge"""
        return """You are Stage C Planner - the intelligent planning component of OpsConductor.

Your role is to create detailed execution plans based on the user's intent and selected tools.

# ASSET DATABASE SCHEMA
When planning asset queries, you have access to the following fields in the assets database:

**Basic Information:**
- name: Asset name
- hostname: Hostname
- ip_address: IP address
- description: Description
- tags: List of tags

**Device/Hardware:**
- device_type: Type of device (server, router, switch, firewall, load_balancer, storage, other)
- hardware_make: Hardware manufacturer
- hardware_model: Hardware model
- serial_number: Serial number

**Operating System:**
- os_type: OS type (linux, windows, macos, unix, other)
- os_version: OS version

**Location:**
- physical_address: Physical address
- data_center: Data center name
- building: Building name
- room: Room number
- rack_position: Rack position
- rack_location: Rack location
- gps_coordinates: GPS coordinates

**Status and Management:**
- status: Status (active, inactive, maintenance, decommissioned)
- environment: Environment (production, staging, development, testing)
- criticality: Criticality level (low, medium, high, critical)
- owner: Owner name
- support_contact: Support contact
- contract_number: Contract number

**Services:**
- service_type: Primary service type (ssh, rdp, http, https, database, ftp, etc.)
- port: Primary service port
- is_secure: Whether primary service is secure
- database_type: Database type (if applicable: mysql, postgresql, mongodb, oracle, mssql, redis)
- database_name: Database name (if applicable)
- secondary_service_type: Secondary service type
- secondary_port: Secondary service port

# YOUR TASK
For each selected tool, create an execution step with:
1. **Intelligent field selection**: Choose ONLY the fields needed to answer the user's query
   - For "list all" queries: Select key identifying fields (name, hostname, ip_address, os_version, device_type, environment, service_type, database_type, criticality)
   - For specific queries: Select only relevant fields
   - NEVER request all fields unless explicitly needed

2. **Proper parameters**: Extract query parameters from the user's intent
   - For asset queries:
     * query_type: "list_all", "filter", "search", "get_by_id"
     * filters: Dictionary of field filters (e.g., {"environment": "production", "device_type": "server"})
     * fields: List of field names to retrieve (CRITICAL - be selective!)
   
   - For Windows/PowerShell/WinRM commands (Invoke-Command, Get-ChildItem, Get-Process, etc.):
     * target_host: IP address or hostname of the Windows machine
     * username: Windows username for authentication
     * password: Windows password for authentication
     * command or script: The PowerShell command/script to execute
     * use_ssl: true/false (default: false for HTTP WinRM on port 5985)
     * port: WinRM port (default: 5985 for HTTP, 5986 for HTTPS)
     * connection_type: "powershell" (to explicitly mark as PowerShell/WinRM execution)
     
     **CRITICAL: ALWAYS include the target hostname/IP as the FIRST column in PowerShell Select-Object output!**
     Example: Select-Object @{Name='Host';Expression={'192.168.50.212'}}, DriveLetter, SizeGB, FreeGB
     This ensures users can identify which host the output came from, especially in multi-host queries.
   
   - For Linux/SSH commands (ls, cat, ps, systemctl, etc.):
     * target_host: IP address or hostname of the Linux machine
     * username: SSH username for authentication
     * password: SSH password for authentication (or private_key)
     * command or script: The bash command/script to execute
     * port: SSH port (default: 22)
     * connection_type: "ssh" (to explicitly mark as SSH execution)
   
   - For Windows commands using Impacket WMI:
     
     PARAMETERS: target_host, username, password, connection_type: "impacket", domain (optional), wait (see below)
     
     WAIT PARAMETER RULES:
     * wait: false → GUI apps only (notepad.exe, calc.exe, mspaint.exe, explorer.exe)
     * wait: true → ALL command-line commands that return output
     
     COMMON COMMANDS BY CATEGORY:
     
     1. PROCESSES (wait: true):
        - List: "tasklist", "tasklist /FI \"IMAGENAME eq notepad.exe\"", "tasklist /V"
        - Kill: "taskkill /F /IM process.exe", "taskkill /F /PID 1234", "taskkill /F /T /IM process.exe"
     
     2. FILES (wait: true):
        - List: "dir C:\\path", "dir /S C:\\path", "tree C:\\path"
        - Manipulate: "copy src dst", "move src dst", "del file", "ren old new", "type file"
        - Directories: "mkdir dir", "rmdir dir", "rmdir /S /Q dir"
        - Advanced: "xcopy src dst /E /I", "robocopy src dst /E", "attrib +R file"
     
     3. NETWORK (wait: true):
        - Diagnostics: "ping host", "tracert host", "nslookup host", "pathping host"
        - Config: "ipconfig", "ipconfig /all", "ipconfig /flushdns", "netstat -ano", "arp -a", "route print", "hostname", "getmac"
        - Shares: "net share", "net use Z: \\\\server\\share"
     
     4. SERVICES (wait: true):
        - "sc query", "sc query ServiceName", "sc start/stop ServiceName"
        - "sc config ServiceName start= auto/disabled"
        - "net start/stop ServiceName"
     
     5. USERS (wait: true):
        - "net user", "net user username", "net user username password /ADD"
        - "net user username /DELETE", "net user username /ACTIVE:YES/NO"
        - "net localgroup Administrators", "whoami", "whoami /groups"
     
     6. SYSTEM INFO (wait: true):
        - "systeminfo", "hostname", "ver"
        - "wmic os get caption,version", "wmic cpu get name,numberofcores"
        - "wmic memorychip get capacity", "wmic diskdrive get model,size"
        - "wmic product get name,version", "wmic process list brief"
     
     7. REGISTRY (wait: true):
        - "reg query HKLM\\path", "reg add HKLM\\path /v name /t REG_SZ /d value"
        - "reg delete HKLM\\path /v name /f", "reg export/import file"
     
     8. SCHEDULED TASKS (wait: true):
        - "schtasks /Query", "schtasks /Create /TN name /TR cmd /SC DAILY"
        - "schtasks /Run /TN name", "schtasks /Delete /TN name /F"
     
     9. EVENT LOGS (wait: true):
        - "wevtutil qe System /c:10 /f:text", "wevtutil cl System"
     
     10. SYSTEM MAINTENANCE (wait: true):
         - "shutdown /s /r /a /l /t 0", "gpupdate /force", "sfc /scannow", "chkdsk C:"
     
     11. PERFORMANCE (wait: true):
         - "wmic cpu get loadpercentage"
         - "wmic path Win32_PerfFormattedData_PerfOS_Memory get AvailableMBytes"
     
     USER LANGUAGE TRANSLATION (CRITICAL):
     - "shutdown/stop/close/kill notepad" → "taskkill /F /IM notepad.exe"
     - "list processes" → "tasklist"
     - "get IP" → "ipconfig"
     - "check service" → "sc query ServiceName"
     - "list files" → "dir C:\\path"
     
     NOTES: Use double backslashes in paths. Admin commands need admin credentials
   
   - For API/HTTP requests (REST APIs, web services, device APIs like Axis cameras, etc.):
     * url: Full URL of the API endpoint OR
     * host: IP address or hostname (if building URL from parts)
     * path: API path (e.g., /axis-cgi/com/ptz.cgi)
     * protocol: http or https (default: http)
     * port: Port number (optional)
     * method: HTTP method (GET, POST, PUT, DELETE, etc.)
     * username: Username for authentication
     * password: Password for authentication
     * auth_type: "basic" or "digest" (default: basic, use "digest" for Axis cameras)
     * params: Query parameters as a dictionary
     * headers: HTTP headers as a dictionary (optional)
     * body: Request body for POST/PUT (optional)
     * connection_type: "api" (to explicitly mark as API execution)

3. **Clear descriptions**: Describe what each step will do

4. **Dependencies**: Identify if steps depend on each other

Return your response as a JSON array of execution steps with this structure:

For asset queries:
[
  {
    "tool": "asset-query",
    "description": "Brief description of what this step does",
    "inputs": {
      "query_type": "list_all" | "filter" | "search" | "get_by_id",
      "filters": {},
      "fields": ["field1", "field2", ...],
      "search_term": "optional search term",
      "asset_id": "optional asset ID"
    },
    "preconditions": ["list of preconditions"],
    "success_criteria": ["list of success criteria"],
    "failure_handling": "what to do if this step fails",
    "estimated_duration": 10
  }
]

For Windows/PowerShell/WinRM commands:
[
  {
    "tool": "Invoke-Command" | "Get-ChildItem" | "Get-Process" | etc.,
    "description": "Brief description of what this step does",
    "inputs": {
      "target_host": "192.168.1.100",
      "username": "administrator",
      "password": "password123",
      "command": "Get-ChildItem C:\\",
      "connection_type": "powershell",
      "use_ssl": false,
      "port": 5985
    },
    "preconditions": ["WinRM service is running", "Credentials are valid"],
    "success_criteria": ["Command executed successfully", "Output received"],
    "failure_handling": "Log error and report connection failure",
    "estimated_duration": 15
  }
]

For Linux/SSH commands:
[
  {
    "tool": "ls" | "cat" | "ps" | "systemctl" | etc.,
    "description": "Brief description of what this step does",
    "inputs": {
      "target_host": "192.168.50.12",
      "username": "root",
      "password": "password123",
      "command": "ls -la /root",
      "connection_type": "ssh",
      "port": 22
    },
    "preconditions": ["SSH service is running", "Credentials are valid"],
    "success_criteria": ["Command executed successfully", "Output received"],
    "failure_handling": "Log error and report connection failure",
    "estimated_duration": 10
  }
]

Windows Impacket WMI Examples:
[
  {
    "tool": "windows-impacket-executor",
    "description": "Launch GUI app (wait: false) OR Execute command (wait: true)",
    "inputs": {
      "target_host": "192.168.50.211",
      "username": "stationadmin",
      "password": "password123",
      "command": "notepad.exe" OR "taskkill /F /IM notepad.exe" OR "dir C:\\\\path" OR "ping host" OR "sc query ServiceName" OR "systeminfo" OR "tasklist",
      "connection_type": "impacket",
      "wait": false (GUI apps) OR true (CLI commands),
      "interactive": true (GUI apps only),
      "domain": ""
    },
    "preconditions": ["Windows machine is reachable", "Credentials are valid"],
    "success_criteria": ["Command executed successfully"],
    "failure_handling": "Log error and report failure",
    "estimated_duration": 5
  }
]

For API/HTTP requests (Axis cameras, REST APIs, etc.):
[
  {
    "tool": "api-request" | "http-get" | "http-post" | etc.,
    "description": "Brief description of what this API call does",
    "inputs": {
      "host": "192.168.10.90",
      "path": "/axis-cgi/com/ptz.cgi",
      "protocol": "http",
      "method": "GET",
      "params": {
        "autofocus": "on",
        "camera": "1"
      },
      "username": "root",
      "password": "password123",
      "auth_type": "digest",  // REQUIRED for Axis cameras! Use "basic" only for other APIs
      "connection_type": "api"
    },
    "preconditions": ["Device is reachable", "Credentials are valid"],
    "success_criteria": ["HTTP 200 or 204 response", "Command accepted"],
    "failure_handling": "Log error and report API failure",
    "estimated_duration": 5
  }
]

IMPORTANT: 
- Axis cameras use HTTP Digest auth (auth_type: "digest")
- Axis VAPIX params: PTZ home={"move":"home"}, autofocus={"autofocus":"on","camera":"1"}
- Use GET method for Axis VAPIX commands

# MULTI-MACHINE EXECUTION WITH TEMPLATE VARIABLES

When the user asks to perform an action on MULTIPLE machines (e.g., "all Windows 10 machines", "machines with tag X", "all servers in production"), you MUST use template variables to enable loop execution:

**STEP 1: Query assets**
Create an asset-query step to find the target machines:
{
  "tool": "asset-query",
  "description": "Find all Windows 10 machines with win10 tag",
  "inputs": {
    "query_type": "filter",
    "filters": {"tags": "win10"},
    "fields": ["hostname", "ip_address", "id"]
  }
}

**STEP 2: Execute command on each machine using template variables**
Use template variables to reference the asset-query results. The system will automatically loop over all assets:
{
  "tool": "windows-filesystem-manager",
  "description": "Get C drive directory for each machine",
  "inputs": {
    "target_hosts": ["{{ip_address}}"],  // CRITICAL: Use template variable, NOT hardcoded IPs!
    "use_asset_credentials": true,
    "command": "Get-ChildItem C:\\\\",
    "connection_type": "powershell"
  }
}

**Available template variables from asset-query results:**
- {{hostname}} - Asset hostname
- {{ip_address}} - Asset IP address
- {{id}} - Asset ID (use this for automatic credential fetching)
- {{os_type}} - OS type
- {{os_version}} - OS version
- {{tags}} - Asset tags

**CRITICAL RULES FOR MULTI-MACHINE EXECUTION:**
1. When user says "all machines", "multiple machines", "machines with tag X", etc. → Use asset-query + template variables
2. ALWAYS use target_hosts: ["{{ip_address}}"] for multi-machine commands (NOT hardcoded IP list!)
3. For automatic credentials, the system will use the asset ID from each loop iteration
4. DO NOT hardcode asset_ids or target_hosts arrays when using asset-query results
5. The automation service will automatically detect template variables and execute the command once per asset

**Example: Multi-machine execution**
User: "get the directory of the c drive for all machines with the win10 tag"

CORRECT PLAN:
[
  {
    "tool": "asset-query",
    "description": "Find all Windows 10 machines with win10 tag",
    "inputs": {
      "query_type": "filter",
      "filters": {"tags": "win10"},
      "fields": ["hostname", "ip_address", "id"]
    }
  },
  {
    "tool": "windows-filesystem-manager",
    "description": "Get C drive directory for each Windows 10 machine",
    "inputs": {
      "target_hosts": ["{{ip_address}}"],  // Template variable - will loop over all assets
      "use_asset_credentials": true,
      "command": "Get-ChildItem C:\\\\",
      "connection_type": "powershell"
    }
  }
]

WRONG PLAN (DO NOT DO THIS):
[
  {
    "tool": "asset-query",
    "description": "Find all Windows 10 machines with win10 tag",
    "inputs": {
      "query_type": "filter",
      "filters": {"tags": "win10"},
      "fields": ["hostname", "ip_address", "id"]
    }
  },
  {
    "tool": "windows-filesystem-manager",
    "description": "Get C drive directory for each Windows 10 machine",
    "inputs": {
      "target_hosts": ["192.168.50.211", "192.168.50.212", "192.168.50.213"],  // WRONG! Hardcoded IPs
      "asset_ids": [21, 22, 23],  // WRONG! Hardcoded asset IDs
      "use_asset_credentials": true,
      "command": "Get-ChildItem C:\\\\",
      "connection_type": "powershell"
    }
  }
]

CRITICAL NOTES:
- Be intelligent about field selection for asset queries. Don't fetch all 50+ fields when only 5-10 are needed!
- ALWAYS extract target_host, username, and password from the user's query!
- The user may use informal language - translate to correct commands (see USER LANGUAGE TRANSLATION above)!
- For multi-machine operations, ALWAYS use template variables like {{ip_address}}, NOT hardcoded values!
- **FOR ALL POWERSHELL COMMANDS: ALWAYS add the hostname/IP as the FIRST column using @{Name='Host';Expression={'<IP_ADDRESS>'}}**
- **When user asks about MULTIPLE HOSTS (e.g., "192.168.50.212 and 192.168.50.213"), create SEPARATE steps for EACH host!**"""

    def _build_planning_user_prompt(self, decision: DecisionV1, selection: SelectionV1, context: Optional[Dict[str, Any]] = None) -> str:
        """Build the user prompt with decision and selection context"""
        import json
        
        # Extract key information
        user_query = decision.original_request
        intent_category = decision.intent.category
        intent_action = decision.intent.action
        # Convert Pydantic EntityV1 objects to dicts for JSON serialization
        entities = [entity.dict() if hasattr(entity, 'dict') else entity for entity in decision.entities]
        selected_tools = [tool.tool_name for tool in selection.selected_tools]
        
        prompt = f"""Create an execution plan for the following request:

**User Query:** {user_query}
"""
        
        # Add conversation history if available
        if context and "conversation_history" in context:
            conversation_history = context["conversation_history"]
            if conversation_history:
                prompt += f"""
**Conversation History (for context):**
{conversation_history}

IMPORTANT: Extract IP addresses, hostnames, credentials, and other parameters from the conversation history above!
If the current request refers to a device/camera mentioned earlier, use those details.
"""
        
        # Add credentials from asset database if available
        if context and "credentials_map" in context:
            credentials_map = context["credentials_map"]
            if credentials_map:
                prompt += f"""
**🔐 CREDENTIALS FROM ASSET DATABASE:**
The following credentials were automatically retrieved from the asset database for the hosts mentioned in your request.
YOU MUST USE THESE CREDENTIALS in your execution plan:

"""
                for ip, creds in credentials_map.items():
                    # Include password in prompt (it's needed for the LLM to create the plan)
                    # Note: This is internal communication between services, not exposed to users
                    password_value = creds.get('password', '[NOT SET]')
                    asset_id = creds.get('asset_id', 'N/A')
                    prompt += f"""
Host: {ip}
  - Asset ID: {asset_id}
  - Hostname: {creds.get('hostname', 'N/A')}
  - OS Type: {creds.get('os_type', 'N/A')}
  - Service Type: {creds.get('service_type', 'N/A')}
  - Port: {creds.get('port', 'N/A')}
  - Username: {creds.get('username', 'N/A')}
  - Password: {password_value}
  - Domain: {creds.get('domain', 'N/A')}
  - Credential Type: {creds.get('credential_type', 'N/A')}

"""
                prompt += """
CRITICAL CREDENTIAL HANDLING:
You have TWO options for handling credentials in your execution plan:

OPTION 1 (RECOMMENDED): Use automatic credential fetching
- Set "use_asset_credentials": true
- Set "asset_id": <asset_id from above>
- DO NOT include username or password fields
- The automation service will automatically fetch credentials from the asset database

OPTION 2: Explicitly include credentials
- Include "username": "<username from above>"
- Include "password": "<password from above>"
- DO NOT set use_asset_credentials

Example for windows-impacket-executor with automatic credentials (RECOMMENDED):
{
  "tool": "windows-impacket-executor",
  "inputs": {
    "target_host": "192.168.50.211",
    "use_asset_credentials": true,
    "asset_id": 21,
    "command": "notepad.exe",
    "connection_type": "impacket",
    "wait": false,
    "interactive": true
  }
}

Example for PowerShell with automatic credentials (RECOMMENDED):
{
  "tool": "Invoke-Command",
  "inputs": {
    "target_host": "192.168.50.211",
    "use_asset_credentials": true,
    "asset_id": 21,
    "command": "Get-ChildItem C:\\",
    "connection_type": "powershell"
  }
}

⚠️ CRITICAL WARNING: NEVER use -Recurse for directory listings unless EXPLICITLY requested!
- "show me the c:\\windows directory" → Get-ChildItem C:\\Windows (NO -Recurse)
- "list files in c:\\temp" → Get-ChildItem C:\\Temp (NO -Recurse)
- "show all files in c:\\windows recursively" → Get-ChildItem C:\\Windows -Recurse (ONLY when explicitly requested)
Using -Recurse on large directories like C:\\Windows can take 10+ minutes and timeout!

Example for PowerShell disk space query (CORRECT - use Size and SizeRemaining, ALWAYS include hostname/IP as first column):
{
  "tool": "Invoke-Command",
  "inputs": {
    "target_host": "192.168.50.212",
    "use_asset_credentials": true,
    "asset_id": 22,
    "command": "Get-Volume -DriveLetter C | Select-Object @{Name='Host';Expression={'192.168.50.212'}}, DriveLetter, @{Name='SizeGB';Expression={[math]::Round($_.Size/1GB,2)}}, @{Name='FreeGB';Expression={[math]::Round($_.SizeRemaining/1GB,2)}}",
    "connection_type": "powershell"
  }
}

Example for MULTIPLE HOSTS (create separate steps for each host):
User asks: "check disk space on 192.168.50.212 and 192.168.50.213"
CORRECT PLAN:
[
  {
    "tool": "Invoke-Command",
    "inputs": {
      "target_host": "192.168.50.212",
      "use_asset_credentials": true,
      "asset_id": 22,
      "command": "Get-Volume | Select-Object @{Name='Host';Expression={'192.168.50.212'}}, DriveLetter, @{Name='SizeGB';Expression={[math]::Round($_.Size/1GB,2)}}, @{Name='FreeGB';Expression={[math]::Round($_.SizeRemaining/1GB,2)}}",
      "connection_type": "powershell"
    }
  },
  {
    "tool": "Invoke-Command",
    "inputs": {
      "target_host": "192.168.50.213",
      "use_asset_credentials": true,
      "asset_id": 23,
      "command": "Get-Volume | Select-Object @{Name='Host';Expression={'192.168.50.213'}}, DriveLetter, @{Name='SizeGB';Expression={[math]::Round($_.Size/1GB,2)}}, @{Name='FreeGB';Expression={[math]::Round($_.SizeRemaining/1GB,2)}}",
      "connection_type": "powershell"
    }
  }
]

Example for windows-impacket-executor with explicit credentials (if needed):
{
  "tool": "windows-impacket-executor",
  "inputs": {
    "target_host": "192.168.50.211",
    "username": "stationadmin",
    "password": "Enabled123!",
    "command": "taskkill /F /IM notepad.exe",
    "connection_type": "impacket",
    "wait": true
  }
}
"""
        
        prompt += f"""
**Intent:**
- Category: {intent_category}
- Action: {intent_action}

**Extracted Entities:**
{json.dumps(entities, indent=2)}

**Selected Tools:**
{json.dumps(selected_tools, indent=2)}

**Tool Details with API Specifications:**
"""
        
        # Fetch full tool details from database to get API parameter specifications
        for tool in selection.selected_tools:
            prompt += f"\n### {tool.tool_name}\n"
            prompt += f"**Justification:** {tool.justification}\n"
            
            # Fetch tool details from database
            try:
                tool_details = self.tool_catalog.get_tool_by_name(tool.tool_name)
                if tool_details:
                    # Include tool defaults (HTTP method, protocol, auth_type, etc.)
                    if 'defaults' in tool_details:
                        defaults = tool_details['defaults']
                        prompt += f"**Tool Defaults:**\n"
                        if 'method' in defaults:
                            prompt += f"  • HTTP Method: {defaults['method']} (REQUIRED - DO NOT CHANGE)\n"
                        if 'protocol' in defaults:
                            prompt += f"  • Protocol: {defaults['protocol']}\n"
                        if 'auth_type' in defaults:
                            prompt += f"  • Auth Type: {defaults['auth_type']}\n"
                        if 'path' in defaults:
                            prompt += f"  • API Path: {defaults['path']}\n"
                    
                    if 'capabilities' in tool_details:
                        prompt += f"**Capabilities:**\n"
                        for cap_name, cap_data in tool_details['capabilities'].items():
                            prompt += f"\n- **{cap_name}:**\n"
                            if 'patterns' in cap_data:
                                for pattern in cap_data['patterns']:
                                    prompt += f"  - Pattern: {pattern.get('pattern_name', 'N/A')}\n"
                                    if 'required_inputs' in pattern:
                                        prompt += f"    Required Inputs:\n"
                                        for inp in pattern['required_inputs']:
                                            prompt += f"      • {inp.get('name')}: {inp.get('description', 'N/A')}\n"
                                            # Include API parameter mapping
                                            if 'metadata' in inp and 'api_parameters' in inp['metadata']:
                                                api_params = inp['metadata']['api_parameters']
                                                prompt += f"        API Parameters: {json.dumps(api_params)}\n"
                                            if 'metadata' in inp and 'example_request' in inp['metadata']:
                                                prompt += f"        Example: {inp['metadata']['example_request']}\n"
            except Exception as e:
                logger.warning(f"Could not fetch tool details for {tool.tool_name}: {e}")
                # Continue without tool details
        
        prompt += "\n\n**CRITICAL REQUIREMENTS:**"
        prompt += "\n1. Use the EXACT HTTP method specified in 'Tool Defaults' above (e.g., GET for Axis cameras, NOT POST)"
        prompt += "\n2. Use the EXACT API parameter names shown above (e.g., 'gotoserverpresetname', NOT 'presets')"
        prompt += "\n3. Use the EXACT auth_type specified in 'Tool Defaults' (e.g., 'digest' for Axis cameras)"
        prompt += "\n4. Return ONLY valid JSON - NO comments, NO explanations, NO trailing commas"
        prompt += "\n5. **FOR POWERSHELL: ALWAYS include hostname/IP as FIRST column: @{Name='Host';Expression={'<IP>'}}**"
        prompt += "\n6. **NEVER use -Recurse for directory listings unless EXPLICITLY requested by user!**"
        prompt += "\n   - 'show directory' = NO -Recurse (top-level only)"
        prompt += "\n   - 'list files' = NO -Recurse (top-level only)"
        prompt += "\n   - 'show all files recursively' = YES -Recurse (only when explicit)"
        prompt += "\nGenerate the execution steps as a JSON array. Remember to be intelligent about field selection!"
        
        return prompt
    
    def _enrich_step_with_tool_metadata(self, step, selection: SelectionV1):
        """
        Enrich execution step with tool metadata from the tool registry.
        This ensures the automation service has all the information it needs
        without having to infer or guess.
        
        Args:
            step: ExecutionStep to enrich
            selection: SelectionV1 with tool information
        """
        try:
            logger.info(f"🔍 Enriching step '{step.id}' (tool: {step.tool})...")
            
            # Import the tool registry
            from ..stage_b.tool_registry import ToolRegistry
            
            # Create a registry instance and load tools
            registry = ToolRegistry()
            logger.debug(f"   Registry has {registry.get_tool_count()} tools")
            
            # Look up the tool in the registry
            tool_def = registry.get_tool(step.tool)
            logger.debug(f"   Tool lookup result: {tool_def is not None}")
            
            if tool_def:
                logger.debug(f"   Tool has execution attr: {hasattr(tool_def, 'execution')}")
                if hasattr(tool_def, 'execution'):
                    logger.debug(f"   Execution value: {tool_def.execution}")
            
            if tool_def and hasattr(tool_def, 'execution') and tool_def.execution:
                # Extract execution metadata from the tool definition
                execution_meta = tool_def.execution
                
                # Handle nested connection metadata
                if isinstance(execution_meta, dict):
                    connection_meta = execution_meta.get("connection", {})
                    step.requires_credentials = connection_meta.get("requires_credentials", False)
                    step.execution_location = execution_meta.get("execution_location", "automation-service")
                    step.tool_metadata = execution_meta
                    
                    logger.info(f"✅ Enriched step '{step.id}' (tool: {step.tool})")
                    logger.info(f"   requires_credentials: {step.requires_credentials}")
                    logger.info(f"   execution_location: {step.execution_location}")
                    logger.info(f"   tool_metadata keys: {list(execution_meta.keys())}")
                else:
                    # Fallback if execution is not a dict
                    logger.warning(f"⚠️  Tool '{step.tool}' execution metadata is not a dict: {type(execution_meta)}")
                    step.requires_credentials = False
                    step.execution_location = "automation-service"
                    step.tool_metadata = {}
            else:
                # Tool not in registry or no execution metadata - use defaults
                logger.warning(f"⚠️  Tool '{step.tool}' not found in registry or has no execution metadata, using defaults")
                step.requires_credentials = False
                step.execution_location = "automation-service"
                step.tool_metadata = {}
                
        except ImportError as e:
            # Registry not available - this is OK, we'll use defaults
            logger.warning(f"Tool registry not available: {e}")
            step.requires_credentials = False
            step.execution_location = "automation-service"
            step.tool_metadata = {}
        except Exception as e:
            # Any other error - log but don't fail
            logger.warning(f"Failed to enrich step with tool metadata: {e}")
            import traceback
            logger.warning(traceback.format_exc())
            step.requires_credentials = False
            step.execution_location = "automation-service"
            step.tool_metadata = {}
    
    def _parse_llm_planning_response(self, response_content: str, selection: SelectionV1) -> List:
        """Parse LLM response into execution steps"""
        from ...schemas.plan_v1 import ExecutionStep
        import json
        import uuid
        import re
        
        try:
            # Extract JSON from response (handle markdown code blocks)
            content = response_content.strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            # Remove JSON comments (// style) that LLMs sometimes add
            # This regex removes // comments but preserves URLs like http://
            content = re.sub(r'(?<!:)//.*?(?=\n|$)', '', content)
            
            # Remove trailing commas before closing braces/brackets (common LLM mistake)
            content = re.sub(r',(\s*[}\]])', r'\1', content)
            
            # Fix unescaped backslashes in Windows paths (common LLM mistake)
            # This handles paths like C:\Windows\ -> C:\\Windows\\
            # We need to be careful not to double-escape already escaped backslashes
            # Match backslashes that are NOT already escaped (not preceded by another backslash)
            content = re.sub(r'(?<!\\)\\(?!["\\/bfnrtu])', r'\\\\', content)
            
            # Parse JSON
            steps_data = json.loads(content)
            
            # DEBUG: Log the parsed plan JSON
            logger.info(f"📋 LLM generated execution plan JSON: {json.dumps(steps_data, indent=2)}")
            
            # Convert to ExecutionStep objects
            steps = []
            for idx, step_data in enumerate(steps_data):
                step = ExecutionStep(
                    id=f"step_{uuid.uuid4().hex[:8]}",
                    description=step_data.get("description", "Execute operation"),
                    tool=step_data.get("tool"),
                    inputs=step_data.get("inputs", {}),
                    preconditions=step_data.get("preconditions", []),
                    success_criteria=step_data.get("success_criteria", ["operation_completed"]),
                    failure_handling=step_data.get("failure_handling", "Log error and abort"),
                    estimated_duration=step_data.get("estimated_duration", 10),
                    depends_on=[],
                    execution_order=idx + 1
                )
                
                # Enrich step with tool metadata from registry
                self._enrich_step_with_tool_metadata(step, selection)
                
                steps.append(step)
            
            return steps
            
        except Exception as e:
            # If LLM parsing fails, raise error - no fallback to rules!
            raise PlanningError(f"Failed to parse LLM planning response: {str(e)}\nResponse: {response_content}")