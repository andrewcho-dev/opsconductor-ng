"""
Network SME Brain - Domain expertise for network infrastructure management

This SME brain provides specialized knowledge and recommendations for:
- Network topology design and optimization
- Load balancing strategies
- Connectivity optimization
- Bandwidth management
- Network security and monitoring
"""

from typing import Dict, List, Any, Optional
import asyncio
import logging
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

from ..base_sme_brain import SMEBrain, SMEQuery, SMERecommendation, SMERecommendationType, SMEConfidence, SMEConfidenceCalculator

logger = logging.getLogger(__name__)


class NetworkComplexity(Enum):
    """Network complexity levels"""
    SIMPLE = "simple"           # Single network, basic configuration
    MODERATE = "moderate"       # Multiple networks, load balancing
    COMPLEX = "complex"         # Multi-region, advanced routing
    ENTERPRISE = "enterprise"   # Global networks, high availability


class NetworkTopologyType(Enum):
    """Network topology types"""
    FLAT = "flat"
    HIERARCHICAL = "hierarchical"
    MESH = "mesh"
    HYBRID = "hybrid"
    MICROSERVICES = "microservices"


@dataclass
class NetworkAnalysis:
    """Network infrastructure analysis result"""
    topology_type: NetworkTopologyType
    complexity_level: NetworkComplexity
    bandwidth_requirements: Dict[str, Any]
    load_balancing_strategy: str
    security_considerations: List[str]
    optimization_opportunities: List[str]
    risk_factors: List[str]


