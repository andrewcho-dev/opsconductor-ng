"""
Technical Brain - Multi-Brain AI Architecture

The Technical Brain is responsible for determining HOW to achieve the user's intent.
It creates technical execution plans and orchestrates SME brain consultations.

Phase 1 Week 2 Implementation - Following exact roadmap specification.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import asyncio
import json

logger = logging.getLogger(__name__)

class TechnicalComplexity(Enum):
    """Technical complexity levels for execution planning"""
    SIMPLE = "simple"           # Single command/script execution
    MODERATE = "moderate"       # Multi-step with dependencies
    COMPLEX = "complex"         # Multi-system coordination
    CRITICAL = "critical"       # High-risk, multi-phase operations

class ExecutionStrategy(Enum):
    """Execution strategies for different scenarios"""
    SEQUENTIAL = "sequential"   # Step-by-step execution
    PARALLEL = "parallel"       # Concurrent execution where possible
    PHASED = "phased"          # Multi-phase with checkpoints
    ROLLBACK_SAFE = "rollback_safe"  # With automatic rollback capability

class ResourceRequirement(Enum):
    """Resource requirement levels"""
    MINIMAL = "minimal"         # Basic system resources
    STANDARD = "standard"       # Normal resource allocation
    INTENSIVE = "intensive"     # High resource requirements
    EXCLUSIVE = "exclusive"     # Requires exclusive access

@dataclass
class TechnicalStep:
    """Individual technical execution step"""
    step_id: str
    name: str
    description: str
    command: Optional[str] = None
    script_path: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    estimated_duration: int = 0  # seconds
    risk_level: str = "medium"
    rollback_command: Optional[str] = None
    validation_command: Optional[str] = None
    required_resources: List[str] = field(default_factory=list)

@dataclass
class TechnicalPlan:
    """Complete technical execution plan"""
    plan_id: str
    name: str
    description: str
    intent_analysis: Dict[str, Any]
    complexity: TechnicalComplexity
    strategy: ExecutionStrategy
    steps: List[TechnicalStep]
    resource_requirements: List[str]
    estimated_duration: int  # total seconds
    risk_assessment: Dict[str, Any]
    sme_consultations_needed: List[str]  # SME domains to consult
    confidence_score: float
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "plan_id": self.plan_id,
            "name": self.name,
            "description": self.description,
            "intent_analysis": self.intent_analysis,
            "complexity": self.complexity.value,
            "strategy": self.strategy.value,
            "steps": [
                {
                    "step_id": step.step_id,
                    "name": step.name,
                    "description": step.description,
                    "command": step.command,
                    "script_path": step.script_path,
                    "dependencies": step.dependencies,
                    "estimated_duration": step.estimated_duration,
                    "risk_level": step.risk_level,
                    "rollback_command": step.rollback_command,
                    "validation_command": step.validation_command,
                    "required_resources": step.required_resources
                }
                for step in self.steps
            ],
            "resource_requirements": self.resource_requirements,
            "estimated_duration": self.estimated_duration,
            "risk_assessment": self.risk_assessment,
            "sme_consultations_needed": self.sme_consultations_needed,
            "confidence_score": self.confidence_score,
            "created_at": self.created_at.isoformat()
        }

class TechnicalMethodSelector:
    """Selects appropriate technical methods based on intent analysis"""
    
    def __init__(self):
        self.method_patterns = self._load_method_patterns()
    
    async def select_methods(self, intent_analysis: Dict[str, Any]) -> List[str]:
        """Select technical methods based on intent analysis"""
        try:
            methods = []
            
            # Extract key information
            itil_service_type = intent_analysis.get("itil_service_type", "")
            business_intent = intent_analysis.get("business_intent", "")
            technical_requirements = intent_analysis.get("technical_requirements", [])
            
            # Method selection based on ITIL service type
            if itil_service_type == "incident_management":
                methods.extend(["diagnostic_analysis", "service_restoration", "root_cause_analysis"])
            elif itil_service_type == "service_request":
                methods.extend(["resource_provisioning", "configuration_management", "deployment_automation"])
            elif itil_service_type == "change_management":
                methods.extend(["change_planning", "impact_analysis", "rollback_preparation"])
            elif itil_service_type == "monitoring_management":
                methods.extend(["metrics_collection", "alerting_configuration", "dashboard_setup"])
            else:
                methods.extend(["information_gathering", "status_reporting"])
            
            # Add methods based on technical requirements
            for requirement in technical_requirements:
                if "database" in requirement.lower():
                    methods.append("database_operations")
                if "network" in requirement.lower():
                    methods.append("network_configuration")
                if "security" in requirement.lower():
                    methods.append("security_hardening")
                if "container" in requirement.lower():
                    methods.append("container_orchestration")
            
            return list(set(methods))  # Remove duplicates
            
        except Exception as e:
            logger.error(f"Error selecting technical methods: {str(e)}")
            return ["information_gathering"]  # Fallback
    
    def _load_method_patterns(self) -> Dict[str, Any]:
        """Load technical method patterns"""
        return {
            "diagnostic_analysis": {
                "description": "Analyze system state and identify issues",
                "complexity": TechnicalComplexity.MODERATE,
                "typical_steps": ["gather_logs", "check_services", "analyze_metrics"]
            },
            "service_restoration": {
                "description": "Restore failed or degraded services",
                "complexity": TechnicalComplexity.COMPLEX,
                "typical_steps": ["stop_service", "clear_locks", "restart_service", "verify_health"]
            },
            "resource_provisioning": {
                "description": "Provision new resources or services",
                "complexity": TechnicalComplexity.MODERATE,
                "typical_steps": ["validate_requirements", "allocate_resources", "configure_service", "test_deployment"]
            },
            "configuration_management": {
                "description": "Manage system and service configurations",
                "complexity": TechnicalComplexity.SIMPLE,
                "typical_steps": ["backup_config", "update_config", "validate_config", "apply_changes"]
            }
        }

class ExecutionPlanGenerator:
    """Generates detailed execution plans from technical methods"""
    
    def __init__(self):
        self.plan_templates = self._load_plan_templates()
    
    async def generate_plan(self, technical_methods: List[str], intent_analysis: Dict[str, Any]) -> TechnicalPlan:
        """Generate execution plan from technical methods"""
        try:
            plan_id = f"plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Determine complexity and strategy
            complexity = self._determine_complexity(technical_methods, intent_analysis)
            strategy = self._determine_strategy(complexity, intent_analysis)
            
            # Generate steps
            steps = await self._generate_steps(technical_methods, intent_analysis)
            
            # Calculate resource requirements
            resource_requirements = self._calculate_resource_requirements(steps)
            
            # Estimate duration
            estimated_duration = sum(step.estimated_duration for step in steps)
            
            # Perform risk assessment
            risk_assessment = self._assess_risks(steps, intent_analysis)
            
            # Determine SME consultations needed
            sme_consultations = self._determine_sme_consultations(technical_methods, intent_analysis)
            
            # Calculate confidence
            confidence_score = self._calculate_confidence(steps, risk_assessment, intent_analysis)
            
            return TechnicalPlan(
                plan_id=plan_id,
                name=f"Technical Plan for {intent_analysis.get('business_intent', 'Unknown Intent')}",
                description=f"Execution plan for {intent_analysis.get('itil_service_type', 'unknown')} request",
                intent_analysis=intent_analysis,
                complexity=complexity,
                strategy=strategy,
                steps=steps,
                resource_requirements=resource_requirements,
                estimated_duration=estimated_duration,
                risk_assessment=risk_assessment,
                sme_consultations_needed=sme_consultations,
                confidence_score=confidence_score
            )
            
        except Exception as e:
            logger.error(f"Error generating execution plan: {str(e)}")
            raise
    
    def _determine_complexity(self, methods: List[str], intent_analysis: Dict[str, Any]) -> TechnicalComplexity:
        """Determine technical complexity"""
        risk_level = intent_analysis.get("risk_level", "medium")
        method_count = len(methods)
        
        if risk_level == "high" or method_count > 5:
            return TechnicalComplexity.CRITICAL
        elif method_count > 3 or "complex" in str(methods):
            return TechnicalComplexity.COMPLEX
        elif method_count > 1:
            return TechnicalComplexity.MODERATE
        else:
            return TechnicalComplexity.SIMPLE
    
    def _determine_strategy(self, complexity: TechnicalComplexity, intent_analysis: Dict[str, Any]) -> ExecutionStrategy:
        """Determine execution strategy"""
        risk_level = intent_analysis.get("risk_level", "medium")
        
        if complexity == TechnicalComplexity.CRITICAL or risk_level == "high":
            return ExecutionStrategy.ROLLBACK_SAFE
        elif complexity == TechnicalComplexity.COMPLEX:
            return ExecutionStrategy.PHASED
        elif "parallel" in intent_analysis.get("technical_requirements", []):
            return ExecutionStrategy.PARALLEL
        else:
            return ExecutionStrategy.SEQUENTIAL
    
    async def _generate_steps(self, methods: List[str], intent_analysis: Dict[str, Any]) -> List[TechnicalStep]:
        """Generate technical steps from methods"""
        steps = []
        step_counter = 1
        
        for method in methods:
            if method in self.plan_templates:
                template = self.plan_templates[method]
                for step_template in template.get("steps", []):
                    step = TechnicalStep(
                        step_id=f"step_{step_counter:03d}",
                        name=step_template["name"],
                        description=step_template["description"],
                        command=step_template.get("command"),
                        script_path=step_template.get("script_path"),
                        dependencies=step_template.get("dependencies", []),
                        estimated_duration=step_template.get("estimated_duration", 60),
                        risk_level=step_template.get("risk_level", "medium"),
                        rollback_command=step_template.get("rollback_command"),
                        validation_command=step_template.get("validation_command"),
                        required_resources=step_template.get("required_resources", [])
                    )
                    steps.append(step)
                    step_counter += 1
        
        return steps
    
    def _calculate_resource_requirements(self, steps: List[TechnicalStep]) -> List[str]:
        """Calculate resource requirements from steps"""
        resources = set()
        for step in steps:
            resources.update(step.required_resources)
        return list(resources)
    
    def _assess_risks(self, steps: List[TechnicalStep], intent_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Assess risks of the execution plan"""
        high_risk_steps = [step for step in steps if step.risk_level == "high"]
        
        return {
            "overall_risk": "high" if high_risk_steps else "medium",
            "high_risk_steps": len(high_risk_steps),
            "total_steps": len(steps),
            "risk_factors": [
                "Production environment" if "production" in str(intent_analysis).lower() else None,
                "Database operations" if any("database" in step.description.lower() for step in steps) else None,
                "Network changes" if any("network" in step.description.lower() for step in steps) else None
            ],
            "mitigation_strategies": [
                "Rollback procedures prepared",
                "Validation steps included",
                "SME consultation recommended"
            ]
        }
    
    def _determine_sme_consultations(self, methods: List[str], intent_analysis: Dict[str, Any]) -> List[str]:
        """Determine which SME brains should be consulted"""
        sme_domains = set()
        
        # Based on technical methods
        for method in methods:
            if "database" in method:
                sme_domains.add("database_administration")
            if "network" in method:
                sme_domains.add("network_infrastructure")
            if "security" in method:
                sme_domains.add("security_and_compliance")
            if "container" in method:
                sme_domains.add("container_orchestration")
        
        # Based on intent analysis
        technical_requirements = intent_analysis.get("technical_requirements", [])
        for requirement in technical_requirements:
            if "cloud" in requirement.lower():
                sme_domains.add("cloud_services")
            if "monitoring" in requirement.lower():
                sme_domains.add("observability_monitoring")
        
        return list(sme_domains)
    
    def _calculate_confidence(self, steps: List[TechnicalStep], risk_assessment: Dict[str, Any], intent_analysis: Dict[str, Any]) -> float:
        """Calculate confidence score for the plan"""
        base_confidence = 0.8
        
        # Reduce confidence for high-risk operations
        if risk_assessment.get("overall_risk") == "high":
            base_confidence -= 0.2
        
        # Reduce confidence for complex plans
        if len(steps) > 10:
            base_confidence -= 0.1
        
        # Reduce confidence for unclear intent
        intent_confidence = intent_analysis.get("overall_confidence", 0.5)
        base_confidence = base_confidence * intent_confidence
        
        return max(0.1, min(1.0, base_confidence))
    
    def _load_plan_templates(self) -> Dict[str, Any]:
        """Load execution plan templates"""
        return {
            "diagnostic_analysis": {
                "steps": [
                    {
                        "name": "Gather System Logs",
                        "description": "Collect relevant system and application logs",
                        "command": "journalctl -n 100 --no-pager",
                        "estimated_duration": 30,
                        "risk_level": "low",
                        "required_resources": ["log_access"]
                    },
                    {
                        "name": "Check Service Status",
                        "description": "Verify status of critical services",
                        "command": "systemctl status",
                        "estimated_duration": 15,
                        "risk_level": "low",
                        "required_resources": ["system_access"]
                    }
                ]
            },
            "service_restoration": {
                "steps": [
                    {
                        "name": "Stop Service",
                        "description": "Gracefully stop the affected service",
                        "command": "systemctl stop {service_name}",
                        "estimated_duration": 30,
                        "risk_level": "medium",
                        "rollback_command": "systemctl start {service_name}",
                        "required_resources": ["service_control"]
                    },
                    {
                        "name": "Restart Service",
                        "description": "Start the service with fresh state",
                        "command": "systemctl start {service_name}",
                        "estimated_duration": 45,
                        "risk_level": "medium",
                        "validation_command": "systemctl is-active {service_name}",
                        "required_resources": ["service_control"]
                    }
                ]
            }
        }

