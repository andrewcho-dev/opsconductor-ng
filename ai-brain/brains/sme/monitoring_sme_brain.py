"""
Monitoring SME Brain - Specialized expertise for observability and monitoring

This brain provides domain-specific knowledge for:
- Metrics collection and analysis
- Alerting configuration and management
- Performance monitoring strategies
- Log analysis and correlation
- Observability best practices
"""

import asyncio
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import re
import time

from ..base_sme_brain import SMEBrain, SMEQuery, SMERecommendation, SMEConfidenceLevel, SMERecommendationType


class MonitoringType(Enum):
    INFRASTRUCTURE = "infrastructure"
    APPLICATION = "application"
    NETWORK = "network"
    SECURITY = "security"
    BUSINESS = "business"
    SYNTHETIC = "synthetic"


class MetricType(Enum):
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"
    TIMER = "timer"


class AlertSeverity(Enum):
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"
    DEBUG = "debug"


@dataclass
class MonitoringStrategy:
    """Comprehensive monitoring strategy recommendation"""
    monitoring_types: List[MonitoringType]
    key_metrics: List[str]
    alerting_rules: List[Dict[str, Any]]
    dashboards: List[str]
    tools_recommended: List[str]
    implementation_priority: List[str]


@dataclass
class AlertingConfiguration:
    """Alerting configuration recommendations"""
    alert_rules: List[Dict[str, Any]]
    notification_channels: List[str]
    escalation_policies: List[Dict[str, Any]]
    suppression_rules: List[str]


