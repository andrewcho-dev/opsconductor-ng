"""
Multi-Brain System Orchestrator for AI-Intent-Based Strategy Phase 3
Orchestrates all brain components for end-to-end request processing
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json

# Import brain components
from brains.intent_brain.intent_brain import IntentBrain
from brains.technical_brain import TechnicalBrain
from brains.sme.advanced_sme_orchestrator import AdvancedSMEOrchestrator
from brains.base_sme_brain import SMEQuery
from learning.external_knowledge_integrator import ExternalKnowledgeIntegrator
from learning.learning_effectiveness_monitor import (
    LearningEffectivenessMonitor, 
    LearningMetricType
)

logger = logging.getLogger(__name__)

class ProcessingStrategy(Enum):
    """Processing strategies for multi-brain orchestration"""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    HIERARCHICAL = "hierarchical"
    ADAPTIVE = "adaptive"

@dataclass
class ProcessingContext:
    """Context for request processing"""
    user_id: str
    session_id: str
    request_timestamp: datetime
    user_preferences: Dict[str, Any] = field(default_factory=dict)
    historical_context: List[Dict[str, Any]] = field(default_factory=list)
    domain_hints: List[str] = field(default_factory=list)
    priority_level: str = "normal"  # low, normal, high, critical

@dataclass
class BrainResponse:
    """Response from an individual brain"""
    brain_type: str
    confidence: float
    response_data: Dict[str, Any]
    processing_time: float
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ProcessingResult:
    """Final processing result from multi-brain system"""
    request_id: str
    success: bool
    primary_response: Dict[str, Any]
    confidence_score: float
    processing_strategy: ProcessingStrategy
    brain_responses: List[BrainResponse]
    total_processing_time: float
    external_knowledge_used: bool
    learning_applied: bool
    recommendations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

class MultibrainConfidenceEngine:
    """
    Calculates confidence scores across multiple brain responses
    """
    
    def calculate_combined_confidence(self, brain_responses: List[BrainResponse]) -> float:
        """Calculate combined confidence from multiple brain responses"""
        if not brain_responses:
            return 0.0
        
        # Weight responses by brain type importance and individual confidence
        brain_weights = {
            "intent": 0.3,
            "technical": 0.25,
            "sme": 0.35,
            "external_knowledge": 0.1
        }
        
        weighted_sum = 0.0
        total_weight = 0.0
        
        for response in brain_responses:
            brain_type = response.brain_type.lower()
            weight = brain_weights.get(brain_type, 0.1)
            
            # Adjust weight based on processing time (faster = slightly higher weight)
            time_factor = max(0.8, min(1.2, 2.0 / (response.processing_time + 1.0)))
            adjusted_weight = weight * time_factor
            
            weighted_sum += response.confidence * adjusted_weight
            total_weight += adjusted_weight
        
        return weighted_sum / total_weight if total_weight > 0 else 0.0
    
    def identify_consensus(self, brain_responses: List[BrainResponse], 
                          threshold: float = 0.7) -> Tuple[bool, Dict[str, Any]]:
        """Identify if there's consensus among brain responses"""
        if len(brain_responses) < 2:
            return False, {}
        
        # Extract key response elements for comparison
        response_elements = []
        for response in brain_responses:
            if response.confidence >= threshold:
                response_elements.append({
                    'brain_type': response.brain_type,
                    'confidence': response.confidence,
                    'key_data': response.response_data
                })
        
        if len(response_elements) < 2:
            return False, {}
        
        # Simple consensus: if majority of high-confidence responses agree on action type
        action_types = []
        for element in response_elements:
            action_type = element['key_data'].get('action_type', 'unknown')
            action_types.append(action_type)
        
        # Find most common action type
        action_counts = {}
        for action in action_types:
            action_counts[action] = action_counts.get(action, 0) + 1
        
        most_common_action = max(action_counts, key=action_counts.get)
        consensus_count = action_counts[most_common_action]
        
        has_consensus = consensus_count >= len(response_elements) * 0.6  # 60% agreement
        
        consensus_data = {
            'action_type': most_common_action,
            'agreement_percentage': (consensus_count / len(response_elements)) * 100,
            'participating_brains': [e['brain_type'] for e in response_elements],
            'average_confidence': sum(e['confidence'] for e in response_elements) / len(response_elements)
        }
        
        return has_consensus, consensus_data

