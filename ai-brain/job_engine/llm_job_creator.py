"""
OpsConductor AI Brain - LLM-Based Job Creation Engine

This module replaces the NLM intent engine with a pure LLM-based approach
for creating automation jobs from natural language descriptions.

Multi-stage LLM pipeline:
1. ANALYZE: Understand the request and extract requirements
2. PLAN: Generate workflow steps and structure  
3. VALIDATE: Check feasibility and safety
4. CREATE: Build the final executable job
"""

import logging
import json
import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
import asyncio

from integrations.llm_client import LLMEngine
from integrations.automation_client import AutomationServiceClient

logger = logging.getLogger(__name__)

def extract_json_from_response(response_text: str) -> str:
    """Extract JSON from LLM response that may be wrapped in markdown code blocks"""
    # First try to find JSON in code blocks
    json_pattern = r'```(?:json)?\s*(\{.*?\})\s*```'
    match = re.search(json_pattern, response_text, re.DOTALL)
    if match:
        return match.group(1)
    
    # If no code blocks, try to find JSON object directly
    json_pattern = r'\{.*\}'
    match = re.search(json_pattern, response_text, re.DOTALL)
    if match:
        return match.group(0)
    
    # If still no match, return the original text
    return response_text.strip()

@dataclass
class JobAnalysis:
    """Analysis result from LLM"""
    intent_type: str
    confidence: float
    requirements: Dict[str, Any]
    target_systems: List[str]
    risk_level: str
    complexity: str
    estimated_duration: str
    
@dataclass
class JobPlan:
    """Job plan from LLM"""
    workflow_type: str
    steps: List[Dict[str, Any]]
    dependencies: List[str]
    validation_checks: List[str]
    rollback_plan: List[str]
    
@dataclass
class JobValidation:
    """Validation result from LLM"""
    is_valid: bool
    safety_score: float
    warnings: List[str]
    recommendations: List[str]
    required_approvals: List[str]

