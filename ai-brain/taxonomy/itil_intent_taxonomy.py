"""
ITIL Intent Taxonomy

This module defines the complete ITIL-based intent taxonomy as specified in the
Phase 1 implementation roadmap. It provides structured categorization of all
possible user intents within the ITIL framework.
"""

import logging
from typing import Dict, List, Set, Optional
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)

class ITILIntentTaxonomy:
    """
    Complete ITIL-based intent taxonomy for user request classification
    
    This taxonomy follows ITIL v4 service management framework and provides
    comprehensive categorization of all possible user intents.
    """
    
    INTENT_CATEGORIES = {
        "information_request": {
            "system_status": [
                "server_status", "service_health", "resource_utilization",
                "system_performance", "uptime_status", "connectivity_status",
                "disk_usage", "memory_usage", "cpu_usage", "network_status"
            ],
            "configuration_inquiry": [
                "current_settings", "installed_components", "version_information",
                "configuration_files", "environment_variables", "service_configuration",
                "network_configuration", "security_settings", "backup_configuration"
            ],
            "documentation": [
                "how_to_guides", "troubleshooting_steps", "best_practices",
                "procedure_documentation", "architecture_diagrams", "runbooks",
                "knowledge_base_articles", "technical_specifications"
            ],
            "monitoring_data": [
                "performance_metrics", "log_analysis", "alert_history",
                "trend_analysis", "capacity_reports", "availability_reports",
                "security_reports", "compliance_reports"
            ]
        },
        
        "service_request": {
            "installation_deployment": [
                "software_install", "service_deployment", "application_deployment",
                "container_deployment", "database_installation", "middleware_setup",
                "monitoring_tool_setup", "security_tool_installation"
            ],
            "configuration_change": [
                "settings_update", "parameter_modification", "environment_configuration",
                "network_configuration_change", "security_configuration_update",
                "performance_tuning", "resource_allocation_change"
            ],
            "access_management": [
                "user_access", "permission_changes", "role_assignment",
                "credential_management", "certificate_management", "key_management",
                "authentication_setup", "authorization_configuration"
            ],
            "resource_provisioning": [
                "server_provisioning", "storage_allocation", "network_setup",
                "database_creation", "environment_setup", "capacity_expansion",
                "load_balancer_configuration", "backup_setup"
            ]
        },
        
        "incident_management": {
            "troubleshooting": [
                "error_diagnosis", "performance_issues", "connectivity_problems",
                "service_failures", "application_errors", "database_issues",
                "network_problems", "security_incidents"
            ],
            "service_restoration": [
                "restart_services", "failover_procedures", "recovery_operations",
                "rollback_procedures", "emergency_fixes", "hotfixes",
                "service_recovery", "data_recovery"
            ],
            "incident_response": [
                "security_incident_response", "outage_response", "escalation_procedures",
                "communication_management", "stakeholder_notification",
                "incident_documentation", "post_incident_review"
            ]
        },
        
        "change_management": {
            "infrastructure_changes": [
                "hardware_updates", "network_modifications", "server_upgrades",
                "storage_changes", "capacity_changes", "architecture_changes",
                "datacenter_changes", "cloud_migrations"
            ],
            "application_changes": [
                "version_upgrades", "configuration_updates", "patch_management",
                "feature_deployments", "bug_fixes", "performance_improvements",
                "security_updates", "dependency_updates"
            ],
            "process_changes": [
                "workflow_modifications", "procedure_updates", "policy_changes",
                "automation_improvements", "integration_changes",
                "monitoring_enhancements", "backup_procedure_changes"
            ]
        },
        
        "monitoring_analytics": {
            "performance_monitoring": [
                "metrics_collection", "alerting_setup", "dashboard_creation",
                "threshold_configuration", "performance_analysis",
                "capacity_monitoring", "availability_monitoring"
            ],
            "log_analysis": [
                "log_parsing", "trend_analysis", "anomaly_detection",
                "correlation_analysis", "forensic_analysis",
                "compliance_logging", "audit_trail_analysis"
            ],
            "reporting": [
                "performance_reports", "availability_reports", "capacity_reports",
                "security_reports", "compliance_reports", "trend_reports",
                "executive_dashboards", "operational_dashboards"
            ]
        },
        
        "testing_validation": {
            "system_testing": [
                "connectivity_tests", "performance_tests", "load_testing",
                "stress_testing", "integration_testing", "end_to_end_testing",
                "disaster_recovery_testing", "backup_testing"
            ],
            "validation_procedures": [
                "configuration_validation", "security_checks", "compliance_validation",
                "data_integrity_checks", "backup_validation", "recovery_validation",
                "performance_validation", "functionality_validation"
            ],
            "quality_assurance": [
                "code_quality_checks", "security_scanning", "vulnerability_assessment",
                "penetration_testing", "compliance_auditing", "best_practice_validation",
                "documentation_review", "process_validation"
            ]
        },
        
        "security_management": {
            "security_monitoring": [
                "threat_detection", "vulnerability_scanning", "security_alerting",
                "intrusion_detection", "malware_detection", "anomaly_detection",
                "compliance_monitoring", "audit_monitoring"
            ],
            "security_operations": [
                "incident_response", "threat_hunting", "forensic_analysis",
                "security_patching", "vulnerability_remediation", "access_review",
                "security_hardening", "penetration_testing"
            ],
            "compliance_management": [
                "regulatory_compliance", "policy_enforcement", "audit_preparation",
                "compliance_reporting", "risk_assessment", "control_validation",
                "certification_management", "governance_oversight"
            ]
        },
        
        "capacity_management": {
            "capacity_planning": [
                "resource_forecasting", "growth_planning", "capacity_modeling",
                "demand_analysis", "trend_analysis", "scenario_planning",
                "budget_planning", "technology_roadmap"
            ],
            "capacity_optimization": [
                "resource_optimization", "performance_tuning", "cost_optimization",
                "efficiency_improvements", "consolidation_planning",
                "rightsizing", "workload_balancing", "utilization_optimization"
            ]
        }
    }
    
    # Intent keywords for classification
    INTENT_KEYWORDS = {
        "information_request": [
            "status", "show", "display", "list", "get", "check", "view", "what",
            "how", "when", "where", "which", "info", "information", "details",
            "report", "summary", "overview", "describe", "explain"
        ],
        "service_request": [
            "install", "deploy", "setup", "configure", "create", "add", "enable",
            "provision", "allocate", "assign", "grant", "provide", "establish",
            "implement", "build", "initialize"
        ],
        "incident_management": [
            "fix", "repair", "resolve", "troubleshoot", "diagnose", "investigate",
            "restore", "recover", "restart", "reset", "rollback", "emergency",
            "urgent", "critical", "broken", "failed", "error", "issue", "problem"
        ],
        "change_management": [
            "update", "upgrade", "modify", "change", "patch", "migrate", "move",
            "replace", "switch", "convert", "transform", "enhance", "improve",
            "optimize", "refactor", "redesign"
        ],
        "monitoring_analytics": [
            "monitor", "track", "measure", "analyze", "alert", "notify", "watch",
            "observe", "dashboard", "metrics", "logs", "trends", "patterns",
            "statistics", "analytics", "insights"
        ],
        "testing_validation": [
            "test", "validate", "verify", "check", "confirm", "ensure", "audit",
            "review", "inspect", "examine", "assess", "evaluate", "benchmark",
            "compare", "quality", "compliance"
        ],
        "security_management": [
            "secure", "protect", "defend", "encrypt", "authenticate", "authorize",
            "scan", "detect", "prevent", "block", "filter", "firewall", "access",
            "permission", "certificate", "vulnerability", "threat", "risk"
        ],
        "capacity_management": [
            "scale", "resize", "expand", "shrink", "optimize", "balance", "allocate",
            "distribute", "forecast", "plan", "capacity", "resources", "utilization",
            "performance", "efficiency", "cost"
        ]
    }
    
    # Priority indicators
    PRIORITY_INDICATORS = {
        "critical": [
            "critical", "emergency", "urgent", "immediate", "asap", "now",
            "outage", "down", "failed", "broken", "disaster", "crisis"
        ],
        "high": [
            "high", "important", "priority", "soon", "quickly", "fast",
            "degraded", "slow", "issue", "problem", "affecting"
        ],
        "medium": [
            "medium", "normal", "standard", "regular", "routine", "planned",
            "scheduled", "maintenance", "improvement", "enhancement"
        ],
        "low": [
            "low", "minor", "cosmetic", "nice to have", "future", "eventually",
            "when possible", "convenience", "optimization", "cleanup"
        ]
    }
    
    # Risk indicators
    RISK_INDICATORS = {
        "high_risk": [
            "production", "live", "critical", "database", "security", "network",
            "core", "primary", "main", "essential", "vital", "mission critical"
        ],
        "medium_risk": [
            "staging", "test", "development", "secondary", "backup", "replica",
            "non-critical", "support", "auxiliary", "optional"
        ],
        "low_risk": [
            "sandbox", "demo", "prototype", "experimental", "temporary", "local",
            "personal", "training", "documentation", "cosmetic"
        ]
    }
    
    @classmethod
    def classify_intent(cls, user_message: str) -> Dict[str, any]:
        """
        Classify user intent based on ITIL taxonomy
        
        Args:
            user_message: User's request message
            
        Returns:
            Dict containing classification results
        """
        message_lower = user_message.lower()
        
        # Classify primary intent category
        category_scores = {}
        for category, keywords in cls.INTENT_KEYWORDS.items():
            score = sum(1 for keyword in keywords if keyword in message_lower)
            if score > 0:
                category_scores[category] = score
        
        # Determine primary category
        primary_category = max(category_scores.keys(), key=lambda k: category_scores[k]) if category_scores else "information_request"
        
        # Find specific intent within category
        specific_intents = []
        if primary_category in cls.INTENT_CATEGORIES:
            for subcategory, intents in cls.INTENT_CATEGORIES[primary_category].items():
                for intent in intents:
                    intent_words = intent.replace("_", " ").split()
                    if any(word in message_lower for word in intent_words):
                        specific_intents.append(intent)
        
        # Determine priority
        priority = "medium"  # default
        for priority_level, indicators in cls.PRIORITY_INDICATORS.items():
            if any(indicator in message_lower for indicator in indicators):
                priority = priority_level
                break
        
        # Determine risk level
        risk_level = "medium"  # default
        for risk_level_key, indicators in cls.RISK_INDICATORS.items():
            if any(indicator in message_lower for indicator in indicators):
                risk_level = risk_level_key.replace("_risk", "")
                break
        
        # Calculate confidence
        confidence = min(1.0, max(category_scores.values()) / 10.0) if category_scores else 0.3
        
        return {
            "primary_category": primary_category,
            "specific_intents": specific_intents[:3],  # Top 3 matches
            "priority": priority,
            "risk_level": risk_level,
            "confidence": confidence,
            "category_scores": category_scores
        }
    
    @classmethod
    def get_category_description(cls, category: str) -> str:
        """Get description of an intent category"""
        descriptions = {
            "information_request": "Requests for information, status, or documentation",
            "service_request": "Requests for new services, installations, or configurations",
            "incident_management": "Requests to resolve issues, problems, or service disruptions",
            "change_management": "Requests to modify, update, or change existing systems",
            "monitoring_analytics": "Requests related to monitoring, metrics, and analysis",
            "testing_validation": "Requests for testing, validation, or quality assurance",
            "security_management": "Requests related to security, compliance, and risk management",
            "capacity_management": "Requests related to capacity planning and optimization"
        }
        return descriptions.get(category, "Unknown category")
    
    @classmethod
    def get_all_categories(cls) -> List[str]:
        """Get all available intent categories"""
        return list(cls.INTENT_CATEGORIES.keys())
    
    @classmethod
    def get_subcategories(cls, category: str) -> List[str]:
        """Get subcategories for a given category"""
        return list(cls.INTENT_CATEGORIES.get(category, {}).keys())
    
    @classmethod
    def get_specific_intents(cls, category: str, subcategory: str = None) -> List[str]:
        """Get specific intents for a category and optional subcategory"""
        if category not in cls.INTENT_CATEGORIES:
            return []
        
        if subcategory:
            return cls.INTENT_CATEGORIES[category].get(subcategory, [])
        else:
            # Return all intents for the category
            all_intents = []
            for subcat_intents in cls.INTENT_CATEGORIES[category].values():
                all_intents.extend(subcat_intents)
            return all_intents