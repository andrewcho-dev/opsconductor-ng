#!/usr/bin/env python3
"""
Network Analytics Probe - Remote packet capture and analysis agent
Runs with privileged host network access to capture real network traffic
"""

import os
import json
import time
import asyncio
import subprocess
import psutil
import requests
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Network Analytics Probe", version="1.0.0")

# Configuration
CENTRAL_ANALYZER_URL = os.getenv("CENTRAL_ANALYZER_URL", "http://172.18.0.1:3006")
PROBE_ID = os.getenv("PROBE_ID", "host-probe-001")
PROBE_NAME = os.getenv("PROBE_NAME", "Host Network Probe")
PROBE_LOCATION = os.getenv("PROBE_LOCATION", "Docker Host")

# Global state
active_captures: Dict[str, Dict] = {}
probe_registered = False

class ProbeInfo(BaseModel):
    probe_id: str
    name: str
    location: str
    capabilities: List[str]
    interfaces: List[Dict[str, Any]]
    status: str
    last_heartbeat: datetime

class CaptureRequest(BaseModel):
    session_id: str
    interface: str
    duration: int = 60
    filter_expression: Optional[str] = None
    packet_count: Optional[int] = None

class CaptureStatus(BaseModel):
    session_id: str
    status: str
    packets_captured: int
    bytes_captured: int
    start_time: datetime
    end_time: Optional[datetime] = None

def get_network_interfaces() -> List[Dict[str, Any]]:
    """Get available network interfaces with detailed information"""
    interfaces = []
    
    try:
        # Get interface statistics
        net_io = psutil.net_io_counters(pernic=True)
        net_addrs = psutil.net_if_addrs()
        net_stats = psutil.net_if_stats()
        
        for interface_name, addrs in net_addrs.items():
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
                    "netmask": addr.netmask,
                    "broadcast": addr.broadcast
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
        logger.error(f"Error getting network interfaces: {e}")
    
    return interfaces

def get_probe_capabilities() -> List[str]:
    """Get probe capabilities"""
    capabilities = ["packet_capture", "interface_monitoring", "traffic_analysis"]
    
    # Check for additional tools
    try:
        subprocess.run(["tcpdump", "--version"], capture_output=True, check=True)
        capabilities.append("tcpdump")
    except:
        pass
    
    try:
        subprocess.run(["nmap", "--version"], capture_output=True, check=True)
        capabilities.append("nmap")
    except:
        pass
    
    return capabilities

async def register_with_central_analyzer():
    """Register this probe with the central analyzer"""
    global probe_registered
    
    try:
        probe_info = ProbeInfo(
            probe_id=PROBE_ID,
            name=PROBE_NAME,
            location=PROBE_LOCATION,
            capabilities=get_probe_capabilities(),
            interfaces=get_network_interfaces(),
            status="active",
            last_heartbeat=datetime.now(timezone.utc)
        )
        
        response = requests.post(
            f"{CENTRAL_ANALYZER_URL}/api/v1/remote/register-probe",
            json=probe_info.model_dump(mode='json'),
            timeout=10
        )
        
        if response.status_code == 200:
            probe_registered = True
            logger.info(f"Successfully registered probe {PROBE_ID} with central analyzer")
        else:
            logger.error(f"Failed to register probe: {response.status_code} - {response.text}")
            
    except Exception as e:
        logger.error(f"Error registering with central analyzer: {e}")

async def send_heartbeat():
    """Send periodic heartbeat to central analyzer"""
    while True:
        try:
            if probe_registered:
                heartbeat_data = {
                    "probe_id": PROBE_ID,
                    "status": "active",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "active_captures": len(active_captures),
                    "interfaces": get_network_interfaces()
                }
                
                response = requests.post(
                    f"{CENTRAL_ANALYZER_URL}/api/v1/remote/heartbeat",
                    json=heartbeat_data,
                    timeout=5
                )
                
                if response.status_code != 200:
                    logger.warning(f"Heartbeat failed: {response.status_code}")
                    
        except Exception as e:
            logger.error(f"Error sending heartbeat: {e}")
        
        await asyncio.sleep(30)  # Send heartbeat every 30 seconds

