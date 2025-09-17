"""
OpsConductor Protocol Manager - Multi-protocol support for AI automation
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from abc import ABC, abstractmethod
import json
from datetime import datetime

# Protocol-specific imports
import paramiko
import aiosmtplib
from pysnmp.hlapi.asyncio import *
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import httpx

logger = logging.getLogger(__name__)

class ProtocolResult:
    """Standard result format for all protocol operations"""
    def __init__(self, success: bool, data: Any = None, error: str = None, metadata: Dict = None):
        self.success = success
        self.data = data
        self.error = error
        self.metadata = metadata or {}
        self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> Dict:
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat()
        }

class BaseProtocolHandler(ABC):
    """Base class for all protocol handlers"""
    
    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(f"protocol.{name}")
    
    @abstractmethod
    async def connect(self, target: Dict[str, Any], credentials: Dict[str, Any]) -> bool:
        """Establish connection to target"""
        pass
    
    @abstractmethod
    async def execute(self, command: str, **kwargs) -> ProtocolResult:
        """Execute command/operation"""
        pass
    
    @abstractmethod
    async def disconnect(self):
        """Close connection"""
        pass

class SNMPHandler(BaseProtocolHandler):
    """SNMP protocol handler for network device monitoring and configuration"""
    
    def __init__(self):
        super().__init__("snmp")
        self.target_info = None
        self.community = "public"
        self.version = "v2c"
    
    async def connect(self, target: Dict[str, Any], credentials: Dict[str, Any]) -> bool:
        """Initialize SNMP connection parameters"""
        try:
            self.target_info = {
                "host": target.get("ip_address", target.get("hostname")),
                "port": target.get("snmp_port", 161)
            }
            
            # Extract SNMP credentials
            self.community = credentials.get("community", "public")
            self.version = credentials.get("version", "v2c")
            
            self.logger.info(f"SNMP connection configured for {self.target_info['host']}")
            return True
            
        except Exception as e:
            self.logger.error(f"SNMP connection setup failed: {e}")
            return False
    
    async def execute(self, command: str, **kwargs) -> ProtocolResult:
        """Execute SNMP operations"""
        try:
            if command == "get_system_info":
                return await self._get_system_info()
            elif command == "get_interface_stats":
                return await self._get_interface_stats()
            elif command == "get_cpu_usage":
                return await self._get_cpu_usage()
            elif command == "get_memory_usage":
                return await self._get_memory_usage()
            elif command == "walk_oid":
                oid = kwargs.get("oid", "1.3.6.1.2.1.1")
                return await self._walk_oid(oid)
            else:
                return ProtocolResult(False, error=f"Unknown SNMP command: {command}")
                
        except Exception as e:
            self.logger.error(f"SNMP execute failed: {e}")
            return ProtocolResult(False, error=str(e))
    
    async def _get_system_info(self) -> ProtocolResult:
        """Get basic system information via SNMP"""
        try:
            system_oids = {
                "sysDescr": "1.3.6.1.2.1.1.1.0",
                "sysObjectID": "1.3.6.1.2.1.1.2.0",
                "sysUpTime": "1.3.6.1.2.1.1.3.0",
                "sysContact": "1.3.6.1.2.1.1.4.0",
                "sysName": "1.3.6.1.2.1.1.5.0",
                "sysLocation": "1.3.6.1.2.1.1.6.0"
            }
            
            results = {}
            for name, oid in system_oids.items():
                async for (errorIndication, errorStatus, errorIndex, varBinds) in getCmd(
                    SnmpEngine(),
                    CommunityData(self.community),
                    UdpTransportTarget((self.target_info["host"], self.target_info["port"])),
                    ContextData(),
                    ObjectType(ObjectIdentity(oid))
                ):
                    if errorIndication:
                        self.logger.error(f"SNMP error for {name}: {errorIndication}")
                        continue
                    elif errorStatus:
                        self.logger.error(f"SNMP error for {name}: {errorStatus.prettyPrint()}")
                        continue
                    else:
                        for varBind in varBinds:
                            results[name] = str(varBind[1])
            
            return ProtocolResult(True, data=results, metadata={"operation": "system_info"})
            
        except Exception as e:
            return ProtocolResult(False, error=f"Failed to get system info: {e}")
    
    async def _get_interface_stats(self) -> ProtocolResult:
        """Get network interface statistics"""
        try:
            interface_data = []
            
            # Walk interface table
            async for (errorIndication, errorStatus, errorIndex, varBinds) in nextCmd(
                SnmpEngine(),
                CommunityData(self.community),
                UdpTransportTarget((self.target_info["host"], self.target_info["port"])),
                ContextData(),
                ObjectType(ObjectIdentity('1.3.6.1.2.1.2.2.1.2')),  # ifDescr
                lexicographicMode=False
            ):
                if errorIndication:
                    break
                elif errorStatus:
                    break
                else:
                    for varBind in varBinds:
                        interface_data.append({
                            "index": str(varBind[0]).split('.')[-1],
                            "description": str(varBind[1])
                        })
            
            return ProtocolResult(True, data=interface_data, metadata={"operation": "interface_stats"})
            
        except Exception as e:
            return ProtocolResult(False, error=f"Failed to get interface stats: {e}")
    
    async def _walk_oid(self, oid: str) -> ProtocolResult:
        """Walk an SNMP OID tree"""
        try:
            results = []
            
            async for (errorIndication, errorStatus, errorIndex, varBinds) in nextCmd(
                SnmpEngine(),
                CommunityData(self.community),
                UdpTransportTarget((self.target_info["host"], self.target_info["port"])),
                ContextData(),
                ObjectType(ObjectIdentity(oid)),
                lexicographicMode=False
            ):
                if errorIndication:
                    break
                elif errorStatus:
                    break
                else:
                    for varBind in varBinds:
                        results.append({
                            "oid": str(varBind[0]),
                            "value": str(varBind[1])
                        })
            
            return ProtocolResult(True, data=results, metadata={"operation": "walk_oid", "base_oid": oid})
            
        except Exception as e:
            return ProtocolResult(False, error=f"Failed to walk OID {oid}: {e}")
    
    async def disconnect(self):
        """SNMP is stateless, no cleanup needed"""
        pass

class SMTPHandler(BaseProtocolHandler):
    """SMTP protocol handler for email notifications and alerts"""
    
    def __init__(self):
        super().__init__("smtp")
        self.smtp_client = None
        self.config = {}
    
    async def connect(self, target: Dict[str, Any], credentials: Dict[str, Any]) -> bool:
        """Connect to SMTP server"""
        try:
            self.config = {
                "hostname": target.get("hostname", target.get("ip_address")),
                "port": target.get("port", 587),
                "use_tls": target.get("use_tls", True),
                "username": credentials.get("username"),
                "password": credentials.get("password")
            }
            
            # Test connection
            self.smtp_client = aiosmtplib.SMTP(
                hostname=self.config["hostname"],
                port=self.config["port"],
                use_tls=self.config["use_tls"]
            )
            
            await self.smtp_client.connect()
            
            if self.config["username"] and self.config["password"]:
                await self.smtp_client.login(self.config["username"], self.config["password"])
            
            self.logger.info(f"SMTP connected to {self.config['hostname']}:{self.config['port']}")
            return True
            
        except Exception as e:
            self.logger.error(f"SMTP connection failed: {e}")
            return False
    
    async def execute(self, command: str, **kwargs) -> ProtocolResult:
        """Execute SMTP operations"""
        try:
            if command == "send_email":
                return await self._send_email(**kwargs)
            elif command == "send_alert":
                return await self._send_alert(**kwargs)
            elif command == "test_connection":
                return await self._test_connection()
            else:
                return ProtocolResult(False, error=f"Unknown SMTP command: {command}")
                
        except Exception as e:
            self.logger.error(f"SMTP execute failed: {e}")
            return ProtocolResult(False, error=str(e))
    
    async def _send_email(self, to_addresses: List[str], subject: str, body: str, 
                         from_address: str = None, html_body: str = None) -> ProtocolResult:
        """Send email message"""
        try:
            if not self.smtp_client:
                return ProtocolResult(False, error="SMTP client not connected")
            
            from_addr = from_address or self.config.get("username", "noreply@opsconductor.local")
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = from_addr
            msg['To'] = ', '.join(to_addresses)
            
            # Add text part
            text_part = MIMEText(body, 'plain')
            msg.attach(text_part)
            
            # Add HTML part if provided
            if html_body:
                html_part = MIMEText(html_body, 'html')
                msg.attach(html_part)
            
            # Send message
            await self.smtp_client.send_message(msg)
            
            return ProtocolResult(True, data={
                "message_id": msg.get('Message-ID'),
                "recipients": to_addresses,
                "subject": subject
            }, metadata={"operation": "send_email"})
            
        except Exception as e:
            return ProtocolResult(False, error=f"Failed to send email: {e}")
    
    async def _send_alert(self, alert_type: str, message: str, severity: str = "info", 
                         recipients: List[str] = None) -> ProtocolResult:
        """Send formatted alert email"""
        try:
            if not recipients:
                recipients = ["ops-team@company.local"]
            
            subject = f"OpsConductor Alert [{severity.upper()}]: {alert_type}"
            
            body = f"""
