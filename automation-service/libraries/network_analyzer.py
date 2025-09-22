"""
Network Analyzer Library for Automation Service
Provides integration with the Network Analyzer Service for protocol analysis
"""

import asyncio
import json
import logging
import os
from typing import Dict, List, Optional, Any
import aiohttp
import structlog

logger = structlog.get_logger(__name__)

class NetworkAnalyzerLibrary:
    """Library for interacting with Network Analyzer Service"""
    
    def __init__(self):
        self.base_url = os.getenv('NETWORK_ANALYZER_SERVICE_URL', 'http://network-analyzer-service:3006')
        self.timeout = aiohttp.ClientTimeout(total=300)  # 5 minute timeout
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for service requests"""
        return {
            "Content-Type": "application/json",
            "x-user-id": "1",  # System user ID
            "x-username": "automation-service",
            "x-user-email": "automation@opsconductor.local",
            "x-user-role": "admin",
            "x-user-permissions": "*",  # Admin wildcard permission
            "x-authenticated": "true"
        }

    async def analyze_protocol(
        self,
        protocol: str,
        data_source: str,
        filters: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Analyze network protocol traffic
        
        Args:
            protocol: Protocol to analyze (tcp, udp, http, https, dns, etc.)
            data_source: Data source (network interface, capture file, etc.)
            filters: Optional filters for analysis
            
        Returns:
            Protocol analysis results
        """
        try:
            logger.info("Starting protocol analysis", 
                       protocol=protocol, 
                       data_source=data_source)
            
            # Prepare request payload
            payload = {
                "protocol": protocol,
                "data_source": data_source,
                "filters": filters or {}
            }
            
            # Make request to network analyzer service
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(
                    f"{self.base_url}/api/v1/analysis/protocol",
                    json=payload,
                    headers=self._get_auth_headers()
                ) as response:
                    
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"Protocol analysis failed: {response.status} - {error_text}")
                    
                    result = await response.json()
                    
                    logger.info("Protocol analysis completed successfully",
                               protocol=protocol,
                               packets_analyzed=result.get('statistics', {}).get('packet_count', 0))
                    
                    return {
                        "success": True,
                        "protocol": result.get("protocol"),
                        "analysis_results": result.get("analysis_results", {}),
                        "statistics": result.get("statistics", {}),
                        "recommendations": result.get("recommendations", []),
                        "timestamp": result.get("timestamp")
                    }
                    
        except Exception as e:
            logger.error("Protocol analysis failed", 
                        protocol=protocol, 
                        error=str(e))
            return {
                "success": False,
                "error": str(e),
                "protocol": protocol,
                "data_source": data_source
            }
    
    async def start_capture(
        self,
        interface: str,
        filter_expression: Optional[str] = None,
        duration: Optional[int] = None,
        packet_count: Optional[int] = None,
        enable_ai_analysis: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Start packet capture session
        
        Args:
            interface: Network interface to capture on
            filter_expression: BPF filter expression
            duration: Capture duration in seconds
            packet_count: Maximum packets to capture
            enable_ai_analysis: Enable AI-powered analysis
            
        Returns:
            Capture session information
        """
        try:
            logger.info("Starting packet capture", 
                       interface=interface, 
                       duration=duration)
            
            payload = {
                "interface": interface,
                "filter_expression": filter_expression,
                "duration": duration,
                "packet_count": packet_count,
                "enable_ai_analysis": enable_ai_analysis
            }
            
            # Remove None values
            payload = {k: v for k, v in payload.items() if v is not None}
            
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(
                    f"{self.base_url}/api/v1/analysis/start-capture",
                    json=payload,
                    headers=self._get_auth_headers()
                ) as response:
                    
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"Capture start failed: {response.status} - {error_text}")
                    
                    result = await response.json()
                    
                    logger.info("Packet capture started successfully",
                               session_id=result.get("session_id"),
                               interface=interface)
                    
                    return {
                        "success": True,
                        "session_id": result.get("session_id"),
                        "status": result.get("status"),
                        "interface": interface,
                        "message": "Packet capture started successfully"
                    }
                    
        except Exception as e:
            logger.error("Failed to start packet capture", 
                        interface=interface, 
                        error=str(e))
            return {
                "success": False,
                "error": str(e),
                "interface": interface
            }
    
    async def get_capture_results(
        self,
        session_id: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Get packet capture results
        
        Args:
            session_id: Capture session ID
            
        Returns:
            Capture results
        """
        try:
            logger.info("Getting capture results", session_id=session_id)
            
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(
                    f"{self.base_url}/api/v1/analysis/capture/{session_id}",
                    headers=self._get_auth_headers()
                ) as response:
                    
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"Failed to get capture results: {response.status} - {error_text}")
                    
                    result = await response.json()
                    
                    logger.info("Retrieved capture results successfully",
                               session_id=session_id,
                               status=result.get("status"))
                    
                    return {
                        "success": True,
                        "session_id": session_id,
                        "status": result.get("status"),
                        "results": result.get("results", {}),
                        "statistics": result.get("statistics", {}),
                        "ai_analysis": result.get("ai_analysis", {})
                    }
                    
        except Exception as e:
            logger.error("Failed to get capture results", 
                        session_id=session_id, 
                        error=str(e))
            return {
                "success": False,
                "error": str(e),
                "session_id": session_id
            }
    
    async def ai_diagnose(
        self,
        symptoms: List[str],
        network_data: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
        enable_auto_remediation: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        AI-powered network diagnosis
        
        Args:
            symptoms: List of observed network symptoms
            network_data: Network data for analysis
            context: Additional context
            enable_auto_remediation: Enable automatic remediation
            
        Returns:
            AI diagnosis results
        """
        try:
            logger.info("Starting AI network diagnosis", 
                       symptoms=symptoms)
            
            payload = {
                "symptoms": symptoms,
                "network_data": network_data or {},
                "context": context or {},
                "enable_auto_remediation": enable_auto_remediation
            }
            
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(
                    f"{self.base_url}/api/v1/analysis/ai-diagnose",
                    json=payload,
                    headers=self._get_auth_headers()
                ) as response:
                    
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"AI diagnosis failed: {response.status} - {error_text}")
                    
                    result = await response.json()
                    
                    logger.info("AI diagnosis completed successfully",
                               diagnosis_id=result.get("diagnosis_id"))
                    
                    return {
                        "success": True,
                        "diagnosis_id": result.get("diagnosis_id"),
                        "diagnosis": result.get("diagnosis", {}),
                        "confidence": result.get("confidence"),
                        "recommendations": result.get("recommendations", []),
                        "remediation_steps": result.get("remediation_steps", [])
                    }
                    
        except Exception as e:
            logger.error("AI diagnosis failed", 
                        symptoms=symptoms, 
                        error=str(e))
            return {
                "success": False,
                "error": str(e),
                "symptoms": symptoms
            }

# Export the library instance
network_analyzer = NetworkAnalyzerLibrary()

# Export individual functions for direct access
analyze_protocol = network_analyzer.analyze_protocol
start_capture = network_analyzer.start_capture
get_capture_results = network_analyzer.get_capture_results
ai_diagnose = network_analyzer.ai_diagnose