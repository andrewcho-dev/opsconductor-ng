"""
Response Formatter
Formats technical information into user-friendly responses

This component handles the conversion of technical execution plans and pipeline
results into clear, actionable messages for end users.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from llm.ollama_client import OllamaClient
from llm.client import LLMRequest
from pipeline.schemas.decision_v1 import DecisionV1
from pipeline.schemas.selection_v1 import SelectionV1
from pipeline.schemas.plan_v1 import PlanV1
from pipeline.schemas.response_v1 import ApprovalPoint, ClarificationRequest

logger = logging.getLogger(__name__)

class ResponseFormatter:
    """
    Response Formatter for Stage D
    
    Converts technical pipeline results into user-friendly messages
    using LLM-powered natural language generation.
    """
    
    def __init__(self, llm_client: OllamaClient):
        """Initialize response formatter with LLM client"""
        self.llm_client = llm_client
        logger.info("Response Formatter initialized")
    
    async def format_information_response(
        self,
        decision: DecisionV1,
        plan: PlanV1,
        analysis: Dict[str, Any]
    ) -> str:
        """Format response for information-only requests"""
        
        try:
            # Create context for LLM
            context = {
                "intent": f"{decision.intent.category}/{decision.intent.action}",
                "confidence": decision.overall_confidence,
                "steps_planned": len(plan.plan.steps),
                "tools_involved": list(set(step.tool for step in plan.plan.steps)),
                "safety_checks": len(plan.plan.safety_checks),
                "analysis_results": analysis
            }
            
            # Generate user-friendly response using LLM
            prompt = self._create_information_response_prompt(context)
            llm_request = LLMRequest(prompt=prompt)
            llm_response = await self.llm_client.generate(llm_request)
            response = llm_response.content
            
            return response.strip()
            
        except Exception as e:
            logger.error(f"Failed to format information response: {e}")
            return self._create_fallback_information_response(decision, plan)
    
    async def format_plan_summary(
        self,
        decision: DecisionV1,
        selection: SelectionV1,
        plan: PlanV1
    ) -> str:
        """Format execution plan summary for users"""
        
        try:
            # Create context for LLM
            context = {
                "intent": f"{decision.intent.category}/{decision.intent.action}",
                "confidence": decision.overall_confidence,
                "total_steps": len(plan.plan.steps),
                "estimated_time": plan.execution_metadata.total_estimated_time,
                "tools": list(set(step.tool for step in plan.plan.steps)),
                "safety_checks": len(plan.plan.safety_checks),
                "risk_level": selection.policy.risk_level.value,
                "requires_approval": selection.policy.requires_approval,
                "step_descriptions": [step.description for step in plan.plan.steps[:3]]  # First 3 steps
            }
            
            # Generate user-friendly plan summary using LLM
            prompt = self._create_plan_summary_prompt(context)
            llm_request = LLMRequest(prompt=prompt)
            llm_response = await self.llm_client.generate(llm_request)
            response = llm_response.content
            
            return response.strip()
            
        except Exception as e:
            logger.error(f"Failed to format plan summary: {e}")
            return self._create_fallback_plan_summary(decision, plan)
    
    async def format_approval_request(
        self,
        decision: DecisionV1,
        plan: PlanV1,
        approval_points: List[ApprovalPoint]
    ) -> str:
        """Format approval request message"""
        
        try:
            # Create context for LLM
            context = {
                "intent": f"{decision.intent.category}/{decision.intent.action}",
                "total_steps": len(plan.plan.steps),
                "estimated_time": plan.execution_metadata.total_estimated_time,
                "approval_count": len(approval_points),
                "high_risk_steps": [ap.step_id for ap in approval_points if ap.risk_level in ["high", "critical"]],
                "approval_reasons": [ap.reason for ap in approval_points],
                "required_roles": list(set(ap.approver_role for ap in approval_points))
            }
            
            # Generate approval request using LLM
            prompt = self._create_approval_request_prompt(context)
            llm_request = LLMRequest(prompt=prompt)
            llm_response = await self.llm_client.generate(llm_request)
            response = llm_response.content
            
            return response.strip()
            
        except Exception as e:
            logger.error(f"Failed to format approval request: {e}")
            return self._create_fallback_approval_request(decision, plan, approval_points)
    
    async def format_execution_ready(
        self,
        decision: DecisionV1,
        plan: PlanV1
    ) -> str:
        """Format message for execution-ready plans"""
        
        try:
            # Create context for LLM
            context = {
                "intent": f"{decision.intent.category}/{decision.intent.action}",
                "total_steps": len(plan.plan.steps),
                "estimated_time": plan.execution_metadata.total_estimated_time,
                "tools": list(set(step.tool for step in plan.plan.steps)),
                "safety_checks": len(plan.plan.safety_checks),
                "key_steps": [step.description for step in plan.plan.steps[:2]]  # First 2 steps
            }
            
            # Generate execution ready message using LLM
            prompt = self._create_execution_ready_prompt(context)
            llm_request = LLMRequest(prompt=prompt)
            llm_response = await self.llm_client.generate(llm_request)
            response = llm_response.content
            
            return response.strip()
            
        except Exception as e:
            logger.error(f"Failed to format execution ready message: {e}")
            return self._create_fallback_execution_ready(decision, plan)
    
    async def format_clarification_message(
        self,
        decision: DecisionV1,
        clarifications: List[ClarificationRequest]
    ) -> str:
        """Format clarification request message"""
        
        try:
            # Create context for LLM
            context = {
                "intent": f"{decision.intent.category}/{decision.intent.action}",
                "confidence": decision.overall_confidence,
                "clarification_count": len(clarifications),
                "questions": [c.question for c in clarifications],
                "required_count": sum(1 for c in clarifications if c.required)
            }
            
            # Generate clarification message using LLM
            prompt = self._create_clarification_prompt(context)
            llm_request = LLMRequest(prompt=prompt)
            llm_response = await self.llm_client.generate(llm_request)
            response = llm_response.content
            
            return response.strip()
            
        except Exception as e:
            logger.error(f"Failed to format clarification message: {e}")
            return self._create_fallback_clarification_message(clarifications)
    
    def _create_information_response_prompt(self, context: Dict[str, Any]) -> str:
        """Create prompt for information response generation"""
        
        return f"""You are generating a user-friendly response for an information request in OpsConductor.