class SMEBrainOrchestrator:
    """Orchestrates consultations with SME brains"""
    
    def __init__(self):
        self.active_sme_brains = {}
        self.consultation_queue = asyncio.Queue()
        self.conflict_resolver = SMEConflictResolver()
    
    async def consult_smes(self, technical_plan: TechnicalPlan, intent_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Orchestrate consultations with relevant SME brains"""
        try:
            consultations = {}
            
            for sme_domain in technical_plan.sme_consultations_needed:
                # For Phase 1, we'll simulate SME consultations
                # In later phases, actual SME brains will be implemented
                consultation = await self._simulate_sme_consultation(sme_domain, technical_plan, intent_analysis)
                consultations[sme_domain] = consultation
            
            return consultations
            
        except Exception as e:
            logger.error(f"Error consulting SME brains: {str(e)}")
            return {}
    
    async def _simulate_sme_consultation(self, domain: str, technical_plan: TechnicalPlan, intent_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate SME consultation (Phase 1 implementation)"""
        # This will be replaced with actual SME brain implementations in Phase 2
        return {
            "domain": domain,
            "recommendations": [f"Follow best practices for {domain}"],
            "confidence": 0.7,
            "risk_assessment": "medium",
            "additional_steps": [],
            "warnings": [],
            "consultation_time": datetime.now().isoformat()
        }

class SMEConflictResolver:
    """Resolves conflicts between SME recommendations"""
    
    async def resolve_conflicts(self, consultations: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve conflicts between SME recommendations"""
        # Phase 1 simple implementation
        return {
            "resolved_recommendations": [],
            "conflict_resolution_strategy": "consensus",
            "confidence_adjustment": 0.0
        }

class TechnicalFeasibilityAnalyzer:
    """Analyzes technical feasibility of execution plans"""
    
    async def analyze_feasibility(self, technical_plan: TechnicalPlan) -> Dict[str, Any]:
        """Analyze technical feasibility"""
        return {
            "feasible": True,
            "feasibility_score": 0.8,
            "blocking_issues": [],
            "recommendations": ["Proceed with caution"],
            "resource_availability": "sufficient"
        }

class TechnicalLearningEngine:
    """Learning engine for Technical Brain"""
    
    async def learn_from_execution(self, execution_result: Dict[str, Any]):
        """Learn from execution results"""
        # Phase 1 placeholder - will be implemented in Phase 2
        logger.info("Technical Brain learning from execution result")

class TechnicalBrain:
    """
    Technical Brain - Determining HOW to achieve user intent
    
    Phase 1 Week 2 Implementation following exact roadmap specification.
    
    Responsibilities:
    1. Technical Method Selection
    2. Execution Plan Generation  
    3. SME Brain Consultation Orchestration
    4. Feasibility and Risk Analysis
    """
    
    def __init__(self):
        self.brain_id = "technical_brain"
        self.brain_type = "technical"
        self.brain_version = "1.0.0"
        
        # Core components
        self.method_selector = TechnicalMethodSelector()
        self.plan_generator = ExecutionPlanGenerator()
        self.sme_orchestrator = SMEBrainOrchestrator()
        self.feasibility_analyzer = TechnicalFeasibilityAnalyzer()
        self.learning_engine = TechnicalLearningEngine()
        
        # Configuration
        self.confidence_threshold = 0.7
        
        logger.info("Technical Brain initialized - Phase 1 Week 2 implementation")
    
    async def create_execution_plan(self, intent_analysis: Dict[str, Any]) -> TechnicalPlan:
        """
        Create technical execution plan based on intent analysis
        
        This is the main entry point for Technical Brain processing.
        
        Args:
            intent_analysis: Analysis result from Intent Brain
            
        Returns:
            TechnicalPlan: Complete technical execution plan
        """
        try:
            logger.info(f"Creating execution plan for intent: {intent_analysis.get('business_intent')}")
            
            # Step 1: Select technical methods
            technical_methods = await self.method_selector.select_methods(intent_analysis)
            logger.info(f"Selected technical methods: {technical_methods}")
            
            # Step 2: Generate initial execution plan
            initial_plan = await self.plan_generator.generate_plan(technical_methods, intent_analysis)
            logger.info(f"Generated initial plan with {len(initial_plan.steps)} steps")
            
            # Step 3: Consult SME brains (if needed)
            sme_consultations = {}
            if initial_plan.sme_consultations_needed:
                sme_consultations = await self.sme_orchestrator.consult_smes(initial_plan, intent_analysis)
                logger.info(f"Completed SME consultations for domains: {list(sme_consultations.keys())}")
            
            # Step 4: Analyze feasibility
            feasibility_analysis = await self.feasibility_analyzer.analyze_feasibility(initial_plan)
            logger.info(f"Feasibility analysis completed: {feasibility_analysis.get('feasible', False)}")
            
            # Step 5: Finalize plan with SME input and feasibility analysis
            final_plan = await self._finalize_plan(initial_plan, sme_consultations, feasibility_analysis)
            
            logger.info(f"Technical plan created successfully: {final_plan.plan_id}")
            return final_plan
            
        except Exception as e:
            logger.error(f"Error creating execution plan: {str(e)}")
            raise
    
    async def _finalize_plan(self, initial_plan: TechnicalPlan, sme_consultations: Dict[str, Any], feasibility_analysis: Dict[str, Any]) -> TechnicalPlan:
        """Finalize execution plan with SME input and feasibility analysis"""
        
        # Adjust confidence based on SME consultations and feasibility
        confidence_adjustment = 0.0
        
        if sme_consultations:
            avg_sme_confidence = sum(consultation.get("confidence", 0.5) for consultation in sme_consultations.values()) / len(sme_consultations)
            confidence_adjustment += (avg_sme_confidence - 0.5) * 0.2
        
        if feasibility_analysis.get("feasible", True):
            confidence_adjustment += 0.1
        else:
            confidence_adjustment -= 0.3
        
        # Update plan confidence
        initial_plan.confidence_score = max(0.1, min(1.0, initial_plan.confidence_score + confidence_adjustment))
        
        # Add SME recommendations to risk assessment
        if sme_consultations:
            initial_plan.risk_assessment["sme_consultations"] = sme_consultations
            initial_plan.risk_assessment["sme_recommendations"] = [
                consultation.get("recommendations", []) for consultation in sme_consultations.values()
            ]
        
        # Add feasibility analysis
        initial_plan.risk_assessment["feasibility_analysis"] = feasibility_analysis
        
        return initial_plan
    
    async def get_brain_status(self) -> Dict[str, Any]:
        """Get current status of Technical Brain"""
        return {
            "brain_id": self.brain_id,
            "brain_type": self.brain_type,
            "brain_version": self.brain_version,
            "confidence_threshold": self.confidence_threshold,
            "status": "active",
            "capabilities": [
                "technical_method_selection",
                "execution_plan_generation",
                "sme_consultation_orchestration",
                "feasibility_analysis",
                "risk_assessment"
            ],
            "sme_domains_available": [
                "database_administration",
                "network_infrastructure", 
                "security_and_compliance",
                "container_orchestration",
                "cloud_services",
                "observability_monitoring"
            ]
        }