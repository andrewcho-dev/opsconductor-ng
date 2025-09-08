"""
Block Definitions for Phase 2 Implementation
Defines all available block types with their inputs, outputs, and configuration schemas
"""

from typing import Dict, List, Any

# Flow Control Blocks - No target needed
FLOW_CONTROL_BLOCKS = {
    "flow.start": {
        "name": "Start",
        "category": "flow-control",
        "description": "Workflow entry point with configurable triggers",
        "icon": "play-circle",
        "color": "#10B981",
        "inputs": [
            {"name": "schedule_trigger", "type": "flow", "required": False, "label": "Schedule"},
            {"name": "webhook_trigger", "type": "flow", "required": False, "label": "Webhook"},
            {"name": "manual_trigger", "type": "flow", "required": False, "label": "Manual"},
            {"name": "event_trigger", "type": "flow", "required": False, "label": "Event"},
            {"name": "trigger_data", "type": "data", "dataType": "object", "required": False, "label": "Trigger Data"}
        ],
        "outputs": [
            {"name": "trigger", "type": "flow", "label": "Start"},
            {"name": "context", "type": "data", "dataType": "object", "label": "Context"},
            {"name": "trigger_info", "type": "data", "dataType": "object", "label": "Trigger Info"}
        ],
        "config_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "default": "Workflow Start"},
                "description": {"type": "string", "default": ""},
                "trigger_types": {
                    "type": "array",
                    "items": {"enum": ["manual", "schedule", "webhook", "event", "file_watch", "service_monitor"]},
                    "default": ["manual"],
                    "description": "Types of triggers that can start this workflow"
                },
                "schedule_config": {
                    "type": "object",
                    "properties": {
                        "cron_expression": {"type": "string", "default": "0 0 * * *"},
                        "timezone": {"type": "string", "default": "UTC"},
                        "enabled": {"type": "boolean", "default": False}
                    }
                },
                "webhook_config": {
                    "type": "object", 
                    "properties": {
                        "endpoint_path": {"type": "string", "default": "/webhook/workflow"},
                        "authentication": {"enum": ["none", "token", "signature"], "default": "token"},
                        "enabled": {"type": "boolean", "default": False}
                    }
                },
                "event_config": {
                    "type": "object",
                    "properties": {
                        "event_types": {
                            "type": "array",
                            "items": {"type": "string"},
                            "default": [],
                            "description": "Event types to listen for"
                        },
                        "filter_expression": {"type": "string", "default": ""},
                        "enabled": {"type": "boolean", "default": False}
                    }
                },
                "file_watch_config": {
                    "type": "object",
                    "properties": {
                        "watch_path": {"type": "string", "default": ""},
                        "file_pattern": {"type": "string", "default": "*"},
                        "watch_events": {
                            "type": "array",
                            "items": {"enum": ["created", "modified", "deleted"]},
                            "default": ["created"]
                        },
                        "enabled": {"type": "boolean", "default": False}
                    }
                },
                "service_monitor_config": {
                    "type": "object",
                    "properties": {
                        "target": {"type": "string", "ui_component": "target_selector"},
                        "service_name": {"type": "string"},
                        "monitor_events": {
                            "type": "array", 
                            "items": {"enum": ["stopped", "started", "failed", "restarted"]},
                            "default": ["stopped", "failed"]
                        },
                        "check_interval_sec": {"type": "integer", "default": 60},
                        "enabled": {"type": "boolean", "default": False}
                    }
                }
            }
        }
    },
    
    "flow.end": {
        "name": "End",
        "category": "flow-control", 
        "description": "Workflow completion point",
        "icon": "stop-circle",
        "color": "#EF4444",
        "inputs": [
            {"name": "trigger", "type": "flow", "required": True, "label": "Complete"},
            {"name": "result", "type": "data", "dataType": "any", "label": "Final Result"}
        ],
        "outputs": [],
        "config_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "default": "Workflow End"},
                "save_result": {"type": "boolean", "default": True},
                "result_name": {"type": "string", "default": "workflow_result"}
            }
        }
    },
    
    "logic.if": {
        "name": "If Condition",
        "category": "logic",
        "description": "Conditional branching based on data evaluation",
        "icon": "git-branch",
        "color": "#8B5CF6",
        "inputs": [
            {"name": "trigger", "type": "flow", "required": True, "label": "Check"},
            {"name": "data", "type": "data", "dataType": "any", "label": "Data to Evaluate"}
        ],
        "outputs": [
            {"name": "true", "type": "flow", "label": "True"},
            {"name": "false", "type": "flow", "label": "False"},
            {"name": "data_out", "type": "data", "dataType": "any", "label": "Pass-through Data"}
        ],
        "config_schema": {
            "type": "object",
            "properties": {
                "condition": {
                    "type": "string", 
                    "default": "{{data.status}} === 'success'",
                    "description": "JavaScript expression to evaluate"
                },
                "description": {"type": "string", "default": ""}
            }
        }
    },
    
    "data.transform": {
        "name": "Transform Data",
        "category": "data",
        "description": "Transform data using JavaScript expressions",
        "icon": "shuffle",
        "color": "#F59E0B",
        "inputs": [
            {"name": "trigger", "type": "flow", "required": True, "label": "Transform"},
            {"name": "input_data", "type": "data", "dataType": "any", "label": "Input Data"}
        ],
        "outputs": [
            {"name": "success", "type": "flow", "label": "Success"},
            {"name": "error", "type": "flow", "label": "Error"},
            {"name": "output_data", "type": "data", "dataType": "any", "label": "Transformed Data"}
        ],
        "config_schema": {
            "type": "object",
            "properties": {
                "script": {
                    "type": "string", 
                    "default": "return { ...input, processed_at: new Date().toISOString() };",
                    "description": "JavaScript transformation script"
                },
                "description": {"type": "string", "default": ""}
            }
        }
    },
    
    "flow.delay": {
        "name": "Wait/Delay",
        "category": "flow-control",
        "description": "Pause workflow execution for specified time",
        "icon": "clock",
        "color": "#6B7280",
        "inputs": [
            {"name": "trigger", "type": "flow", "required": True, "label": "Wait"}
        ],
        "outputs": [
            {"name": "continue", "type": "flow", "label": "Continue"}
        ],
        "config_schema": {
            "type": "object",
            "properties": {
                "delay_seconds": {"type": "integer", "default": 5, "minimum": 1},
                "description": {"type": "string", "default": ""}
            }
        }
    }
}

