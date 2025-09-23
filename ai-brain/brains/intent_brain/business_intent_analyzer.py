"""
Business Intent Analyzer

This module analyzes the business intent behind user requests, understanding
the desired outcomes and business value of IT operations.
"""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
import re

logger = logging.getLogger(__name__)

class BusinessOutcome(Enum):
    """Business Outcomes for IT Operations"""
    COST_REDUCTION = "cost_reduction"
    PERFORMANCE_IMPROVEMENT = "performance_improvement"
    AVAILABILITY_ENHANCEMENT = "availability_enhancement"
    SECURITY_STRENGTHENING = "security_strengthening"
    COMPLIANCE_ADHERENCE = "compliance_adherence"
    SCALABILITY_IMPROVEMENT = "scalability_improvement"
    OPERATIONAL_EFFICIENCY = "operational_efficiency"
    RISK_MITIGATION = "risk_mitigation"
    INNOVATION_ENABLEMENT = "innovation_enablement"
    CUSTOMER_SATISFACTION = "customer_satisfaction"

class BusinessPriority(Enum):
    """Business Priority Levels"""
    STRATEGIC = "strategic"
    TACTICAL = "tactical"
    OPERATIONAL = "operational"
    MAINTENANCE = "maintenance"

@dataclass
class BusinessIntent:
    """Business Intent Analysis Result"""
    primary_outcome: BusinessOutcome
    secondary_outcomes: List[BusinessOutcome]
    business_priority: BusinessPriority
    value_proposition: str
    success_criteria: List[str]
    stakeholders: List[str]
    business_risk: str
    roi_indicators: List[str]
    confidence: float
    reasoning: str

