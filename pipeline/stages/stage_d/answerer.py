"""
Stage D - Answerer
Main orchestrator for response generation and user communication

This component takes execution plans from Stage C and generates user-friendly responses,
handles approval workflows, and provides context-aware answering.
"""

import asyncio
import logging
import time
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime

from llm.ollama_client import OllamaClient
from pipeline.schemas.decision_v1 import DecisionV1, DecisionType
from pipeline.schemas.selection_v1 import SelectionV1
from pipeline.schemas.plan_v1 import PlanV1
from pipeline.schemas.response_v1 import (
    ResponseV1, ResponseType, ConfidenceLevel, ExecutionSummary,
    ApprovalPoint, ActionSuggestion, ClarificationResponse, ClarificationRequest
)

from .response_formatter import ResponseFormatter
from .approval_handler import ApprovalHandler
from .context_analyzer import ContextAnalyzer

logger = logging.getLogger(__name__)

class StageDAnswerer:
    """
    Stage D Answerer - Response Generation and User Communication
    
    Responsibilities:
    1. Generate user-friendly responses from execution plans
    2. Handle approval workflows and requirements
    3. Provide context-aware answering
    4. Format technical information for end users
    5. Suggest follow-up actions and recommendations
    """
    
    def __init__(self, llm_client: OllamaClient):
        """Initialize Stage D Answerer with LLM client"""
        self.llm_client = llm_client
        self.response_formatter = ResponseFormatter(llm_client)
        self.approval_handler = ApprovalHandler()
        self.context_analyzer = ContextAnalyzer(llm_client)
        
        # Statistics tracking
        self.stats = {
            "responses_generated": 0,
            "approval_requests_created": 0,
            "clarifications_requested": 0,
            "average_response_time_ms": 0,
            "total_processing_time_ms": 0,
            "response_types": {
                "information": 0,
                "plan_summary": 0,
                "approval_request": 0,
                "execution_ready": 0,
                "error": 0,
                "clarification": 0
            }
        }
        
        logger.info("Stage D Answerer initialized")
    
    async def generate_response(
        self,
        decision: DecisionV1,
        selection: SelectionV1,
        plan: PlanV1,
        context: Optional[Dict[str, Any]] = None
    ) -> ResponseV1:
        """
        Generate user-friendly response from pipeline results
        
        Args:
            decision: Stage A classification results
            selection: Stage B tool selection results
            plan: Stage C execution plan
            context: Additional context information
            
        Returns:
            ResponseV1: User-facing response
        """
        start_time = time.time()
        response_id = f"resp_{uuid.uuid4().hex[:8]}_{int(time.time())}"
        
        try:
            logger.info(f"Generating response for {decision.intent.category}/{decision.intent.action}")
            
            # 🚀 FAST PATH: Handle simple information/asset_management requests without selection/plan
            # Check if selection has no tools (information-only request)
            has_no_tools = (selection is None or 
                           (hasattr(selection, 'selected_tools') and len(selection.selected_tools) == 0))
            
            logger.info(f"🔍 FAST PATH DEBUG: has_no_tools={has_no_tools}, plan={plan}, category={decision.intent.category}")
            
            if has_no_tools and plan is None and decision.intent.category in ["information", "asset_management"]:
                logger.info(f"🚀 FAST PATH: Generating direct {decision.intent.category} response")
                
                # Generate direct answer using LLM for simple questions
                direct_response = await self._generate_direct_information_response(
                    decision.original_request, context
                )
                
                processing_time_ms = int((time.time() - start_time) * 1000)
                self.stats["responses_generated"] += 1
                self.stats["response_types"]["information"] += 1
                self.stats["total_processing_time_ms"] += processing_time_ms
                
                return ResponseV1(
                    response_type=ResponseType.INFORMATION,
                    message=direct_response,
                    confidence=ConfidenceLevel.HIGH,
                    execution_summary=None,
                    approval_required=False,
                    approval_points=[],
                    suggested_actions=[],
                    sources_consulted=["LLM Direct Response"],
                    related_documentation=[],
                    warnings=[],
                    limitations=[],
                    technical_details=None,
                    clarification_needed=None,
                    partial_analysis=None,
                    metadata={
                        "fast_path": True,
                        "processing_method": "direct_llm_response",
                        "bypassed_components": ["plan_analysis", "tool_selection", "approval_workflow"]
                    },
                    response_id=response_id,
                    timestamp=datetime.now().isoformat(),
                    processing_time_ms=processing_time_ms
                )
            
            # Normal path: Analyze context and determine response type
            response_type = await self._determine_response_type(decision, selection, plan)
            
            # Generate appropriate response based on type
            if response_type == ResponseType.INFORMATION:
                response = await self._generate_information_response(
                    decision, selection, plan, response_id, context
                )
            elif response_type == ResponseType.PLAN_SUMMARY:
                response = await self._generate_plan_summary_response(
                    decision, selection, plan, response_id, context
                )
            elif response_type == ResponseType.APPROVAL_REQUEST:
                response = await self._generate_approval_request_response(
                    decision, selection, plan, response_id, context
                )
            elif response_type == ResponseType.EXECUTION_READY:
                response = await self._generate_execution_ready_response(
                    decision, selection, plan, response_id, context
                )
            else:
                response = await self._generate_error_response(
                    "Unknown response type", response_id
                )
            
            # Calculate processing time
            processing_time_ms = max(1, int((time.time() - start_time) * 1000))
            response.processing_time_ms = processing_time_ms
            
            # Update statistics
            self._update_statistics(response_type, processing_time_ms)
            
            logger.info(f"Response generated: {response_type.value} ({processing_time_ms}ms)")
            return response
            
        except Exception as e:
            processing_time_ms = max(1, int((time.time() - start_time) * 1000))
            logger.error(f"Response generation failed: {e}")
            return await self._generate_error_response(str(e), response_id, processing_time_ms)
    
    async def request_clarification(
        self,
        decision: DecisionV1,
        missing_info: List[str],
        context: Optional[Dict[str, Any]] = None
    ) -> ClarificationResponse:
        """
        Generate clarification request when information is missing
        
        Args:
            decision: Partial decision from Stage A
            missing_info: List of missing information
            context: Additional context
            
        Returns:
            ClarificationResponse: Request for user clarification
        """
        start_time = time.time()
        response_id = f"clarify_{uuid.uuid4().hex[:8]}_{int(time.time())}"
        
        try:
            # Generate clarification questions
            clarifications = await self._generate_clarification_questions(
                decision, missing_info, context
            )
            
            # Create main clarification message
            message = await self.response_formatter.format_clarification_message(
                decision, clarifications
            )
            
            processing_time_ms = max(1, int((time.time() - start_time) * 1000))
            
            # Update statistics
            self.stats["clarifications_requested"] += 1
            self.stats["response_types"]["clarification"] += 1
            
            return ClarificationResponse(
                message=message,
                clarifications_needed=clarifications,
                partial_analysis={
                    "intent": decision.intent.category,
                    "action": decision.intent.action,
                    "confidence": decision.overall_confidence,
                    "entities_found": len(decision.entities)
                },
                response_id=response_id,
                processing_time_ms=processing_time_ms
            )
            
        except Exception as e:
            processing_time_ms = max(1, int((time.time() - start_time) * 1000))
            logger.error(f"Clarification generation failed: {e}")
            
            return ClarificationResponse(
                message=f"I need more information to help you, but encountered an error: {e}",
                clarifications_needed=[
                    ClarificationRequest(
                        question="Could you please rephrase your request with more details?",
                        context="I had trouble understanding your original request"
                    )
                ],
                response_id=response_id,
                processing_time_ms=processing_time_ms
            )
    
    async def generate_error_response(self, error_message: str) -> ResponseV1:
        """
        Public method to generate error response (called by orchestrator)
        
        Args:
            error_message: Error message to include in response
            
        Returns:
            ResponseV1: Error response
        """
        response_id = f"error_{uuid.uuid4().hex[:8]}_{int(time.time())}"
        return await self._generate_error_response(error_message, response_id, 0)
    
    async def _determine_response_type(
        self,
        decision: DecisionV1,
        selection: SelectionV1,
        plan: PlanV1
    ) -> ResponseType:
        """Determine the appropriate response type based on pipeline results"""
        
        # Check if this is an information-only request (no plan)
        if plan is None or decision.decision_type == DecisionType.INFO:
            return ResponseType.INFORMATION
        
        # Check if approval is required
        if plan.execution_metadata.approval_points:
            return ResponseType.APPROVAL_REQUEST
        
        # Check if plan is ready for execution
        if (plan.plan.steps and 
            selection.policy.risk_level.value in ["low", "medium"] and
            not plan.execution_metadata.approval_points):
            return ResponseType.EXECUTION_READY
        
        # Default to plan summary
        return ResponseType.PLAN_SUMMARY
    
    async def _generate_information_response(
        self,
        decision: DecisionV1,
        selection: SelectionV1,
        plan: PlanV1,
        response_id: str,
        context: Optional[Dict[str, Any]]
    ) -> ResponseV1:
        """Generate response for information-only requests"""
        
        # Analyze the information request
        analysis = await self.context_analyzer.analyze_information_request(
            decision, selection, plan
        )
        
        # Format the response message
        message = await self.response_formatter.format_information_response(
            decision, plan, analysis
        )
        
        # Generate execution summary
        execution_summary = self._create_execution_summary(plan)
        
        # Generate suggested actions
        suggested_actions = await self._generate_suggested_actions(
            decision, plan, "information"
        )
        
        return ResponseV1(
            response_type=ResponseType.INFORMATION,
            message=message,
            confidence=ConfidenceLevel.HIGH,
            execution_summary=execution_summary,
            suggested_actions=suggested_actions,
            sources_consulted=analysis.get("sources", []),
            technical_details=analysis.get("technical_details"),
            response_id=response_id,
            processing_time_ms=0  # Will be set by caller
        )
    
    async def _generate_plan_summary_response(
        self,
        decision: DecisionV1,
        selection: SelectionV1,
        plan: PlanV1,
        response_id: str,
        context: Optional[Dict[str, Any]]
    ) -> ResponseV1:
        """Generate response summarizing the execution plan"""
        
        # Format the plan summary message
        message = await self.response_formatter.format_plan_summary(
            decision, selection, plan
        )
        
        # Create execution summary
        execution_summary = self._create_execution_summary(plan)
        
        # Generate suggested actions
        suggested_actions = await self._generate_suggested_actions(
            decision, plan, "plan_summary"
        )
        
        # Check for warnings
        warnings = self._identify_warnings(plan)
        
        return ResponseV1(
            response_type=ResponseType.PLAN_SUMMARY,
            message=message,
            confidence=self._determine_confidence(decision, selection),
            execution_summary=execution_summary,
            suggested_actions=suggested_actions,
            warnings=warnings,
            sources_consulted=["execution_plan", "safety_analysis", "tool_capabilities"],
            response_id=response_id,
            processing_time_ms=0  # Will be set by caller
        )
    
    async def _generate_approval_request_response(
        self,
        decision: DecisionV1,
        selection: SelectionV1,
        plan: PlanV1,
        response_id: str,
        context: Optional[Dict[str, Any]]
    ) -> ResponseV1:
        """Generate response requesting approval for high-risk operations"""
        
        # Process approval points
        approval_points = self.approval_handler.process_approval_points(
            plan.execution_metadata.approval_points
        )
        
        # Format approval request message
        message = await self.response_formatter.format_approval_request(
            decision, plan, approval_points
        )
        
        # Create execution summary
        execution_summary = self._create_execution_summary(plan)
        
        # Generate suggested actions for post-approval
        suggested_actions = await self._generate_suggested_actions(
            decision, plan, "approval_request"
        )
        
        return ResponseV1(
            response_type=ResponseType.APPROVAL_REQUEST,
            message=message,
            confidence=self._determine_confidence(decision, selection),
            execution_summary=execution_summary,
            approval_required=True,
            approval_points=approval_points,
            suggested_actions=suggested_actions,
            warnings=self._identify_warnings(plan),
            sources_consulted=["execution_plan", "risk_assessment", "approval_policies"],
            response_id=response_id,
            processing_time_ms=0  # Will be set by caller
        )
    
    async def _generate_execution_ready_response(
        self,
        decision: DecisionV1,
        selection: SelectionV1,
        plan: PlanV1,
        response_id: str,
        context: Optional[Dict[str, Any]]
    ) -> ResponseV1:
        """Generate response for plans ready for immediate execution"""
        
        # Format execution ready message
        message = await self.response_formatter.format_execution_ready(
            decision, plan
        )
        
        # Create execution summary
        execution_summary = self._create_execution_summary(plan)
        
        # Generate monitoring suggestions
        suggested_actions = await self._generate_suggested_actions(
            decision, plan, "execution_ready"
        )
        
        return ResponseV1(
            response_type=ResponseType.EXECUTION_READY,
            message=message,
            confidence=ConfidenceLevel.HIGH,
            execution_summary=execution_summary,
            suggested_actions=suggested_actions,
            sources_consulted=["execution_plan", "safety_checks"],
            response_id=response_id,
            processing_time_ms=0  # Will be set by caller
        )
    
    async def _generate_error_response(
        self,
        error_message: str,
        response_id: str,
        processing_time_ms: int = 0
    ) -> ResponseV1:
        """Generate error response"""
        
        return ResponseV1(
            response_type=ResponseType.ERROR,
            message=f"I encountered an error while processing your request: {error_message}",
            confidence=ConfidenceLevel.LOW,
            warnings=[error_message],
            suggested_actions=[
                ActionSuggestion(
                    action="Retry request",
                    description="Try rephrasing your request or providing more details",
                    priority="medium"
                )
            ],
            response_id=response_id,
            processing_time_ms=processing_time_ms
        )
    
    def _create_execution_summary(self, plan: PlanV1) -> ExecutionSummary:
        """Create execution summary from plan"""
        
        # Determine risk level based on risk factors and approval points
        risk_level = "low"
        if plan.execution_metadata.approval_points:
            risk_level = "high"
        elif any("production" in factor.lower() for factor in plan.execution_metadata.risk_factors):
            risk_level = "medium"
        elif any("restart" in factor.lower() or "critical" in factor.lower() for factor in plan.execution_metadata.risk_factors):
            risk_level = "high"
        
        return ExecutionSummary(
            total_steps=len(plan.plan.steps),
            estimated_duration=plan.execution_metadata.total_estimated_time,
            risk_level=risk_level,
            tools_involved=list(set(step.tool for step in plan.plan.steps)),
            safety_checks=len(plan.plan.safety_checks),
            approval_points=len(plan.execution_metadata.approval_points)
        )
    
    def _determine_confidence(self, decision: DecisionV1, selection: SelectionV1) -> ConfidenceLevel:
        """Determine confidence level based on decision and selection quality"""
        
        if decision.overall_confidence >= 0.8 and selection.total_tools > 0:
            return ConfidenceLevel.HIGH
        elif decision.overall_confidence >= 0.6:
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.LOW
    
    def _identify_warnings(self, plan: PlanV1) -> List[str]:
        """Identify warnings from the execution plan"""
        
        warnings = []
        
        # Check for high-risk operations
        if any("high" in factor or "critical" in factor for factor in plan.execution_metadata.risk_factors):
            warnings.append("This operation involves high-risk activities")
        
        # Check for production environment
        if any("production" in step.description.lower() for step in plan.plan.steps):
            warnings.append("This operation affects production systems")
        
        # Check for service restarts
        if any("restart" in step.description.lower() for step in plan.plan.steps):
            warnings.append("This operation may cause service downtime")
        
        return warnings
    
    async def _generate_suggested_actions(
        self,
        decision: DecisionV1,
        plan: PlanV1,
        response_type: str
    ) -> List[ActionSuggestion]:
        """Generate context-appropriate suggested actions"""
        
        suggestions = []
        
        # Common monitoring suggestion
        if plan.plan.steps:
            suggestions.append(ActionSuggestion(
                action="Monitor execution",
                description="Watch the execution progress and system metrics",
                priority="high",
                estimated_time=plan.execution_metadata.total_estimated_time + 300
            ))
        
        # Type-specific suggestions
        if response_type == "approval_request":
            suggestions.append(ActionSuggestion(
                action="Review approval requirements",
                description="Ensure all necessary approvals are obtained before execution",
                priority="high",
                estimated_time=600
            ))
        
        elif response_type == "execution_ready":
            suggestions.append(ActionSuggestion(
                action="Prepare rollback plan",
                description="Have a rollback strategy ready in case of issues",
                priority="medium",
                estimated_time=300
            ))
        
        # Add documentation suggestion
        suggestions.append(ActionSuggestion(
            action="Document changes",
            description="Record the changes made for future reference",
            priority="low",
            estimated_time=180
        ))
        
        return suggestions
    
    async def _generate_clarification_questions(
        self,
        decision: DecisionV1,
        missing_info: List[str],
        context: Optional[Dict[str, Any]]
    ) -> List[ClarificationRequest]:
        """Generate specific clarification questions"""
        
        clarifications = []
        
        for missing in missing_info:
            if missing == "environment":
                clarifications.append(ClarificationRequest(
                    question="Which environment should I target?",
                    options=["development", "staging", "production"],
                    required=True,
                    context="This affects safety procedures and approval requirements"
                ))
            
            elif missing == "service_name":
                clarifications.append(ClarificationRequest(
                    question="Which specific service are you referring to?",
                    required=True,
                    context="I need the exact service name to create an accurate plan"
                ))
            
            elif missing == "host_target":
                clarifications.append(ClarificationRequest(
                    question="Which hosts should be targeted?",
                    required=True,
                    context="I need to know the specific hosts or host groups to target"
                ))
        
        # If no specific missing info provided, generate general clarifications
        if not clarifications and not missing_info:
            clarifications.append(ClarificationRequest(
                question="Could you provide more details about what you'd like me to do?",
                required=False,
                context="I need more information to create an accurate plan"
            ))
        
        return clarifications
    
    def _update_statistics(self, response_type: ResponseType, processing_time_ms: int):
        """Update internal statistics"""
        
        self.stats["responses_generated"] += 1
        self.stats["total_processing_time_ms"] += processing_time_ms
        self.stats["average_response_time_ms"] = (
            self.stats["total_processing_time_ms"] / self.stats["responses_generated"]
        )
        self.stats["response_types"][response_type.value] += 1
        
        if response_type == ResponseType.APPROVAL_REQUEST:
            self.stats["approval_requests_created"] += 1
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of Stage D Answerer"""
        
        return {
            "stage_d_answerer": "healthy",
            "llm_client": "connected" if self.llm_client else "disconnected",
            "components": {
                "response_formatter": "healthy",
                "approval_handler": "healthy", 
                "context_analyzer": "healthy"
            },
            "statistics": self.stats
        }
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get Stage D capabilities"""
        
        return {
            "component": "stage_d_answerer",
            "capabilities": [
                "user_friendly_response_generation",
                "approval_workflow_handling",
                "context_aware_answering",
                "technical_information_formatting",
                "follow_up_action_suggestions",
                "clarification_request_generation"
            ],
            "response_types": [rt.value for rt in ResponseType],
            "confidence_levels": [cl.value for cl in ConfidenceLevel],
            "features": [
                "execution_plan_summarization",
                "risk_assessment_communication",
                "approval_point_identification",
                "warning_and_limitation_detection",
                "suggested_action_generation",
                "technical_detail_formatting"
            ],
            "llm_integration": "available" if self.llm_client else "disabled"
        }
    
    async def _generate_direct_information_response(self, user_request: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        🚀 FAST PATH: Generate direct response for simple information requests
        
        This bypasses all the complex plan analysis and approval workflows
        for simple questions that just need direct answers.
        
        NOW WITH COMPREHENSIVE ASSET AWARENESS:
        - Injects full asset context (50+ fields) when relevant
        - Uses live asset data for accurate responses
        - Supports both asset-based and ad-hoc queries
        
        Args:
            user_request: Original user request (e.g., "what is 2+2", "how many Linux servers")
            context: Optional context information
            
        Returns:
            Direct answer string
        """
        try:
            # Import asset context provider
            from pipeline.integration.asset_service_context import (
                should_inject_asset_context,
                get_comprehensive_asset_context,
                fetch_all_assets
            )
            
            # Check if this is an asset-related query
            should_inject_assets = should_inject_asset_context(user_request)
            
            # Build system prompt with optional asset context
            system_prompt = "You are a helpful assistant that answers questions directly and accurately."
            
            if should_inject_assets:
                logger.info(f"🚀 FAST PATH: Detected asset query, injecting comprehensive asset context")
                
                try:
                    # Get comprehensive asset context (schema + live data)
                    asset_context = await get_comprehensive_asset_context(
                        include_summary=True,
                        max_assets_in_summary=100
                    )
                    
                    # Enhance system prompt with asset knowledge
                    system_prompt = f"""You are a helpful assistant with complete knowledge of our infrastructure assets.

{asset_context}

IMPORTANT INSTRUCTIONS:
- Use the asset data above to answer questions accurately
- When counting or listing assets, use the EXACT data provided
- Include relevant details (hostname, IP, OS, environment) when listing assets
- If asked about specific assets, reference the data above
- For ad-hoc targets (not in asset list), acknowledge they're not in the inventory
- Answer directly and concisely without explaining the system"""
                    
                    logger.info(f"✓ Injected asset context: {len(asset_context)} chars")
                    
                except Exception as e:
                    logger.error(f"Failed to inject asset context: {e}")
                    # Continue without asset context
            
            # Build prompt
            prompt = f"""Answer this question directly and concisely:

Question: {user_request}

Provide a clear, accurate answer. If you have asset data, use it. Otherwise, answer based on general knowledge."""

            # Use LLM to generate direct response
            from llm.client import LLMRequest
            
            llm_request = LLMRequest(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.1,  # Low temperature for consistent, factual responses
                max_tokens=500   # Allow more tokens for asset listings
            )
            
            response = await self.llm_client.generate(llm_request)
            
            # Extract text from LLM response object
            if hasattr(response, 'content'):
                direct_answer = response.content.strip()
            elif hasattr(response, 'response'):
                direct_answer = response.response.strip()
            elif hasattr(response, 'text'):
                direct_answer = response.text.strip()
            else:
                direct_answer = str(response).strip()
            
            if not direct_answer:
                return f"I understand you're asking about '{user_request}', but I wasn't able to generate a specific answer. Could you please rephrase your question?"
            
            return direct_answer
            
        except Exception as e:
            logger.error(f"Failed to generate direct information response: {e}")
            return f"I understand you're asking '{user_request}', but I'm having trouble processing that question right now. Please try rephrasing it or ask something else."