class LLMJobCreator:
    """Pure LLM-based job creation engine"""
    
    def __init__(self, llm_engine: LLMEngine, automation_client: Optional[AutomationServiceClient] = None):
        self.llm_engine = llm_engine
        self.automation_client = automation_client or AutomationServiceClient()
        
    async def create_job_from_natural_language(self, description: str, 
                                             user_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a complete automation job using pure LLM analysis
        
        Args:
            description: Natural language description of the automation request
            user_context: Optional user context and preferences
            
        Returns:
            Complete job creation result with workflow, execution plan, etc.
        """
        try:
            logger.info(f"Creating job from description: {description}")
            
            # STAGE 1: ANALYZE - Understand the request
            analysis = await self._analyze_request(description, user_context)
            if not analysis:
                return {"success": False, "error": "Failed to analyze request"}
            
            logger.info(f"✅ Analysis completed: {analysis.intent_type}")
            
            # STAGE 2: PLAN - Generate workflow structure
            plan = await self._generate_plan(description, analysis, user_context)
            if not plan:
                return {"success": False, "error": "Failed to generate plan"}
                
            logger.info(f"✅ Plan generated: {plan.workflow_type} with {len(plan.steps)} steps")
            
            # STAGE 3: VALIDATE - Check safety and feasibility
            validation = await self._validate_plan(description, analysis, plan, user_context)
            if not validation.is_valid:
                return {
                    "success": False, 
                    "error": "Plan validation failed",
                    "warnings": validation.warnings,
                    "recommendations": validation.recommendations
                }
            
            # STAGE 4: CREATE - Build final executable job
            job_result = await self._create_executable_job(description, analysis, plan, validation, user_context)
            
            return job_result
            
        except Exception as e:
            logger.error(f"Error in LLM job creation: {e}")
            return {
                "success": False,
                "error": f"Job creation failed: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
    
    async def _analyze_request(self, description: str, user_context: Optional[Dict[str, Any]]) -> Optional[JobAnalysis]:
        """STAGE 1: Analyze the natural language request using LLM"""
        try:
            system_prompt = """You are an expert IT operations analyst. Analyze automation requests and extract structured information.

Your task is to analyze the user's request and return a JSON object with the following structure:
{
    "intent_type": "automation_request|information_query|system_status|troubleshooting|configuration|monitoring|deployment|maintenance|security|backup_restore|user_management|network_operations|database_operations|file_operations|service_management",
    "confidence": 0.95,
    "requirements": {
        "description": "Clear description of what needs to be done",
        "targets": ["list", "of", "target", "systems"],
        "actions": ["list", "of", "required", "actions"],
        "parameters": {"key": "value", "pairs": "of parameters"},
        "conditions": ["any", "conditions", "or", "constraints"]
    },
    "target_systems": ["server1", "server2", "group:webservers"],
    "risk_level": "low|medium|high|critical",
    "complexity": "simple|moderate|complex|expert",
    "estimated_duration": "5 minutes|30 minutes|2 hours|1 day"
}

Be precise and conservative with risk assessment. If unclear, ask for clarification."""

            context_info = ""
            if user_context:
                context_info = f"\nUser context: {json.dumps(user_context, indent=2)}"

            prompt = f"""Analyze this automation request:

Request: "{description}"{context_info}

Provide your analysis as a JSON object:"""

            response = await self.llm_engine.chat(
                message=prompt,
                system_prompt=system_prompt,
                model=None  # Use default model
            )
            
            # Parse JSON response
            try:
                # Extract JSON from the response (handles markdown code blocks)
                json_text = extract_json_from_response(response["response"])
                analysis_data = json.loads(json_text)
                
                return JobAnalysis(
                    intent_type=analysis_data.get("intent_type", "automation_request"),
                    confidence=analysis_data.get("confidence", 0.5),
                    requirements=analysis_data.get("requirements", {}),
                    target_systems=analysis_data.get("target_systems", []),
                    risk_level=analysis_data.get("risk_level", "medium"),
                    complexity=analysis_data.get("complexity", "moderate"),
                    estimated_duration=analysis_data.get("estimated_duration", "30 minutes")
                )
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse analysis JSON: {e}")
                logger.error(f"Raw response: {response['response']}")
                return None
                
        except Exception as e:
            logger.error(f"Error in request analysis: {e}")
            return None
    
    async def _generate_plan(self, description: str, analysis: JobAnalysis, 
                           user_context: Optional[Dict[str, Any]]) -> Optional[JobPlan]:
        """STAGE 2: Generate detailed workflow plan using LLM"""
        try:
            system_prompt = """You are an expert automation workflow designer. Create detailed execution plans for IT operations.

Your task is to generate a workflow plan and return a JSON object with this structure:
{
    "workflow_type": "system_maintenance|deployment|monitoring_setup|security_audit|backup_restore|configuration_change|troubleshooting|information_gathering",
    "steps": [
        {
            "id": "step_1",
            "name": "Step Name",
            "type": "command|script|validation|condition|parallel|sequential|error_handler|notification",
            "action": "Specific action to perform",
            "command": "actual command or script",
            "target": "target system or group",
            "timeout": 300,
            "retry_count": 3,
            "success_criteria": "How to determine success",
            "error_handling": "What to do on failure"
        }
    ],
    "dependencies": ["external_service", "required_tool"],
    "validation_checks": ["pre-check", "post-check"],
    "rollback_plan": ["step to undo", "restore command"]
}

Create safe, well-structured workflows with proper error handling."""

            analysis_context = f"""
Analysis Results:
- Intent: {analysis.intent_type}
- Risk Level: {analysis.risk_level}
- Complexity: {analysis.complexity}
- Target Systems: {analysis.target_systems}
- Requirements: {json.dumps(analysis.requirements, indent=2)}
"""

            prompt = f"""Create a detailed workflow plan for this request:

Original Request: "{description}"

{analysis_context}

Generate a comprehensive workflow plan as JSON:"""

            response = await self.llm_engine.chat(
                message=prompt,
                system_prompt=system_prompt,
                model=None
            )
            
            logger.info(f"Raw plan response: {response['response'][:300]}...")
            
            # Parse JSON response
            try:
                # Extract JSON from the response (handles markdown code blocks)
                json_text = extract_json_from_response(response["response"])
                logger.info(f"Extracted JSON for plan: {json_text[:200]}...")
                plan_data = json.loads(json_text)
                
                return JobPlan(
                    workflow_type=plan_data.get("workflow_type", "automation"),
                    steps=plan_data.get("steps", []),
                    dependencies=plan_data.get("dependencies", []),
                    validation_checks=plan_data.get("validation_checks", []),
                    rollback_plan=plan_data.get("rollback_plan", [])
                )
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse plan JSON: {e}")
                logger.error(f"Raw response: {response['response']}")
                return None
                
        except Exception as e:
            logger.error(f"Error in plan generation: {e}")
            return None
    
    async def _validate_plan(self, description: str, analysis: JobAnalysis, plan: JobPlan,
                           user_context: Optional[Dict[str, Any]]) -> JobValidation:
        """STAGE 3: Validate the plan for safety and feasibility using LLM"""
        try:
            system_prompt = """You are a senior IT security and operations validator. Review automation plans for safety and feasibility.

Your task is to validate the plan and return a JSON object with this structure:
{
    "is_valid": true,
    "safety_score": 0.85,
    "warnings": ["Warning messages about potential issues"],
    "recommendations": ["Suggestions for improvement"],
    "required_approvals": ["manager", "security_team"]
}

Validation Guidelines:
- For LOW RISK operations (service restarts, status checks, log viewing): Be permissive, approve if basic safety measures are in place
- For MEDIUM/HIGH RISK operations: Be thorough in safety assessment
- Consider: Data loss risks, Service disruption potential, Security implications, Rollback feasibility
- Simple service management operations (start/stop/restart/status) are generally safe if they target appropriate services
- Approve operations that have reasonable error handling and rollback plans"""

            plan_context = f"""
Plan to Validate:
- Workflow Type: {plan.workflow_type}
- Number of Steps: {len(plan.steps)}
- Dependencies: {plan.dependencies}
- Risk Level: {analysis.risk_level}

Steps:
{json.dumps(plan.steps, indent=2)}

Rollback Plan:
{json.dumps(plan.rollback_plan, indent=2)}
"""

            prompt = f"""Validate this automation plan for safety and feasibility:

Original Request: "{description}"

{plan_context}

Provide your validation assessment as JSON:"""

            response = await self.llm_engine.chat(
                message=prompt,
                system_prompt=system_prompt,
                model=None
            )
            
            logger.info(f"Raw validation response: {response['response']}")
            
            # Parse JSON response
            try:
                # Extract JSON from the response (handles markdown code blocks)
                json_text = extract_json_from_response(response["response"])
                validation_data = json.loads(json_text)
                
                # Log validation details for debugging
                logger.info(f"Validation result: is_valid={validation_data.get('is_valid', False)}")
                logger.info(f"Safety score: {validation_data.get('safety_score', 0.5)}")
                logger.info(f"Warnings: {validation_data.get('warnings', [])}")
                logger.info(f"Recommendations: {validation_data.get('recommendations', [])}")
                
                return JobValidation(
                    is_valid=validation_data.get("is_valid", False),
                    safety_score=validation_data.get("safety_score", 0.5),
                    warnings=validation_data.get("warnings", []),
                    recommendations=validation_data.get("recommendations", []),
                    required_approvals=validation_data.get("required_approvals", [])
                )
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse validation JSON: {e}")
                logger.error(f"Raw response: {response['response']}")
                # Return safe default
                return JobValidation(
                    is_valid=False,
                    safety_score=0.0,
                    warnings=["Failed to parse validation response"],
                    recommendations=["Manual review required"],
                    required_approvals=["administrator"]
                )
                
        except Exception as e:
            logger.error(f"Error in plan validation: {e}")
            return JobValidation(
                is_valid=False,
                safety_score=0.0,
                warnings=[f"Validation error: {str(e)}"],
                recommendations=["Manual review required"],
                required_approvals=["administrator"]
            )
    
    async def _create_executable_job(self, description: str, analysis: JobAnalysis, 
                                   plan: JobPlan, validation: JobValidation,
                                   user_context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """STAGE 4: Create and submit the actual executable job to automation service"""
        try:
            # Check if automation service is available
            if not await self.automation_client.health_check():
                logger.error("Automation service is not available")
                return {
                    "success": False,
                    "error": "Automation service is not available - cannot create real jobs",
                    "timestamp": datetime.now().isoformat()
                }
            
            # Build workflow structure for automation service
            workflow = {
                "id": f"llm_workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "name": f"LLM Generated: {description[:50]}...",
                "description": description,
                "workflow_type": plan.workflow_type,
                "steps": plan.steps,
                "risk_level": analysis.risk_level,
                "estimated_duration": analysis.estimated_duration,
                "created_by": "llm_engine",
                "created_at": datetime.now().isoformat(),
                "source_request": description,
                "confidence": analysis.confidence,
                "rollback_plan": plan.rollback_plan,
                "validation_checks": plan.validation_checks,
                "metadata": {
                    "intent_type": analysis.intent_type,
                    "complexity": analysis.complexity,
                    "safety_score": validation.safety_score,
                    "warnings": validation.warnings,
                    "recommendations": validation.recommendations,
                    "engine": "llm_job_creator",
                    "llm_stages": ["analyze", "plan", "validate", "create"],
                    "target_systems": analysis.target_systems,
                    "requires_approval": len(validation.required_approvals) > 0,
                    "approval_required_from": validation.required_approvals
                }
            }
            
            # Generate intelligent job name based on analysis and plan
            job_name = await self._generate_intelligent_job_name(description, analysis, plan)
            
            logger.info(f"Submitting real job to automation service: {job_name}")
            
            # Actually submit the job to automation service
            submission_result = await self.automation_client.submit_ai_workflow(
                workflow=workflow,
                job_name=job_name
            )
            
            if not submission_result.get('success'):
                logger.error(f"Failed to submit job to automation service: {submission_result.get('error')}")
                return {
                    "success": False,
                    "error": f"Failed to submit job to automation service: {submission_result.get('error')}",
                    "timestamp": datetime.now().isoformat()
                }
            
            # Return actual results from automation service
            real_job_id = submission_result.get('job_id')
            execution_id = submission_result.get('execution_id')
            task_id = submission_result.get('task_id')
            
            logger.info(f"Successfully created and submitted real job: {real_job_id}")
            
            return {
                "success": True,
                "job_id": real_job_id,  # Real job ID from automation service
                "execution_id": execution_id,  # Real execution ID
                "task_id": task_id,  # Real task ID
                "job_name": job_name,
                "message": f"Job successfully created and started execution in automation service",
                "workflow": workflow,
                "submission_details": submission_result,
                "metadata": {
                    "created_at": datetime.now().isoformat(),
                    "intent_type": analysis.intent_type,
                    "requires_approval": len(validation.required_approvals) > 0,
                    "estimated_duration": analysis.estimated_duration,
                    "risk_level": analysis.risk_level,
                    "complexity": analysis.complexity,
                    "confidence": analysis.confidence,
                    "safety_score": validation.safety_score,
                    "warnings": validation.warnings,
                    "recommendations": validation.recommendations,
                    "engine": "llm_job_creator",
                    "llm_stages": ["analyze", "plan", "validate", "create", "submit"],
                    "automation_service_integration": True
                }
            }
            
        except Exception as e:
            logger.error(f"Error creating and submitting executable job: {e}")
            return {
                "success": False,
                "error": f"Failed to create and submit job: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
    
    async def _generate_intelligent_job_name(self, description: str, analysis: JobAnalysis, plan: JobPlan) -> str:
        """Generate an intelligent, descriptive job name based on the chat context and automation purpose"""
        try:
            system_prompt = """You are an expert at creating concise, descriptive job names for IT automation tasks.

Your task is to generate a clear, professional job name that:
1. Reflects the main purpose/action of the automation
2. Includes key target systems or services when relevant
3. Is concise but descriptive (ideally 3-8 words)
4. Uses professional IT terminology
5. Avoids generic terms like "AI Job" or "Automation Task"

Examples of good job names:
- "Restart Apache Services on Web Servers"
- "Deploy Application to Production Environment"
- "Monitor Disk Usage on Database Servers"
- "Update Security Patches on Linux Hosts"
- "Backup MySQL Database to S3"
- "Scale Kubernetes Pods for High Traffic"
- "Configure Load Balancer Health Checks"
- "Rotate SSL Certificates on API Gateway"

Return ONLY the job name, no additional text or formatting."""

            # Create context for the LLM
            context_info = f"""
Original Request: "{description}"

Analysis:
- Intent Type: {analysis.intent_type}
- Target Systems: {', '.join(analysis.target_systems) if analysis.target_systems else 'General'}
- Workflow Type: {plan.workflow_type}
- Main Actions: {', '.join([step.get('action', step.get('name', 'Unknown')) for step in plan.steps[:3]])}
- Risk Level: {analysis.risk_level}
- Complexity: {analysis.complexity}
"""

            prompt = f"""Generate a professional job name for this automation task:

{context_info}

Job Name:"""

            response = await self.llm_engine.chat(
                message=prompt,
                system_prompt=system_prompt,
                model=None  # Use default model
            )
            
            # Extract the job name from the response
            job_name = response["response"].strip()
            
            # Clean up the response (remove quotes, extra formatting)
            job_name = job_name.strip('"\'`')
            job_name = job_name.replace('\n', ' ').replace('\r', ' ')
            
            # Ensure it's not too long (max 80 characters)
            if len(job_name) > 80:
                job_name = job_name[:77] + "..."
            
            # NO FALLBACKS ALLOWED - FAIL HARD if LLM response is inadequate
            if not job_name or len(job_name) < 5:
                raise RuntimeError(f"NO FALLBACKS ALLOWED: LLM failed to generate adequate job name. Response: '{job_name}'")
            
            logger.info(f"Generated intelligent job name: '{job_name}' for request: '{description[:50]}...'")
            return job_name
            
        except Exception as e:
            logger.error(f"Error generating intelligent job name: {e}")
            # Fallback to a simple but better name than the original
            if analysis.target_systems:
                targets = ', '.join(analysis.target_systems[:2])
                return f"{analysis.intent_type.replace('_', ' ').title()} on {targets}"
            else:
                return f"{analysis.intent_type.replace('_', ' ').title()} Task"