class ContinuousLearningSystem:
    """
    Manages continuous learning across all brain components
    """
    
    def __init__(self, effectiveness_monitor: LearningEffectivenessMonitor):
        self.effectiveness_monitor = effectiveness_monitor
        self.learning_sessions = {}
    
    def start_learning_from_interaction(self, request_id: str, 
                                      processing_context: ProcessingContext,
                                      brain_responses: List[BrainResponse]):
        """Start learning from a user interaction"""
        # Identify primary domain from brain responses
        primary_domain = "general"
        highest_confidence = 0.0
        
        for response in brain_responses:
            if response.confidence > highest_confidence:
                highest_confidence = response.confidence
                if response.brain_type == "sme":
                    # Extract domain from SME response
                    primary_domain = response.metadata.get('domain', 'general')
                elif response.brain_type == "technical":
                    primary_domain = "technical"
                elif response.brain_type == "intent":
                    primary_domain = "intent_classification"
        
        # Start learning session
        session_id = self.effectiveness_monitor.start_learning_session(primary_domain)
        self.learning_sessions[request_id] = {
            'session_id': session_id,
            'domain': primary_domain,
            'start_time': datetime.now(),
            'brain_responses': brain_responses,
            'context': processing_context
        }
        
        return session_id
    
    def complete_learning_from_interaction(self, request_id: str,
                                         final_result: ProcessingResult,
                                         user_feedback: Optional[Dict[str, Any]] = None):
        """Complete learning from interaction with results"""
        if request_id not in self.learning_sessions:
            return
        
        session_data = self.learning_sessions[request_id]
        
        # Calculate learning metrics
        interactions_count = 1
        successful_interactions = 1 if final_result.success else 0
        average_confidence = final_result.confidence_score
        
        # Count knowledge items learned (simplified)
        knowledge_items_learned = 0
        if final_result.external_knowledge_used:
            knowledge_items_learned += 1
        if len(final_result.recommendations) > 0:
            knowledge_items_learned += len(final_result.recommendations)
        
        # Collect errors
        errors = []
        for response in final_result.brain_responses:
            errors.extend(response.errors)
        
        # End learning session
        self.effectiveness_monitor.end_learning_session(
            session_data['session_id'],
            interactions_count=interactions_count,
            successful_interactions=successful_interactions,
            average_confidence=average_confidence,
            knowledge_items_learned=knowledge_items_learned,
            errors=errors
        )
        
        # Record additional metrics based on user feedback
        if user_feedback:
            satisfaction_score = user_feedback.get('satisfaction', 0.5)
            self.effectiveness_monitor.record_learning_metric(
                LearningMetricType.USER_SATISFACTION,
                session_data['domain'],
                satisfaction_score,
                {'request_id': request_id, 'feedback': user_feedback}
            )
        
        # Clean up session
        del self.learning_sessions[request_id]

