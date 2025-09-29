"""
AI Brain Service - CLEAN ARCHITECTURE
Main orchestration service for AI-driven workflow management.
Simplified connections: AI Brain -> Prefect -> Services
"""

import asyncio
import logging
import json
import httpx
from typing import Dict, Any, Optional, List
from datetime import datetime
import os

logger = logging.getLogger(__name__)

class CleanAIBrainService:
    """
    Clean AI Brain Service - Simplified Architecture
    
    Responsibilities:
    - AI-powered decision making (via Ollama LLM)
    - Workflow orchestration coordination (via Prefect)
    - High-level intent processing
    - Cross-service workflow generation
    
    NOT Responsible For:
    - Direct service connections (Prefect handles this)
    - Background job management (Prefect handles this)
    - Task execution (Services handle this)
    
    Architecture Flow:
    User Request -> AI Brain (Decision) -> Prefect (Orchestration) -> Services (Execution)
    """
    
    def __init__(self):
        """Initialize the Clean AI Brain service with simplified components."""
        self.ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.prefect_url = os.getenv("PREFECT_API_URL", "http://localhost:4200/api")
        
        # Service registry for Prefect flow generation
        self.service_registry = {
            "automation": {
                "url": os.getenv("AUTOMATION_SERVICE_URL", "http://localhost:8001"),
                "capabilities": ["command_execution", "script_running", "system_management"]
            },
            "asset": {
                "url": os.getenv("ASSET_SERVICE_URL", "http://localhost:8002"),
                "capabilities": ["asset_discovery", "inventory_management", "asset_tracking"]
            },
            "network": {
                "url": os.getenv("NETWORK_SERVICE_URL", "http://localhost:8003"),
                "capabilities": ["network_analysis", "connectivity_testing", "monitoring"]
            },
            "communication": {
                "url": os.getenv("COMMUNICATION_SERVICE_URL", "http://localhost:8004"),
                "capabilities": ["notifications", "alerts", "messaging"]
            }
        }
        
        logger.info("Clean AI Brain Service initialized")
    
    async def process_intent(self, intent: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process user intent and coordinate execution via Prefect.
        
        Args:
            intent: User's natural language intent
            context: Additional context for processing
            
        Returns:
            Execution result with status and details
        """
        try:
            logger.info(f"Processing intent: {intent}")
            
            # Step 1: Generate execution plan using Ollama LLM
            plan = await self.generate_execution_plan(intent, context or {})
            
            # Step 2: Create and submit Prefect flow
            flow_id = await self.create_prefect_flow(plan)
            
            # Step 3: Monitor execution (simplified)
            result = await self.monitor_execution(flow_id)
            
            return {
                "status": "success",
                "intent": intent,
                "plan": plan,
                "flow_id": flow_id,
                "result": result,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing intent: {e}")
            return {
                "status": "error",
                "intent": intent,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def generate_execution_plan(self, intent: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate execution plan using Ollama LLM.
        
        Args:
            intent: User's intent
            context: Execution context
            
        Returns:
            Structured execution plan
        """
        try:
            # Create prompt for LLM
            prompt = self._create_planning_prompt(intent, context)
            
            # Call Ollama LLM
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": "llama3.2:3b",
                        "prompt": prompt,
                        "stream": False,
                        "format": "json"
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    plan_text = result.get("response", "{}")
                    
                    try:
                        plan = json.loads(plan_text)
                        return self._validate_and_enhance_plan(plan)
                    except json.JSONDecodeError:
                        # Fallback to simple plan
                        return self._create_fallback_plan(intent, context)
                else:
                    logger.error(f"Ollama API error: {response.status_code}")
                    return self._create_fallback_plan(intent, context)
                    
        except Exception as e:
            logger.error(f"Error generating plan: {e}")
            return self._create_fallback_plan(intent, context)
    
    def _create_planning_prompt(self, intent: str, context: Dict[str, Any]) -> str:
        """Create structured prompt for execution planning."""
        services_info = json.dumps(self.service_registry, indent=2)
        
        return f"""
You are an AI operations conductor. Analyze the user intent and create an execution plan.

User Intent: {intent}
Context: {json.dumps(context, indent=2)}

Available Services:
{services_info}

Create a JSON execution plan with this structure:
{{
    "intent_analysis": "Brief analysis of what the user wants",
    "required_services": ["list", "of", "services", "needed"],
    "execution_steps": [
        {{
            "step": 1,
            "service": "service_name",
            "action": "specific_action",
            "parameters": {{"key": "value"}},
            "description": "What this step does"
        }}
    ],
    "expected_outcome": "What the user should expect"
}}

Respond with ONLY the JSON, no additional text.
"""
    
    def _validate_and_enhance_plan(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and enhance the generated plan."""
        # Ensure required fields exist
        if "execution_steps" not in plan:
            plan["execution_steps"] = []
        
        if "required_services" not in plan:
            plan["required_services"] = []
        
        # Add metadata
        plan["plan_id"] = f"plan_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        plan["created_at"] = datetime.utcnow().isoformat()
        
        return plan
    
    def _create_fallback_plan(self, intent: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Create a simple fallback plan when LLM fails."""
        return {
            "plan_id": f"fallback_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            "intent_analysis": f"Simple execution of: {intent}",
            "required_services": ["automation"],
            "execution_steps": [
                {
                    "step": 1,
                    "service": "automation",
                    "action": "execute_command",
                    "parameters": {"command": intent},
                    "description": "Execute the requested operation"
                }
            ],
            "expected_outcome": "Command execution result",
            "created_at": datetime.utcnow().isoformat()
        }
    
    async def create_prefect_flow(self, plan: Dict[str, Any]) -> str:
        """
        Create and submit Prefect flow for execution.
        
        Args:
            plan: Execution plan from LLM
            
        Returns:
            Flow run ID
        """
        try:
            # For now, return a mock flow ID
            # In full implementation, this would create actual Prefect flows
            flow_id = f"flow_{plan.get('plan_id', 'unknown')}"
            
            logger.info(f"Created Prefect flow: {flow_id}")
            return flow_id
            
        except Exception as e:
            logger.error(f"Error creating Prefect flow: {e}")
            raise
    
    async def monitor_execution(self, flow_id: str) -> Dict[str, Any]:
        """
        Monitor Prefect flow execution.
        
        Args:
            flow_id: Prefect flow run ID
            
        Returns:
            Execution result
        """
        try:
            # For now, return a mock result
            # In full implementation, this would monitor actual Prefect flows
            return {
                "flow_id": flow_id,
                "status": "completed",
                "result": "Execution completed successfully",
                "completed_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error monitoring execution: {e}")
            return {
                "flow_id": flow_id,
                "status": "error",
                "error": str(e),
                "completed_at": datetime.utcnow().isoformat()
            }
    
    async def get_architecture_status(self) -> Dict[str, Any]:
        """Get clean architecture status."""
        return {
            "architecture": "clean",
            "version": "1.0.0",
            "components": {
                "ai_brain": {
                    "status": "active",
                    "responsibilities": [
                        "AI decision making",
                        "Orchestration coordination",
                        "Intent processing"
                    ]
                },
                "prefect": {
                    "status": "active",
                    "responsibilities": [
                        "Workflow orchestration",
                        "Task coordination",
                        "Execution monitoring"
                    ]
                },
                "services": {
                    "status": "active",
                    "responsibilities": [
                        "Specialized execution",
                        "Direct operations",
                        "Result reporting"
                    ]
                }
            },
            "flow": "User → AI Brain → Prefect → Services",
            "eliminated": [
                "Celery workers",
                "Direct service connections",
                "Background processing duplication",
                "Multiple orchestration systems"
            ]
        }
    
    async def get_services_status(self) -> Dict[str, Any]:
        """Get status of all registered services."""
        services_status = {}
        
        async with httpx.AsyncClient() as client:
            for service_name, service_info in self.service_registry.items():
                try:
                    response = await client.get(
                        f"{service_info['url']}/health",
                        timeout=5.0
                    )
                    services_status[service_name] = {
                        "status": "healthy" if response.status_code == 200 else "unhealthy",
                        "url": service_info["url"],
                        "capabilities": service_info["capabilities"]
                    }
                except Exception as e:
                    services_status[service_name] = {
                        "status": "unreachable",
                        "url": service_info["url"],
                        "error": str(e),
                        "capabilities": service_info["capabilities"]
                    }
        
        return services_status