"""
Brain Communication Protocol - Coordinates multi-brain analysis and communication

This module provides the communication framework for coordinating analysis
across all brain components in the Multi-Brain Architecture.
"""

from typing import Dict, List, Any, Optional, Union
import asyncio
from dataclasses import dataclass, field
from enum import Enum
import json
from datetime import datetime

from brains.intent_brain.intent_brain import IntentBrain, IntentAnalysisResult
from brains.technical_brain import TechnicalBrain, TechnicalPlan
from brains.base_sme_brain import SMEBrain, SMEQuery, SMERecommendation


class AnalysisPhase(Enum):
    """Multi-brain analysis phases"""
    INTENT_ANALYSIS = "intent_analysis"
    TECHNICAL_PLANNING = "technical_planning"
    SME_CONSULTATION = "sme_consultation"
    CONFIDENCE_AGGREGATION = "confidence_aggregation"
    STRATEGY_DETERMINATION = "strategy_determination"


class CommunicationStatus(Enum):
    """Communication status between brains"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass
class BrainMessage:
    """Message structure for brain-to-brain communication"""
    sender: str
    receiver: str
    message_type: str
    content: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    correlation_id: str = ""
    priority: int = 1  # 1=high, 2=medium, 3=low


@dataclass
class MultibrainAnalysis:
    """Complete multi-brain analysis result"""
    user_request: str
    intent_analysis: Optional[IntentAnalysisResult] = None
    technical_plan: Optional[TechnicalPlan] = None
    sme_recommendations: Dict[str, SMERecommendation] = field(default_factory=dict)
    aggregated_confidence: float = 0.0
    execution_strategy: str = "sequential"
    risk_assessment: Dict[str, List[str]] = field(default_factory=dict)
    implementation_timeline: List[str] = field(default_factory=list)
    validation_criteria: List[str] = field(default_factory=list)
    analysis_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BrainCommunicationMetrics:
    """Metrics for brain communication performance"""
    total_analysis_time: float = 0.0
    intent_analysis_time: float = 0.0
    technical_planning_time: float = 0.0
    sme_consultation_time: float = 0.0
    confidence_aggregation_time: float = 0.0
    messages_exchanged: int = 0
    failed_communications: int = 0
    timeout_count: int = 0


class BrainCommunicationProtocol:
    """
    Brain Communication Protocol for coordinating multi-brain analysis
    
    This class orchestrates communication between all brain components:
    - Intent Brain: Analyzes user intent and requirements
    - Technical Brain: Creates execution plans and orchestrates SMEs
    - SME Brains: Provide domain-specific expertise
    - Confidence Engine: Aggregates confidence and determines strategy
    """
    
    def __init__(self):
        self.intent_brain = None
        self.technical_brain = None
        self.sme_brains: Dict[str, SMEBrain] = {}
        self.message_queue = asyncio.Queue()
        self.active_analyses: Dict[str, MultibrainAnalysis] = {}
        self.communication_metrics = BrainCommunicationMetrics()
        self.timeout_seconds = 30
        
        # Communication channels
        self.brain_channels: Dict[str, asyncio.Queue] = {}
        self.response_channels: Dict[str, asyncio.Queue] = {}
        
    async def initialize_brains(self, intent_brain: IntentBrain, technical_brain: TechnicalBrain, 
                              sme_brains: Dict[str, SMEBrain]):
        """Initialize brain components for communication"""
        self.intent_brain = intent_brain
        self.technical_brain = technical_brain
        self.sme_brains = sme_brains
        
        # Initialize communication channels
        for brain_name in ["intent", "technical"] + list(sme_brains.keys()):
            self.brain_channels[brain_name] = asyncio.Queue()
            self.response_channels[brain_name] = asyncio.Queue()
    
    async def coordinate_multi_brain_analysis(self, user_request: str) -> MultibrainAnalysis:
        """
        Coordinate analysis across all brain components
        
        Args:
            user_request: User's request to analyze
            
        Returns:
            MultibrainAnalysis: Complete analysis from all brain components
        """
        analysis_start_time = datetime.now()
        correlation_id = f"analysis_{int(analysis_start_time.timestamp())}"
        
        try:
            # Initialize analysis
            analysis = MultibrainAnalysis(
                user_request=user_request,
                analysis_metadata={
                    "correlation_id": correlation_id,
                    "start_time": analysis_start_time.isoformat(),
                    "phases_completed": []
                }
            )
            
            self.active_analyses[correlation_id] = analysis
            
            # Phase 1: Intent Analysis
            await self._execute_intent_analysis_phase(analysis, correlation_id)
            
            # Phase 2: Technical Planning
            await self._execute_technical_planning_phase(analysis, correlation_id)
            
            # Phase 3: SME Consultation
            await self._execute_sme_consultation_phase(analysis, correlation_id)
            
            # Phase 4: Confidence Aggregation
            await self._execute_confidence_aggregation_phase(analysis, correlation_id)
            
            # Phase 5: Strategy Determination
            await self._execute_strategy_determination_phase(analysis, correlation_id)
            
            # Finalize analysis
            analysis_end_time = datetime.now()
            analysis.analysis_metadata["end_time"] = analysis_end_time.isoformat()
            analysis.analysis_metadata["total_duration"] = (analysis_end_time - analysis_start_time).total_seconds()
            
            # Update metrics
            self.communication_metrics.total_analysis_time = (analysis_end_time - analysis_start_time).total_seconds()
            
            return analysis
            
        except Exception as e:
            # Handle analysis failure
            analysis.analysis_metadata["error"] = str(e)
            analysis.analysis_metadata["status"] = "failed"
            self.communication_metrics.failed_communications += 1
            
            # Return partial analysis
            return analysis
        
        finally:
            # Cleanup
            if correlation_id in self.active_analyses:
                del self.active_analyses[correlation_id]
    
    async def _execute_intent_analysis_phase(self, analysis: MultibrainAnalysis, correlation_id: str):
        """Execute intent analysis phase"""
        phase_start = datetime.now()
        
        try:
            if not self.intent_brain:
                raise Exception("Intent Brain not initialized")
            
            # Send message to Intent Brain
            message = BrainMessage(
                sender="protocol",
                receiver="intent",
                message_type="analyze_intent",
                content={"user_request": analysis.user_request},
                correlation_id=correlation_id
            )
            
            await self._send_message(message)
            
            # Analyze intent
            analysis.intent_analysis = await self.intent_brain.analyze_intent(analysis.user_request)
            
            # Update metadata
            analysis.analysis_metadata["phases_completed"].append("intent_analysis")
            self.communication_metrics.intent_analysis_time = (datetime.now() - phase_start).total_seconds()
            
        except Exception as e:
            analysis.analysis_metadata["intent_analysis_error"] = str(e)
            raise
    
    async def _execute_technical_planning_phase(self, analysis: MultibrainAnalysis, correlation_id: str):
        """Execute technical planning phase"""
        phase_start = datetime.now()
        
        try:
            if not self.technical_brain or not analysis.intent_analysis:
                raise Exception("Technical Brain not initialized or Intent Analysis missing")
            
            # Send message to Technical Brain
            message = BrainMessage(
                sender="protocol",
                receiver="technical",
                message_type="create_execution_plan",
                content={"intent_analysis": analysis.intent_analysis.__dict__},
                correlation_id=correlation_id
            )
            
            await self._send_message(message)
            
            # Create technical plan
            analysis.technical_plan = await self.technical_brain.create_execution_plan(analysis.intent_analysis)
            
            # Update metadata
            analysis.analysis_metadata["phases_completed"].append("technical_planning")
            self.communication_metrics.technical_planning_time = (datetime.now() - phase_start).total_seconds()
            
        except Exception as e:
            analysis.analysis_metadata["technical_planning_error"] = str(e)
            raise
    
    async def _execute_sme_consultation_phase(self, analysis: MultibrainAnalysis, correlation_id: str):
        """Execute SME consultation phase"""
        phase_start = datetime.now()
        
        try:
            if not analysis.technical_plan:
                raise Exception("Technical Plan missing for SME consultation")
            
            # Determine which SME brains to consult
            required_smes = analysis.technical_plan.required_sme_consultations
            
            # Consult SME brains in parallel
            sme_tasks = []
            for sme_domain in required_smes:
                if sme_domain in self.sme_brains:
                    task = self._consult_sme_brain(sme_domain, analysis, correlation_id)
                    sme_tasks.append(task)
            
            # Wait for all SME consultations
            if sme_tasks:
                sme_results = await asyncio.gather(*sme_tasks, return_exceptions=True)
                
                # Process SME results
                for i, result in enumerate(sme_results):
                    if isinstance(result, Exception):
                        sme_domain = required_smes[i]
                        analysis.analysis_metadata[f"sme_{sme_domain}_error"] = str(result)
                    else:
                        sme_domain, recommendation = result
                        analysis.sme_recommendations[sme_domain] = recommendation
            
            # Update metadata
            analysis.analysis_metadata["phases_completed"].append("sme_consultation")
            self.communication_metrics.sme_consultation_time = (datetime.now() - phase_start).total_seconds()
            
        except Exception as e:
            analysis.analysis_metadata["sme_consultation_error"] = str(e)
            raise
    
    async def _consult_sme_brain(self, sme_domain: str, analysis: MultibrainAnalysis, 
                               correlation_id: str) -> tuple[str, SMERecommendation]:
        """Consult a specific SME brain"""
        sme_brain = self.sme_brains[sme_domain]
        
        # Create SME query
        sme_query = SMEQuery(
            domain=sme_domain,
            query=analysis.user_request,
            context=f"Intent: {analysis.intent_analysis.primary_intent if analysis.intent_analysis else 'unknown'}, "
                   f"Technical Plan: {analysis.technical_plan.execution_strategy if analysis.technical_plan else 'unknown'}",
            technical_context=analysis.technical_plan.__dict__ if analysis.technical_plan else {},
            intent_context=analysis.intent_analysis.__dict__ if analysis.intent_analysis else {}
        )
        
        # Send message to SME Brain
        message = BrainMessage(
            sender="protocol",
            receiver=sme_domain,
            message_type="provide_expertise",
            content={"sme_query": sme_query.__dict__},
            correlation_id=correlation_id
        )
        
        await self._send_message(message)
        
        # Get SME recommendation
        recommendation = await sme_brain.provide_expertise(sme_query)
        
        return sme_domain, recommendation
    
    async def _execute_confidence_aggregation_phase(self, analysis: MultibrainAnalysis, correlation_id: str):
        """Execute confidence aggregation phase"""
        phase_start = datetime.now()
        
        try:
            # Collect confidence scores from all brains
            confidence_scores = {}
            
            if analysis.intent_analysis:
                confidence_scores["intent"] = analysis.intent_analysis.confidence
            
            if analysis.technical_plan:
                confidence_scores["technical"] = analysis.technical_plan.confidence
            
            for sme_domain, recommendation in analysis.sme_recommendations.items():
                confidence_scores[f"sme_{sme_domain}"] = recommendation.confidence.score
            
            # Calculate aggregated confidence
            if confidence_scores:
                # Weighted average (Intent and Technical have higher weight)
                weights = {
                    "intent": 0.3,
                    "technical": 0.4,
                }
                
                # Distribute remaining weight among SME brains
                sme_count = len([k for k in confidence_scores.keys() if k.startswith("sme_")])
                if sme_count > 0:
                    sme_weight = 0.3 / sme_count
                    for key in confidence_scores.keys():
                        if key.startswith("sme_"):
                            weights[key] = sme_weight
                
                # Calculate weighted average
                total_weight = 0
                weighted_sum = 0
                
                for brain, confidence in confidence_scores.items():
                    weight = weights.get(brain, 0.1)  # Default weight for unknown brains
                    weighted_sum += confidence * weight
                    total_weight += weight
                
                analysis.aggregated_confidence = weighted_sum / total_weight if total_weight > 0 else 0.5
            else:
                analysis.aggregated_confidence = 0.3  # Low confidence if no brain responses
            
            # Update metadata
            analysis.analysis_metadata["phases_completed"].append("confidence_aggregation")
            analysis.analysis_metadata["confidence_breakdown"] = confidence_scores
            self.communication_metrics.confidence_aggregation_time = (datetime.now() - phase_start).total_seconds()
            
        except Exception as e:
            analysis.analysis_metadata["confidence_aggregation_error"] = str(e)
            analysis.aggregated_confidence = 0.3  # Default low confidence
    
    async def _execute_strategy_determination_phase(self, analysis: MultibrainAnalysis, correlation_id: str):
        """Execute strategy determination phase"""
        try:
            # Determine execution strategy based on confidence and complexity
            if analysis.aggregated_confidence >= 0.8:
                analysis.execution_strategy = "parallel"
            elif analysis.aggregated_confidence >= 0.6:
                analysis.execution_strategy = "sequential"
            elif analysis.aggregated_confidence >= 0.4:
                analysis.execution_strategy = "phased"
            else:
                analysis.execution_strategy = "manual_review"
            
            # Aggregate risk assessments
            all_risks = {"high_risk": [], "medium_risk": [], "low_risk": [], "mitigation_strategies": []}
            
            for recommendation in analysis.sme_recommendations.values():
                for risk_level, risks in recommendation.risk_assessment.items():
                    if risk_level in all_risks:
                        all_risks[risk_level].extend(risks)
            
            analysis.risk_assessment = all_risks
            
            # Create implementation timeline
            if analysis.technical_plan:
                analysis.implementation_timeline = analysis.technical_plan.implementation_steps
            
            # Aggregate validation criteria
            validation_criteria = set()
            for recommendation in analysis.sme_recommendations.values():
                validation_criteria.update(recommendation.validation_criteria)
            analysis.validation_criteria = list(validation_criteria)
            
            # Update metadata
            analysis.analysis_metadata["phases_completed"].append("strategy_determination")
            
        except Exception as e:
            analysis.analysis_metadata["strategy_determination_error"] = str(e)
            analysis.execution_strategy = "manual_review"  # Safe default
    
    async def _send_message(self, message: BrainMessage):
        """Send message between brains"""
        try:
            await self.message_queue.put(message)
            self.communication_metrics.messages_exchanged += 1
            
            # Log message for debugging
            print(f"Message sent: {message.sender} -> {message.receiver}: {message.message_type}")
            
        except Exception as e:
            self.communication_metrics.failed_communications += 1
            raise Exception(f"Failed to send message: {e}")
    
    async def get_communication_metrics(self) -> BrainCommunicationMetrics:
        """Get communication performance metrics"""
        return self.communication_metrics
    
    async def reset_metrics(self):
        """Reset communication metrics"""
        self.communication_metrics = BrainCommunicationMetrics()
    
    async def get_active_analyses(self) -> Dict[str, MultibrainAnalysis]:
        """Get currently active analyses"""
        return self.active_analyses.copy()
    
    async def cancel_analysis(self, correlation_id: str) -> bool:
        """Cancel an active analysis"""
        if correlation_id in self.active_analyses:
            analysis = self.active_analyses[correlation_id]
            analysis.analysis_metadata["status"] = "cancelled"
            analysis.analysis_metadata["cancelled_at"] = datetime.now().isoformat()
            del self.active_analyses[correlation_id]
            return True
        return False
    
    def create_brain_message(self, sender: str, receiver: str, message_type: str, content: Dict[str, Any]) -> BrainMessage:
        """
        Create a brain message for communication between brains.
        
        Args:
            sender: The brain sending the message
            receiver: The brain receiving the message
            message_type: Type of message being sent
            content: Message content
            
        Returns:
            BrainMessage object
        """
        import uuid
        
        message = BrainMessage(
            sender=sender,
            receiver=receiver,
            message_type=message_type,
            content=content,
            timestamp=datetime.now(),
            correlation_id=str(uuid.uuid4()),
            priority=1
        )
        
        # Add message_id for backward compatibility
        message.message_id = message.correlation_id
        
        return message
    
    def __str__(self) -> str:
        """String representation of the protocol"""
        return (f"BrainCommunicationProtocol("
                f"brains={len(self.sme_brains) + 2}, "
                f"active_analyses={len(self.active_analyses)}, "
                f"messages_exchanged={self.communication_metrics.messages_exchanged})")
    
    def __repr__(self) -> str:
        """Detailed representation of the protocol"""
        return (f"BrainCommunicationProtocol("
                f"intent_brain={self.intent_brain is not None}, "
                f"technical_brain={self.technical_brain is not None}, "
                f"sme_brains={list(self.sme_brains.keys())}, "
                f"active_analyses={len(self.active_analyses)}, "
                f"metrics={self.communication_metrics})")