class MonitoringSMEBrain(SMEBrain):
    """
    Monitoring and Observability Subject Matter Expert Brain
    
    Provides specialized expertise in monitoring systems, alerting,
    performance analysis, and observability best practices.
    """
    
    domain = "observability_monitoring"
    expertise_areas = [
        "metrics_collection",
        "alerting_configuration", 
        "performance_monitoring",
        "log_analysis",
        "distributed_tracing",
        "synthetic_monitoring",
        "capacity_planning",
        "incident_response_monitoring"
    ]
    
    def __init__(self):
        super().__init__(self.domain, self.expertise_areas)
        self.monitoring_knowledge_base = self._initialize_monitoring_knowledge()
        self.alerting_engine = self._initialize_alerting_engine()
        self.metrics_analyzer = self._initialize_metrics_analyzer()
        
    def _initialize_monitoring_knowledge(self) -> Dict[str, Any]:
        """Initialize monitoring-specific knowledge base"""
        return {
            "monitoring_tools": {
                "open_source": {
                    "prometheus": {
                        "type": "metrics",
                        "strengths": ["time_series", "alerting", "service_discovery"],
                        "use_cases": ["kubernetes", "microservices", "infrastructure"]
                    },
                    "grafana": {
                        "type": "visualization",
                        "strengths": ["dashboards", "multi_datasource", "alerting"],
                        "use_cases": ["metrics_visualization", "log_analysis", "monitoring_overview"]
                    },
                    "elk_stack": {
                        "type": "logging",
                        "strengths": ["log_aggregation", "search", "analysis"],
                        "use_cases": ["centralized_logging", "security_monitoring", "troubleshooting"]
                    },
                    "jaeger": {
                        "type": "tracing",
                        "strengths": ["distributed_tracing", "performance_analysis"],
                        "use_cases": ["microservices", "performance_debugging", "dependency_mapping"]
                    }
                },
                "commercial": {
                    "datadog": {
                        "type": "full_stack",
                        "strengths": ["ease_of_use", "integrations", "apm"],
                        "use_cases": ["cloud_monitoring", "application_performance", "infrastructure"]
                    },
                    "new_relic": {
                        "type": "apm",
                        "strengths": ["application_monitoring", "user_experience", "alerts"],
                        "use_cases": ["application_performance", "error_tracking", "user_monitoring"]
                    },
                    "splunk": {
                        "type": "analytics",
                        "strengths": ["log_analysis", "security", "machine_learning"],
                        "use_cases": ["security_monitoring", "compliance", "operational_intelligence"]
                    }
                }
            },
            "key_metrics": {
                "infrastructure": {
                    "system": ["cpu_usage", "memory_usage", "disk_usage", "network_io", "load_average"],
                    "application": ["response_time", "throughput", "error_rate", "availability"],
                    "database": ["connection_count", "query_time", "lock_waits", "replication_lag"],
                    "network": ["bandwidth_usage", "packet_loss", "latency", "connection_errors"]
                },
                "application": {
                    "performance": ["response_time", "throughput", "concurrent_users", "queue_depth"],
                    "errors": ["error_rate", "exception_count", "failed_requests", "timeout_rate"],
                    "business": ["conversion_rate", "user_engagement", "transaction_volume", "revenue_metrics"]
                }
            },
            "alerting_best_practices": [
                "Alert on symptoms, not causes",
                "Reduce alert fatigue with proper thresholds",
                "Implement alert escalation policies",
                "Use runbooks for alert resolution",
                "Regular alert review and tuning",
                "Context-aware alerting"
            ],
            "monitoring_patterns": {
                "golden_signals": ["latency", "traffic", "errors", "saturation"],
                "red_method": ["rate", "errors", "duration"],
                "use_method": ["utilization", "saturation", "errors"],
                "four_pillars": ["metrics", "logs", "traces", "events"]
            }
        }
    
    def _initialize_alerting_engine(self) -> Dict[str, Any]:
        """Initialize alerting configuration engine"""
        return {
            "alert_types": {
                "threshold": {
                    "description": "Alert when metric crosses threshold",
                    "use_cases": ["cpu_high", "disk_full", "response_time_slow"]
                },
                "anomaly": {
                    "description": "Alert on statistical anomalies",
                    "use_cases": ["traffic_spikes", "unusual_patterns", "performance_degradation"]
                },
                "absence": {
                    "description": "Alert when expected data is missing",
                    "use_cases": ["service_down", "heartbeat_missing", "data_pipeline_failure"]
                },
                "composite": {
                    "description": "Alert based on multiple conditions",
                    "use_cases": ["complex_scenarios", "correlated_failures", "business_impact"]
                }
            },
            "severity_guidelines": {
                "critical": "Immediate action required, service impact",
                "warning": "Attention needed, potential impact",
                "info": "Informational, no immediate action",
                "debug": "Diagnostic information"
            }
        }
    
    def _initialize_metrics_analyzer(self) -> Dict[str, Any]:
        """Initialize metrics analysis engine"""
        return {
            "analysis_methods": {
                "trend_analysis": "Identify long-term patterns and trends",
                "anomaly_detection": "Detect unusual patterns or outliers",
                "correlation_analysis": "Find relationships between metrics",
                "capacity_planning": "Predict future resource needs",
                "performance_profiling": "Identify performance bottlenecks"
            },
            "metric_patterns": {
                "seasonal": "Regular patterns based on time",
                "cyclical": "Repeating patterns over longer periods",
                "trending": "Consistent increase or decrease",
                "volatile": "High variability with no clear pattern",
                "stable": "Consistent values with low variability"
            }
        }
    
    async def provide_expertise(self, query: SMEQuery) -> SMERecommendation:
        """
        Provide monitoring-specific expertise based on the query
        
        Args:
            query: SME query containing the request and context
            
        Returns:
            SME recommendation with monitoring-specific guidance
        """
        try:
            # Analyze the query for monitoring-related intent
            monitoring_analysis = await self._analyze_monitoring_intent(query)
            
            # Generate recommendations based on the analysis
            recommendations = await self._generate_monitoring_recommendations(monitoring_analysis, query)
            
            # Calculate confidence based on query specificity and domain match
            confidence = await self._calculate_confidence(query, monitoring_analysis)
            
            return SMERecommendation(
                recommendation_id=f"monitoring_{query.query_id}_{int(time.time())}",
                domain=self.domain,
                query_id=query.query_id,
                recommendation_type=SMERecommendationType.BEST_PRACTICE,
                title=f"Monitoring Strategy for {query.domain}",
                description=recommendations.get("summary", "Comprehensive monitoring and observability recommendations"),
                rationale=monitoring_analysis.get("reasoning", "Monitoring and observability analysis"),
                confidence=self._confidence_level_to_score(confidence),
                priority=recommendations.get("priority", "medium"),
                implementation_steps=recommendations.get("implementation_steps", []),
                dependencies=recommendations.get("dependencies", [])
            )
            
        except Exception as e:
            return SMERecommendation(
                recommendation_id=f"monitoring_error_{query.query_id}_{int(time.time())}",
                domain=self.domain,
                query_id=query.query_id,
                recommendation_type=SMERecommendationType.TROUBLESHOOTING_STEP,
                title="Monitoring Analysis Error",
                description=f"Monitoring analysis failed: {str(e)}",
                rationale="Error in monitoring analysis",
                confidence=self._confidence_level_to_score(SMEConfidenceLevel.LOW),
                priority="high",
                implementation_steps=["Review monitoring requirements manually"],
                dependencies=[]
            )
    
    async def _analyze_monitoring_intent(self, query: SMEQuery) -> Dict[str, Any]:
        """Analyze the query for monitoring-related intent and requirements"""
        intent_analysis = {
            "monitoring_types": [],
            "metric_focus": [],
            "alerting_requirements": [],
            "tools_mentioned": [],
            "performance_concerns": [],
            "log_analysis_needs": [],
            "dashboard_requirements": [],
            "reasoning": ""
        }
        
        query_text = query.query_text.lower()
        
        # Detect monitoring types
        monitoring_keywords = {
            MonitoringType.INFRASTRUCTURE: ["infrastructure", "server", "system", "cpu", "memory", "disk"],
            MonitoringType.APPLICATION: ["application", "app", "service", "api", "response", "performance"],
            MonitoringType.NETWORK: ["network", "bandwidth", "latency", "connectivity", "packet"],
            MonitoringType.SECURITY: ["security", "intrusion", "vulnerability", "compliance", "audit"],
            MonitoringType.BUSINESS: ["business", "revenue", "conversion", "user", "transaction"],
            MonitoringType.SYNTHETIC: ["synthetic", "uptime", "availability", "endpoint", "health"]
        }
        
        for mon_type, keywords in monitoring_keywords.items():
            if any(keyword in query_text for keyword in keywords):
                intent_analysis["monitoring_types"].append(mon_type)
        
        # Detect metric focus
        metric_keywords = {
            "performance": ["performance", "speed", "latency", "response", "throughput"],
            "availability": ["availability", "uptime", "downtime", "outage", "health"],
            "errors": ["error", "exception", "failure", "bug", "issue"],
            "capacity": ["capacity", "usage", "utilization", "resource", "scaling"],
            "security": ["security", "breach", "attack", "vulnerability", "compliance"]
        }
        
        for focus, keywords in metric_keywords.items():
            if any(keyword in query_text for keyword in keywords):
                intent_analysis["metric_focus"].append(focus)
        
        # Detect alerting requirements
        alerting_keywords = ["alert", "notification", "alarm", "warning", "critical", "escalation"]
        if any(keyword in query_text for keyword in alerting_keywords):
            intent_analysis["alerting_requirements"] = self._extract_alerting_requirements(query_text)
        
        # Detect mentioned tools
        all_tools = []
        for category in self.monitoring_knowledge_base["monitoring_tools"].values():
            all_tools.extend(category.keys())
        
        for tool in all_tools:
            if tool in query_text:
                intent_analysis["tools_mentioned"].append(tool)
        
        # Detect performance concerns
        performance_keywords = ["slow", "fast", "bottleneck", "optimize", "improve", "degrade"]
        if any(keyword in query_text for keyword in performance_keywords):
            intent_analysis["performance_concerns"] = self._extract_performance_concerns(query_text)
        
        # Detect log analysis needs
        log_keywords = ["log", "logging", "trace", "debug", "audit", "event"]
        if any(keyword in query_text for keyword in log_keywords):
            intent_analysis["log_analysis_needs"] = self._extract_log_requirements(query_text)
        
        # Detect dashboard requirements
        dashboard_keywords = ["dashboard", "visualization", "chart", "graph", "report", "view"]
        if any(keyword in query_text for keyword in dashboard_keywords):
            intent_analysis["dashboard_requirements"] = self._extract_dashboard_requirements(query_text)
        
        # Build reasoning
        intent_analysis["reasoning"] = self._build_monitoring_reasoning(intent_analysis)
        
        return intent_analysis
    
    def _extract_alerting_requirements(self, query_text: str) -> List[str]:
        """Extract specific alerting requirements from query text"""
        requirements = []
        
        if "critical" in query_text:
            requirements.append("critical_alerts")
        if "warning" in query_text:
            requirements.append("warning_alerts")
        if "escalation" in query_text:
            requirements.append("escalation_policy")
        if "notification" in query_text:
            requirements.append("notification_channels")
        if "threshold" in query_text:
            requirements.append("threshold_based")
        
        return requirements
    
    def _extract_performance_concerns(self, query_text: str) -> List[str]:
        """Extract performance concerns from query text"""
        concerns = []
        
        if "slow" in query_text or "latency" in query_text:
            concerns.append("response_time")
        if "bottleneck" in query_text:
            concerns.append("performance_bottleneck")
        if "resource" in query_text or "cpu" in query_text or "memory" in query_text:
            concerns.append("resource_utilization")
        if "throughput" in query_text or "capacity" in query_text:
            concerns.append("throughput_capacity")
        
        return concerns
    
    def _extract_log_requirements(self, query_text: str) -> List[str]:
        """Extract log analysis requirements from query text"""
        requirements = []
        
        if "centralized" in query_text:
            requirements.append("centralized_logging")
        if "search" in query_text:
            requirements.append("log_search")
        if "correlation" in query_text:
            requirements.append("log_correlation")
        if "real-time" in query_text or "realtime" in query_text:
            requirements.append("real_time_analysis")
        if "retention" in query_text:
            requirements.append("log_retention")
        
        return requirements
    
    def _extract_dashboard_requirements(self, query_text: str) -> List[str]:
        """Extract dashboard requirements from query text"""
        requirements = []
        
        if "real-time" in query_text or "realtime" in query_text:
            requirements.append("real_time_dashboard")
        if "executive" in query_text or "management" in query_text:
            requirements.append("executive_dashboard")
        if "operational" in query_text or "ops" in query_text:
            requirements.append("operational_dashboard")
        if "custom" in query_text:
            requirements.append("custom_dashboard")
        
        return requirements
    
    async def _generate_monitoring_recommendations(self, analysis: Dict[str, Any], query: SMEQuery) -> Dict[str, Any]:
        """Generate monitoring-specific recommendations based on analysis"""
        recommendations = {
            "monitoring_strategy": {},
            "tool_recommendations": [],
            "key_metrics": [],
            "alerting_configuration": {},
            "dashboard_design": {},
            "implementation_steps": [],
            "best_practices": [],
            "risk_assessment": "Medium",
            "estimated_effort": "Medium",
            "dependencies": []
        }
        
        # Generate monitoring strategy
        recommendations["monitoring_strategy"] = await self._generate_monitoring_strategy(analysis)
        
        # Generate tool recommendations
        recommendations["tool_recommendations"] = await self._generate_tool_recommendations(analysis)
        
        # Generate key metrics
        recommendations["key_metrics"] = await self._generate_key_metrics(analysis)
        
        # Generate alerting configuration
        if analysis["alerting_requirements"]:
            recommendations["alerting_configuration"] = await self._generate_alerting_config(analysis)
        
        # Generate dashboard design
        if analysis["dashboard_requirements"]:
            recommendations["dashboard_design"] = await self._generate_dashboard_design(analysis)
        
        # Generate implementation steps
        recommendations["implementation_steps"] = await self._generate_monitoring_implementation_steps(analysis)
        
        # Generate best practices
        recommendations["best_practices"] = await self._generate_monitoring_best_practices(analysis)
        
        return recommendations
    
    async def _generate_monitoring_strategy(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive monitoring strategy"""
        strategy = {
            "approach": "layered_monitoring",
            "monitoring_types": analysis["monitoring_types"],
            "focus_areas": analysis["metric_focus"],
            "methodology": []
        }
        
        # Determine methodology based on monitoring types
        if MonitoringType.APPLICATION in analysis["monitoring_types"]:
            strategy["methodology"].append("RED method (Rate, Errors, Duration)")
        if MonitoringType.INFRASTRUCTURE in analysis["monitoring_types"]:
            strategy["methodology"].append("USE method (Utilization, Saturation, Errors)")
        
        # Add golden signals if multiple types
        if len(analysis["monitoring_types"]) > 1:
            strategy["methodology"].append("Four Golden Signals (Latency, Traffic, Errors, Saturation)")
        
        return strategy
    
    async def _generate_tool_recommendations(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate tool recommendations based on analysis"""
        recommendations = []
        
        # If specific tools mentioned, provide guidance on those
        if analysis["tools_mentioned"]:
            for tool in analysis["tools_mentioned"]:
                tool_info = self._get_tool_info(tool)
                if tool_info:
                    recommendations.append({
                        "tool": tool,
                        "category": tool_info.get("type", "unknown"),
                        "strengths": tool_info.get("strengths", []),
                        "recommended_for": tool_info.get("use_cases", [])
                    })
        else:
            # Recommend tools based on monitoring types
            recommendations = self._recommend_tools_by_type(analysis["monitoring_types"])
        
        return recommendations
    
    def _get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific monitoring tool"""
        for category in self.monitoring_knowledge_base["monitoring_tools"].values():
            if tool_name in category:
                return category[tool_name]
        return None
    
    def _recommend_tools_by_type(self, monitoring_types: List[MonitoringType]) -> List[Dict[str, Any]]:
        """Recommend tools based on monitoring types"""
        recommendations = []
        
        # Basic stack recommendation
        if MonitoringType.INFRASTRUCTURE in monitoring_types or MonitoringType.APPLICATION in monitoring_types:
            recommendations.extend([
                {
                    "tool": "prometheus",
                    "category": "metrics",
                    "reason": "Excellent for time-series metrics collection and alerting"
                },
                {
                    "tool": "grafana",
                    "category": "visualization",
                    "reason": "Powerful dashboards and visualization capabilities"
                }
            ])
        
        # Add logging if needed
        if any("log" in str(mt) for mt in monitoring_types) or MonitoringType.SECURITY in monitoring_types:
            recommendations.append({
                "tool": "elk_stack",
                "category": "logging",
                "reason": "Comprehensive log aggregation and analysis"
            })
        
        return recommendations
    
    async def _generate_key_metrics(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate key metrics recommendations"""
        metrics = []
        
        for monitoring_type in analysis["monitoring_types"]:
            if monitoring_type == MonitoringType.INFRASTRUCTURE:
                metrics.extend([
                    {"name": "cpu_usage_percent", "type": "gauge", "threshold": "80%"},
                    {"name": "memory_usage_percent", "type": "gauge", "threshold": "85%"},
                    {"name": "disk_usage_percent", "type": "gauge", "threshold": "90%"},
                    {"name": "network_io_bytes", "type": "counter", "threshold": "bandwidth_limit"}
                ])
            elif monitoring_type == MonitoringType.APPLICATION:
                metrics.extend([
                    {"name": "response_time_ms", "type": "histogram", "threshold": "500ms"},
                    {"name": "request_rate", "type": "counter", "threshold": "baseline_+50%"},
                    {"name": "error_rate_percent", "type": "gauge", "threshold": "1%"},
                    {"name": "active_connections", "type": "gauge", "threshold": "connection_limit"}
                ])
        
        return metrics
    
    async def _generate_alerting_config(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate alerting configuration recommendations"""
        config = {
            "alert_rules": [],
            "notification_channels": ["email", "slack", "pagerduty"],
            "escalation_policy": {
                "level_1": "team_on_call",
                "level_2": "team_lead",
                "level_3": "management"
            },
            "suppression_rules": [
                "maintenance_windows",
                "known_issues",
                "dependency_failures"
            ]
        }
        
        # Generate specific alert rules based on requirements
        if "critical_alerts" in analysis["alerting_requirements"]:
            config["alert_rules"].extend([
                {
                    "name": "service_down",
                    "condition": "up == 0",
                    "severity": "critical",
                    "duration": "1m"
                },
                {
                    "name": "high_error_rate",
                    "condition": "error_rate > 5%",
                    "severity": "critical",
                    "duration": "5m"
                }
            ])
        
        return config
    
    async def _generate_dashboard_design(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate dashboard design recommendations"""
        design = {
            "dashboard_types": [],
            "key_visualizations": [],
            "layout_recommendations": [],
            "refresh_intervals": {}
        }
        
        # Determine dashboard types based on requirements
        if "operational_dashboard" in analysis["dashboard_requirements"]:
            design["dashboard_types"].append({
                "type": "operational",
                "purpose": "Real-time system monitoring",
                "audience": "operations_team",
                "key_metrics": ["system_health", "performance", "errors"]
            })
        
        if "executive_dashboard" in analysis["dashboard_requirements"]:
            design["dashboard_types"].append({
                "type": "executive",
                "purpose": "High-level business metrics",
                "audience": "management",
                "key_metrics": ["availability", "performance_trends", "business_impact"]
            })
        
        return design
    
    async def _generate_monitoring_implementation_steps(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate implementation steps for monitoring setup"""
        steps = [
            "1. Define monitoring requirements and success criteria",
            "2. Select and set up monitoring tools",
            "3. Implement metrics collection for key systems",
            "4. Configure alerting rules and notification channels",
            "5. Create operational dashboards",
            "6. Set up log aggregation and analysis",
            "7. Implement distributed tracing (if applicable)",
            "8. Test alerting and escalation procedures",
            "9. Train team on monitoring tools and procedures",
            "10. Establish monitoring maintenance and review processes"
        ]
        
        # Customize based on specific requirements
        if analysis["dashboard_requirements"]:
            steps.insert(5, "5.5. Design and implement custom dashboards")
        
        if MonitoringType.SECURITY in analysis["monitoring_types"]:
            steps.insert(-2, "9.5. Implement security monitoring and compliance checks")
        
        return steps
    
    async def _generate_monitoring_best_practices(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate monitoring best practices based on analysis"""
        practices = [
            "Monitor the four golden signals: latency, traffic, errors, saturation",
            "Alert on symptoms, not causes",
            "Implement proper alert thresholds to avoid fatigue",
            "Use runbooks for alert resolution procedures",
            "Regularly review and tune alerting rules",
            "Implement monitoring for monitoring (meta-monitoring)",
            "Ensure monitoring data retention policies",
            "Practice incident response procedures"
        ]
        
        # Add specific practices based on analysis
        if "performance" in analysis["metric_focus"]:
            practices.append("Implement performance baselines and trend analysis")
        
        if "capacity" in analysis["metric_focus"]:
            practices.append("Use monitoring data for capacity planning")
        
        return practices
    
    def _build_monitoring_reasoning(self, analysis: Dict[str, Any]) -> str:
        """Build reasoning explanation for the monitoring analysis"""
        reasoning_parts = []
        
        if analysis["monitoring_types"]:
            types = [mt.value for mt in analysis["monitoring_types"]]
            reasoning_parts.append(f"Monitoring types identified: {', '.join(types)}")
        
        if analysis["metric_focus"]:
            reasoning_parts.append(f"Metric focus areas: {', '.join(analysis['metric_focus'])}")
        
        if analysis["tools_mentioned"]:
            reasoning_parts.append(f"Tools mentioned: {', '.join(analysis['tools_mentioned'])}")
        
        if analysis["alerting_requirements"]:
            reasoning_parts.append(f"Alerting requirements: {', '.join(analysis['alerting_requirements'])}")
        
        return "; ".join(reasoning_parts) if reasoning_parts else "General monitoring and observability inquiry"
    
    async def _calculate_confidence(self, query: SMEQuery, analysis: Dict[str, Any]) -> SMEConfidenceLevel:
        """Calculate confidence level based on query analysis"""
        confidence_score = 0.0
        
        # Base confidence for monitoring domain
        monitoring_keywords = ["monitor", "alert", "metric", "dashboard", "log", "trace", "observability"]
        query_text = f"{query.context} {' '.join(query.specific_questions)}".lower()
        if any(keyword in query_text for keyword in monitoring_keywords):
            confidence_score += 0.3
        
        # Boost for specific monitoring types
        if analysis["monitoring_types"]:
            confidence_score += 0.2
        
        # Boost for specific tools mentioned
        if analysis["tools_mentioned"]:
            confidence_score += 0.2
        
        # Boost for specific requirements
        if analysis["alerting_requirements"] or analysis["dashboard_requirements"]:
            confidence_score += 0.2
        
        # Boost for technical context
        if query.context and any(key in query.context for key in ["performance", "availability", "errors"]):
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
        """Analyze technical plan from monitoring perspective"""
        try:
            analysis = {
                "monitoring_requirements": self._assess_monitoring_needs(technical_plan),
                "recommended_tools": self._recommend_monitoring_tools(technical_plan, intent_analysis),
                "alerting_strategy": self._design_alerting_strategy(technical_plan),
                "dashboard_requirements": self._analyze_dashboard_needs(technical_plan),
                "performance_metrics": self._identify_key_metrics(technical_plan),
                "observability_gaps": self._identify_observability_gaps(technical_plan),
                "risk_assessment": self._assess_monitoring_risks(technical_plan)
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Monitoring technical plan analysis failed: {e}")
            return {
                "error": f"Monitoring analysis failed: {str(e)}",
                "monitoring_requirements": "unknown",
                "risk_assessment": "high"
            }
    
    def _assess_monitoring_needs(self, technical_plan: Dict[str, Any]) -> Dict[str, Any]:
        """Assess monitoring requirements based on technical plan"""
        plan_str = str(technical_plan).lower()
        
        needs = {
            "infrastructure_monitoring": "database" in plan_str or "server" in plan_str,
            "application_monitoring": "application" in plan_str or "service" in plan_str,
            "network_monitoring": "network" in plan_str or "api" in plan_str,
            "security_monitoring": "security" in plan_str or "auth" in plan_str,
            "business_monitoring": "business" in plan_str or "user" in plan_str
        }
        
        return needs
    
    def _recommend_monitoring_tools(self, technical_plan: Dict[str, Any], intent_analysis: Dict[str, Any]) -> List[str]:
        """Recommend specific monitoring tools"""
        tools = []
        plan_str = str(technical_plan).lower()
        
        if "prometheus" in plan_str or "metrics" in plan_str:
            tools.extend(["prometheus", "grafana"])
        if "logs" in plan_str or "logging" in plan_str:
            tools.extend(["elasticsearch", "logstash", "kibana"])
        if "tracing" in plan_str or "distributed" in plan_str:
            tools.append("jaeger")
        if "uptime" in plan_str or "availability" in plan_str:
            tools.append("pingdom")
            
        return tools if tools else ["prometheus", "grafana"]  # Default stack
    
    def _design_alerting_strategy(self, technical_plan: Dict[str, Any]) -> Dict[str, Any]:
        """Design alerting strategy"""
        return {
            "critical_alerts": ["service_down", "high_error_rate", "resource_exhaustion"],
            "warning_alerts": ["high_latency", "resource_usage_threshold", "unusual_traffic"],
            "notification_channels": ["email", "slack", "pagerduty"],
            "escalation_policy": "immediate -> team lead -> manager"
        }
    
    def _analyze_dashboard_needs(self, technical_plan: Dict[str, Any]) -> List[str]:
        """Analyze dashboard requirements"""
        dashboards = ["system_overview", "application_performance"]
        plan_str = str(technical_plan).lower()
        
        if "database" in plan_str:
            dashboards.append("database_performance")
        if "network" in plan_str:
            dashboards.append("network_monitoring")
        if "security" in plan_str:
            dashboards.append("security_monitoring")
        if "business" in plan_str:
            dashboards.append("business_metrics")
            
        return dashboards
    
    def _identify_key_metrics(self, technical_plan: Dict[str, Any]) -> Dict[str, List[str]]:
        """Identify key metrics to monitor"""
        return {
            "infrastructure": ["cpu_usage", "memory_usage", "disk_usage", "network_io"],
            "application": ["response_time", "throughput", "error_rate", "availability"],
            "business": ["user_sessions", "conversion_rate", "revenue_metrics"],
            "security": ["failed_logins", "suspicious_activity", "vulnerability_scans"]
        }
    
    def _identify_observability_gaps(self, technical_plan: Dict[str, Any]) -> List[str]:
        """Identify potential observability gaps"""
        gaps = []
        plan_str = str(technical_plan).lower()
        
        if "microservices" in plan_str and "tracing" not in plan_str:
            gaps.append("distributed_tracing")
        if "database" in plan_str and "monitoring" not in plan_str:
            gaps.append("database_monitoring")
        if "api" in plan_str and "logging" not in plan_str:
            gaps.append("api_logging")
            
        return gaps
    
    def _assess_monitoring_risks(self, technical_plan: Dict[str, Any]) -> str:
        """Assess monitoring-related risks"""
        plan_str = str(technical_plan).lower()
        
        if "production" in plan_str and "monitoring" not in plan_str:
            return "high - production system without adequate monitoring"
        elif "distributed" in plan_str and "tracing" not in plan_str:
            return "medium - distributed system without tracing"
        else:
            return "low - adequate monitoring considerations"

    async def learn_from_execution(self, execution_data: Dict[str, Any]) -> None:
        """Learn from execution results to improve monitoring recommendations"""
        try:
            # Extract learning insights from execution data
            if execution_data.get("success"):
                # Successful execution - reinforce the recommendations
                await self._reinforce_successful_monitoring_patterns(execution_data)
            else:
                # Failed execution - learn from the failure
                await self._learn_from_monitoring_failures(execution_data)
                
            # Update knowledge base with new insights
            await self._update_monitoring_knowledge(execution_data)
            
        except Exception as e:
            # Log learning failure but don't raise
            print(f"Monitoring SME learning error: {e}")
    
    async def _reinforce_successful_monitoring_patterns(self, execution_data: Dict[str, Any]) -> None:
        """Reinforce successful monitoring implementation patterns"""
        # Implementation for reinforcing successful patterns
        pass
    
    async def _learn_from_monitoring_failures(self, execution_data: Dict[str, Any]) -> None:
        """Learn from failed monitoring implementations"""
        # Implementation for learning from failures
        pass
    
    async def _update_monitoring_knowledge(self, execution_data: Dict[str, Any]) -> None:
        """Update monitoring knowledge base with new insights"""
        # Implementation for updating knowledge base
        pass