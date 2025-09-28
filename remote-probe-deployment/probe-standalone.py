#!/usr/bin/env python3
"""
OpsConductor Network Analytics Remote Probe - Standalone Version
Designed for deployment on remote Windows and Linux systems
"""

import os
import sys
import json
import time
import asyncio
import subprocess
import platform
import signal
import logging
import yaml
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
import requests
import psutil
from dataclasses import dataclass, asdict
import threading

# Configuration
@dataclass
class ProbeConfig:
    central_analyzer_url: str = "http://YOUR_HOST_IP:3006"
    probe_id: str = "remote-probe-001"
    probe_name: str = "Remote Network Probe"
    probe_location: str = "Remote Location"
    api_key: Optional[str] = None
    heartbeat_interval: int = 30
    log_level: str = "INFO"
    log_file: Optional[str] = None
    interfaces: List[str] = None
    
    @classmethod
    def from_file(cls, config_path: str) -> 'ProbeConfig':
        """Load configuration from YAML file"""
        try:
            with open(config_path, 'r') as f:
                data = yaml.safe_load(f)
            
            return cls(
                central_analyzer_url=data.get('central_analyzer', {}).get('url', cls.central_analyzer_url),
                probe_id=data.get('probe', {}).get('id', cls.probe_id),
                probe_name=data.get('probe', {}).get('name', cls.probe_name),
                probe_location=data.get('probe', {}).get('location', cls.probe_location),
                api_key=data.get('central_analyzer', {}).get('api_key'),
                heartbeat_interval=data.get('heartbeat_interval', cls.heartbeat_interval),
                log_level=data.get('logging', {}).get('level', cls.log_level),
                log_file=data.get('logging', {}).get('file'),
                interfaces=data.get('interfaces', [])
            )
        except Exception as e:
            print(f"Error loading config from {config_path}: {e}")
            return cls()