# Trigger Blocks - Connect to Start Block
TRIGGER_BLOCKS = {
    "trigger.schedule": {
        "name": "Schedule Trigger",
        "category": "triggers",
        "description": "Trigger workflow on a schedule",
        "icon": "calendar",
        "color": "#8B5CF6",
        "inputs": [],
        "outputs": [
            {"name": "trigger", "type": "flow", "label": "Scheduled"},
            {"name": "schedule_info", "type": "data", "dataType": "object", "label": "Schedule Info"}
        ],
        "config_schema": {
            "type": "object",
            "properties": {
                "cron_expression": {
                    "type": "string", 
                    "default": "0 9 * * MON-FRI",
                    "description": "Cron expression for schedule"
                },
                "timezone": {"type": "string", "default": "UTC"},
                "enabled": {"type": "boolean", "default": True},
                "description": {"type": "string", "default": ""}
            }
        }
    },
    
    "trigger.webhook": {
        "name": "Webhook Trigger", 
        "category": "triggers",
        "description": "Trigger workflow via HTTP webhook",
        "icon": "webhook",
        "color": "#F59E0B",
        "inputs": [],
        "outputs": [
            {"name": "trigger", "type": "flow", "label": "Webhook Called"},
            {"name": "webhook_data", "type": "data", "dataType": "object", "label": "Webhook Payload"}
        ],
        "config_schema": {
            "type": "object",
            "properties": {
                "endpoint_path": {
                    "type": "string",
                    "default": "/webhook/my-workflow",
                    "description": "Custom webhook endpoint path"
                },
                "authentication": {
                    "enum": ["none", "token", "signature"],
                    "default": "token",
                    "description": "Authentication method"
                },
                "auth_token": {"type": "string", "default": ""},
                "allowed_methods": {
                    "type": "array",
                    "items": {"enum": ["GET", "POST", "PUT", "PATCH"]},
                    "default": ["POST"]
                },
                "enabled": {"type": "boolean", "default": True},
                "description": {"type": "string", "default": ""}
            }
        }
    },
    
    "trigger.file_watch": {
        "name": "File Watcher",
        "category": "triggers", 
        "description": "Trigger when files are created/modified/deleted",
        "icon": "folder-search",
        "color": "#059669",
        "inputs": [],
        "outputs": [
            {"name": "trigger", "type": "flow", "label": "File Event"},
            {"name": "file_info", "type": "data", "dataType": "object", "label": "File Info"}
        ],
        "config_schema": {
            "type": "object",
            "required": ["target", "watch_path"],
            "properties": {
                "target": {
                    "type": "string",
                    "description": "Target server to watch files on",
                    "ui_component": "target_selector"
                },
                "watch_path": {
                    "type": "string",
                    "description": "Path to watch for file changes"
                },
                "file_pattern": {
                    "type": "string", 
                    "default": "*",
                    "description": "File pattern to match (e.g., *.txt, *.log)"
                },
                "watch_events": {
                    "type": "array",
                    "items": {"enum": ["created", "modified", "deleted", "moved"]},
                    "default": ["created", "modified"]
                },
                "recursive": {"type": "boolean", "default": False},
                "enabled": {"type": "boolean", "default": True},
                "description": {"type": "string", "default": ""}
            }
        }
    },
    
    "trigger.service_monitor": {
        "name": "Service Monitor",
        "category": "triggers",
        "description": "Trigger when service status changes",
        "icon": "activity",
        "color": "#DC2626",
        "inputs": [],
        "outputs": [
            {"name": "trigger", "type": "flow", "label": "Service Event"},
            {"name": "service_status", "type": "data", "dataType": "object", "label": "Service Status"}
        ],
        "config_schema": {
            "type": "object",
            "required": ["target", "service_name"],
            "properties": {
                "target": {
                    "type": "string",
                    "description": "Target server to monitor service on",
                    "ui_component": "target_selector"
                },
                "service_name": {
                    "type": "string",
                    "description": "Name of service to monitor"
                },
                "monitor_events": {
                    "type": "array",
                    "items": {"enum": ["stopped", "started", "failed", "restarted", "crashed"]},
                    "default": ["stopped", "failed"]
                },
                "check_interval_sec": {"type": "integer", "default": 60, "minimum": 10},
                "enabled": {"type": "boolean", "default": True},
                "description": {"type": "string", "default": ""}
            }
        }
    },
    
    "trigger.manual": {
        "name": "Manual Trigger",
        "category": "triggers",
        "description": "Manual workflow execution trigger",
        "icon": "play",
        "color": "#10B981",
        "inputs": [],
        "outputs": [
            {"name": "trigger", "type": "flow", "label": "Manual Start"},
            {"name": "user_info", "type": "data", "dataType": "object", "label": "User Info"}
        ],
        "config_schema": {
            "type": "object",
            "properties": {
                "require_confirmation": {"type": "boolean", "default": False},
                "confirmation_message": {"type": "string", "default": "Are you sure you want to run this workflow?"},
                "allowed_users": {
                    "type": "array",
                    "items": {"type": "string"},
                    "default": [],
                    "description": "Specific users allowed to trigger (empty = all users)"
                },
                "allowed_roles": {
                    "type": "array", 
                    "items": {"enum": ["admin", "operator", "user"]},
                    "default": ["admin", "operator"]
                },
                "description": {"type": "string", "default": ""}
            }
        }
    }
}