Request Details:
- Intent: {context['intent']}
- Confidence: {context['confidence']:.2f}
- Steps planned: {context['steps_planned']}
- Tools involved: {', '.join(context['tools_involved'])}
- Safety checks: {context['safety_checks']}

Create a clear, professional response that:
1. Acknowledges the user's information request
2. Summarizes what information will be gathered
3. Mentions the tools and steps involved
4. Provides an estimated timeframe
5. Uses friendly, non-technical language

Keep the response concise (2-3 sentences) and helpful."""
    
    def _create_plan_summary_prompt(self, context: Dict[str, Any]) -> str:
        """Create prompt for plan summary generation"""
        
        return f"""You are generating a user-friendly plan summary for OpsConductor.

Plan Details:
- Intent: {context['intent']}
- Total steps: {context['total_steps']}
- Estimated time: {context['estimated_time']} seconds
- Tools: {', '.join(context['tools'])}
- Safety checks: {context['safety_checks']}
- Risk level: {context['risk_level']}
- Requires approval: {context['requires_approval']}

Key steps include:
{chr(10).join(f"- {step}" for step in context['step_descriptions'])}

Create a clear, professional summary that:
1. Confirms understanding of the request
2. Summarizes the plan in simple terms
3. Mentions key safety measures
4. Indicates the estimated time
5. Uses reassuring, confident language

Keep the response informative but accessible (3-4 sentences)."""
    
    def _create_approval_request_prompt(self, context: Dict[str, Any]) -> str:
        """Create prompt for approval request generation"""
        
        return f"""You are generating an approval request message for OpsConductor.

Request Details:
- Intent: {context['intent']}
- Total steps: {context['total_steps']}
- Estimated time: {context['estimated_time']} seconds
- Approval points: {context['approval_count']}
- Required roles: {', '.join(context['required_roles'])}

