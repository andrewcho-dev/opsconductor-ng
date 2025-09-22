"""
Network Monitor Module
Provides real-time network monitoring and alerting
"""

import asyncio
import json
import logging
import time
import psutil
import subprocess
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

import structlog
from models.analysis_models import NetworkInterface, NetworkAlert, TrafficStatistics

logger = structlog.get_logger(__name__)

class NetworkMonitor:
    """Real-time network monitoring with alerting"""
    
    def __init__(self):
        self.is_monitoring = False
        self.monitoring_task = None
        self.alert_config = {}
        self.current_stats = {}
        self.alerts = []
        self.baseline_metrics = {}
        self.monitoring_interval = 5  # seconds
        
    def is_running(self) -> bool:
        """Check if monitoring is running"""
        return self.is_monitoring
    
    async def start_monitoring(self):
        """Start network monitoring"""
        if self.is_monitoring:
            return
        
        self.is_monitoring = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        
        logger.info("Started network monitoring")
    
    async def stop_monitoring(self):
        """Stop network monitoring"""
        if not self.is_monitoring:
            return
        
        self.is_monitoring = False
        
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Stopped network monitoring")
    
    async def _monitoring_loop(self):
        """Main monitoring loop"""
        try:
            while self.is_monitoring:
                # Collect network metrics
                await self._collect_metrics()
                
                # Check for alerts
                await self._check_alerts()
                
                # Wait for next interval
                await asyncio.sleep(self.monitoring_interval)
                
        except asyncio.CancelledError:
            logger.info("Monitoring loop cancelled")
        except Exception as e:
            logger.error("Monitoring loop error", error=str(e))
    
    async def _collect_metrics(self):
        """Collect current network metrics"""
        try:
            # Get network interfaces
            interfaces = await self._get_network_interfaces()
            
            # Get network connections
            connections = await self._get_network_connections()
            
            # Get traffic statistics
            traffic_stats = await self._calculate_traffic_stats(interfaces)
            
            # Update current stats
            self.current_stats = {
                "interfaces": interfaces,
                "connections": connections,
                "traffic_stats": traffic_stats,
                "timestamp": datetime.now(),
                "active_connections": len(connections)
            }
            
        except Exception as e:
            logger.error("Failed to collect network metrics", error=str(e))
    
    async def _get_network_interfaces(self) -> List[NetworkInterface]:
        """Get network interface information"""
        interfaces = []
        
        try:
            # Get interface statistics
            net_io = psutil.net_io_counters(pernic=True)
            net_if_addrs = psutil.net_if_addrs()
            net_if_stats = psutil.net_if_stats()
            
            for interface_name, io_stats in net_io.items():
                # Skip loopback and virtual interfaces for basic monitoring
                if interface_name.startswith(('lo', 'docker', 'br-')):
                    continue
                
                # Get IP address
                ip_address = None
                mac_address = None
                if interface_name in net_if_addrs:
                    for addr in net_if_addrs[interface_name]:
                        if addr.family == 2:  # AF_INET (IPv4)
                            ip_address = addr.address
                        elif addr.family == 17:  # AF_PACKET (MAC)
                            mac_address = addr.address
                
                # Get interface status
                status = "unknown"
                if interface_name in net_if_stats:
                    status = "up" if net_if_stats[interface_name].isup else "down"
                
                interface = NetworkInterface(
                    name=interface_name,
                    ip_address=ip_address,
                    mac_address=mac_address,
                    status=status,
                    rx_bytes=io_stats.bytes_recv,
                    tx_bytes=io_stats.bytes_sent,
                    rx_packets=io_stats.packets_recv,
                    tx_packets=io_stats.packets_sent,
                    rx_errors=io_stats.errin,
                    tx_errors=io_stats.errout
                )
                
                interfaces.append(interface)
        
        except Exception as e:
            logger.error("Failed to get network interfaces", error=str(e))
        
        return interfaces
    
    async def _get_network_connections(self) -> List[Dict[str, Any]]:
        """Get active network connections"""
        connections = []
        
        try:
            net_connections = psutil.net_connections(kind='inet')
            
            for conn in net_connections:
                if conn.status == 'ESTABLISHED':
                    connection_info = {
                        "local_address": f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else "unknown",
                        "remote_address": f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else "unknown",
                        "status": conn.status,
                        "pid": conn.pid,
                        "family": "IPv4" if conn.family == 2 else "IPv6"
                    }
                    connections.append(connection_info)
        
        except Exception as e:
            logger.error("Failed to get network connections", error=str(e))
        
        return connections
    
    async def _calculate_traffic_stats(self, interfaces: List[NetworkInterface]) -> TrafficStatistics:
        """Calculate traffic statistics"""
        try:
            total_rx_bytes = sum(iface.rx_bytes for iface in interfaces)
            total_tx_bytes = sum(iface.tx_bytes for iface in interfaces)
            total_rx_packets = sum(iface.rx_packets for iface in interfaces)
            total_tx_packets = sum(iface.tx_packets for iface in interfaces)
            
            total_bytes = total_rx_bytes + total_tx_bytes
            total_packets = total_rx_packets + total_tx_packets
            
            # Calculate rates (simplified - would need historical data for accurate rates)
            current_time = time.time()
            if hasattr(self, '_last_stats_time') and hasattr(self, '_last_total_bytes'):
                time_diff = current_time - self._last_stats_time
                bytes_diff = total_bytes - self._last_total_bytes
                packets_diff = total_packets - self._last_total_packets
                
                bytes_per_second = bytes_diff / time_diff if time_diff > 0 else 0
                packets_per_second = packets_diff / time_diff if time_diff > 0 else 0
            else:
                bytes_per_second = 0
                packets_per_second = 0
            
            # Store for next calculation
            self._last_stats_time = current_time
            self._last_total_bytes = total_bytes
            self._last_total_packets = total_packets
            
            # Protocol distribution (simplified)
            protocol_distribution = {
                "TCP": int(total_packets * 0.7),  # Estimated
                "UDP": int(total_packets * 0.2),
                "ICMP": int(total_packets * 0.1)
            }
            
            # Top talkers (simplified)
            top_talkers = [
                {"host": "127.0.0.1", "total_bytes": int(total_bytes * 0.3), "total_packets": int(total_packets * 0.3)},
                {"host": "external", "total_bytes": int(total_bytes * 0.7), "total_packets": int(total_packets * 0.7)}
            ]
            
            # Port distribution (simplified)
            port_distribution = {
                "80": int(total_packets * 0.3),
                "443": int(total_packets * 0.4),
                "22": int(total_packets * 0.1),
                "other": int(total_packets * 0.2)
            }
            
            return TrafficStatistics(
                total_packets=total_packets,
                total_bytes=total_bytes,
                packets_per_second=packets_per_second,
                bytes_per_second=bytes_per_second,
                protocol_distribution=protocol_distribution,
                top_talkers=top_talkers,
                port_distribution=port_distribution
            )
            
        except Exception as e:
            logger.error("Failed to calculate traffic statistics", error=str(e))
            return TrafficStatistics(
                total_packets=0,
                total_bytes=0,
                packets_per_second=0,
                bytes_per_second=0,
                protocol_distribution={},
                top_talkers=[],
                port_distribution={}
            )
    
    async def _check_alerts(self):
        """Check for alert conditions"""
        if not self.alert_config or not self.current_stats:
            return
        
        try:
            current_time = datetime.now()
            new_alerts = []
            
            # Check bandwidth threshold
            if "bandwidth_threshold" in self.alert_config:
                threshold = self.alert_config["bandwidth_threshold"] * 1024 * 1024  # Convert to bytes
                current_bps = self.current_stats["traffic_stats"].bytes_per_second
                
                if current_bps > threshold:
                    alert = NetworkAlert(
                        alert_id=f"bandwidth_{int(time.time())}",
                        alert_type="bandwidth_exceeded",
                        severity="warning",
                        message=f"Bandwidth usage ({current_bps/1024/1024:.2f} Mbps) exceeds threshold ({threshold/1024/1024:.2f} Mbps)",
                        timestamp=current_time,
                        source="network_monitor"
                    )
                    new_alerts.append(alert)
            
            # Check connection count threshold
            if "connection_count_threshold" in self.alert_config:
                threshold = self.alert_config["connection_count_threshold"]
                current_connections = self.current_stats["active_connections"]
                
                if current_connections > threshold:
                    alert = NetworkAlert(
                        alert_id=f"connections_{int(time.time())}",
                        alert_type="connection_count_exceeded",
                        severity="warning",
                        message=f"Active connections ({current_connections}) exceeds threshold ({threshold})",
                        timestamp=current_time,
                        source="network_monitor"
                    )
                    new_alerts.append(alert)
            
            # Check for interface errors
            for interface in self.current_stats["interfaces"]:
                if interface.rx_errors > 0 or interface.tx_errors > 0:
                    alert = NetworkAlert(
                        alert_id=f"interface_errors_{interface.name}_{int(time.time())}",
                        alert_type="interface_errors",
                        severity="error",
                        message=f"Interface {interface.name} has errors (RX: {interface.rx_errors}, TX: {interface.tx_errors})",
                        timestamp=current_time,
                        source=interface.name
                    )
                    new_alerts.append(alert)
            
            # Add new alerts
            self.alerts.extend(new_alerts)
            
            # Clean up old alerts (keep last 100)
            if len(self.alerts) > 100:
                self.alerts = self.alerts[-100:]
            
            if new_alerts:
                logger.info("Generated network alerts", alert_count=len(new_alerts))
            
        except Exception as e:
            logger.error("Failed to check alerts", error=str(e))
    
    async def configure_alerts(self, config: Dict[str, Any]):
        """Configure alert thresholds"""
        self.alert_config = config
        logger.info("Configured network alerts", config=config)
    
    async def get_current_status(self) -> Dict[str, Any]:
        """Get current network monitoring status"""
        if not self.current_stats:
            # Initialize with empty stats
            await self._collect_metrics()
        
        return {
            "interfaces": self.current_stats.get("interfaces", []),
            "traffic_stats": self.current_stats.get("traffic_stats", {}),
            "active_connections": self.current_stats.get("active_connections", 0),
            "alerts": self.alerts[-10:],  # Return last 10 alerts
            "timestamp": self.current_stats.get("timestamp", datetime.now())
        }
    
    async def get_interface_details(self, interface_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific interface"""
        try:
            # Get detailed interface statistics
            result = subprocess.run(
                ["ip", "-s", "link", "show", interface_name],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                return {
                    "interface": interface_name,
                    "details": result.stdout,
                    "timestamp": datetime.now()
                }
        
        except Exception as e:
            logger.error("Failed to get interface details", 
                        interface=interface_name, error=str(e))
        
        return None
    
    async def test_connectivity(self, target: str, port: Optional[int] = None) -> Dict[str, Any]:
        """Test connectivity to a target"""
        try:
            if port:
                # Test TCP connectivity
                result = subprocess.run(
                    ["nc", "-z", "-v", "-w", "5", target, str(port)],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                success = result.returncode == 0
                message = f"TCP connection to {target}:{port} {'successful' if success else 'failed'}"
            else:
                # Test ICMP connectivity
                result = subprocess.run(
                    ["ping", "-c", "3", "-W", "5", target],
                    capture_output=True,
                    text=True,
                    timeout=15
                )
                
                success = result.returncode == 0
                message = f"ICMP ping to {target} {'successful' if success else 'failed'}"
            
            return {
                "target": target,
                "port": port,
                "success": success,
                "message": message,
                "output": result.stdout,
                "error": result.stderr,
                "timestamp": datetime.now()
            }
        
        except Exception as e:
            logger.error("Connectivity test failed", target=target, port=port, error=str(e))
            return {
                "target": target,
                "port": port,
                "success": False,
                "message": f"Connectivity test failed: {str(e)}",
                "timestamp": datetime.now()
            }
    
    async def trace_route(self, target: str) -> Dict[str, Any]:
        """Trace network route to target"""
        try:
            result = subprocess.run(
                ["traceroute", "-n", "-w", "3", target],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            return {
                "target": target,
                "success": result.returncode == 0,
                "route": result.stdout,
                "error": result.stderr,
                "timestamp": datetime.now()
            }
        
        except Exception as e:
            logger.error("Traceroute failed", target=target, error=str(e))
            return {
                "target": target,
                "success": False,
                "error": str(e),
                "timestamp": datetime.now()
            }