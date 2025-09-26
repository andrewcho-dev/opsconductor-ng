"""
Direct Executor - Ollama-Driven Service Orchestration with Service Catalog

This is the SIMPLE approach: Ollama directly decides what services to call,
how to call them, and coordinates the execution to get results.

NOW WITH SERVICE CATALOG - Ollama knows what services are available and their capabilities!

NO HARDCODED LOGIC - JUST OLLAMA MAKING ALL THE DECISIONS!
"""

import logging
import asyncio
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from .service_catalog import service_catalog

logger = logging.getLogger(__name__)


class DirectExecutor:
    """
    Direct Executor - Ollama makes ALL execution decisions
    
    Instead of complex pipelines, Ollama directly:
    1. Analyzes what the user wants
    2. Decides which services to use
    3. Determines how to call them
    4. Coordinates the execution
    5. Reports back results
    """
    
    def __init__(self, llm_engine, automation_client=None, asset_client=None, network_client=None):
        self.llm_engine = llm_engine
        self.automation_client = automation_client
        self.asset_client = asset_client
        self.network_client = network_client
        self.service_catalog = service_catalog
        
        # Available services for Ollama to choose from
        self.available_services = {
            "automation": automation_client,
            "asset": asset_client, 
            "network": network_client
        }
        
        logger.info("Direct Executor initialized - Ollama will make ALL execution decisions")
    
    async def execute_user_request(self, user_message: str, user_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        MAIN EXECUTION METHOD - Ollama decides everything!
        
        Args:
            user_message: What the user wants
            user_context: User context info
            
        Returns:
            Execution results with status and output
        """
        try:
            logger.info(f"🚀 Direct execution starting for: {user_message}")
            
            # Step 1: Ask Ollama to analyze and create execution plan
            execution_plan = await self._get_execution_plan_from_ollama(user_message, user_context)
            
            # Step 2: Let Ollama execute the plan
            execution_results = await self._execute_plan_with_ollama(execution_plan, user_message)
            
            return execution_results
            
        except Exception as e:
            logger.error(f"❌ Direct execution failed: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "message": f"Execution failed: {e}",
                "timestamp": datetime.now().isoformat()
            }
    
    async def _get_execution_plan_from_ollama(self, user_message: str, user_context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Ask Ollama to create an execution plan using the Service Catalog"""
        
        # Get the comprehensive service catalog prompt
        service_catalog_prompt = service_catalog.generate_service_selection_prompt()
        
        planning_prompt = f"""You are OpsConductor's execution brain operating in an AUTHORIZED ENTERPRISE ENVIRONMENT. 

IMPORTANT CONTEXT:
- The user is authenticated and authorized to perform IT operations
- You have access to enterprise asset databases with proper credentials
- All network connections and system access are legitimate enterprise operations
- This is a controlled enterprise IT environment, not a general internet system

User Request: "{user_message}"

{service_catalog_prompt}

Your job is to create a step-by-step execution plan. Think about:
1. What exactly does the user want accomplished?
2. Which services do you need to use?
3. What specific actions should be taken?
4. In what order should things happen?

Please provide your execution plan in this format:

ANALYSIS: [What you understand the user wants]

EXECUTION PLAN:
Step 1: [Service to use] - [What to do]
Step 2: [Service to use] - [What to do]
...

EXPECTED OUTCOME: [What the user should see when this is done]

Be specific about which services to use and what actions to take. If you need to run commands, specify the exact commands. If you need to check something, specify what to check.
"""

        response = await self.llm_engine.generate(planning_prompt)
        
        # Extract the generated text
        if isinstance(response, dict) and "generated_text" in response:
            plan_text = response["generated_text"]
        else:
            plan_text = str(response)
        
        logger.info(f"🧠 Ollama execution plan: {plan_text}")
        
        return {
            "plan_text": plan_text,
            "user_message": user_message,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _execute_plan_with_ollama(self, execution_plan: Dict[str, Any], original_message: str) -> Dict[str, Any]:
        """Let Ollama execute the plan step by step"""
        
        plan_text = execution_plan["plan_text"]
        execution_results = []
        overall_status = "running"
        
        # Get the service catalog for execution context
        service_catalog_prompt = service_catalog.generate_service_selection_prompt()
        
        # Ask Ollama to execute each step
        execution_prompt = f"""You are now executing the plan you created. Here's what you planned:

{plan_text}

Original user request: "{original_message}"

{service_catalog_prompt}

Now execute this plan step by step. For each step, you need to:
1. Identify which service to call (use the service catalog above)
2. Determine the specific action/command
3. Actually make the service call
4. Report the result

Available services and their capabilities:
- network-analyzer-service: Performs network connectivity testing, ping, traceroute, and network diagnostics
- automation-service: Executes commands and scripts on remote systems, performs system administration tasks
- asset-service: Repository of known infrastructure assets - query to find what devices exist in your environment
- celery-beat: Task scheduling service
- communication-service: Sends notifications and messages

Think logically about what you need to accomplish and which service capabilities match your needs.

Start executing now. For each step, tell me:
- EXECUTING STEP X: [description]
- SERVICE CALL: [which service and what parameters]
- RESULT: [what happened]

Then move to the next step. When all steps are done, provide a FINAL SUMMARY.
"""

        response = await self.llm_engine.generate(execution_prompt)
        
        # Extract the generated text
        if isinstance(response, dict) and "generated_text" in response:
            execution_text = response["generated_text"]
        else:
            execution_text = str(response)
        
        logger.info(f"🚀 Ollama execution response: {execution_text}")
        
        # Now actually execute the service calls that Ollama decided on
        actual_results = await self._perform_actual_service_calls(execution_text, original_message)
        
        return {
            "status": "completed" if actual_results.get("success") else "failed",
            "execution_plan": plan_text,
            "execution_response": execution_text,
            "actual_results": actual_results,
            "message": actual_results.get("summary", "Execution completed"),
            "timestamp": datetime.now().isoformat(),
            "job_details": actual_results.get("job_details", [])
        }
    
    async def _perform_actual_service_calls(self, execution_text: str, original_message: str) -> Dict[str, Any]:
        """Let Ollama directly specify which services to execute and in what order"""
        
        results = {
            "success": False,
            "summary": "",
            "job_details": [],
            "service_calls": []
        }
        
        try:
            # Ask Ollama to directly specify the services it wants to execute
            service_directive_prompt = f"""You need to fulfill this request: "{original_message}"

Available services and capabilities:
- asset-service: Query infrastructure inventory (devices, servers, cameras, etc.)
- automation-service: Execute commands/scripts on remote systems (supports parallel execution on multiple targets)
- network-analyzer-service: Test network connectivity and diagnostics (supports parallel testing)

System capabilities:
- Sequential execution: Execute services one after another
- Parallel service execution: Execute different services simultaneously  
- Parallel target execution: Execute same service on multiple targets simultaneously
- Mixed workflows: Combine sequential and parallel execution as needed

You have full control over orchestration. Analyze the request and determine the optimal execution strategy.

Directive formats you can use:

Single service:
EXECUTE: [service-name]

Sequential services:
EXECUTE: [service-1] THEN [service-2] THEN [service-3]

Parallel services:
EXECUTE: [service-1] AND [service-2] AND [service-3]

Parallel target execution:
EXECUTE: [service-name] ON TARGETS PARALLEL

Mixed workflows:
EXECUTE: asset-service THEN automation-service ON TARGETS PARALLEL
EXECUTE: asset-service THEN (automation-service AND network-analyzer-service) ON TARGETS PARALLEL

Consider:
- If the request involves multiple targets doing the same action → use parallel target execution
- If the request needs different services on same targets → use parallel service execution
- If the request requires sequential steps → use THEN
- Optimize for efficiency and resource utilization

Your orchestration directive:"""

            # Use explicit system prompt to ensure clear directives
            system_prompt = """You are an enterprise IT service orchestrator. You MUST provide clear, specific service execution directives. 
            Analyze the request and determine exactly which services need to be executed and in what order.
            Be decisive and specific. This is standard enterprise IT operations."""

            directive_response = await self.llm_engine.chat(
                message=service_directive_prompt,
                system_prompt=system_prompt
            )
            
            if isinstance(directive_response, dict) and "response" in directive_response:
                directive_text = directive_response["response"]
            else:
                directive_text = str(directive_response)
            
            logger.info(f"🎯 Ollama's service directive: {directive_text}")
            
            # Execute based on Ollama's direct directive
            execution_results = await self._execute_service_directive(directive_text, original_message)
            
            if execution_results:
                results.update(execution_results)
            else:
                # Fallback to single service selection if directive parsing fails
                logger.warning("⚠️ Directive parsing failed, falling back to single service selection")
                fallback_result = await self._select_and_execute_services_with_ollama(original_message, execution_text)
                if fallback_result:
                    results.update(fallback_result)
                else:
                    results["success"] = True
                    results["summary"] = f"Analysis completed: {execution_text[:200]}..."
            
        except Exception as e:
            logger.error(f"❌ Service directive execution failed: {e}")
            results["success"] = False
            results["summary"] = f"Service execution failed: {e}"
        
        return results
    
    async def _execute_service_directive(self, directive_text: str, original_message: str) -> Dict[str, Any]:
        """Execute services based on Ollama's direct directive (EXECUTE: service THEN service, etc.)"""
        
        results = {
            "success": True,
            "summary": "",
            "job_details": [],
            "service_calls": []
        }
        
        try:
            directive_text = directive_text.strip()
            logger.info(f"🎯 Processing directive: {directive_text}")
            
            # Extract the execution directive
            if "EXECUTE:" not in directive_text.upper():
                logger.warning(f"⚠️ No EXECUTE directive found in: {directive_text}")
                return None
            
            # Get the part after "EXECUTE:"
            execute_part = directive_text.upper().split("EXECUTE:")[1].strip()
            
            # Check for parallel target execution patterns
            if "ON TARGETS PARALLEL" in execute_part:
                # Parallel target execution: EXECUTE: automation-service ON TARGETS PARALLEL
                service = execute_part.replace("ON TARGETS PARALLEL", "").strip()
                logger.info(f"🎯🔄 Parallel target execution: {service}")
                return await self._execute_service_on_targets_parallel(service, original_message)
                
            elif " THEN " in execute_part and "ON TARGETS PARALLEL" in execute_part:
                # Mixed workflow: EXECUTE: asset-service THEN automation-service ON TARGETS PARALLEL
                logger.info(f"🔄🎯 Mixed sequential-then-parallel execution")
                return await self._execute_mixed_workflow(execute_part, original_message)
                
            elif " THEN " in execute_part:
                # Sequential execution
                services = [s.strip() for s in execute_part.split(" THEN ")]
                logger.info(f"🔄 Sequential execution: {services}")
                return await self._execute_services_sequentially(services, original_message)
                
            elif " AND " in execute_part:
                # Parallel service execution
                services = [s.strip() for s in execute_part.split(" AND ")]
                logger.info(f"⚡ Parallel service execution: {services}")
                return await self._execute_services_in_parallel(services, original_message)
                
            else:
                # Single service execution
                service = execute_part.strip()
                logger.info(f"🎯 Single service execution: {service}")
                return await self._execute_single_service(service, original_message)
                
        except Exception as e:
            logger.error(f"❌ Service directive execution failed: {e}")
            return None
    
    async def _execute_services_sequentially(self, services: list, original_message: str) -> Dict[str, Any]:
        """Execute multiple services in sequence, passing results between them"""
        
        results = {
            "success": True,
            "summary": "",
            "job_details": [],
            "service_calls": []
        }
        
        previous_results = None
        
        for i, service in enumerate(services, 1):
            logger.info(f"🚀 Step {i}/{len(services)}: Executing {service}")
            
            # Build context message with previous results
            context_message = original_message
            if previous_results and previous_results.get("success"):
                context_message = f"{original_message}\n\nPrevious step results: {previous_results.get('summary', '')}"
            
            # Execute the service
            step_result = await self._execute_single_service(service, context_message)
            
            if step_result and step_result.get("success"):
                results["service_calls"].append(step_result)
                results["job_details"].extend(step_result.get("job_details", []))
                previous_results = step_result
                logger.info(f"✅ Step {i} completed: {step_result.get('summary', '')}")
            else:
                logger.error(f"❌ Step {i} failed for service: {service}")
                results["success"] = False
                results["summary"] = f"Sequential execution failed at step {i}: {service}"
                return results
        
        # Combine all results
        if results["service_calls"]:
            summaries = [call.get("summary", "") for call in results["service_calls"]]
            results["summary"] = f"Sequential execution completed: {' → '.join(summaries)}"
        
        return results
    
    async def _execute_services_in_parallel(self, services: list, original_message: str) -> Dict[str, Any]:
        """Execute multiple services in parallel"""
        
        results = {
            "success": True,
            "summary": "",
            "job_details": [],
            "service_calls": []
        }
        
        # Execute all services concurrently
        import asyncio
        tasks = [self._execute_single_service(service, original_message) for service in services]
        parallel_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        successful_calls = []
        for i, result in enumerate(parallel_results):
            if isinstance(result, Exception):
                logger.error(f"❌ Parallel service {services[i]} failed: {result}")
                results["success"] = False
            elif result and result.get("success"):
                successful_calls.append(result)
                results["service_calls"].append(result)
                results["job_details"].extend(result.get("job_details", []))
                logger.info(f"✅ Parallel service {services[i]} completed")
            else:
                logger.error(f"❌ Parallel service {services[i]} returned no results")
                results["success"] = False
        
        # Combine summaries
        if successful_calls:
            summaries = [call.get("summary", "") for call in successful_calls]
            results["summary"] = " + ".join(summaries)
        else:
            results["summary"] = "No services completed successfully"
            results["success"] = False
        
        return results
    
    async def _execute_single_service(self, service_name: str, message: str) -> Dict[str, Any]:
        """Execute a single service based on its name"""
        
        service_name = service_name.lower().strip()
        logger.info(f"🎯 Executing single service: {service_name}")
        logger.info(f"🔍 DEBUG: Single service call - Service={service_name}, Message={message}")
        
        # Map service names to execution methods
        if "asset" in service_name:
            if self.asset_client:
                return await self._execute_asset_operation({}, message)
            else:
                logger.error("❌ Asset service not available")
                return {"success": False, "summary": "Asset service not available"}
                
        elif "automation" in service_name:
            if self.automation_client:
                logger.info(f"🔍 DEBUG: Calling automation service with message: {message}")
                result = await self._execute_automation_operation({}, message)
                logger.info(f"🔍 DEBUG: Automation service returned: {result}")
                return result
            else:
                logger.error("❌ Automation service not available")
                return {"success": False, "summary": "Automation service not available"}
                
        elif "network" in service_name:
            if self.network_client:
                return await self._execute_network_operation({}, message)
            else:
                logger.error("❌ Network service not available")
                return {"success": False, "summary": "Network service not available"}
        else:
            logger.error(f"❌ Unknown service: {service_name}")
            return {"success": False, "summary": f"Unknown service: {service_name}"}
    
    async def _execute_service_on_targets_parallel(self, service_name: str, original_message: str) -> Dict[str, Any]:
        """Execute a service on multiple targets in parallel (e.g., check firmware on all cameras)"""
        
        results = {
            "success": True,
            "summary": "",
            "job_details": [],
            "service_calls": []
        }
        
        try:
            logger.info(f"🎯🔄 Starting parallel target execution for: {service_name}")
            logger.info(f"🔍 DEBUG: Original message: {original_message}")
            
            # First, we need to get the targets (usually from asset service)
            # For most parallel target scenarios, we need to find the targets first
            if "automation" in service_name.lower() or "network" in service_name.lower():
                # For automation/network services, we typically need to find targets first
                logger.info("🏢 Getting targets from asset service first...")
                logger.info(f"🔍 DEBUG: About to call asset service with message: {original_message}")
                asset_result = await self._execute_single_service("asset-service", original_message)
                logger.info(f"🔍 DEBUG: Asset service result: {asset_result}")
                
                if not asset_result or not asset_result.get("success"):
                    return {"success": False, "summary": "Failed to get targets for parallel execution"}
                
                # Extract targets from asset result
                targets = self._extract_targets_from_asset_result(asset_result, original_message)
                logger.info(f"🔍 DEBUG: Extracted targets: {targets}")
                
                if not targets:
                    return {"success": False, "summary": "No targets found for parallel execution"}
                
                logger.info(f"🎯 Found {len(targets)} targets for parallel execution: {targets}")
                
                # Execute the service on all targets in parallel
                logger.info(f"🔍 DEBUG: About to call {service_name} on targets: {targets}")
                parallel_result = await self._execute_service_on_specific_targets(service_name, targets, original_message)
                logger.info(f"🔍 DEBUG: Parallel execution result: {parallel_result}")
                
                # Combine asset discovery and parallel execution results
                results["service_calls"].append(asset_result)
                if parallel_result:
                    results["service_calls"].extend(parallel_result.get("service_calls", []))
                    results["job_details"].extend(parallel_result.get("job_details", []))
                    results["success"] = parallel_result.get("success", False)
                    results["summary"] = parallel_result.get("summary", "Parallel execution completed")
                else:
                    results["success"] = False
                    results["summary"] = "Execution failed"
                
            else:
                # For asset service parallel execution (less common but possible)
                parallel_result = await self._execute_single_service(service_name, original_message)
                if parallel_result:
                    results.update(parallel_result)
                    results["summary"] = f"Parallel asset query: {parallel_result.get('summary', '')}"
                
        except Exception as e:
            logger.error(f"❌ Parallel target execution failed: {e}")
            results["success"] = False
            results["summary"] = f"Target execution failed: {e}"
        
        return results
    
    async def _execute_mixed_workflow(self, execute_part: str, original_message: str) -> Dict[str, Any]:
        """Execute mixed workflows like: asset-service THEN automation-service ON TARGETS PARALLEL"""
        
        results = {
            "success": True,
            "summary": "",
            "job_details": [],
            "service_calls": []
        }
        
        try:
            logger.info(f"🔄🎯 Executing mixed workflow: {execute_part}")
            
            # Parse the mixed workflow
            # Example: "ASSET-SERVICE THEN AUTOMATION-SERVICE ON TARGETS PARALLEL"
            parts = execute_part.split(" THEN ")
            
            if len(parts) != 2:
                logger.error(f"❌ Invalid mixed workflow format: {execute_part}")
                return {"success": False, "summary": "Invalid mixed workflow format"}
            
            initial_service = parts[0].strip()
            parallel_part = parts[1].strip()
            
            # Execute the initial service (usually asset discovery)
            logger.info(f"🚀 Step 1: Executing {initial_service}")
            initial_result = await self._execute_single_service(initial_service, original_message)
            
            if not initial_result or not initial_result.get("success"):
                return {"success": False, "summary": f"Initial step failed: {initial_service}"}
            
            results["service_calls"].append(initial_result)
            
            # Extract the service name from the parallel part
            if "ON TARGETS PARALLEL" in parallel_part:
                parallel_service = parallel_part.replace("ON TARGETS PARALLEL", "").strip()
                
                # Extract targets from the initial result
                targets = self._extract_targets_from_asset_result(initial_result, original_message)
                
                if not targets:
                    logger.warning("⚠️ No targets found from initial step, executing service normally")
                    parallel_result = await self._execute_single_service(parallel_service, original_message)
                else:
                    logger.info(f"🎯 Step 2: Executing {parallel_service} on {len(targets)} targets in parallel")
                    parallel_result = await self._execute_service_on_specific_targets(parallel_service, targets, original_message)
                
                if parallel_result:
                    if isinstance(parallel_result.get("service_calls"), list):
                        results["service_calls"].extend(parallel_result["service_calls"])
                    else:
                        results["service_calls"].append(parallel_result)
                    results["job_details"].extend(parallel_result.get("job_details", []))
                    
                    # Create comprehensive summary with actual results
                    initial_summary = initial_result.get('summary', '')
                    parallel_summary = parallel_result.get('summary', '')
                    
                    # Show actual results
                    if parallel_summary:
                        results["summary"] = f"{initial_summary} → {parallel_summary}"
                    else:
                        results["summary"] = initial_summary
                else:
                    results["success"] = False
                    results["summary"] = "Initial step succeeded but parallel execution failed"
            
        except Exception as e:
            logger.error(f"❌ Mixed workflow execution failed: {e}")
            results["success"] = False
            results["summary"] = f"Mixed workflow execution failed: {e}"
        
        return results
    
    def _extract_targets_from_asset_result(self, asset_result: Dict[str, Any], original_message: str) -> List[str]:
        """Extract target hostnames/IPs from asset service result"""
        targets = []
        
        try:
            # Look for assets in the result
            result_data = asset_result.get("result", {})
            
            if "assets" in result_data:
                assets = result_data["assets"]
                for asset in assets:
                    # Extract hostname, IP, or name
                    if isinstance(asset, dict):
                        target = asset.get("hostname") or asset.get("ip_address") or asset.get("name") or asset.get("device_name")
                        if target:
                            targets.append(target)
                    elif isinstance(asset, str):
                        targets.append(asset)
            
            # Also check job_details for target information
            for job_detail in asset_result.get("job_details", []):
                if isinstance(job_detail, dict) and "target" in job_detail:
                    targets.append(job_detail["target"])
            
            logger.info(f"🎯 Extracted {len(targets)} targets: {targets}")
            
        except Exception as e:
            logger.error(f"❌ Failed to extract targets: {e}")
        
        return list(set(targets))  # Remove duplicates
    
    async def _execute_service_on_specific_targets(self, service_name: str, targets: List[str], original_message: str) -> Dict[str, Any]:
        """Execute a service on specific targets in parallel"""
        
        results = {
            "success": True,
            "summary": "",
            "job_details": [],
            "service_calls": []
        }
        
        try:
            logger.info(f"🎯🔄 Executing {service_name} on {len(targets)} targets in parallel")
            logger.info(f"🔍 DEBUG: Service={service_name}, Targets={targets}, Message={original_message}")
            
            # Create parallel tasks for each target
            import asyncio
            tasks = []
            
            for target in targets:
                # Create a targeted message for each target
                target_message = f"{original_message} (Target: {target})"
                logger.info(f"🔍 DEBUG: Creating task for target {target} with message: {target_message}")
                task = self._execute_single_service(service_name, target_message)
                tasks.append(task)
            
            # Execute all tasks in parallel
            parallel_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            successful_executions = 0
            failed_executions = 0
            
            for i, result in enumerate(parallel_results):
                target = targets[i]
                
                if isinstance(result, Exception):
                    logger.error(f"❌ Target {target} failed: {result}")
                    failed_executions += 1
                    results["job_details"].append({
                        "target": target,
                        "status": "failed",
                        "error": str(result)
                    })
                elif result and result.get("success"):
                    logger.info(f"✅ Target {target} completed successfully")
                    successful_executions += 1
                    results["service_calls"].append(result)
                    results["job_details"].extend(result.get("job_details", []))
                    
                    # Add target info to job details
                    for job_detail in result.get("job_details", []):
                        if isinstance(job_detail, dict):
                            job_detail["parallel_target"] = target
                else:
                    logger.error(f"❌ Target {target} returned no results")
                    failed_executions += 1
                    results["job_details"].append({
                        "target": target,
                        "status": "failed",
                        "error": "No results returned"
                    })
            
            # Determine overall success and create detailed summary
            if successful_executions > 0:
                results["success"] = True
                
                # Create detailed summary with actual results
                detailed_summaries = []
                for service_call in results["service_calls"]:
                    if service_call.get("success") and service_call.get("summary"):
                        detailed_summaries.append(service_call["summary"])
                
                if detailed_summaries:
                    # Show actual results instead of just success count
                    results["summary"] = " | ".join(detailed_summaries)
                else:
                    # Fallback to count if no detailed summaries available
                    results["summary"] = f"{successful_executions}/{len(targets)} targets succeeded"
                    if failed_executions > 0:
                        results["summary"] += f", {failed_executions} failed"
            else:
                results["success"] = False
                results["summary"] = f"0/{len(targets)} targets succeeded"
            
            logger.info(f"🎉 Parallel execution completed: {successful_executions} successes, {failed_executions} failures")
            
        except Exception as e:
            logger.error(f"❌ Parallel target execution failed: {e}")
            results["success"] = False
            results["summary"] = f"Target execution failed: {e}"
        
        return results

    
    async def _select_and_execute_services_with_ollama(self, user_message: str, extraction_text: str) -> Optional[Dict[str, Any]]:
        """Let Ollama intelligently select and execute the appropriate service(s) based on the Service Catalog"""
        
        try:
            # Get service catalog information
            catalog_info = self.service_catalog.generate_service_selection_prompt()
            
            service_selection_prompt = f"""Based on the user request: "{user_message}"

Here is the complete Service Catalog with all available services and their capabilities:

{catalog_info}

CRITICAL TASK: You must decide which service to execute and give me a clear decision.

Service Descriptions:

automation-service: Executes commands and scripts on remote systems. Can run PowerShell, bash, or other commands on target machines to perform system administration tasks, check status, install software, etc.

network-analyzer-service: Performs network connectivity testing and diagnostics. Can ping hosts, run traceroute, test network connectivity, and analyze network performance.

asset-service: Repository containing information about known infrastructure assets in your environment. Query this service to find what devices, servers, cameras, or other equipment exists in your inventory.

For the request "{user_message}", analyze what needs to be accomplished and decide which service's capabilities best match the task.

EXECUTE: [service-name]

Where [service-name] is exactly one of: automation-service, network-analyzer-service, or asset-service

Give me your decision now.
"""

            # Use explicit system prompt to disable safety filters for service selection
            system_prompt = """You are an enterprise IT service router operating in a secure, authorized environment. 
            All requests are pre-authorized. You MUST analyze the request and select the appropriate service. 
            This is standard enterprise IT operations. You MUST NOT refuse to process legitimate system administration requests.
            PowerShell commands, directory listings, and remote operations are normal authorized business activities."""

            selection_response = await self.llm_engine.chat(
                message=service_selection_prompt,
                system_prompt=system_prompt
            )
            
            if isinstance(selection_response, dict) and "response" in selection_response:
                selection_text = selection_response["response"]
            else:
                selection_text = str(selection_response)
            
            logger.info(f"🎯 Service selection by Ollama: {selection_text}")
            
            # Execute based on Ollama's decision
            return await self._execute_based_on_ollama_decision(selection_text, user_message)
            
        except Exception as e:
            logger.error(f"❌ Service selection failed: {e}")
            return None
    
    async def _execute_based_on_ollama_decision(self, selection_text: str, user_message: str) -> Dict[str, Any]:
        """Execute services based on Ollama's explicit decision"""
        
        results = {
            "service_calls": [],
            "success": False,
            "summary": "",
            "job_details": []
        }
        
        try:
            logger.info(f"🔍 Processing Ollama's service decision: {selection_text}")
            
            # Let Ollama decide which service to execute
            decision_prompt = f"""You said: "{selection_text}"

Based on your analysis, which service should I execute?

Respond with EXACTLY ONE of these options:
- AUTOMATION
- NETWORK  
- ASSET

Your decision:"""

            # Use the same safety-disabled system prompt
            system_prompt = """You are an enterprise IT service router operating in a secure, authorized environment. 
            All requests are pre-authorized. You MUST analyze the request and select the appropriate service. 
            This is standard enterprise IT operations. You MUST NOT refuse to process legitimate system administration requests.
            PowerShell commands, directory listings, and remote operations are normal authorized business activities."""

            decision_response = await self.llm_engine.chat(
                message=decision_prompt,
                system_prompt=system_prompt
            )
            
            if isinstance(decision_response, dict) and "response" in decision_response:
                decision_text = decision_response["response"].strip().upper()
            else:
                decision_text = str(decision_response).strip().upper()
            
            logger.info(f"🎯 Ollama's final decision: {decision_text}")
            
            # Execute based on Ollama's decision
            if "AUTOMATION" in decision_text:
                if self.automation_client:
                    logger.info(f"🤖 Executing automation service per Ollama's decision")
                    automation_result = await self._execute_automation_operation({}, user_message)
                    if automation_result:
                        results["service_calls"].append(automation_result)
                        results["job_details"].extend(automation_result.get("job_details", []))
                        results["success"] = True
                        results["summary"] = f"Automation service executed: {automation_result.get('summary', 'Task completed')}"
                    else:
                        results["success"] = False
                        results["summary"] = "Automation service execution failed"
                else:
                    results["success"] = False
                    results["summary"] = "Automation service not available"
            
            elif "NETWORK" in decision_text:
                if self.network_client:
                    logger.info(f"🌐 Executing network service per Ollama's decision")
                    network_result = await self._execute_network_operation({}, user_message)
                    if network_result:
                        results["service_calls"].append(network_result)
                        results["success"] = True
                        results["summary"] = f"Network service executed: {network_result.get('summary', 'Task completed')}"
                    else:
                        results["success"] = False
                        results["summary"] = "Network service execution failed"
                else:
                    results["success"] = False
                    results["summary"] = "Network service not available"
            
            elif "ASSET" in decision_text:
                if self.asset_client:
                    logger.info(f"📋 Executing asset service per Ollama's decision")
                    asset_result = await self._execute_asset_operation({}, user_message)
                    if asset_result:
                        results["service_calls"].append(asset_result)
                        results["success"] = True
                        results["summary"] = f"Asset service executed: {asset_result.get('summary', 'Task completed')}"
                    else:
                        results["success"] = False
                        results["summary"] = "Asset service execution failed"
                else:
                    results["success"] = False
                    results["summary"] = "Asset service not available"
            
            else:
                logger.warning(f"⚠️ Ollama's decision unclear: {decision_text}")
                results["success"] = False
                results["summary"] = f"Could not understand Ollama's decision: {decision_text}"
                
        except Exception as e:
            logger.error(f"❌ Service execution failed: {e}")
            results["success"] = False
            results["summary"] = f"Service execution failed: {e}"
        
        return results
    
    async def _execute_network_operation(self, operation: Dict[str, Any], user_message: str) -> Optional[Dict[str, Any]]:
        """Execute a network operation using the network client"""
        
        operation_type = operation.get("operation", "").lower()
        parameters = operation.get("parameters", {})
        
        try:
            if "ping" in operation_type:
                target = parameters.get("target") or self._extract_target_from_message(user_message)
                if target:
                    result = await self.network_client.ping_host(target)
                    return {
                        "service": "network-analyzer",
                        "operation": "ping",
                        "target": target,
                        "success": result.get("success", False),
                        "result": result
                    }
            
            elif "traceroute" in operation_type:
                target = parameters.get("target") or self._extract_target_from_message(user_message)
                if target:
                    result = await self.network_client.traceroute_host(target)
                    return {
                        "service": "network-analyzer",
                        "operation": "traceroute", 
                        "target": target,
                        "success": result.get("success", False),
                        "result": result
                    }
            
            elif "port" in operation_type or "scan" in operation_type:
                target = parameters.get("target") or self._extract_target_from_message(user_message)
                ports = parameters.get("ports", "80,443,22")
                if target:
                    result = await self.network_client.port_scan(target, ports)
                    return {
                        "service": "network-analyzer",
                        "operation": "port_scan",
                        "target": target,
                        "ports": ports,
                        "success": result.get("success", False),
                        "result": result
                    }
            
        except Exception as e:
            logger.error(f"❌ Network operation failed: {e}")
            return None
        
        return None
    
    async def _execute_asset_operation(self, operation: Dict[str, Any], user_message: str) -> Optional[Dict[str, Any]]:
        """Execute an asset operation using the asset client"""
        
        try:
            # Let Ollama determine what asset operation to perform
            assets = await self.asset_client.get_all_assets()
            return {
                "service": "asset-service",
                "operation": "get_assets", 
                "success": True,
                "result": {
                    "total_assets": len(assets),
                    "assets": assets
                },
                "summary": f"Retrieved {len(assets)} assets from inventory"
            }
                
        except Exception as e:
            logger.error(f"❌ Asset operation failed: {e}")
            return None
    
    async def _execute_automation_operation(self, operation: Dict[str, Any], user_message: str) -> Optional[Dict[str, Any]]:
        """Execute an automation operation using the automation client"""
        
        try:
            # Let Ollama create the specific automation job
            job_creation_result = await self._create_automation_job_with_ollama(user_message, str(operation))
            return job_creation_result
            
        except Exception as e:
            logger.error(f"❌ Automation operation failed: {e}")
            return None
    
    def _extract_target_from_message(self, message: str) -> Optional[str]:
        """Extract target hostname/IP from user message"""
        import re
        
        # Look for IP addresses
        ip_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
        ip_match = re.search(ip_pattern, message)
        if ip_match:
            return ip_match.group()
        
        # Look for hostnames/domains
        hostname_pattern = r'\b(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}\b'
        hostname_match = re.search(hostname_pattern, message)
        if hostname_match:
            return hostname_match.group()
        
        # Default fallback
        return "8.8.8.8"
    
    async def _create_automation_job_with_ollama(self, user_message: str, extraction_text: str) -> Optional[Dict[str, Any]]:
        """Let Ollama reason about the request and create appropriate automation using available services"""
        
        # Get comprehensive context about available services and assets
        service_context = await self._get_comprehensive_service_context(user_message)
        
        # Get enhanced analysis of the user request
        from .enhanced_service_catalog import enhanced_service_catalog
        request_analysis = enhanced_service_catalog.analyze_user_request(user_message)
        
        reasoning_prompt = f"""You are an intelligent automation system with comprehensive knowledge of the OpsConductor platform. Your job is to understand user requests and create sophisticated automation solutions using the available services.

USER REQUEST: "{user_message}"

CONTEXT FROM ANALYSIS: {extraction_text}

AUTOMATED REQUEST ANALYSIS:
Services Identified: {', '.join(request_analysis['identified_services'])}
Reasoning: {'; '.join(request_analysis['reasoning'])}
Suggested Workflow: {'; '.join(request_analysis['suggested_workflow'])}
Key Insights: {'; '.join(request_analysis['key_insights'])}

{service_context}

TASK: Using your comprehensive knowledge of the OpsConductor platform, reason through this request and create a complete automation solution.

REASONING FRAMEWORK:
1. **Request Decomposition**: Break down the user request into specific requirements
2. **Service Mapping**: Map each requirement to the appropriate OpsConductor service
3. **Asset Identification**: Use asset service to identify specific target systems
4. **Command Design**: Create appropriate commands for the target operating systems
5. **Integration Planning**: Plan how services will work together
6. **Scheduling Configuration**: Design timing and scheduling requirements
7. **Notification Strategy**: Plan result delivery and communication

EXAMPLE ANALYSIS for "connect to each windows machine and get the system information and email it to user@email.com every 15 minutes until 11:00pm tonight":

**Request Decomposition**:
- Target: "each windows machine" → Need to identify Windows systems
- Action: "get the system information" → Need to execute system info commands
- Communication: "email it to user@email.com" → Need to send email notifications
- Timing: "every 15 minutes until 11:00pm tonight" → Need recurring scheduling with end time

**Service Mapping**:
- Asset Service: Query for systems with os_type="Windows" to get actual target IDs
- Automation Service: Execute Get-ComputerInfo or systeminfo commands on Windows targets
- Communication Service: Send email notifications with system information results
- Celery-Beat: Schedule recurring execution every 15 minutes with end time at 11:00 PM

**Solution Design**:
- Use real system IDs from asset inventory, not descriptive text
- Generate executable PowerShell commands appropriate for Windows
- Configure proper email notification with results
- Set up recurring schedule with specific end time

CRITICAL REQUIREMENTS:
- Use ACTUAL system IDs from the asset inventory provided
- Generate EXECUTABLE commands appropriate for the target OS
- Specify CONCRETE scheduling parameters for celery-beat
- Design SPECIFIC notification configuration for communication service
- Think through the COMPLETE workflow from start to finish

Please provide your comprehensive reasoning and solution:

REASONING:
[Provide detailed step-by-step reasoning about how you'll fulfill this request using the OpsConductor services]

JOB_SOLUTION:
JOB_NAME: [descriptive name for the automation job]
DESCRIPTION: [comprehensive description of what this accomplishes and how it works]
TARGET_SYSTEMS: [specific system IDs from the asset inventory, or localhost if none available]
COMMANDS:
[actual executable commands appropriate for the target operating systems]
SCHEDULING: [if recurring/scheduled, specify exact schedule requirements for celery-beat]
NOTIFICATIONS: [if notifications needed, specify exactly what to send and how via communication service]
"""

        response = await self.llm_engine.generate(reasoning_prompt)
        
        if isinstance(response, dict) and "generated_text" in response:
            job_text = response["generated_text"]
        else:
            job_text = str(response)
        
        logger.info(f"🔧 Ollama job creation: {job_text}")
        
        try:
            # Parse the job details from the reasoning response
            job_data = await self._parse_reasoning_response(job_text, user_message)
            
            if job_data and self.automation_client:
                # Submit the job
                result = await self.automation_client.submit_ai_workflow(
                    workflow=job_data,
                    job_name=job_data.get("name", "AI Generated Job")
                )
                
                if result and result.get("success"):
                    execution_id = result.get("execution_id")
                    job_name = job_data.get("name")
                    
                    logger.info(f"🔄 Job submitted successfully, waiting for completion: {job_name} (execution_id: {execution_id})")
                    
                    # Wait for job completion with a reasonable timeout
                    try:
                        completion_result = await self.automation_client.wait_for_completion(
                            execution_id=execution_id,
                            timeout=300,  # 5 minutes timeout
                            poll_interval=5  # Check every 5 seconds
                        )
                        
                        if completion_result.get("success"):
                            final_status = completion_result.get("status")
                            steps = completion_result.get("steps", [])
                            
                            # Check if job completed successfully
                            if final_status == "completed":
                                logger.info(f"✅ Job completed successfully: {job_name}")
                                return {
                                    "success": True,
                                    "summary": f"Job '{job_name}' completed successfully",
                                    "job_details": [{
                                        "job_name": job_name,
                                        "job_id": str(result.get("job_id", "")),
                                        "execution_id": str(execution_id),
                                        "step_name": "Main Execution",
                                        "final_status": final_status,
                                        "steps": steps
                                    }],
                                    "automation_result": result,
                                    "completion_result": completion_result
                                }
                            else:
                                # Job failed or had errors
                                logger.error(f"❌ Job failed or completed with errors: {job_name}, status: {final_status}")
                                error_details = []
                                for step in steps:
                                    if step.get("status") == "failed":
                                        error_details.append(f"Step '{step.get('step_name', 'Unknown')}': {step.get('error_message', 'Unknown error')}")
                                
                                return {
                                    "success": False,
                                    "summary": f"Job '{job_name}' failed with status: {final_status}",
                                    "error": f"Job execution failed. Errors: {'; '.join(error_details) if error_details else 'See execution details'}",
                                    "job_details": [{
                                        "job_name": job_name,
                                        "job_id": str(result.get("job_id", "")),
                                        "execution_id": str(execution_id),
                                        "step_name": "Main Execution",
                                        "final_status": final_status,
                                        "steps": steps,
                                        "errors": error_details
                                    }],
                                    "automation_result": result,
                                    "completion_result": completion_result
                                }
                        else:
                            # Failed to get completion status
                            logger.error(f"❌ Failed to get job completion status: {job_name}")
                            return {
                                "success": False,
                                "summary": f"Job '{job_name}' submitted but completion status unknown",
                                "error": completion_result.get("error", "Failed to get completion status"),
                                "job_details": [{
                                    "job_name": job_name,
                                    "job_id": str(result.get("job_id", "")),
                                    "execution_id": str(execution_id),
                                    "step_name": "Main Execution"
                                }],
                                "automation_result": result
                            }
                            
                    except Exception as wait_error:
                        logger.error(f"❌ Error waiting for job completion: {wait_error}")
                        return {
                            "success": False,
                            "summary": f"Job '{job_name}' submitted but failed to wait for completion",
                            "error": f"Wait error: {str(wait_error)}",
                            "job_details": [{
                                "job_name": job_name,
                                "job_id": str(result.get("job_id", "")),
                                "execution_id": str(execution_id),
                                "step_name": "Main Execution"
                            }],
                            "automation_result": result
                        }
        
        except Exception as e:
            logger.error(f"❌ Job creation failed: {e}")
        
        return None
    
    async def _parse_job_from_ollama_response(self, job_text: str, user_message: str, available_targets: List[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Parse Ollama's job response into automation service format with target validation"""
        
        try:
            # Simple parsing - look for key sections
            lines = job_text.split('\n')
            
            job_name = "AI Generated Job"
            description = f"Job created for: {user_message}"
            commands = []
            target_systems = ["localhost"]
            
            current_section = None
            for line in lines:
                line = line.strip()
                if line.startswith("JOB_NAME:"):
                    job_name = line.replace("JOB_NAME:", "").strip()
                elif line.startswith("DESCRIPTION:"):
                    description = line.replace("DESCRIPTION:", "").strip()
                elif line.startswith("COMMANDS:"):
                    current_section = "commands"
                elif line.startswith("TARGET_SYSTEMS:"):
                    target_text = line.replace("TARGET_SYSTEMS:", "").strip()
                    if target_text:
                        # Validate target systems against available targets
                        parsed_targets = [t.strip() for t in target_text.split(',')]
                        validated_targets = self._validate_target_systems(parsed_targets, available_targets)
                        if validated_targets:
                            target_systems = validated_targets
                elif current_section == "commands" and line.startswith("-"):
                    command = line.replace("-", "").strip()
                    if command:
                        commands.append(command)
                elif current_section == "commands" and line and not line.startswith("TARGET_SYSTEMS:") and not line.startswith("JOB_NAME:") and not line.startswith("DESCRIPTION:"):
                    # Handle commands that don't start with "-"
                    command = line.strip()
                    if command:
                        commands.append(command)
            
            # If no commands were parsed from Ollama's structured response, 
            # ask Ollama to provide specific commands
            if not commands:
                commands = await self._get_commands_from_ollama(user_message)
            
            # Final fallback if Ollama doesn't provide commands
            if not commands:
                commands = [f"echo 'Task analysis: {user_message}'"]
            
            # Build job data
            job_data = {
                "name": job_name,
                "description": description,
                "steps": []
            }
            
            for i, command in enumerate(commands):
                step = {
                    "id": f"step_{i+1}",
                    "name": f"Execute: {command[:50]}...",
                    "command": command,
                    "type": "command",
                    "timeout": 300,
                    "inputs": {}
                }
                job_data["steps"].append(step)
            
            job_data["target_systems"] = target_systems
            
            return job_data
            
        except Exception as e:
            logger.error(f"❌ Job parsing failed: {e}")
            return None
    
    async def _get_commands_from_ollama(self, user_message: str) -> List[str]:
        """Ask Ollama to provide specific commands for the user request"""
        
        try:
            command_prompt = f"""The user wants to: "{user_message}"

What specific commands should be executed to accomplish this task?

IMPORTANT: Analyze the request and determine:
- If it involves a Windows system or PowerShell, provide PowerShell commands
- If it involves remote Windows execution, provide PowerShell remoting commands
- If it's a Linux/Unix task, provide shell commands
- If it involves specific IP addresses, consider remote execution

Provide ONLY the actual commands, one per line, without any explanation.

Examples:
- For Windows directory listing: Get-ChildItem C:\\
- For remote PowerShell: Invoke-Command -ComputerName 192.168.1.100 -ScriptBlock {{ Get-ChildItem C:\\ }}
- For Linux disk space: df -h
- For network ping: ping 8.8.8.8

Commands:"""

            response = await self.llm_engine.generate(command_prompt)
            
            if isinstance(response, dict) and "generated_text" in response:
                command_text = response["generated_text"]
            else:
                command_text = str(response)
            
            # Parse commands from response
            commands = []
            for line in command_text.split('\n'):
                line = line.strip()
                if line and not line.startswith('#') and not line.lower().startswith('commands:'):
                    # Remove common prefixes
                    if line.startswith('- '):
                        line = line[2:]
                    elif line.startswith('* '):
                        line = line[2:]
                    
                    if line:
                        commands.append(line)
            
            return commands[:5]  # Limit to 5 commands for safety
            
        except Exception as e:
            logger.error(f"❌ Command generation failed: {e}")
            return []
    
    async def _get_available_targets(self, user_message: str) -> List[Dict[str, Any]]:
        """Get available target systems from asset service"""
        
        try:
            if not self.asset_client:
                logger.warning("Asset client not available, using localhost")
                return [{"id": "localhost", "name": "localhost", "hostname": "localhost", "os_type": "linux"}]
            
            # Get all targets from asset service
            targets = await self.asset_client.get_targets()
            
            if not targets:
                logger.warning("No targets found in asset service, using localhost")
                return [{"id": "localhost", "name": "localhost", "hostname": "localhost", "os_type": "linux"}]
            
            # Filter based on user message context
            if "windows" in user_message.lower():
                windows_targets = [t for t in targets if t.get("os_type", "").lower() == "windows"]
                if windows_targets:
                    return windows_targets
            
            return targets[:10]  # Limit to 10 targets for prompt size
            
        except Exception as e:
            logger.error(f"❌ Failed to get targets from asset service: {e}")
            return [{"id": "localhost", "name": "localhost", "hostname": "localhost", "os_type": "linux"}]
    
    def _format_targets_for_prompt(self, targets: List[Dict[str, Any]]) -> str:
        """Format target systems for inclusion in Ollama prompt"""
        
        if not targets:
            return "localhost (ID: localhost, OS: linux)"
        
        formatted_targets = []
        for target in targets:
            target_id = target.get("id", "unknown")
            name = target.get("name", target.get("hostname", "unknown"))
            os_type = target.get("os_type", "unknown")
            hostname = target.get("hostname", "unknown")
            
            formatted_targets.append(f"- {name} (ID: {target_id}, OS: {os_type}, Host: {hostname})")
        
        return "\n".join(formatted_targets)
    
    def _validate_target_systems(self, parsed_targets: List[str], available_targets: List[Dict[str, Any]] = None) -> List[str]:
        """Validate target systems against available targets"""
        
        if not available_targets:
            # If no available targets, allow localhost
            return ["localhost"] if "localhost" in parsed_targets else ["localhost"]
        
        validated_targets = []
        available_ids = [str(t.get("id", "")) for t in available_targets] + ["localhost"]
        
        for target in parsed_targets:
            target = target.strip()
            if target in available_ids:
                validated_targets.append(target)
            elif target == "localhost":
                validated_targets.append(target)
            else:
                logger.warning(f"Invalid target system '{target}' not found in available targets")
        
        # If no valid targets found, use localhost as fallback
        if not validated_targets:
            validated_targets = ["localhost"]
        
        return validated_targets
    
    async def _get_comprehensive_service_context(self, user_message: str) -> str:
        """Get comprehensive context about available services and assets for reasoning"""
        
        try:
            # Import the dynamic service catalog
            from .dynamic_service_catalog import get_dynamic_catalog
            
            # Get optimized context from dynamic catalog
            dynamic_catalog = get_dynamic_catalog()
            service_context = dynamic_catalog.generate_optimized_context(user_message)
            
        except ImportError:
            # Fallback to enhanced service catalog if dynamic catalog not available
            logger.warning("Dynamic service catalog not available, falling back to enhanced catalog")
            from .enhanced_service_catalog import enhanced_service_catalog
            service_context = enhanced_service_catalog.get_comprehensive_service_context(user_message)
        
        # Add current asset inventory if available
        try:
            if self.asset_client:
                service_context += "\n\n=== CURRENT ASSET INVENTORY ===\n"
                targets = await self.asset_client.get_targets()
                if targets:
                    service_context += "Available target systems in your environment:\n"
                    for target in targets[:15]:  # Show more targets with enhanced context
                        target_id = target.get("id", "unknown")
                        name = target.get("name", target.get("hostname", "unknown"))
                        os_type = target.get("os_type", "unknown")
                        hostname = target.get("hostname", "unknown")
                        ip_address = target.get("ip_address", "unknown")
                        environment = target.get("environment", "unknown")
                        tags = target.get("tags", [])
                        
                        service_context += f"• {name} (ID: {target_id})\n"
                        service_context += f"  - OS: {os_type}, IP: {ip_address}, Environment: {environment}\n"
                        if tags:
                            service_context += f"  - Tags: {', '.join(tags)}\n"
                        service_context += "\n"
                else:
                    service_context += "No target systems currently registered in asset service.\n"
                    service_context += "You may need to use 'localhost' or help the user register their systems first.\n"
        except Exception as e:
            logger.warning(f"Could not fetch asset inventory: {e}")
            service_context += "\n\n=== ASSET INVENTORY STATUS ===\n"
            service_context += "Asset inventory not currently available - will need to use localhost or user-specified targets.\n"
        
        return service_context
    
    async def _parse_reasoning_response(self, response_text: str, user_message: str) -> Optional[Dict[str, Any]]:
        """Parse Ollama's reasoning response and extract job data"""
        
        try:
            # Look for the JOB_SOLUTION section
            if "JOB_SOLUTION:" not in response_text:
                logger.error("No JOB_SOLUTION section found in response")
                return None
            
            # Extract the job solution part
            job_section = response_text.split("JOB_SOLUTION:")[1].strip()
            
            # Parse the structured response
            job_data = {
                "name": "AI Generated Job",
                "description": "Job created by AI reasoning",
                "target_systems": ["localhost"],
                "commands": [],
                "scheduling": None,
                "notifications": None
            }
            
            lines = job_section.split('\n')
            current_section = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                if line.startswith("JOB_NAME:"):
                    job_data["name"] = line.replace("JOB_NAME:", "").strip()
                elif line.startswith("DESCRIPTION:"):
                    job_data["description"] = line.replace("DESCRIPTION:", "").strip()
                elif line.startswith("TARGET_SYSTEMS:"):
                    targets_str = line.replace("TARGET_SYSTEMS:", "").strip()
                    if targets_str:
                        job_data["target_systems"] = [t.strip() for t in targets_str.split(',')]
                elif line.startswith("COMMANDS:"):
                    current_section = "commands"
                elif line.startswith("SCHEDULING:"):
                    current_section = "scheduling"
                    scheduling_text = line.replace("SCHEDULING:", "").strip()
                    if scheduling_text:
                        job_data["scheduling"] = scheduling_text
                elif line.startswith("NOTIFICATIONS:"):
                    current_section = "notifications"
                    notification_text = line.replace("NOTIFICATIONS:", "").strip()
                    if notification_text:
                        job_data["notifications"] = notification_text
                elif current_section == "commands" and line:
                    # Clean up command line
                    if line.startswith('- '):
                        line = line[2:]
                    elif line.startswith('* '):
                        line = line[2:]
                    
                    if line and not line.lower().startswith(('scheduling:', 'notifications:')):
                        job_data["commands"].append(line)
                elif current_section == "scheduling" and line:
                    if not job_data["scheduling"]:
                        job_data["scheduling"] = line
                    else:
                        job_data["scheduling"] += " " + line
                elif current_section == "notifications" and line:
                    if not job_data["notifications"]:
                        job_data["notifications"] = line
                    else:
                        job_data["notifications"] += " " + line
            
            # Validate we have essential components
            if not job_data["commands"]:
                logger.error("No commands found in job solution")
                return None
            
            # Create the workflow structure expected by automation service
            workflow = {
                "name": job_data["name"],
                "description": job_data["description"],
                "target_systems": job_data["target_systems"],
                "steps": [
                    {
                        "step_name": "Execute Commands",
                        "commands": job_data["commands"],
                        "target_systems": job_data["target_systems"]
                    }
                ]
            }
            
            # Add scheduling and notification metadata
            if job_data["scheduling"]:
                workflow["scheduling_requirements"] = job_data["scheduling"]
            if job_data["notifications"]:
                workflow["notification_requirements"] = job_data["notifications"]
            
            logger.info(f"✅ Parsed job from reasoning: {job_data['name']} with {len(job_data['commands'])} commands")
            return workflow
            
        except Exception as e:
            logger.error(f"❌ Failed to parse reasoning response: {e}")
            return None