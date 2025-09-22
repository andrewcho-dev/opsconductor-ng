"""
Data models for Network Analyzer Service
"""

from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

class AnalysisType(str, Enum):
    """Types of network analysis"""
    PACKET_CAPTURE = "packet_capture"
    TRAFFIC_MONITORING = "traffic_monitoring"
    PROTOCOL_ANALYSIS = "protocol_analysis"
    PERFORMANCE_ANALYSIS = "performance_analysis"
    SECURITY_ANALYSIS = "security_analysis"
    CONNECTIVITY_TEST = "connectivity_test"

class CaptureStatus(str, Enum):
    """Packet capture session status"""
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    COMPLETED = "completed"
    FAILED = "failed"

class NetworkProtocol(str, Enum):
    """Supported network protocols"""
    TCP = "tcp"
    UDP = "udp"
    ICMP = "icmp"
    HTTP = "http"
    HTTPS = "https"
    DNS = "dns"
    DHCP = "dhcp"
    ARP = "arp"
    SSH = "ssh"
    FTP = "ftp"
    SMTP = "smtp"
    SNMP = "snmp"

# Request Models
class StartCaptureRequest(BaseModel):
    """Request to start packet capture"""
    interface: str = Field(..., description="Network interface to capture on")
    filter_expression: Optional[str] = Field(None, description="BPF filter expression")
    duration: Optional[int] = Field(None, description="Capture duration in seconds")
    packet_count: Optional[int] = Field(None, description="Maximum packets to capture")
    target_id: Optional[int] = Field(None, description="Target asset ID for remote capture")
    enable_ai_analysis: bool = Field(False, description="Enable AI-powered analysis")
    
    class Config:
        schema_extra = {
            "example": {
                "interface": "eth0",
                "filter_expression": "tcp port 80",
                "duration": 60,
                "packet_count": 1000,
                "enable_ai_analysis": True
            }
        }

class ProtocolAnalysisRequest(BaseModel):
    """Request for protocol analysis"""
    protocol: NetworkProtocol
    data_source: str = Field(..., description="Data source (capture file, live interface, etc.)")
    filters: Optional[Dict[str, Any]] = Field(None, description="Additional filters")
    
    class Config:
        schema_extra = {
            "example": {
                "protocol": "http",
                "data_source": "eth0",
                "filters": {"port": 80, "method": "GET"}
            }
        }

class AIDiagnosisRequest(BaseModel):
    """Request for AI-powered network diagnosis"""
    symptoms: List[str] = Field(..., description="Observed network symptoms")
    network_data: Optional[Dict[str, Any]] = Field(None, description="Network data for analysis")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")
    enable_auto_remediation: bool = Field(False, description="Enable automatic remediation")
    
    class Config:
        schema_extra = {
            "example": {
                "symptoms": ["slow response times", "intermittent connectivity"],
                "network_data": {"latency": 150, "packet_loss": 0.05},
                "context": {"application": "web_server", "time_of_day": "peak_hours"},
                "enable_auto_remediation": False
            }
        }

class NetworkAlertConfig(BaseModel):
    """Network monitoring alert configuration"""
    bandwidth_threshold: Optional[float] = Field(None, description="Bandwidth threshold in Mbps")
    latency_threshold: Optional[float] = Field(None, description="Latency threshold in ms")
    packet_loss_threshold: Optional[float] = Field(None, description="Packet loss threshold (0-1)")
    connection_count_threshold: Optional[int] = Field(None, description="Max concurrent connections")
    enable_anomaly_detection: bool = Field(True, description="Enable AI anomaly detection")
    
    class Config:
        schema_extra = {
            "example": {
                "bandwidth_threshold": 100.0,
                "latency_threshold": 100.0,
                "packet_loss_threshold": 0.01,
                "connection_count_threshold": 1000,
                "enable_anomaly_detection": True
            }
        }

