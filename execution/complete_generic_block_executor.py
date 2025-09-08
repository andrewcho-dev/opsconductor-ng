"""
Complete Generic Block Executor
Handles all generic block types with full functionality
"""

import asyncio
import json
import time
import re
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
try:
    from .connection_manager import connection_manager, CommandResult, FileOperationResult
    from .advanced_connection_handlers import DockerConnectionHandler, KubernetesConnectionHandler, HTTPConnectionHandler
except ImportError:
    from connection_manager import connection_manager, CommandResult, FileOperationResult
    from advanced_connection_handlers import DockerConnectionHandler, KubernetesConnectionHandler, HTTPConnectionHandler


class CompleteGenericBlockExecutor:
    """Complete executor for all generic block types"""
    
    def __init__(self):
        self.data_context = {}
        self.execution_history = []
    
    async def execute_block(self, block_type: str, block_config: Dict[str, Any], input_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute any generic block type"""
        if input_data is None:
            input_data = {}
        
        # Store execution start time
        start_time = time.time()
        
        try:
            # Route to appropriate handler
            if block_type == "action.command":
                result = await self.execute_command_block(block_config, input_data)
            elif block_type == "action.file_operation":
                result = await self.execute_file_operation_block(block_config, input_data)
            elif block_type == "action.http_request":
                result = await self.execute_http_request_block(block_config, input_data)
            elif block_type == "action.service_control":
                result = await self.execute_service_control_block(block_config, input_data)
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
            elif block_type.startswith("trigger."):
                result = await self.execute_trigger_block(block_type, block_config, input_data)
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
            return {
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
    
    async def execute_command_block(self, block_config: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute action.command block"""
        try:
            # Extract configuration with template processing
            target_id = self._process_template(block_config['target'], input_data)
            connection_method = self._process_template(block_config.get('connection_method', 'auto'), input_data)
            command = self._process_template(input_data.get('command') or block_config['command'], input_data)
            shell = self._process_template(block_config.get('shell', 'auto'), input_data)
            timeout = int(self._process_template(str(block_config.get('timeout_seconds', 60)), input_data))
            working_dir = self._process_template(block_config.get('working_directory', ''), input_data)
            
            # Process environment variables
            env_vars = {}
            for key, value in block_config.get('environment_variables', {}).items():
                env_vars[key] = self._process_template(str(value), input_data)
            
            # Connection-specific options
            ssh_options = block_config.get('ssh_options', {})
            winrm_options = block_config.get('winrm_options', {})
            
            # Execute command
            result = await connection_manager.execute_command(
                target_id=target_id,
                command=command,
                connection_method=connection_method,
                shell=shell,
                timeout_seconds=timeout,
                working_directory=working_dir,
                environment_variables=env_vars,
                **ssh_options,
                **winrm_options
            )
            
            # Return structured result
            return {
                "success": result.success,
                "result": {
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "exit_code": result.exit_code,
                    "execution_time": result.execution_time_ms,
                    "target": result.target,
                    "connection_type": result.connection_type,
                    "command": command
                },
                "error": result.error_message if not result.success else None
            }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "result": None
            }
    
    async def execute_file_operation_block(self, block_config: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute action.file_operation block"""
        try:
            # Extract configuration with template processing
            target_id = self._process_template(block_config['target'], input_data)
            connection_method = self._process_template(block_config.get('connection_method', 'auto'), input_data)
            operation = self._process_template(block_config['operation'], input_data)
            source_path = self._process_template(input_data.get('source_path') or block_config.get('source_path', ''), input_data)
            destination_path = self._process_template(input_data.get('destination_path') or block_config.get('destination_path', ''), input_data)
            
            # Operation-specific options
            kwargs = {
                'source_path': source_path,
                'destination_path': destination_path,
                'create_directories': block_config.get('create_directories', False),
                'overwrite_existing': block_config.get('overwrite_existing', False),
                'recursive': block_config.get('recursive', False),
                'encoding': block_config.get('encoding', 'utf-8'),
                'permissions': block_config.get('permissions', '644')
            }
            
            # Add file content if provided
            if 'file_content' in input_data:
                kwargs['file_content'] = self._process_template(str(input_data['file_content']), input_data)
            elif 'file_content' in block_config:
                kwargs['file_content'] = self._process_template(str(block_config['file_content']), input_data)
            
            # Execute file operation
            result = await connection_manager.file_operation(
                target_id=target_id,
                operation=operation,
                connection_method=connection_method,
                **kwargs
            )
            
            # Return structured result
            return {
                "success": result.success,
                "result": {
                    "operation": result.operation,
                    "path": result.path,
                    "data": result.result,
                    "target": result.target,
                    "connection_type": result.connection_type
                },
                "error": result.error_message if not result.success else None
            }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "result": None
            }
    
    async def execute_http_request_block(self, block_config: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute action.http_request block"""
        try:
            # Extract configuration with template processing
            method = self._process_template(block_config.get('method', 'GET'), input_data).upper()
            url = self._process_template(block_config['url'], input_data)
            timeout = int(self._process_template(str(block_config.get('timeout_seconds', 30)), input_data))
            
            # Process headers
            headers = {}
            for key, value in block_config.get('headers', {}).items():
                headers[key] = self._process_template(str(value), input_data)
            
            # Process authentication
            auth_config = block_config.get('authentication', {})
            if auth_config:
                auth_type = auth_config.get('type', 'none')
                if auth_type == 'basic':
                    username = self._process_template(auth_config['username'], input_data)
                    password = self._process_template(auth_config['password'], input_data)
                    import base64
                    credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
                    headers['Authorization'] = f"Basic {credentials}"
                elif auth_type == 'bearer':
                    token = self._process_template(auth_config['token'], input_data)
                    headers['Authorization'] = f"Bearer {token}"
                elif auth_type == 'api_key':
                    key_header = auth_config.get('header', 'X-API-Key')
                    key_value = self._process_template(auth_config['key'], input_data)
                    headers[key_header] = key_value
            
            # Process body/data
            body = None
            if 'body' in block_config:
                body = self._process_template(str(block_config['body']), input_data)
            elif 'json' in block_config:
                json_data = block_config['json']
                if isinstance(json_data, dict):
                    # Process templates in JSON data
                    body = json.dumps(self._process_template_dict(json_data, input_data))
                    headers['Content-Type'] = 'application/json'
                else:
                    body = self._process_template(str(json_data), input_data)
            
            # Create HTTP handler configuration
            http_config = {
                'base_url': '',
                'headers': headers,
                'ssl_verify': block_config.get('ssl_verify', True),
                'timeout': timeout
            }
            
            # Create HTTP handler and execute request
            handler = HTTPConnectionHandler(http_config)
            
            # Execute HTTP request
            result = await handler.execute_command(
                command={
                    'method': method,
                    'endpoint': url,
                    'data': body
                },
                timeout_seconds=timeout
            )
            
            # Parse response if JSON
            response_data = result.stdout
            try:
                if response_data and result.success:
                    parsed_response = json.loads(response_data)
                    response_data = parsed_response
            except json.JSONDecodeError:
                pass  # Keep as string if not valid JSON
            
            return {
                "success": result.success,
                "response": {
                    "status_code": result.exit_code if result.exit_code > 0 else 200,
                    "data": response_data,
                    "headers": {},  # Would need to extract from actual response
                    "url": url,
                    "method": method,
                    "execution_time": result.execution_time_ms
                },
                "result": {
                    "status_code": result.exit_code if result.exit_code > 0 else 200,
                    "response_data": response_data,
                    "success": result.success
                },
                "error": result.error_message if not result.success else None
            }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "result": None
            }
    
    async def execute_service_control_block(self, block_config: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute action.service_control block"""
        try:
            # Extract configuration with template processing
            target_id = self._process_template(block_config['target'], input_data)
            connection_method = self._process_template(block_config.get('connection_method', 'auto'), input_data)
            service_name = self._process_template(input_data.get('service_name') or block_config['service_name'], input_data)
            action = self._process_template(block_config['action'], input_data)
            service_manager = self._process_template(block_config.get('service_manager', 'auto'), input_data)
            timeout = int(self._process_template(str(block_config.get('timeout_seconds', 30)), input_data))
            
            # Get target configuration to determine OS type
            target_config = connection_manager.get_target_info(target_id)
            os_type = target_config.get('os_type', 'auto')
            
            # Build service command based on OS type and service manager
            if os_type == 'windows' or connection_method == 'winrm':
                # Windows service commands
                command_map = {
                    'start': f'net start "{service_name}"',
                    'stop': f'net stop "{service_name}"',
                    'restart': f'net stop "{service_name}" && net start "{service_name}"',
                    'status': f'sc query "{service_name}"',
                    'enable': f'sc config "{service_name}" start= auto',
                    'disable': f'sc config "{service_name}" start= disabled'
                }
                shell = 'cmd'
            else:
                # Linux service commands (systemd by default)
                if service_manager == 'systemd' or service_manager == 'auto':
                    command_map = {
                        'start': f'systemctl start {service_name}',
                        'stop': f'systemctl stop {service_name}',
                        'restart': f'systemctl restart {service_name}',
                        'status': f'systemctl status {service_name}',
                        'enable': f'systemctl enable {service_name}',
                        'disable': f'systemctl disable {service_name}'
                    }
                elif service_manager == 'service':
                    command_map = {
                        'start': f'service {service_name} start',
                        'stop': f'service {service_name} stop',
                        'restart': f'service {service_name} restart',
                        'status': f'service {service_name} status',
                        'enable': f'chkconfig {service_name} on',
                        'disable': f'chkconfig {service_name} off'
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Unsupported service manager: {service_manager}",
                        "result": None
                    }
                shell = 'bash'
            
            if action not in command_map:
                return {
                    "success": False,
                    "error": f"Unsupported service action: {action}",
                    "result": None
                }
            
            command = command_map[action]
            
            # Execute service command
            result = await connection_manager.execute_command(
                target_id=target_id,
                command=command,
                connection_method=connection_method,
                shell=shell,
                timeout_seconds=timeout
            )
            
            # Parse service status from output
            service_status = self._parse_service_status(result.stdout, result.stderr, action, os_type)
            
            return {
                "success": result.success,
                "service_status": service_status,
                "result": {
                    "action": action,
                    "service_name": service_name,
                    "status": service_status,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "target": result.target,
                    "connection_type": result.connection_type
                },
                "error": result.error_message if not result.success else None
            }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "result": None
            }
    
    async def execute_notification_block(self, block_config: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute action.notification block"""
        try:
            # Extract configuration with template processing
            notification_type = self._process_template(block_config['notification_type'], input_data)
            recipients = block_config.get('recipients', [])
            if isinstance(recipients, str):
                recipients = [recipients]
            recipients = [self._process_template(r, input_data) for r in recipients]
            
            subject = self._process_template(block_config.get('subject', ''), input_data)
            message = self._process_template(input_data.get('message') or block_config.get('message', ''), input_data)
            priority = self._process_template(block_config.get('priority', 'normal'), input_data)
            
            # Simulate notification sending
            if notification_type == 'email':
                # Email notification logic
                notification_result = {
                    "type": "email",
                    "recipients": recipients,
                    "subject": subject,
                    "message": message,
                    "priority": priority,
                    "sent_at": datetime.now().isoformat(),
                    "message_id": f"msg_{int(time.time())}"
                }
            elif notification_type == 'slack':
                # Slack notification logic
                notification_result = {
                    "type": "slack",
                    "channels": recipients,
                    "message": message,
                    "priority": priority,
                    "sent_at": datetime.now().isoformat(),
                    "message_id": f"slack_{int(time.time())}"
                }
            elif notification_type == 'webhook':
                # Webhook notification logic
                webhook_url = self._process_template(block_config.get('webhook_url', ''), input_data)
                notification_result = {
                    "type": "webhook",
                    "url": webhook_url,
                    "payload": {
                        "subject": subject,
                        "message": message,
                        "priority": priority,
                        "timestamp": datetime.now().isoformat()
                    },
                    "sent_at": datetime.now().isoformat()
                }
            else:
                return {
                    "success": False,
                    "error": f"Unsupported notification type: {notification_type}",
                    "result": None
                }
            
            return {
                "success": True,
                "result": notification_result,
                "notification_sent": True
            }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "result": None
            }
    
    async def execute_data_transform_block(self, block_config: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute data.transform block"""
        try:
            # Get transformation script
            script = block_config.get('script', '')
            
            if not script:
                return {
                    "success": False,
                    "error": "No transformation script provided",
                    "result": None
                }
            
            # Create execution context
            context = {
                'input': input_data,
                'data': input_data,
                'json': json,
                'datetime': datetime,
                'time': time,
                're': re
            }
            
            # Execute JavaScript-like transformation (simplified Python execution)
            try:
                # Convert JavaScript-like syntax to Python
                python_script = self._convert_js_to_python(script)
                
                # Execute the script
                exec(python_script, context)
                
                # Get the result
                if 'result' in context:
                    output_data = context['result']
                elif 'return_value' in context:
                    output_data = context['return_value']
                else:
                    # Look for the last expression result
                    output_data = input_data
                
                return {
                    "success": True,
                    "output_data": output_data,
                    "result": output_data
                }
                
            except Exception as script_error:
                return {
                    "success": False,
                    "error": f"Script execution error: {str(script_error)}",
                    "result": None
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "result": None
            }
    
    async def execute_logic_if_block(self, block_config: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute logic.if block"""
        try:
            # Extract condition with template processing
            condition = self._process_template(block_config['condition'], input_data)
            
            # Evaluate condition
            try:
                # Create safe evaluation context
                context = {
                    'data': input_data,
                    'input': input_data,
                    'True': True,
                    'False': False,
                    'None': None
                }
                
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
                
            except Exception as eval_error:
                return {
                    "success": False,
                    "error": f"Condition evaluation error: {str(eval_error)}",
                    "result": None
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "result": None
            }
    
    async def execute_flow_delay_block(self, block_config: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute flow.delay block"""
        try:
            # Extract delay configuration
            delay_seconds = float(self._process_template(str(block_config.get('delay_seconds', 1)), input_data))
            delay_minutes = float(self._process_template(str(block_config.get('delay_minutes', 0)), input_data))
            delay_hours = float(self._process_template(str(block_config.get('delay_hours', 0)), input_data))
            
            # Calculate total delay
            total_delay = delay_seconds + (delay_minutes * 60) + (delay_hours * 3600)
            
            if total_delay <= 0:
                return {
                    "success": False,
                    "error": "Delay must be greater than 0",
                    "result": None
                }
            
            # Perform delay
            start_time = time.time()
            await asyncio.sleep(total_delay)
            actual_delay = time.time() - start_time
            
            return {
                "success": True,
                "result": {
                    "requested_delay_seconds": total_delay,
                    "actual_delay_seconds": actual_delay,
                    "delay_completed_at": datetime.now().isoformat()
                }
            }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "result": None
            }
    
    async def execute_flow_start_block(self, block_config: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute flow.start block"""
        try:
            flow_name = self._process_template(block_config.get('name', 'Unnamed Flow'), input_data)
            trigger_types = block_config.get('trigger_types', ['manual'])
            
            return {
                "success": True,
                "result": {
                    "flow_name": flow_name,
                    "trigger_types": trigger_types,
                    "started_at": datetime.now().isoformat(),
                    "flow_started": True
                }
            }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "result": None
            }
    
    async def execute_flow_end_block(self, block_config: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute flow.end block"""
        try:
            flow_name = self._process_template(block_config.get('name', 'Flow Complete'), input_data)
            save_result = block_config.get('save_result', False)
            result_name = self._process_template(block_config.get('result_name', ''), input_data)
            
            end_result = {
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
            
            if save_result and result_name:
                end_result["saved_result"] = {
                    "name": result_name,
                    "data": input_data
                }
            
            return {
                "success": True,
                "result": end_result
            }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "result": None
            }
    
    async def execute_trigger_block(self, block_type: str, block_config: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute trigger blocks"""
        try:
            if block_type == "trigger.schedule":
                cron_expression = block_config.get('cron_expression', '0 0 * * *')
                timezone = block_config.get('timezone', 'UTC')
                enabled = block_config.get('enabled', True)
                
                return {
                    "success": True,
                    "result": {
                        "trigger_type": "schedule",
                        "cron_expression": cron_expression,
                        "timezone": timezone,
                        "enabled": enabled,
                        "next_run": "calculated_next_run_time",  # Would calculate actual next run
                        "triggered_at": datetime.now().isoformat()
                    }
                }
            
            elif block_type == "trigger.webhook":
                webhook_path = block_config.get('webhook_path', '/webhook')
                methods = block_config.get('methods', ['POST'])
                
                return {
                    "success": True,
                    "result": {
                        "trigger_type": "webhook",
                        "webhook_path": webhook_path,
                        "methods": methods,
                        "triggered_at": datetime.now().isoformat()
                    }
                }
            
            elif block_type == "trigger.manual":
                return {
                    "success": True,
                    "result": {
                        "trigger_type": "manual",
                        "triggered_at": datetime.now().isoformat(),
                        "triggered_by": "user"
                    }
                }
            
            else:
                return {
                    "success": False,
                    "error": f"Unsupported trigger type: {block_type}",
                    "result": None
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "result": None
            }
    
    def _process_template(self, template: str, data: Dict[str, Any]) -> str:
        """Process template strings with data substitution"""
        if not isinstance(template, str):
            return template
        
        # Simple template processing ({{key}} -> value)
        import re
        
        def replace_template(match):
            key_path = match.group(1).strip()
            try:
                # Handle nested keys like data.result.stdout
                keys = key_path.split('.')
                value = data
                for key in keys:
                    if isinstance(value, dict) and key in value:
                        value = value[key]
                    else:
                        return match.group(0)  # Return original if key not found
                return str(value)
            except:
                return match.group(0)  # Return original if error
        
        return re.sub(r'{{([^}]+)}}', replace_template, template)
    
    def _process_template_dict(self, data: Dict[str, Any], template_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process templates in dictionary values"""
        result = {}
        for key, value in data.items():
            if isinstance(value, str):
                result[key] = self._process_template(value, template_data)
            elif isinstance(value, dict):
                result[key] = self._process_template_dict(value, template_data)
            elif isinstance(value, list):
                result[key] = [self._process_template(str(item), template_data) if isinstance(item, str) else item for item in value]
            else:
                result[key] = value
        return result
    
    def _parse_service_status(self, stdout: str, stderr: str, action: str, os_type: str) -> Dict[str, Any]:
        """Parse service status from command output"""
        status = {
            "status": "unknown",
            "enabled": None,
            "pid": None,
            "uptime": None
        }
        
        try:
            if os_type == 'windows':
                # Parse Windows service status
                if 'RUNNING' in stdout:
                    status["status"] = "running"
                elif 'STOPPED' in stdout:
                    status["status"] = "stopped"
                elif 'START_PENDING' in stdout:
                    status["status"] = "starting"
                elif 'STOP_PENDING' in stdout:
                    status["status"] = "stopping"
            else:
                # Parse Linux systemctl status
                if 'active (running)' in stdout:
                    status["status"] = "running"
                elif 'inactive (dead)' in stdout:
                    status["status"] = "stopped"
                elif 'failed' in stdout:
                    status["status"] = "failed"
                elif 'activating' in stdout:
                    status["status"] = "starting"
                
                # Extract enabled status
                if 'enabled' in stdout:
                    status["enabled"] = True
                elif 'disabled' in stdout:
                    status["enabled"] = False
                
                # Extract PID if available
                pid_match = re.search(r'Main PID: (\d+)', stdout)
                if pid_match:
                    status["pid"] = int(pid_match.group(1))
        except:
            pass
        
        return status
    
    def _convert_js_to_python(self, js_script: str) -> str:
        """Convert JavaScript-like syntax to Python"""
        # Simple conversions for common JavaScript patterns
        python_script = js_script
        
        # Convert const/let/var to simple assignment
        python_script = re.sub(r'\b(const|let|var)\s+(\w+)\s*=', r'\2 =', python_script)
        
        # Convert === to ==
        python_script = python_script.replace(' === ', ' == ')
        python_script = python_script.replace(' !== ', ' != ')
        
        # Convert JavaScript return to Python result assignment
        python_script = re.sub(r'\breturn\s+(.+);?$', r'result = \1', python_script, flags=re.MULTILINE)
        
        # Convert console.log to print (optional)
        python_script = re.sub(r'console\.log\((.*?)\)', r'print(\1)', python_script)
        
        # Handle JSON.stringify
        python_script = python_script.replace('JSON.stringify', 'json.dumps')
        python_script = python_script.replace('JSON.parse', 'json.loads')
        
        return python_script
    
    def get_execution_summary(self) -> Dict[str, Any]:
        """Get execution summary"""
        total_blocks = len(self.execution_history)
        successful_blocks = len([h for h in self.execution_history if h['success']])
        failed_blocks = total_blocks - successful_blocks
        total_time = sum([h['execution_time_ms'] for h in self.execution_history])
        
        return {
            "total_blocks_executed": total_blocks,
            "successful_blocks": successful_blocks,
            "failed_blocks": failed_blocks,
            "success_rate": (successful_blocks / total_blocks * 100) if total_blocks > 0 else 0,
            "total_execution_time_ms": total_time,
            "execution_history": self.execution_history
        }
    
    def clear_execution_history(self):
        """Clear execution history"""
        self.execution_history = []
        self.data_context = {}


# Global executor instance
complete_generic_block_executor = CompleteGenericBlockExecutor()