# System Operation Blocks - Target required
SYSTEM_OPERATION_BLOCKS = {
    "system.service_check": {
        "name": "Check Service Status",
        "category": "system",
        "description": "Check if a Windows/Linux service is running",
        "icon": "activity",
        "color": "#3B82F6",
        "inputs": [
            {"name": "trigger", "type": "flow", "required": True, "label": "Check"},
            {"name": "target_override", "type": "data", "dataType": "string", "label": "Target Override"}
        ],
        "outputs": [
            {"name": "success", "type": "flow", "label": "Success"},
            {"name": "error", "type": "flow", "label": "Error"},
            {"name": "service_info", "type": "data", "dataType": "object", "label": "Service Info"}
        ],
        "config_schema": {
            "type": "object",
            "required": ["target", "service_name"],
            "properties": {
                "target": {
                    "type": "string",
                    "description": "Target server to check service on",
                    "ui_component": "target_selector"
                },
                "service_name": {
                    "type": "string",
                    "description": "Name of the service to check",
                    "examples": ["IIS", "Apache2", "nginx", "SQL Server"]
                },
                "timeout_sec": {"type": "integer", "default": 30, "minimum": 5},
                "description": {"type": "string", "default": ""}
            }
        }
    },
    
    "system.service_control": {
        "name": "Control Service",
        "category": "system",
        "description": "Start, stop, restart, or manage a service",
        "icon": "power",
        "color": "#DC2626",
        "inputs": [
            {"name": "trigger", "type": "flow", "required": True, "label": "Execute"},
            {"name": "service_info", "type": "data", "dataType": "object", "label": "Service Info"},
            {"name": "target_override", "type": "data", "dataType": "string", "label": "Target Override"}
        ],
        "outputs": [
            {"name": "success", "type": "flow", "label": "Success"},
            {"name": "error", "type": "flow", "label": "Error"},
            {"name": "action_result", "type": "data", "dataType": "object", "label": "Action Result"}
        ],
        "config_schema": {
            "type": "object",
            "required": ["target", "action"],
            "properties": {
                "target": {
                    "type": "string",
                    "description": "Target server to control service on",
                    "ui_component": "target_selector"
                },
                "service_name": {
                    "type": "string",
                    "description": "Service name (can be overridden by input data)"
                },
                "action": {
                    "enum": ["start", "stop", "restart", "reload"],
                    "default": "restart",
                    "description": "Action to perform on the service"
                },
                "timeout_sec": {"type": "integer", "default": 60, "minimum": 10},
                "wait_for_status": {"type": "boolean", "default": True},
                "description": {"type": "string", "default": ""}
            }
        }
    },
    
    "system.command": {
        "name": "Execute Command",
        "category": "system",
        "description": "Execute shell command or PowerShell script",
        "icon": "terminal",
        "color": "#1F2937",
        "inputs": [
            {"name": "trigger", "type": "flow", "required": True, "label": "Execute"},
            {"name": "command_data", "type": "data", "dataType": "any", "label": "Command Data"}
        ],
        "outputs": [
            {"name": "success", "type": "flow", "label": "Success"},
            {"name": "error", "type": "flow", "label": "Error"},
            {"name": "command_result", "type": "data", "dataType": "object", "label": "Command Output"}
        ],
        "config_schema": {
            "type": "object",
            "required": ["target", "command"],
            "properties": {
                "target": {
                    "type": "string",
                    "description": "Target server to execute command on",
                    "ui_component": "target_selector"
                },
                "command": {
                    "type": "string",
                    "description": "Command or script to execute",
                    "ui_component": "code_editor"
                },
                "shell": {
                    "enum": ["powershell", "cmd", "bash", "sh"],
                    "default": "powershell",
                    "description": "Shell to use for execution"
                },
                "timeout_sec": {"type": "integer", "default": 300, "minimum": 10},
                "working_directory": {"type": "string", "default": ""},
                "description": {"type": "string", "default": ""}
            }
        }
    }
}