Approval reasons:
{chr(10).join(f"- {reason}" for reason in context['approval_reasons'])}

Create a professional approval request that:
1. Explains why approval is needed
2. Summarizes the planned operation
3. Highlights the safety measures in place
4. Clearly states what roles need to approve
5. Uses formal but accessible language

Keep the message clear and authoritative (3-4 sentences)."""
    
    def _create_execution_ready_prompt(self, context: Dict[str, Any]) -> str:
        """Create prompt for execution ready message"""
        
        return f"""You are generating an execution-ready message for OpsConductor.

Plan Details:
- Intent: {context['intent']}
- Total steps: {context['total_steps']}
- Estimated time: {context['estimated_time']} seconds
- Tools: {', '.join(context['tools'])}
- Safety checks: {context['safety_checks']}

Key steps:
{chr(10).join(f"- {step}" for step in context['key_steps'])}

Create a confident, ready-to-execute message that:
1. Confirms the plan is ready for execution
2. Summarizes what will happen
3. Mentions safety measures in place
4. Provides the estimated timeframe
5. Uses confident, professional language

Keep the message clear and action-oriented (2-3 sentences)."""
    
    def _create_clarification_prompt(self, context: Dict[str, Any]) -> str:
        """Create prompt for clarification request"""
        
        return f"""You are generating a clarification request for OpsConductor.

Request Details:
- Intent: {context['intent']}
- Confidence: {context['confidence']:.2f}
- Questions needed: {context['clarification_count']}
- Required questions: {context['required_count']}

Questions to ask:
{chr(10).join(f"- {question}" for question in context['questions'])}

Create a helpful clarification request that:
1. Acknowledges partial understanding
2. Explains why more information is needed
3. Asks questions in a friendly way
4. Encourages the user to provide details
5. Uses supportive, helpful language

Keep the message encouraging and clear (2-3 sentences)."""
    
    def _create_fallback_information_response(self, decision: DecisionV1, plan: PlanV1) -> str:
        """Create fallback information response when LLM fails"""
        
        tools = list(set(step.tool for step in plan.plan.steps))
        time_estimate = plan.execution_metadata.total_estimated_time
        
        return (f"I'll gather the requested information about {decision.intent.action}. "
                f"This will involve {len(plan.plan.steps)} steps using {', '.join(tools)} "
                f"and should take approximately {time_estimate} seconds to complete.")
    
    def _create_fallback_plan_summary(self, decision: DecisionV1, plan: PlanV1) -> str:
        """Create fallback plan summary when LLM fails"""
        
        tools = list(set(step.tool for step in plan.plan.steps))
        time_estimate = plan.execution_metadata.total_estimated_time
        
        return (f"I've created a plan for {decision.intent.action} with {len(plan.plan.steps)} steps. "
                f"The plan uses {', '.join(tools)} and includes {len(plan.plan.safety_checks)} safety checks. "
                f"Estimated execution time is {time_estimate} seconds.")
    
    def _create_fallback_approval_request(
        self,
        decision: DecisionV1,
        plan: PlanV1,
        approval_points: List[ApprovalPoint]
    ) -> str:
        """Create fallback approval request when LLM fails"""
        
        return (f"The plan for {decision.intent.action} requires approval before execution. "
                f"There are {len(approval_points)} approval points that need review. "
                f"Please review and approve the high-risk operations before proceeding.")
    
    def _create_fallback_execution_ready(self, decision: DecisionV1, plan: PlanV1) -> str:
        """Create fallback execution ready message when LLM fails"""
        
        return (f"The plan for {decision.intent.action} is ready for execution. "
                f"It includes {len(plan.plan.steps)} steps with {len(plan.plan.safety_checks)} safety checks. "
                f"Estimated execution time is {plan.execution_metadata.total_estimated_time} seconds.")
    
    def _create_fallback_clarification_message(self, clarifications: List[ClarificationRequest]) -> str:
        """Create fallback clarification message when LLM fails"""
        
        return (f"I need some additional information to help you effectively. "
                f"Please provide answers to {len(clarifications)} questions so I can create the best plan for your request.")