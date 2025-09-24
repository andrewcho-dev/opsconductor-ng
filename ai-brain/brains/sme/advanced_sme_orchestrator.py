"""
Advanced SME Orchestrator - Sophisticated consultation patterns for SME brains

This module implements advanced consultation patterns including:
- Parallel consultation with dependency management
- Sequential consultation with context passing
- Conditional consultation based on previous results
- Cross-domain expertise sharing
"""

import asyncio
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass
from enum import Enum
import json
from datetime import datetime

from ..base_sme_brain import SMEBrain, SMEQuery, SMERecommendation, SMEConfidenceLevel
from .sme_conflict_resolver import SMEConflictResolver, ResolvedRecommendation, ResolutionStrategy


class ConsultationPattern(Enum):
    PARALLEL = "parallel"              # All SMEs consulted simultaneously
    SEQUENTIAL = "sequential"          # SMEs consulted in order with context passing
    CONDITIONAL = "conditional"        # SMEs consulted based on conditions
    HIERARCHICAL = "hierarchical"      # SMEs consulted in priority order
    COLLABORATIVE = "collaborative"    # SMEs collaborate on shared analysis


class ConsultationPriority(Enum):
    CRITICAL = "critical"     # Must be consulted
    HIGH = "high"            # Should be consulted
    MEDIUM = "medium"        # May be consulted
    LOW = "low"             # Optional consultation
    CONDITIONAL = "conditional"  # Consulted based on conditions


@dataclass
class ConsultationRequest:
    """Request for SME consultation"""
    query: SMEQuery
    pattern: ConsultationPattern
    target_domains: List[str]
    priority_domains: Dict[str, ConsultationPriority]
    context_sharing: bool = True
    max_consultation_time: int = 30  # seconds
    require_consensus: bool = False


@dataclass
class ConsultationResult:
    """Result of SME consultation process"""
    resolved_recommendation: ResolvedRecommendation
    consultation_metadata: Dict[str, Any]
    consulted_domains: List[str]
    consultation_duration: float
    consensus_achieved: bool
    confidence_distribution: Dict[str, float]


@dataclass
class SMEConsultationContext:
    """Context shared between SME consultations"""
    original_query: SMEQuery
    previous_recommendations: Dict[str, SMERecommendation]
    shared_insights: Dict[str, Any]
    consultation_history: List[Dict[str, Any]]
    domain_dependencies: Dict[str, List[str]]


class AdvancedSMEOrchestrator:
    """
    Advanced SME Orchestrator for sophisticated consultation patterns
    
    Manages complex consultation workflows between multiple SME brains,
    including parallel processing, context sharing, and conflict resolution.
    """
    
    def __init__(self, sme_brains: Dict[str, SMEBrain]):
        self.sme_brains = sme_brains
        self.conflict_resolver = SMEConflictResolver()
        self.consultation_history = []
        self.domain_relationships = self._initialize_domain_relationships()
        
    def _initialize_domain_relationships(self) -> Dict[str, Dict[str, Any]]:
        """Initialize relationships between different SME domains"""
        return {
            "security_and_compliance": {
                "influences": ["network_infrastructure", "cloud_services", "database_administration"],
                "influenced_by": [],
                "collaboration_strength": {
                    "network_infrastructure": 0.8,
                    "cloud_services": 0.9,
                    "database_administration": 0.7
                }
            },
            "network_infrastructure": {
                "influences": ["cloud_services", "container_orchestration", "observability_monitoring"],
                "influenced_by": ["security_and_compliance"],
                "collaboration_strength": {
                    "security_and_compliance": 0.8,
                    "cloud_services": 0.9,
                    "observability_monitoring": 0.7
                }
            },
            "database_administration": {
                "influences": ["observability_monitoring", "cloud_services"],
                "influenced_by": ["security_and_compliance", "network_infrastructure"],
                "collaboration_strength": {
                    "security_and_compliance": 0.7,
                    "observability_monitoring": 0.8,
                    "cloud_services": 0.6
                }
            },
            "container_orchestration": {
                "influences": ["observability_monitoring", "cloud_services"],
                "influenced_by": ["network_infrastructure", "security_and_compliance"],
                "collaboration_strength": {
                    "network_infrastructure": 0.8,
                    "cloud_services": 0.9,
                    "observability_monitoring": 0.7
                }
            },
            "cloud_services": {
                "influences": ["observability_monitoring"],
                "influenced_by": ["security_and_compliance", "network_infrastructure", "database_administration"],
                "collaboration_strength": {
                    "security_and_compliance": 0.9,
                    "network_infrastructure": 0.9,
                    "observability_monitoring": 0.8
                }
            },
            "observability_monitoring": {
                "influences": [],
                "influenced_by": ["network_infrastructure", "database_administration", "container_orchestration", "cloud_services"],
                "collaboration_strength": {
                    "network_infrastructure": 0.7,
                    "database_administration": 0.8,
                    "container_orchestration": 0.7,
                    "cloud_services": 0.8
                }
            }
        }
    
    async def orchestrate_consultation(self, request: ConsultationRequest) -> ConsultationResult:
        """
        Orchestrate SME consultation based on the specified pattern
        
        Args:
            request: Consultation request with pattern and parameters
            
        Returns:
            Consultation result with resolved recommendations
        """
        start_time = datetime.now()
        
        try:
            # Initialize consultation context
            context = SMEConsultationContext(
                original_query=request.query,
                previous_recommendations={},
                shared_insights={},
                consultation_history=[],
                domain_dependencies=self._analyze_domain_dependencies(request.target_domains)
            )
            
            # Execute consultation based on pattern
            if request.pattern == ConsultationPattern.PARALLEL:
                sme_recommendations = await self._parallel_consultation(request, context)
            elif request.pattern == ConsultationPattern.SEQUENTIAL:
                sme_recommendations = await self._sequential_consultation(request, context)
            elif request.pattern == ConsultationPattern.CONDITIONAL:
                sme_recommendations = await self._conditional_consultation(request, context)
            elif request.pattern == ConsultationPattern.HIERARCHICAL:
                sme_recommendations = await self._hierarchical_consultation(request, context)
            elif request.pattern == ConsultationPattern.COLLABORATIVE:
                sme_recommendations = await self._collaborative_consultation(request, context)
            else:
                # Default to parallel consultation
                sme_recommendations = await self._parallel_consultation(request, context)
            
            # Resolve conflicts between recommendations
            resolved_recommendation = await self.conflict_resolver.resolve_conflicts(sme_recommendations)
            
            # Calculate consultation metadata
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            consultation_result = ConsultationResult(
                resolved_recommendation=resolved_recommendation,
                consultation_metadata=self._build_consultation_metadata(context, request),
                consulted_domains=list(sme_recommendations.keys()),
                consultation_duration=duration,
                consensus_achieved=self._check_consensus(sme_recommendations),
                confidence_distribution=self._calculate_confidence_distribution(sme_recommendations)
            )
            
            # Store consultation history
            self.consultation_history.append({
                "timestamp": start_time.isoformat(),
                "pattern": request.pattern.value,
                "domains": list(sme_recommendations.keys()),
                "duration": duration,
                "consensus": consultation_result.consensus_achieved
            })
            
            return consultation_result
            
        except Exception as e:
            # Handle consultation failure
            return await self._handle_consultation_failure(request, str(e), start_time)
    
    async def _parallel_consultation(self, request: ConsultationRequest, 
                                   context: SMEConsultationContext) -> Dict[str, SMERecommendation]:
        """Execute parallel consultation with all relevant SME brains"""
        
        # Create consultation tasks for all target domains
        consultation_tasks = {}
        for domain in request.target_domains:
            if domain in self.sme_brains:
                # Create enhanced query with shared context
                enhanced_query = self._enhance_query_with_context(request.query, context, domain)
                consultation_tasks[domain] = asyncio.create_task(
                    self.sme_brains[domain].provide_expertise(enhanced_query)
                )
        
        # Wait for all consultations to complete with timeout
        try:
            completed_tasks = await asyncio.wait_for(
                asyncio.gather(*consultation_tasks.values(), return_exceptions=True),
                timeout=request.max_consultation_time
            )
            
            # Process results
            sme_recommendations = {}
            for domain, result in zip(consultation_tasks.keys(), completed_tasks):
                if isinstance(result, SMERecommendation):
                    sme_recommendations[domain] = result
                    context.previous_recommendations[domain] = result
                elif isinstance(result, Exception):
                    # Log error but continue with other recommendations
                    print(f"SME consultation failed for {domain}: {result}")
            
            return sme_recommendations
            
        except asyncio.TimeoutError:
            # Handle timeout - return partial results
            sme_recommendations = {}
            for domain, task in consultation_tasks.items():
                if task.done() and not task.exception():
                    sme_recommendations[domain] = task.result()
            
            return sme_recommendations
    
    async def _sequential_consultation(self, request: ConsultationRequest, 
                                     context: SMEConsultationContext) -> Dict[str, SMERecommendation]:
        """Execute sequential consultation with context passing"""
        
        sme_recommendations = {}
        
        # Determine consultation order based on domain dependencies
        consultation_order = self._determine_consultation_order(request.target_domains)
        
        for domain in consultation_order:
            if domain in self.sme_brains:
                # Create enhanced query with accumulated context
                enhanced_query = self._enhance_query_with_context(request.query, context, domain)
                
                try:
                    # Consult SME brain
                    recommendation = await asyncio.wait_for(
                        self.sme_brains[domain].provide_expertise(enhanced_query),
                        timeout=request.max_consultation_time // len(consultation_order)
                    )
                    
                    sme_recommendations[domain] = recommendation
                    context.previous_recommendations[domain] = recommendation
                    
                    # Update shared insights for next consultation
                    await self._update_shared_insights(context, domain, recommendation)
                    
                    # Record consultation in history
                    context.consultation_history.append({
                        "domain": domain,
                        "timestamp": datetime.now().isoformat(),
                        "confidence": recommendation.confidence,
                        "key_insights": self._extract_key_insights(recommendation)
                    })
                    
                except asyncio.TimeoutError:
                    print(f"SME consultation timeout for {domain}")
                    continue
                except Exception as e:
                    print(f"SME consultation error for {domain}: {e}")
                    continue
        
        return sme_recommendations
    
    async def _conditional_consultation(self, request: ConsultationRequest, 
                                      context: SMEConsultationContext) -> Dict[str, SMERecommendation]:
        """Execute conditional consultation based on previous results"""
        
        sme_recommendations = {}
        
        # Start with critical and high priority domains
        initial_domains = [
            domain for domain, priority in request.priority_domains.items()
            if priority in [ConsultationPriority.CRITICAL, ConsultationPriority.HIGH]
        ]
        
        # Consult initial domains in parallel
        if initial_domains:
            initial_request = ConsultationRequest(
                query=request.query,
                pattern=ConsultationPattern.PARALLEL,
                target_domains=initial_domains,
                priority_domains=request.priority_domains,
                context_sharing=request.context_sharing,
                max_consultation_time=request.max_consultation_time // 2
            )
            initial_recommendations = await self._parallel_consultation(initial_request, context)
            sme_recommendations.update(initial_recommendations)
        
        # Determine additional consultations based on initial results
        additional_domains = await self._determine_conditional_consultations(
            sme_recommendations, request, context
        )
        
        # Consult additional domains if needed
        if additional_domains:
            for domain in additional_domains:
                if domain in self.sme_brains:
                    enhanced_query = self._enhance_query_with_context(request.query, context, domain)
                    
                    try:
                        recommendation = await asyncio.wait_for(
                            self.sme_brains[domain].provide_expertise(enhanced_query),
                            timeout=request.max_consultation_time // 4
                        )
                        sme_recommendations[domain] = recommendation
                        context.previous_recommendations[domain] = recommendation
                        
                    except (asyncio.TimeoutError, Exception) as e:
                        print(f"Conditional SME consultation failed for {domain}: {e}")
        
        return sme_recommendations
    
    async def _hierarchical_consultation(self, request: ConsultationRequest, 
                                       context: SMEConsultationContext) -> Dict[str, SMERecommendation]:
        """Execute hierarchical consultation based on domain priorities"""
        
        sme_recommendations = {}
        
        # Group domains by priority
        priority_groups = {}
        for domain, priority in request.priority_domains.items():
            if priority not in priority_groups:
                priority_groups[priority] = []
            priority_groups[priority].append(domain)
        
        # Consult in priority order
        priority_order = [
            ConsultationPriority.CRITICAL,
            ConsultationPriority.HIGH,
            ConsultationPriority.MEDIUM,
            ConsultationPriority.LOW
        ]
        
        for priority in priority_order:
            if priority in priority_groups:
                domains = priority_groups[priority]
                
                # Consult domains in this priority level in parallel
                priority_request = ConsultationRequest(
                    query=request.query,
                    pattern=ConsultationPattern.PARALLEL,
                    target_domains=domains,
                    priority_domains=request.priority_domains,
                    context_sharing=request.context_sharing,
                    max_consultation_time=request.max_consultation_time // len(priority_order)
                )
                
                priority_recommendations = await self._parallel_consultation(priority_request, context)
                sme_recommendations.update(priority_recommendations)
                
                # Update context for next priority level
                for domain, rec in priority_recommendations.items():
                    await self._update_shared_insights(context, domain, rec)
        
        return sme_recommendations
    
    async def _collaborative_consultation(self, request: ConsultationRequest, 
                                        context: SMEConsultationContext) -> Dict[str, SMERecommendation]:
        """Execute collaborative consultation with cross-domain sharing"""
        
        sme_recommendations = {}
        
        # Phase 1: Initial parallel consultation
        initial_recommendations = await self._parallel_consultation(request, context)
        sme_recommendations.update(initial_recommendations)
        
        # Phase 2: Cross-domain collaboration
        collaboration_rounds = 2  # Number of collaboration rounds
        
        for round_num in range(collaboration_rounds):
            # Share insights between domains
            await self._facilitate_cross_domain_sharing(context, initial_recommendations)
            
            # Re-consult with shared insights
            collaborative_recommendations = {}
            for domain in request.target_domains:
                if domain in self.sme_brains:
                    # Create query with collaborative context
                    collaborative_query = self._create_collaborative_query(
                        request.query, context, domain, round_num
                    )
                    
                    try:
                        recommendation = await asyncio.wait_for(
                            self.sme_brains[domain].provide_expertise(collaborative_query),
                            timeout=request.max_consultation_time // (collaboration_rounds + 1)
                        )
                        collaborative_recommendations[domain] = recommendation
                        
                    except (asyncio.TimeoutError, Exception) as e:
                        print(f"Collaborative consultation failed for {domain} in round {round_num}: {e}")
            
            # Update recommendations with collaborative insights
            sme_recommendations.update(collaborative_recommendations)
        
        return sme_recommendations
    
    def _analyze_domain_dependencies(self, target_domains: List[str]) -> Dict[str, List[str]]:
        """Analyze dependencies between target domains"""
        dependencies = {}
        
        for domain in target_domains:
            dependencies[domain] = []
            if domain in self.domain_relationships:
                influenced_by = self.domain_relationships[domain].get("influenced_by", [])
                # Only include dependencies that are also in target domains
                dependencies[domain] = [dep for dep in influenced_by if dep in target_domains]
        
        return dependencies
    
    def _determine_consultation_order(self, target_domains: List[str]) -> List[str]:
        """Determine optimal consultation order based on dependencies"""
        
        # Topological sort based on dependencies
        dependencies = self._analyze_domain_dependencies(target_domains)
        
        # Simple dependency-based ordering
        ordered_domains = []
        remaining_domains = set(target_domains)
        
        while remaining_domains:
            # Find domains with no unresolved dependencies
            ready_domains = []
            for domain in remaining_domains:
                domain_deps = dependencies.get(domain, [])
                if not any(dep in remaining_domains for dep in domain_deps):
                    ready_domains.append(domain)
            
            if not ready_domains:
                # Circular dependency or error - add remaining domains
                ready_domains = list(remaining_domains)
            
            # Sort ready domains by priority (security first, etc.)
            ready_domains.sort(key=lambda d: self._get_domain_priority_score(d), reverse=True)
            
            ordered_domains.extend(ready_domains)
            remaining_domains -= set(ready_domains)
        
        return ordered_domains
    
    def _get_domain_priority_score(self, domain: str) -> int:
        """Get priority score for domain ordering"""
        priority_scores = {
            "security_and_compliance": 10,
            "network_infrastructure": 8,
            "database_administration": 7,
            "container_orchestration": 6,
            "cloud_services": 5,
            "observability_monitoring": 4
        }
        return priority_scores.get(domain, 0)
    
    def _enhance_query_with_context(self, original_query: SMEQuery, 
                                  context: SMEConsultationContext, domain: str) -> SMEQuery:
        """Enhance query with consultation context for specific domain"""
        
        enhanced_context = dict(original_query.context) if original_query.context else {}
        
        # Add shared insights
        if context.shared_insights:
            enhanced_context["shared_insights"] = context.shared_insights
        
        # Add previous recommendations from related domains
        related_recommendations = {}
        if domain in self.domain_relationships:
            influences = self.domain_relationships[domain].get("influenced_by", [])
            for influencing_domain in influences:
                if influencing_domain in context.previous_recommendations:
                    related_recommendations[influencing_domain] = {
                        "recommendations": context.previous_recommendations[influencing_domain].recommendations,
                        "confidence": context.previous_recommendations[influencing_domain].confidence
                    }
        
        if related_recommendations:
            enhanced_context["related_recommendations"] = related_recommendations
        
        # Add consultation history
        if context.consultation_history:
            enhanced_context["consultation_history"] = context.consultation_history[-3:]  # Last 3 consultations
        
        return SMEQuery(
            query_text=original_query.query_text,
            context=enhanced_context,
            user_id=original_query.user_id,
            session_id=original_query.session_id
        )
    
    async def _update_shared_insights(self, context: SMEConsultationContext, 
                                    domain: str, recommendation: SMERecommendation) -> None:
        """Update shared insights based on SME recommendation"""
        
        # Extract key insights from recommendation
        key_insights = self._extract_key_insights(recommendation)
        
        # Add to shared insights
        if domain not in context.shared_insights:
            context.shared_insights[domain] = {}
        
        context.shared_insights[domain].update({
            "key_recommendations": key_insights,
            "confidence_level": recommendation.confidence,
            "risk_assessment": getattr(recommendation, 'risk_assessment', 'Medium'),
            "estimated_effort": recommendation.estimated_effort
        })
    
    def _extract_key_insights(self, recommendation: SMERecommendation) -> List[str]:
        """Extract key insights from SME recommendation"""
        insights = []
        
        # Extract from recommendations
        if isinstance(recommendation.recommendations, dict):
            for key, value in recommendation.recommendations.items():
                if isinstance(value, str) and len(value) > 10:  # Meaningful recommendations
                    insights.append(f"{key}: {value}")
        
        # Extract from implementation steps (first 3)
        if recommendation.implementation_steps:
            insights.extend(recommendation.implementation_steps[:3])
        
        return insights[:5]  # Limit to 5 key insights
    
    async def _determine_conditional_consultations(self, initial_recommendations: Dict[str, SMERecommendation],
                                                 request: ConsultationRequest,
                                                 context: SMEConsultationContext) -> List[str]:
        """Determine additional consultations based on initial results"""
        
        additional_domains = []
        
        # Check if security concerns were raised
        security_concerns = any(
            "security" in str(rec.recommendations).lower() or 
            "security" in rec.risk_assessment.lower()
            for rec in initial_recommendations.values()
        )
        
        if security_concerns and "security_and_compliance" not in initial_recommendations:
            additional_domains.append("security_and_compliance")
        
        # Check if monitoring needs were identified
        monitoring_needs = any(
            "monitor" in str(rec.recommendations).lower() or
            "alert" in str(rec.recommendations).lower()
            for rec in initial_recommendations.values()
        )
        
        if monitoring_needs and "observability_monitoring" not in initial_recommendations:
            additional_domains.append("observability_monitoring")
        
        # Check if cloud services were mentioned
        cloud_mentions = any(
            "cloud" in str(rec.recommendations).lower() or
            "aws" in str(rec.recommendations).lower() or
            "azure" in str(rec.recommendations).lower()
            for rec in initial_recommendations.values()
        )
        
        if cloud_mentions and "cloud_services" not in initial_recommendations:
            additional_domains.append("cloud_services")
        
        # Only return domains that are available and not already consulted
        return [domain for domain in additional_domains 
                if domain in self.sme_brains and domain in request.target_domains]
    
    async def _facilitate_cross_domain_sharing(self, context: SMEConsultationContext,
                                             recommendations: Dict[str, SMERecommendation]) -> None:
        """Facilitate sharing of insights between domains"""
        
        # Calculate collaboration strengths
        for domain1 in recommendations:
            if domain1 in self.domain_relationships:
                collaboration_strengths = self.domain_relationships[domain1].get("collaboration_strength", {})
                
                for domain2, strength in collaboration_strengths.items():
                    if domain2 in recommendations and strength > 0.7:  # High collaboration
                        # Share insights between highly collaborative domains
                        if domain1 not in context.shared_insights:
                            context.shared_insights[domain1] = {}
                        
                        context.shared_insights[domain1][f"collaboration_with_{domain2}"] = {
                            "recommendations": getattr(recommendations[domain2], 'recommendations', {}),
                            "confidence": recommendations[domain2].confidence,
                            "collaboration_strength": strength
                        }
    
    def _create_collaborative_query(self, original_query: SMEQuery, 
                                  context: SMEConsultationContext, 
                                  domain: str, round_num: int) -> SMEQuery:
        """Create query for collaborative consultation round"""
        
        enhanced_context = dict(original_query.context) if original_query.context else {}
        
        # Add collaborative context
        enhanced_context["collaboration_round"] = round_num
        enhanced_context["collaborative_insights"] = context.shared_insights
        
        # Add specific collaboration instructions
        if domain in self.domain_relationships:
            collaboration_strengths = self.domain_relationships[domain].get("collaboration_strength", {})
            high_collaboration_domains = [
                d for d, strength in collaboration_strengths.items() 
                if strength > 0.7 and d in context.previous_recommendations
            ]
            
            if high_collaboration_domains:
                enhanced_context["collaborate_with"] = high_collaboration_domains
        
        return SMEQuery(
            query_text=f"[Collaborative Round {round_num}] {original_query.query_text}",
            context=enhanced_context,
            user_id=original_query.user_id,
            session_id=original_query.session_id
        )
    
    def _build_consultation_metadata(self, context: SMEConsultationContext, 
                                   request: ConsultationRequest) -> Dict[str, Any]:
        """Build metadata about the consultation process"""
        return {
            "consultation_pattern": request.pattern.value,
            "target_domains": request.target_domains,
            "context_sharing_enabled": request.context_sharing,
            "consultation_history_length": len(context.consultation_history),
            "shared_insights_count": len(context.shared_insights),
            "domain_dependencies": context.domain_dependencies
        }
    
    def _check_consensus(self, sme_recommendations: Dict[str, SMERecommendation]) -> bool:
        """Check if consensus was achieved between SME recommendations"""
        if len(sme_recommendations) < 2:
            return True  # Single recommendation is consensus
        
        # Simple consensus check based on confidence scores
        confidence_scores = [rec.confidence for rec in sme_recommendations.values()]
        high_confidence_count = sum(1 for conf in confidence_scores if conf >= 0.7)
        
        # Consensus if majority have high confidence (>= 0.7)
        return high_confidence_count >= len(confidence_scores) / 2
    
    def _calculate_confidence_distribution(self, sme_recommendations: Dict[str, SMERecommendation]) -> Dict[str, float]:
        """Calculate confidence distribution across SME recommendations"""
        distribution = {}
        
        for domain, rec in sme_recommendations.items():
            distribution[domain] = rec.confidence
        
        return distribution
    
    async def _handle_consultation_failure(self, request: ConsultationRequest, 
                                         error: str, start_time: datetime) -> ConsultationResult:
        """Handle consultation failure gracefully"""
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Create error resolved recommendation
        error_recommendation = ResolvedRecommendation(
            primary_recommendation={
                "domain": "error_handling",
                "description": f"Consultation failed: {error}",
                "title": "Consultation Failure",
                "recommendation_type": "error_response",
                "implementation_steps": ["Manual analysis required due to consultation failure"]
            },
            alternative_approaches=[],
            resolution_strategy=ResolutionStrategy.HIGHEST_CONFIDENCE,
            confidence=0.15,  # Low confidence as float
            reasoning=f"Consultation failure: {error}",
            implementation_notes=["Manual analysis required due to consultation failure"],
            risk_mitigation=[f"Review consultation failure: {error}"]
        )
        
        return ConsultationResult(
            resolved_recommendation=error_recommendation,
            consultation_metadata={"error": error, "pattern": request.pattern.value},
            consulted_domains=[],
            consultation_duration=duration,
            consensus_achieved=False,
            confidence_distribution={}
        )