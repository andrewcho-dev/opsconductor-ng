"""
Enhanced Generic Blocks with Connection Method Support
Handles SSH, WinRM, local execution, and other connection types
"""

from typing import Dict, List, Any

# Enhanced generic action blocks with connection method support
ENHANCED_GENERIC_BLOCKS = {
    "action.command": {
        "name": "Execute Command",
        "category": "system",
        "description": "Execute commands via SSH, WinRM, or locally",
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
                    "ui_component": "command_editor"  # Special editor with syntax highlighting
                },
                "shell": {
                    "type": "string",
                    "default": "auto",
                    "enum": ["auto", "cmd", "powershell", "bash", "sh", "zsh"],
                    "description": "Shell to use for command execution"
                },
                "working_directory": {"type": "string", "default": ""},
                "environment_variables": {
                    "type": "object",
                    "default": {},
                    "ui_component": "key_value_editor"
                },
                "timeout_seconds": {"type": "integer", "default": 60},
                "run_as_user": {"type": "string", "default": ""},
                "capture_output": {"type": "boolean", "default": True},
                "capture_stderr": {"type": "boolean", "default": True},
                
                # SSH-specific options
                "ssh_options": {
                    "type": "object",
                    "properties": {
                        "port": {"type": "integer", "default": 22},
                        "key_file": {"type": "string", "default": ""},
                        "strict_host_key_checking": {"type": "boolean", "default": True},
                        "connection_timeout": {"type": "integer", "default": 10}
                    }
                },
                
                # WinRM-specific options
                "winrm_options": {
                    "type": "object",
                    "properties": {
                        "port": {"type": "integer", "default": 5985},
                        "use_ssl": {"type": "boolean", "default": False},
                        "ssl_port": {"type": "integer", "default": 5986},
                        "transport": {"enum": ["ntlm", "kerberos", "basic"], "default": "ntlm"},
                        "operation_timeout": {"type": "integer", "default": 60},
                        "read_timeout": {"type": "integer", "default": 90}
                    }
                },
                
                # Docker-specific options
                "docker_options": {
                    "type": "object",
                    "properties": {
                        "container_id": {"type": "string", "default": ""},
                        "image": {"type": "string", "default": ""},
                        "docker_host": {"type": "string", "default": ""},
                        "user": {"type": "string", "default": ""}
                    }
                },
                
                # Kubernetes-specific options
                "k8s_options": {
                    "type": "object",
                    "properties": {
                        "namespace": {"type": "string", "default": "default"},
                        "pod_name": {"type": "string", "default": ""},
                        "container_name": {"type": "string", "default": ""},
                        "kubeconfig_path": {"type": "string", "default": ""}
                    }
                }
            }
        }
    },
    
    "action.file_operation": {
        "name": "File Operation",
        "category": "files",
        "description": "File operations via SSH, WinRM, SMB, or locally",
        "icon": "file",
        "color": "#059669",
        "inputs": [
            {"name": "trigger", "type": "flow", "required": True, "label": "Execute"},
            {"name": "source_path", "type": "data", "dataType": "string", "required": False, "label": "Source Path"},
            {"name": "destination_path", "type": "data", "dataType": "string", "required": False, "label": "Destination Path"},
            {"name": "file_content", "type": "data", "dataType": "any", "required": False, "label": "File Content"}
        ],
        "outputs": [
            {"name": "success", "type": "flow", "label": "Success"},
            {"name": "error", "type": "flow", "label": "Error"},
            {"name": "result", "type": "data", "dataType": "any", "label": "Operation Result"}
        ],
        "config_schema": {
            "type": "object",
            "required": ["target", "operation"],
            "properties": {
                "target": {
                    "type": "string",
                    "ui_component": "target_selector",
                    "description": "Target system for file operation"
                },
                "connection_method": {
                    "enum": ["auto", "ssh", "winrm", "smb", "ftp", "sftp", "local"],
                    "default": "auto",
                    "description": "How to connect for file operations"
                },
                "operation": {
                    "enum": ["read", "write", "copy", "move", "delete", "list", "exists", "create_directory", "get_info", "set_permissions"],
                    "default": "read",
                    "description": "File operation to perform"
                },
                "source_path": {"type": "string", "description": "Source file/directory path"},
                "destination_path": {"type": "string", "description": "Destination path (for copy/move)"},
                "create_directories": {"type": "boolean", "default": False},
                "overwrite_existing": {"type": "boolean", "default": False},
                "file_permissions": {"type": "string", "default": "644"},
                "encoding": {"type": "string", "default": "utf-8", "enum": ["utf-8", "ascii", "binary"]},
                "recursive": {"type": "boolean", "default": False},
                
                # SMB-specific options
                "smb_options": {
                    "type": "object",
                    "properties": {
                        "share_name": {"type": "string", "default": ""},
                        "domain": {"type": "string", "default": ""},
                        "smb_version": {"enum": ["1", "2", "3"], "default": "3"}
                    }
                },
                
                # FTP/SFTP options
                "ftp_options": {
                    "type": "object",
                    "properties": {
                        "port": {"type": "integer", "default": 21},
                        "passive_mode": {"type": "boolean", "default": True},
                        "binary_mode": {"type": "boolean", "default": False}
                    }
                }
            }
        }
    },
    
    "action.service_control": {
        "name": "Service Control",
        "category": "system", 
        "description": "Control services via SSH, WinRM, or locally",
        "icon": "settings",
        "color": "#DC2626",
        "inputs": [
            {"name": "trigger", "type": "flow", "required": True, "label": "Execute"},
            {"name": "service_name", "type": "data", "dataType": "string", "required": False, "label": "Service Name Override"}
        ],
        "outputs": [
            {"name": "success", "type": "flow", "label": "Success"},
            {"name": "error", "type": "flow", "label": "Error"},
            {"name": "service_status", "type": "data", "dataType": "object", "label": "Service Status"}
        ],
        "config_schema": {
            "type": "object",
            "required": ["target", "service_name", "action"],
            "properties": {
                "target": {
                    "type": "string",
                    "ui_component": "target_selector",
                    "description": "Target system with the service"
                },
                "connection_method": {
                    "enum": ["auto", "ssh", "winrm", "local"],
                    "default": "auto",
                    "description": "How to connect to manage services"
                },
                "service_name": {
                    "type": "string",
                    "description": "Name of the service to control"
                },
                "action": {
                    "enum": ["start", "stop", "restart", "reload", "status", "enable", "disable", "list"],
                    "default": "status",
                    "description": "Action to perform on the service"
                },
                "service_manager": {
                    "enum": ["auto", "systemd", "service", "sc", "net", "docker", "kubernetes"],
                    "default": "auto",
                    "description": "Service management system to use"
                },
                "wait_for_status": {
                    "enum": ["", "running", "stopped"],
                    "default": "",
                    "description": "Wait for service to reach this status"
                },
                "timeout_seconds": {"type": "integer", "default": 30}
            }
        }
    }
}