# File Operation Blocks - Target required
FILE_OPERATION_BLOCKS = {
    "file.copy": {
        "name": "Copy File",
        "category": "file",
        "description": "Copy file between local and remote systems",
        "icon": "copy",
        "color": "#059669",
        "inputs": [
            {"name": "trigger", "type": "flow", "required": True, "label": "Copy"},
            {"name": "file_info", "type": "data", "dataType": "object", "label": "File Info"}
        ],
        "outputs": [
            {"name": "success", "type": "flow", "label": "Success"},
            {"name": "error", "type": "flow", "label": "Error"},
            {"name": "copy_result", "type": "data", "dataType": "object", "label": "Copy Result"}
        ],
        "config_schema": {
            "type": "object",
            "required": ["target", "source_path", "destination_path"],
            "properties": {
                "target": {
                    "type": "string",
                    "description": "Target server for file operation",
                    "ui_component": "target_selector"
                },
                "source_path": {
                    "type": "string",
                    "description": "Source file path"
                },
                "destination_path": {
                    "type": "string", 
                    "description": "Destination file path"
                },
                "overwrite": {"type": "boolean", "default": True},
                "preserve_permissions": {"type": "boolean", "default": True},
                "timeout_sec": {"type": "integer", "default": 300},
                "description": {"type": "string", "default": ""}
            }
        }
    },
    
    "file.check": {
        "name": "Check File/Directory",
        "category": "file",
        "description": "Check if file or directory exists and get properties",
        "icon": "file-search",
        "color": "#7C3AED",
        "inputs": [
            {"name": "trigger", "type": "flow", "required": True, "label": "Check"},
            {"name": "path_data", "type": "data", "dataType": "string", "label": "Path Override"}
        ],
        "outputs": [
            {"name": "exists", "type": "flow", "label": "Exists"},
            {"name": "not_exists", "type": "flow", "label": "Not Exists"},
            {"name": "error", "type": "flow", "label": "Error"},
            {"name": "file_info", "type": "data", "dataType": "object", "label": "File Info"}
        ],
        "config_schema": {
            "type": "object",
            "required": ["target", "path"],
            "properties": {
                "target": {
                    "type": "string",
                    "description": "Target server to check file on",
                    "ui_component": "target_selector"
                },
                "path": {
                    "type": "string",
                    "description": "File or directory path to check"
                },
                "check_type": {
                    "enum": ["file", "directory", "any"],
                    "default": "any"
                },
                "timeout_sec": {"type": "integer", "default": 30},
                "description": {"type": "string", "default": ""}
            }
        }
    }
}

