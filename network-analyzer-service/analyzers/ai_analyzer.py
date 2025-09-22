"""
AI Network Analyzer Module
Provides intelligent analysis and diagnosis of network issues using AI
"""

import asyncio
import json
import logging
import time
import uuid
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta

import structlog
import httpx
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from models.analysis_models import AIAnalysisResult, NetworkAlert

logger = structlog.get_logger(__name__)

class AINetworkAnalyzer:
    """AI-powered network analysis and diagnosis"""
    
    def __init__(self):
        self.ai_service_url = "http://ai-brain:3005"
        self.analysis_cache: Dict[str, Dict] = {}
        self.anomaly_detector = IsolationForest(contamination=0.1, random_state=42)
        self.scaler = StandardScaler()
        self.is_trained = False
        
        # Network issue patterns and signatures
        self.issue_patterns = {
            "high_latency": {
                "indicators": ["response_time > 100ms", "tcp_retransmissions", "slow_queries"],
                "common_causes": ["network_congestion", "routing_issues", "server_overload"],
                "remediation": ["check_bandwidth", "optimize_routing", "scale_resources"]
            },
            "packet_loss": {
                "indicators": ["dropped_packets", "tcp_retransmissions", "incomplete_transfers"],
                "common_causes": ["network_congestion", "faulty_hardware", "buffer_overflow"],
                "remediation": ["check_hardware", "adjust_buffer_sizes", "load_balancing"]
            },
            "connectivity_issues": {
                "indicators": ["connection_timeouts", "dns_failures", "unreachable_hosts"],
                "common_causes": ["dns_issues", "firewall_blocking", "routing_problems"],
                "remediation": ["check_dns", "verify_firewall_rules", "trace_route"]
            },
            "security_anomalies": {
                "indicators": ["unusual_traffic_patterns", "port_scanning", "suspicious_connections"],
                "common_causes": ["malware", "unauthorized_access", "ddos_attack"],
                "remediation": ["block_suspicious_ips", "update_security_rules", "investigate_logs"]
            }
        }
    
    def is_ready(self) -> bool:
        """Check if AI analyzer is ready"""
        try:
            # Check if AI service is available
            return True  # For now, assume ready
        except Exception:
            return False
    
    async def analyze_capture_session(self, session_id: str) -> AIAnalysisResult:
        """Analyze a packet capture session using AI"""
        try:
            analysis_id = str(uuid.uuid4())
            
            logger.info("Starting AI analysis of capture session", 
                       session_id=session_id, analysis_id=analysis_id)
            
            # Get capture data (this would be implemented to fetch from packet analyzer)
            capture_data = await self._get_capture_data(session_id)
            
            if not capture_data:
                raise ValueError(f"No capture data found for session {session_id}")
            
            # Perform various AI analyses
            anomalies = await self._detect_anomalies(capture_data)
            performance_insights = await self._analyze_performance(capture_data)
            security_analysis = await self._analyze_security(capture_data)
            protocol_insights = await self._analyze_protocols(capture_data)
            
            # Generate findings and recommendations
            findings = []
            recommendations = []
            security_concerns = []
            
            # Process anomalies
            if anomalies:
                findings.extend([f"Detected {len(anomalies)} network anomalies"])
                for anomaly in anomalies:
                    findings.append(f"Anomaly: {anomaly['description']}")
                    if anomaly.get('severity') == 'high':
                        security_concerns.append(anomaly['description'])
            
            # Process performance insights
            if performance_insights.get('issues'):
                for issue in performance_insights['issues']:
                    findings.append(f"Performance issue: {issue}")
                    recommendations.extend(self._get_performance_recommendations(issue))
            
            # Process security analysis
            if security_analysis.get('threats'):
                for threat in security_analysis['threats']:
                    security_concerns.append(threat)
                    recommendations.extend(self._get_security_recommendations(threat))
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(
                capture_data, anomalies, performance_insights, security_analysis
            )
            
            result = AIAnalysisResult(
                analysis_id=analysis_id,
                confidence_score=confidence_score,
                findings=findings,
                recommendations=recommendations,
                anomalies_detected=anomalies,
                performance_insights=performance_insights,
                security_concerns=security_concerns
            )
            
            # Cache the result
            self.analysis_cache[analysis_id] = {
                "result": result,
                "timestamp": time.time(),
                "session_id": session_id
            }
            
            logger.info("Completed AI analysis", 
                       analysis_id=analysis_id, 
                       confidence_score=confidence_score)
            
            return result
            
        except Exception as e:
            logger.error("AI analysis failed", 
                        session_id=session_id, error=str(e))
            raise
    
    async def diagnose_network_issue(
        self,
        symptoms: List[str],
        network_data: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Diagnose network issues based on symptoms and data"""
        try:
            diagnosis_id = str(uuid.uuid4())
            
            logger.info("Starting network diagnosis", 
                       diagnosis_id=diagnosis_id, 
                       symptoms=symptoms)
            
            # Analyze symptoms against known patterns
            issue_matches = self._match_issue_patterns(symptoms)
            
            # Incorporate network data if available
            if network_data:
                data_insights = await self._analyze_network_metrics(network_data)
                issue_matches.update(data_insights)
            
            # Use AI service for advanced analysis
            ai_diagnosis = await self._get_ai_diagnosis(symptoms, network_data, context)
            
            # Determine most likely issue type
            issue_type, confidence = self._determine_issue_type(issue_matches, ai_diagnosis)
            
            # Generate root cause analysis
            root_cause = self._analyze_root_cause(issue_type, symptoms, network_data)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(issue_type, symptoms, context)
            
            # Create remediation plan if confidence is high enough
            remediation_plan = None
            if confidence > 0.7:
                remediation_plan = self._create_remediation_plan(issue_type, symptoms, context)
            
            # Gather supporting evidence
            supporting_evidence = self._gather_supporting_evidence(
                symptoms, network_data, issue_matches
            )
            
            diagnosis = {
                "diagnosis_id": diagnosis_id,
                "issue_type": issue_type,
                "confidence_score": confidence,
                "root_cause": root_cause,
                "recommendations": recommendations,
                "remediation_plan": remediation_plan,
                "supporting_evidence": supporting_evidence,
                "remediation_available": remediation_plan is not None
            }
            
            # Cache diagnosis
            self.analysis_cache[diagnosis_id] = {
                "diagnosis": diagnosis,
                "timestamp": time.time(),
                "symptoms": symptoms
            }
            
            logger.info("Completed network diagnosis", 
                       diagnosis_id=diagnosis_id, 
                       issue_type=issue_type,
                       confidence_score=confidence)
            
            return diagnosis
            
        except Exception as e:
            logger.error("Network diagnosis failed", error=str(e))
            raise
    
    async def _get_capture_data(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get capture data for analysis"""
        # This would integrate with the packet analyzer
        # For now, return mock data structure
        return {
            "packets": [],
            "statistics": {},
            "duration": 60,
            "interfaces": ["eth0"]
        }
    
    async def _detect_anomalies(self, capture_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect network anomalies using machine learning"""
        try:
            anomalies = []
            
            # Extract features for anomaly detection
            features = self._extract_anomaly_features(capture_data)
            
            if not features:
                return anomalies
            
            # Use isolation forest for anomaly detection
            if not self.is_trained and len(features) > 10:
                # Train on current data (in production, use historical data)
                feature_array = np.array(features)
                scaled_features = self.scaler.fit_transform(feature_array)
                self.anomaly_detector.fit(scaled_features)
                self.is_trained = True
            
            if self.is_trained:
                feature_array = np.array(features)
                scaled_features = self.scaler.transform(feature_array)
                anomaly_scores = self.anomaly_detector.decision_function(scaled_features)
                anomaly_labels = self.anomaly_detector.predict(scaled_features)
                
                # Identify anomalies
                for i, (score, label) in enumerate(zip(anomaly_scores, anomaly_labels)):
                    if label == -1:  # Anomaly detected
                        severity = "high" if score < -0.5 else "medium"
                        anomalies.append({
                            "index": i,
                            "score": float(score),
                            "severity": severity,
                            "description": f"Network anomaly detected (score: {score:.3f})",
                            "timestamp": time.time()
                        })
            
            return anomalies
            
        except Exception as e:
            logger.warning("Anomaly detection failed", error=str(e))
            return []
    
    def _extract_anomaly_features(self, capture_data: Dict[str, Any]) -> List[List[float]]:
        """Extract features for anomaly detection"""
        # This would extract relevant features from network data
        # For now, return mock features
        return [[1.0, 2.0, 3.0], [1.1, 2.1, 3.1], [0.9, 1.9, 2.9]]
    
    async def _analyze_performance(self, capture_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze network performance"""
        performance_insights = {
            "latency_analysis": {},
            "throughput_analysis": {},
            "packet_loss_analysis": {},
            "issues": []
        }
        
        # Analyze latency patterns
        # This would be implemented with real packet timing analysis
        
        # Analyze throughput
        # This would calculate actual throughput metrics
        
        # Identify performance issues
        # This would detect common performance problems
        
        return performance_insights
    
    async def _analyze_security(self, capture_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze security aspects of network traffic"""
        security_analysis = {
            "threats": [],
            "suspicious_patterns": [],
            "recommendations": []
        }
        
        # Detect port scanning
        # Detect unusual traffic patterns
        # Detect potential DDoS
        # Detect malware communication patterns
        
        return security_analysis
    
    async def _analyze_protocols(self, capture_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze protocol usage and issues"""
        protocol_insights = {
            "protocol_distribution": {},
            "protocol_issues": [],
            "optimization_opportunities": []
        }
        
        return protocol_insights
    
    def _match_issue_patterns(self, symptoms: List[str]) -> Dict[str, float]:
        """Match symptoms against known issue patterns"""
        matches = {}
        
        for issue_type, pattern in self.issue_patterns.items():
            score = 0.0
            for symptom in symptoms:
                for indicator in pattern["indicators"]:
                    if any(keyword in symptom.lower() for keyword in indicator.split("_")):
                        score += 1.0
            
            if score > 0:
                matches[issue_type] = score / len(pattern["indicators"])
        
        return matches
    
    async def _analyze_network_metrics(self, network_data: Dict[str, Any]) -> Dict[str, float]:
        """Analyze network metrics for issue detection"""
        insights = {}
        
        # Analyze latency
        if "latency" in network_data:
            latency = network_data["latency"]
            if latency > 100:
                insights["high_latency"] = min(1.0, latency / 200)
        
        # Analyze packet loss
        if "packet_loss" in network_data:
            loss = network_data["packet_loss"]
            if loss > 0.01:
                insights["packet_loss"] = min(1.0, loss * 10)
        
        # Analyze bandwidth utilization
        if "bandwidth_utilization" in network_data:
            util = network_data["bandwidth_utilization"]
            if util > 0.8:
                insights["high_bandwidth"] = min(1.0, (util - 0.8) * 5)
        
        return insights
    
    async def _get_ai_diagnosis(
        self,
        symptoms: List[str],
        network_data: Optional[Dict[str, Any]],
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Get AI-powered diagnosis from the AI service"""
        try:
            async with httpx.AsyncClient() as client:
                payload = {
                    "message": f"Diagnose network issue with symptoms: {', '.join(symptoms)}",
                    "context": {
                        "type": "network_diagnosis",
                        "symptoms": symptoms,
                        "network_data": network_data,
                        "context": context
                    }
                }
                
                response = await client.post(
                    f"{self.ai_service_url}/ai/chat",
                    json=payload,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return {
                        "ai_response": result.get("response", ""),
                        "confidence": result.get("confidence", 0.5),
                        "suggestions": result.get("suggestions", [])
                    }
        
        except Exception as e:
            logger.warning("AI diagnosis request failed", error=str(e))
        
        return {"ai_response": "", "confidence": 0.0, "suggestions": []}
    
    def _determine_issue_type(
        self,
        pattern_matches: Dict[str, float],
        ai_diagnosis: Dict[str, Any]
    ) -> Tuple[str, float]:
        """Determine the most likely issue type and confidence"""
        if not pattern_matches:
            return "unknown", 0.1
        
        # Find highest scoring pattern match
        best_match = max(pattern_matches.items(), key=lambda x: x[1])
        issue_type, pattern_score = best_match
        
        # Incorporate AI confidence if available
        ai_confidence = ai_diagnosis.get("confidence", 0.0)
        
        # Calculate combined confidence
        combined_confidence = (pattern_score * 0.7) + (ai_confidence * 0.3)
        
        return issue_type, min(1.0, combined_confidence)
    
    def _analyze_root_cause(
        self,
        issue_type: str,
        symptoms: List[str],
        network_data: Optional[Dict[str, Any]]
    ) -> str:
        """Analyze and determine root cause"""
        if issue_type in self.issue_patterns:
            causes = self.issue_patterns[issue_type]["common_causes"]
            
            # Simple heuristic to select most likely cause
            # In production, this would be more sophisticated
            if network_data:
                if "server_response_time" in network_data and network_data["server_response_time"] > 1000:
                    return "server_overload"
                elif "bandwidth_utilization" in network_data and network_data["bandwidth_utilization"] > 0.9:
                    return "network_congestion"
            
            return causes[0] if causes else "unknown"
        
        return "unknown"
    
    def _generate_recommendations(
        self,
        issue_type: str,
        symptoms: List[str],
        context: Optional[Dict[str, Any]]
    ) -> List[str]:
        """Generate recommendations based on issue type"""
        recommendations = []
        
        if issue_type in self.issue_patterns:
            base_recommendations = self.issue_patterns[issue_type]["remediation"]
            recommendations.extend(base_recommendations)
        
        # Add context-specific recommendations
        if context:
            if context.get("application") == "web_server":
                recommendations.append("Check web server performance and configuration")
            elif context.get("time_of_day") == "peak_hours":
                recommendations.append("Consider load balancing during peak hours")
        
        # Add general recommendations
        recommendations.extend([
            "Monitor network metrics continuously",
            "Review network topology and configuration",
            "Check for recent infrastructure changes"
        ])
        
        return list(set(recommendations))  # Remove duplicates
    
    def _create_remediation_plan(
        self,
        issue_type: str,
        symptoms: List[str],
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Create automated remediation plan"""
        plan = {
            "steps": [],
            "estimated_duration": "5-15 minutes",
            "risk_level": "low",
            "requires_approval": True
        }
        
        if issue_type == "high_latency":
            plan["steps"] = [
                {"action": "check_bandwidth_utilization", "description": "Check current bandwidth usage"},
                {"action": "analyze_routing_table", "description": "Analyze network routing"},
                {"action": "test_connectivity", "description": "Test connectivity to key endpoints"}
            ]
        elif issue_type == "connectivity_issues":
            plan["steps"] = [
                {"action": "check_dns_resolution", "description": "Verify DNS resolution"},
                {"action": "test_firewall_rules", "description": "Check firewall configuration"},
                {"action": "trace_network_path", "description": "Trace network path to destination"}
            ]
        
        return plan
    
    def _gather_supporting_evidence(
        self,
        symptoms: List[str],
        network_data: Optional[Dict[str, Any]],
        issue_matches: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        """Gather supporting evidence for diagnosis"""
        evidence = []
        
        # Add symptom evidence
        for symptom in symptoms:
            evidence.append({
                "type": "symptom",
                "description": symptom,
                "relevance": "high"
            })
        
        # Add metric evidence
        if network_data:
            for metric, value in network_data.items():
                evidence.append({
                    "type": "metric",
                    "metric": metric,
                    "value": value,
                    "relevance": "medium"
                })
        
        # Add pattern match evidence
        for issue_type, score in issue_matches.items():
            if score > 0.3:
                evidence.append({
                    "type": "pattern_match",
                    "issue_type": issue_type,
                    "confidence": score,
                    "relevance": "high" if score > 0.7 else "medium"
                })
        
        return evidence
    
    def _calculate_confidence_score(
        self,
        capture_data: Dict[str, Any],
        anomalies: List[Dict[str, Any]],
        performance_insights: Dict[str, Any],
        security_analysis: Dict[str, Any]
    ) -> float:
        """Calculate overall confidence score for analysis"""
        base_score = 0.5
        
        # Increase confidence based on data quality
        if capture_data.get("packets"):
            packet_count = len(capture_data["packets"])
            if packet_count > 1000:
                base_score += 0.2
            elif packet_count > 100:
                base_score += 0.1
        
        # Adjust based on findings
        if anomalies:
            base_score += min(0.2, len(anomalies) * 0.05)
        
        if performance_insights.get("issues"):
            base_score += min(0.1, len(performance_insights["issues"]) * 0.02)
        
        return min(1.0, base_score)
    
    def _get_performance_recommendations(self, issue: str) -> List[str]:
        """Get recommendations for performance issues"""
        recommendations = {
            "high_latency": ["Optimize network routing", "Check for congestion", "Upgrade bandwidth"],
            "low_throughput": ["Check network configuration", "Optimize TCP settings", "Review QoS policies"],
            "packet_loss": ["Check network hardware", "Adjust buffer sizes", "Review network topology"]
        }
        
        return recommendations.get(issue, ["Review network configuration"])
    
    def _get_security_recommendations(self, threat: str) -> List[str]:
        """Get recommendations for security threats"""
        recommendations = {
            "port_scan": ["Block suspicious IPs", "Review firewall rules", "Monitor access logs"],
            "ddos": ["Enable DDoS protection", "Rate limit connections", "Contact ISP"],
            "malware": ["Run security scan", "Update antivirus", "Isolate affected systems"]
        }
        
        return recommendations.get(threat, ["Review security policies"])
    
    async def execute_remediation(self, remediation_plan: Dict[str, Any], user_id: int):
        """Execute automated remediation plan"""
        try:
            logger.info("Starting automated remediation", 
                       user_id=user_id, 
                       plan=remediation_plan)
            
            for step in remediation_plan.get("steps", []):
                action = step["action"]
                description = step["description"]
                
                logger.info("Executing remediation step", 
                           action=action, 
                           description=description)
                
                # Execute the remediation action
                # This would integrate with the automation service
                await self._execute_remediation_action(action, step)
                
                # Wait between steps
                await asyncio.sleep(2)
            
            logger.info("Completed automated remediation", user_id=user_id)
            
        except Exception as e:
            logger.error("Remediation execution failed", 
                        user_id=user_id, error=str(e))
            raise
    
    async def _execute_remediation_action(self, action: str, step: Dict[str, Any]):
        """Execute a specific remediation action"""
        # This would integrate with the automation service to execute actions
        # For now, just log the action
        logger.info("Executing remediation action", action=action, step=step)
        
        # Simulate action execution
        await asyncio.sleep(1)