class NetworkSMEBrain(SMEBrain):
    """
    Network SME Brain for network infrastructure expertise
    
    Provides domain-specific knowledge for:
    - Network topology design and analysis
    - Load balancing and traffic management
    - Connectivity optimization
    - Bandwidth planning and management
    - Network security and compliance
    """
    
    def __init__(self, llm_engine=None):
        super().__init__(
            domain="network_infrastructure",
            expertise_areas=[
                "network_topology",
                "load_balancing", 
                "connectivity_optimization",
                "bandwidth_management",
                "network_security",
                "traffic_analysis",
                "routing_optimization",
                "network_monitoring"
            ],
            llm_engine=llm_engine
        )
        
        # Network-specific knowledge base
        self.topology_patterns = {
            "microservices": {
                "recommended_patterns": ["service_mesh", "api_gateway", "circuit_breaker"],
                "load_balancing": ["round_robin", "least_connections", "weighted"],
                "security": ["mutual_tls", "network_policies", "ingress_control"]
            },
            "enterprise": {
                "recommended_patterns": ["hierarchical", "redundant_paths", "failover"],
                "load_balancing": ["geographic", "application_aware", "health_based"],
                "security": ["network_segmentation", "zero_trust", "monitoring"]
            },
            "cloud_native": {
                "recommended_patterns": ["overlay_networks", "software_defined", "elastic"],
                "load_balancing": ["auto_scaling", "traffic_splitting", "canary"],
                "security": ["encryption_in_transit", "network_policies", "audit_logging"]
            }
        }
        
        self.bandwidth_optimization_strategies = {
            "compression": ["gzip", "brotli", "custom_compression"],
            "caching": ["cdn", "edge_caching", "application_caching"],
            "traffic_shaping": ["qos_policies", "bandwidth_limiting", "priority_queues"],
            "protocol_optimization": ["http2", "grpc", "websockets"]
        }
        
        self.load_balancing_algorithms = {
            "round_robin": {"complexity": "simple", "use_case": "uniform_traffic"},
            "least_connections": {"complexity": "moderate", "use_case": "variable_session_length"},
            "weighted_round_robin": {"complexity": "moderate", "use_case": "heterogeneous_servers"},
            "ip_hash": {"complexity": "simple", "use_case": "session_persistence"},
            "geographic": {"complexity": "complex", "use_case": "global_distribution"},
            "application_aware": {"complexity": "complex", "use_case": "intelligent_routing"}
        }
    
    async def provide_expertise(self, query: SMEQuery) -> SMERecommendation:
        """
        Provide network infrastructure expertise
        
        Args:
            query: SME query containing network-related request
            
        Returns:
            SMERecommendation with network-specific analysis and recommendations
        """
        try:
            # Analyze network requirements
            network_analysis = await self._analyze_network_requirements(query)
            
            # Generate network recommendations
            recommendations = await self._generate_network_recommendations(network_analysis, query)
            
            # Assess network risks
            risk_assessment = await self._assess_network_risks(network_analysis, query)
            
            # Calculate confidence
            confidence = await self._calculate_network_confidence(network_analysis, query)
            
            return await self._create_recommendation(
                query=query,
                recommendation_type=SMERecommendationType.BEST_PRACTICE,
                title="Network Infrastructure Recommendations",
                description=f"Network analysis and recommendations based on requirements",
                rationale="Optimized network configuration for performance and security",
                implementation_steps=recommendations,
                priority="medium",
                validation_criteria=await self._define_validation_criteria(network_analysis),
                dependencies=await self._identify_network_dependencies(network_analysis)
            )
            
        except Exception as e:
            # Return low-confidence recommendation on error
            return await self._create_recommendation(
                query=query,
                recommendation_type=SMERecommendationType.TROUBLESHOOTING_STEP,
                title="Network Analysis Error",
                description=f"Unable to provide network expertise due to: {str(e)}",
                rationale="Error occurred during network analysis",
                implementation_steps=["Manual network review required"],
                priority="low",
                validation_criteria=["Manual network validation"],
                dependencies=["Network analysis tools"],
                risks_if_ignored=["Network analysis failed"]
            )
    
    async def _analyze_network_requirements(self, query: SMEQuery) -> NetworkAnalysis:
        """Analyze network infrastructure requirements"""
        
        # Determine topology type
        topology_type = self._determine_topology_type(query)
        
        # Assess complexity level
        complexity_level = self._assess_network_complexity(query)
        
        # Analyze bandwidth requirements
        bandwidth_requirements = self._analyze_bandwidth_requirements(query)
        
        # Determine load balancing strategy
        load_balancing_strategy = self._determine_load_balancing_strategy(query, complexity_level)
        
        # Identify security considerations
        security_considerations = self._identify_security_considerations(query, topology_type)
        
        # Find optimization opportunities
        optimization_opportunities = self._identify_optimization_opportunities(query)
        
        # Assess risk factors
        risk_factors = self._assess_risk_factors(query, complexity_level)
        
        return NetworkAnalysis(
            topology_type=topology_type,
            complexity_level=complexity_level,
            bandwidth_requirements=bandwidth_requirements,
            load_balancing_strategy=load_balancing_strategy,
            security_considerations=security_considerations,
            optimization_opportunities=optimization_opportunities,
            risk_factors=risk_factors
        )
    
    def _determine_topology_type(self, query: SMEQuery) -> NetworkTopologyType:
        """Determine appropriate network topology type"""
        context = query.context.lower()
        
        if any(term in context for term in ["microservice", "service mesh", "api gateway"]):
            return NetworkTopologyType.MICROSERVICES
        elif any(term in context for term in ["mesh", "peer-to-peer", "distributed"]):
            return NetworkTopologyType.MESH
        elif any(term in context for term in ["hierarchical", "tier", "layer"]):
            return NetworkTopologyType.HIERARCHICAL
        elif any(term in context for term in ["hybrid", "mixed", "multiple"]):
            return NetworkTopologyType.HYBRID
        else:
            return NetworkTopologyType.FLAT
    
    def _assess_network_complexity(self, query: SMEQuery) -> NetworkComplexity:
        """Assess network complexity level"""
        context = query.context.lower()
        
        complexity_indicators = {
            NetworkComplexity.ENTERPRISE: [
                "global", "multi-region", "enterprise", "high availability",
                "disaster recovery", "compliance", "audit"
            ],
            NetworkComplexity.COMPLEX: [
                "multi-zone", "load balancer", "auto-scaling", "monitoring",
                "advanced routing", "traffic management"
            ],
            NetworkComplexity.MODERATE: [
                "multiple networks", "load balancing", "redundancy",
                "failover", "scaling"
            ],
            NetworkComplexity.SIMPLE: [
                "single network", "basic", "simple", "minimal"
            ]
        }
        
        for complexity, indicators in complexity_indicators.items():
            if any(indicator in context for indicator in indicators):
                return complexity
        
        return NetworkComplexity.MODERATE  # Default
    
    def _analyze_bandwidth_requirements(self, query: SMEQuery) -> Dict[str, Any]:
        """Analyze bandwidth requirements"""
        context = query.context.lower()
        
        requirements = {
            "estimated_bandwidth": "moderate",
            "peak_traffic_handling": "standard",
            "optimization_needed": False,
            "monitoring_required": True
        }
        
        # High bandwidth indicators
        if any(term in context for term in ["high traffic", "large files", "streaming", "video"]):
            requirements["estimated_bandwidth"] = "high"
            requirements["peak_traffic_handling"] = "advanced"
            requirements["optimization_needed"] = True
        
        # Low bandwidth indicators
        elif any(term in context for term in ["minimal", "basic", "small scale"]):
            requirements["estimated_bandwidth"] = "low"
            requirements["peak_traffic_handling"] = "basic"
        
        return requirements
    
    def _determine_load_balancing_strategy(self, query: SMEQuery, complexity: NetworkComplexity) -> str:
        """Determine appropriate load balancing strategy"""
        context = query.context.lower()
        
        # Check for specific load balancing requirements
        if "session persistence" in context or "sticky session" in context:
            return "ip_hash"
        elif "geographic" in context or "global" in context:
            return "geographic"
        elif "intelligent" in context or "application aware" in context:
            return "application_aware"
        elif complexity == NetworkComplexity.ENTERPRISE:
            return "weighted_round_robin"
        elif complexity == NetworkComplexity.COMPLEX:
            return "least_connections"
        else:
            return "round_robin"
    
    def _identify_security_considerations(self, query: SMEQuery, topology: NetworkTopologyType) -> List[str]:
        """Identify network security considerations"""
        considerations = [
            "Network segmentation",
            "Firewall configuration",
            "Encryption in transit"
        ]
        
        if topology == NetworkTopologyType.MICROSERVICES:
            considerations.extend([
                "Service mesh security",
                "Mutual TLS authentication",
                "Network policies"
            ])
        elif topology == NetworkTopologyType.MESH:
            considerations.extend([
                "Peer authentication",
                "Distributed security",
                "Trust boundaries"
            ])
        
        context = query.context.lower()
        if any(term in context for term in ["compliance", "audit", "regulation"]):
            considerations.extend([
                "Compliance monitoring",
                "Audit logging",
                "Access control"
            ])
        
        return considerations
    
    def _identify_optimization_opportunities(self, query: SMEQuery) -> List[str]:
        """Identify network optimization opportunities"""
        opportunities = []
        context = query.context.lower()
        
        if any(term in context for term in ["slow", "latency", "performance"]):
            opportunities.extend([
                "CDN implementation",
                "Edge caching",
                "Protocol optimization"
            ])
        
        if any(term in context for term in ["bandwidth", "traffic", "congestion"]):
            opportunities.extend([
                "Traffic compression",
                "QoS policies",
                "Bandwidth management"
            ])
        
        if any(term in context for term in ["scaling", "growth", "expansion"]):
            opportunities.extend([
                "Auto-scaling configuration",
                "Elastic load balancing",
                "Capacity planning"
            ])
        
        return opportunities or ["Network monitoring", "Performance baseline"]
    
    def _assess_risk_factors(self, query: SMEQuery, complexity: NetworkComplexity) -> List[str]:
        """Assess network risk factors"""
        risks = []
        
        if complexity in [NetworkComplexity.COMPLEX, NetworkComplexity.ENTERPRISE]:
            risks.extend([
                "Configuration complexity",
                "Single points of failure",
                "Scalability bottlenecks"
            ])
        
        context = query.context.lower()
        if any(term in context for term in ["public", "internet", "external"]):
            risks.extend([
                "External attack surface",
                "DDoS vulnerability",
                "Data exposure"
            ])
        
        if any(term in context for term in ["legacy", "old", "deprecated"]):
            risks.extend([
                "Legacy system integration",
                "Protocol compatibility",
                "Security vulnerabilities"
            ])
        
        return risks or ["Standard network risks"]
    
    async def _generate_network_recommendations(self, analysis: NetworkAnalysis, query: SMEQuery) -> List[str]:
        """Generate network-specific recommendations"""
        recommendations = []
        
        # Topology recommendations
        if analysis.topology_type == NetworkTopologyType.MICROSERVICES:
            recommendations.extend([
                "Implement service mesh for inter-service communication",
                "Configure API gateway for external traffic",
                "Set up network policies for service isolation"
            ])
        
        # Load balancing recommendations
        lb_config = self.load_balancing_algorithms.get(analysis.load_balancing_strategy, {})
        recommendations.append(f"Implement {analysis.load_balancing_strategy} load balancing")
        
        # Bandwidth optimization
        if analysis.bandwidth_requirements.get("optimization_needed"):
            recommendations.extend([
                "Implement traffic compression",
                "Configure CDN for static content",
                "Set up QoS policies for critical traffic"
            ])
        
        # Security recommendations (without pattern matching)
        recommendations.extend([
            f"Implement {consideration}" for consideration in analysis.security_considerations[:3]
        ])
        
        # Optimization recommendations
        recommendations.extend(analysis.optimization_opportunities[:2])
        
        return recommendations
    
    async def _assess_network_risks(self, analysis: NetworkAnalysis, query: SMEQuery) -> Dict[str, List[str]]:
        """Assess network-related risks using LLM intelligence"""
        if not self.llm_engine:
            raise Exception("LLM engine required for network risk assessment - NO FALLBACKS ALLOWED")
        
        try:
            risk_prompt = f"""
            Analyze the following network risks and categorize them by severity:
            
            Risk Factors: {analysis.risk_factors}
            Query Context: {query.context}
            Network Topology: {analysis.topology_type}
            
            Categorize each risk as high, medium, or low severity.
            Also provide specific mitigation strategies for these risks.
            
            Return as JSON with arrays: high_risk, medium_risk, low_risk, mitigation_strategies
            """
            
            import json
            response = await self.llm_engine.generate(risk_prompt, max_tokens=600)
            response_text = response["generated_text"]
            risk_assessment = json.loads(response_text)
            
            # Ensure all required keys are present
            default_assessment = {
                "high_risk": [],
                "medium_risk": [],
                "low_risk": [],
                "mitigation_strategies": [
                    "Implement network monitoring",
                    "Regular security assessments",
                    "Redundancy planning",
                    "Performance testing"
                ]
            }
            
            for key in default_assessment:
                if key not in risk_assessment:
                    risk_assessment[key] = default_assessment[key]
            
            return risk_assessment
            
        except Exception as e:
            logger.error(f"LLM network risk assessment failed: {e}")
            return {
                "high_risk": [],
                "medium_risk": [],
                "low_risk": analysis.risk_factors,
                "mitigation_strategies": [
                    "Implement network monitoring",
                    "Regular security assessments",
                    "Redundancy planning",
                    "Performance testing"
                ]
            }
    
    async def _calculate_network_confidence(self, analysis: NetworkAnalysis, query: SMEQuery) -> SMEConfidence:
        """Calculate confidence in network recommendations"""
        base_confidence = 0.8
        
        # Adjust based on complexity
        if analysis.complexity_level == NetworkComplexity.ENTERPRISE:
            base_confidence -= 0.1
        elif analysis.complexity_level == NetworkComplexity.SIMPLE:
            base_confidence += 0.1
        
        # Adjust based on risk factors
        high_risk_count = len([r for r in analysis.risk_factors if "vulnerability" in r.lower()])
        base_confidence -= (high_risk_count * 0.05)
        
        # Ensure confidence is within bounds
        confidence_score = max(0.3, min(0.95, base_confidence))
        
        reasoning = f"Network analysis confidence based on {analysis.complexity_level.value} complexity"
        if high_risk_count > 0:
            reasoning += f" with {high_risk_count} high-risk factors identified"
        
        return SMEConfidence(score=confidence_score, reasoning=reasoning)
    
    async def _generate_implementation_notes(self, analysis: NetworkAnalysis) -> List[str]:
        """Generate implementation notes"""
        notes = [
            f"Network topology: {analysis.topology_type.value}",
            f"Complexity level: {analysis.complexity_level.value}",
            f"Load balancing: {analysis.load_balancing_strategy}"
        ]
        
        if analysis.bandwidth_requirements.get("optimization_needed"):
            notes.append("Bandwidth optimization required")
        
        if len(analysis.security_considerations) > 3:
            notes.append("Multiple security considerations identified")
        
        return notes
    
    async def _suggest_alternative_approaches(self, analysis: NetworkAnalysis) -> List[str]:
        """Suggest alternative network approaches"""
        alternatives = []
        
        if analysis.topology_type == NetworkTopologyType.MICROSERVICES:
            alternatives.append("Consider serverless architecture for reduced network complexity")
        
        if analysis.complexity_level == NetworkComplexity.ENTERPRISE:
            alternatives.append("Evaluate cloud-native networking solutions")
        
        if "geographic" in analysis.load_balancing_strategy:
            alternatives.append("Consider edge computing for reduced latency")
        
        return alternatives or ["Standard network implementation"]
    
    async def _identify_network_dependencies(self, analysis: NetworkAnalysis) -> List[str]:
        """Identify network implementation dependencies"""
        dependencies = [
            "Network infrastructure provisioning",
            "DNS configuration",
            "SSL/TLS certificates"
        ]
        
        if analysis.topology_type == NetworkTopologyType.MICROSERVICES:
            dependencies.extend([
                "Service mesh installation",
                "Container networking",
                "Service discovery"
            ])
        
        if analysis.complexity_level in [NetworkComplexity.COMPLEX, NetworkComplexity.ENTERPRISE]:
            dependencies.extend([
                "Load balancer configuration",
                "Monitoring setup",
                "Backup connectivity"
            ])
        
        return dependencies
    
    async def _define_validation_criteria(self, analysis: NetworkAnalysis) -> List[str]:
        """Define network validation criteria"""
        criteria = [
            "Network connectivity verification",
            "Load balancing functionality test",
            "Security policy validation"
        ]
        
        if analysis.bandwidth_requirements.get("optimization_needed"):
            criteria.extend([
                "Bandwidth utilization test",
                "Performance benchmarking"
            ])
        
        if analysis.complexity_level == NetworkComplexity.ENTERPRISE:
            criteria.extend([
                "Failover testing",
                "Disaster recovery validation"
            ])
        
        return criteria
    
    async def analyze_technical_plan(self, technical_plan: Dict[str, Any], intent_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze technical plan from network infrastructure perspective
        
        Args:
            technical_plan: Technical plan from Technical Brain
            intent_analysis: Original intent analysis
            
        Returns:
            Analysis results with network recommendations and risk assessment
        """
        try:
            # Extract network-related requirements from technical plan
            network_requirements = {
                "application_type": technical_plan.get("deployment_type", "standard"),
                "expected_load": intent_analysis.get("scale_requirements", {}).get("expected_load", "medium"),
                "security_requirements": intent_analysis.get("security_requirements", "standard"),
                "availability_requirements": intent_analysis.get("availability_requirements", "standard")
            }
            
            # Perform network analysis
            network_analysis_query = SMEQuery(
                query_id=f"network_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                domain="network_infrastructure",
                context=f"Technical plan analysis for {technical_plan.get('deployment_type', 'application')}",
                technical_plan=technical_plan,
                intent_analysis=intent_analysis
            )
            network_analysis = await self._analyze_network_requirements(network_analysis_query)
            
            # Generate network-specific recommendations
            recommendations = await self.provide_expertise(SMEQuery(
                query_id=f"network_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                domain="network_infrastructure",
                context=f"Technical plan analysis for {technical_plan.get('deployment_type', 'application')}",
                technical_plan=technical_plan,
                intent_analysis=intent_analysis
            ))
            
            # Assess network risks
            risk_assessment = await self._assess_network_risks(network_analysis, SMEQuery(
                query_id="risk_assessment",
                domain="network_infrastructure", 
                context="Risk assessment",
                technical_plan=technical_plan,
                intent_analysis=intent_analysis
            ))
            
            # Calculate confidence based on analysis
            analysis_confidence = await self._calculate_network_confidence(network_analysis, network_analysis_query)
            
            return {
                "domain": "network_infrastructure",
                "analysis_confidence": analysis_confidence,
                "network_analysis": {
                    "topology_type": network_analysis.topology_type.value,
                    "complexity_level": network_analysis.complexity_level.value,
                    "bandwidth_requirements": network_analysis.bandwidth_requirements,
                    "load_balancing_strategy": network_analysis.load_balancing_strategy,
                    "security_considerations": network_analysis.security_considerations,
                    "optimization_opportunities": network_analysis.optimization_opportunities,
                    "risk_factors": network_analysis.risk_factors
                },
                "recommendations": [recommendations.to_dict()] if hasattr(recommendations, 'to_dict') else [],
                "risk_assessment": risk_assessment,
                "implementation_priority": "high" if network_analysis.complexity_level in [NetworkComplexity.COMPLEX, NetworkComplexity.ENTERPRISE] else "medium",
                "estimated_effort": "high" if network_analysis.complexity_level == NetworkComplexity.ENTERPRISE else "medium"
            }
            
        except Exception as e:
            return {
                "domain": "network_infrastructure",
                "analysis_confidence": 0.2,
                "error": f"Network analysis failed: {str(e)}",
                "recommendations": [],
                "risk_assessment": {"high_risk": [f"Network analysis error: {str(e)}"]},
                "implementation_priority": "low",
                "estimated_effort": "unknown"
            }
    
    async def analyze_network_requirements(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze network requirements and provide specific recommendations.
        
        Args:
            requirements: Dictionary containing network requirements and context
            
        Returns:
            Dictionary with network analysis and recommendations
        """
        try:
            # Extract network-specific requirements
            network_type = requirements.get("network_type", "general")
            performance_requirements = requirements.get("performance", {})
            security_requirements = requirements.get("security", {})
            scalability_requirements = requirements.get("scalability", {})
            
            # Analyze network architecture needs
            architecture_recommendations = []
            if network_type == "high_performance":
                architecture_recommendations.extend([
                    "Implement load balancing for traffic distribution",
                    "Configure network segmentation for performance isolation",
                    "Optimize routing protocols for minimal latency"
                ])
            elif network_type == "secure":
                architecture_recommendations.extend([
                    "Implement network access control (NAC)",
                    "Configure VPN tunnels for secure communication",
                    "Deploy intrusion detection systems (IDS)"
                ])
            
            # Performance analysis
            performance_analysis = {
                "bandwidth_requirements": performance_requirements.get("bandwidth", "standard"),
                "latency_targets": performance_requirements.get("latency", "< 100ms"),
                "throughput_expectations": performance_requirements.get("throughput", "standard")
            }
            
            # Security analysis
            security_analysis = {
                "encryption_requirements": security_requirements.get("encryption", "TLS 1.3"),
                "access_control": security_requirements.get("access_control", "role_based"),
                "monitoring_needs": security_requirements.get("monitoring", "standard")
            }
            
            # Calculate confidence based on requirement clarity
            confidence = 0.8
            if not performance_requirements:
                confidence -= 0.1
            if not security_requirements:
                confidence -= 0.1
            
            return {
                "domain": "network_infrastructure",
                "analysis_type": "requirements_analysis",
                "confidence": confidence,
                "architecture_recommendations": architecture_recommendations,
                "performance_analysis": performance_analysis,
                "security_analysis": security_analysis,
                "implementation_priority": "high" if network_type in ["secure", "high_performance"] else "medium",
                "estimated_timeline": "2-4 weeks",
                "risk_factors": [
                    "Network downtime during implementation",
                    "Configuration complexity",
                    "Performance impact during transition"
                ]
            }
            
        except Exception as e:
            return {
                "domain": "network_infrastructure",
                "analysis_type": "requirements_analysis",
                "confidence": 0.2,
                "error": f"Network requirements analysis failed: {str(e)}",
                "architecture_recommendations": [],
                "risk_factors": [f"Analysis error: {str(e)}"]
            }
    
    async def learn_from_execution(self, execution_data: Dict[str, Any]):
        """Learn from network execution results"""
        try:
            # Extract network-specific metrics
            network_metrics = execution_data.get("network_metrics", {})
            
            # Update knowledge base based on results
            if network_metrics.get("latency_improvement"):
                await self.learning_engine.record_success(
                    "latency_optimization",
                    network_metrics["latency_improvement"]
                )
            
            if network_metrics.get("bandwidth_utilization"):
                await self.learning_engine.record_metric(
                    "bandwidth_efficiency",
                    network_metrics["bandwidth_utilization"]
                )
            
            # Learn from failures
            if execution_data.get("status") == "failed":
                failure_reason = execution_data.get("error", "Unknown network failure")
                await self.learning_engine.record_failure(
                    "network_implementation",
                    failure_reason
                )
            
        except Exception as e:
            # Log learning error but don't fail
            print(f"Network SME learning error: {e}")