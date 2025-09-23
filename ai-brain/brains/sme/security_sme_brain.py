"""
Security SME Brain - Multi-Brain AI Architecture

Subject Matter Expert brain for security and compliance.
Provides expertise on threat modeling, vulnerability assessment, compliance validation, and access control.

Phase 1 Week 3 Implementation - Following exact roadmap specification.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..base_sme_brain import (
    SMEBrain, SMEQuery, SMERecommendation, SMERecommendationType, ExecutionData
)

logger = logging.getLogger(__name__)

class SecuritySMEBrain(SMEBrain):
    """
    Security SME Brain - Expert in security and compliance
    
    Domain: security_and_compliance
    Expertise Areas: threat_modeling, vulnerability_assessment, 
                    compliance_validation, access_control, encryption_standards
    """
    
    domain = "security_and_compliance"
    expertise_areas = [
        "threat_modeling",
        "vulnerability_assessment",
        "compliance_validation",
        "access_control",
        "encryption_standards",
        "incident_response",
        "security_monitoring",
        "penetration_testing",
        "security_hardening",
        "data_protection"
    ]
    
    def __init__(self):
        super().__init__(self.domain, self.expertise_areas)
        self._load_security_knowledge()
        logger.info("Security SME Brain initialized")
    
    def _load_security_knowledge(self):
        """Load security-specific knowledge base"""
        # Security best practices
        self.knowledge_base.knowledge_entries.update({
            "access_control_principles": {
                "content": "Implement principle of least privilege, use role-based access control, enable multi-factor authentication",
                "tags": ["access_control", "authentication", "authorization"],
                "confidence": 0.95
            },
            "encryption_standards": {
                "content": "Use AES-256 for data at rest, TLS 1.3 for data in transit, implement proper key management",
                "tags": ["encryption", "data_protection", "standards"],
                "confidence": 0.9
            },
            "vulnerability_management": {
                "content": "Regular security scanning, patch management, vulnerability assessment, penetration testing",
                "tags": ["vulnerability", "scanning", "patching"],
                "confidence": 0.85
            },
            "incident_response_framework": {
                "content": "Preparation, identification, containment, eradication, recovery, lessons learned",
                "tags": ["incident_response", "framework", "process"],
                "confidence": 0.9
            },
            "compliance_frameworks": {
                "content": "SOC 2, ISO 27001, PCI DSS, GDPR, HIPAA compliance requirements and controls",
                "tags": ["compliance", "frameworks", "regulations"],
                "confidence": 0.8
            }
        })
        
        # Security threat patterns
        self.knowledge_base.failure_patterns = {
            "privilege_escalation": {
                "pattern": "Unauthorized elevation of user privileges",
                "causes": ["Misconfigured permissions", "Unpatched vulnerabilities", "Weak access controls"],
                "solutions": ["Implement least privilege", "Regular access reviews", "Patch management"]
            },
            "data_breach": {
                "pattern": "Unauthorized access to sensitive data",
                "causes": ["Weak encryption", "Poor access controls", "Unpatched systems"],
                "solutions": ["Strong encryption", "Access monitoring", "Security hardening"]
            },
            "malware_infection": {
                "pattern": "Malicious software execution",
                "causes": ["Unpatched systems", "Poor endpoint protection", "Social engineering"],
                "solutions": ["Endpoint protection", "User training", "Network segmentation"]
            }
        }
    
    async def provide_expertise(self, query: SMEQuery) -> List[SMERecommendation]:
        """
        Provide security-specific expertise
        
        Args:
            query: SME query containing context and requirements
            
        Returns:
            List of security-specific recommendations
        """
        try:
            recommendations = []
            
            # Track query
            self.query_history.append(query)
            
            # Analyze security context
            security_analysis = await self._analyze_security_context(query)
            
            # Generate recommendations based on context
            if "access" in query.context.lower() or "authentication" in query.context.lower():
                recommendations.extend(await self._recommend_access_controls(query, security_analysis))
            
            if "encryption" in query.context.lower() or "data protection" in query.context.lower():
                recommendations.extend(await self._recommend_encryption_config(query, security_analysis))
            
            if "vulnerability" in query.context.lower() or "scanning" in query.context.lower():
                recommendations.extend(await self._recommend_vulnerability_management(query, security_analysis))
            
            if "compliance" in query.context.lower() or "audit" in query.context.lower():
                recommendations.extend(await self._recommend_compliance_measures(query, security_analysis))
            
            if "incident" in query.context.lower() or "response" in query.context.lower():
                recommendations.extend(await self._recommend_incident_response(query, security_analysis))
            
            # Always include general security recommendations for high-risk operations
            if query.risk_level == "high" or security_analysis["threat_level"] == "high":
                recommendations.extend(await self._provide_general_security_recommendations(query, security_analysis))
            
            # Limit to max recommendations
            return recommendations[:self.max_recommendations_per_query]
            
        except Exception as e:
            logger.error(f"Error providing security expertise: {str(e)}")
            return []
    
    async def analyze_technical_plan(self, technical_plan: Dict[str, Any], intent_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze technical plan from security perspective
        
        Args:
            technical_plan: Technical plan from Technical Brain
            intent_analysis: Original intent analysis
            
        Returns:
            Security-specific analysis and recommendations
        """
        try:
            analysis = {
                "domain": self.domain,
                "analysis_id": f"security_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "security_relevance": 1.0,  # Security is always relevant
                "threat_assessment": {},
                "vulnerability_assessment": {},
                "compliance_assessment": {},
                "recommendations": [],
                "risk_mitigation_strategies": [],
                "security_controls_needed": []
            }
            
            # Perform STRIDE threat analysis
            analysis["threat_assessment"] = await self._perform_stride_analysis(technical_plan, intent_analysis)
            
            # Assess vulnerabilities
            analysis["vulnerability_assessment"] = await self._assess_vulnerabilities(technical_plan)
            
            # Check compliance requirements
            analysis["compliance_assessment"] = await self._assess_compliance_needs(technical_plan, intent_analysis)
            
            # Generate security recommendations
            analysis["recommendations"] = await self._generate_security_recommendations(technical_plan, intent_analysis)
            
            # Identify risk mitigation strategies
            analysis["risk_mitigation_strategies"] = await self._identify_risk_mitigations(technical_plan)
            
            # Determine required security controls
            analysis["security_controls_needed"] = await self._determine_security_controls(technical_plan, intent_analysis)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing technical plan for security: {str(e)}")
            return {"domain": self.domain, "error": str(e)}
    
    async def _analyze_security_context(self, query: SMEQuery) -> Dict[str, Any]:
        """Analyze security-specific context from query"""
        context = {
            "threat_level": "medium",
            "data_sensitivity": "medium",
            "compliance_requirements": [],
            "access_requirements": "standard",
            "encryption_requirements": "standard"
        }
        
        query_text = query.context.lower()
        
        # Assess threat level
        high_threat_indicators = ["production", "critical", "sensitive", "public", "internet"]
        if any(indicator in query_text for indicator in high_threat_indicators):
            context["threat_level"] = "high"
        
        # Assess data sensitivity
        sensitive_data_indicators = ["personal", "financial", "medical", "confidential", "classified"]
        if any(indicator in query_text for indicator in sensitive_data_indicators):
            context["data_sensitivity"] = "high"
        
        # Identify compliance requirements
        compliance_indicators = {
            "gdpr": ["gdpr", "european", "privacy"],
            "hipaa": ["hipaa", "medical", "healthcare"],
            "pci": ["pci", "payment", "credit card"],
            "sox": ["sox", "financial", "audit"],
            "iso27001": ["iso", "27001", "information security"]
        }
        
        for compliance, indicators in compliance_indicators.items():
            if any(indicator in query_text for indicator in indicators):
                context["compliance_requirements"].append(compliance)
        
        # Assess access requirements
        if any(word in query_text for word in ["admin", "privileged", "root", "elevated"]):
            context["access_requirements"] = "high_privilege"
        elif any(word in query_text for word in ["public", "anonymous", "guest"]):
            context["access_requirements"] = "public"
        
        # Assess encryption requirements
        if context["data_sensitivity"] == "high" or context["threat_level"] == "high":
            context["encryption_requirements"] = "high"
        
        return context
    
    async def _recommend_access_controls(self, query: SMEQuery, security_analysis: Dict[str, Any]) -> List[SMERecommendation]:
        """Recommend access control measures"""
        recommendations = []
        
        recommendations.append(await self._create_recommendation(
            query=query,
            recommendation_type=SMERecommendationType.SECURITY_REQUIREMENT,
            title="Implement Strong Access Controls",
            description="Configure robust access control mechanisms with principle of least privilege",
            rationale="Prevents unauthorized access and reduces attack surface",
            implementation_steps=[
                "Implement role-based access control (RBAC)",
                "Enable multi-factor authentication (MFA)",
                "Configure session timeouts",
                "Implement account lockout policies",
                "Enable access logging and monitoring",
                "Regular access reviews and cleanup"
            ],
            priority="critical" if security_analysis["access_requirements"] == "high_privilege" else "high",
            validation_criteria=[
                "MFA is enforced for all users",
                "Access permissions follow least privilege",
                "Access attempts are logged",
                "Inactive accounts are disabled"
            ],
            risks_if_ignored=[
                "Unauthorized access",
                "Privilege escalation",
                "Data breaches",
                "Compliance violations"
            ],
            tags=["access_control", "authentication", "authorization"]
        ))
        
        return recommendations
    
    async def _recommend_encryption_config(self, query: SMEQuery, security_analysis: Dict[str, Any]) -> List[SMERecommendation]:
        """Recommend encryption configuration"""
        recommendations = []
        
        encryption_level = "standard"
        if security_analysis["data_sensitivity"] == "high" or security_analysis["encryption_requirements"] == "high":
            encryption_level = "high"
        
        recommendations.append(await self._create_recommendation(
            query=query,
            recommendation_type=SMERecommendationType.SECURITY_REQUIREMENT,
            title="Implement Strong Encryption",
            description="Configure encryption for data at rest and in transit",
            rationale="Protects sensitive data from unauthorized access and interception",
            implementation_steps=[
                "Use AES-256 encryption for data at rest",
                "Implement TLS 1.3 for data in transit",
                "Configure proper key management",
                "Enable database encryption",
                "Implement certificate management",
                "Use encrypted communication channels"
            ] if encryption_level == "high" else [
                "Use AES-128 encryption for data at rest",
                "Implement TLS 1.2+ for data in transit",
                "Basic key management setup",
                "Enable HTTPS for web services"
            ],
            priority="critical" if encryption_level == "high" else "high",
            validation_criteria=[
                "All data at rest is encrypted",
                "All communications use TLS",
                "Keys are properly managed",
                "Certificates are valid and current"
            ],
            risks_if_ignored=[
                "Data exposure",
                "Man-in-the-middle attacks",
                "Compliance violations",
                "Reputation damage"
            ],
            tags=["encryption", "data_protection", "tls"]
        ))
        
        return recommendations
    
    async def _recommend_vulnerability_management(self, query: SMEQuery, security_analysis: Dict[str, Any]) -> List[SMERecommendation]:
        """Recommend vulnerability management practices"""
        recommendations = []
        
        recommendations.append(await self._create_recommendation(
            query=query,
            recommendation_type=SMERecommendationType.BEST_PRACTICE,
            title="Implement Comprehensive Vulnerability Management",
            description="Establish systematic vulnerability identification and remediation processes",
            rationale="Proactively identifies and addresses security vulnerabilities before exploitation",
            implementation_steps=[
                "Deploy automated vulnerability scanners",
                "Establish regular scanning schedules",
                "Implement patch management processes",
                "Conduct periodic penetration testing",
                "Monitor security advisories",
                "Maintain vulnerability database",
                "Establish SLAs for remediation"
            ],
            priority="high",
            validation_criteria=[
                "Vulnerability scans run regularly",
                "Critical vulnerabilities patched within SLA",
                "Scan results are reviewed and acted upon",
                "Patch management process is documented"
            ],
            risks_if_ignored=[
                "Exploitation of known vulnerabilities",
                "System compromises",
                "Data breaches",
                "Compliance failures"
            ],
            dependencies=["monitoring_setup", "patch_management_system"],
            tags=["vulnerability_management", "scanning", "patching"]
        ))
        
        return recommendations
    
    async def _recommend_compliance_measures(self, query: SMEQuery, security_analysis: Dict[str, Any]) -> List[SMERecommendation]:
        """Recommend compliance measures"""
        recommendations = []
        
        compliance_reqs = security_analysis.get("compliance_requirements", [])
        
        if compliance_reqs:
            recommendations.append(await self._create_recommendation(
                query=query,
                recommendation_type=SMERecommendationType.BEST_PRACTICE,
                title="Implement Compliance Controls",
                description=f"Configure controls for {', '.join(compliance_reqs)} compliance",
                rationale="Ensures adherence to regulatory requirements and industry standards",
                implementation_steps=[
                    "Document compliance requirements",
                    "Implement required security controls",
                    "Establish audit logging",
                    "Configure data retention policies",
                    "Implement access controls",
                    "Conduct regular compliance assessments",
                    "Maintain compliance documentation"
                ],
                priority="critical",
                validation_criteria=[
                    "All required controls are implemented",
                    "Audit logs are properly configured",
                    "Compliance assessments pass",
                    "Documentation is current"
                ],
                risks_if_ignored=[
                    "Regulatory fines",
                    "Legal liability",
                    "Business disruption",
                    "Reputation damage"
                ],
                tags=["compliance"] + compliance_reqs
            ))
        
        return recommendations
    
    async def _recommend_incident_response(self, query: SMEQuery, security_analysis: Dict[str, Any]) -> List[SMERecommendation]:
        """Recommend incident response measures"""
        recommendations = []
        
        recommendations.append(await self._create_recommendation(
            query=query,
            recommendation_type=SMERecommendationType.BEST_PRACTICE,
            title="Establish Incident Response Capabilities",
            description="Implement comprehensive incident response procedures and capabilities",
            rationale="Enables rapid detection, containment, and recovery from security incidents",
            implementation_steps=[
                "Develop incident response plan",
                "Establish incident response team",
                "Implement security monitoring",
                "Configure alerting systems",
                "Establish communication procedures",
                "Conduct incident response training",
                "Test incident response procedures"
            ],
            priority="high",
            validation_criteria=[
                "Incident response plan is documented",
                "Response team is trained",
                "Monitoring systems are operational",
                "Response procedures are tested"
            ],
            risks_if_ignored=[
                "Delayed incident detection",
                "Prolonged system compromise",
                "Increased damage from incidents",
                "Poor incident recovery"
            ],
            dependencies=["monitoring_setup", "alerting_configuration"],
            tags=["incident_response", "monitoring", "procedures"]
        ))
        
        return recommendations
    
    async def _provide_general_security_recommendations(self, query: SMEQuery, security_analysis: Dict[str, Any]) -> List[SMERecommendation]:
        """Provide general security recommendations for high-risk operations"""
        recommendations = []
        
        recommendations.append(await self._create_recommendation(
            query=query,
            recommendation_type=SMERecommendationType.SECURITY_REQUIREMENT,
            title="General Security Hardening",
            description="Implement general security hardening measures for high-risk operations",
            rationale="Provides baseline security protection against common threats",
            implementation_steps=[
                "Disable unnecessary services",
                "Configure secure defaults",
                "Implement network segmentation",
                "Enable security logging",
                "Configure firewalls",
                "Implement intrusion detection",
                "Regular security updates"
            ],
            priority="high",
            validation_criteria=[
                "Unnecessary services are disabled",
                "Security configurations are applied",
                "Network segmentation is in place",
                "Security monitoring is active"
            ],
            risks_if_ignored=[
                "Increased attack surface",
                "System vulnerabilities",
                "Unauthorized access",
                "Security incidents"
            ],
            tags=["security_hardening", "baseline_security", "general"]
        ))
        
        return recommendations
    
    async def _perform_stride_analysis(self, technical_plan: Dict[str, Any], intent_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Perform STRIDE threat modeling analysis"""
        stride_analysis = {
            "spoofing": [],
            "tampering": [],
            "repudiation": [],
            "information_disclosure": [],
            "denial_of_service": [],
            "elevation_of_privilege": []
        }
        
        plan_text = str(technical_plan).lower()
        
        # Analyze for STRIDE threats
        if "authentication" in plan_text or "login" in plan_text:
            stride_analysis["spoofing"].append("Authentication bypass risk")
        
        if "database" in plan_text or "data" in plan_text:
            stride_analysis["tampering"].append("Data modification risk")
            stride_analysis["information_disclosure"].append("Data exposure risk")
        
        if "admin" in plan_text or "privileged" in plan_text:
            stride_analysis["elevation_of_privilege"].append("Privilege escalation risk")
        
        if "network" in plan_text or "service" in plan_text:
            stride_analysis["denial_of_service"].append("Service disruption risk")
        
        if "log" not in plan_text:
            stride_analysis["repudiation"].append("Insufficient audit logging")
        
        return stride_analysis
    
    async def _assess_vulnerabilities(self, technical_plan: Dict[str, Any]) -> Dict[str, Any]:
        """Assess potential vulnerabilities in technical plan"""
        vulnerabilities = {
            "high_risk": [],
            "medium_risk": [],
            "low_risk": [],
            "recommendations": []
        }
        
        plan_text = str(technical_plan).lower()
        
        # Check for high-risk patterns
        if "root" in plan_text or "sudo" in plan_text:
            vulnerabilities["high_risk"].append("Elevated privilege usage")
        
        if "password" in plan_text and "plain" in plan_text:
            vulnerabilities["high_risk"].append("Plain text password usage")
        
        # Check for medium-risk patterns
        if "http" in plan_text and "https" not in plan_text:
            vulnerabilities["medium_risk"].append("Unencrypted communication")
        
        if "default" in plan_text:
            vulnerabilities["medium_risk"].append("Default configuration usage")
        
        # Generate recommendations
        if vulnerabilities["high_risk"]:
            vulnerabilities["recommendations"].append("Address high-risk vulnerabilities immediately")
        
        if vulnerabilities["medium_risk"]:
            vulnerabilities["recommendations"].append("Implement security controls for medium-risk items")
        
        return vulnerabilities
    
    async def _assess_compliance_needs(self, technical_plan: Dict[str, Any], intent_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Assess compliance requirements"""
        compliance = {
            "applicable_frameworks": [],
            "required_controls": [],
            "audit_requirements": [],
            "data_protection_needs": []
        }
        
        context_text = str(intent_analysis).lower() + str(technical_plan).lower()
        
        # Identify applicable frameworks
        if "financial" in context_text or "payment" in context_text:
            compliance["applicable_frameworks"].append("PCI DSS")
            compliance["required_controls"].append("Payment data encryption")
        
        if "healthcare" in context_text or "medical" in context_text:
            compliance["applicable_frameworks"].append("HIPAA")
            compliance["required_controls"].append("PHI protection")
        
        if "personal" in context_text or "privacy" in context_text:
            compliance["applicable_frameworks"].append("GDPR")
            compliance["required_controls"].append("Data subject rights")
        
        # General audit requirements
        if compliance["applicable_frameworks"]:
            compliance["audit_requirements"] = [
                "Comprehensive audit logging",
                "Access control documentation",
                "Regular compliance assessments"
            ]
        
        return compliance
    
    async def _generate_security_recommendations(self, technical_plan: Dict[str, Any], intent_analysis: Dict[str, Any]) -> List[str]:
        """Generate security recommendations based on plan analysis"""
        recommendations = []
        
        plan_text = str(technical_plan).lower()
        
        if "network" in plan_text:
            recommendations.append("Implement network segmentation")
            recommendations.append("Configure firewall rules")
        
        if "database" in plan_text:
            recommendations.append("Enable database encryption")
            recommendations.append("Implement database access controls")
        
        if "web" in plan_text or "http" in plan_text:
            recommendations.append("Implement HTTPS/TLS")
            recommendations.append("Configure web application firewall")
        
        return recommendations
    
    async def _identify_risk_mitigations(self, technical_plan: Dict[str, Any]) -> List[str]:
        """Identify risk mitigation strategies"""
        mitigations = []
        
        plan_text = str(technical_plan).lower()
        
        if "production" in plan_text:
            mitigations.append("Implement change management process")
            mitigations.append("Require security review for production changes")
        
        if "admin" in plan_text:
            mitigations.append("Implement privileged access management")
            mitigations.append("Require approval for administrative actions")
        
        if "data" in plan_text:
            mitigations.append("Implement data loss prevention")
            mitigations.append("Configure data backup and recovery")
        
        return mitigations
    
    async def _determine_security_controls(self, technical_plan: Dict[str, Any], intent_analysis: Dict[str, Any]) -> List[str]:
        """Determine required security controls"""
        controls = []
        
        # Always required controls
        controls.extend([
            "Access control",
            "Audit logging",
            "Security monitoring"
        ])
        
        plan_text = str(technical_plan).lower()
        
        if "network" in plan_text:
            controls.append("Network security controls")
        
        if "database" in plan_text:
            controls.append("Database security controls")
        
        if "encryption" in plan_text or "sensitive" in str(intent_analysis).lower():
            controls.append("Encryption controls")
        
        return list(set(controls))  # Remove duplicates