# Target system definitions with connection details
TARGET_SYSTEM_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": "string", "description": "Friendly name for the target"},
        "hostname": {"type": "string", "description": "IP address or hostname"},
        "os_type": {"enum": ["windows", "linux", "macos", "auto"], "default": "auto"},
        "default_connection": {"enum": ["ssh", "winrm", "local"], "default": "auto"},
        
        # Authentication
        "auth_method": {"enum": ["password", "key", "kerberos", "certificate"], "default": "password"},
        "username": {"type": "string"},
        "password": {"type": "string", "ui_component": "password"},
        "private_key": {"type": "string", "ui_component": "file_selector"},
        "certificate": {"type": "string", "ui_component": "file_selector"},
        
        # SSH settings
        "ssh_port": {"type": "integer", "default": 22},
        "ssh_key_file": {"type": "string"},
        
        # WinRM settings  
        "winrm_port": {"type": "integer", "default": 5985},
        "winrm_ssl_port": {"type": "integer", "default": 5986},
        "winrm_use_ssl": {"type": "boolean", "default": False},
        "winrm_transport": {"enum": ["ntlm", "kerberos", "basic"], "default": "ntlm"},
        
        # Connection pooling and caching
        "connection_timeout": {"type": "integer", "default": 10},
        "max_connections": {"type": "integer", "default": 5},
        "connection_cache_ttl": {"type": "integer", "default": 300}
    }
}