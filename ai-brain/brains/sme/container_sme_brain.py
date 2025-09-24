"""
Container SME Brain - Multi-Brain AI Architecture

Subject Matter Expert brain for container orchestration and containerization.
Provides expertise on Docker, Kubernetes, container security, and resource optimization.

Phase 1 Week 3 Implementation - Following exact roadmap specification.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..base_sme_brain import (
    SMEBrain, SMEQuery, SMERecommendation, SMERecommendationType, ExecutionData
)

logger = logging.getLogger(__name__)

class ContainerSMEBrain(SMEBrain):
    """
    Container SME Brain - Expert in container orchestration
    
    Domain: container_orchestration
    Expertise Areas: docker_configuration, kubernetes_deployment, 
                    container_security, resource_optimization, scaling_strategies
    """
    
    domain = "container_orchestration"
    expertise_areas = [
        "docker_configuration",
        "kubernetes_deployment", 
        "container_security",
        "resource_optimization",
        "scaling_strategies",
        "container_networking",
        "persistent_storage",
        "service_mesh",
        "container_monitoring",
        "image_management"
    ]
    
    def __init__(self, llm_engine=None):
        super().__init__(self.domain, self.expertise_areas, llm_engine)
        self._load_container_knowledge()
        logger.info("Container SME Brain initialized with LLM intelligence")
    
    def _load_container_knowledge(self):
        """Load container-specific knowledge base"""
        # Docker best practices
        self.knowledge_base.knowledge_entries.update({
            "docker_security_best_practices": {
                "content": "Use non-root users, scan images for vulnerabilities, use minimal base images, implement proper secrets management",
                "tags": ["docker", "security", "best_practices"],
                "confidence": 0.9
            },
            "docker_resource_limits": {
                "content": "Always set memory and CPU limits, use health checks, implement proper logging configuration",
                "tags": ["docker", "resources", "performance"],
                "confidence": 0.85
            },
            "kubernetes_deployment_patterns": {
                "content": "Use rolling updates, implement readiness and liveness probes, configure resource requests and limits",
                "tags": ["kubernetes", "deployment", "reliability"],
                "confidence": 0.9
            },
            "container_networking_security": {
                "content": "Use network policies, implement service mesh for secure communication, avoid privileged containers",
                "tags": ["networking", "security", "kubernetes"],
                "confidence": 0.8
            }
        })
        
        # Common failure patterns
        self.knowledge_base.failure_patterns = {
            "oom_kills": {
                "pattern": "Container killed due to out of memory",
                "causes": ["Insufficient memory limits", "Memory leaks", "Incorrect resource requests"],
                "solutions": ["Increase memory limits", "Profile application memory usage", "Set appropriate requests"]
            },
            "image_pull_failures": {
                "pattern": "Failed to pull container image",
                "causes": ["Network connectivity", "Authentication issues", "Image not found"],
                "solutions": ["Check network connectivity", "Verify image registry credentials", "Confirm image exists"]
            }
        }
    
    async def provide_expertise(self, query: SMEQuery) -> List[SMERecommendation]:
        """
        Provide container-specific expertise
        
        Args:
            query: SME query containing context and requirements
            
        Returns:
            List of container-specific recommendations
        """
        try:
            recommendations = []
            
            # Track query
            self.query_history.append(query)
            
            # Analyze query context
            context_analysis = await self._analyze_container_context(query)
            
            # Generate recommendations based on context
            if "deployment" in query.context.lower():
                recommendations.extend(await self._recommend_deployment_config(query, context_analysis))
            
            if "security" in query.context.lower():
                recommendations.extend(await self._recommend_security_config(query, context_analysis))
            
            if "performance" in query.context.lower():
                recommendations.extend(await self._recommend_performance_config(query, context_analysis))
            
            if "scaling" in query.context.lower():
                recommendations.extend(await self._recommend_scaling_config(query, context_analysis))
            
            # If no specific context, provide general recommendations
            if not recommendations:
                recommendations.extend(await self._provide_general_recommendations(query, context_analysis))
            
            # Limit to max recommendations
            return recommendations[:self.max_recommendations_per_query]
            
        except Exception as e:
            logger.error(f"Error providing container expertise: {str(e)}")
            return []
    
    async def analyze_technical_plan(self, technical_plan: Dict[str, Any], intent_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze technical plan from container perspective
        
        Args:
            technical_plan: Technical plan from Technical Brain
            intent_analysis: Original intent analysis
            
        Returns:
            Container-specific analysis and recommendations
        """
        try:
            analysis = {
                "domain": self.domain,
                "analysis_id": f"container_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "container_relevance": 0.0,
                "recommendations": [],
                "risk_assessment": {},
                "optimization_opportunities": [],
                "compliance_checks": []
            }
            
            # Check if plan involves containers
            plan_text = str(technical_plan).lower()
            container_keywords = ["docker", "kubernetes", "container", "pod", "deployment", "service"]
            
            relevance_score = sum(1 for keyword in container_keywords if keyword in plan_text)
            analysis["container_relevance"] = min(1.0, relevance_score / len(container_keywords))
            
            if analysis["container_relevance"] > 0.3:
                # Analyze container-specific aspects
                analysis["recommendations"] = await self._analyze_container_steps(technical_plan)
                analysis["risk_assessment"] = await self._assess_container_risks(technical_plan, intent_analysis)
                analysis["optimization_opportunities"] = await self._identify_optimizations(technical_plan)
                analysis["compliance_checks"] = await self._check_compliance(technical_plan)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing technical plan: {str(e)}")
            return {"domain": self.domain, "error": str(e)}
    
    async def _analyze_container_context(self, query: SMEQuery) -> Dict[str, Any]:
        """Analyze container-specific context from query"""
        context = {
            "container_technology": "unknown",
            "deployment_environment": query.environment,
            "scale_requirements": "medium",
            "security_requirements": "standard",
            "performance_requirements": "standard"
        }
        
        query_text = query.context.lower()
        
        # Detect container technology
        if "kubernetes" in query_text or "k8s" in query_text:
            context["container_technology"] = "kubernetes"
        elif "docker" in query_text:
            context["container_technology"] = "docker"
        elif "openshift" in query_text:
            context["container_technology"] = "openshift"
        
        # Detect scale requirements
        if any(word in query_text for word in ["scale", "high availability", "cluster"]):
            context["scale_requirements"] = "high"
        elif any(word in query_text for word in ["single", "simple", "basic"]):
            context["scale_requirements"] = "low"
        
        # Detect security requirements
        if any(word in query_text for word in ["secure", "security", "compliance", "audit"]):
            context["security_requirements"] = "high"
        
        # Detect performance requirements
        if any(word in query_text for word in ["performance", "fast", "optimize", "efficient"]):
            context["performance_requirements"] = "high"
        
        return context
    
    async def _recommend_deployment_config(self, query: SMEQuery, context: Dict[str, Any]) -> List[SMERecommendation]:
        """Recommend deployment configuration"""
        recommendations = []
        
        if context["container_technology"] == "kubernetes":
            recommendations.append(await self._create_recommendation(
                query=query,
                recommendation_type=SMERecommendationType.BEST_PRACTICE,
                title="Kubernetes Deployment Best Practices",
                description="Implement proper Kubernetes deployment configuration with health checks and resource limits",
                rationale="Ensures reliable deployments with proper monitoring and resource management",
                implementation_steps=[
                    "Configure readiness and liveness probes",
                    "Set appropriate resource requests and limits",
                    "Use rolling update strategy",
                    "Implement proper labels and selectors",
                    "Configure pod disruption budgets"
                ],
                priority="high",
                validation_criteria=[
                    "Pods start successfully",
                    "Health checks pass",
                    "Resource usage within limits"
                ],
                risks_if_ignored=[
                    "Deployment failures",
                    "Resource contention",
                    "Service disruptions"
                ],
                tags=["kubernetes", "deployment", "reliability"]
            ))
        
        elif context["container_technology"] == "docker":
            recommendations.append(await self._create_recommendation(
                query=query,
                recommendation_type=SMERecommendationType.CONFIGURATION_GUIDANCE,
                title="Docker Container Configuration",
                description="Configure Docker containers with proper security and resource settings",
                rationale="Ensures secure and efficient container operation",
                implementation_steps=[
                    "Use non-root user in container",
                    "Set memory and CPU limits",
                    "Configure health checks",
                    "Use minimal base images",
                    "Implement proper logging"
                ],
                priority="medium",
                validation_criteria=[
                    "Container starts without root privileges",
                    "Resource limits enforced",
                    "Health checks functional"
                ],
                tags=["docker", "security", "configuration"]
            ))
        
        return recommendations
    
    async def _recommend_security_config(self, query: SMEQuery, context: Dict[str, Any]) -> List[SMERecommendation]:
        """Recommend security configuration"""
        recommendations = []
        
        recommendations.append(await self._create_recommendation(
            query=query,
            recommendation_type=SMERecommendationType.SECURITY_REQUIREMENT,
            title="Container Security Hardening",
            description="Implement comprehensive container security measures",
            rationale="Protects against container-specific security threats and vulnerabilities",
            implementation_steps=[
                "Scan container images for vulnerabilities",
                "Use minimal base images (distroless when possible)",
                "Run containers as non-root users",
                "Implement network policies",
                "Use secrets management for sensitive data",
                "Enable container runtime security monitoring"
            ],
            priority="critical" if context["security_requirements"] == "high" else "high",
            validation_criteria=[
                "No critical vulnerabilities in images",
                "Containers run as non-root",
                "Network policies enforced",
                "Secrets properly managed"
            ],
            risks_if_ignored=[
                "Container breakouts",
                "Data breaches",
                "Privilege escalation",
                "Network-based attacks"
            ],
            tags=["security", "hardening", "compliance"]
        ))
        
        return recommendations
    
    async def _recommend_performance_config(self, query: SMEQuery, context: Dict[str, Any]) -> List[SMERecommendation]:
        """Recommend performance configuration"""
        recommendations = []
        
        recommendations.append(await self._create_recommendation(
            query=query,
            recommendation_type=SMERecommendationType.PERFORMANCE_OPTIMIZATION,
            title="Container Performance Optimization",
            description="Optimize container performance through proper resource management and configuration",
            rationale="Ensures efficient resource utilization and optimal application performance",
            implementation_steps=[
                "Set appropriate CPU and memory requests/limits",
                "Use multi-stage builds to reduce image size",
                "Implement proper caching strategies",
                "Configure JVM settings for Java applications",
                "Use init containers for initialization tasks",
                "Implement horizontal pod autoscaling"
            ],
            priority="medium",
            validation_criteria=[
                "Resource utilization within optimal range",
                "Application response times meet SLA",
                "Autoscaling triggers work correctly"
            ],
            risks_if_ignored=[
                "Poor application performance",
                "Resource waste",
                "Scaling issues"
            ],
            tags=["performance", "optimization", "resources"]
        ))
        
        return recommendations
    
    async def _recommend_scaling_config(self, query: SMEQuery, context: Dict[str, Any]) -> List[SMERecommendation]:
        """Recommend scaling configuration"""
        recommendations = []
        
        if context["scale_requirements"] == "high":
            recommendations.append(await self._create_recommendation(
                query=query,
                recommendation_type=SMERecommendationType.BEST_PRACTICE,
                title="High Availability Container Scaling",
                description="Configure containers for high availability and automatic scaling",
                rationale="Ensures service availability and handles varying load demands",
                implementation_steps=[
                    "Configure Horizontal Pod Autoscaler (HPA)",
                    "Set up cluster autoscaling",
                    "Implement pod anti-affinity rules",
                    "Configure multiple replicas across zones",
                    "Set up load balancing",
                    "Implement circuit breakers"
                ],
                priority="high",
                validation_criteria=[
                    "Autoscaling responds to load changes",
                    "Services remain available during scaling",
                    "Load distributed evenly"
                ],
                dependencies=["monitoring_setup", "load_balancer_config"],
                tags=["scaling", "high_availability", "load_balancing"]
            ))
        
        return recommendations
    
    async def _provide_general_recommendations(self, query: SMEQuery, context: Dict[str, Any]) -> List[SMERecommendation]:
        """Provide general container recommendations"""
        recommendations = []
        
        recommendations.append(await self._create_recommendation(
            query=query,
            recommendation_type=SMERecommendationType.BEST_PRACTICE,
            title="Container Best Practices",
            description="Follow container best practices for reliable and secure deployments",
            rationale="Ensures consistent, secure, and maintainable container deployments",
            implementation_steps=[
                "Use official base images when possible",
                "Keep images small and focused",
                "Tag images with specific versions",
                "Implement proper logging and monitoring",
                "Use health checks",
                "Follow the principle of least privilege"
            ],
            priority="medium",
            validation_criteria=[
                "Images follow security best practices",
                "Containers are properly monitored",
                "Deployments are reproducible"
            ],
            tags=["best_practices", "general", "reliability"]
        ))
        
        return recommendations
    
    async def _analyze_container_steps(self, technical_plan: Dict[str, Any]) -> List[str]:
        """Analyze technical plan steps for container-specific recommendations"""
        recommendations = []
        
        steps = technical_plan.get("steps", [])
        for step in steps:
            step_desc = step.get("description", "").lower()
            
            if "docker" in step_desc or "container" in step_desc:
                recommendations.append("Ensure proper container security configuration")
                recommendations.append("Implement resource limits and health checks")
            
            if "kubernetes" in step_desc or "deploy" in step_desc:
                recommendations.append("Use rolling deployment strategy")
                recommendations.append("Configure pod disruption budgets")
        
        return list(set(recommendations))  # Remove duplicates
    
    async def _assess_container_risks(self, technical_plan: Dict[str, Any], intent_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Assess container-specific risks"""
        risks = {
            "security_risks": [],
            "performance_risks": [],
            "availability_risks": [],
            "overall_risk_level": "medium"
        }
        
        plan_text = str(technical_plan).lower()
        
        # Security risks
        if "privileged" in plan_text:
            risks["security_risks"].append("Privileged container usage detected")
        if "root" in plan_text:
            risks["security_risks"].append("Potential root user usage")
        
        # Performance risks
        if "limit" not in plan_text:
            risks["performance_risks"].append("No resource limits specified")
        
        # Availability risks
        if "replica" not in plan_text and "scale" not in plan_text:
            risks["availability_risks"].append("Single instance deployment risk")
        
        # Determine overall risk level
        total_risks = len(risks["security_risks"]) + len(risks["performance_risks"]) + len(risks["availability_risks"])
        if total_risks > 3:
            risks["overall_risk_level"] = "high"
        elif total_risks > 1:
            risks["overall_risk_level"] = "medium"
        else:
            risks["overall_risk_level"] = "low"
        
        return risks
    
    async def _identify_optimizations(self, technical_plan: Dict[str, Any]) -> List[str]:
        """Identify container optimization opportunities"""
        optimizations = []
        
        plan_text = str(technical_plan).lower()
        
        if "image" in plan_text:
            optimizations.append("Consider using multi-stage builds to reduce image size")
        
        if "cpu" not in plan_text and "memory" not in plan_text:
            optimizations.append("Add resource requests and limits for better scheduling")
        
        if "cache" not in plan_text:
            optimizations.append("Implement layer caching for faster builds")
        
        return optimizations
    
    async def _check_compliance(self, technical_plan: Dict[str, Any]) -> List[str]:
        """Check container compliance requirements"""
        compliance_checks = []
        
        plan_text = str(technical_plan).lower()
        
        if "security" in plan_text:
            compliance_checks.append("Verify container security scanning is enabled")
            compliance_checks.append("Ensure non-root user configuration")
        
        if "production" in plan_text:
            compliance_checks.append("Validate resource limits are set")
            compliance_checks.append("Confirm health checks are implemented")
        
        return compliance_checks