class BusinessIntentAnalyzer:
    """
    Analyzes the business intent and desired outcomes behind IT requests.
    
    This analyzer helps understand WHY a request is being made from a business
    perspective, enabling better prioritization and resource allocation.
    """
    
    def __init__(self):
        """Initialize the business intent analyzer."""
        self.outcome_patterns = self._build_outcome_patterns()
        self.priority_indicators = self._build_priority_indicators()
        self.stakeholder_patterns = self._build_stakeholder_patterns()
        self.value_indicators = self._build_value_indicators()
    
    def _build_outcome_patterns(self) -> Dict[BusinessOutcome, Dict[str, Any]]:
        """Build patterns for identifying business outcomes."""
        return {
            BusinessOutcome.COST_REDUCTION: {
                "keywords": [
                    "cost", "save", "reduce", "optimize", "efficient", "budget",
                    "cheaper", "economical", "resource optimization"
                ],
                "patterns": [
                    r"(?i)(reduce|save|cut).*(cost|expense|budget)",
                    r"(?i)(optimize|improve).*(efficiency|resource)",
                    r"(?i)(cheaper|economical|cost-effective)"
                ],
                "value_prop": "Reduce operational costs and improve resource efficiency"
            },
            BusinessOutcome.PERFORMANCE_IMPROVEMENT: {
                "keywords": [
                    "performance", "speed", "faster", "optimize", "improve",
                    "response time", "throughput", "latency"
                ],
                "patterns": [
                    r"(?i)(improve|increase|boost).*(performance|speed)",
                    r"(?i)(faster|quicker|reduce).*(response|latency)",
                    r"(?i)(optimize|enhance).*(throughput|processing)"
                ],
                "value_prop": "Enhance system performance and user experience"
            },
            BusinessOutcome.AVAILABILITY_ENHANCEMENT: {
                "keywords": [
                    "availability", "uptime", "reliability", "stable", "resilient",
                    "fault tolerance", "disaster recovery", "backup"
                ],
                "patterns": [
                    r"(?i)(improve|increase).*(availability|uptime)",
                    r"(?i)(ensure|maintain).*(reliability|stability)",
                    r"(?i)(disaster recovery|backup|failover)"
                ],
                "value_prop": "Increase system availability and business continuity"
            },
            BusinessOutcome.SECURITY_STRENGTHENING: {
                "keywords": [
                    "security", "secure", "protect", "compliance", "audit",
                    "vulnerability", "threat", "risk", "encryption"
                ],
                "patterns": [
                    r"(?i)(improve|enhance|strengthen).*(security|protection)",
                    r"(?i)(comply|compliance).*(regulation|standard)",
                    r"(?i)(protect|secure).*(data|system|network)"
                ],
                "value_prop": "Strengthen security posture and ensure compliance"
            },
            BusinessOutcome.SCALABILITY_IMPROVEMENT: {
                "keywords": [
                    "scale", "grow", "expand", "capacity", "elastic", "flexible",
                    "accommodate", "handle more"
                ],
                "patterns": [
                    r"(?i)(scale|expand|grow).*(capacity|system|infrastructure)",
                    r"(?i)(handle|accommodate).*(more|additional|increased)",
                    r"(?i)(elastic|flexible|scalable)"
                ],
                "value_prop": "Enable business growth through scalable infrastructure"
            },
            BusinessOutcome.OPERATIONAL_EFFICIENCY: {
                "keywords": [
                    "automate", "streamline", "simplify", "efficient", "process",
                    "workflow", "productivity", "manual"
                ],
                "patterns": [
                    r"(?i)(automate|streamline).*(process|workflow|task)",
                    r"(?i)(reduce|eliminate).*(manual|repetitive)",
                    r"(?i)(improve|increase).*(efficiency|productivity)"
                ],
                "value_prop": "Improve operational efficiency through automation"
            }
        }
    
    def _build_priority_indicators(self) -> Dict[BusinessPriority, List[str]]:
        """Build business priority indicators."""
        return {
            BusinessPriority.STRATEGIC: [
                "strategic", "business critical", "competitive advantage",
                "market opportunity", "digital transformation", "innovation"
            ],
            BusinessPriority.TACTICAL: [
                "project", "initiative", "improvement", "enhancement",
                "optimization", "modernization"
            ],
            BusinessPriority.OPERATIONAL: [
                "daily operations", "routine", "standard", "regular",
                "maintenance", "support"
            ],
            BusinessPriority.MAINTENANCE: [
                "maintenance", "patch", "update", "fix", "repair",
                "housekeeping", "cleanup"
            ]
        }
    
    def _build_stakeholder_patterns(self) -> Dict[str, List[str]]:
        """Build stakeholder identification patterns."""
        return {
            "Executive": ["ceo", "cto", "cio", "executive", "leadership", "board"],
            "Business Users": ["users", "customers", "clients", "business", "department"],
            "IT Operations": ["ops", "operations", "infrastructure", "system admin"],
            "Development": ["developers", "dev team", "engineering", "development"],
            "Security": ["security team", "compliance", "audit", "risk management"],
            "Finance": ["finance", "accounting", "budget", "cost center"]
        }
    
    def _build_value_indicators(self) -> Dict[str, List[str]]:
        """Build value proposition indicators."""
        return {
            "Revenue Impact": ["revenue", "sales", "income", "profit", "customer"],
            "Cost Impact": ["cost", "expense", "budget", "savings", "efficiency"],
            "Risk Impact": ["risk", "compliance", "security", "audit", "regulation"],
            "Operational Impact": ["operations", "productivity", "performance", "availability"]
        }
    
    async def analyze_business_intent(self, user_message: str, 
                                    context: Optional[Dict] = None) -> BusinessIntent:
        """
        Analyze the business intent behind a user request.
        
        Args:
            user_message: The user's natural language request
            context: Optional context information
            
        Returns:
            BusinessIntent with detailed business analysis
        """
        try:
            logger.info(f"Analyzing business intent for message: {user_message[:100]}...")
            
            message_lower = user_message.lower()
            
            # Identify primary business outcome
            primary_outcome, outcome_confidence = self._identify_primary_outcome(message_lower)
            
            # Identify secondary outcomes
            secondary_outcomes = self._identify_secondary_outcomes(message_lower, primary_outcome)
            
            # Determine business priority
            business_priority = self._determine_business_priority(message_lower)
            
            # Generate value proposition
            value_proposition = self._generate_value_proposition(primary_outcome, message_lower)
            
            # Identify success criteria
            success_criteria = self._identify_success_criteria(primary_outcome, message_lower)
            
            # Identify stakeholders
            stakeholders = self._identify_stakeholders(message_lower)
            
            # Assess business risk
            business_risk = self._assess_business_risk(primary_outcome, business_priority)
            
            # Identify ROI indicators
            roi_indicators = self._identify_roi_indicators(primary_outcome, message_lower)
            
            # Generate reasoning
            reasoning = self._generate_reasoning(
                primary_outcome, business_priority, stakeholders, outcome_confidence
            )
            
            business_intent = BusinessIntent(
                primary_outcome=primary_outcome,
                secondary_outcomes=secondary_outcomes,
                business_priority=business_priority,
                value_proposition=value_proposition,
                success_criteria=success_criteria,
                stakeholders=stakeholders,
                business_risk=business_risk,
                roi_indicators=roi_indicators,
                confidence=outcome_confidence,
                reasoning=reasoning
            )
            
            logger.info(f"Business intent analysis completed: {primary_outcome.value}")
            return business_intent
            
        except Exception as e:
            logger.error(f"Error in business intent analysis: {e}")
            # Return default analysis
            return BusinessIntent(
                primary_outcome=BusinessOutcome.OPERATIONAL_EFFICIENCY,
                secondary_outcomes=[],
                business_priority=BusinessPriority.OPERATIONAL,
                value_proposition="Standard IT operational support",
                success_criteria=["Request completed successfully"],
                stakeholders=["IT Operations"],
                business_risk="Low operational risk",
                roi_indicators=["Operational continuity"],
                confidence=0.3,
                reasoning=f"Analysis failed: {str(e)}"
            )
    
    def _identify_primary_outcome(self, message: str) -> tuple[BusinessOutcome, float]:
        """Identify the primary business outcome."""
        best_outcome = BusinessOutcome.OPERATIONAL_EFFICIENCY
        best_confidence = 0.0
        
        for outcome, info in self.outcome_patterns.items():
            confidence = 0.0
            
            # Check keyword matches
            for keyword in info["keywords"]:
                if keyword in message:
                    confidence += 0.1
            
            # Check pattern matches
            for pattern in info["patterns"]:
                if re.search(pattern, message):
                    confidence += 0.3
            
            # Normalize confidence
            confidence = min(confidence, 1.0)
            
            if confidence > best_confidence:
                best_outcome = outcome
                best_confidence = confidence
        
        # Ensure minimum confidence
        if best_confidence < 0.4:
            best_confidence = 0.4
        
        return best_outcome, best_confidence
    
    def _identify_secondary_outcomes(self, message: str, 
                                   primary: BusinessOutcome) -> List[BusinessOutcome]:
        """Identify secondary business outcomes."""
        secondary = []
        
        for outcome, info in self.outcome_patterns.items():
            if outcome == primary:
                continue
                
            confidence = 0.0
            for keyword in info["keywords"]:
                if keyword in message:
                    confidence += 0.1
            
            if confidence >= 0.2:  # Lower threshold for secondary outcomes
                secondary.append(outcome)
        
        return secondary[:2]  # Limit to top 2 secondary outcomes
    
    def _determine_business_priority(self, message: str) -> BusinessPriority:
        """Determine business priority level."""
        for priority, indicators in self.priority_indicators.items():
            for indicator in indicators:
                if indicator in message:
                    return priority
        return BusinessPriority.OPERATIONAL
    
    def _generate_value_proposition(self, outcome: BusinessOutcome, message: str) -> str:
        """Generate value proposition based on outcome."""
        base_value = self.outcome_patterns[outcome]["value_prop"]
        
        # Enhance with specific context from message
        if "critical" in message or "urgent" in message:
            return f"{base_value} with immediate business impact"
        elif "strategic" in message or "competitive" in message:
            return f"{base_value} to support strategic business objectives"
        else:
            return base_value
    
    def _identify_success_criteria(self, outcome: BusinessOutcome, message: str) -> List[str]:
        """Identify success criteria based on outcome."""
        criteria_map = {
            BusinessOutcome.COST_REDUCTION: [
                "Measurable cost savings achieved",
                "Resource utilization improved",
                "Budget targets met"
            ],
            BusinessOutcome.PERFORMANCE_IMPROVEMENT: [
                "Response times improved",
                "Throughput increased",
                "User satisfaction enhanced"
            ],
            BusinessOutcome.AVAILABILITY_ENHANCEMENT: [
                "System uptime increased",
                "Service reliability improved",
                "Business continuity maintained"
            ],
            BusinessOutcome.SECURITY_STRENGTHENING: [
                "Security posture enhanced",
                "Compliance requirements met",
                "Risk exposure reduced"
            ],
            BusinessOutcome.SCALABILITY_IMPROVEMENT: [
                "System capacity increased",
                "Growth requirements supported",
                "Scalability targets achieved"
            ],
            BusinessOutcome.OPERATIONAL_EFFICIENCY: [
                "Process automation implemented",
                "Manual effort reduced",
                "Operational productivity improved"
            ]
        }
        
        return criteria_map.get(outcome, ["Request completed successfully"])
    
    def _identify_stakeholders(self, message: str) -> List[str]:
        """Identify relevant stakeholders."""
        stakeholders = []
        
        for stakeholder_type, patterns in self.stakeholder_patterns.items():
            for pattern in patterns:
                if pattern in message:
                    stakeholders.append(stakeholder_type)
                    break
        
        # Default stakeholders if none identified
        if not stakeholders:
            stakeholders = ["IT Operations"]
        
        return stakeholders
    
    def _assess_business_risk(self, outcome: BusinessOutcome, 
                            priority: BusinessPriority) -> str:
        """Assess business risk level."""
        risk_matrix = {
            (BusinessOutcome.SECURITY_STRENGTHENING, BusinessPriority.STRATEGIC): "High - Security strategic initiative",
            (BusinessOutcome.AVAILABILITY_ENHANCEMENT, BusinessPriority.STRATEGIC): "High - Availability critical to business",
            (BusinessOutcome.COST_REDUCTION, BusinessPriority.STRATEGIC): "Medium - Cost optimization initiative",
            (BusinessOutcome.PERFORMANCE_IMPROVEMENT, BusinessPriority.TACTICAL): "Medium - Performance improvement project",
            (BusinessOutcome.OPERATIONAL_EFFICIENCY, BusinessPriority.OPERATIONAL): "Low - Standard operational request"
        }
        
        return risk_matrix.get((outcome, priority), "Medium - Standard business risk")
    
    def _identify_roi_indicators(self, outcome: BusinessOutcome, message: str) -> List[str]:
        """Identify ROI indicators."""
        roi_map = {
            BusinessOutcome.COST_REDUCTION: [
                "Cost savings per month",
                "Resource utilization improvement",
                "Operational expense reduction"
            ],
            BusinessOutcome.PERFORMANCE_IMPROVEMENT: [
                "Response time improvement",
                "User productivity increase",
                "System throughput enhancement"
            ],
            BusinessOutcome.AVAILABILITY_ENHANCEMENT: [
                "Uptime percentage increase",
                "Downtime cost avoidance",
                "Business continuity value"
            ],
            BusinessOutcome.SECURITY_STRENGTHENING: [
                "Risk reduction value",
                "Compliance cost avoidance",
                "Security incident prevention"
            ]
        }
        
        return roi_map.get(outcome, ["Operational value delivered"])
    
    def _generate_reasoning(self, outcome: BusinessOutcome, priority: BusinessPriority,
                          stakeholders: List[str], confidence: float) -> str:
        """Generate reasoning for the business intent analysis."""
        return (f"Primary business outcome identified as {outcome.value} with {confidence:.1%} confidence. "
                f"Business priority level: {priority.value}. "
                f"Key stakeholders: {', '.join(stakeholders)}. "
                f"Analysis based on business value indicators and stakeholder impact assessment.")