class NetworkProbe:
    def __init__(self, config: ProbeConfig):
        self.config = config
        self.active_captures: Dict[str, Dict] = {}
        self.probe_registered = False
        self.running = True
        self.logger = self._setup_logging()
        
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logger = logging.getLogger('opsconductor-probe')
        logger.setLevel(getattr(logging, self.config.log_level.upper()))
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # File handler if specified
        if self.config.log_file:
            try:
                # Create log directory if it doesn't exist
                log_dir = Path(self.config.log_file).parent
                log_dir.mkdir(parents=True, exist_ok=True)
                
                file_handler = logging.FileHandler(self.config.log_file)
                file_handler.setFormatter(formatter)
                logger.addHandler(file_handler)
            except Exception as e:
                print(f"Warning: Could not setup file logging: {e}")
        
        return logger

    def get_network_interfaces(self) -> List[Dict[str, Any]]:
        """Get available network interfaces with detailed information"""
        interfaces = []
        
        try:
            # Get interface statistics
            net_io = psutil.net_io_counters(pernic=True)
            net_addrs = psutil.net_if_addrs()
            net_stats = psutil.net_if_stats()
            
            # Filter interfaces if specified in config
            interface_filter = self.config.interfaces if self.config.interfaces else None
            
            for interface_name, addrs in net_addrs.items():
                # Skip if interface filter is specified and this interface is not in it
                if interface_filter and interface_name not in interface_filter:
                    continue
                
                # Skip loopback and virtual interfaces for most cases
                if interface_name.startswith(('lo', 'docker', 'veth', 'br-')):
                    continue
                
                interface_info = {
                    "name": interface_name,
                    "addresses": [],
                    "statistics": {},
                    "status": "unknown"
                }
                
                # Get addresses
                for addr in addrs:
                    addr_info = {
                        "family": str(addr.family),
                        "address": addr.address,
                        "netmask": getattr(addr, 'netmask', None),
                        "broadcast": getattr(addr, 'broadcast', None)
                    }
                    interface_info["addresses"].append(addr_info)
                
                # Get statistics
                if interface_name in net_io:
                    io_stats = net_io[interface_name]
                    interface_info["statistics"] = {
                        "bytes_sent": io_stats.bytes_sent,
                        "bytes_recv": io_stats.bytes_recv,
                        "packets_sent": io_stats.packets_sent,
                        "packets_recv": io_stats.packets_recv,
                        "errin": io_stats.errin,
                        "errout": io_stats.errout,
                        "dropin": io_stats.dropin,
                        "dropout": io_stats.dropout
                    }
                
                # Get interface status
                if interface_name in net_stats:
                    stats = net_stats[interface_name]
                    interface_info["status"] = "up" if stats.isup else "down"
                    interface_info["duplex"] = str(stats.duplex)
                    interface_info["speed"] = stats.speed
                    interface_info["mtu"] = stats.mtu
                
                interfaces.append(interface_info)
                
        except Exception as e:
            self.logger.error(f"Error getting network interfaces: {e}")
        
        return interfaces

    def get_probe_capabilities(self) -> List[str]:
        """Get probe capabilities"""
        capabilities = ["packet_capture", "interface_monitoring", "traffic_analysis"]
        
        # Check for tcpdump/windump
        if platform.system() == "Windows":
            # Check for WinPcap/Npcap tools
            try:
                subprocess.run(["windump", "-h"], capture_output=True, check=True)
                capabilities.append("windump")
            except:
                pass
        else:
            # Check for tcpdump on Linux/Unix
            try:
                subprocess.run(["tcpdump", "--version"], capture_output=True, check=True)
                capabilities.append("tcpdump")
            except:
                pass
        
        # Check for nmap
        try:
            subprocess.run(["nmap", "--version"], capture_output=True, check=True)
            capabilities.append("nmap")
        except:
            pass
        
        return capabilities

    def register_with_central_analyzer(self) -> bool:
        """Register this probe with the central analyzer"""
        try:
            probe_info = {
                "probe_id": self.config.probe_id,
                "name": self.config.probe_name,
                "location": self.config.probe_location,
                "capabilities": self.get_probe_capabilities(),
                "interfaces": self.get_network_interfaces(),
                "status": "active",
                "last_heartbeat": datetime.now(timezone.utc).isoformat(),
                "platform": platform.system(),
                "platform_version": platform.release()
            }
            
            headers = {"Content-Type": "application/json"}
            if self.config.api_key:
                headers["Authorization"] = f"Bearer {self.config.api_key}"
            
            response = requests.post(
                f"{self.config.central_analyzer_url}/api/v1/remote/register-probe",
                json=probe_info,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                self.probe_registered = True
                self.logger.info(f"Successfully registered probe {self.config.probe_id} with central analyzer")
                return True
            else:
                self.logger.error(f"Failed to register probe: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error registering with central analyzer: {e}")
            return False

    def send_heartbeat(self) -> bool:
        """Send heartbeat to central analyzer"""
        try:
            heartbeat_data = {
                "probe_id": self.config.probe_id,
                "status": "active",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "active_captures": len(self.active_captures),
                "interfaces": self.get_network_interfaces()
            }
            
            headers = {"Content-Type": "application/json"}
            if self.config.api_key:
                headers["Authorization"] = f"Bearer {self.config.api_key}"
            
            response = requests.post(
                f"{self.config.central_analyzer_url}/api/v1/remote/heartbeat",
                json=heartbeat_data,
                headers=headers,
                timeout=5
            )
            
            return response.status_code == 200
            
        except Exception as e:
            self.logger.error(f"Error sending heartbeat: {e}")
            return False

    def heartbeat_loop(self):
        """Heartbeat loop running in separate thread"""
        while self.running:
            if self.probe_registered:
                success = self.send_heartbeat()
                if not success:
                    self.logger.warning("Heartbeat failed, attempting to re-register")
                    self.probe_registered = False
            else:
                # Try to register
                self.register_with_central_analyzer()
            
            time.sleep(self.config.heartbeat_interval)

    def start_packet_capture(self, session_id: str, interface: str, duration: int, 
                           filter_expression: Optional[str] = None, 
                           packet_count: Optional[int] = None) -> Dict:
        """Start packet capture using appropriate tool for the platform"""
        try:
            capture_file = f"/tmp/capture_{session_id}.pcap"
            if platform.system() == "Windows":
                capture_file = f"C:\\temp\\capture_{session_id}.pcap"
                # Ensure temp directory exists
                os.makedirs("C:\\temp", exist_ok=True)
                
                # Use windump on Windows
                cmd = ["windump", "-i", interface, "-w", capture_file]
            else:
                # Use tcpdump on Linux/Unix
                cmd = ["tcpdump", "-i", interface, "-w", capture_file]
            
            if filter_expression:
                cmd.append(filter_expression)
            
            if packet_count:
                cmd.extend(["-c", str(packet_count)])
            
            # Start capture process
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            capture_info = {
                "session_id": session_id,
                "interface": interface,
                "process": process,
                "start_time": datetime.now(timezone.utc),
                "duration": duration,
                "filter": filter_expression,
                "packet_count": packet_count,
                "status": "running",
                "capture_file": capture_file
            }
            
            self.active_captures[session_id] = capture_info
            
            # Schedule capture stop
            timer = threading.Timer(duration, self.stop_capture, args=[session_id])
            timer.start()
            capture_info["timer"] = timer
            
            self.logger.info(f"Started packet capture session {session_id} on interface {interface}")
            
            return {
                "session_id": session_id,
                "status": "started",
                "message": f"Packet capture started on interface {interface}"
            }
            
        except Exception as e:
            self.logger.error(f"Error starting packet capture: {e}")
            raise

    def stop_capture(self, session_id: str):
        """Stop packet capture"""
        if session_id not in self.active_captures:
            return
        
        capture_info = self.active_captures[session_id]
        
        try:
            if capture_info["status"] == "running":
                capture_info["process"].terminate()
                capture_info["status"] = "completed"
                capture_info["end_time"] = datetime.now(timezone.utc)
                
                # Cancel timer if it exists
                if "timer" in capture_info:
                    capture_info["timer"].cancel()
                
                # Send results to central analyzer
                self.send_capture_results(session_id)
                
                self.logger.info(f"Stopped packet capture session {session_id}")
                
        except Exception as e:
            self.logger.error(f"Error stopping capture {session_id}: {e}")

    def send_capture_results(self, session_id: str):
        """Send capture results to central analyzer"""
        try:
            if session_id not in self.active_captures:
                return
            
            capture_info = self.active_captures[session_id]
            pcap_file = capture_info["capture_file"]
            
            # Get capture statistics
            stats = {
                "session_id": session_id,
                "probe_id": self.config.probe_id,
                "interface": capture_info["interface"],
                "start_time": capture_info["start_time"].isoformat(),
                "end_time": capture_info.get("end_time", datetime.now(timezone.utc)).isoformat(),
                "status": capture_info["status"],
                "packets_captured": 0,
                "bytes_captured": 0
            }
            
            # Try to get packet count and file size
            try:
                if os.path.exists(pcap_file):
                    stats["bytes_captured"] = os.path.getsize(pcap_file)
                    
                    # Try to count packets
                    if platform.system() == "Windows":
                        # Use windump to read packet count
                        result = subprocess.run(
                            ["windump", "-r", pcap_file, "-q"], 
                            capture_output=True, text=True
                        )
                    else:
                        # Use tcpdump to read packet count
                        result = subprocess.run(
                            ["tcpdump", "-r", pcap_file, "-q"], 
                            capture_output=True, text=True
                        )
                    
                    if result.stdout.strip():
                        stats["packets_captured"] = len(result.stdout.strip().split('\n'))
            except:
                pass
            
            # Send to central analyzer
            headers = {"Content-Type": "application/json"}
            if self.config.api_key:
                headers["Authorization"] = f"Bearer {self.config.api_key}"
            
            response = requests.post(
                f"{self.config.central_analyzer_url}/api/v1/remote/capture-results",
                json=stats,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                self.logger.info(f"Successfully sent capture results for session {session_id}")
            else:
                self.logger.error(f"Failed to send capture results: {response.status_code}")
                
        except Exception as e:
            self.logger.error(f"Error sending capture results: {e}")

    def run(self):
        """Main run loop"""
        self.logger.info(f"Starting OpsConductor Network Probe {self.config.probe_id}")
        self.logger.info(f"Platform: {platform.system()} {platform.release()}")
        self.logger.info(f"Central Analyzer: {self.config.central_analyzer_url}")
        
        # Start heartbeat thread
        heartbeat_thread = threading.Thread(target=self.heartbeat_loop, daemon=True)
        heartbeat_thread.start()
        
        # Initial registration
        self.register_with_central_analyzer()
        
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.logger.info("Received interrupt signal, shutting down...")
            self.shutdown()

    def shutdown(self):
        """Shutdown the probe gracefully"""
        self.running = False
        
        # Stop all active captures
        for session_id in list(self.active_captures.keys()):
            self.stop_capture(session_id)
        
        self.logger.info("Probe shutdown complete")

def get_default_config_path() -> str:
    """Get default configuration file path based on platform"""
    if platform.system() == "Windows":
        return "C:\\Program Files\\OpsConductor Probe\\config.yaml"
    else:
        return "/etc/opsconductor-probe/config.yaml"

def create_default_config(config_path: str):
    """Create default configuration file"""
    default_config = {
        'central_analyzer': {
            'url': 'http://YOUR_HOST_IP:3006',
            'api_key': None
        },
        'probe': {
            'id': 'remote-probe-001',
            'name': 'Remote Network Probe',
            'location': 'Remote Location'
        },
        'heartbeat_interval': 30,
        'logging': {
            'level': 'INFO',
            'file': '/var/log/opsconductor-probe.log' if platform.system() != "Windows" 
                   else 'C:\\ProgramData\\OpsConductor\\probe.log'
        },
        'interfaces': []
    }
    
    # Create directory if it doesn't exist
    config_dir = Path(config_path).parent
    config_dir.mkdir(parents=True, exist_ok=True)
    
    with open(config_path, 'w') as f:
        yaml.dump(default_config, f, default_flow_style=False)
    
    print(f"Created default configuration at: {config_path}")

def main():
    """Main entry point"""
    # Parse command line arguments
    config_path = get_default_config_path()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--create-config":
            create_default_config(config_path)
            return
        elif sys.argv[1] == "--config":
            if len(sys.argv) > 2:
                config_path = sys.argv[2]
            else:
                print("Error: --config requires a path argument")
                return
        elif sys.argv[1] == "--help":
            print("OpsConductor Network Analytics Remote Probe")
            print("Usage:")
            print("  probe-standalone.py                    # Run with default config")
            print("  probe-standalone.py --config <path>    # Run with custom config")
            print("  probe-standalone.py --create-config    # Create default config file")
            print("  probe-standalone.py --help             # Show this help")
            return
    
    # Load configuration
    if not os.path.exists(config_path):
        print(f"Configuration file not found: {config_path}")
        print("Run with --create-config to create a default configuration file")
        return
    
    config = ProbeConfig.from_file(config_path)
    
    # Create and run probe
    probe = NetworkProbe(config)
    
    # Setup signal handlers
    def signal_handler(signum, frame):
        probe.shutdown()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    probe.run()

if __name__ == "__main__":
    main()