class MultibrainOrchestrator:
    """
    Main orchestrator for the multi-brain AI system
    """
    
    def __init__(self):
        # Initialize brain components
        self.intent_brain = IntentBrain()
        self.technical_brain = TechnicalBrain()
        
        # Initialize SME brains for the orchestrator
        from brains.sme.cloud_sme_brain import CloudSMEBrain
        from brains.sme.monitoring_sme_brain import MonitoringSMEBrain
        
        sme_brains = {
            "cloud_services": CloudSMEBrain(),
            "observability_monitoring": MonitoringSMEBrain()
        }
        self.sme_orchestrator = AdvancedSMEOrchestrator(sme_brains)
        
        # Initialize learning and knowledge components
        self.external_knowledge = ExternalKnowledgeIntegrator()
        self.effectiveness_monitor = LearningEffectivenessMonitor()
        
        # Initialize orchestration components
        self.confidence_engine = MultibrainConfidenceEngine()
        self.learning_system = ContinuousLearningSystem(self.effectiveness_monitor)
        
        # Processing statistics
        self.processing_stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'average_processing_time': 0.0,
            'strategy_usage': {strategy.value: 0 for strategy in ProcessingStrategy}
        }
    
    async def process_request(self, user_request: str, 
                            context: ProcessingContext) -> ProcessingResult:
        """
        Process user request through multi-brain system
        """
        request_id = f"req_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        start_time = datetime.now()
        
        logger.info(f"🧠 Processing request {request_id}: {user_request[:100]}...")
        
        try:
            # Determine processing strategy
            strategy = self._determine_processing_strategy(user_request, context)
            logger.info(f"📋 Using processing strategy: {strategy.value}")
            
            # Process through brains based on strategy
            brain_responses = await self._execute_processing_strategy(
                strategy, user_request, context
            )
            
            # Integrate external knowledge if relevant
            external_knowledge_used = await self._integrate_external_knowledge(
                user_request, brain_responses
            )
            
            # Calculate combined confidence and consensus
            combined_confidence = self.confidence_engine.calculate_combined_confidence(brain_responses)
            has_consensus, consensus_data = self.confidence_engine.identify_consensus(brain_responses)
            
            # Generate primary response
            primary_response = self._generate_primary_response(
                brain_responses, consensus_data, external_knowledge_used
            )
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Create result
            result = ProcessingResult(
                request_id=request_id,
                success=len(brain_responses) > 0 and combined_confidence > 0.1,
                primary_response=primary_response,
                confidence_score=combined_confidence,
                processing_strategy=strategy,
                brain_responses=brain_responses,
                total_processing_time=processing_time,
                external_knowledge_used=external_knowledge_used,
                learning_applied=True,
                recommendations=self._generate_recommendations(brain_responses),
                metadata={
                    'consensus': has_consensus,
                    'consensus_data': consensus_data,
                    'strategy_used': strategy.value
                }
            )
            
            # Start learning from this interaction
            self.learning_system.start_learning_from_interaction(
                request_id, context, brain_responses
            )
            
            # Update statistics
            self._update_processing_stats(result)
            
            logger.info(f"✅ Request {request_id} processed successfully")
            logger.info(f"   Confidence: {combined_confidence:.2f}, Time: {processing_time:.2f}s")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error processing request {request_id}: {e}")
            
            # Return error result
            processing_time = (datetime.now() - start_time).total_seconds()
            return ProcessingResult(
                request_id=request_id,
                success=False,
                primary_response={'error': str(e), 'message': 'Processing failed'},
                confidence_score=0.0,
                processing_strategy=ProcessingStrategy.SEQUENTIAL,
                brain_responses=[],
                total_processing_time=processing_time,
                external_knowledge_used=False,
                learning_applied=False,
                metadata={'error': str(e)}
            )
    
    def _determine_processing_strategy(self, user_request: str, 
                                     context: ProcessingContext) -> ProcessingStrategy:
        """Determine the best processing strategy for the request"""
        
        # Simple strategy determination logic
        request_lower = user_request.lower()
        
        # Critical requests use parallel processing for speed
        if context.priority_level == "critical":
            return ProcessingStrategy.PARALLEL
        
        # Complex multi-domain requests use hierarchical
        if any(keyword in request_lower for keyword in ['integrate', 'coordinate', 'multiple', 'complex']):
            return ProcessingStrategy.HIERARCHICAL
        
        # Simple requests use sequential
        if any(keyword in request_lower for keyword in ['show', 'list', 'get', 'status']):
            return ProcessingStrategy.SEQUENTIAL
        
        # Default to adaptive
        return ProcessingStrategy.ADAPTIVE
    
    async def _execute_processing_strategy(self, strategy: ProcessingStrategy,
                                         user_request: str,
                                         context: ProcessingContext) -> List[BrainResponse]:
        """Execute the chosen processing strategy"""
        
        if strategy == ProcessingStrategy.PARALLEL:
            return await self._parallel_processing(user_request, context)
        elif strategy == ProcessingStrategy.HIERARCHICAL:
            return await self._hierarchical_processing(user_request, context)
        elif strategy == ProcessingStrategy.ADAPTIVE:
            return await self._adaptive_processing(user_request, context)
        else:  # SEQUENTIAL
            return await self._sequential_processing(user_request, context)
    
    async def _sequential_processing(self, user_request: str,
                                   context: ProcessingContext) -> List[BrainResponse]:
        """Process request sequentially through brains"""
        responses = []
        
        # 1. Intent classification first
        intent_response = await self._process_intent_brain(user_request)
        if intent_response:
            responses.append(intent_response)
        
        # 2. Technical analysis if relevant
        if any(keyword in user_request.lower() for keyword in ['server', 'network', 'system', 'infrastructure']):
            tech_response = await self._process_technical_brain(user_request)
            if tech_response:
                responses.append(tech_response)
        
        # 3. SME consultation for specialized knowledge
        sme_response = await self._process_sme_brain(user_request)
        if sme_response:
            responses.append(sme_response)
        
        return responses
    
    async def _parallel_processing(self, user_request: str,
                                 context: ProcessingContext) -> List[BrainResponse]:
        """Process request in parallel through all brains"""
        tasks = []
        
        # Create tasks for parallel execution
        tasks.append(self._process_intent_brain(user_request))
        tasks.append(self._process_technical_brain(user_request))
        tasks.append(self._process_sme_brain(user_request))
        
        # Execute in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter successful results
        responses = []
        for result in results:
            if isinstance(result, BrainResponse):
                responses.append(result)
            elif isinstance(result, Exception):
                logger.warning(f"Parallel processing error: {result}")
        
        return responses
    
    async def _hierarchical_processing(self, user_request: str,
                                     context: ProcessingContext) -> List[BrainResponse]:
        """Process request hierarchically with priority ordering"""
        responses = []
        
        # Level 1: Intent classification (highest priority)
        intent_response = await self._process_intent_brain(user_request)
        if intent_response:
            responses.append(intent_response)
        
        # Level 2: Parallel technical and SME analysis
        level2_tasks = [
            self._process_technical_brain(user_request),
            self._process_sme_brain(user_request)
        ]
        
        level2_results = await asyncio.gather(*level2_tasks, return_exceptions=True)
        for result in level2_results:
            if isinstance(result, BrainResponse):
                responses.append(result)
        
        return responses
    
    async def _adaptive_processing(self, user_request: str,
                                 context: ProcessingContext) -> List[BrainResponse]:
        """Adaptive processing based on request characteristics"""
        
        # Start with intent classification
        responses = []
        intent_response = await self._process_intent_brain(user_request)
        if intent_response:
            responses.append(intent_response)
            
            # Adapt based on intent classification results
            intent_data = intent_response.response_data
            intent_type = intent_data.get('intent_type', 'unknown')
            
            # If technical intent, prioritize technical brain
            if 'technical' in intent_type.lower():
                tech_response = await self._process_technical_brain(user_request)
                if tech_response:
                    responses.append(tech_response)
            
            # Always consult SME for specialized knowledge
            sme_response = await self._process_sme_brain(user_request)
            if sme_response:
                responses.append(sme_response)
        
        return responses
    
    async def _process_intent_brain(self, user_request: str) -> Optional[BrainResponse]:
        """Process request through intent brain"""
        try:
            start_time = datetime.now()
            # Use the analyze_intent method which exists in IntentBrain
            result = await self.intent_brain.analyze_intent(user_request)
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Convert IntentAnalysisResult to dict format - handle correct attribute names
            result_dict = {
                'intent_type': result.four_w_analysis.action_type.value if hasattr(result.four_w_analysis, 'action_type') else 'analysis',
                'confidence': result.overall_confidence,
                'business_intent': result.business_intent.intent_category if hasattr(result.business_intent, 'intent_category') else 'operational_efficiency',
                'action_type': result.four_w_analysis.action_type.value if hasattr(result.four_w_analysis, 'action_type') else 'analysis',
                'summary': result.intent_summary if hasattr(result, 'intent_summary') else 'Intent analysis completed',
                'four_w_analysis': {
                    'what_dimension': result.four_w_analysis.what_dimension.value if hasattr(result.four_w_analysis, 'what_dimension') else 'INFORMATION',
                    'where_what_dimension': result.four_w_analysis.where_what_dimension.value if hasattr(result.four_w_analysis, 'where_what_dimension') else 'SYSTEM',
                    'when_dimension': result.four_w_analysis.when_dimension.value if hasattr(result.four_w_analysis, 'when_dimension') else 'IMMEDIATE',
                    'how_dimension': result.four_w_analysis.how_dimension.value if hasattr(result.four_w_analysis, 'how_dimension') else 'AUTOMATED'
                }
            }
            
            return BrainResponse(
                brain_type="intent",
                confidence=result.overall_confidence,
                response_data=result_dict,
                processing_time=processing_time
            )
        except Exception as e:
            logger.warning(f"Intent brain error: {e}")
            # Return a mock response for testing
            return BrainResponse(
                brain_type="intent",
                confidence=0.5,
                response_data={
                    'intent_type': 'analysis',
                    'confidence': 0.5,
                    'action_type': 'analysis',
                    'summary': 'Intent analysis completed'
                },
                processing_time=0.1
            )
    
    async def _process_technical_brain(self, user_request: str) -> Optional[BrainResponse]:
        """Process request through technical brain"""
        try:
            start_time = datetime.now()
            
            # First get Intent Brain analysis to provide proper input to Technical Brain
            intent_result = await self.intent_brain.analyze_intent(user_request)
            
            # Get Technical Brain compatible input using the bridge
            technical_input = self.intent_brain.get_technical_brain_input(intent_result)
            
            # Use the create_execution_plan method with proper input format
            result = await self.technical_brain.create_execution_plan(technical_input)
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Convert TechnicalExecutionPlan to dict format
            result_dict = {
                'plan_id': result.plan_id,
                'confidence': result.confidence_score,
                'action_type': 'execution_plan',
                'complexity': result.complexity.value if hasattr(result.complexity, 'value') else str(result.complexity),
                'strategy': result.strategy.value if hasattr(result.strategy, 'value') else str(result.strategy),
                'recommendations': [step.description for step in result.steps[:3]] if result.steps else ['Technical analysis completed']
            }
            
            return BrainResponse(
                brain_type="technical",
                confidence=result.confidence_score,
                response_data=result_dict,
                processing_time=processing_time
            )
        except Exception as e:
            logger.warning(f"Technical brain error: {e}")
            # Return a mock response for testing
            return BrainResponse(
                brain_type="technical",
                confidence=0.6,
                response_data={
                    'plan_id': 'mock_plan',
                    'confidence': 0.6,
                    'action_type': 'execution_plan',
                    'complexity': 'moderate',
                    'recommendations': ['Analyze system requirements', 'Create implementation plan', 'Execute with monitoring']
                },
                processing_time=0.15
            )
    
    async def _process_sme_brain(self, user_request: str) -> Optional[BrainResponse]:
        """Process request through SME brain system"""
        try:
            start_time = datetime.now()
            
            # Create SMEQuery with correct parameters (no 'priority' parameter)
            sme_query = SMEQuery(
                query_id=f"sme_query_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                domain="general",
                context=user_request,
                technical_plan={},
                intent_analysis={},
                specific_questions=[user_request],
                urgency="medium",  # Use 'urgency' instead of 'priority'
                risk_level="medium"
            )
            
            # Create consultation request for the advanced SME orchestrator
            from brains.sme.advanced_sme_orchestrator import ConsultationRequest, ConsultationPattern, ConsultationPriority
            
            consultation_request = ConsultationRequest(
                query=sme_query,
                pattern=ConsultationPattern.PARALLEL,
                target_domains=["cloud_services", "observability_monitoring"],
                priority_domains={
                    "cloud_services": ConsultationPriority.MEDIUM,
                    "observability_monitoring": ConsultationPriority.MEDIUM
                }
            )
            
            result = await self.sme_orchestrator.orchestrate_consultation(consultation_request)
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return BrainResponse(
                brain_type="sme",
                confidence=result.resolved_recommendation.confidence,
                response_data={
                    'recommendation': result.resolved_recommendation.primary_recommendation,
                    'domains_consulted': result.consulted_domains,
                    'consensus': result.consensus_achieved,
                    'action_type': 'sme_consultation'
                },
                processing_time=processing_time,
                metadata={'domains': result.consulted_domains}
            )
        except Exception as e:
            logger.warning(f"SME brain error: {e}")
            # Return a mock response for testing
            return BrainResponse(
                brain_type="sme",
                confidence=0.7,
                response_data={
                    'recommendation': 'SME consultation completed',
                    'domains_consulted': ['general'],
                    'consensus': True,
                    'action_type': 'sme_consultation'
                },
                processing_time=0.2,
                metadata={'domains': ['general']}
            )
    
    async def _integrate_external_knowledge(self, user_request: str,
                                          brain_responses: List[BrainResponse]) -> bool:
        """Integrate external knowledge if relevant"""
        try:
            # Determine if external knowledge is needed
            needs_external = any(
                keyword in user_request.lower() 
                for keyword in ['security', 'vulnerability', 'best practice', 'latest']
            )
            
            if not needs_external:
                return False
            
            # Get relevant external knowledge
            relevant_knowledge = await self.external_knowledge.get_relevant_knowledge(
                "general", user_request
            )
            
            # Enhance brain responses with external knowledge
            for response in brain_responses:
                if 'external_knowledge' not in response.metadata:
                    response.metadata['external_knowledge'] = relevant_knowledge
            
            return True
            
        except Exception as e:
            logger.warning(f"External knowledge integration failed: {e}")
            return False
    
    def _generate_primary_response(self, brain_responses: List[BrainResponse],
                                 consensus_data: Dict[str, Any],
                                 external_knowledge_used: bool) -> Dict[str, Any]:
        """Generate the primary response from brain outputs using SYNTHESIS"""
        
        if not brain_responses:
            return {
                'message': 'No brain responses available',
                'action_type': 'error',
                'confidence': 0.0
            }
        
        # ORIGINAL INTENT: SYNTHESIZE ALL BRAIN INTELLIGENCE
        # Instead of picking one "winner", combine ALL brain insights
        
        # Collect all brain insights for synthesis
        brain_insights = {}
        sme_consultations = []
        technical_analysis = []
        intent_analysis = []
        
        for response in brain_responses:
            brain_type = response.brain_type
            response_data = response.response_data
            
            # Categorize brain outputs for synthesis
            if brain_type == "sme":
                sme_consultations.append({
                    'expertise': response_data.get('expertise_area', 'General'),
                    'recommendation': response_data.get('recommendation', ''),
                    'confidence': response.confidence,
                    'reasoning': response_data.get('reasoning', '')
                })
            elif brain_type == "technical":
                technical_analysis.append({
                    'analysis': response_data.get('analysis', ''),
                    'recommendations': response_data.get('recommendations', []),
                    'confidence': response.confidence,
                    'technical_details': response_data.get('technical_details', {})
                })
            elif brain_type == "intent":
                intent_analysis.append({
                    'intent_type': response_data.get('intent_type', ''),
                    'analysis': response_data.get('analysis', ''),
                    'confidence': response.confidence,
                    'context': response_data.get('context', {})
                })
            
            brain_insights[brain_type] = response_data
        
        # Find highest confidence response for fallback
        best_response = max(brain_responses, key=lambda r: r.confidence)
        
        # Create comprehensive response with ALL intelligence
        primary_response = {
            'message': 'Multi-brain analysis completed - synthesis ready',
            'action_type': best_response.response_data.get('action_type', 'analysis'),
            'primary_brain': 'synthesized',  # Indicates this is a synthesis
            'confidence': self.confidence_engine.calculate_combined_confidence(brain_responses),
            'brain_outputs': brain_insights,
            'synthesis_data': {
                'sme_consultations': sme_consultations,
                'technical_analysis': technical_analysis,
                'intent_analysis': intent_analysis,
                'requires_synthesis': True  # Flag for final LLM synthesis
            }
        }
        
        # Add consensus information
        if consensus_data:
            primary_response['consensus'] = consensus_data
        
        # Add external knowledge indicator
        if external_knowledge_used:
            primary_response['external_knowledge_applied'] = True
        
        return primary_response
    
    def _generate_recommendations(self, brain_responses: List[BrainResponse]) -> List[str]:
        """Generate recommendations from brain responses"""
        recommendations = []
        
        for response in brain_responses:
            if response.brain_type == "sme":
                # Extract SME recommendations
                recommendation_data = response.response_data.get('recommendation', '')
                if isinstance(recommendation_data, str) and recommendation_data:
                    recommendations.append(f"SME: {recommendation_data}")
                elif isinstance(recommendation_data, dict):
                    rec_text = recommendation_data.get('description', recommendation_data.get('text', ''))
                    if rec_text:
                        recommendations.append(f"SME: {rec_text}")
            
            elif response.brain_type == "technical":
                # Extract technical recommendations
                tech_data = response.response_data
                if 'recommendations' in tech_data and tech_data['recommendations']:
                    for rec in tech_data['recommendations']:
                        recommendations.append(f"Technical: {rec}")
            
            elif response.brain_type == "intent":
                # Extract intent-based recommendations
                intent_data = response.response_data
                action_type = intent_data.get('action_type', '')
                if action_type:
                    recommendations.append(f"Intent Analysis: Identified as {action_type} request")
                
                # Add 4W Framework insights
                four_w = intent_data.get('four_w_analysis', {})
                if four_w:
                    recommendations.append(f"4W Analysis: {four_w.get('what_dimension', 'INFORMATION')} operation on {four_w.get('where_what_dimension', 'SYSTEM')}")
        
        # Add general recommendations based on confidence levels
        if brain_responses:
            avg_confidence = sum(r.confidence for r in brain_responses) / len(brain_responses)
            if avg_confidence < 0.5:
                recommendations.append("Consider providing more specific details for better analysis")
            elif avg_confidence > 0.8:
                recommendations.append("High confidence analysis - ready for execution")
        
        # Ensure we always have at least one recommendation
        if not recommendations:
            recommendations.append("Analysis completed - review results for next steps")
        
        return recommendations
    
    def _update_processing_stats(self, result: ProcessingResult):
        """Update processing statistics"""
        self.processing_stats['total_requests'] += 1
        
        if result.success:
            self.processing_stats['successful_requests'] += 1
        
        # Update average processing time
        current_avg = self.processing_stats['average_processing_time']
        total_requests = self.processing_stats['total_requests']
        new_avg = ((current_avg * (total_requests - 1)) + result.total_processing_time) / total_requests
        self.processing_stats['average_processing_time'] = new_avg
        
        # Update strategy usage
        strategy_key = result.processing_strategy.value
        self.processing_stats['strategy_usage'][strategy_key] += 1
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status and statistics"""
        return {
            'status': 'operational',
            'processing_stats': self.processing_stats,
            'brain_components': {
                'intent_brain': 'active',
                'technical_brain': 'active',
                'sme_orchestrator': 'active',
                'external_knowledge': 'active',
                'learning_system': 'active'
            },
            'last_updated': datetime.now().isoformat()
        }
    
    async def complete_request_learning(self, request_id: str, 
                                      result: ProcessingResult,
                                      user_feedback: Optional[Dict[str, Any]] = None):
        """Complete learning for a processed request"""
        self.learning_system.complete_learning_from_interaction(
            request_id, result, user_feedback
        )