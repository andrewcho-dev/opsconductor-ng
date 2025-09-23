"""
Cloud SME Brain - Specialized expertise for cloud services and infrastructure

This brain provides domain-specific knowledge for:
- Cloud resource management
- Cost optimization
- Scalability planning
- Cloud security best practices
"""

import asyncio
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

from ..base_sme_brain import SMEBrain, SMEQuery, SMERecommendation, SMEConfidenceLevel, SMERecommendationType
from datetime import datetime


class CloudProvider(Enum):
    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"
    MULTI_CLOUD = "multi_cloud"
    HYBRID = "hybrid"


class CloudServiceType(Enum):
    COMPUTE = "compute"
    STORAGE = "storage"
    DATABASE = "database"
    NETWORKING = "networking"
    SECURITY = "security"
    MONITORING = "monitoring"
    SERVERLESS = "serverless"
    CONTAINER = "container"


@dataclass
class CloudResourceAnalysis:
    """Analysis of cloud resource requirements and recommendations"""
    resource_type: CloudServiceType
    provider_recommendations: Dict[CloudProvider, Dict[str, Any]]
    cost_estimates: Dict[str, float]
    scalability_factors: List[str]
    security_considerations: List[str]
    performance_metrics: Dict[str, Any]


@dataclass
class CostOptimizationRecommendation:
    """Cost optimization recommendations for cloud resources"""
    current_cost_estimate: float
    optimized_cost_estimate: float
    savings_percentage: float
    optimization_strategies: List[str]
    implementation_complexity: str
    risk_assessment: str


