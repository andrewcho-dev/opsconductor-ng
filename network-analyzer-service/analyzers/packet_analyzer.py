"""
Packet Analyzer Module
Handles packet capture and basic analysis using tcpdump, tshark, and scapy
"""

import asyncio
import json
import logging
import os
import subprocess
import tempfile
import time
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime

import structlog
import scapy.all as scapy
import pyshark
import dpkt
from scapy.layers.inet import IP, TCP, UDP, ICMP
from scapy.layers.http import HTTP

from models.analysis_models import PacketInfo, TrafficStatistics, CaptureStatus

logger = structlog.get_logger(__name__)

class PacketAnalyzer:
    """Advanced packet analyzer with multiple capture backends"""
    
    def __init__(self):
        self.active_captures: Dict[str, Dict] = {}
        self.capture_results: Dict[str, Dict] = {}
        self.temp_dir = tempfile.mkdtemp(prefix="netanalyzer_")
        
    def is_ready(self) -> bool:
        """Check if analyzer is ready"""
        try:
            # Check if required tools are available
            subprocess.run(["tcpdump", "--version"], 
                         capture_output=True, check=True, timeout=5)
            subprocess.run(["tshark", "--version"], 
                         capture_output=True, check=True, timeout=5)
            return True
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
            logger.warning("Required packet capture tools not available")
            return False
    
    async def start_capture(
        self,
        interface: str,
        filter_expression: Optional[str] = None,
        duration: Optional[int] = None,
        packet_count: Optional[int] = None,
        target_id: Optional[int] = None
    ) -> str:
        """Start packet capture session"""
        session_id = str(uuid.uuid4())
        
        try:
            # Prepare capture configuration
            capture_config = {
                "session_id": session_id,
                "interface": interface,
                "filter_expression": filter_expression,
                "duration": duration,
                "packet_count": packet_count,
                "target_id": target_id,
                "status": CaptureStatus.STARTING,
                "started_at": time.time(),
                "capture_file": os.path.join(self.temp_dir, f"capture_{session_id}.pcap"),
                "packets": [],
                "statistics": None
            }
            
            self.active_captures[session_id] = capture_config
            
            # Start capture in background
            asyncio.create_task(self._execute_capture(session_id))
            
            logger.info("Started packet capture session", 
                       session_id=session_id, 
                       interface=interface)
            
            return session_id
            
        except Exception as e:
            logger.error("Failed to start packet capture", 
                        session_id=session_id, error=str(e))
            if session_id in self.active_captures:
                self.active_captures[session_id]["status"] = CaptureStatus.FAILED
            raise
    
    async def _execute_capture(self, session_id: str):
        """Execute packet capture using tcpdump"""
        config = self.active_captures[session_id]
        
        try:
            config["status"] = CaptureStatus.RUNNING
            
            # Build tcpdump command
            cmd = ["tcpdump", "-i", config["interface"], "-w", config["capture_file"]]
            
            if config["filter_expression"]:
                cmd.append(config["filter_expression"])
            
            if config["packet_count"]:
                cmd.extend(["-c", str(config["packet_count"])])
            
            # Start tcpdump process
            logger.info("Starting tcpdump", command=" ".join(cmd))
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            config["process"] = process
            
            # Wait for completion or timeout
            if config["duration"]:
                try:
                    await asyncio.wait_for(process.wait(), timeout=config["duration"])
                except asyncio.TimeoutError:
                    process.terminate()
                    await process.wait()
            else:
                await process.wait()
            
            config["status"] = CaptureStatus.COMPLETED
            
            # Process captured packets
            await self._process_capture_file(session_id)
            
            logger.info("Packet capture completed", 
                       session_id=session_id,
                       packet_count=len(config["packets"]))
            
        except Exception as e:
            logger.error("Packet capture failed", 
                        session_id=session_id, error=str(e))
            config["status"] = CaptureStatus.FAILED
            config["error"] = str(e)
    
    async def _process_capture_file(self, session_id: str):
        """Process captured packets from pcap file"""
        config = self.active_captures[session_id]
        capture_file = config["capture_file"]
        
        try:
            if not os.path.exists(capture_file):
                logger.warning("Capture file not found", 
                             session_id=session_id, 
                             file=capture_file)
                return
            
            # Use scapy to read and analyze packets
            packets = scapy.rdpcap(capture_file)
            
            processed_packets = []
            protocol_stats = {}
            port_stats = {}
            total_bytes = 0
            
            for i, packet in enumerate(packets):
                if i >= 10000:  # Limit processing for performance
                    break
                
                packet_info = self._extract_packet_info(packet)
                processed_packets.append(packet_info)
                
                # Update statistics
                protocol = packet_info.protocol
                protocol_stats[protocol] = protocol_stats.get(protocol, 0) + 1
                
                if packet_info.destination_port:
                    port = str(packet_info.destination_port)
                    port_stats[port] = port_stats.get(port, 0) + 1
                
                total_bytes += packet_info.size
            
            # Calculate statistics
            duration = time.time() - config["started_at"]
            packet_count = len(processed_packets)
            
            statistics = TrafficStatistics(
                total_packets=packet_count,
                total_bytes=total_bytes,
                packets_per_second=packet_count / duration if duration > 0 else 0,
                bytes_per_second=total_bytes / duration if duration > 0 else 0,
                protocol_distribution=protocol_stats,
                top_talkers=self._calculate_top_talkers(processed_packets),
                port_distribution=port_stats
            )
            
            config["packets"] = processed_packets
            config["statistics"] = statistics
            
            # Store results for later retrieval
            self.capture_results[session_id] = {
                "status": config["status"],
                "packet_count": packet_count,
                "packets": processed_packets,
                "statistics": statistics,
                "completed_at": time.time()
            }
            
        except Exception as e:
            logger.error("Failed to process capture file", 
                        session_id=session_id, error=str(e))
            config["status"] = CaptureStatus.FAILED
            config["error"] = str(e)
    
    def _extract_packet_info(self, packet) -> PacketInfo:
        """Extract information from a scapy packet"""
        try:
            # Basic packet info
            timestamp = float(packet.time)
            size = len(packet)
            
            # Default values
            src_ip = "unknown"
            dst_ip = "unknown"
            src_port = None
            dst_port = None
            protocol = "unknown"
            flags = []
            payload_preview = None
            
            # Extract IP layer info
            if packet.haslayer(IP):
                ip_layer = packet[IP]
                src_ip = ip_layer.src
                dst_ip = ip_layer.dst
                protocol = ip_layer.proto
                
                # Convert protocol number to name
                protocol_names = {1: "ICMP", 6: "TCP", 17: "UDP"}
                protocol = protocol_names.get(protocol, str(protocol))
            
            # Extract transport layer info
            if packet.haslayer(TCP):
                tcp_layer = packet[TCP]
                src_port = tcp_layer.sport
                dst_port = tcp_layer.dport
                protocol = "TCP"
                
                # Extract TCP flags
                if tcp_layer.flags:
                    flag_names = {
                        0x01: "FIN", 0x02: "SYN", 0x04: "RST", 0x08: "PSH",
                        0x10: "ACK", 0x20: "URG", 0x40: "ECE", 0x80: "CWR"
                    }
                    flags = [name for flag, name in flag_names.items() 
                            if tcp_layer.flags & flag]
                
            elif packet.haslayer(UDP):
                udp_layer = packet[UDP]
                src_port = udp_layer.sport
                dst_port = udp_layer.dport
                protocol = "UDP"
            
            elif packet.haslayer(ICMP):
                protocol = "ICMP"
            
            # Extract application layer info
            if packet.haslayer(HTTP):
                protocol = "HTTP"
                # Get HTTP method and URI if available
                try:
                    http_layer = packet[HTTP]
                    if hasattr(http_layer, 'Method'):
                        payload_preview = f"{http_layer.Method.decode()} {http_layer.Path.decode()}"
                except:
                    pass
            
            # Extract payload preview (first 50 bytes)
            if not payload_preview and packet.payload:
                try:
                    raw_payload = bytes(packet.payload)
                    if raw_payload:
                        payload_preview = raw_payload[:50].hex()
                except:
                    pass
            
            return PacketInfo(
                timestamp=timestamp,
                source_ip=src_ip,
                destination_ip=dst_ip,
                source_port=src_port,
                destination_port=dst_port,
                protocol=protocol,
                size=size,
                flags=flags if flags else None,
                payload_preview=payload_preview
            )
            
        except Exception as e:
            logger.warning("Failed to extract packet info", error=str(e))
            return PacketInfo(
                timestamp=time.time(),
                source_ip="error",
                destination_ip="error",
                protocol="unknown",
                size=0
            )
    
    def _calculate_top_talkers(self, packets: List[PacketInfo]) -> List[Dict[str, Any]]:
        """Calculate top talking hosts"""
        host_stats = {}
        
        for packet in packets:
            src = packet.source_ip
            dst = packet.destination_ip
            
            if src not in host_stats:
                host_stats[src] = {"sent_bytes": 0, "sent_packets": 0, "received_bytes": 0, "received_packets": 0}
            if dst not in host_stats:
                host_stats[dst] = {"sent_bytes": 0, "sent_packets": 0, "received_bytes": 0, "received_packets": 0}
            
            host_stats[src]["sent_bytes"] += packet.size
            host_stats[src]["sent_packets"] += 1
            host_stats[dst]["received_bytes"] += packet.size
            host_stats[dst]["received_packets"] += 1
        
        # Sort by total bytes and return top 10
        top_talkers = []
        for host, stats in host_stats.items():
            total_bytes = stats["sent_bytes"] + stats["received_bytes"]
            total_packets = stats["sent_packets"] + stats["received_packets"]
            
            top_talkers.append({
                "host": host,
                "total_bytes": total_bytes,
                "total_packets": total_packets,
                "sent_bytes": stats["sent_bytes"],
                "received_bytes": stats["received_bytes"]
            })
        
        return sorted(top_talkers, key=lambda x: x["total_bytes"], reverse=True)[:10]
    
    async def stop_capture(self, session_id: str):
        """Stop an active packet capture"""
        if session_id not in self.active_captures:
            raise ValueError(f"Session {session_id} not found")
        
        config = self.active_captures[session_id]
        
        try:
            if "process" in config and config["process"]:
                config["process"].terminate()
                await config["process"].wait()
            
            config["status"] = CaptureStatus.COMPLETED
            
            # Process any remaining data
            if config["status"] != CaptureStatus.FAILED:
                await self._process_capture_file(session_id)
            
            logger.info("Stopped packet capture", session_id=session_id)
            
        except Exception as e:
            logger.error("Failed to stop packet capture", 
                        session_id=session_id, error=str(e))
            config["status"] = CaptureStatus.FAILED
            raise
    
    async def get_capture_results(self, session_id: str) -> Dict[str, Any]:
        """Get results from a capture session"""
        if session_id in self.capture_results:
            return self.capture_results[session_id]
        
        if session_id in self.active_captures:
            config = self.active_captures[session_id]
            return {
                "status": config["status"],
                "packet_count": len(config.get("packets", [])),
                "packets": config.get("packets", []),
                "statistics": config.get("statistics"),
                "error": config.get("error")
            }
        
        raise ValueError(f"Session {session_id} not found")
    
    async def get_session_update(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get real-time update for a session"""
        if session_id not in self.active_captures:
            return None
        
        config = self.active_captures[session_id]
        
        return {
            "session_id": session_id,
            "status": config["status"],
            "packet_count": len(config.get("packets", [])),
            "duration": time.time() - config["started_at"],
            "error": config.get("error")
        }
    
    def cleanup_session(self, session_id: str):
        """Clean up session resources"""
        try:
            if session_id in self.active_captures:
                config = self.active_captures[session_id]
                
                # Remove capture file
                if "capture_file" in config and os.path.exists(config["capture_file"]):
                    os.remove(config["capture_file"])
                
                del self.active_captures[session_id]
            
            if session_id in self.capture_results:
                del self.capture_results[session_id]
                
        except Exception as e:
            logger.warning("Failed to cleanup session", 
                          session_id=session_id, error=str(e))