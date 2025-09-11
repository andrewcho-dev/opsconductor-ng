"""
Generic Block System for OpsConductor
Implements 8 universal blocks that handle all automation scenarios
"""

import json
import re
import time
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod

from .logging import get_logger

logger = get_logger("generic-blocks")

class GenericBlockExecutor:
    """Executes generic blocks with connection abstraction"""
    
    def __init__(self):
        self.execution_history = []
        self.connection_pool = {}
    
    async def execute_block(self, block_type: str, block_config: Dict[str, Any], input_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute any generic block type"""
        if input_data is None:
            input_data = {}
        
        start_time = time.time()
        
        try:
            # Route to appropriate handler
            if block_type == "action.command":
                result = await self.execute_command_block(block_config, input_data)
            elif block_type == "action.http_request":
                result = await self.execute_http_request_block(block_config, input_data)
            elif block_type == "action.notification":
                result = await self.execute_notification_block(block_config, input_data)
            elif block_type == "data.transform":
                result = await self.execute_data_transform_block(block_config, input_data)
            elif block_type == "logic.if":
                result = await self.execute_logic_if_block(block_config, input_data)
            elif block_type == "flow.delay":
                result = await self.execute_flow_delay_block(block_config, input_data)
            elif block_type == "flow.start":
                result = await self.execute_flow_start_block(block_config, input_data)
            elif block_type == "flow.end":
                result = await self.execute_flow_end_block(block_config, input_data)
            else:
                result = {
                    "success": False,
                    "error": f"Unsupported block type: {block_type}",
                    "result": None
                }
            
            # Add execution metadata
            execution_time = int((time.time() - start_time) * 1000)
            result["execution_metadata"] = {
                "block_type": block_type,
                "execution_time_ms": execution_time,
                "timestamp": datetime.now().isoformat(),
                "block_id": block_config.get("id", "unknown")
            }
            
            # Store in execution history
            self.execution_history.append({
                "block_type": block_type,
                "block_id": block_config.get("id", "unknown"),
                "success": result.get("success", False),
                "execution_time_ms": execution_time,
                "timestamp": datetime.now().isoformat()
            })
            
            return result
            
        except Exception as e:
            execution_time = int((time.time() - start_time) * 1000)
            error_result = {
                "success": False,
                "error": str(e),
                "result": None,
                "execution_metadata": {
                    "block_type": block_type,
                    "execution_time_ms": execution_time,
                    "timestamp": datetime.now().isoformat(),
                    "block_id": block_config.get("id", "unknown")
                }
            }
            
            # Store failed execution in history
            self.execution_history.append({
                "block_type": block_type,
                "block_id": block_config.get("id", "unknown"),
                "success": False,
                "execution_time_ms": execution_time,
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            })
            
            return error_result
    
    async def execute_command_block(self, block_config: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute action.command block - handles SSH, WinRM, local, Docker, K8s"""
        target = self._process_template(block_config.get('target', 'localhost'), input_data)
        command = self._process_template(block_config.get('command', ''), input_data)
        connection_method = block_config.get('connection_method', 'auto')
        
        logger.info(f"Executing command block: target={target}, command={command}, method={connection_method}")
        
        try:
            # Get connection for target
            connection = await self._get_connection(target, connection_method, block_config)
            
            # Execute command through connection
            result = await connection.execute_command(command, block_config)
            
            return {
                "success": result.get("exit_code", 0) == 0,
                "result": {
                    "stdout": result.get("stdout", ""),
                    "stderr": result.get("stderr", ""),
                    "exit_code": result.get("exit_code", 0),
                    "execution_time": result.get("execution_time", 0),
                    "target": target,
                    "connection_method": connection_method,
                    "command": command
                }
            }
        except Exception as e:
            logger.error(f"Command execution failed: {str(e)}")
            return {
                "success": False,
                "error": f"Command execution failed: {str(e)}",
                "result": None
            }
    
    async def execute_http_request_block(self, block_config: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute action.http_request block - handles REST APIs, webhooks, etc."""
        method = self._process_template(block_config.get('method', 'GET'), input_data)
        url = self._process_template(block_config.get('url', ''), input_data)
        headers = block_config.get('headers', {})
        body = self._process_template(json.dumps(block_config.get('body', {})), input_data)
        
        logger.info(f"Executing HTTP request: {method} {url}")
        
        try:
            # Process headers with templates
            processed_headers = {}
            for key, value in headers.items():
                processed_headers[key] = self._process_template(str(value), input_data)
            
            # Get HTTP connection
            connection = await self._get_http_connection(url, block_config)
            
            # Execute HTTP request
            result = await connection.execute_request(method, url, processed_headers, body, block_config)
            
            return {
                "success": result.get("status_code", 500) < 400,
                "response": result,
                "result": {
                    "status_code": result.get("status_code", 500),
                    "response_data": result.get("data", ""),
                    "success": result.get("status_code", 500) < 400
                }
            }
        except Exception as e:
            logger.error(f"HTTP request failed: {str(e)}")
            return {
                "success": False,
                "error": f"HTTP request failed: {str(e)}",
                "result": None
            }
    
    async def execute_notification_block(self, block_config: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute action.notification block - handles email, Slack, Teams, etc."""
        notification_type = self._process_template(block_config.get('notification_type', 'email'), input_data)
        recipients = block_config.get('recipients', [])
        subject = self._process_template(block_config.get('subject', ''), input_data)
        message = self._process_template(block_config.get('message', ''), input_data)
        
        logger.info(f"Executing notification: type={notification_type}, recipients={len(recipients)}")
        
        try:
            # Get notification service connection
            connection = await self._get_notification_connection(notification_type, block_config)
            
            # Send notification
            result = await connection.send_notification(notification_type, recipients, subject, message, block_config)
            
            return {
                "success": True,
                "result": {
                    "type": notification_type,
                    "recipients": recipients,
                    "subject": subject,
                    "message": message,
                    "sent_at": datetime.now().isoformat(),
                    "message_id": result.get("message_id", f"msg_{int(time.time())}")
                },
                "notification_sent": True
            }
        except Exception as e:
            logger.error(f"Notification failed: {str(e)}")
            return {
                "success": False,
                "error": f"Notification failed: {str(e)}",
                "result": None
            }
    
    async def execute_data_transform_block(self, block_config: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute data.transform block - handles JSON, CSV, XML, text processing"""
        script = block_config.get('script', '')
        
        if not script:
            return {"success": False, "error": "No transformation script provided", "result": None}
        
        logger.info(f"Executing data transformation script")
        
        # Create execution context
        context = {
            'input': input_data,
            'data': input_data,
            'json': json,
            'datetime': datetime,
            'time': time,
            're': re,
            'result': None  # Initialize result
        }
        
        try:
            # Execute the script directly as Python
            exec(script, context)
            
            # Get the result
            output_data = context.get('result', input_data)
            
            return {
                "success": True,
                "output_data": output_data,
                "result": output_data
            }
        except Exception as e:
            logger.error(f"Data transformation failed: {str(e)}")
            return {"success": False, "error": f"Script execution error: {str(e)}", "result": None}
    
    async def execute_logic_if_block(self, block_config: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute logic.if block - handles conditional logic"""
        condition = self._process_template(block_config.get('condition', 'True'), input_data)
        
        logger.info(f"Executing logic condition: {condition}")
        
        # Create safe evaluation context
        context = {
            'data': input_data,
            'input': input_data,
            'True': True,
            'False': False,
            'None': None
        }
        
        try:
            # Convert template-style condition to Python
            python_condition = condition.replace('{{', '').replace('}}', '')
            python_condition = python_condition.replace(' === ', ' == ')
            python_condition = python_condition.replace(' !== ', ' != ')
            
            # Evaluate condition
            result = eval(python_condition, {"__builtins__": {}}, context)
            
            return {
                "success": True,
                "condition_result": bool(result),
                "result": {
                    "condition": condition,
                    "evaluated": bool(result),
                    "branch": "true" if result else "false"
                }
            }
        except Exception as e:
            logger.error(f"Condition evaluation failed: {str(e)}")
            return {"success": False, "error": f"Condition evaluation error: {str(e)}", "result": None}
    
    async def execute_flow_delay_block(self, block_config: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute flow.delay block - handles timing and delays"""
        delay_seconds = float(self._process_template(str(block_config.get('delay_seconds', 1)), input_data))
        
        logger.info(f"Executing delay: {delay_seconds} seconds")
        
        start_time = time.time()
        await asyncio.sleep(delay_seconds)
        actual_delay = time.time() - start_time
        
        return {
            "success": True,
            "result": {
                "requested_delay_seconds": delay_seconds,
                "actual_delay_seconds": actual_delay,
                "delay_completed_at": datetime.now().isoformat()
            }
        }
    
    async def execute_flow_start_block(self, block_config: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute flow.start block - handles workflow initialization"""
        flow_name = self._process_template(block_config.get('name', 'Unnamed Flow'), input_data)
        trigger_types = block_config.get('trigger_types', ['manual'])
        
        logger.info(f"Starting flow: {flow_name}")
        
        return {
            "success": True,
            "result": {
                "flow_name": flow_name,
                "trigger_types": trigger_types,
                "started_at": datetime.now().isoformat(),
                "flow_started": True
            }
        }
    
    async def execute_flow_end_block(self, block_config: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute flow.end block - handles workflow completion"""
        flow_name = self._process_template(block_config.get('name', 'Flow Complete'), input_data)
        
        logger.info(f"Completing flow: {flow_name}")
        
        return {
            "success": True,
            "result": {
                "flow_name": flow_name,
                "completed_at": datetime.now().isoformat(),
                "flow_completed": True,
                "execution_summary": {
                    "total_blocks": len(self.execution_history),
                    "successful_blocks": len([h for h in self.execution_history if h['success']]),
                    "failed_blocks": len([h for h in self.execution_history if not h['success']]),
                    "total_execution_time": sum([h['execution_time_ms'] for h in self.execution_history])
                }
            }
        }
    
    def _process_template(self, template: str, data: Dict[str, Any]) -> str:
        """Process template strings with data substitution"""
        if not isinstance(template, str):
            return template
        
        def replace_template(match):
            key_path = match.group(1).strip()
            try:
                keys = key_path.split('.')
                value = data
                for key in keys:
                    if isinstance(value, dict) and key in value:
                        value = value[key]
                    elif isinstance(value, list) and key.isdigit():
                        value = value[int(key)]
                    else:
                        return match.group(0)
                return str(value)
            except:
                return match.group(0)
        
        return re.sub(r'{{([^}]+)}}', replace_template, template)
    
    async def _get_connection(self, target: str, connection_method: str, config: Dict[str, Any]):
        """Get connection for target system"""
        # This would integrate with the actual connection management system
        # For now, return a mock connection
        return MockConnection(target, connection_method, config)
    
    async def _get_http_connection(self, url: str, config: Dict[str, Any]):
        """Get HTTP connection"""
        return MockHTTPConnection(url, config)
    
    async def _get_notification_connection(self, notification_type: str, config: Dict[str, Any]):
        """Get notification service connection"""
        return MockNotificationConnection(notification_type, config)


class MockConnection:
    """Mock connection for demonstration"""
    
    def __init__(self, target: str, connection_method: str, config: Dict[str, Any]):
        self.target = target
        self.connection_method = connection_method
        self.config = config
    
    async def execute_command(self, command: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Mock command execution"""
        # Simulate different command outputs
        if 'echo' in command.lower():
            stdout = command.replace('echo ', '').strip("'\"")
            stderr = ""
            exit_code = 0
        elif 'tasklist' in command.lower():
            stdout = "\"Image Name\",\"PID\",\"Session Name\",\"Session#\",\"Mem Usage\"\\n\"MyApplication.exe\",\"1234\",\"Console\",\"1\",\"25,600 K\""
            stderr = ""
            exit_code = 0
        elif 'systemctl status' in command.lower():
            stdout = "● nginx.service - A high performance web server\\n   Active: active (running) since Mon 2023-01-01 10:00:00 UTC"
            stderr = ""
            exit_code = 0
        else:
            stdout = f"Simulated execution of: {command}"
            stderr = ""
            exit_code = 0
        
        return {
            "stdout": stdout,
            "stderr": stderr,
            "exit_code": exit_code,
            "execution_time": 50
        }


class MockHTTPConnection:
    """Mock HTTP connection for demonstration"""
    
    def __init__(self, url: str, config: Dict[str, Any]):
        self.url = url
        self.config = config
    
    async def execute_request(self, method: str, url: str, headers: Dict[str, str], body: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Mock HTTP request execution"""
        if 'axis-cgi' in url:
            response_data = "OK"
            status_code = 200
        elif 'httpbin.org' in url:
            response_data = '{"slideshow": {"title": "Sample Slide Show"}}'
            status_code = 200
        else:
            response_data = '{"status": "ok", "message": "simulated response"}'
            status_code = 200
        
        return {
            "status_code": status_code,
            "data": response_data,
            "url": url,
            "method": method,
            "execution_time": 100
        }


class MockNotificationConnection:
    """Mock notification connection for demonstration"""
    
    def __init__(self, notification_type: str, config: Dict[str, Any]):
        self.notification_type = notification_type
        self.config = config
    
    async def send_notification(self, notification_type: str, recipients: List[str], subject: str, message: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Mock notification sending"""
        return {
            "message_id": f"msg_{int(time.time())}",
            "sent_at": datetime.now().isoformat(),
            "status": "sent"
        }


# Generic block definitions for the step library system
GENERIC_BLOCKS = {
    "action.command": {
        "name": "Execute Command",
        "category": "Actions",
        "description": "Execute commands via SSH, WinRM, local, Docker, or Kubernetes",
        "icon": "terminal",
        "color": "#1F2937",
        "inputs": [
            {"name": "trigger", "type": "flow", "required": True, "label": "Execute"},
            {"name": "command", "type": "data", "dataType": "string", "required": False, "label": "Command Override"},
            {"name": "arguments", "type": "data", "dataType": "array", "required": False, "label": "Arguments"}
        ],
        "outputs": [
            {"name": "success", "type": "flow", "label": "Success"},
            {"name": "error", "type": "flow", "label": "Error"},
            {"name": "result", "type": "data", "dataType": "object", "label": "Command Result"}
        ],
        "config_schema": {
            "type": "object",
            "required": ["target"],
            "properties": {
                "target": {
                    "type": "string",
                    "ui_component": "target_selector",
                    "description": "Target system to execute command on"
                },
                "connection_method": {
                    "enum": ["auto", "ssh", "winrm", "local", "docker", "kubernetes"],
                    "default": "auto",
                    "description": "How to connect to the target system"
                },
                "command": {
                    "type": "string",
                    "default": "",
                    "description": "Command to execute",
                    "ui_component": "command_editor"
                },
                "timeout_seconds": {"type": "integer", "default": 60}
            }
        }
    },
    
    "action.http_request": {
        "name": "HTTP Request",
        "category": "Actions",
        "description": "Make HTTP requests to REST APIs, webhooks, and web services",
        "icon": "globe",
        "color": "#059669",
        "inputs": [
            {"name": "trigger", "type": "flow", "required": True, "label": "Execute"},
            {"name": "url", "type": "data", "dataType": "string", "required": False, "label": "URL Override"},
            {"name": "body", "type": "data", "dataType": "any", "required": False, "label": "Request Body"}
        ],
        "outputs": [
            {"name": "success", "type": "flow", "label": "Success"},
            {"name": "error", "type": "flow", "label": "Error"},
            {"name": "response", "type": "data", "dataType": "object", "label": "HTTP Response"}
        ],
        "config_schema": {
            "type": "object",
            "required": ["url"],
            "properties": {
                "method": {
                    "enum": ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"],
                    "default": "GET",
                    "description": "HTTP method"
                },
                "url": {
                    "type": "string",
                    "description": "Request URL"
                },
                "headers": {
                    "type": "object",
                    "default": {},
                    "description": "HTTP headers"
                },
                "body": {
                    "type": "object",
                    "default": {},
                    "description": "Request body"
                },
                "timeout_seconds": {"type": "integer", "default": 30}
            }
        }
    },
    
    "action.notification": {
        "name": "Send Notification",
        "category": "Actions",
        "description": "Send notifications via email, Slack, Teams, webhooks, etc.",
        "icon": "bell",
        "color": "#DC2626",
        "inputs": [
            {"name": "trigger", "type": "flow", "required": True, "label": "Send"},
            {"name": "message", "type": "data", "dataType": "string", "required": False, "label": "Message Override"},
            {"name": "recipients", "type": "data", "dataType": "array", "required": False, "label": "Recipients Override"}
        ],
        "outputs": [
            {"name": "success", "type": "flow", "label": "Success"},
            {"name": "error", "type": "flow", "label": "Error"},
            {"name": "result", "type": "data", "dataType": "object", "label": "Notification Result"}
        ],
        "config_schema": {
            "type": "object",
            "required": ["notification_type", "recipients"],
            "properties": {
                "notification_type": {
                    "enum": ["email", "slack", "teams", "webhook", "sms"],
                    "default": "email",
                    "description": "Type of notification"
                },
                "recipients": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Notification recipients"
                },
                "subject": {
                    "type": "string",
                    "default": "",
                    "description": "Notification subject"
                },
                "message": {
                    "type": "string",
                    "description": "Notification message"
                }
            }
        }
    },
    
    "data.transform": {
        "name": "Transform Data",
        "category": "Data",
        "description": "Transform and process data using Python scripts",
        "icon": "code",
        "color": "#7C3AED",
        "inputs": [
            {"name": "trigger", "type": "flow", "required": True, "label": "Transform"},
            {"name": "input_data", "type": "data", "dataType": "any", "required": False, "label": "Input Data"}
        ],
        "outputs": [
            {"name": "success", "type": "flow", "label": "Success"},
            {"name": "error", "type": "flow", "label": "Error"},
            {"name": "output_data", "type": "data", "dataType": "any", "label": "Output Data"}
        ],
        "config_schema": {
            "type": "object",
            "required": ["script"],
            "properties": {
                "script": {
                    "type": "string",
                    "description": "Python transformation script",
                    "ui_component": "code_editor"
                }
            }
        }
    },
    
    "logic.if": {
        "name": "Conditional Logic",
        "category": "Logic",
        "description": "Execute conditional logic and branching",
        "icon": "git-branch",
        "color": "#F59E0B",
        "inputs": [
            {"name": "trigger", "type": "flow", "required": True, "label": "Evaluate"},
            {"name": "condition_data", "type": "data", "dataType": "any", "required": False, "label": "Condition Data"}
        ],
        "outputs": [
            {"name": "true", "type": "flow", "label": "True"},
            {"name": "false", "type": "flow", "label": "False"},
            {"name": "result", "type": "data", "dataType": "object", "label": "Condition Result"}
        ],
        "config_schema": {
            "type": "object",
            "required": ["condition"],
            "properties": {
                "condition": {
                    "type": "string",
                    "description": "Condition to evaluate",
                    "ui_component": "condition_editor"
                }
            }
        }
    },
    
    "flow.delay": {
        "name": "Delay",
        "category": "Flow",
        "description": "Add delays and timing control to workflows",
        "icon": "clock",
        "color": "#6B7280",
        "inputs": [
            {"name": "trigger", "type": "flow", "required": True, "label": "Start Delay"},
            {"name": "delay_seconds", "type": "data", "dataType": "number", "required": False, "label": "Delay Override"}
        ],
        "outputs": [
            {"name": "complete", "type": "flow", "label": "Complete"},
            {"name": "result", "type": "data", "dataType": "object", "label": "Delay Result"}
        ],
        "config_schema": {
            "type": "object",
            "required": ["delay_seconds"],
            "properties": {
                "delay_seconds": {
                    "type": "number",
                    "default": 1,
                    "description": "Delay in seconds"
                }
            }
        }
    },
    
    "flow.start": {
        "name": "Flow Start",
        "category": "Flow",
        "description": "Start point for workflows with trigger configuration",
        "icon": "play",
        "color": "#10B981",
        "inputs": [],
        "outputs": [
            {"name": "start", "type": "flow", "label": "Start"},
            {"name": "trigger_data", "type": "data", "dataType": "object", "label": "Trigger Data"}
        ],
        "config_schema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "default": "Workflow",
                    "description": "Flow name"
                },
                "trigger_types": {
                    "type": "array",
                    "items": {"enum": ["manual", "scheduled", "webhook", "file_change", "api"]},
                    "default": ["manual"],
                    "description": "Trigger types"
                }
            }
        }
    },
    
    "flow.end": {
        "name": "Flow End",
        "category": "Flow",
        "description": "End point for workflows with execution summary",
        "icon": "stop",
        "color": "#EF4444",
        "inputs": [
            {"name": "trigger", "type": "flow", "required": True, "label": "Complete"},
            {"name": "final_data", "type": "data", "dataType": "any", "required": False, "label": "Final Data"}
        ],
        "outputs": [
            {"name": "summary", "type": "data", "dataType": "object", "label": "Execution Summary"}
        ],
        "config_schema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "default": "Flow Complete",
                    "description": "Completion message"
                }
            }
        }
    }
}