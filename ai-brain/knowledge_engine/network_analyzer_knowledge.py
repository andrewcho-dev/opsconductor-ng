"""
OpsConductor AI Brain - Network Analyzer Knowledge Module

This module provides comprehensive knowledge about the network analyzer service
capabilities, use cases, and integration patterns for the AI system.
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class NetworkAnalysisType(Enum):
    """Types of network analysis available"""
    PACKET_CAPTURE = "packet_capture"
    REAL_TIME_MONITORING = "real_time_monitoring"
    PROTOCOL_ANALYSIS = "protocol_analysis"
    AI_ANOMALY_DETECTION = "ai_anomaly_detection"
    PERFORMANCE_ANALYSIS = "performance_analysis"
    REMOTE_ANALYSIS = "remote_analysis"

class NetworkProtocol(Enum):
    """Supported network protocols for analysis"""
    TCP = "tcp"
    UDP = "udp"
    HTTP = "http"
    HTTPS = "https"
    DNS = "dns"
    ICMP = "icmp"
    SSH = "ssh"
    FTP = "ftp"
    SMTP = "smtp"
    SNMP = "snmp"

@dataclass
class NetworkAnalysisCapability:
    """Represents a specific network analysis capability"""
    name: str
    description: str
    use_cases: List[str]
    required_parameters: List[str]
    optional_parameters: List[str]
    output_format: str
    typical_duration: str
    resource_requirements: str

@dataclass
class NetworkTroubleshootingScenario:
    """Common network troubleshooting scenarios"""
    scenario: str
    symptoms: List[str]
    recommended_analysis: List[str]
    expected_findings: List[str]
    remediation_steps: List[str]

class NetworkAnalyzerKnowledge:
    """Comprehensive knowledge about network analyzer capabilities"""
    
    def __init__(self):
        self.capabilities = self._initialize_capabilities()
        self.troubleshooting_scenarios = self._initialize_troubleshooting_scenarios()
        self.protocol_knowledge = self._initialize_protocol_knowledge()
        self.use_case_patterns = self._initialize_use_case_patterns()
        
    def _initialize_capabilities(self) -> Dict[str, NetworkAnalysisCapability]:
        """Initialize network analysis capabilities"""
        return {
            "packet_capture": NetworkAnalysisCapability(
                name="Packet Capture",
                description="Capture and analyze network packets in real-time using tcpdump, tshark, and scapy",
                use_cases=[
                    "Troubleshoot network connectivity issues",
                    "Analyze application-level network behavior",
                    "Investigate security incidents",
                    "Debug protocol-specific problems",
                    "Monitor network traffic patterns"
                ],
                required_parameters=["interface"],
                optional_parameters=["filter", "duration", "max_packets", "output_format"],
                output_format="JSON with packet details, statistics, and analysis",
                typical_duration="30 seconds to 30 minutes",
                resource_requirements="Low CPU, moderate memory for packet buffering"
            ),
            
            "real_time_monitoring": NetworkAnalysisCapability(
                name="Real-time Network Monitoring",
                description="Monitor network performance metrics with configurable alerting",
                use_cases=[
                    "Monitor bandwidth utilization",
                    "Track network latency and jitter",
                    "Detect packet loss",
                    "Monitor connection counts",
                    "Alert on threshold breaches"
                ],
                required_parameters=["interface"],
                optional_parameters=["thresholds", "alert_channels", "sampling_interval"],
                output_format="WebSocket stream with real-time metrics",
                typical_duration="Continuous monitoring",
                resource_requirements="Low CPU, minimal memory"
            ),
            
            "protocol_analysis": NetworkAnalysisCapability(
                name="Protocol Analysis",
                description="Deep analysis of specific network protocols with performance metrics",
                use_cases=[
                    "Analyze HTTP request/response patterns",
                    "Monitor DNS query performance",
                    "Troubleshoot TCP connection issues",
                    "Analyze SMTP email flow",
                    "Debug SSH connection problems"
                ],
                required_parameters=["protocol"],
                optional_parameters=["data_source", "analysis_depth", "time_window"],
                output_format="Detailed protocol metrics and issue identification",
                typical_duration="1-10 minutes",
                resource_requirements="Moderate CPU for deep packet inspection"
            ),
            
            "ai_anomaly_detection": NetworkAnalysisCapability(
                name="AI-Powered Anomaly Detection",
                description="Machine learning-based detection of network anomalies and intelligent diagnosis",
                use_cases=[
                    "Detect unusual traffic patterns",
                    "Identify potential security threats",
                    "Predict network performance issues",
                    "Classify network behavior patterns",
                    "Provide intelligent remediation suggestions"
                ],
                required_parameters=["network_data"],
                optional_parameters=["baseline_data", "sensitivity", "analysis_window"],
                output_format="Anomaly scores, classifications, and AI recommendations",
                typical_duration="2-15 minutes",
                resource_requirements="High CPU for ML processing, significant memory"
            ),
            
            "remote_analysis": NetworkAnalysisCapability(
                name="Remote Network Analysis",
                description="Deploy lightweight agents to remote systems for distributed analysis",
                use_cases=[
                    "Monitor multiple network segments",
                    "Analyze traffic at remote locations",
                    "Coordinate distributed troubleshooting",
                    "Collect network data from edge devices",
                    "Perform cross-site network analysis"
                ],
                required_parameters=["target_id", "analysis_type"],
                optional_parameters=["duration", "agent_config", "data_collection_interval"],
                output_format="Aggregated results from multiple remote agents",
                typical_duration="5 minutes to several hours",
                resource_requirements="Minimal local resources, depends on remote systems"
            )
        }
    
    def _initialize_troubleshooting_scenarios(self) -> List[NetworkTroubleshootingScenario]:
        """Initialize common troubleshooting scenarios"""
        return [
            NetworkTroubleshootingScenario(
                scenario="Slow Web Application Performance",
                symptoms=["High page load times", "Intermittent timeouts", "User complaints"],
                recommended_analysis=["packet_capture", "protocol_analysis", "real_time_monitoring"],
                expected_findings=["HTTP response times", "TCP connection issues", "Bandwidth bottlenecks"],
                remediation_steps=["Optimize HTTP headers", "Adjust TCP window sizes", "Increase bandwidth"]
            ),
            
            NetworkTroubleshootingScenario(
                scenario="Intermittent Network Connectivity",
                symptoms=["Connection drops", "Packet loss", "Ping failures"],
                recommended_analysis=["real_time_monitoring", "packet_capture", "ai_anomaly_detection"],
                expected_findings=["Packet loss patterns", "Network congestion", "Hardware issues"],
                remediation_steps=["Check network hardware", "Adjust QoS settings", "Replace faulty components"]
            ),
            
            NetworkTroubleshootingScenario(
                scenario="DNS Resolution Problems",
                symptoms=["Slow DNS lookups", "DNS timeouts", "Name resolution failures"],
                recommended_analysis=["protocol_analysis", "packet_capture"],
                expected_findings=["DNS query response times", "DNS server issues", "Network path problems"],
                remediation_steps=["Configure backup DNS servers", "Optimize DNS cache", "Check DNS server health"]
            ),
            
            NetworkTroubleshootingScenario(
                scenario="Suspected Security Breach",
                symptoms=["Unusual traffic patterns", "Unexpected connections", "Performance degradation"],
                recommended_analysis=["ai_anomaly_detection", "packet_capture", "protocol_analysis"],
                expected_findings=["Malicious traffic patterns", "Unauthorized connections", "Data exfiltration"],
                remediation_steps=["Block suspicious IPs", "Update security rules", "Investigate compromised systems"]
            ),
            
            NetworkTroubleshootingScenario(
                scenario="VPN Connection Issues",
                symptoms=["VPN disconnections", "Slow VPN performance", "Authentication failures"],
                recommended_analysis=["protocol_analysis", "packet_capture", "real_time_monitoring"],
                expected_findings=["VPN tunnel stability", "Authentication issues", "Bandwidth limitations"],
                remediation_steps=["Adjust VPN settings", "Update VPN client", "Optimize network path"]
            )
        ]
    
    def _initialize_protocol_knowledge(self) -> Dict[str, Dict[str, Any]]:
        """Initialize protocol-specific knowledge"""
        return {
            "http": {
                "common_issues": ["Slow response times", "404 errors", "Connection timeouts"],
                "key_metrics": ["Response time", "Status codes", "Content length", "Keep-alive usage"],
                "analysis_focus": ["Request/response patterns", "Header analysis", "Performance bottlenecks"],
                "troubleshooting_tips": ["Check server response times", "Analyze HTTP headers", "Monitor connection pooling"]
            },
            
            "tcp": {
                "common_issues": ["Connection timeouts", "Retransmissions", "Window scaling problems"],
                "key_metrics": ["RTT", "Window size", "Retransmission rate", "Connection establishment time"],
                "analysis_focus": ["Three-way handshake", "Window scaling", "Congestion control"],
                "troubleshooting_tips": ["Check TCP window sizes", "Monitor retransmissions", "Analyze connection patterns"]
            },
            
            "dns": {
                "common_issues": ["Slow resolution", "NXDOMAIN errors", "DNS cache issues"],
                "key_metrics": ["Query response time", "Query types", "Response codes", "Cache hit ratio"],
                "analysis_focus": ["Query patterns", "Response times", "Error rates"],
                "troubleshooting_tips": ["Check DNS server health", "Analyze query patterns", "Monitor cache performance"]
            },
            
            "ssh": {
                "common_issues": ["Authentication failures", "Connection drops", "Slow file transfers"],
                "key_metrics": ["Connection time", "Authentication time", "Transfer rates", "Error rates"],
                "analysis_focus": ["Authentication process", "Encryption overhead", "Transfer performance"],
                "troubleshooting_tips": ["Check SSH configuration", "Monitor authentication logs", "Analyze transfer patterns"]
            }
        }
    
    def _initialize_use_case_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Initialize common use case patterns"""
        return {
            "performance_troubleshooting": {
                "description": "Diagnose network performance issues",
                "recommended_workflow": [
                    "Start real-time monitoring to establish baseline",
                    "Capture packets during performance issues",
                    "Analyze specific protocols involved",
                    "Use AI analysis for pattern recognition",
                    "Generate remediation recommendations"
                ],
                "typical_duration": "15-30 minutes",
                "success_indicators": ["Identified bottleneck", "Performance metrics improved", "Issue resolved"]
            },
            
            "security_investigation": {
                "description": "Investigate potential security incidents",
                "recommended_workflow": [
                    "Capture packets for forensic analysis",
                    "Use AI anomaly detection for threat identification",
                    "Analyze suspicious protocols and connections",
                    "Deploy remote agents for distributed investigation",
                    "Generate security incident report"
                ],
                "typical_duration": "30-60 minutes",
                "success_indicators": ["Threat identified", "Attack vector understood", "Mitigation implemented"]
            },
            
            "capacity_planning": {
                "description": "Analyze network capacity and plan for growth",
                "recommended_workflow": [
                    "Set up continuous monitoring",
                    "Collect baseline performance data",
                    "Analyze traffic patterns and trends",
                    "Use AI for capacity predictions",
                    "Generate capacity planning report"
                ],
                "typical_duration": "Several days to weeks",
                "success_indicators": ["Usage patterns identified", "Growth projections created", "Capacity recommendations provided"]
            },
            
            "application_debugging": {
                "description": "Debug application-level network issues",
                "recommended_workflow": [
                    "Capture application-specific traffic",
                    "Analyze relevant protocols (HTTP, database, etc.)",
                    "Monitor real-time performance during issue reproduction",
                    "Use AI analysis for pattern recognition",
                    "Provide application-specific recommendations"
                ],
                "typical_duration": "20-45 minutes",
                "success_indicators": ["Application issue identified", "Network cause determined", "Fix implemented"]
            }
        }
    
    def get_capability(self, capability_name: str) -> Optional[NetworkAnalysisCapability]:
        """Get information about a specific capability"""
        return self.capabilities.get(capability_name)
    
    def get_troubleshooting_scenarios(self, symptoms: List[str]) -> List[NetworkTroubleshootingScenario]:
        """Get relevant troubleshooting scenarios based on symptoms"""
        relevant_scenarios = []
        for scenario in self.troubleshooting_scenarios:
            # Check if any symptoms match (using fuzzy matching)
            scenario_symptoms_lower = [s.lower() for s in scenario.symptoms]
            for symptom in symptoms:
                symptom_lower = symptom.lower()
                # Check for exact match or partial match
                if any(symptom_lower in scenario_symptom or scenario_symptom in symptom_lower 
                       for scenario_symptom in scenario_symptoms_lower):
                    relevant_scenarios.append(scenario)
                    break
                # Check for keyword matches
                symptom_keywords = symptom_lower.split()
                for keyword in symptom_keywords:
                    if len(keyword) > 3 and any(keyword in scenario_symptom 
                                               for scenario_symptom in scenario_symptoms_lower):
                        relevant_scenarios.append(scenario)
                        break
        return relevant_scenarios
    
    def get_protocol_knowledge(self, protocol: str) -> Optional[Dict[str, Any]]:
        """Get knowledge about a specific protocol"""
        return self.protocol_knowledge.get(protocol.lower())
    
    def recommend_analysis_workflow(self, use_case: str, symptoms: List[str] = None) -> Dict[str, Any]:
        """Recommend an analysis workflow based on use case and symptoms"""
        # Get base workflow from use case patterns
        base_workflow = self.use_case_patterns.get(use_case, {})
        
        # Enhance with symptom-specific recommendations
        if symptoms:
            relevant_scenarios = self.get_troubleshooting_scenarios(symptoms)
            if relevant_scenarios:
                # Merge recommendations from relevant scenarios
                additional_analysis = []
                for scenario in relevant_scenarios:
                    additional_analysis.extend(scenario.recommended_analysis)
                
                # Add unique additional analysis types
                if "recommended_workflow" in base_workflow:
                    existing_analysis = base_workflow["recommended_workflow"]
                    for analysis in set(additional_analysis):
                        if analysis not in str(existing_analysis):
                            existing_analysis.append(f"Consider {analysis} for symptom-specific analysis")
        
        return base_workflow
    
    def get_ai_suggestions(self, analysis_results: Dict[str, Any]) -> List[str]:
        """Generate AI-powered suggestions based on analysis results"""
        suggestions = []
        
        # Analyze results and provide intelligent suggestions
        if "packet_loss" in analysis_results and analysis_results.get("packet_loss", 0) > 1:
            suggestions.append("High packet loss detected - check network hardware and congestion")
        
        if "latency" in analysis_results and analysis_results.get("latency", 0) > 100:
            suggestions.append("High latency detected - investigate network path and routing")
        
        if "anomalies" in analysis_results and analysis_results.get("anomalies"):
            suggestions.append("Network anomalies detected - consider security investigation")
        
        if "protocol_errors" in analysis_results and analysis_results.get("protocol_errors"):
            suggestions.append("Protocol errors found - check application configuration and compatibility")
        
        # Add general recommendations
        suggestions.append("Consider implementing continuous monitoring for proactive issue detection")
        suggestions.append("Document findings for future reference and trend analysis")
        
        return suggestions

# Global instance for AI system to use
network_analyzer_knowledge = NetworkAnalyzerKnowledge()