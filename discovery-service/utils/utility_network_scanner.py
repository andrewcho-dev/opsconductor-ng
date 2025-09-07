#!/usr/bin/env python3
"""
Network Scanner Utility Module
Handles network scanning operations for discovery service
"""

import asyncio
import nmap
from typing import List, Dict, Optional, Tuple
from shared.logging import get_logger

logger = get_logger("discovery-service.network-scanner")


class NetworkScannerUtility:
    """Utility class for network scanning operations"""
    
    def __init__(self):
        self.nm = nmap.PortScanner()
    
    async def scan_network_range(self, cidr_range: str, ports: str = "22,3389,5985,5986") -> List[Dict]:
        """Scan network range for active hosts and services"""
        try:
            logger.info(f"Starting network scan: {cidr_range} on ports {ports}")
            
            # Run nmap scan in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            scan_result = await loop.run_in_executor(
                None, 
                self._execute_nmap_scan, 
                cidr_range, 
                ports
            )
            
            discovered_hosts = []
            for host in scan_result.all_hosts():
                host_data = self._extract_host_data(scan_result, host)
                analyzed_host = self.analyze_host(host_data)
                if analyzed_host:
                    discovered_hosts.append(analyzed_host)
            
            logger.info(f"Network scan completed: {cidr_range} - found {len(discovered_hosts)} hosts")
            return discovered_hosts
            
        except Exception as e:
            logger.error(f"Network scan failed for {cidr_range}: {e}")
            raise
    
    def _execute_nmap_scan(self, cidr_range: str, ports: str) -> object:
        """Execute nmap scan synchronously"""
        return self.nm.scan(
            hosts=cidr_range,
            ports=ports,
            arguments='-sS -O -sV --host-timeout 30s --max-retries 2'
        )
    
    def _extract_host_data(self, scan_result: object, host: str) -> Dict:
        """Extract host data from nmap scan result"""
        return {
            'ip_address': host,
            'hostname': scan_result[host].hostname(),
            'state': scan_result[host].state(),
            'protocols': list(scan_result[host].all_protocols()),
            'ports': scan_result[host].all_tcp() if 'tcp' in scan_result[host].all_protocols() else {},
            'os_fingerprint': scan_result[host].get('osmatch', []),
            'scan_data': scan_result[host]
        }
    
    def analyze_host(self, host_data: Dict) -> Optional[Dict]:
        """Analyze host data to determine OS and services"""
        if host_data['state'] != 'up':
            return None
        
        # Detect OS type and version
        os_type = self.detect_os_type(host_data)
        os_version = self.detect_os_version(host_data)
        
        # Detect services and preferred service
        services, preferred_service = self.detect_services(host_data)
        
        return {
            'ip_address': host_data['ip_address'],
            'hostname': host_data['hostname'] or None,
            'os_type': os_type,
            'os_version': os_version,
            'services': services,
            'preferred_service': preferred_service,
            'scan_timestamp': asyncio.get_event_loop().time()
        }
    
    def detect_os_type(self, host_data: Dict) -> str:
        """Detect OS type based on open ports and OS fingerprinting"""
        # Check OS fingerprinting first
        if host_data.get('os_fingerprint'):
            for os_match in host_data['os_fingerprint']:
                os_name = os_match.get('name', '').lower()
                if 'windows' in os_name:
                    return 'windows'
                elif any(linux_dist in os_name for linux_dist in ['linux', 'ubuntu', 'centos', 'redhat', 'debian']):
                    return 'linux'
                elif 'unix' in os_name or 'bsd' in os_name:
                    return 'unix'
        
        # Fallback to port-based detection
        ports = host_data.get('ports', {})
        
        # Windows indicators
        if any(port in ports for port in [3389, 5985, 5986, 445, 135]):
            return 'windows'
        
        # Linux/Unix indicators  
        if 22 in ports:  # SSH is common on Linux/Unix
            return 'linux'
        
        return 'unknown'
    
    def detect_os_version(self, host_data: Dict) -> Optional[str]:
        """Detect OS version from fingerprinting"""
        if host_data.get('os_fingerprint'):
            return host_data['os_fingerprint'][0].get('name')
        return None
    
    def detect_services(self, host_data: Dict) -> Tuple[List[Dict], Optional[Dict]]:
        """Detect available services and determine preferred service"""
        services = []
        ports = host_data.get('ports', {})
        
        for port, port_info in ports.items():
            if port_info.get('state') == 'open':
                service_name = port_info.get('name', 'unknown')
                service_version = port_info.get('version', '')
                
                service = {
                    'port': port,
                    'protocol': 'tcp',
                    'service': service_name,
                    'version': service_version,
                    'state': 'open'
                }
                services.append(service)
        
        # Select preferred service
        preferred_service = self.select_preferred_service(services)
        
        return services, preferred_service
    
    def select_preferred_service(self, services: List[Dict]) -> Optional[Dict]:
        """Select preferred service based on security and availability"""
        if not services:
            return None
        
        # Priority order: SSH (22), WinRM HTTPS (5986), WinRM HTTP (5985), RDP (3389)
        priority_ports = [22, 5986, 5985, 3389]
        
        for priority_port in priority_ports:
            for service in services:
                if service['port'] == priority_port:
                    return service
        
        # If no priority service found, return first available
        return services[0]