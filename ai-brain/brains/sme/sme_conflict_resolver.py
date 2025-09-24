"""
SME Conflict Resolver - Advanced conflict resolution for SME brain recommendations

This module handles conflicts between different SME brain recommendations,
providing intelligent resolution strategies and consensus building.
"""

import asyncio
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import json

from ..base_sme_brain import SMERecommendation, SMEConfidenceLevel


class ConflictType(Enum):
    CONTRADICTORY = "contradictory"  # Recommendations directly contradict each other
    OVERLAPPING = "overlapping"      # Recommendations have overlapping concerns
    PRIORITY = "priority"            # Different priorities for same resources
    APPROACH = "approach"            # Different approaches to same problem
    DEPENDENCY = "dependency"        # Conflicting dependency requirements


class ResolutionStrategy(Enum):
    HIGHEST_CONFIDENCE = "highest_confidence"
    CONSENSUS_BUILDING = "consensus_building"
    DOMAIN_PRIORITY = "domain_priority"
    RISK_MINIMIZATION = "risk_minimization"
    COST_OPTIMIZATION = "cost_optimization"
    HYBRID_APPROACH = "hybrid_approach"


@dataclass
class ConflictAnalysis:
    """Analysis of conflicts between SME recommendations"""
    conflict_type: ConflictType
    conflicting_domains: List[str]
    conflict_description: str
    impact_assessment: str
    resolution_complexity: str
    affected_areas: List[str]


@dataclass
class ResolvedRecommendation:
    """Resolved recommendation after conflict resolution"""
    primary_recommendation: Dict[str, Any]
    alternative_approaches: List[Dict[str, Any]]
    resolution_strategy: ResolutionStrategy
    confidence: float  # Changed from confidence_level to confidence (float)
    reasoning: str
    implementation_notes: List[str]
    risk_mitigation: List[str]