def start_packet_capture(session_id: str, interface: str, duration: int, 
                        filter_expression: Optional[str] = None, 
                        packet_count: Optional[int] = None) -> Dict:
    """Start packet capture using tcpdump"""
    try:
        # Build tcpdump command
        cmd = ["tcpdump", "-i", interface, "-w", f"/tmp/capture_{session_id}.pcap"]
        
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
            "status": "running"
        }
        
        active_captures[session_id] = capture_info
        
        # Schedule capture stop
        asyncio.create_task(stop_capture_after_duration(session_id, duration))
        
        return {
            "session_id": session_id,
            "status": "started",
            "message": f"Packet capture started on interface {interface}"
        }
        
    except Exception as e:
        logger.error(f"Error starting packet capture: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def stop_capture_after_duration(session_id: str, duration: int):
    """Stop capture after specified duration"""
    await asyncio.sleep(duration)
    
    if session_id in active_captures:
        capture_info = active_captures[session_id]
        if capture_info["status"] == "running":
            try:
                capture_info["process"].terminate()
                capture_info["status"] = "completed"
                capture_info["end_time"] = datetime.now(timezone.utc)
                
                # Send results to central analyzer
                await send_capture_results(session_id)
                
            except Exception as e:
                logger.error(f"Error stopping capture {session_id}: {e}")

async def send_capture_results(session_id: str):
    """Send capture results to central analyzer"""
    try:
        if session_id not in active_captures:
            return
        
        capture_info = active_captures[session_id]
        pcap_file = f"/tmp/capture_{session_id}.pcap"
        
        # Get capture statistics
        stats = {
            "session_id": session_id,
            "probe_id": PROBE_ID,
            "interface": capture_info["interface"],
            "start_time": capture_info["start_time"].isoformat(),
            "end_time": capture_info.get("end_time", datetime.now(timezone.utc)).isoformat(),
            "status": capture_info["status"],
            "packets_captured": 0,
            "bytes_captured": 0
        }
        
        # Try to get packet count from pcap file
        try:
            if os.path.exists(pcap_file):
                result = subprocess.run(
                    ["tcpdump", "-r", pcap_file, "-q"], 
                    capture_output=True, text=True
                )
                stats["packets_captured"] = len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0
                stats["bytes_captured"] = os.path.getsize(pcap_file)
        except:
            pass
        
        # Send to central analyzer
        response = requests.post(
            f"{CENTRAL_ANALYZER_URL}/api/v1/remote/capture-results",
            json=stats,
            timeout=10
        )
        
        if response.status_code == 200:
            logger.info(f"Successfully sent capture results for session {session_id}")
        else:
            logger.error(f"Failed to send capture results: {response.status_code}")
            
    except Exception as e:
        logger.error(f"Error sending capture results: {e}")

# API Endpoints

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "probe_id": PROBE_ID,
        "registered": probe_registered,
        "active_captures": len(active_captures),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.get("/interfaces")
async def get_interfaces():
    """Get available network interfaces"""
    return {
        "interfaces": get_network_interfaces(),
        "probe_id": PROBE_ID
    }

@app.post("/capture/start")
async def start_capture(request: CaptureRequest, background_tasks: BackgroundTasks):
    """Start packet capture"""
    if request.session_id in active_captures:
        raise HTTPException(status_code=400, detail="Capture session already active")
    
    result = start_packet_capture(
        request.session_id,
        request.interface,
        request.duration,
        request.filter_expression,
        request.packet_count
    )
    
    return result

@app.get("/capture/{session_id}/status")
async def get_capture_status(session_id: str):
    """Get capture status"""
    if session_id not in active_captures:
        raise HTTPException(status_code=404, detail="Capture session not found")
    
    capture_info = active_captures[session_id]
    
    return CaptureStatus(
        session_id=session_id,
        status=capture_info["status"],
        packets_captured=0,  # Would need to implement real-time counting
        bytes_captured=0,
        start_time=capture_info["start_time"],
        end_time=capture_info.get("end_time")
    )

@app.post("/capture/{session_id}/stop")
async def stop_capture(session_id: str):
    """Stop packet capture"""
    if session_id not in active_captures:
        raise HTTPException(status_code=404, detail="Capture session not found")
    
    capture_info = active_captures[session_id]
    
    try:
        if capture_info["status"] == "running":
            capture_info["process"].terminate()
            capture_info["status"] = "stopped"
            capture_info["end_time"] = datetime.now(timezone.utc)
            
            # Send results to central analyzer
            await send_capture_results(session_id)
        
        return {"message": f"Capture session {session_id} stopped"}
        
    except Exception as e:
        logger.error(f"Error stopping capture: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/info")
async def get_probe_info():
    """Get probe information"""
    return ProbeInfo(
        probe_id=PROBE_ID,
        name=PROBE_NAME,
        location=PROBE_LOCATION,
        capabilities=get_probe_capabilities(),
        interfaces=get_network_interfaces(),
        status="active" if probe_registered else "unregistered",
        last_heartbeat=datetime.now(timezone.utc)
    )

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize probe on startup"""
    logger.info(f"Starting Network Analytics Probe {PROBE_ID}")
    logger.info(f"Central Analyzer URL: {CENTRAL_ANALYZER_URL}")
    
    # Register with central analyzer
    await register_with_central_analyzer()
    
    # Start heartbeat task
    asyncio.create_task(send_heartbeat())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3007)