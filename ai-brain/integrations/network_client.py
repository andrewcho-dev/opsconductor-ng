#!/usr/bin/env python3
"""
Network Analyzer Service Client
Provides interface to the network-analyzer-service for network diagnostics
"""

import aiohttp
import asyncio
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

class NetworkAnalyzerClient:
    """Client for interacting with the network-analyzer-service"""
    
    def __init__(self, base_url: str = "http://network-analyzer-service:3006"):
        self.base_url = base_url.rstrip('/')
        self.session = None
        
    async def _get_session(self):
        """Get or create aiohttp session"""
        if self.session is None:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def close(self):
        """Close the client session"""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def ping_host(self, target: str, count: int = 4) -> Dict[str, Any]:
        """
        Ping a host using the network analyzer service
        
        Args:
            target: IP address or hostname to ping
            count: Number of ping packets to send
            
        Returns:
            Ping results with statistics
        """
        try:
            session = await self._get_session()
            
            payload = {
                "target": target,
                "count": count,
                "timeout": 5
            }
            
            async with session.post(f"{self.base_url}/api/v1/diagnostics/ping", json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"Ping to {target} completed successfully")
                    return result
                else:
                    error_text = await response.text()
                    logger.error(f"Ping failed: {response.status} - {error_text}")
                    return {
                        "success": False,
                        "error": f"HTTP {response.status}: {error_text}",
                        "target": target
                    }
                    
        except Exception as e:
            logger.error(f"Ping request failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "target": target
            }
    
    async def traceroute_host(self, target: str, max_hops: int = 30) -> Dict[str, Any]:
        """
        Perform traceroute to a host
        
        Args:
            target: IP address or hostname to trace
            max_hops: Maximum number of hops
            
        Returns:
            Traceroute results
        """
        try:
            session = await self._get_session()
            
            payload = {
                "target": target,
                "max_hops": max_hops,
                "timeout": 5
            }
            
            async with session.post(f"{self.base_url}/api/v1/diagnostics/traceroute", json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"Traceroute to {target} completed successfully")
                    return result
                else:
                    error_text = await response.text()
                    logger.error(f"Traceroute failed: {response.status} - {error_text}")
                    return {
                        "success": False,
                        "error": f"HTTP {response.status}: {error_text}",
                        "target": target
                    }
                    
        except Exception as e:
            logger.error(f"Traceroute request failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "target": target
            }
    
    async def port_scan(self, target: str, ports: List[int] = None) -> Dict[str, Any]:
        """
        Scan ports on a target host
        
        Args:
            target: IP address or hostname to scan
            ports: List of ports to scan (default: common ports)
            
        Returns:
            Port scan results
        """
        try:
            session = await self._get_session()
            
            if ports is None:
                ports = [22, 23, 25, 53, 80, 110, 143, 443, 993, 995, 3389, 5432, 3306]
            
            payload = {
                "target": target,
                "ports": ports,
                "timeout": 3
            }
            
            async with session.post(f"{self.base_url}/api/v1/diagnostics/port-scan", json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"Port scan of {target} completed successfully")
                    return result
                else:
                    error_text = await response.text()
                    logger.error(f"Port scan failed: {response.status} - {error_text}")
                    return {
                        "success": False,
                        "error": f"HTTP {response.status}: {error_text}",
                        "target": target
                    }
                    
        except Exception as e:
            logger.error(f"Port scan request failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "target": target
            }
    
    async def get_network_status(self) -> Dict[str, Any]:
        """
        Get current network monitoring status
        
        Returns:
            Network status information
        """
        try:
            session = await self._get_session()
            
            async with session.get(f"{self.base_url}/api/v1/monitoring/status") as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info("Network status retrieved successfully")
                    return result
                else:
                    error_text = await response.text()
                    logger.error(f"Network status failed: {response.status} - {error_text}")
                    return {
                        "success": False,
                        "error": f"HTTP {response.status}: {error_text}"
                    }
                    
        except Exception as e:
            logger.error(f"Network status request failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def start_packet_capture(self, interface: str = "any", duration: int = 60, filter_expression: str = None) -> Dict[str, Any]:
        """
        Start a packet capture session
        
        Args:
            interface: Network interface to capture on
            duration: Capture duration in seconds
            filter_expression: BPF filter expression
            
        Returns:
            Capture session information
        """
        try:
            session = await self._get_session()
            
            payload = {
                "interface": interface,
                "duration": duration,
                "filter_expression": filter_expression,
                "enable_ai_analysis": True
            }
            
            async with session.post(f"{self.base_url}/api/v1/analysis/start-capture", json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"Packet capture started: {result.get('session_id')}")
                    return result
                else:
                    error_text = await response.text()
                    logger.error(f"Packet capture failed: {response.status} - {error_text}")
                    return {
                        "success": False,
                        "error": f"HTTP {response.status}: {error_text}"
                    }
                    
        except Exception as e:
            logger.error(f"Packet capture request failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_capture_results(self, session_id: str) -> Dict[str, Any]:
        """
        Get results from a packet capture session
        
        Args:
            session_id: Capture session ID
            
        Returns:
            Capture results
        """
        try:
            session = await self._get_session()
            
            async with session.get(f"{self.base_url}/api/v1/analysis/capture/{session_id}") as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"Capture results retrieved for session: {session_id}")
                    return result
                else:
                    error_text = await response.text()
                    logger.error(f"Get capture results failed: {response.status} - {error_text}")
                    return {
                        "success": False,
                        "error": f"HTTP {response.status}: {error_text}",
                        "session_id": session_id
                    }
                    
        except Exception as e:
            logger.error(f"Get capture results request failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "session_id": session_id
            }
    
    async def ai_network_diagnosis(self, symptoms: List[str], network_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Get AI-powered network diagnosis
        
        Args:
            symptoms: List of network symptoms/issues
            network_data: Additional network data for analysis
            
        Returns:
            AI diagnosis results
        """
        try:
            session = await self._get_session()
            
            payload = {
                "symptoms": symptoms,
                "network_data": network_data or {},
                "context": {
                    "timestamp": datetime.now().isoformat(),
                    "source": "ai-brain"
                }
            }
            
            async with session.post(f"{self.base_url}/api/v1/analysis/ai-diagnose", json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info("AI network diagnosis completed successfully")
                    return result
                else:
                    error_text = await response.text()
                    logger.error(f"AI diagnosis failed: {response.status} - {error_text}")
                    return {
                        "success": False,
                        "error": f"HTTP {response.status}: {error_text}"
                    }
                    
        except Exception as e:
            logger.error(f"AI diagnosis request failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check if the network analyzer service is healthy
        
        Returns:
            Health status
        """
        try:
            session = await self._get_session()
            
            async with session.get(f"{self.base_url}/health") as response:
                if response.status == 200:
                    result = await response.json()
                    logger.debug("Network analyzer service is healthy")
                    return result
                else:
                    error_text = await response.text()
                    logger.warning(f"Health check failed: {response.status} - {error_text}")
                    return {
                        "status": "unhealthy",
                        "error": f"HTTP {response.status}: {error_text}"
                    }
                    
        except Exception as e:
            logger.error(f"Health check request failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }