"""
Protocol Analyzer Module
Provides detailed analysis of specific network protocols
"""

import asyncio
import json
import logging
import subprocess
import tempfile
import time
from typing import Dict, List, Optional, Any
from datetime import datetime

import structlog
import scapy.all as scapy
from scapy.layers.inet import IP, TCP, UDP, ICMP
from scapy.layers.http import HTTP
from scapy.layers.dns import DNS, DNSQR, DNSRR

from models.analysis_models import NetworkProtocol

logger = structlog.get_logger(__name__)

class ProtocolAnalyzer:
    """Advanced protocol-specific network analysis"""
    
    def __init__(self):
        self.analysis_cache = {}
        self.protocol_handlers = {
            NetworkProtocol.TCP: self._analyze_tcp,
            NetworkProtocol.UDP: self._analyze_udp,
            NetworkProtocol.HTTP: self._analyze_http,
            NetworkProtocol.HTTPS: self._analyze_https,
            NetworkProtocol.DNS: self._analyze_dns,
            NetworkProtocol.ICMP: self._analyze_icmp,
            NetworkProtocol.SSH: self._analyze_ssh,
            NetworkProtocol.FTP: self._analyze_ftp,
            NetworkProtocol.SMTP: self._analyze_smtp,
            NetworkProtocol.SNMP: self._analyze_snmp
        }
    
    async def analyze_protocol(
        self,
        protocol: NetworkProtocol,
        data_source: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Analyze specific network protocol"""
        try:
            logger.info("Starting protocol analysis", 
                       protocol=protocol, 
                       data_source=data_source)
            
            # Get protocol handler
            handler = self.protocol_handlers.get(protocol)
            if not handler:
                raise ValueError(f"Unsupported protocol: {protocol}")
            
            # Capture or load data
            packets = await self._get_protocol_data(protocol, data_source, filters)
            
            if not packets:
                return {
                    "results": {"message": "No packets found for analysis"},
                    "statistics": {},
                    "recommendations": [],
                    "timestamp": datetime.now()
                }
            
            # Analyze protocol-specific data
            analysis_results = await handler(packets, filters or {})
            
            # Generate statistics
            statistics = self._generate_protocol_statistics(packets, protocol)
            
            # Generate recommendations
            recommendations = self._generate_protocol_recommendations(
                protocol, analysis_results, statistics
            )
            
            result = {
                "results": analysis_results,
                "statistics": statistics,
                "recommendations": recommendations,
                "timestamp": datetime.now()
            }
            
            logger.info("Completed protocol analysis", 
                       protocol=protocol, 
                       packet_count=len(packets))
            
            return result
            
        except Exception as e:
            logger.error("Protocol analysis failed", 
                        protocol=protocol, error=str(e))
            raise
    
    async def _get_protocol_data(
        self,
        protocol: NetworkProtocol,
        data_source: str,
        filters: Optional[Dict[str, Any]]
    ) -> List[Any]:
        """Get protocol-specific packet data"""
        try:
            # Build capture filter based on protocol
            capture_filter = self._build_capture_filter(protocol, filters)
            
            # If data_source is a file, read it
            if data_source.endswith('.pcap') or data_source.endswith('.cap'):
                packets = scapy.rdpcap(data_source)
            else:
                # Assume it's an interface - capture live data
                packets = await self._capture_live_data(data_source, capture_filter, 100)
            
            # Filter packets for the specific protocol
            filtered_packets = self._filter_packets_by_protocol(packets, protocol)
            
            return filtered_packets
            
        except Exception as e:
            logger.error("Failed to get protocol data", 
                        protocol=protocol, error=str(e))
            return []
    
    def _build_capture_filter(
        self,
        protocol: NetworkProtocol,
        filters: Optional[Dict[str, Any]]
    ) -> str:
        """Build BPF capture filter for protocol"""
        base_filters = {
            NetworkProtocol.TCP: "tcp",
            NetworkProtocol.UDP: "udp",
            NetworkProtocol.HTTP: "tcp port 80",
            NetworkProtocol.HTTPS: "tcp port 443",
            NetworkProtocol.DNS: "udp port 53 or tcp port 53",
            NetworkProtocol.ICMP: "icmp",
            NetworkProtocol.SSH: "tcp port 22",
            NetworkProtocol.FTP: "tcp port 21 or tcp port 20",
            NetworkProtocol.SMTP: "tcp port 25 or tcp port 587",
            NetworkProtocol.SNMP: "udp port 161 or udp port 162"
        }
        
        base_filter = base_filters.get(protocol, "")
        
        # Add additional filters
        if filters:
            if "port" in filters:
                base_filter += f" and port {filters['port']}"
            if "host" in filters:
                base_filter += f" and host {filters['host']}"
        
        return base_filter
    
    async def _capture_live_data(
        self,
        interface: str,
        capture_filter: str,
        packet_count: int
    ) -> List[Any]:
        """Capture live data from interface"""
        try:
            # Use scapy to capture packets
            packets = scapy.sniff(
                iface=interface,
                filter=capture_filter,
                count=packet_count,
                timeout=30
            )
            return list(packets)
            
        except Exception as e:
            logger.error("Live capture failed", 
                        interface=interface, error=str(e))
            return []
    
    def _filter_packets_by_protocol(
        self,
        packets: List[Any],
        protocol: NetworkProtocol
    ) -> List[Any]:
        """Filter packets by specific protocol"""
        filtered = []
        
        for packet in packets:
            if self._packet_matches_protocol(packet, protocol):
                filtered.append(packet)
        
        return filtered
    
    def _packet_matches_protocol(self, packet: Any, protocol: NetworkProtocol) -> bool:
        """Check if packet matches the specified protocol"""
        try:
            if protocol == NetworkProtocol.TCP:
                return packet.haslayer(TCP)
            elif protocol == NetworkProtocol.UDP:
                return packet.haslayer(UDP)
            elif protocol == NetworkProtocol.HTTP:
                return packet.haslayer(HTTP) or (packet.haslayer(TCP) and 
                                               (packet[TCP].dport == 80 or packet[TCP].sport == 80))
            elif protocol == NetworkProtocol.HTTPS:
                return packet.haslayer(TCP) and (packet[TCP].dport == 443 or packet[TCP].sport == 443)
            elif protocol == NetworkProtocol.DNS:
                return packet.haslayer(DNS)
            elif protocol == NetworkProtocol.ICMP:
                return packet.haslayer(ICMP)
            elif protocol == NetworkProtocol.SSH:
                return packet.haslayer(TCP) and (packet[TCP].dport == 22 or packet[TCP].sport == 22)
            elif protocol == NetworkProtocol.FTP:
                return packet.haslayer(TCP) and (packet[TCP].dport in [20, 21] or packet[TCP].sport in [20, 21])
            elif protocol == NetworkProtocol.SMTP:
                return packet.haslayer(TCP) and (packet[TCP].dport in [25, 587] or packet[TCP].sport in [25, 587])
            elif protocol == NetworkProtocol.SNMP:
                return packet.haslayer(UDP) and (packet[UDP].dport in [161, 162] or packet[UDP].sport in [161, 162])
            
        except Exception:
            pass
        
        return False
    
    async def _analyze_tcp(self, packets: List[Any], filters: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze TCP protocol"""
        results = {
            "connection_analysis": {},
            "performance_metrics": {},
            "issues_detected": []
        }
        
        try:
            connections = {}
            total_retransmissions = 0
            total_out_of_order = 0
            
            for packet in packets:
                if not packet.haslayer(TCP):
                    continue
                
                tcp_layer = packet[TCP]
                ip_layer = packet[IP] if packet.haslayer(IP) else None
                
                if not ip_layer:
                    continue
                
                # Track connections
                conn_key = f"{ip_layer.src}:{tcp_layer.sport}-{ip_layer.dst}:{tcp_layer.dport}"
                
                if conn_key not in connections:
                    connections[conn_key] = {
                        "packets": 0,
                        "bytes": 0,
                        "flags_seen": set(),
                        "seq_numbers": [],
                        "timestamps": []
                    }
                
                conn = connections[conn_key]
                conn["packets"] += 1
                conn["bytes"] += len(packet)
                conn["flags_seen"].add(tcp_layer.flags)
                conn["seq_numbers"].append(tcp_layer.seq)
                conn["timestamps"].append(float(packet.time))
                
                # Detect retransmissions (simplified)
                if tcp_layer.seq in conn["seq_numbers"][:-1]:
                    total_retransmissions += 1
            
            # Analyze connections
            connection_stats = []
            for conn_key, conn_data in connections.items():
                # Calculate connection duration
                if len(conn_data["timestamps"]) > 1:
                    duration = max(conn_data["timestamps"]) - min(conn_data["timestamps"])
                else:
                    duration = 0
                
                # Determine connection state
                flags = conn_data["flags_seen"]
                if 2 in flags and 16 in flags:  # SYN and ACK
                    state = "established"
                elif 1 in flags:  # FIN
                    state = "closed"
                elif 4 in flags:  # RST
                    state = "reset"
                else:
                    state = "unknown"
                
                connection_stats.append({
                    "connection": conn_key,
                    "packets": conn_data["packets"],
                    "bytes": conn_data["bytes"],
                    "duration": duration,
                    "state": state
                })
            
            results["connection_analysis"] = {
                "total_connections": len(connections),
                "connection_details": connection_stats[:10],  # Top 10
                "total_retransmissions": total_retransmissions
            }
            
            # Performance metrics
            if packets:
                total_bytes = sum(len(p) for p in packets)
                duration = max(float(p.time) for p in packets) - min(float(p.time) for p in packets)
                throughput = total_bytes / duration if duration > 0 else 0
                
                results["performance_metrics"] = {
                    "total_packets": len(packets),
                    "total_bytes": total_bytes,
                    "duration": duration,
                    "throughput_bps": throughput,
                    "retransmission_rate": total_retransmissions / len(packets) if packets else 0
                }
            
            # Detect issues
            if total_retransmissions > len(packets) * 0.05:  # > 5% retransmission rate
                results["issues_detected"].append("High retransmission rate detected")
            
            if len([c for c in connection_stats if c["state"] == "reset"]) > len(connection_stats) * 0.1:
                results["issues_detected"].append("High connection reset rate detected")
            
        except Exception as e:
            logger.error("TCP analysis failed", error=str(e))
            results["error"] = str(e)
        
        return results
    
    async def _analyze_udp(self, packets: List[Any], filters: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze UDP protocol"""
        results = {
            "traffic_analysis": {},
            "port_analysis": {},
            "issues_detected": []
        }
        
        try:
            port_stats = {}
            total_bytes = 0
            
            for packet in packets:
                if not packet.haslayer(UDP):
                    continue
                
                udp_layer = packet[UDP]
                total_bytes += len(packet)
                
                # Track port usage
                for port in [udp_layer.sport, udp_layer.dport]:
                    if port not in port_stats:
                        port_stats[port] = {"packets": 0, "bytes": 0}
                    port_stats[port]["packets"] += 1
                    port_stats[port]["bytes"] += len(packet)
            
            # Sort ports by traffic
            top_ports = sorted(port_stats.items(), 
                             key=lambda x: x[1]["bytes"], 
                             reverse=True)[:10]
            
            results["traffic_analysis"] = {
                "total_packets": len(packets),
                "total_bytes": total_bytes,
                "unique_ports": len(port_stats)
            }
            
            results["port_analysis"] = {
                "top_ports": [{"port": port, **stats} for port, stats in top_ports]
            }
            
            # Check for potential issues
            if len(port_stats) > 1000:
                results["issues_detected"].append("Unusually high number of unique ports")
            
        except Exception as e:
            logger.error("UDP analysis failed", error=str(e))
            results["error"] = str(e)
        
        return results
    
    async def _analyze_http(self, packets: List[Any], filters: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze HTTP protocol"""
        results = {
            "request_analysis": {},
            "response_analysis": {},
            "performance_metrics": {},
            "issues_detected": []
        }
        
        try:
            requests = []
            responses = []
            methods = {}
            status_codes = {}
            
            for packet in packets:
                if packet.haslayer(HTTP):
                    http_layer = packet[HTTP]
                    
                    # Check if it's a request or response
                    if hasattr(http_layer, 'Method'):
                        # HTTP Request
                        method = http_layer.Method.decode() if isinstance(http_layer.Method, bytes) else str(http_layer.Method)
                        path = http_layer.Path.decode() if hasattr(http_layer, 'Path') and isinstance(http_layer.Path, bytes) else "/"
                        
                        requests.append({
                            "method": method,
                            "path": path,
                            "timestamp": float(packet.time)
                        })
                        
                        methods[method] = methods.get(method, 0) + 1
                    
                    elif hasattr(http_layer, 'Status_Code'):
                        # HTTP Response
                        status_code = str(http_layer.Status_Code)
                        responses.append({
                            "status_code": status_code,
                            "timestamp": float(packet.time)
                        })
                        
                        status_codes[status_code] = status_codes.get(status_code, 0) + 1
            
            results["request_analysis"] = {
                "total_requests": len(requests),
                "methods": methods,
                "top_paths": self._get_top_paths(requests)
            }
            
            results["response_analysis"] = {
                "total_responses": len(responses),
                "status_codes": status_codes
            }
            
            # Performance analysis
            if requests and responses:
                avg_response_time = self._calculate_avg_response_time(requests, responses)
                results["performance_metrics"] = {
                    "average_response_time": avg_response_time
                }
            
            # Detect issues
            error_responses = sum(count for code, count in status_codes.items() 
                                if code.startswith(('4', '5')))
            if error_responses > len(responses) * 0.1:  # > 10% error rate
                results["issues_detected"].append("High HTTP error rate detected")
            
        except Exception as e:
            logger.error("HTTP analysis failed", error=str(e))
            results["error"] = str(e)
        
        return results
    
    async def _analyze_https(self, packets: List[Any], filters: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze HTTPS protocol"""
        results = {
            "tls_analysis": {},
            "connection_analysis": {},
            "issues_detected": []
        }
        
        try:
            # HTTPS analysis is limited without decryption
            # Focus on connection patterns and TLS handshake analysis
            
            connections = {}
            handshakes = 0
            
            for packet in packets:
                if not packet.haslayer(TCP):
                    continue
                
                tcp_layer = packet[TCP]
                ip_layer = packet[IP] if packet.haslayer(IP) else None
                
                if not ip_layer or (tcp_layer.dport != 443 and tcp_layer.sport != 443):
                    continue
                
                conn_key = f"{ip_layer.src}:{tcp_layer.sport}-{ip_layer.dst}:{tcp_layer.dport}"
                
                if conn_key not in connections:
                    connections[conn_key] = {"packets": 0, "bytes": 0}
                
                connections[conn_key]["packets"] += 1
                connections[conn_key]["bytes"] += len(packet)
                
                # Detect TLS handshake (simplified)
                if len(packet) > 100 and tcp_layer.flags == 24:  # PSH+ACK
                    handshakes += 1
            
            results["connection_analysis"] = {
                "total_connections": len(connections),
                "estimated_handshakes": handshakes
            }
            
            results["tls_analysis"] = {
                "note": "Detailed TLS analysis requires decryption capabilities"
            }
            
        except Exception as e:
            logger.error("HTTPS analysis failed", error=str(e))
            results["error"] = str(e)
        
        return results
    
    async def _analyze_dns(self, packets: List[Any], filters: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze DNS protocol"""
        results = {
            "query_analysis": {},
            "response_analysis": {},
            "performance_metrics": {},
            "issues_detected": []
        }
        
        try:
            queries = []
            responses = []
            query_types = {}
            response_codes = {}
            
            for packet in packets:
                if not packet.haslayer(DNS):
                    continue
                
                dns_layer = packet[DNS]
                
                if dns_layer.qr == 0:  # Query
                    if dns_layer.qdcount > 0:
                        query_name = dns_layer.qd.qname.decode() if isinstance(dns_layer.qd.qname, bytes) else str(dns_layer.qd.qname)
                        query_type = dns_layer.qd.qtype
                        
                        queries.append({
                            "name": query_name,
                            "type": query_type,
                            "timestamp": float(packet.time),
                            "id": dns_layer.id
                        })
                        
                        query_types[query_type] = query_types.get(query_type, 0) + 1
                
                else:  # Response
                    responses.append({
                        "rcode": dns_layer.rcode,
                        "timestamp": float(packet.time),
                        "id": dns_layer.id,
                        "ancount": dns_layer.ancount
                    })
                    
                    response_codes[dns_layer.rcode] = response_codes.get(dns_layer.rcode, 0) + 1
            
            results["query_analysis"] = {
                "total_queries": len(queries),
                "query_types": query_types,
                "top_domains": self._get_top_domains(queries)
            }
            
            results["response_analysis"] = {
                "total_responses": len(responses),
                "response_codes": response_codes
            }
            
            # Performance analysis
            if queries and responses:
                avg_response_time = self._calculate_dns_response_time(queries, responses)
                results["performance_metrics"] = {
                    "average_response_time": avg_response_time
                }
            
            # Detect issues
            failed_queries = response_codes.get(3, 0)  # NXDOMAIN
            if failed_queries > len(responses) * 0.1:  # > 10% failure rate
                results["issues_detected"].append("High DNS failure rate detected")
            
        except Exception as e:
            logger.error("DNS analysis failed", error=str(e))
            results["error"] = str(e)
        
        return results
    
    async def _analyze_icmp(self, packets: List[Any], filters: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze ICMP protocol"""
        results = {
            "message_analysis": {},
            "issues_detected": []
        }
        
        try:
            message_types = {}
            
            for packet in packets:
                if not packet.haslayer(ICMP):
                    continue
                
                icmp_layer = packet[ICMP]
                msg_type = icmp_layer.type
                
                message_types[msg_type] = message_types.get(msg_type, 0) + 1
            
            results["message_analysis"] = {
                "total_packets": len(packets),
                "message_types": message_types
            }
            
            # Detect potential issues
            if message_types.get(3, 0) > len(packets) * 0.5:  # > 50% unreachable messages
                results["issues_detected"].append("High rate of destination unreachable messages")
            
        except Exception as e:
            logger.error("ICMP analysis failed", error=str(e))
            results["error"] = str(e)
        
        return results
    
    # Placeholder methods for other protocols
    async def _analyze_ssh(self, packets: List[Any], filters: Dict[str, Any]) -> Dict[str, Any]:
        return {"note": "SSH analysis focuses on connection patterns (encrypted payload)"}
    
    async def _analyze_ftp(self, packets: List[Any], filters: Dict[str, Any]) -> Dict[str, Any]:
        return {"note": "FTP analysis implementation needed"}
    
    async def _analyze_smtp(self, packets: List[Any], filters: Dict[str, Any]) -> Dict[str, Any]:
        return {"note": "SMTP analysis implementation needed"}
    
    async def _analyze_snmp(self, packets: List[Any], filters: Dict[str, Any]) -> Dict[str, Any]:
        return {"note": "SNMP analysis implementation needed"}
    
    def _generate_protocol_statistics(self, packets: List[Any], protocol: NetworkProtocol) -> Dict[str, Any]:
        """Generate general statistics for protocol"""
        if not packets:
            return {}
        
        total_bytes = sum(len(p) for p in packets)
        timestamps = [float(p.time) for p in packets]
        duration = max(timestamps) - min(timestamps) if len(timestamps) > 1 else 0
        
        return {
            "packet_count": len(packets),
            "total_bytes": total_bytes,
            "duration": duration,
            "packets_per_second": len(packets) / duration if duration > 0 else 0,
            "bytes_per_second": total_bytes / duration if duration > 0 else 0,
            "average_packet_size": total_bytes / len(packets) if packets else 0
        }
    
    def _generate_protocol_recommendations(
        self,
        protocol: NetworkProtocol,
        analysis_results: Dict[str, Any],
        statistics: Dict[str, Any]
    ) -> List[str]:
        """Generate protocol-specific recommendations"""
        recommendations = []
        
        # General recommendations based on issues
        if "issues_detected" in analysis_results:
            for issue in analysis_results["issues_detected"]:
                if "retransmission" in issue.lower():
                    recommendations.append("Check network quality and reduce packet loss")
                elif "error rate" in issue.lower():
                    recommendations.append("Investigate application-level errors")
                elif "failure rate" in issue.lower():
                    recommendations.append("Check DNS server configuration and connectivity")
        
        # Protocol-specific recommendations
        if protocol == NetworkProtocol.TCP:
            if statistics.get("packets_per_second", 0) > 1000:
                recommendations.append("Consider connection pooling to reduce overhead")
        
        elif protocol == NetworkProtocol.HTTP:
            if "status_codes" in analysis_results.get("response_analysis", {}):
                status_codes = analysis_results["response_analysis"]["status_codes"]
                if any(code.startswith('5') for code in status_codes):
                    recommendations.append("Investigate server errors (5xx responses)")
        
        elif protocol == NetworkProtocol.DNS:
            if statistics.get("packets_per_second", 0) > 100:
                recommendations.append("Consider DNS caching to reduce query load")
        
        # Add general recommendations if none specific
        if not recommendations:
            recommendations.append("Monitor protocol performance regularly")
            recommendations.append("Consider protocol optimization opportunities")
        
        return recommendations
    
    def _get_top_paths(self, requests: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Get top HTTP paths"""
        path_counts = {}
        for req in requests:
            path = req["path"]
            path_counts[path] = path_counts.get(path, 0) + 1
        
        return [{"path": path, "count": count} 
                for path, count in sorted(path_counts.items(), 
                                        key=lambda x: x[1], 
                                        reverse=True)[:10]]
    
    def _get_top_domains(self, queries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Get top DNS domains"""
        domain_counts = {}
        for query in queries:
            domain = query["name"].rstrip('.')
            domain_counts[domain] = domain_counts.get(domain, 0) + 1
        
        return [{"domain": domain, "count": count} 
                for domain, count in sorted(domain_counts.items(), 
                                          key=lambda x: x[1], 
                                          reverse=True)[:10]]
    
    def _calculate_avg_response_time(
        self,
        requests: List[Dict[str, Any]],
        responses: List[Dict[str, Any]]
    ) -> float:
        """Calculate average HTTP response time"""
        # Simplified calculation - would need request/response matching in production
        if not requests or not responses:
            return 0.0
        
        # Rough estimate based on timestamp differences
        req_times = [r["timestamp"] for r in requests]
        resp_times = [r["timestamp"] for r in responses]
        
        if req_times and resp_times:
            avg_req_time = sum(req_times) / len(req_times)
            avg_resp_time = sum(resp_times) / len(resp_times)
            return abs(avg_resp_time - avg_req_time)
        
        return 0.0
    
    def _calculate_dns_response_time(
        self,
        queries: List[Dict[str, Any]],
        responses: List[Dict[str, Any]]
    ) -> float:
        """Calculate average DNS response time"""
        # Match queries and responses by ID
        response_times = []
        
        for query in queries:
            query_id = query["id"]
            query_time = query["timestamp"]
            
            # Find matching response
            for response in responses:
                if response["id"] == query_id and response["timestamp"] > query_time:
                    response_times.append(response["timestamp"] - query_time)
                    break
        
        return sum(response_times) / len(response_times) if response_times else 0.0