OpsConductor System Alert

Alert Type: {alert_type}
Severity: {severity.upper()}
Timestamp: {datetime.utcnow().isoformat()}

Message:
{message}

---
This alert was generated automatically by OpsConductor AI.
            """.strip()
            
            html_body = f"""
<html>
<body>
<h2>OpsConductor System Alert</h2>
<table border="1" cellpadding="5">
<tr><td><strong>Alert Type:</strong></td><td>{alert_type}</td></tr>
<tr><td><strong>Severity:</strong></td><td><span style="color: {'red' if severity == 'critical' else 'orange' if severity == 'warning' else 'blue'}">{severity.upper()}</span></td></tr>
<tr><td><strong>Timestamp:</strong></td><td>{datetime.utcnow().isoformat()}</td></tr>
</table>
<h3>Message:</h3>
<p>{message}</p>
<hr>
<small>This alert was generated automatically by OpsConductor AI.</small>
</body>
</html>
            """
            
            return await self._send_email(recipients, subject, body, html_body=html_body)
            
        except Exception as e:
            return ProtocolResult(False, error=f"Failed to send alert: {e}")
    
    async def _test_connection(self) -> ProtocolResult:
        """Test SMTP connection"""
        try:
            if not self.smtp_client:
                return ProtocolResult(False, error="SMTP client not connected")
            
            # Send NOOP command to test connection
            await self.smtp_client.noop()
            
            return ProtocolResult(True, data={"status": "connected"}, metadata={"operation": "test_connection"})
            
        except Exception as e:
            return ProtocolResult(False, error=f"Connection test failed: {e}")
    
    async def disconnect(self):
        """Close SMTP connection"""
        try:
            if self.smtp_client:
                await self.smtp_client.quit()
                self.smtp_client = None
        except Exception as e:
            self.logger.error(f"SMTP disconnect error: {e}")

class SSHHandler(BaseProtocolHandler):
    """SSH protocol handler for secure remote execution"""
    
    def __init__(self):
        super().__init__("ssh")
        self.ssh_client = None
        self.target_info = None
    
    async def connect(self, target: Dict[str, Any], credentials: Dict[str, Any]) -> bool:
        """Connect to SSH server"""
        try:
            self.target_info = target
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Connect with credentials
            await asyncio.get_event_loop().run_in_executor(
                None,
                self.ssh_client.connect,
                target.get("ip_address", target.get("hostname")),
                target.get("port", 22),
                credentials.get("username"),
                credentials.get("password"),
                credentials.get("private_key")
            )
            
            self.logger.info(f"SSH connected to {target.get('hostname')}")
            return True
            
        except Exception as e:
            self.logger.error(f"SSH connection failed: {e}")
            return False
    
    async def execute(self, command: str, **kwargs) -> ProtocolResult:
        """Execute SSH operations"""
        try:
            if command == "run_command":
                cmd = kwargs.get("cmd", "")
                return await self._run_command(cmd)
            elif command == "run_script":
                script = kwargs.get("script", "")
                interpreter = kwargs.get("interpreter", "/bin/bash")
                return await self._run_script(script, interpreter)
            elif command == "file_transfer":
                return await self._file_transfer(**kwargs)
            else:
                return ProtocolResult(False, error=f"Unknown SSH command: {command}")
                
        except Exception as e:
            self.logger.error(f"SSH execute failed: {e}")
            return ProtocolResult(False, error=str(e))
    
    async def _run_command(self, cmd: str) -> ProtocolResult:
        """Execute a single command via SSH"""
        try:
            if not self.ssh_client:
                return ProtocolResult(False, error="SSH client not connected")
            
            # Execute command
            stdin, stdout, stderr = await asyncio.get_event_loop().run_in_executor(
                None, self.ssh_client.exec_command, cmd
            )
            
            # Read output
            stdout_data = await asyncio.get_event_loop().run_in_executor(None, stdout.read)
            stderr_data = await asyncio.get_event_loop().run_in_executor(None, stderr.read)
            exit_code = stdout.channel.recv_exit_status()
            
            return ProtocolResult(True, data={
                "stdout": stdout_data.decode('utf-8'),
                "stderr": stderr_data.decode('utf-8'),
                "exit_code": exit_code,
                "command": cmd
            }, metadata={"operation": "run_command"})
            
        except Exception as e:
            return ProtocolResult(False, error=f"Failed to run command: {e}")
    
    async def _run_script(self, script: str, interpreter: str = "/bin/bash") -> ProtocolResult:
        """Execute a script via SSH"""
        try:
            # Create temporary script file
            script_path = f"/tmp/opsconductor_script_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.sh"
            
            # Upload script
            sftp = self.ssh_client.open_sftp()
            await asyncio.get_event_loop().run_in_executor(
                None, sftp.putfo, script.encode('utf-8'), script_path
            )
            sftp.close()
            
            # Make executable and run
            chmod_result = await self._run_command(f"chmod +x {script_path}")
            if not chmod_result.success:
                return chmod_result
            
            exec_result = await self._run_command(f"{interpreter} {script_path}")
            
            # Cleanup
            await self._run_command(f"rm -f {script_path}")
            
            return exec_result
            
        except Exception as e:
            return ProtocolResult(False, error=f"Failed to run script: {e}")
    
    async def _file_transfer(self, local_path: str = None, remote_path: str = None, 
                           operation: str = "upload", content: str = None) -> ProtocolResult:
        """Transfer files via SFTP"""
        try:
            if not self.ssh_client:
                return ProtocolResult(False, error="SSH client not connected")
            
            sftp = self.ssh_client.open_sftp()
            
            if operation == "upload":
                if content:
                    # Upload content as file
                    await asyncio.get_event_loop().run_in_executor(
                        None, sftp.putfo, content.encode('utf-8'), remote_path
                    )
                elif local_path:
                    # Upload file
                    await asyncio.get_event_loop().run_in_executor(
                        None, sftp.put, local_path, remote_path
                    )
                else:
                    return ProtocolResult(False, error="No content or local_path provided for upload")
                
                result_data = {"operation": "upload", "remote_path": remote_path}
                
            elif operation == "download":
                # Download file
                await asyncio.get_event_loop().run_in_executor(
                    None, sftp.get, remote_path, local_path
                )
                result_data = {"operation": "download", "local_path": local_path}
            
            else:
                return ProtocolResult(False, error=f"Unknown file operation: {operation}")
            
            sftp.close()
            return ProtocolResult(True, data=result_data, metadata={"operation": "file_transfer"})
            
        except Exception as e:
            return ProtocolResult(False, error=f"File transfer failed: {e}")
    
    async def disconnect(self):
        """Close SSH connection"""
        try:
            if self.ssh_client:
                self.ssh_client.close()
                self.ssh_client = None
        except Exception as e:
            self.logger.error(f"SSH disconnect error: {e}")

class VAPIXHandler(BaseProtocolHandler):
    """VAPIX API handler for Axis camera integration"""
    
    def __init__(self):
        super().__init__("vapix")
        self.base_url = None
        self.auth = None
        self.session = None
    
    async def connect(self, target: Dict[str, Any], credentials: Dict[str, Any]) -> bool:
        """Connect to VAPIX API"""
        try:
            host = target.get("ip_address", target.get("hostname"))
            port = target.get("port", 80)
            use_https = target.get("use_https", False)
            
            protocol = "https" if use_https else "http"
            self.base_url = f"{protocol}://{host}:{port}"
            
            self.auth = httpx.BasicAuth(
                credentials.get("username", "root"),
                credentials.get("password", "")
            )
            
            self.session = httpx.AsyncClient(auth=self.auth, verify=False)
            
            # Test connection
            response = await self.session.get(f"{self.base_url}/axis-cgi/param.cgi?action=list&group=Properties.System")
            response.raise_for_status()
            
            self.logger.info(f"VAPIX connected to {host}")
            return True
            
        except Exception as e:
            self.logger.error(f"VAPIX connection failed: {e}")
            return False
    
    async def execute(self, command: str, **kwargs) -> ProtocolResult:
        """Execute VAPIX operations"""
        try:
            if command == "get_system_info":
                return await self._get_system_info()
            elif command == "setup_motion_detection":
                return await self._setup_motion_detection(**kwargs)
            elif command == "get_motion_events":
                return await self._get_motion_events()
            elif command == "capture_image":
                return await self._capture_image(**kwargs)
            else:
                return ProtocolResult(False, error=f"Unknown VAPIX command: {command}")
                
        except Exception as e:
            self.logger.error(f"VAPIX execute failed: {e}")
            return ProtocolResult(False, error=str(e))
    
    async def _get_system_info(self) -> ProtocolResult:
        """Get camera system information"""
        try:
            response = await self.session.get(f"{self.base_url}/axis-cgi/param.cgi?action=list&group=Properties")
            response.raise_for_status()
            
            # Parse response
            info = {}
            for line in response.text.split('\n'):
                if '=' in line:
                    key, value = line.split('=', 1)
                    info[key.strip()] = value.strip()
            
            return ProtocolResult(True, data=info, metadata={"operation": "system_info"})
            
        except Exception as e:
            return ProtocolResult(False, error=f"Failed to get system info: {e}")
    
    async def _setup_motion_detection(self, sensitivity: int = 50, enabled: bool = True) -> ProtocolResult:
        """Configure motion detection"""
        try:
            params = {
                "action": "update",
                "MotionDetection.M1.Enabled": "yes" if enabled else "no",
                "MotionDetection.M1.Level": str(sensitivity)
            }
            
            response = await self.session.post(f"{self.base_url}/axis-cgi/param.cgi", data=params)
            response.raise_for_status()
            
            return ProtocolResult(True, data={
                "enabled": enabled,
                "sensitivity": sensitivity
            }, metadata={"operation": "setup_motion_detection"})
            
        except Exception as e:
            return ProtocolResult(False, error=f"Failed to setup motion detection: {e}")
    
    async def _capture_image(self, resolution: str = "1920x1080") -> ProtocolResult:
        """Capture image from camera"""
        try:
            params = {"resolution": resolution}
            response = await self.session.get(f"{self.base_url}/axis-cgi/jpg/image.cgi", params=params)
            response.raise_for_status()
            
            return ProtocolResult(True, data={
                "image_data": response.content,
                "content_type": response.headers.get("content-type"),
                "size": len(response.content)
            }, metadata={"operation": "capture_image", "resolution": resolution})
            
        except Exception as e:
            return ProtocolResult(False, error=f"Failed to capture image: {e}")
    
    async def disconnect(self):
        """Close VAPIX session"""
        try:
            if self.session:
                await self.session.aclose()
                self.session = None
        except Exception as e:
            self.logger.error(f"VAPIX disconnect error: {e}")

class ProtocolManager:
    """Central manager for all protocol handlers"""
    
    def __init__(self):
        self.handlers = {
            "snmp": SNMPHandler(),
            "smtp": SMTPHandler(),
            "ssh": SSHHandler(),
            "vapix": VAPIXHandler()
        }
        self.active_connections = {}
        self.logger = logging.getLogger("protocol_manager")
    
    async def get_handler(self, protocol: str) -> Optional[BaseProtocolHandler]:
        """Get protocol handler by name"""
        return self.handlers.get(protocol.lower())
    
    async def connect(self, protocol: str, target: Dict[str, Any], credentials: Dict[str, Any]) -> bool:
        """Connect to target using specified protocol"""
        try:
            handler = await self.get_handler(protocol)
            if not handler:
                self.logger.error(f"Unknown protocol: {protocol}")
                return False
            
            success = await handler.connect(target, credentials)
            if success:
                connection_id = f"{protocol}_{target.get('hostname', target.get('ip_address'))}"
                self.active_connections[connection_id] = handler
                self.logger.info(f"Connected to {connection_id}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Connection failed for {protocol}: {e}")
            return False
    
    async def execute(self, protocol: str, target: Dict[str, Any], command: str, **kwargs) -> ProtocolResult:
        """Execute command using specified protocol"""
        try:
            connection_id = f"{protocol}_{target.get('hostname', target.get('ip_address'))}"
            handler = self.active_connections.get(connection_id)
            
            if not handler:
                self.logger.warning(f"No active connection for {connection_id}, attempting to connect...")
                # Try to connect first
                credentials = kwargs.get("credentials", {})
                if not await self.connect(protocol, target, credentials):
                    return ProtocolResult(False, error=f"Failed to connect to {connection_id}")
                handler = self.active_connections.get(connection_id)
            
            if not handler:
                return ProtocolResult(False, error=f"Handler not available for {protocol}")
            
            return await handler.execute(command, **kwargs)
            
        except Exception as e:
            self.logger.error(f"Execute failed for {protocol}: {e}")
            return ProtocolResult(False, error=str(e))
    
    async def disconnect(self, protocol: str, target: Dict[str, Any]):
        """Disconnect from target"""
        try:
            connection_id = f"{protocol}_{target.get('hostname', target.get('ip_address'))}"
            handler = self.active_connections.get(connection_id)
            
            if handler:
                await handler.disconnect()
                del self.active_connections[connection_id]
                self.logger.info(f"Disconnected from {connection_id}")
            
        except Exception as e:
            self.logger.error(f"Disconnect failed for {protocol}: {e}")
    
    async def disconnect_all(self):
        """Disconnect all active connections"""
        for connection_id, handler in list(self.active_connections.items()):
            try:
                await handler.disconnect()
                del self.active_connections[connection_id]
                self.logger.info(f"Disconnected from {connection_id}")
            except Exception as e:
                self.logger.error(f"Error disconnecting {connection_id}: {e}")
    
    def get_supported_protocols(self) -> List[str]:
        """Get list of supported protocols"""
        return list(self.handlers.keys())
    
    def get_protocol_capabilities(self, protocol: str) -> Dict[str, Any]:
        """Get capabilities for a specific protocol"""
        capabilities = {
            "snmp": {
                "commands": ["get_system_info", "get_interface_stats", "get_cpu_usage", "get_memory_usage", "walk_oid"],
                "description": "Network device monitoring and SNMP operations",
                "connection_type": "stateless"
            },
            "smtp": {
                "commands": ["send_email", "send_alert", "test_connection"],
                "description": "Email notifications and alerts",
                "connection_type": "session"
            },
            "ssh": {
                "commands": ["run_command", "run_script", "file_transfer"],
                "description": "Secure remote command execution and file transfer",
                "connection_type": "session"
            },
            "vapix": {
                "commands": ["get_system_info", "setup_motion_detection", "get_motion_events", "capture_image"],
                "description": "Axis camera integration and motion detection",
                "connection_type": "session"
            }
        }
        
        return capabilities.get(protocol.lower(), {})

# Global protocol manager instance
protocol_manager = ProtocolManager()