class SMEConflictResolver:
    """
    Advanced conflict resolution system for SME brain recommendations
    
    Handles conflicts between different SME brains by analyzing the nature
    of conflicts and applying appropriate resolution strategies.
    """
    
    def __init__(self):
        self.domain_priorities = self._initialize_domain_priorities()
        self.resolution_strategies = self._initialize_resolution_strategies()
        self.conflict_patterns = self._initialize_conflict_patterns()
        
    def _initialize_domain_priorities(self) -> Dict[str, int]:
        """Initialize domain priority weights for conflict resolution"""
        return {
            "security_and_compliance": 10,  # Highest priority - security first
            "network_infrastructure": 8,    # High priority - foundation
            "database_administration": 7,   # High priority - data integrity
            "container_orchestration": 6,   # Medium-high priority
            "cloud_services": 5,            # Medium priority
            "observability_monitoring": 4,  # Medium priority - visibility
        }
    
    def _initialize_resolution_strategies(self) -> Dict[ResolutionStrategy, Dict[str, Any]]:
        """Initialize resolution strategy configurations"""
        return {
            ResolutionStrategy.HIGHEST_CONFIDENCE: {
                "description": "Select recommendation with highest confidence",
                "use_when": ["clear_confidence_difference", "single_domain_expertise"],
                "risk_level": "low"
            },
            ResolutionStrategy.CONSENSUS_BUILDING: {
                "description": "Build consensus by combining compatible recommendations",
                "use_when": ["overlapping_recommendations", "complementary_approaches"],
                "risk_level": "medium"
            },
            ResolutionStrategy.DOMAIN_PRIORITY: {
                "description": "Prioritize based on domain importance hierarchy",
                "use_when": ["security_conflicts", "foundational_infrastructure"],
                "risk_level": "low"
            },
            ResolutionStrategy.RISK_MINIMIZATION: {
                "description": "Choose approach that minimizes overall risk",
                "use_when": ["high_risk_scenarios", "critical_systems"],
                "risk_level": "low"
            },
            ResolutionStrategy.COST_OPTIMIZATION: {
                "description": "Balance recommendations for cost effectiveness",
                "use_when": ["budget_constraints", "resource_optimization"],
                "risk_level": "medium"
            },
            ResolutionStrategy.HYBRID_APPROACH: {
                "description": "Combine multiple recommendations into hybrid solution",
                "use_when": ["complex_scenarios", "multi_domain_requirements"],
                "risk_level": "high"
            }
        }
    
    def _initialize_conflict_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Initialize common conflict patterns and their characteristics"""
        return {
            "security_vs_performance": {
                "domains": ["security_and_compliance", "observability_monitoring"],
                "common_conflicts": ["encryption_overhead", "monitoring_access", "audit_logging"],
                "resolution_bias": "security_first"
            },
            "cost_vs_reliability": {
                "domains": ["cloud_services", "database_administration"],
                "common_conflicts": ["redundancy_costs", "backup_strategies", "scaling_approaches"],
                "resolution_bias": "reliability_first"
            },
            "scalability_vs_simplicity": {
                "domains": ["container_orchestration", "network_infrastructure"],
                "common_conflicts": ["architecture_complexity", "deployment_strategies", "maintenance_overhead"],
                "resolution_bias": "balanced_approach"
            },
            "cloud_vs_onpremise": {
                "domains": ["cloud_services", "network_infrastructure"],
                "common_conflicts": ["data_sovereignty", "cost_models", "control_requirements"],
                "resolution_bias": "hybrid_approach"
            }
        }
    
    async def resolve_conflicts(self, sme_recommendations: Dict[str, SMERecommendation]) -> ResolvedRecommendation:
        """
        Resolve conflicts between multiple SME recommendations
        
        Args:
            sme_recommendations: Dictionary of domain -> SME recommendation
            
        Returns:
            Resolved recommendation with conflict resolution applied
        """
        try:
            # Analyze conflicts between recommendations
            conflicts = await self._analyze_conflicts(sme_recommendations)
            
            if not conflicts:
                # No conflicts - combine recommendations harmoniously
                return await self._combine_harmonious_recommendations(sme_recommendations)
            
            # Determine best resolution strategy
            resolution_strategy = await self._determine_resolution_strategy(conflicts, sme_recommendations)
            
            # Apply resolution strategy
            resolved_recommendation = await self._apply_resolution_strategy(
                resolution_strategy, conflicts, sme_recommendations
            )
            
            return resolved_recommendation
            
        except Exception as e:
            # NO FALLBACK - FAIL HARD AS REQUESTED
            raise Exception(f"SME conflict resolution FAILED - NO FALLBACKS ALLOWED: {e}")
    
    async def _analyze_conflicts(self, sme_recommendations: Dict[str, SMERecommendation]) -> List[ConflictAnalysis]:
        """Analyze conflicts between SME recommendations"""
        conflicts = []
        domains = list(sme_recommendations.keys())
        
        # Compare each pair of recommendations
        for i, domain1 in enumerate(domains):
            for domain2 in domains[i+1:]:
                rec1 = sme_recommendations[domain1]
                rec2 = sme_recommendations[domain2]
                
                conflict = await self._detect_conflict(domain1, rec1, domain2, rec2)
                if conflict:
                    conflicts.append(conflict)
        
        return conflicts
    
    async def _detect_conflict(self, domain1: str, rec1: SMERecommendation, 
                             domain2: str, rec2: SMERecommendation) -> Optional[ConflictAnalysis]:
        """Detect conflicts between two specific recommendations"""
        
        # Check for contradictory recommendations
        contradictions = await self._check_contradictions(rec1, rec2)
        if contradictions:
            return ConflictAnalysis(
                conflict_type=ConflictType.CONTRADICTORY,
                conflicting_domains=[domain1, domain2],
                conflict_description=f"Contradictory recommendations: {contradictions}",
                impact_assessment="High - may lead to implementation failures",
                resolution_complexity="High",
                affected_areas=self._extract_affected_areas(rec1, rec2)
            )
        
        # Check for overlapping concerns
        overlaps = await self._check_overlaps(rec1, rec2)
        if overlaps:
            return ConflictAnalysis(
                conflict_type=ConflictType.OVERLAPPING,
                conflicting_domains=[domain1, domain2],
                conflict_description=f"Overlapping concerns: {overlaps}",
                impact_assessment="Medium - may cause resource conflicts",
                resolution_complexity="Medium",
                affected_areas=self._extract_affected_areas(rec1, rec2)
            )
        
        # Check for priority conflicts
        priority_conflicts = await self._check_priority_conflicts(rec1, rec2)
        if priority_conflicts:
            return ConflictAnalysis(
                conflict_type=ConflictType.PRIORITY,
                conflicting_domains=[domain1, domain2],
                conflict_description=f"Priority conflicts: {priority_conflicts}",
                impact_assessment="Medium - may affect implementation order",
                resolution_complexity="Low",
                affected_areas=self._extract_affected_areas(rec1, rec2)
            )
        
        # Check for approach conflicts
        approach_conflicts = await self._check_approach_conflicts(rec1, rec2)
        if approach_conflicts:
            return ConflictAnalysis(
                conflict_type=ConflictType.APPROACH,
                conflicting_domains=[domain1, domain2],
                conflict_description=f"Different approaches: {approach_conflicts}",
                impact_assessment="Low - different valid approaches",
                resolution_complexity="Medium",
                affected_areas=self._extract_affected_areas(rec1, rec2)
            )
        
        return None
    
    async def _check_contradictions(self, rec1: SMERecommendation, rec2: SMERecommendation) -> List[str]:
        """Check for direct contradictions between recommendations"""
        contradictions = []
        
        # Convert recommendations to comparable format
        rec1_text = rec1.description.lower()
        rec2_text = rec2.description.lower()
        
        # Check for contradictory keywords
        contradiction_pairs = [
            ("enable", "disable"),
            ("allow", "deny"),
            ("public", "private"),
            ("encrypted", "unencrypted"),
            ("centralized", "distributed"),
            ("synchronous", "asynchronous"),
            ("scale_up", "scale_down"),
            ("increase", "decrease")
        ]
        
        for positive, negative in contradiction_pairs:
            if positive in rec1_text and negative in rec2_text:
                contradictions.append(f"{positive} vs {negative}")
            elif negative in rec1_text and positive in rec2_text:
                contradictions.append(f"{negative} vs {positive}")
        
        return contradictions
    
    async def _check_overlaps(self, rec1: SMERecommendation, rec2: SMERecommendation) -> List[str]:
        """Check for overlapping concerns between recommendations"""
        overlaps = []
        
        # Check for overlapping implementation steps
        steps1 = set(rec1.implementation_steps)
        steps2 = set(rec2.implementation_steps)
        common_steps = steps1.intersection(steps2)
        
        if common_steps:
            overlaps.extend([f"Common implementation: {step}" for step in common_steps])
        
        # Check for overlapping dependencies
        deps1 = set(rec1.dependencies)
        deps2 = set(rec2.dependencies)
        common_deps = deps1.intersection(deps2)
        
        if common_deps:
            overlaps.extend([f"Common dependency: {dep}" for dep in common_deps])
        
        return overlaps
    
    async def _check_priority_conflicts(self, rec1: SMERecommendation, rec2: SMERecommendation) -> List[str]:
        """Check for priority conflicts between recommendations"""
        conflicts = []
        
        # Check estimated effort conflicts
        if rec1.estimated_effort == "High" and rec2.estimated_effort == "High":
            conflicts.append("Both recommendations require high effort")
        
        # Check risk assessment conflicts (without pattern matching)
        if "High" in str(rec1.risk_assessment) and "High" in str(rec2.risk_assessment):
            conflicts.append("Both recommendations have high risk")
        
        return conflicts
    
    async def _check_approach_conflicts(self, rec1: SMERecommendation, rec2: SMERecommendation) -> List[str]:
        """Check for different approaches to similar problems"""
        conflicts = []
        
        # This is a simplified check - in practice, would use more sophisticated analysis
        rec1_approaches = self._extract_approaches(rec1)
        rec2_approaches = self._extract_approaches(rec2)
        
        # Check for different approaches to similar goals
        common_goals = set(rec1_approaches.keys()).intersection(set(rec2_approaches.keys()))
        for goal in common_goals:
            if rec1_approaches[goal] != rec2_approaches[goal]:
                conflicts.append(f"Different approaches for {goal}: {rec1_approaches[goal]} vs {rec2_approaches[goal]}")
        
        return conflicts
    
    def _extract_approaches(self, recommendation: SMERecommendation) -> Dict[str, str]:
        """Extract approaches from recommendation (simplified)"""
        approaches = {}
        
        # This is a simplified extraction - would be more sophisticated in practice
        rec_text = recommendation.description.lower()
        
        if "monitoring" in rec_text:
            if "centralized" in rec_text:
                approaches["monitoring"] = "centralized"
            elif "distributed" in rec_text:
                approaches["monitoring"] = "distributed"
        
        if "scaling" in rec_text:
            if "horizontal" in rec_text:
                approaches["scaling"] = "horizontal"
            elif "vertical" in rec_text:
                approaches["scaling"] = "vertical"
        
        return approaches
    
    def _extract_affected_areas(self, rec1: SMERecommendation, rec2: SMERecommendation) -> List[str]:
        """Extract areas affected by both recommendations"""
        areas = set()
        
        # Extract from implementation steps
        for step in rec1.implementation_steps + rec2.implementation_steps:
            if "network" in step.lower():
                areas.add("network")
            if "security" in step.lower():
                areas.add("security")
            if "database" in step.lower():
                areas.add("database")
            if "monitoring" in step.lower():
                areas.add("monitoring")
            if "storage" in step.lower():
                areas.add("storage")
        
        return list(areas)
    
    async def _determine_resolution_strategy(self, conflicts: List[ConflictAnalysis], 
                                           sme_recommendations: Dict[str, SMERecommendation]) -> ResolutionStrategy:
        """Determine the best resolution strategy based on conflicts"""
        
        # If no conflicts, use consensus building
        if not conflicts:
            return ResolutionStrategy.CONSENSUS_BUILDING
        
        # Check for security conflicts - prioritize security
        security_conflicts = [c for c in conflicts if "security" in c.conflicting_domains]
        if security_conflicts:
            return ResolutionStrategy.DOMAIN_PRIORITY
        
        # Check for high-risk conflicts - minimize risk
        high_risk_conflicts = [c for c in conflicts if "High" in c.impact_assessment]
        if high_risk_conflicts:
            return ResolutionStrategy.RISK_MINIMIZATION
        
        # Check confidence levels
        confidence_levels = [self._score_to_confidence(rec.confidence) for rec in sme_recommendations.values()]
        if len(set(confidence_levels)) > 1:  # Different confidence levels
            return ResolutionStrategy.HIGHEST_CONFIDENCE
        
        # Check for contradictory conflicts
        contradictory_conflicts = [c for c in conflicts if c.conflict_type == ConflictType.CONTRADICTORY]
        if contradictory_conflicts:
            return ResolutionStrategy.HYBRID_APPROACH
        
        # Default to consensus building
        return ResolutionStrategy.CONSENSUS_BUILDING
    
    async def _apply_resolution_strategy(self, strategy: ResolutionStrategy, 
                                       conflicts: List[ConflictAnalysis],
                                       sme_recommendations: Dict[str, SMERecommendation]) -> ResolvedRecommendation:
        """Apply the selected resolution strategy"""
        
        if strategy == ResolutionStrategy.HIGHEST_CONFIDENCE:
            return await self._resolve_by_highest_confidence(sme_recommendations)
        
        elif strategy == ResolutionStrategy.DOMAIN_PRIORITY:
            return await self._resolve_by_domain_priority(sme_recommendations)
        
        elif strategy == ResolutionStrategy.RISK_MINIMIZATION:
            return await self._resolve_by_risk_minimization(sme_recommendations)
        
        elif strategy == ResolutionStrategy.CONSENSUS_BUILDING:
            return await self._resolve_by_consensus(sme_recommendations)
        
        elif strategy == ResolutionStrategy.HYBRID_APPROACH:
            return await self._resolve_by_hybrid_approach(conflicts, sme_recommendations)
        
        else:
            # Use highest confidence resolution as default strategy
            return await self._resolve_by_highest_confidence(sme_recommendations)
    
    async def _resolve_by_highest_confidence(self, sme_recommendations: Dict[str, SMERecommendation]) -> ResolvedRecommendation:
        """Resolve by selecting the recommendation with highest confidence"""
        
        # Find highest confidence recommendation
        best_domain = max(sme_recommendations.keys(), 
                         key=lambda d: sme_recommendations[d].confidence)
        best_rec = sme_recommendations[best_domain]
        
        # Create alternatives from other recommendations
        alternatives = []
        for domain, rec in sme_recommendations.items():
            if domain != best_domain:
                alternatives.append({
                    "domain": domain,
                    "description": rec.description,
                    "confidence": rec.confidence
                })
        
        return ResolvedRecommendation(
            primary_recommendation={
                "domain": best_domain,
                "description": best_rec.description,
                "title": best_rec.title,
                "recommendation_type": best_rec.recommendation_type,
                "implementation_steps": best_rec.implementation_steps
            },
            alternative_approaches=alternatives,
            resolution_strategy=ResolutionStrategy.HIGHEST_CONFIDENCE,
            confidence=best_rec.confidence,
            reasoning=f"Selected {best_domain} recommendation due to highest confidence ({best_rec.confidence})",
            implementation_notes=best_rec.implementation_steps,
            risk_mitigation=[f"Monitor implementation of {best_domain} recommendations closely"]
        )
    
    async def _resolve_by_domain_priority(self, sme_recommendations: Dict[str, SMERecommendation]) -> ResolvedRecommendation:
        """Resolve by domain priority (security first, etc.)"""
        
        # Find highest priority domain
        best_domain = max(sme_recommendations.keys(), 
                         key=lambda d: self.domain_priorities.get(d, 0))
        best_rec = sme_recommendations[best_domain]
        
        # Integrate compatible recommendations from other domains
        integrated_description = best_rec.description
        implementation_steps = list(best_rec.implementation_steps)
        
        for domain, rec in sme_recommendations.items():
            if domain != best_domain:
                # Add compatible implementation steps
                for step in rec.implementation_steps:
                    if step not in implementation_steps:
                        implementation_steps.append(f"[{domain}] {step}")
        
        return ResolvedRecommendation(
            primary_recommendation={
                "domain": best_domain,
                "description": integrated_description,
                "title": best_rec.title,
                "recommendation_type": best_rec.recommendation_type,
                "implementation_steps": implementation_steps
            },
            alternative_approaches=[],
            resolution_strategy=ResolutionStrategy.DOMAIN_PRIORITY,
            confidence=best_rec.confidence,
            reasoning=f"Prioritized {best_domain} due to domain importance, integrated compatible recommendations",
            implementation_notes=implementation_steps,
            risk_mitigation=[f"Ensure {best_domain} requirements are not compromised by other domain needs"]
        )
    
    async def _resolve_by_risk_minimization(self, sme_recommendations: Dict[str, SMERecommendation]) -> ResolvedRecommendation:
        """Resolve by minimizing overall risk"""
        
        # Find lowest risk recommendation
        best_domain = min(sme_recommendations.keys(), 
                         key=lambda d: self._risk_to_score(sme_recommendations[d].risk_assessment))
        best_rec = sme_recommendations[best_domain]
        
        # Add risk mitigation from all domains
        risk_mitigation = []
        for domain, rec in sme_recommendations.items():
            risk_mitigation.append(f"[{domain}] {rec.risk_assessment}")
        
        return ResolvedRecommendation(
            primary_recommendation={
                "domain": best_domain,
                "description": best_rec.description,
                "title": best_rec.title,
                "recommendation_type": best_rec.recommendation_type,
                "implementation_steps": best_rec.implementation_steps
            },
            alternative_approaches=[],
            resolution_strategy=ResolutionStrategy.RISK_MINIMIZATION,
            confidence=best_rec.confidence,
            reasoning=f"Selected {best_domain} recommendation to minimize risk",
            implementation_notes=best_rec.implementation_steps,
            risk_mitigation=risk_mitigation
        )
    
    async def _resolve_by_consensus(self, sme_recommendations: Dict[str, SMERecommendation]) -> ResolvedRecommendation:
        """Resolve by building consensus between recommendations"""
        
        # Combine all recommendations
        combined_descriptions = []
        all_implementation_steps = []
        all_dependencies = []
        
        for domain, rec in sme_recommendations.items():
            # Add descriptions with domain prefix
            combined_descriptions.append(f"[{domain}] {rec.description}")
            
            # Combine implementation steps
            for step in rec.implementation_steps:
                step_with_domain = f"[{domain}] {step}"
                if step_with_domain not in all_implementation_steps:
                    all_implementation_steps.append(step_with_domain)
            
            # Combine dependencies
            for dep in rec.dependencies:
                if dep not in all_dependencies:
                    all_dependencies.append(dep)
        
        # Calculate average confidence
        confidence_scores = [rec.confidence for rec in sme_recommendations.values()]
        avg_confidence_score = sum(confidence_scores) / len(confidence_scores)
        
        return ResolvedRecommendation(
            primary_recommendation={
                "domain": "consensus",
                "description": "; ".join(combined_descriptions),
                "title": "Consensus Recommendation",
                "recommendation_type": "consensus_building",
                "implementation_steps": all_implementation_steps
            },
            alternative_approaches=[],
            resolution_strategy=ResolutionStrategy.CONSENSUS_BUILDING,
            confidence=avg_confidence_score,
            reasoning="Built consensus by combining compatible recommendations from all domains",
            implementation_notes=all_implementation_steps,
            risk_mitigation=["Monitor integration points between different domain recommendations"]
        )
    
    async def _resolve_by_hybrid_approach(self, conflicts: List[ConflictAnalysis],
                                        sme_recommendations: Dict[str, SMERecommendation]) -> ResolvedRecommendation:
        """Resolve by creating a hybrid approach that addresses conflicts"""
        
        # Create hybrid recommendation that addresses conflicts
        hybrid_recommendations = {}
        implementation_notes = []
        risk_mitigation = []
        
        # For each conflict, create a hybrid solution
        for conflict in conflicts:
            if conflict.conflict_type == ConflictType.CONTRADICTORY:
                # Create compromise solution
                hybrid_key = f"hybrid_{conflict.conflict_description.replace(' ', '_')}"
                hybrid_recommendations[hybrid_key] = "Implement phased approach addressing both concerns"
                implementation_notes.append(f"Phase 1: Address {conflict.conflicting_domains[0]} concerns")
                implementation_notes.append(f"Phase 2: Address {conflict.conflicting_domains[1]} concerns")
                risk_mitigation.append(f"Monitor for issues during transition between phases")
        
        # Add non-conflicting descriptions
        hybrid_descriptions = []
        for domain, rec in sme_recommendations.items():
            if not any(domain in str(conflict.conflict_description) for conflict in conflicts):
                hybrid_descriptions.append(f"[{domain}] {rec.description}")
        
        return ResolvedRecommendation(
            primary_recommendation={
                "domain": "hybrid",
                "description": "; ".join(hybrid_descriptions),
                "title": "Hybrid Approach Recommendation",
                "recommendation_type": "hybrid_approach",
                "implementation_steps": implementation_notes
            },
            alternative_approaches=[],
            resolution_strategy=ResolutionStrategy.HYBRID_APPROACH,
            confidence=0.5,  # Medium confidence as float
            reasoning="Created hybrid approach to address contradictory recommendations",
            implementation_notes=implementation_notes,
            risk_mitigation=risk_mitigation
        )
    
    async def _combine_harmonious_recommendations(self, sme_recommendations: Dict[str, SMERecommendation]) -> ResolvedRecommendation:
        """Combine recommendations when there are no conflicts"""
        
        # Simply combine all recommendations
        combined_descriptions = []
        all_implementation_steps = []
        all_dependencies = []
        
        for domain, rec in sme_recommendations.items():
            combined_descriptions.append(f"[{domain}] {rec.description}")
            all_implementation_steps.extend(rec.implementation_steps)
            all_dependencies.extend(rec.dependencies)
        
        # Remove duplicates while preserving order
        all_implementation_steps = list(dict.fromkeys(all_implementation_steps))
        all_dependencies = list(dict.fromkeys(all_dependencies))
        
        # Calculate highest confidence
        highest_confidence = max(rec.confidence for rec in sme_recommendations.values())
        
        return ResolvedRecommendation(
            primary_recommendation={
                "domain": "harmonious",
                "description": "; ".join(combined_descriptions),
                "title": "Harmonious Combined Recommendation",
                "recommendation_type": "consensus_building",
                "implementation_steps": all_implementation_steps
            },
            alternative_approaches=[],
            resolution_strategy=ResolutionStrategy.CONSENSUS_BUILDING,
            confidence=highest_confidence,
            reasoning="No conflicts detected - combined all SME recommendations harmoniously",
            implementation_notes=all_implementation_steps,
            risk_mitigation=["Monitor for unexpected interactions between different domain implementations"]
        )
    

    
    def _confidence_to_score(self, confidence: SMEConfidenceLevel) -> float:
        """Convert confidence level to numeric score"""
        confidence_scores = {
            SMEConfidenceLevel.LOW: 0.3,
            SMEConfidenceLevel.MEDIUM: 0.6,
            SMEConfidenceLevel.HIGH: 0.9
        }
        return confidence_scores.get(confidence, 0.3)
    
    def _score_to_confidence(self, score: float) -> SMEConfidenceLevel:
        """Convert numeric score to confidence level"""
        if score >= 0.8:
            return SMEConfidenceLevel.HIGH
        elif score >= 0.5:
            return SMEConfidenceLevel.MEDIUM
        else:
            return SMEConfidenceLevel.LOW
    
    def _risk_to_score(self, risk_assessment: str) -> float:
        """Convert risk assessment to numeric score (lower is better)"""
        risk_assessment_lower = risk_assessment.lower()
        if "low" in risk_assessment_lower:
            return 0.3
        elif "medium" in risk_assessment_lower:
            return 0.6
        elif "high" in risk_assessment_lower:
            return 0.9
        else:
            return 0.6  # Default to medium risk