class CloudSMEBrain(SMEBrain):
    """
    Cloud Services Subject Matter Expert Brain
    
    Provides specialized expertise in cloud infrastructure, cost optimization,
    scalability planning, and cloud security best practices.
    """
    
    domain = "cloud_services"
    expertise_areas = [
        "cloud_resource_management",
        "cost_optimization", 
        "scalability",
        "cloud_security",
        "multi_cloud_strategy",
        "cloud_migration",
        "serverless_architecture",
        "container_orchestration_cloud"
    ]
    
    def __init__(self):
        super().__init__(self.domain, self.expertise_areas)
        self.cloud_knowledge_base = self._initialize_cloud_knowledge()
        self.cost_optimization_engine = self._initialize_cost_engine()
        self.scalability_analyzer = self._initialize_scalability_analyzer()
        
    def _initialize_cloud_knowledge(self) -> Dict[str, Any]:
        """Initialize cloud-specific knowledge base"""
        return {
            "aws_services": {
                "compute": ["EC2", "Lambda", "ECS", "EKS", "Fargate"],
                "storage": ["S3", "EBS", "EFS", "FSx"],
                "database": ["RDS", "DynamoDB", "Aurora", "Redshift"],
                "networking": ["VPC", "CloudFront", "Route53", "ELB"],
                "security": ["IAM", "KMS", "Secrets Manager", "WAF"],
                "monitoring": ["CloudWatch", "X-Ray", "Config"]
            },
            "azure_services": {
                "compute": ["Virtual Machines", "Functions", "Container Instances", "AKS"],
                "storage": ["Blob Storage", "Disk Storage", "Files"],
                "database": ["SQL Database", "Cosmos DB", "PostgreSQL"],
                "networking": ["Virtual Network", "Load Balancer", "Application Gateway"],
                "security": ["Key Vault", "Security Center", "Sentinel"],
                "monitoring": ["Monitor", "Application Insights", "Log Analytics"]
            },
            "gcp_services": {
                "compute": ["Compute Engine", "Cloud Functions", "GKE", "Cloud Run"],
                "storage": ["Cloud Storage", "Persistent Disk", "Filestore"],
                "database": ["Cloud SQL", "Firestore", "BigQuery"],
                "networking": ["VPC", "Cloud Load Balancing", "Cloud CDN"],
                "security": ["Cloud KMS", "Security Command Center", "IAM"],
                "monitoring": ["Cloud Monitoring", "Cloud Logging", "Cloud Trace"]
            },
            "best_practices": {
                "cost_optimization": [
                    "Right-sizing instances",
                    "Reserved instances/committed use",
                    "Spot instances for non-critical workloads",
                    "Auto-scaling policies",
                    "Storage lifecycle management",
                    "Regular cost reviews and optimization"
                ],
                "security": [
                    "Principle of least privilege",
                    "Network segmentation",
                    "Encryption at rest and in transit",
                    "Regular security audits",
                    "Multi-factor authentication",
                    "Security monitoring and alerting"
                ],
                "scalability": [
                    "Horizontal scaling over vertical",
                    "Microservices architecture",
                    "Caching strategies",
                    "Content delivery networks",
                    "Database sharding",
                    "Load balancing"
                ]
            }
        }
    
    def _initialize_cost_engine(self) -> Dict[str, Any]:
        """Initialize cost optimization engine"""
        return {
            "pricing_models": {
                "on_demand": {"flexibility": "high", "cost": "high"},
                "reserved": {"flexibility": "low", "cost": "medium", "savings": "20-75%"},
                "spot": {"flexibility": "medium", "cost": "low", "savings": "50-90%"}
            },
            "optimization_strategies": [
                "instance_rightsizing",
                "storage_optimization",
                "network_optimization",
                "scheduling_optimization",
                "resource_tagging",
                "cost_monitoring"
            ]
        }
    
    def _initialize_scalability_analyzer(self) -> Dict[str, Any]:
        """Initialize scalability analysis engine"""
        return {
            "scaling_patterns": {
                "predictable": ["scheduled_scaling", "capacity_planning"],
                "unpredictable": ["auto_scaling", "elastic_scaling"],
                "burst": ["spot_instances", "serverless_functions"]
            },
            "performance_metrics": [
                "response_time",
                "throughput",
                "resource_utilization",
                "error_rates",
                "availability"
            ]
        }
    
    async def provide_expertise(self, query: SMEQuery) -> SMERecommendation:
        """
        Provide cloud-specific expertise based on the query
        
        Args:
            query: SME query containing the request and context
            
        Returns:
            SME recommendation with cloud-specific guidance
        """
        try:
            # Analyze the query for cloud-related intent
            cloud_analysis = await self._analyze_cloud_intent(query)
            
            # Generate recommendations based on the analysis
            recommendations = await self._generate_cloud_recommendations(cloud_analysis, query)
            
            # Calculate confidence based on query specificity and domain match
            confidence = await self._calculate_confidence(query, cloud_analysis)
            
            # Create a readable description from recommendations
            description_parts = []
            if "provider_recommendations" in recommendations:
                description_parts.extend(recommendations["provider_recommendations"])
            if "cost_optimization" in recommendations:
                description_parts.append(f"Cost optimization: {recommendations['cost_optimization'].get('summary', 'Optimize cloud costs')}")
            if "security_considerations" in recommendations:
                description_parts.append(f"Security: {recommendations['security_considerations'].get('summary', 'Implement cloud security best practices')}")
            
            description = "; ".join(description_parts) if description_parts else "Cloud services recommendations based on analysis"
            
            return SMERecommendation(
                recommendation_id=f"cloud_{query.query_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                domain=self.domain,
                query_id=query.query_id,
                recommendation_type=SMERecommendationType.BEST_PRACTICE,
                title=f"Cloud Services Recommendation for {query.domain}",
                description=description,
                rationale=cloud_analysis.get("reasoning", "Cloud services analysis"),
                confidence=self._confidence_level_to_score(confidence),
                priority="high",
                implementation_steps=recommendations.get("implementation_steps", ["Set up cloud infrastructure", "Configure services", "Implement monitoring"]),
                estimated_effort=recommendations.get("estimated_effort", "medium"),
                dependencies=recommendations.get("dependencies", [])
            )
            
        except Exception as e:
            return SMERecommendation(
                recommendation_id=f"cloud_error_{query.query_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                domain=self.domain,
                query_id=query.query_id,
                recommendation_type=SMERecommendationType.RISK_MITIGATION,
                title="Cloud Analysis Error",
                description=f"Cloud analysis failed: {str(e)}",
                rationale="Error in cloud analysis",
                confidence=0.1,
                priority="low",
                implementation_steps=["Review query and retry analysis"],
                estimated_effort="unknown",
                dependencies=[]
            )
    
    async def _analyze_cloud_intent(self, query: SMEQuery) -> Dict[str, Any]:
        """Analyze the query for cloud-related intent and requirements"""
        intent_analysis = {
            "cloud_providers": [],
            "service_types": [],
            "optimization_focus": [],
            "scalability_requirements": {},
            "security_requirements": [],
            "cost_constraints": {},
            "reasoning": ""
        }
        
        query_text = f"{query.context} {' '.join(query.specific_questions)}".lower()
        
        # Detect cloud providers
        for provider in CloudProvider:
            if provider.value in query_text or provider.name.lower() in query_text:
                intent_analysis["cloud_providers"].append(provider)
        
        # Detect service types
        for service_type in CloudServiceType:
            if service_type.value in query_text:
                intent_analysis["service_types"].append(service_type)
        
        # Detect optimization focus
        optimization_keywords = {
            "cost": ["cost", "price", "budget", "expensive", "cheap", "optimize"],
            "performance": ["performance", "speed", "latency", "throughput"],
            "scalability": ["scale", "scaling", "elastic", "auto-scale"],
            "security": ["security", "secure", "compliance", "encryption"]
        }
        
        for focus, keywords in optimization_keywords.items():
            if any(keyword in query_text for keyword in keywords):
                intent_analysis["optimization_focus"].append(focus)
        
        # Extract scalability requirements
        if "scale" in query_text:
            intent_analysis["scalability_requirements"] = {
                "auto_scaling": "auto" in query_text or "automatic" in query_text,
                "horizontal": "horizontal" in query_text,
                "vertical": "vertical" in query_text,
                "elastic": "elastic" in query_text
            }
        
        # Build reasoning
        intent_analysis["reasoning"] = self._build_analysis_reasoning(intent_analysis)
        
        return intent_analysis
    
    async def _generate_cloud_recommendations(self, analysis: Dict[str, Any], query: SMEQuery) -> Dict[str, Any]:
        """Generate cloud-specific recommendations based on analysis"""
        recommendations = {
            "primary_recommendations": [],
            "alternative_options": [],
            "cost_optimization": {},
            "security_considerations": [],
            "scalability_strategy": {},
            "implementation_steps": [],
            "risk_assessment": "Medium",
            "estimated_effort": "Medium",
            "dependencies": []
        }
        
        # Generate provider-specific recommendations
        if analysis["cloud_providers"]:
            for provider in analysis["cloud_providers"]:
                provider_recs = await self._get_provider_recommendations(provider, analysis)
                recommendations["primary_recommendations"].extend(provider_recs)
        else:
            # Multi-cloud recommendations if no specific provider mentioned
            recommendations["primary_recommendations"] = await self._get_multi_cloud_recommendations(analysis)
        
        # Generate cost optimization recommendations
        if "cost" in analysis["optimization_focus"]:
            recommendations["cost_optimization"] = await self._generate_cost_optimization(analysis)
        
        # Generate security recommendations
        if "security" in analysis["optimization_focus"] or analysis["security_requirements"]:
            recommendations["security_considerations"] = await self._generate_security_recommendations(analysis)
        
        # Generate scalability strategy
        if "scalability" in analysis["optimization_focus"] or analysis["scalability_requirements"]:
            recommendations["scalability_strategy"] = await self._generate_scalability_strategy(analysis)
        
        # Generate implementation steps
        recommendations["implementation_steps"] = await self._generate_implementation_steps(analysis, recommendations)
        
        return recommendations
    
    async def _get_provider_recommendations(self, provider: CloudProvider, analysis: Dict[str, Any]) -> List[str]:
        """Get recommendations for a specific cloud provider"""
        provider_services = self.cloud_knowledge_base.get(f"{provider.value}_services", {})
        recommendations = []
        
        for service_type in analysis["service_types"]:
            if service_type.value in provider_services:
                services = provider_services[service_type.value]
                recommendations.append(
                    f"For {service_type.value} on {provider.value.upper()}, consider: {', '.join(services[:3])}"
                )
        
        return recommendations
    
    async def _get_multi_cloud_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Get multi-cloud recommendations when no specific provider is mentioned"""
        recommendations = [
            "Consider multi-cloud strategy for vendor lock-in avoidance",
            "Evaluate AWS, Azure, and GCP based on specific service requirements",
            "Implement cloud-agnostic architecture where possible"
        ]
        
        if "cost" in analysis["optimization_focus"]:
            recommendations.append("Compare pricing across providers for cost optimization")
        
        return recommendations
    
    async def _generate_cost_optimization(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate cost optimization recommendations"""
        return {
            "strategies": [
                "Implement right-sizing for compute instances",
                "Use reserved instances for predictable workloads",
                "Leverage spot instances for fault-tolerant applications",
                "Implement auto-scaling to match demand",
                "Optimize storage with lifecycle policies"
            ],
            "monitoring": [
                "Set up cost alerts and budgets",
                "Regular cost reviews and optimization",
                "Tag resources for cost allocation"
            ],
            "estimated_savings": "20-40% typical cost reduction"
        }
    
    async def _generate_security_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate security recommendations"""
        return [
            "Implement principle of least privilege for IAM",
            "Enable encryption at rest and in transit",
            "Set up network segmentation with VPCs",
            "Implement multi-factor authentication",
            "Regular security audits and compliance checks",
            "Monitor and log all access and changes"
        ]
    
    async def _generate_scalability_strategy(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate scalability strategy"""
        strategy = {
            "approach": "horizontal_scaling_preferred",
            "components": [],
            "monitoring": []
        }
        
        if analysis["scalability_requirements"].get("auto_scaling"):
            strategy["components"].append("Auto-scaling groups with CloudWatch metrics")
            strategy["monitoring"].append("CPU, memory, and custom application metrics")
        
        if analysis["scalability_requirements"].get("elastic"):
            strategy["components"].append("Elastic load balancers")
            strategy["components"].append("Container orchestration (EKS/AKS/GKE)")
        
        return strategy
    
    async def _generate_implementation_steps(self, analysis: Dict[str, Any], recommendations: Dict[str, Any]) -> List[str]:
        """Generate implementation steps based on analysis and recommendations"""
        steps = [
            "1. Assess current infrastructure and requirements",
            "2. Design cloud architecture based on requirements",
            "3. Set up cloud accounts and basic security",
            "4. Implement core services and networking",
            "5. Configure monitoring and alerting",
            "6. Test and validate the implementation",
            "7. Migrate workloads in phases",
            "8. Optimize based on performance metrics"
        ]
        
        if "cost" in analysis["optimization_focus"]:
            steps.insert(-1, "7.5. Implement cost optimization measures")
        
        return steps
    
    def _build_analysis_reasoning(self, analysis: Dict[str, Any]) -> str:
        """Build reasoning explanation for the analysis"""
        reasoning_parts = []
        
        if analysis["cloud_providers"]:
            providers = [p.value.upper() for p in analysis["cloud_providers"]]
            reasoning_parts.append(f"Detected cloud providers: {', '.join(providers)}")
        
        if analysis["service_types"]:
            services = [s.value for s in analysis["service_types"]]
            reasoning_parts.append(f"Service types identified: {', '.join(services)}")
        
        if analysis["optimization_focus"]:
            reasoning_parts.append(f"Optimization focus: {', '.join(analysis['optimization_focus'])}")
        
        return "; ".join(reasoning_parts) if reasoning_parts else "General cloud services inquiry"
    
    async def _calculate_confidence(self, query: SMEQuery, analysis: Dict[str, Any]) -> SMEConfidenceLevel:
        """Calculate confidence level based on query analysis"""
        confidence_score = 0.0
        
        # Base confidence for cloud domain
        query_text = f"{query.context} {' '.join(query.specific_questions)}".lower()
        if any(keyword in query_text for keyword in ["cloud", "aws", "azure", "gcp"]):
            confidence_score += 0.3
        
        # Boost for specific providers
        if analysis["cloud_providers"]:
            confidence_score += 0.2
        
        # Boost for specific service types
        if analysis["service_types"]:
            confidence_score += 0.2
        
        # Boost for optimization focus
        if analysis["optimization_focus"]:
            confidence_score += 0.2
        
        # Boost for technical context
        if query.context and any(key in query.context for key in ["infrastructure", "deployment", "scaling"]):
            confidence_score += 0.1
        
        # Convert to confidence level
        if confidence_score >= 0.8:
            return SMEConfidenceLevel.HIGH
        elif confidence_score >= 0.5:
            return SMEConfidenceLevel.MEDIUM
        else:
            return SMEConfidenceLevel.LOW
    
    def _confidence_level_to_score(self, confidence_level: SMEConfidenceLevel) -> float:
        """Convert confidence level to numeric score"""
        confidence_mapping = {
            SMEConfidenceLevel.VERY_HIGH: 0.95,
            SMEConfidenceLevel.HIGH: 0.85,
            SMEConfidenceLevel.MEDIUM: 0.65,
            SMEConfidenceLevel.LOW: 0.35,
            SMEConfidenceLevel.VERY_LOW: 0.15
        }
        return confidence_mapping.get(confidence_level, 0.5)
    
    async def analyze_technical_plan(self, technical_plan: Dict[str, Any], intent_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze technical plan from cloud perspective"""
        try:
            analysis = {
                "cloud_readiness": self._assess_cloud_readiness(technical_plan),
                "recommended_services": self._recommend_cloud_services(technical_plan, intent_analysis),
                "cost_optimization": self._analyze_cost_optimization(technical_plan),
                "scalability_assessment": self._assess_scalability(technical_plan),
                "security_considerations": self._analyze_cloud_security(technical_plan),
                "migration_strategy": self._suggest_migration_strategy(technical_plan),
                "risk_assessment": self._assess_cloud_risks(technical_plan)
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Cloud technical plan analysis failed: {e}")
            return {
                "error": f"Cloud analysis failed: {str(e)}",
                "cloud_readiness": "unknown",
                "risk_assessment": "high"
            }
    
    def _assess_cloud_readiness(self, technical_plan: Dict[str, Any]) -> str:
        """Assess how ready the plan is for cloud deployment"""
        # Simple assessment based on plan characteristics
        if "containerization" in str(technical_plan).lower():
            return "high"
        elif "microservices" in str(technical_plan).lower():
            return "medium"
        else:
            return "low"
    
    def _recommend_cloud_services(self, technical_plan: Dict[str, Any], intent_analysis: Dict[str, Any]) -> List[str]:
        """Recommend specific cloud services based on the plan"""
        services = []
        plan_str = str(technical_plan).lower()
        
        if "database" in plan_str:
            services.append("managed_database")
        if "storage" in plan_str:
            services.append("object_storage")
        if "compute" in plan_str or "server" in plan_str:
            services.append("compute_instances")
        if "load" in plan_str or "traffic" in plan_str:
            services.append("load_balancer")
            
        return services
    
    def _analyze_cost_optimization(self, technical_plan: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze cost optimization opportunities"""
        return {
            "reserved_instances": "Consider reserved instances for predictable workloads",
            "auto_scaling": "Implement auto-scaling to optimize costs",
            "storage_tiering": "Use appropriate storage tiers for different data types"
        }
    
    def _assess_scalability(self, technical_plan: Dict[str, Any]) -> Dict[str, Any]:
        """Assess scalability characteristics"""
        return {
            "horizontal_scaling": "Design for horizontal scaling",
            "stateless_design": "Ensure stateless application design",
            "caching_strategy": "Implement appropriate caching layers"
        }
    
    def _analyze_cloud_security(self, technical_plan: Dict[str, Any]) -> List[str]:
        """Analyze cloud security considerations"""
        return [
            "Implement proper IAM policies",
            "Use encryption at rest and in transit",
            "Configure network security groups",
            "Enable logging and monitoring"
        ]
    
    def _suggest_migration_strategy(self, technical_plan: Dict[str, Any]) -> Dict[str, Any]:
        """Suggest cloud migration strategy"""
        return {
            "approach": "phased_migration",
            "phases": ["assessment", "pilot", "migration", "optimization"],
            "timeline": "3-6 months depending on complexity"
        }
    
    def _assess_cloud_risks(self, technical_plan: Dict[str, Any]) -> str:
        """Assess cloud-specific risks"""
        # Simple risk assessment
        if "legacy" in str(technical_plan).lower():
            return "high - legacy system migration complexity"
        elif "data" in str(technical_plan).lower():
            return "medium - data migration and compliance considerations"
        else:
            return "low - standard cloud deployment"

    async def learn_from_execution(self, execution_data: Dict[str, Any]) -> None:
        """Learn from execution results to improve cloud recommendations"""
        try:
            # Extract learning insights from execution data
            if execution_data.get("success"):
                # Successful execution - reinforce the recommendations
                await self._reinforce_successful_patterns(execution_data)
            else:
                # Failed execution - learn from the failure
                await self._learn_from_failures(execution_data)
                
            # Update knowledge base with new insights
            await self._update_cloud_knowledge(execution_data)
            
        except Exception as e:
            # Log learning failure but don't raise
            print(f"Cloud SME learning error: {e}")
    
    async def _reinforce_successful_patterns(self, execution_data: Dict[str, Any]) -> None:
        """Reinforce successful cloud implementation patterns"""
        # Implementation for reinforcing successful patterns
        pass
    
    async def _learn_from_failures(self, execution_data: Dict[str, Any]) -> None:
        """Learn from failed cloud implementations"""
        # Implementation for learning from failures
        pass
    
    async def _update_cloud_knowledge(self, execution_data: Dict[str, Any]) -> None:
        """Update cloud knowledge base with new insights"""
        # Implementation for updating knowledge base
        pass