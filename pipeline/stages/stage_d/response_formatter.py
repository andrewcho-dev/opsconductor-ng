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
                "analysis_results": analysis
            }
            
            # Add plan details if plan exists
            if plan:
                context.update({
                    "steps_planned": len(plan.plan.steps),
                    "tools_involved": list(set(step.tool for step in plan.plan.steps)),
                    "safety_checks": len(plan.plan.safety_checks)
                })
            else:
                context.update({
                    "steps_planned": 0,
                    "tools_involved": [],
                    "safety_checks": 0,
                    "is_information_only": True
                })
            
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
        """Format message for execution-ready plans - returns minimal message since execution output will replace it"""
        
        # Return empty string - the execution output will be the actual message
        # This eliminates the verbose "ready for execution" preamble
        return ""
    
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
        
        if plan is None:
            return (f"I understand you're asking about {decision.intent.action}. "
                    f"This is an information request that doesn't require any tool execution.")
        
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
    
    # ========================================
    # Asset-Service Specific Formatting
    # ========================================
    
    def format_asset_results(
        self,
        assets: List[Dict[str, Any]],
        query_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Format asset-service query results with disambiguation logic.
        
        Handles different result scenarios:
        - 0 results: "No assets found" message
        - 1 result: Direct answer with asset details
        - 2-5 results: Table of candidates for disambiguation
        - 6-50 results: Grouped summary by environment
        - 50+ results: Pagination guidance
        
        Args:
            assets: List of asset dictionaries from asset-service
            query_context: Optional context about the query (search term, filters, etc.)
            
        Returns:
            Formatted string for LLM consumption
        """
        result_count = len(assets)
        
        # Case 1: No results
        if result_count == 0:
            return self._format_no_assets_found(query_context)
        
        # Case 2: Single result - direct answer
        elif result_count == 1:
            return self._format_single_asset(assets[0])
        
        # Case 3: Few results (2-5) - show table for disambiguation
        elif result_count <= 5:
            return self._format_few_assets(assets, query_context)
        
        # Case 4: Many results (6-50) - group by environment
        elif result_count <= 50:
            return self._format_many_assets(assets, query_context)
        
        # Case 5: Too many results (50+) - pagination guidance
        else:
            return self._format_too_many_assets(result_count, assets[:10], query_context)
    
    def _format_no_assets_found(self, query_context: Optional[Dict[str, Any]]) -> str:
        """Format message when no assets are found."""
        base_message = "No assets found"
        
        if query_context:
            filters = []
            if "hostname" in query_context:
                filters.append(f"hostname '{query_context['hostname']}'")
            if "ip_address" in query_context:
                filters.append(f"IP address '{query_context['ip_address']}'")
            if "environment" in query_context:
                filters.append(f"environment '{query_context['environment']}'")
            if "service" in query_context:
                filters.append(f"service '{query_context['service']}'")
            
            if filters:
                base_message += f" matching {' and '.join(filters)}"
        
        base_message += ".\n\nSuggestions:\n"
        base_message += "- Check for typos in the hostname or filters\n"
        base_message += "- Try a broader search (e.g., partial hostname)\n"
        base_message += "- Verify the asset exists in the asset-service inventory"
        
        return base_message
    
    def _format_single_asset(self, asset: Dict[str, Any]) -> str:
        """Format a single asset result."""
        lines = ["Asset found:\n"]
        
        # Rank fields by importance for display
        important_fields = ["hostname", "ip_address", "environment", "status", "os_type", "service_type"]
        other_fields = [k for k in asset.keys() if k not in important_fields and not k.startswith("_")]
        
        # Display important fields first
        for field in important_fields:
            if field in asset and asset[field]:
                lines.append(f"  {field}: {asset[field]}")
        
        # Display other fields
        for field in sorted(other_fields):
            if asset[field]:
                lines.append(f"  {field}: {asset[field]}")
        
        return "\n".join(lines)
    
    def _format_few_assets(self, assets: List[Dict[str, Any]], query_context: Optional[Dict[str, Any]]) -> str:
        """Format 2-5 assets as a table for disambiguation."""
        lines = [f"Found {len(assets)} matching assets:\n"]
        
        # Determine which fields to display (common fields across all assets)
        display_fields = ["hostname", "ip_address", "environment", "status"]
        
        # Create table header
        header = " | ".join(f"{field:20}" for field in display_fields)
        lines.append(header)
        lines.append("-" * len(header))
        
        # Create table rows
        for asset in assets:
            row = " | ".join(f"{str(asset.get(field, 'N/A')):20}" for field in display_fields)
            lines.append(row)
        
        lines.append("\nPlease specify which asset you're interested in by providing more details (e.g., environment, IP address).")
        
        return "\n".join(lines)
    
    def _format_many_assets(self, assets: List[Dict[str, Any]], query_context: Optional[Dict[str, Any]]) -> str:
        """Format 6-50 assets grouped by environment."""
        lines = [f"Found {len(assets)} matching assets.\n"]
        
        # Group by environment
        by_environment = {}
        for asset in assets:
            env = asset.get("environment", "unknown")
            if env not in by_environment:
                by_environment[env] = []
            by_environment[env].append(asset)
        
        lines.append("Summary by environment:")
        for env in sorted(by_environment.keys()):
            count = len(by_environment[env])
            lines.append(f"  {env}: {count} assets")
        
        lines.append("\nShowing first 10 assets:")
        for i, asset in enumerate(assets[:10], 1):
            hostname = asset.get("hostname", "N/A")
            ip = asset.get("ip_address", "N/A")
            env = asset.get("environment", "N/A")
            lines.append(f"  {i}. {hostname} ({ip}) - {env}")
        
        if len(assets) > 10:
            lines.append(f"\n... and {len(assets) - 10} more assets.")
        
        lines.append("\nTo narrow results, add filters like environment, service type, or OS type.")
        
        return "\n".join(lines)
    
    def _format_too_many_assets(
        self,
        total_count: int,
        sample_assets: List[Dict[str, Any]],
        query_context: Optional[Dict[str, Any]]
    ) -> str:
        """Format message when there are too many results (50+)."""
        lines = [f"Found {total_count} matching assets (showing first 10):\n"]
        
        for i, asset in enumerate(sample_assets, 1):
            hostname = asset.get("hostname", "N/A")
            env = asset.get("environment", "N/A")
            lines.append(f"  {i}. {hostname} - {env}")
        
        lines.append(f"\n... and {total_count - 10} more assets.")
        lines.append("\n⚠️  Too many results to display effectively.")
        lines.append("\nPlease narrow your search by adding filters:")
        lines.append("  - Specify an environment (e.g., 'production', 'staging')")
        lines.append("  - Add a service type (e.g., 'web', 'database')")
        lines.append("  - Use a more specific hostname pattern")
        lines.append("  - Filter by OS type or status")
        
        return "\n".join(lines)
    
    def rank_assets(self, assets: List[Dict[str, Any]], query_context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Rank assets deterministically for consistent ordering.
        
        Ranking criteria (in order of priority):
        1. Exact hostname match (if query_context has hostname)
        2. Environment priority: production > staging > development > other
        3. Status: active > inactive > unknown
        4. Alphabetical by hostname
        
        Args:
            assets: List of asset dictionaries
            query_context: Optional context with query information
            
        Returns:
            Sorted list of assets
        """
        def rank_key(asset: Dict[str, Any]) -> tuple:
            # Priority 1: Exact hostname match
            exact_match = 0
            if query_context and "hostname" in query_context:
                if asset.get("hostname") == query_context["hostname"]:
                    exact_match = 1
            
            # Priority 2: Environment ranking
            env_priority = {
                "production": 4,
                "prod": 4,
                "staging": 3,
                "stage": 3,
                "development": 2,
                "dev": 2,
                "test": 1
            }
            env = asset.get("environment", "").lower()
            env_rank = env_priority.get(env, 0)
            
            # Priority 3: Status ranking
            status_priority = {
                "active": 3,
                "running": 3,
                "inactive": 2,
                "stopped": 1,
                "unknown": 0
            }
            status = asset.get("status", "").lower()
            status_rank = status_priority.get(status, 0)
            
            # Priority 4: Alphabetical by hostname
            hostname = asset.get("hostname", "zzz")  # Put assets without hostname last
            
            # Return tuple for sorting (higher values first, except hostname which is alphabetical)
            return (-exact_match, -env_rank, -status_rank, hostname)
        
        return sorted(assets, key=rank_key)
    
    def format_asset_error(self, error_type: str, error_details: Optional[Dict[str, Any]] = None) -> str:
        """
        Format standardized error messages for asset-service failures.
        
        Args:
            error_type: Type of error (timeout, circuit_breaker, schema_error, api_error, etc.)
            error_details: Optional details about the error
            
        Returns:
            User-friendly error message
        """
        error_messages = {
            "timeout": (
                "⚠️  Asset-service request timed out.\n"
                "The asset-service is taking longer than expected to respond.\n"
                "Please try again in a moment."
            ),
            "circuit_breaker": (
                "⚠️  Asset-service is temporarily unavailable.\n"
                "The service has experienced multiple failures and is in recovery mode.\n"
                "Please try again in a few minutes."
            ),
            "schema_error": (
                "⚠️  Asset-service returned unexpected data format.\n"
                "The response from asset-service doesn't match the expected schema.\n"
                "This may indicate a version mismatch or API change."
            ),
            "api_error": (
                "⚠️  Asset-service API error.\n"
                "The asset-service encountered an error processing your request."
            ),
            "network_error": (
                "⚠️  Network error connecting to asset-service.\n"
                "Unable to reach the asset-service endpoint.\n"
                "Please check network connectivity."
            ),
            "permission_denied": (
                "⚠️  Permission denied.\n"
                "You don't have permission to access this asset information.\n"
                "Please contact your administrator if you need access."
            ),
            "not_found": (
                "⚠️  Asset not found.\n"
                "The requested asset does not exist in the inventory."
            )
        }
        
        base_message = error_messages.get(error_type, f"⚠️  An error occurred: {error_type}")
        
        # Add error details if provided
        if error_details:
            if "message" in error_details:
                base_message += f"\n\nDetails: {error_details['message']}"
            if "status_code" in error_details:
                base_message += f"\nStatus code: {error_details['status_code']}"
        
        return base_message
    
    def redact_credential_handle(self, credential_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Redact sensitive credential information, returning only safe handles.
        
        Args:
            credential_data: Raw credential data from asset-service
            
        Returns:
            Redacted credential data with only safe handles
        """
        redacted = {}
        
        # Safe fields to include
        safe_fields = ["credential_id", "credential_type", "asset_id", "created_at", "expires_at", "status"]
        
        for field in safe_fields:
            if field in credential_data:
                redacted[field] = credential_data[field]
        
        # Add redaction notice
        redacted["_redacted"] = True
        redacted["_note"] = "Sensitive credential data has been redacted. Use credential_id to access."
        
        return redacted