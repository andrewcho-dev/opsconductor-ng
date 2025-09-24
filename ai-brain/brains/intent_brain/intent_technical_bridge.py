"""
Intent-to-Technical Bridge - 4W Framework Integration

This module bridges the 4W Framework Intent Brain output with the Technical Brain input,
translating systematic 4W analysis into technical execution requirements.

Key Functions:
1. Convert 4W Framework analysis to Technical Brain compatible format
2. Map resource complexity to technical complexity
3. Translate action types to technical methods
4. Preserve all 4W analysis data for enhanced technical planning
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import asdict

from .four_w_analyzer import FourWAnalysis, ActionType, ScopeLevel, UrgencyLevel, MethodType

logger = logging.getLogger(__name__)

class IntentTechnicalBridge:
    """
    Bridge between 4W Framework Intent Brain and Technical Brain
    
    Converts FourWAnalysis output into Technical Brain compatible input format
    while preserving the rich 4W analysis data for enhanced technical planning.
    """
    
    def __init__(self):
        """Initialize the Intent-to-Technical bridge."""
        self.bridge_version = "1.0.0"
        self.conversion_history = []
        
        # Mapping tables for 4W to Technical Brain conversion
        self.action_to_itil_mapping = self._build_action_to_itil_mapping()
        self.complexity_mapping = self._build_complexity_mapping()
        self.method_mapping = self._build_method_mapping()
        
        logger.info("Intent-to-Technical Bridge initialized")
    
    def convert_4w_to_technical_input(self, four_w_analysis: FourWAnalysis) -> Dict[str, Any]:
        """
        Convert 4W Framework analysis to Technical Brain compatible input.
        
        Args:
            four_w_analysis: Complete 4W Framework analysis result
            
        Returns:
            Dict compatible with Technical Brain create_execution_plan() method
        """
        try:
            logger.info(f"Converting 4W analysis to Technical Brain input")
            
            # Extract core 4W components
            what_analysis = four_w_analysis.what_analysis
            where_what_analysis = four_w_analysis.where_what_analysis
            when_analysis = four_w_analysis.when_analysis
            how_analysis = four_w_analysis.how_analysis
            
            # Convert to Technical Brain format
            technical_input = {
                # Core Technical Brain expected fields
                "itil_service_type": self._map_action_to_itil(what_analysis.action_type),
                "business_intent": what_analysis.root_need,
                "technical_requirements": self._extract_technical_requirements(four_w_analysis),
                "urgency_level": when_analysis.urgency.value,
                "scope_level": where_what_analysis.scope_level.value,
                "execution_method_preference": how_analysis.method_preference.value,
                
                # Enhanced fields from 4W analysis
                "four_w_analysis": {
                    "what": {
                        "action_type": what_analysis.action_type.value,
                        "specific_outcome": what_analysis.specific_outcome,
                        "root_need": what_analysis.root_need,
                        "surface_request": what_analysis.surface_request,
                        "confidence": what_analysis.confidence
                    },
                    "where_what": {
                        "target_systems": where_what_analysis.target_systems,
                        "scope_level": where_what_analysis.scope_level.value,
                        "affected_components": where_what_analysis.affected_components,
                        "dependencies": where_what_analysis.dependencies,
                        "confidence": where_what_analysis.confidence
                    },
                    "when": {
                        "urgency": when_analysis.urgency.value,
                        "timeline_type": when_analysis.timeline_type.value,
                        "specific_timeline": when_analysis.specific_timeline,
                        "scheduling_constraints": when_analysis.scheduling_constraints,
                        "business_hours_required": when_analysis.business_hours_required,
                        "confidence": when_analysis.confidence
                    },
                    "how": {
                        "method_preference": how_analysis.method_preference.value,
                        "execution_constraints": how_analysis.execution_constraints,
                        "approval_required": how_analysis.approval_required,
                        "rollback_needed": how_analysis.rollback_needed,
                        "testing_required": how_analysis.testing_required,
                        "confidence": how_analysis.confidence
                    }
                },
                
                # Resource and risk assessment from 4W
                "resource_complexity": four_w_analysis.resource_complexity,
                "estimated_effort": four_w_analysis.estimated_effort,
                "required_capabilities": four_w_analysis.required_capabilities,
                "risk_level": four_w_analysis.risk_level,
                "risk_factors": four_w_analysis.risk_factors,
                
                # Analysis metadata
                "overall_confidence": four_w_analysis.overall_confidence,
                "missing_information": four_w_analysis.missing_information,
                "clarifying_questions": four_w_analysis.clarifying_questions,
                "analysis_timestamp": four_w_analysis.analysis_timestamp.isoformat(),
                "processing_time": four_w_analysis.processing_time,
                
                # Bridge metadata
                "bridge_version": self.bridge_version,
                "conversion_timestamp": datetime.now().isoformat()
            }
            
            # Log conversion summary
            logger.info(f"4W to Technical conversion completed:")
            logger.info(f"  - Action Type: {what_analysis.action_type.value} → ITIL: {technical_input['itil_service_type']}")
            logger.info(f"  - Resource Complexity: {four_w_analysis.resource_complexity}")
            logger.info(f"  - Overall Confidence: {four_w_analysis.overall_confidence:.2%}")
            
            # Store conversion history
            self.conversion_history.append({
                "timestamp": datetime.now(),
                "four_w_confidence": four_w_analysis.overall_confidence,
                "itil_service_type": technical_input["itil_service_type"],
                "resource_complexity": four_w_analysis.resource_complexity
            })
            
            return technical_input
            
        except Exception as e:
            logger.error(f"Error converting 4W analysis to Technical Brain input: {e}")
            # NO FALLBACK - FAIL HARD AS REQUESTED
            raise Exception(f"4W to Technical Brain conversion FAILED - NO FALLBACKS ALLOWED: {e}")
    
    def _map_action_to_itil(self, action_type: ActionType) -> str:
        """Map 4W action type to ITIL service type."""
        return self.action_to_itil_mapping.get(action_type, "service_request")
    
    def _extract_technical_requirements(self, four_w_analysis: FourWAnalysis) -> List[str]:
        """Extract technical requirements from 4W analysis."""
        requirements = []
        
        # From target systems
        requirements.extend(four_w_analysis.where_what_analysis.target_systems)
        
        # From affected components
        requirements.extend(four_w_analysis.where_what_analysis.affected_components)
        
        # From required capabilities
        requirements.extend(four_w_analysis.required_capabilities)
        
        # From execution constraints
        requirements.extend(four_w_analysis.how_analysis.execution_constraints)
        
        # Add scope-based requirements
        scope_level = four_w_analysis.where_what_analysis.scope_level
        if scope_level == ScopeLevel.ORG_WIDE:
            requirements.append("organization_wide_coordination")
        elif scope_level == ScopeLevel.ENVIRONMENT:
            requirements.append("environment_management")
        elif scope_level == ScopeLevel.CLUSTER:
            requirements.append("cluster_coordination")
        
        # Add method-based requirements
        method_pref = four_w_analysis.how_analysis.method_preference
        if method_pref == MethodType.AUTOMATED:
            requirements.append("automation_capability")
        elif method_pref == MethodType.MANUAL:
            requirements.append("manual_execution")
        elif method_pref == MethodType.HYBRID:
            requirements.append("hybrid_execution")
        
        # Remove duplicates and empty strings
        return list(set(req for req in requirements if req))
    
    def _build_action_to_itil_mapping(self) -> Dict[ActionType, str]:
        """Build mapping from 4W action types to ITIL service types."""
        return {
            ActionType.INFORMATION: "information_request",
            ActionType.OPERATIONAL: "service_request", 
            ActionType.DIAGNOSTIC: "incident_management",
            ActionType.PROVISIONING: "service_request"
        }
    
    def _build_complexity_mapping(self) -> Dict[str, str]:
        """Build mapping from 4W resource complexity to Technical Brain complexity."""
        return {
            "LOW": "simple",
            "MEDIUM": "moderate", 
            "HIGH": "complex"
        }
    
    def _build_method_mapping(self) -> Dict[MethodType, List[str]]:
        """Build mapping from 4W method preferences to technical methods."""
        return {
            MethodType.AUTOMATED: ["automation_orchestration", "script_execution"],
            MethodType.MANUAL: ["manual_procedures", "guided_execution"],
            MethodType.GUIDED: ["assisted_execution", "step_by_step_guidance"],
            MethodType.HYBRID: ["hybrid_orchestration", "semi_automated_execution"]
        }
    

    
    def get_conversion_stats(self) -> Dict[str, Any]:
        """Get statistics about 4W to Technical conversions."""
        if not self.conversion_history:
            return {"total_conversions": 0}
        
        total = len(self.conversion_history)
        avg_confidence = sum(conv["four_w_confidence"] for conv in self.conversion_history) / total
        
        itil_types = {}
        complexity_levels = {}
        
        for conv in self.conversion_history:
            itil_type = conv["itil_service_type"]
            complexity = conv["resource_complexity"]
            
            itil_types[itil_type] = itil_types.get(itil_type, 0) + 1
            complexity_levels[complexity] = complexity_levels.get(complexity, 0) + 1
        
        return {
            "total_conversions": total,
            "average_confidence": avg_confidence,
            "itil_service_types": itil_types,
            "resource_complexity_distribution": complexity_levels,
            "bridge_version": self.bridge_version
        }