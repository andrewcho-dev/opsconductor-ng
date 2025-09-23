"""
Multi-Brain Coordinator

Central coordination system that orchestrates the multi-brain AI architecture,
managing communication between Intent Brain, Technical Brain, and SME Brains.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import asyncio

# Import advanced SME orchestration components
from ..brains.sme.advanced_sme_orchestrator import (
    AdvancedSMEOrchestrator, ConsultationRequest, ConsultationPattern, 
    ConsultationPriority, ConsultationResult
)
from ..brains.base_sme_brain import SMEQuery

logger = logging.getLogger(__name__)

class CoordinationPhase(Enum):
    """Phases of multi-brain coordination"""
    INTENT_ANALYSIS = "intent_analysis"
    TECHNICAL_PLANNING = "technical_planning"
    SME_CONSULTATION = "sme_consultation"
    EXECUTION_PLANNING = "execution_planning"
    CONFIDENCE_AGGREGATION = "confidence_aggregation"
    FINAL_DECISION = "final_decision"

class DecisionStatus(Enum):
    """Status of coordination decision"""
    APPROVED = "approved"
    REQUIRES_REVIEW = "requires_review"
    REJECTED = "rejected"
    ESCALATED = "escalated"

@dataclass
class CoordinationResult:
    """Result of multi-brain coordination"""
    coordination_id: str
    user_message: str
    timestamp: datetime
    
    # Phase results
    intent_result: Optional[Dict[str, Any]]
    technical_result: Optional[Dict[str, Any]]
    sme_results: Dict[str, Dict[str, Any]]
    
    # Aggregated decision
    final_decision: DecisionStatus
    aggregated_confidence: float
    recommended_actions: List[str]
    risk_assessment: Dict[str, Any]
    
    # Execution plan
    execution_plan: Optional[Dict[str, Any]]
    resource_requirements: List[str]
    estimated_duration: Optional[float]
    
    # Metadata
    coordination_time: float
    participating_brains: List[str]
    confidence_breakdown: Dict[str, float]

class MultiBrainCoordinator:
    """
    Multi-Brain Coordinator
    
    Orchestrates the multi-brain AI architecture by:
    1. Coordinating Intent Brain analysis
    2. Engaging Technical Brain for execution planning
    3. Consulting relevant SME Brains for domain expertise
    4. Aggregating confidence scores and recommendations
    5. Making final decisions with risk assessment
    6. Facilitating continuous learning across brains
    """
    
    def __init__(self, brain_registry=None, learning_engine=None):
        """
        Initialize the multi-brain coordinator.
        
        Args:
            brain_registry: Registry of available brains
            learning_engine: Continuous learning engine
        """
        self.coordinator_id = "multi_brain_coordinator"
        self.version = "2.0.0"  # Updated for Phase 3 advanced features
        self.brain_registry = brain_registry
        self.learning_engine = learning_engine
        
        # Initialize advanced SME orchestrator
        self.advanced_sme_orchestrator = None
        if brain_registry:
            sme_brains = self._extract_sme_brains(brain_registry)
            if sme_brains:
                self.advanced_sme_orchestrator = AdvancedSMEOrchestrator(sme_brains)
        
        # Coordination configuration
        self.min_confidence_threshold = 0.7
        self.sme_consultation_threshold = 0.6  # Lowered for more SME consultation
        self.escalation_threshold = 0.5  # When to escalate decisions
        self.max_coordination_time = 45.0  # Increased for advanced consultation
        
        # Active coordinations
        self.active_coordinations: Dict[str, CoordinationResult] = {}
        
        logger.info(f"Multi-Brain Coordinator v{self.version} initialized with advanced SME orchestration")
    
    async def coordinate_request(self, user_message: str, 
                               context: Optional[Dict] = None) -> CoordinationResult:
        """
        Coordinate a user request across multiple brains.
        
        Args:
            user_message: The user's natural language request
            context: Optional context information
            
        Returns:
            CoordinationResult with comprehensive analysis and decision
        """
        start_time = datetime.now()
        coordination_id = f"coord_{int(start_time.timestamp())}"
        
        try:
            logger.info(f"Starting multi-brain coordination: {coordination_id}")
            
            # Initialize coordination result
            result = CoordinationResult(
                coordination_id=coordination_id,
                user_message=user_message,
                timestamp=start_time,
                intent_result=None,
                technical_result=None,
                sme_results={},
                final_decision=DecisionStatus.REQUIRES_REVIEW,
                aggregated_confidence=0.0,
                recommended_actions=[],
                risk_assessment={},
                execution_plan=None,
                resource_requirements=[],
                estimated_duration=None,
                coordination_time=0.0,
                participating_brains=[],
                confidence_breakdown={}
            )
            
            self.active_coordinations[coordination_id] = result
            
            # Phase 1: Intent Analysis
            logger.info(f"Phase 1: Intent Analysis - {coordination_id}")
            intent_result = await self._coordinate_intent_analysis(user_message, context)
            result.intent_result = intent_result
            result.participating_brains.append("intent_brain")
            
            if not intent_result or intent_result.get("overall_confidence", 0) < 0.3:
                logger.warning(f"Intent analysis failed or low confidence - {coordination_id}")
                result.final_decision = DecisionStatus.REJECTED
                return self._finalize_coordination(result, start_time)
            
            # Phase 2: Technical Planning
            logger.info(f"Phase 2: Technical Planning - {coordination_id}")
            technical_result = await self._coordinate_technical_planning(intent_result, context)
            result.technical_result = technical_result
            if technical_result:
                result.participating_brains.append("technical_brain")
            
            # Phase 3: SME Consultation (if needed)
            if intent_result.get("overall_confidence", 0) >= self.sme_consultation_threshold:
                logger.info(f"Phase 3: SME Consultation - {coordination_id}")
                sme_results = await self._coordinate_sme_consultation(intent_result, technical_result)
                result.sme_results = sme_results
                result.participating_brains.extend(sme_results.keys())
            
            # Phase 4: Confidence Aggregation
            logger.info(f"Phase 4: Confidence Aggregation - {coordination_id}")
            aggregated_confidence, confidence_breakdown = self._aggregate_confidence(
                intent_result, technical_result, result.sme_results
            )
            result.aggregated_confidence = aggregated_confidence
            result.confidence_breakdown = confidence_breakdown
            
            # Phase 5: Final Decision
            logger.info(f"Phase 5: Final Decision - {coordination_id}")
            final_decision = self._make_final_decision(result)
            result.final_decision = final_decision
            
            # Phase 6: Execution Planning (if approved)
            if final_decision == DecisionStatus.APPROVED:
                logger.info(f"Phase 6: Execution Planning - {coordination_id}")
                execution_plan = await self._create_execution_plan(result)
                result.execution_plan = execution_plan
            
            # Generate recommendations and risk assessment
            result.recommended_actions = self._generate_recommendations(result)
            result.risk_assessment = self._assess_coordination_risk(result)
            
            return self._finalize_coordination(result, start_time)
            
        except Exception as e:
            logger.error(f"Multi-brain coordination failed: {e}")
            coordination_time = (datetime.now() - start_time).total_seconds()
            
            # Return error result
            return CoordinationResult(
                coordination_id=coordination_id,
                user_message=user_message,
                timestamp=start_time,
                intent_result=None,
                technical_result=None,
                sme_results={},
                final_decision=DecisionStatus.REJECTED,
                aggregated_confidence=0.0,
                recommended_actions=["Manual review required due to coordination error"],
                risk_assessment={"error": str(e), "risk_level": "HIGH"},
                execution_plan=None,
                resource_requirements=["Manual intervention"],
                estimated_duration=None,
                coordination_time=coordination_time,
                participating_brains=[],
                confidence_breakdown={}
            )
    
    async def _coordinate_intent_analysis(self, user_message: str, 
                                        context: Optional[Dict]) -> Optional[Dict[str, Any]]:
        """Coordinate with Intent Brain for analysis."""
        try:
            if not self.brain_registry:
                logger.warning("No brain registry available for intent analysis")
                return None
            
            intent_brain = self.brain_registry.get_brain("intent_brain")
            if not intent_brain:
                logger.warning("Intent Brain not available")
                return None
            
            # Analyze intent
            intent_result = await intent_brain.analyze_intent(user_message, context)
            
            # Convert to dictionary for coordination
            if hasattr(intent_brain, 'to_dict'):
                return intent_brain.to_dict(intent_result)
            else:
                # Fallback conversion
                return {
                    "intent_id": getattr(intent_result, 'intent_id', 'unknown'),
                    "overall_confidence": getattr(intent_result, 'overall_confidence', 0.0),
                    "intent_summary": getattr(intent_result, 'intent_summary', 'Unknown intent'),
                    "technical_requirements": getattr(intent_result, 'technical_requirements', []),
                    "risk_level": getattr(intent_result, 'risk_level', 'MEDIUM')
                }
                
        except Exception as e:
            logger.error(f"Intent analysis coordination failed: {e}")
            return None
    
    async def _coordinate_technical_planning(self, intent_result: Dict[str, Any],
                                           context: Optional[Dict]) -> Optional[Dict[str, Any]]:
        """Coordinate with Technical Brain for execution planning."""
        try:
            if not self.brain_registry:
                logger.warning("No brain registry available for technical planning")
                return None
            
            technical_brain = self.brain_registry.get_brain("technical_brain")
            if not technical_brain:
                logger.warning("Technical Brain not available")
                return None
            
            # Plan technical execution
            technical_result = await technical_brain.plan_execution(intent_result, context)
            return technical_result
            
        except Exception as e:
            logger.error(f"Technical planning coordination failed: {e}")
            return None
    
    async def _coordinate_sme_consultation(self, intent_result: Dict[str, Any],
                                         technical_result: Optional[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Coordinate with relevant SME Brains for domain expertise using advanced orchestration."""
        sme_results = {}
        
        try:
            # Use advanced SME orchestrator if available
            if self.advanced_sme_orchestrator:
                return await self._advanced_sme_consultation(intent_result, technical_result)
            
            # Fallback to legacy SME consultation
            return await self._legacy_sme_consultation(intent_result, technical_result)
            
        except Exception as e:
            logger.error(f"SME consultation coordination failed: {e}")
            return sme_results
    
    async def _advanced_sme_consultation(self, intent_result: Dict[str, Any],
                                       technical_result: Optional[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Advanced SME consultation using the new orchestrator."""
        try:
            # Determine consultation strategy based on intent complexity
            consultation_pattern = self._determine_consultation_pattern(intent_result, technical_result)
            
            # Identify target domains and priorities
            target_domains, priority_domains = self._analyze_domain_requirements(intent_result, technical_result)
            
            if not target_domains:
                logger.info("No SME domains identified for consultation")
                return {}
            
            # Create SME query from intent and technical results
            sme_query = self._create_sme_query(intent_result, technical_result)
            
            # Create consultation request
            consultation_request = ConsultationRequest(
                query=sme_query,
                pattern=consultation_pattern,
                target_domains=target_domains,
                priority_domains=priority_domains,
                context_sharing=True,
                max_consultation_time=int(self.max_coordination_time * 0.7),  # 70% of total time
                require_consensus=consultation_pattern == ConsultationPattern.COLLABORATIVE
            )
            
            # Execute advanced consultation
            consultation_result = await self.advanced_sme_orchestrator.orchestrate_consultation(consultation_request)
            
            # Convert consultation result to legacy format for compatibility
            return self._convert_consultation_result(consultation_result)
            
        except Exception as e:
            logger.error(f"Advanced SME consultation failed: {e}")
            # Fallback to legacy consultation
            return await self._legacy_sme_consultation(intent_result, technical_result)
    
    async def _legacy_sme_consultation(self, intent_result: Dict[str, Any],
                                     technical_result: Optional[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Legacy SME consultation method for fallback."""
        sme_results = {}
        
        try:
            if not self.brain_registry:
                logger.warning("No brain registry available for SME consultation")
                return sme_results
            
            # Determine which SME brains to consult
            required_smes = self._identify_required_smes(intent_result, technical_result)
            
            # Consult each relevant SME brain
            for sme_type in required_smes:
                sme_brain = self.brain_registry.get_brain(f"{sme_type}_sme")
                if sme_brain:
                    try:
                        sme_result = await sme_brain.provide_expertise(intent_result, technical_result)
                        sme_results[f"{sme_type}_sme"] = sme_result
                    except Exception as e:
                        logger.warning(f"SME consultation failed for {sme_type}: {e}")
                        sme_results[f"{sme_type}_sme"] = {
                            "error": str(e),
                            "confidence": 0.0,
                            "recommendations": []
                        }
            
            return sme_results
            
        except Exception as e:
            logger.error(f"Legacy SME consultation failed: {e}")
            return sme_results
    
    def _identify_required_smes(self, intent_result: Dict[str, Any],
                              technical_result: Optional[Dict[str, Any]]) -> List[str]:
        """Identify which SME brains should be consulted."""
        required_smes = []
        
        # Analyze technical requirements for SME needs
        technical_requirements = intent_result.get("technical_requirements", [])
        
        for requirement in technical_requirements:
            requirement_lower = requirement.lower()
            
            if any(keyword in requirement_lower for keyword in ["container", "docker", "kubernetes"]):
                required_smes.append("container")
            
            if any(keyword in requirement_lower for keyword in ["security", "firewall", "certificate"]):
                required_smes.append("security")
            
            if any(keyword in requirement_lower for keyword in ["network", "routing", "dns"]):
                required_smes.append("network")
            
            if any(keyword in requirement_lower for keyword in ["database", "sql", "mysql", "postgres"]):
                required_smes.append("database")
            
            if any(keyword in requirement_lower for keyword in ["cloud", "aws", "azure", "gcp"]):
                required_smes.append("cloud")
            
            if any(keyword in requirement_lower for keyword in ["monitor", "alert", "metric"]):
                required_smes.append("monitoring")
        
        # Remove duplicates
        return list(set(required_smes))
    
    def _aggregate_confidence(self, intent_result: Optional[Dict[str, Any]],
                            technical_result: Optional[Dict[str, Any]],
                            sme_results: Dict[str, Dict[str, Any]]) -> Tuple[float, Dict[str, float]]:
        """Aggregate confidence scores from all participating brains."""
        confidence_scores = {}
        
        # Intent Brain confidence
        if intent_result:
            confidence_scores["intent_brain"] = intent_result.get("overall_confidence", 0.0)
        
        # Technical Brain confidence
        if technical_result:
            confidence_scores["technical_brain"] = technical_result.get("confidence", 0.0)
        
        # SME Brain confidences
        for sme_name, sme_result in sme_results.items():
            confidence_scores[sme_name] = sme_result.get("confidence", 0.0)
        
        # Calculate weighted average
        if not confidence_scores:
            return 0.0, {}
        
        # Weights: Intent Brain (40%), Technical Brain (30%), SME Brains (30% total)
        total_weight = 0.0
        weighted_sum = 0.0
        
        # Intent Brain weight
        if "intent_brain" in confidence_scores:
            weight = 0.4
            weighted_sum += confidence_scores["intent_brain"] * weight
            total_weight += weight
        
        # Technical Brain weight
        if "technical_brain" in confidence_scores:
            weight = 0.3
            weighted_sum += confidence_scores["technical_brain"] * weight
            total_weight += weight
        
        # SME Brains weight (distributed equally among participating SMEs)
        sme_count = len([k for k in confidence_scores.keys() if k.endswith("_sme")])
        if sme_count > 0:
            sme_weight_each = 0.3 / sme_count
            for sme_name in confidence_scores:
                if sme_name.endswith("_sme"):
                    weighted_sum += confidence_scores[sme_name] * sme_weight_each
                    total_weight += sme_weight_each
        
        # Calculate final aggregated confidence
        aggregated_confidence = weighted_sum / total_weight if total_weight > 0 else 0.0
        
        return aggregated_confidence, confidence_scores
    
    def _make_final_decision(self, result: CoordinationResult) -> DecisionStatus:
        """Make final decision based on aggregated analysis."""
        confidence = result.aggregated_confidence
        
        # High confidence - approve
        if confidence >= self.min_confidence_threshold:
            return DecisionStatus.APPROVED
        
        # Very low confidence - reject
        if confidence < self.escalation_threshold:
            return DecisionStatus.REJECTED
        
        # Medium confidence - requires review
        if confidence >= self.escalation_threshold:
            # Check for high-risk factors
            intent_result = result.intent_result or {}
            risk_level = intent_result.get("risk_level", "MEDIUM")
            
            if risk_level == "HIGH":
                return DecisionStatus.ESCALATED
            else:
                return DecisionStatus.REQUIRES_REVIEW
        
        return DecisionStatus.REQUIRES_REVIEW
    
    async def _create_execution_plan(self, result: CoordinationResult) -> Optional[Dict[str, Any]]:
        """Create detailed execution plan for approved requests."""
        try:
            execution_plan = {
                "plan_id": f"exec_{result.coordination_id}",
                "created_at": datetime.now().isoformat(),
                "status": "ready",
                "phases": [],
                "estimated_duration": 0.0,
                "resource_requirements": [],
                "risk_mitigation": []
            }
            
            # Add phases from technical result
            if result.technical_result:
                technical_phases = result.technical_result.get("execution_phases", [])
                execution_plan["phases"].extend(technical_phases)
                execution_plan["estimated_duration"] += result.technical_result.get("estimated_duration", 0.0)
            
            # Add SME-specific phases
            for sme_name, sme_result in result.sme_results.items():
                sme_phases = sme_result.get("execution_phases", [])
                for phase in sme_phases:
                    phase["sme_brain"] = sme_name
                execution_plan["phases"].extend(sme_phases)
                execution_plan["estimated_duration"] += sme_result.get("estimated_duration", 0.0)
            
            # Aggregate resource requirements
            all_requirements = set()
            if result.intent_result:
                all_requirements.update(result.intent_result.get("resource_requirements", []))
            if result.technical_result:
                all_requirements.update(result.technical_result.get("resource_requirements", []))
            for sme_result in result.sme_results.values():
                all_requirements.update(sme_result.get("resource_requirements", []))
            
            execution_plan["resource_requirements"] = list(all_requirements)
            result.resource_requirements = list(all_requirements)
            result.estimated_duration = execution_plan["estimated_duration"]
            
            return execution_plan
            
        except Exception as e:
            logger.error(f"Execution plan creation failed: {e}")
            return None
    
    def _generate_recommendations(self, result: CoordinationResult) -> List[str]:
        """Generate recommendations based on coordination results."""
        recommendations = []
        
        # Decision-based recommendations
        if result.final_decision == DecisionStatus.APPROVED:
            recommendations.append("Proceed with automated execution")
            if result.aggregated_confidence < 0.8:
                recommendations.append("Monitor execution closely due to moderate confidence")
        
        elif result.final_decision == DecisionStatus.REQUIRES_REVIEW:
            recommendations.append("Manual review recommended before execution")
            recommendations.append("Consider additional validation steps")
        
        elif result.final_decision == DecisionStatus.ESCALATED:
            recommendations.append("Escalate to senior technical staff")
            recommendations.append("Conduct thorough risk assessment")
        
        elif result.final_decision == DecisionStatus.REJECTED:
            recommendations.append("Request requires clarification or modification")
            recommendations.append("Consider alternative approaches")
        
        # Risk-based recommendations
        if result.intent_result:
            risk_level = result.intent_result.get("risk_level", "MEDIUM")
            if risk_level == "HIGH":
                recommendations.append("Implement additional safety measures")
                recommendations.append("Prepare rollback procedures")
        
        # SME-specific recommendations
        for sme_name, sme_result in result.sme_results.items():
            sme_recommendations = sme_result.get("recommendations", [])
            for rec in sme_recommendations:
                recommendations.append(f"{sme_name}: {rec}")
        
        return recommendations
    
    def _assess_coordination_risk(self, result: CoordinationResult) -> Dict[str, Any]:
        """Assess overall risk of the coordination decision."""
        risk_assessment = {
            "overall_risk": "MEDIUM",
            "risk_factors": [],
            "mitigation_strategies": []
        }
        
        # Confidence-based risk
        if result.aggregated_confidence < 0.5:
            risk_assessment["risk_factors"].append("Low confidence in analysis")
            risk_assessment["mitigation_strategies"].append("Require manual validation")
        
        # Intent-based risk
        if result.intent_result:
            intent_risk = result.intent_result.get("risk_level", "MEDIUM")
            if intent_risk == "HIGH":
                risk_assessment["overall_risk"] = "HIGH"
                risk_assessment["risk_factors"].append("High-risk intent classification")
        
        # SME-identified risks
        for sme_name, sme_result in result.sme_results.items():
            sme_risks = sme_result.get("risk_factors", [])
            for risk in sme_risks:
                risk_assessment["risk_factors"].append(f"{sme_name}: {risk}")
        
        # Determine overall risk level
        high_risk_indicators = len([r for r in risk_assessment["risk_factors"] if "high" in r.lower()])
        if high_risk_indicators > 0 or result.aggregated_confidence < 0.4:
            risk_assessment["overall_risk"] = "HIGH"
        elif result.aggregated_confidence > 0.8 and not risk_assessment["risk_factors"]:
            risk_assessment["overall_risk"] = "LOW"
        
        return risk_assessment
    
    def _extract_sme_brains(self, brain_registry) -> Dict[str, Any]:
        """Extract SME brains from brain registry for advanced orchestrator."""
        sme_brains = {}
        
        try:
            # Get all available brains
            all_brains = brain_registry.get_all_brains() if hasattr(brain_registry, 'get_all_brains') else {}
            
            # Filter SME brains
            for brain_name, brain_instance in all_brains.items():
                if 'sme' in brain_name.lower() and hasattr(brain_instance, 'provide_expertise'):
                    # Extract domain name from brain name (e.g., "container_sme" -> "container_orchestration")
                    domain_mapping = {
                        'container_sme': 'container_orchestration',
                        'security_sme': 'security_and_compliance',
                        'network_sme': 'network_infrastructure',
                        'database_sme': 'database_administration',
                        'cloud_sme': 'cloud_services',
                        'monitoring_sme': 'observability_monitoring'
                    }
                    
                    domain = domain_mapping.get(brain_name, brain_name.replace('_sme', ''))
                    sme_brains[domain] = brain_instance
            
            logger.info(f"Extracted {len(sme_brains)} SME brains for advanced orchestration")
            return sme_brains
            
        except Exception as e:
            logger.error(f"Failed to extract SME brains: {e}")
            return {}
    
    def _determine_consultation_pattern(self, intent_result: Dict[str, Any], 
                                      technical_result: Optional[Dict[str, Any]]) -> ConsultationPattern:
        """Determine the best consultation pattern based on intent complexity."""
        
        # Analyze complexity factors
        complexity_score = 0
        
        # Intent complexity
        technical_requirements = intent_result.get("technical_requirements", [])
        complexity_score += len(technical_requirements) * 0.2
        
        # Risk level
        risk_level = intent_result.get("risk_level", "MEDIUM")
        if risk_level == "HIGH":
            complexity_score += 0.5
        elif risk_level == "CRITICAL":
            complexity_score += 1.0
        
        # Technical complexity
        if technical_result:
            execution_steps = technical_result.get("execution_steps", [])
            complexity_score += len(execution_steps) * 0.1
            
            if technical_result.get("requires_coordination", False):
                complexity_score += 0.3
        
        # Determine pattern based on complexity
        if complexity_score >= 1.5:
            return ConsultationPattern.COLLABORATIVE  # High complexity - need collaboration
        elif complexity_score >= 1.0:
            return ConsultationPattern.HIERARCHICAL   # Medium-high complexity - prioritized consultation
        elif complexity_score >= 0.5:
            return ConsultationPattern.SEQUENTIAL     # Medium complexity - sequential with context
        else:
            return ConsultationPattern.PARALLEL       # Low complexity - parallel consultation
    
    def _analyze_domain_requirements(self, intent_result: Dict[str, Any], 
                                   technical_result: Optional[Dict[str, Any]]) -> Tuple[List[str], Dict[str, ConsultationPriority]]:
        """Analyze domain requirements and priorities."""
        
        target_domains = []
        priority_domains = {}
        
        # Analyze technical requirements
        technical_requirements = intent_result.get("technical_requirements", [])
        
        for requirement in technical_requirements:
            requirement_lower = requirement.lower()
            
            # Container/orchestration requirements
            if any(keyword in requirement_lower for keyword in ["container", "docker", "kubernetes", "orchestration"]):
                target_domains.append("container_orchestration")
                priority_domains["container_orchestration"] = ConsultationPriority.HIGH
            
            # Security requirements
            if any(keyword in requirement_lower for keyword in ["security", "firewall", "certificate", "encryption", "compliance"]):
                target_domains.append("security_and_compliance")
                priority_domains["security_and_compliance"] = ConsultationPriority.CRITICAL
            
            # Network requirements
            if any(keyword in requirement_lower for keyword in ["network", "routing", "dns", "load", "proxy"]):
                target_domains.append("network_infrastructure")
                priority_domains["network_infrastructure"] = ConsultationPriority.HIGH
            
            # Database requirements
            if any(keyword in requirement_lower for keyword in ["database", "sql", "nosql", "data", "storage"]):
                target_domains.append("database_administration")
                priority_domains["database_administration"] = ConsultationPriority.HIGH
            
            # Cloud requirements
            if any(keyword in requirement_lower for keyword in ["cloud", "aws", "azure", "gcp", "scaling"]):
                target_domains.append("cloud_services")
                priority_domains["cloud_services"] = ConsultationPriority.MEDIUM
            
            # Monitoring requirements
            if any(keyword in requirement_lower for keyword in ["monitor", "alert", "log", "metric", "observability"]):
                target_domains.append("observability_monitoring")
                priority_domains["observability_monitoring"] = ConsultationPriority.MEDIUM
        
        # Remove duplicates while preserving order
        target_domains = list(dict.fromkeys(target_domains))
        
        # If no specific domains identified, use general consultation
        if not target_domains:
            # Default to most common domains for general consultation
            target_domains = ["security_and_compliance", "network_infrastructure", "observability_monitoring"]
            priority_domains = {
                "security_and_compliance": ConsultationPriority.HIGH,
                "network_infrastructure": ConsultationPriority.MEDIUM,
                "observability_monitoring": ConsultationPriority.LOW
            }
        
        return target_domains, priority_domains
    
    def _create_sme_query(self, intent_result: Dict[str, Any], 
                         technical_result: Optional[Dict[str, Any]]) -> SMEQuery:
        """Create SME query from intent and technical results."""
        
        # Build query text
        intent_summary = intent_result.get("intent_summary", "Unknown request")
        query_text = f"Intent: {intent_summary}"
        
        # Add technical requirements if available
        technical_requirements = intent_result.get("technical_requirements", [])
        if technical_requirements:
            query_text += f"\nTechnical Requirements: {', '.join(technical_requirements)}"
        
        # Build context
        context = {
            "intent_result": intent_result,
            "technical_result": technical_result,
            "coordination_timestamp": datetime.now().isoformat(),
            "coordination_id": intent_result.get("intent_id", "unknown")
        }
        
        return SMEQuery(
            query_text=query_text,
            context=context,
            user_id=intent_result.get("user_id", "system"),
            session_id=intent_result.get("session_id", "coordination")
        )
    
    def _convert_consultation_result(self, consultation_result: ConsultationResult) -> Dict[str, Dict[str, Any]]:
        """Convert advanced consultation result to legacy format."""
        
        legacy_results = {}
        
        # Extract primary recommendation
        primary_rec = consultation_result.resolved_recommendation.primary_recommendation
        
        # Create results for each consulted domain
        for domain in consultation_result.consulted_domains:
            legacy_results[f"{domain}_sme"] = {
                "recommendations": primary_rec,
                "confidence": consultation_result.confidence_distribution.get(domain, 0.5),
                "reasoning": consultation_result.resolved_recommendation.reasoning,
                "implementation_steps": consultation_result.resolved_recommendation.implementation_notes,
                "risk_assessment": consultation_result.resolved_recommendation.risk_mitigation,
                "consultation_metadata": {
                    "pattern": consultation_result.consultation_metadata.get("consultation_pattern", "unknown"),
                    "duration": consultation_result.consultation_duration,
                    "consensus_achieved": consultation_result.consensus_achieved
                }
            }
        
        # Add overall consultation metadata
        legacy_results["_consultation_summary"] = {
            "total_domains": len(consultation_result.consulted_domains),
            "consultation_duration": consultation_result.consultation_duration,
            "consensus_achieved": consultation_result.consensus_achieved,
            "resolution_strategy": consultation_result.resolved_recommendation.resolution_strategy.value,
            "overall_confidence": consultation_result.resolved_recommendation.confidence_level.value
        }
        
        return legacy_results
    
    def _finalize_coordination(self, result: CoordinationResult, start_time: datetime) -> CoordinationResult:
        """Finalize coordination and clean up."""
        result.coordination_time = (datetime.now() - start_time).total_seconds()
        
        # Remove from active coordinations
        if result.coordination_id in self.active_coordinations:
            del self.active_coordinations[result.coordination_id]
        
        # Log completion
        logger.info(f"Multi-brain coordination completed: {result.coordination_id} - "
                   f"Decision: {result.final_decision.value}, "
                   f"Confidence: {result.aggregated_confidence:.2%}, "
                   f"Time: {result.coordination_time:.2f}s")
        
        # Learn from coordination if learning engine is available
        if self.learning_engine:
            asyncio.create_task(self._learn_from_coordination(result))
        
        return result
    
    async def _learn_from_coordination(self, result: CoordinationResult):
        """Learn from coordination results."""
        try:
            learning_data = {
                "coordination_result": {
                    "decision": result.final_decision.value,
                    "confidence": result.aggregated_confidence,
                    "coordination_time": result.coordination_time,
                    "participating_brains": result.participating_brains,
                    "confidence_breakdown": result.confidence_breakdown
                }
            }
            
            await self.learning_engine.process_execution_feedback(
                learning_data, "multi_brain_coordinator"
            )
            
        except Exception as e:
            logger.warning(f"Learning from coordination failed: {e}")
    
    async def get_coordination_status(self) -> Dict[str, Any]:
        """Get current coordination system status."""
        return {
            "coordinator_id": self.coordinator_id,
            "version": self.version,
            "active_coordinations": len(self.active_coordinations),
            "configuration": {
                "min_confidence_threshold": self.min_confidence_threshold,
                "sme_consultation_threshold": self.sme_consultation_threshold,
                "escalation_threshold": self.escalation_threshold,
                "max_coordination_time": self.max_coordination_time
            },
            "available_brains": (
                list(self.brain_registry.get_registered_brains().keys()) 
                if self.brain_registry else []
            )
        }