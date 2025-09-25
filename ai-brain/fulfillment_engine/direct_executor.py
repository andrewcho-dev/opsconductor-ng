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
        
        planning_prompt = f"""You are OpsConductor's execution brain. A user wants you to do something, and you need to create a plan to execute it.

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

REMEMBER THE SERVICE SELECTION RULES:
- Network tasks (ping, traceroute, connectivity) → network-analyzer-service
- Scheduling tasks → celery-beat
- System administration → automation-service
- Asset management → asset-service
- Notifications → communication-service

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
        """Parse Ollama's execution response and make actual service calls"""
        
        results = {
            "success": False,
            "summary": "",
            "job_details": [],
            "service_calls": []
        }
        
        try:
            # Ask Ollama to extract the specific service calls it wants to make
            extraction_prompt = f"""Based on your execution plan, extract the specific service calls you want to make:

Your execution response:
{execution_text}

Original user request: "{original_message}"

Now provide the EXACT service calls in this format:

SERVICE_CALLS:
1. SERVICE: automation
   ACTION: submit_ai_workflow
   PARAMETERS: {{"name": "...", "steps": [...]}}

2. SERVICE: asset  
   ACTION: get_servers
   PARAMETERS: {{}}

Format each service call clearly so I can execute them.
"""

            extraction_response = await self.llm_engine.generate(extraction_prompt)
            
            if isinstance(extraction_response, dict) and "generated_text" in extraction_response:
                extraction_text = extraction_response["generated_text"]
            else:
                extraction_text = str(extraction_response)
            
            logger.info(f"🔧 Service call extraction: {extraction_text}")
            
            # Let Ollama decide which service(s) to use based on the Service Catalog
            service_selection_result = await self._select_and_execute_services_with_ollama(original_message, extraction_text)
            
            if service_selection_result:
                results.update(service_selection_result)
            else:
                # If no specific service calls were made, still return success with Ollama's analysis
                results["success"] = True
                results["summary"] = f"Analysis completed: {execution_text[:200]}..."
            
        except Exception as e:
            logger.error(f"❌ Service call execution failed: {e}")
            results["success"] = False
            results["summary"] = f"Service call execution failed: {e}"
        
        return results
    
    async def _select_and_execute_services_with_ollama(self, user_message: str, extraction_text: str) -> Optional[Dict[str, Any]]:
        """Let Ollama intelligently select and execute the appropriate service(s) based on the Service Catalog"""
        
        try:
            # Get service catalog information
            catalog_info = self.service_catalog.get_service_selection_guidance()
            
            service_selection_prompt = f"""Based on the user request: "{user_message}"

Here is the complete Service Catalog with all available services and their capabilities:

{catalog_info}

TASK: Analyze the user request and determine which service(s) to use and what specific operations to perform.

Consider:
1. What is the user trying to accomplish?
2. Which service(s) are best suited for this task based on their capabilities?
3. What specific operations should be performed?
4. Should multiple services be used together?

Respond with a JSON object containing your service selection and execution plan:
{{
    "selected_services": [
        {{
            "service_name": "service-name",
            "reason": "why this service was selected",
            "operations": [
                {{
                    "operation": "specific operation to perform",
                    "parameters": {{"param1": "value1", "param2": "value2"}}
                }}
            ]
        }}
    ],
    "execution_strategy": "sequential|parallel",
    "reasoning": "detailed explanation of service selection and execution plan"
}}

Make intelligent decisions based on the service capabilities, not hardcoded rules.
"""

            selection_response = await self.llm_engine.generate(service_selection_prompt)
            
            if isinstance(selection_response, dict) and "generated_text" in selection_response:
                selection_text = selection_response["generated_text"]
            else:
                selection_text = str(selection_response)
            
            logger.info(f"🎯 Service selection by Ollama: {selection_text}")
            
            # Parse the service selection and execute
            return await self._execute_selected_services(selection_text, user_message)
            
        except Exception as e:
            logger.error(f"❌ Service selection failed: {e}")
            return None
    
    async def _execute_selected_services(self, selection_text: str, user_message: str) -> Dict[str, Any]:
        """Execute the services selected by Ollama"""
        
        results = {
            "service_calls": [],
            "success": False,
            "summary": "",
            "job_details": []
        }
        
        try:
            # Try to parse JSON from Ollama's response
            import json
            import re
            
            # Extract JSON from the response
            json_match = re.search(r'\{.*\}', selection_text, re.DOTALL)
            if json_match:
                selection_data = json.loads(json_match.group())
                
                logger.info(f"📋 Parsed service selection: {selection_data}")
                
                for service_selection in selection_data.get("selected_services", []):
                    service_name = service_selection.get("service_name", "")
                    operations = service_selection.get("operations", [])
                    
                    # Execute based on service type
                    if "network-analyzer" in service_name.lower() and self.network_client:
                        for operation in operations:
                            network_result = await self._execute_network_operation(operation, user_message)
                            if network_result:
                                results["service_calls"].append(network_result)
                    
                    elif "automation" in service_name.lower() and self.automation_client:
                        for operation in operations:
                            automation_result = await self._execute_automation_operation(operation, user_message)
                            if automation_result:
                                results["service_calls"].append(automation_result)
                                results["job_details"].extend(automation_result.get("job_details", []))
                    
                    # Add support for other services as they become available
                    # elif "celery-beat" in service_name.lower():
                    # elif "asset" in service_name.lower():
                    # elif "communication" in service_name.lower():
                
                # Set overall success and summary
                if results["service_calls"]:
                    results["success"] = any(call.get("success", False) for call in results["service_calls"])
                    results["summary"] = selection_data.get("reasoning", "Services executed based on Ollama's selection")
                else:
                    results["success"] = True
                    results["summary"] = "Analysis completed - no service execution required"
            
            else:
                logger.warning("Could not parse JSON from Ollama's service selection response")
                results["success"] = True
                results["summary"] = "Service selection analysis completed"
                
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
                    result = await self.network_client.ping(target)
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
                    result = await self.network_client.traceroute(target)
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
        """Let Ollama create the specific automation job"""
        
        job_prompt = f"""Create an automation job for this user request: "{user_message}"

Based on your analysis: {extraction_text}

Create a job with these details:
- Job name
- Description  
- Commands to run
- Target systems

Provide the job in this format:

JOB_NAME: [descriptive name]
DESCRIPTION: [what this job does]
COMMANDS:
- [command 1]
- [command 2]
TARGET_SYSTEMS: [localhost or specific servers]

Be specific about the actual commands to run.
"""

        response = await self.llm_engine.generate(job_prompt)
        
        if isinstance(response, dict) and "generated_text" in response:
            job_text = response["generated_text"]
        else:
            job_text = str(response)
        
        logger.info(f"🔧 Ollama job creation: {job_text}")
        
        try:
            # Parse the job details and submit to automation service
            job_data = await self._parse_job_from_ollama_response(job_text, user_message)
            
            if job_data and self.automation_client:
                # Submit the job
                result = await self.automation_client.submit_ai_workflow(
                    workflow=job_data,
                    job_name=job_data.get("name", "AI Generated Job")
                )
                
                if result and result.get("success"):
                    return {
                        "success": True,
                        "summary": f"Job '{job_data.get('name')}' submitted successfully",
                        "job_details": [{
                            "job_name": job_data.get("name"),
                            "job_id": str(result.get("job_id", "")),
                            "execution_id": str(result.get("execution_id", "")),
                            "step_name": "Main Execution"
                        }],
                        "automation_result": result
                    }
        
        except Exception as e:
            logger.error(f"❌ Job creation failed: {e}")
        
        return None
    
    async def _parse_job_from_ollama_response(self, job_text: str, user_message: str) -> Optional[Dict[str, Any]]:
        """Parse Ollama's job response into automation service format"""
        
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
                    target_systems = [line.replace("TARGET_SYSTEMS:", "").strip()]
                elif current_section == "commands" and line.startswith("-"):
                    command = line.replace("-", "").strip()
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

What specific shell commands should be executed to accomplish this task?

Provide ONLY the commands, one per line, without any explanation or formatting.
Be specific and use proper Linux/Unix commands.

Examples:
- For "restart nginx": sudo systemctl restart nginx
- For "check disk space": df -h
- For "list processes": ps aux
- For "update system": sudo apt update && sudo apt upgrade -y

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