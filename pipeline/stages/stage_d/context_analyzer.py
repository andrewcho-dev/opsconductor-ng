"""
Context Analyzer
Analyzes context and provides intelligent insights

This component analyzes the context of requests and execution plans to provide
intelligent insights, recommendations, and contextual information for responses.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from llm.ollama_client import OllamaClient
from pipeline.schemas.decision_v1 import DecisionV1
from pipeline.schemas.selection_v1 import SelectionV1
from pipeline.schemas.plan_v1 import PlanV1

logger = logging.getLogger(__name__)

class ContextAnalyzer:
    """
    Context Analyzer for Stage D
    
    Analyzes request context, execution plans, and system state to provide
    intelligent insights and recommendations for user responses.
    """
    
    def __init__(self, llm_client: OllamaClient):
        """Initialize context analyzer with LLM client"""
        self.llm_client = llm_client
        
        # Context analysis patterns
        self.analysis_patterns = {
            "system_status": self._analyze_system_status_context,
            "service_management": self._analyze_service_management_context,
            "troubleshooting": self._analyze_troubleshooting_context,
            "configuration_management": self._analyze_configuration_context,
            "monitoring": self._analyze_monitoring_context,
            "log_analysis": self._analyze_log_analysis_context
        }
        
        logger.info("Context Analyzer initialized")
    
    async def analyze_information_request(
        self,
        decision: DecisionV1,
        selection: SelectionV1,
        plan: PlanV1
    ) -> Dict[str, Any]:
        """
        Analyze context for information-only requests
        
        Args:
            decision: Stage A classification results
            selection: Stage B tool selection results
            plan: Stage C execution plan
            
        Returns:
            Dict containing analysis results and insights
        """
        
        try:
            # Determine analysis type based on intent
            intent_category = decision.intent.category
            analyzer = self.analysis_patterns.get(
                intent_category, 
                self._analyze_general_context
            )
            
            # Perform specific analysis
            analysis = await analyzer(decision, selection, plan)
            
            # Add general insights
            analysis.update(await self._generate_general_insights(decision, plan))
            
            logger.info(f"Context analysis completed for {intent_category}")
            return analysis
            
        except Exception as e:
            logger.error(f"Context analysis failed: {e}")
            return {
                "sources": ["execution_plan"],
                "insights": ["Analysis unavailable due to processing error"],
                "recommendations": ["Review request and try again"],
                "technical_details": {"error": str(e)}
            }
    
    async def analyze_execution_context(
        self,
        decision: DecisionV1,
        plan: PlanV1
    ) -> Dict[str, Any]:
        """
        Analyze context for execution plans
        
        Args:
            decision: Stage A classification results
            plan: Stage C execution plan
            
        Returns:
            Dict containing execution context analysis
        """
        
        try:
            # Analyze execution complexity
            complexity = self._assess_execution_complexity(plan)
            
            # Identify potential risks
            risks = self._identify_execution_risks(plan)
            
            # Generate execution insights
            insights = await self._generate_execution_insights(decision, plan)
            
            # Analyze dependencies
            dependencies = self._analyze_execution_dependencies(plan)
            
            return {
                "complexity": complexity,
                "risks": risks,
                "insights": insights,
                "dependencies": dependencies,
                "recommendations": await self._generate_execution_recommendations(plan)
            }
            
        except Exception as e:
            logger.error(f"Execution context analysis failed: {e}")
            return {
                "complexity": "unknown",
                "risks": ["Analysis error occurred"],
                "insights": ["Unable to analyze execution context"],
                "dependencies": [],
                "recommendations": ["Review execution plan manually"]
            }
    
    async def _analyze_system_status_context(
        self,
        decision: DecisionV1,
        selection: SelectionV1,
        plan: PlanV1
    ) -> Dict[str, Any]:
        """Analyze context for system status requests"""
        
        # Identify what system information will be gathered
        info_types = []
        tools_used = [step.tool for step in plan.plan.steps]
        
        if "ps" in tools_used:
            info_types.append("process_information")
        if "systemctl" in tools_used:
            info_types.append("service_status")
        if "journalctl" in tools_used:
            info_types.append("system_logs")
        if "info_display" in tools_used:
            info_types.append("system_metrics")
        
        return {
            "sources": ["system_monitoring", "service_registry"],
            "information_types": info_types,
            "insights": [
                f"Will gather {len(info_types)} types of system information",
                f"Using {len(tools_used)} monitoring tools",
                "Real-time system status will be provided"
            ],
            "technical_details": {
                "tools_used": tools_used,
                "estimated_data_points": len(plan.plan.steps) * 5
            }
        }
    
    async def _analyze_service_management_context(
        self,
        decision: DecisionV1,
        selection: SelectionV1,
        plan: PlanV1
    ) -> Dict[str, Any]:
        """Analyze context for service management requests"""
        
        # Identify services being managed
        services = [e.value for e in decision.entities if hasattr(e, 'type') and e.type == "service"]
        actions = [e.value for e in decision.entities if hasattr(e, 'type') and e.type == "action"]
        
        # Analyze impact
        impact_level = "low"
        if any("restart" in action.lower() for action in actions):
            impact_level = "medium"
        if any("production" in step.description.lower() for step in plan.plan.steps):
            impact_level = "high"
        
        return {
            "sources": ["service_registry", "deployment_configs"],
            "services_affected": services,
            "actions_planned": actions,
            "impact_level": impact_level,
            "insights": [
                f"Managing {len(services)} services with {len(actions)} actions",
                f"Impact level assessed as {impact_level}",
                f"Safety checks in place: {len(plan.plan.safety_checks)}"
            ],
            "technical_details": {
                "service_dependencies": "Will be checked during execution",
                "rollback_available": len(plan.plan.rollback_plan) > 0
            }
        }
    
    async def _analyze_troubleshooting_context(
        self,
        decision: DecisionV1,
        selection: SelectionV1,
        plan: PlanV1
    ) -> Dict[str, Any]:
        """Analyze context for troubleshooting requests"""
        
        # Identify troubleshooting approach
        diagnostic_tools = []
        remediation_tools = []
        
        for step in plan.plan.steps:
            if step.tool in ["journalctl", "ps", "info_display"]:
                diagnostic_tools.append(step.tool)
            elif step.tool in ["systemctl", "config_manager", "docker"]:
                remediation_tools.append(step.tool)
        
        return {
            "sources": ["error_logs", "system_diagnostics", "troubleshooting_guides"],
            "diagnostic_tools": list(set(diagnostic_tools)),
            "remediation_tools": list(set(remediation_tools)),
            "insights": [
                f"Diagnostic phase uses {len(set(diagnostic_tools))} tools",
                f"Remediation phase uses {len(set(remediation_tools))} tools",
                "Systematic troubleshooting approach planned"
            ],
            "technical_details": {
                "troubleshooting_phases": ["diagnosis", "remediation", "verification"],
                "estimated_resolution_time": plan.execution_metadata.total_estimated_time
            }
        }
    
    async def _analyze_configuration_context(
        self,
        decision: DecisionV1,
        selection: SelectionV1,
        plan: PlanV1
    ) -> Dict[str, Any]:
        """Analyze context for configuration management requests"""
        
        # Identify configuration changes
        config_types = []
        if "config_manager" in [step.tool for step in plan.plan.steps]:
            config_types.append("application_config")
        if "file_manager" in [step.tool for step in plan.plan.steps]:
            config_types.append("file_system_config")
        if "systemctl" in [step.tool for step in plan.plan.steps]:
            config_types.append("service_config")
        
        return {
            "sources": ["configuration_management", "change_logs"],
            "configuration_types": config_types,
            "insights": [
                f"Managing {len(config_types)} types of configurations",
                "Configuration changes will be tracked",
                "Backup and rollback procedures in place"
            ],
            "technical_details": {
                "change_tracking": "Enabled",
                "backup_strategy": "Automatic before changes"
            }
        }
    
    async def _analyze_monitoring_context(
        self,
        decision: DecisionV1,
        selection: SelectionV1,
        plan: PlanV1
    ) -> Dict[str, Any]:
        """Analyze context for monitoring requests"""
        
        return {
            "sources": ["monitoring_systems", "metrics_databases"],
            "monitoring_scope": decision.entities.hosts + decision.entities.services,
            "insights": [
                "Comprehensive monitoring setup planned",
                "Real-time metrics will be available",
                "Alert thresholds will be configured"
            ],
            "technical_details": {
                "metrics_collected": "System and application metrics",
                "retention_period": "Standard retention policy"
            }
        }
    
    async def _analyze_log_analysis_context(
        self,
        decision: DecisionV1,
        selection: SelectionV1,
        plan: PlanV1
    ) -> Dict[str, Any]:
        """Analyze context for log analysis requests"""
        
        return {
            "sources": ["system_logs", "application_logs", "audit_logs"],
            "log_sources": decision.entities.hosts + decision.entities.services,
            "insights": [
                "Multi-source log analysis planned",
                "Pattern recognition will be applied",
                "Relevant events will be highlighted"
            ],
            "technical_details": {
                "log_retention": "Available for analysis",
                "analysis_methods": ["pattern_matching", "anomaly_detection"]
            }
        }
    
    async def _analyze_general_context(
        self,
        decision: DecisionV1,
        selection: SelectionV1,
        plan: PlanV1
    ) -> Dict[str, Any]:
        """General context analysis for unspecified intent types"""
        
        # Handle None plan (information-only requests)
        if plan is None:
            return {
                "sources": ["llm_knowledge"],
                "insights": [
                    "Information-only request, no execution plan needed",
                    "Response generated from available knowledge"
                ],
                "technical_details": {
                    "execution_approach": "Direct information response",
                    "safety_measures": "No execution required"
                }
            }
        
        return {
            "sources": ["execution_plan", "tool_capabilities"],
            "insights": [
                f"Plan includes {len(plan.plan.steps)} execution steps",
                f"Using {len(set(step.tool for step in plan.plan.steps))} different tools",
                f"Safety measures include {len(plan.plan.safety_checks)} checks"
            ],
            "technical_details": {
                "execution_approach": "Systematic step-by-step execution",
                "safety_measures": "Comprehensive safety checks included"
            }
        }
    
    async def _generate_general_insights(
        self,
        decision: DecisionV1,
        plan: PlanV1
    ) -> Dict[str, Any]:
        """Generate general insights about the request and plan"""
        
        insights = []
        recommendations = []
        
        # Confidence-based insights
        if decision.overall_confidence >= 0.8:
            insights.append("High confidence in request understanding")
        elif decision.overall_confidence >= 0.6:
            insights.append("Good understanding of request with minor uncertainties")
        else:
            insights.append("Request understanding has some uncertainties")
            recommendations.append("Consider providing additional context for better results")
        
        # Plan complexity insights (only if plan exists)
        if plan:
            if len(plan.plan.steps) > 5:
                insights.append("Complex operation with multiple steps")
                recommendations.append("Monitor execution progress closely")
            else:
                insights.append("Straightforward operation with manageable complexity")
            
            # Safety insights
            if len(plan.plan.safety_checks) > 10:
                insights.append("Comprehensive safety measures in place")
            else:
                recommendations.append("Consider additional safety monitoring")
        else:
            insights.append("Information-only request, no execution plan needed")
        
        return {
            "general_insights": insights,
            "recommendations": recommendations
        }
    
    def _assess_execution_complexity(self, plan: PlanV1) -> str:
        """Assess the complexity of the execution plan"""
        
        step_count = len(plan.plan.steps)
        tool_count = len(set(step.tool for step in plan.plan.steps))
        dependency_count = sum(len(step.depends_on) for step in plan.plan.steps)
        
        complexity_score = step_count + (tool_count * 2) + dependency_count
        
        if complexity_score > 20:
            return "high"
        elif complexity_score > 10:
            return "medium"
        else:
            return "low"
    
    def _identify_execution_risks(self, plan: PlanV1) -> List[str]:
        """Identify potential risks in the execution plan"""
        
        risks = []
        
        # Check for production operations
        if any("production" in step.description.lower() for step in plan.plan.steps):
            risks.append("Production environment operations")
        
        # Check for service restarts
        if any("restart" in step.description.lower() for step in plan.plan.steps):
            risks.append("Service restart operations may cause downtime")
        
        # Check for configuration changes
        if any(step.tool == "config_manager" for step in plan.plan.steps):
            risks.append("Configuration changes may affect system behavior")
        
        # Check for complex dependencies
        max_dependencies = max((len(step.depends_on) for step in plan.plan.steps), default=0)
        if max_dependencies > 3:
            risks.append("Complex step dependencies may cause execution delays")
        
        return risks
    
    async def _generate_execution_insights(
        self,
        decision: DecisionV1,
        plan: PlanV1
    ) -> List[str]:
        """Generate insights about execution plan"""
        
        insights = []
        
        # Execution time insights
        total_time = plan.execution_metadata.total_estimated_time
        if total_time > 600:  # 10 minutes
            insights.append(f"Long-running operation ({total_time // 60} minutes estimated)")
        else:
            insights.append(f"Quick operation ({total_time} seconds estimated)")
        
        # Tool usage insights
        tools = set(step.tool for step in plan.plan.steps)
        if len(tools) > 3:
            insights.append(f"Multi-tool operation using {len(tools)} different tools")
        
        # Safety insights
        safety_ratio = len(plan.plan.safety_checks) / len(plan.plan.steps)
        if safety_ratio > 2:
            insights.append("High safety check coverage")
        
        return insights
    
    def _analyze_execution_dependencies(self, plan: PlanV1) -> Dict[str, Any]:
        """Analyze execution dependencies"""
        
        # Count dependencies
        total_dependencies = sum(len(step.depends_on) for step in plan.plan.steps)
        
        # Find steps with no dependencies (can run in parallel)
        parallel_steps = [step.id for step in plan.plan.steps if not step.depends_on]
        
        # Find critical path (steps with most dependencies)
        max_deps = max((len(step.depends_on) for step in plan.plan.steps), default=0)
        critical_steps = [step.id for step in plan.plan.steps if len(step.depends_on) == max_deps]
        
        return {
            "total_dependencies": total_dependencies,
            "parallel_executable": len(parallel_steps),
            "critical_path_steps": critical_steps,
            "dependency_complexity": "high" if max_deps > 2 else "low"
        }
    
    async def _generate_execution_recommendations(self, plan: PlanV1) -> List[str]:
        """Generate recommendations for execution"""
        
        recommendations = []
        
        # Time-based recommendations
        if plan.execution_metadata.total_estimated_time > 300:
            recommendations.append("Monitor execution progress regularly")
        
        # Safety-based recommendations
        if len(plan.plan.safety_checks) < len(plan.plan.steps):
            recommendations.append("Consider additional safety monitoring")
        
        # Approval-based recommendations
        if plan.execution_metadata.approval_points:
            recommendations.append("Ensure all approvals are obtained before execution")
        
        # General recommendations
        recommendations.append("Have rollback plan ready in case of issues")
        recommendations.append("Document execution results for future reference")
        
        return recommendations