class DeployAgentRequest(BaseModel):
    """Request to deploy remote analysis agent"""
    target_id: int = Field(..., description="Target asset ID")
    agent_config: Dict[str, Any] = Field(..., description="Agent configuration")
    
    class Config:
        schema_extra = {
            "example": {
                "target_id": 123,
                "agent_config": {
                    "capture_interfaces": ["eth0"],
                    "analysis_modules": ["packet_capture", "performance_monitoring"],
                    "reporting_interval": 60
                }
            }
        }

class RemoteAnalysisRequest(BaseModel):
    """Request for remote network analysis"""
    analysis_type: AnalysisType
    parameters: Dict[str, Any] = Field(..., description="Analysis parameters")
    
    class Config:
        schema_extra = {
            "example": {
                "analysis_type": "connectivity_test",
                "parameters": {
                    "target_host": "8.8.8.8",
                    "port": 53,
                    "protocol": "udp"
                }
            }
        }

# Response Models
class PacketInfo(BaseModel):
    """Individual packet information"""
    timestamp: float
    source_ip: str
    destination_ip: str
    source_port: Optional[int] = None
    destination_port: Optional[int] = None
    protocol: str
    size: int
    flags: Optional[List[str]] = None
    payload_preview: Optional[str] = None

class TrafficStatistics(BaseModel):
    """Network traffic statistics"""
    total_packets: int
    total_bytes: int
    packets_per_second: float
    bytes_per_second: float
    protocol_distribution: Dict[str, int]
    top_talkers: List[Dict[str, Any]]
    port_distribution: Dict[str, int]

class NetworkInterface(BaseModel):
    """Network interface information"""
    name: str
    ip_address: Optional[str] = None
    mac_address: Optional[str] = None
    status: str
    rx_bytes: int
    tx_bytes: int
    rx_packets: int
    tx_packets: int
    rx_errors: int
    tx_errors: int

class NetworkAlert(BaseModel):
    """Network monitoring alert"""
    alert_id: str
    alert_type: str
    severity: str
    message: str
    timestamp: datetime
    source: Optional[str] = None
    resolved: bool = False
    resolution_time: Optional[datetime] = None

class AIAnalysisResult(BaseModel):
    """AI analysis results"""
    analysis_id: str
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    findings: List[str]
    recommendations: List[str]
    anomalies_detected: List[Dict[str, Any]]
    performance_insights: Dict[str, Any]
    security_concerns: List[str]

class CaptureSessionResponse(BaseModel):
    """Response for capture session creation"""
    session_id: str
    status: CaptureStatus
    message: str

class CaptureResultResponse(BaseModel):
    """Response with capture results"""
    session_id: str
    status: CaptureStatus
    packet_count: int
    packets: List[PacketInfo]
    statistics: TrafficStatistics
    ai_analysis: Optional[AIAnalysisResult] = None

class NetworkStatusResponse(BaseModel):
    """Network monitoring status response"""
    interfaces: List[NetworkInterface]
    traffic_stats: TrafficStatistics
    active_connections: int
    alerts: List[NetworkAlert]
    timestamp: datetime

class ProtocolAnalysisResponse(BaseModel):
    """Protocol analysis response"""
    protocol: NetworkProtocol
    analysis_results: Dict[str, Any]
    statistics: Dict[str, Any]
    recommendations: List[str]
    timestamp: datetime

class AIDiagnosisResponse(BaseModel):
    """AI diagnosis response"""
    diagnosis_id: str
    issue_type: str
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    root_cause: str
    recommendations: List[str]
    remediation_plan: Optional[Dict[str, Any]] = None
    supporting_evidence: List[Dict[str, Any]]

class AnalysisSessionInfo(BaseModel):
    """Analysis session information"""
    session_id: str
    session_type: str
    user_id: Union[int, str]
    started_at: float
    status: str

# WebSocket Models
class WebSocketMessage(BaseModel):
    """WebSocket message format"""
    message_type: str
    session_id: str
    data: Dict[str, Any]
    timestamp: datetime

class RealTimeUpdate(BaseModel):
    """Real-time analysis update"""
    update_type: str
    session_id: str
    packet_count: Optional[int] = None
    current_stats: Optional[TrafficStatistics] = None
    alerts: Optional[List[NetworkAlert]] = None
    ai_insights: Optional[List[str]] = None