# Logging/Output Blocks - May or may not need target
LOGGING_BLOCKS = {
    "log.write": {
        "name": "Write Log Entry",
        "category": "logging",
        "description": "Write structured log entry to file or database",
        "icon": "file-text",
        "color": "#6366F1",
        "inputs": [
            {"name": "trigger", "type": "flow", "required": True, "label": "Log"},
            {"name": "log_data", "type": "data", "dataType": "any", "label": "Data to Log"}
        ],
        "outputs": [
            {"name": "success", "type": "flow", "label": "Success"},
            {"name": "error", "type": "flow", "label": "Error"},
            {"name": "log_entry", "type": "data", "dataType": "object", "label": "Log Entry"}
        ],
        "config_schema": {
            "type": "object",
            "required": ["log_destination"],
            "properties": {
                "log_destination": {
                    "enum": ["local_file", "remote_file", "database", "syslog"],
                    "default": "local_file"
                },
                "target": {
                    "type": "string",
                    "description": "Target server (for remote logging)",
                    "ui_component": "target_selector"
                },
                "log_path": {
                    "type": "string",
                    "default": "/var/log/opsconductor/workflow.log"
                },
                "log_format": {
                    "enum": ["json", "text", "csv"],
                    "default": "json"
                },
                "log_level": {
                    "enum": ["debug", "info", "warning", "error"],
                    "default": "info"
                },
                "message_template": {
                    "type": "string",
                    "default": "{{timestamp}} - {{level}} - {{message}}"
                },
                "description": {"type": "string", "default": ""}
            }
        }
    }
}

# Combine all block definitions
ALL_BLOCK_DEFINITIONS = {
    **FLOW_CONTROL_BLOCKS,
    **TRIGGER_BLOCKS,
    **SYSTEM_OPERATION_BLOCKS, 
    **FILE_OPERATION_BLOCKS,
    **LOGGING_BLOCKS
}

def get_block_definition(block_type: str) -> Dict[str, Any]:
    """Get block definition by type"""
    return ALL_BLOCK_DEFINITIONS.get(block_type)

def get_blocks_by_category(category: str) -> Dict[str, Dict[str, Any]]:
    """Get all blocks in a specific category"""
    return {
        block_type: definition 
        for block_type, definition in ALL_BLOCK_DEFINITIONS.items()
        if definition.get('category') == category
    }

def get_all_categories() -> List[str]:
    """Get list of all available categories"""
    categories = set()
    for definition in ALL_BLOCK_DEFINITIONS.values():
        categories.add(definition.get('category', 'unknown'))
    return sorted(list(categories))

def validate_block_config(block_type: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """Validate block configuration against schema"""
    definition = get_block_definition(block_type)
    if not definition:
        raise ValueError(f"Unknown block type: {block_type}")
    
    # TODO: Implement JSON schema validation
    # For now, just return the config
    return config