"""
Redesigned Block Definitions - Generic + Extensible Approach
Following Node-RED and n8n patterns for handling infinite actions
"""

from typing import Dict, List, Any

# =============================================================================
# CORE BLOCKS - Generic, reusable functionality
# =============================================================================

CORE_BLOCKS = {
    # Flow Control
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
                    "default": ["manual"]
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
                }
            }
        }
    },
    
    "logic.switch": {
        "name": "Switch",
        "category": "logic", 
        "description": "Route data based on multiple conditions",
        "icon": "shuffle",
        "color": "#8B5CF6",
        "inputs": [
            {"name": "trigger", "type": "flow", "required": True, "label": "Route"},
            {"name": "data", "type": "data", "dataType": "any", "label": "Data to Route"}
        ],
        "outputs": [
            {"name": "case_1", "type": "flow", "label": "Case 1"},
            {"name": "case_2", "type": "flow", "label": "Case 2"},
            {"name": "case_3", "type": "flow", "label": "Case 3"},
            {"name": "default", "type": "flow", "label": "Default"},
            {"name": "data_out", "type": "data", "dataType": "any", "label": "Pass-through Data"}
        ],
        "config_schema": {
            "type": "object",
            "properties": {
                "cases": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "condition": {"type": "string"},
                            "label": {"type": "string"}
                        }
                    },
                    "default": [
                        {"condition": "{{data.status}} === 'success'", "label": "Success"},
                        {"condition": "{{data.status}} === 'error'", "label": "Error"}
                    ]
                }
            }
        }
    },
    
    "data.transform": {
        "name": "Transform Data",
        "category": "data",
        "description": "Transform data using JavaScript expressions",
        "icon": "code",
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
                    "ui_component": "code_editor",
                    "language": "javascript"
                }
            }
        }
    },
    
    "data.filter": {
        "name": "Filter Data",
        "category": "data",
        "description": "Filter array data based on conditions",
        "icon": "filter",
        "color": "#F59E0B",
        "inputs": [
            {"name": "trigger", "type": "flow", "required": True, "label": "Filter"},
            {"name": "input_data", "type": "data", "dataType": "array", "label": "Input Array"}
        ],
        "outputs": [
            {"name": "success", "type": "flow", "label": "Success"},
            {"name": "filtered_data", "type": "data", "dataType": "array", "label": "Filtered Data"}
        ],
        "config_schema": {
            "type": "object",
            "properties": {
                "filter_condition": {
                    "type": "string",
                    "default": "item.status === 'active'",
                    "description": "JavaScript condition for filtering (item variable available)"
                }
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
                "delay_seconds": {"type": "integer", "default": 5, "minimum": 1}
            }
        }
    }
}

# =============================================================================
# GENERIC ACTION BLOCKS - Configurable for different operations
# =============================================================================

GENERIC_ACTION_BLOCKS = {
    "action.http_request": {
        "name": "HTTP Request",
        "category": "communication",
        "description": "Make HTTP requests to any API or service",
        "icon": "globe",
        "color": "#3B82F6",
        "inputs": [
            {"name": "trigger", "type": "flow", "required": True, "label": "Execute"},
            {"name": "url", "type": "data", "dataType": "string", "required": False, "label": "URL Override"},
            {"name": "headers", "type": "data", "dataType": "object", "required": False, "label": "Headers"},
            {"name": "body", "type": "data", "dataType": "any", "required": False, "label": "Request Body"}
        ],
        "outputs": [
            {"name": "success", "type": "flow", "label": "Success"},
            {"name": "error", "type": "flow", "label": "Error"},
            {"name": "response", "type": "data", "dataType": "object", "label": "Response Data"}
        ],
        "config_schema": {
            "type": "object",
            "properties": {
                "method": {
                    "enum": ["GET", "POST", "PUT", "PATCH", "DELETE"],
                    "default": "GET"
                },
                "url": {
                    "type": "string",
                    "default": "https://api.example.com/endpoint",
                    "description": "Request URL"
                },
                "headers": {
                    "type": "object",
                    "default": {"Content-Type": "application/json"},
                    "ui_component": "key_value_editor"
                },
                "authentication": {
                    "type": "object",
                    "properties": {
                        "type": {"enum": ["none", "basic", "bearer", "api_key"], "default": "none"},
                        "username": {"type": "string"},
                        "password": {"type": "string", "ui_component": "password"},
                        "token": {"type": "string", "ui_component": "password"},
                        "api_key": {"type": "string", "ui_component": "password"},
                        "api_key_header": {"type": "string", "default": "X-API-Key"}
                    }
                },
                "timeout_seconds": {"type": "integer", "default": 30},
                "retry_attempts": {"type": "integer", "default": 0, "maximum": 5}
            }
        }
    },
    
    "action.command": {
        "name": "Execute Command",
        "category": "system",
        "description": "Execute shell commands on target systems",
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
                "command": {
                    "type": "string",
                    "default": "echo 'Hello World'",
                    "description": "Command to execute"
                },
                "working_directory": {"type": "string", "default": ""},
                "environment_variables": {
                    "type": "object",
                    "default": {},
                    "ui_component": "key_value_editor"
                },
                "timeout_seconds": {"type": "integer", "default": 60},
                "run_as_user": {"type": "string", "default": ""},
                "capture_output": {"type": "boolean", "default": True}
            }
        }
    },
    
    "action.file_operation": {
        "name": "File Operation",
        "category": "files",
        "description": "Perform file operations (read, write, copy, move, delete)",
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
                "operation": {
                    "enum": ["read", "write", "copy", "move", "delete", "list", "exists", "create_directory"],
                    "default": "read",
                    "description": "File operation to perform"
                },
                "source_path": {"type": "string", "description": "Source file/directory path"},
                "destination_path": {"type": "string", "description": "Destination path (for copy/move)"},
                "create_directories": {"type": "boolean", "default": False},
                "overwrite_existing": {"type": "boolean", "default": False},
                "file_permissions": {"type": "string", "default": "644"},
                "encoding": {"type": "string", "default": "utf-8", "enum": ["utf-8", "ascii", "binary"]}
            }
        }
    },
    
    "action.service_control": {
        "name": "Service Control",
        "category": "system",
        "description": "Control system services (start, stop, restart, status)",
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
                "service_name": {
                    "type": "string",
                    "description": "Name of the service to control"
                },
                "action": {
                    "enum": ["start", "stop", "restart", "reload", "status", "enable", "disable"],
                    "default": "status",
                    "description": "Action to perform on the service"
                },
                "wait_for_status": {
                    "enum": ["", "running", "stopped"],
                    "default": "",
                    "description": "Wait for service to reach this status"
                },
                "timeout_seconds": {"type": "integer", "default": 30}
            }
        }
    },
    
    "action.notification": {
        "name": "Send Notification",
        "category": "communication",
        "description": "Send notifications via email, Slack, Teams, etc.",
        "icon": "bell",
        "color": "#F59E0B",
        "inputs": [
            {"name": "trigger", "type": "flow", "required": True, "label": "Send"},
            {"name": "message", "type": "data", "dataType": "string", "required": False, "label": "Message Override"},
            {"name": "recipients", "type": "data", "dataType": "array", "required": False, "label": "Recipients Override"}
        ],
        "outputs": [
            {"name": "success", "type": "flow", "label": "Success"},
            {"name": "error", "type": "flow", "label": "Error"},
            {"name": "result", "type": "data", "dataType": "object", "label": "Send Result"}
        ],
        "config_schema": {
            "type": "object",
            "required": ["notification_type"],
            "properties": {
                "notification_type": {
                    "enum": ["email", "slack", "teams", "webhook", "sms"],
                    "default": "email",
                    "description": "Type of notification to send"
                },
                "recipients": {
                    "type": "array",
                    "items": {"type": "string"},
                    "default": [],
                    "description": "List of recipients"
                },
                "subject": {"type": "string", "default": "Workflow Notification"},
                "message": {
                    "type": "string",
                    "default": "Workflow completed successfully",
                    "ui_component": "textarea"
                },
                "priority": {
                    "enum": ["low", "normal", "high", "urgent"],
                    "default": "normal"
                },
                "template": {"type": "string", "default": ""},
                "attachments": {
                    "type": "array",
                    "items": {"type": "string"},
                    "default": []
                }
            }
        }
    }
}

# =============================================================================
# TRIGGER BLOCKS - Event sources
# =============================================================================

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
                    "ui_component": "cron_editor"
                },
                "timezone": {"type": "string", "default": "UTC"},
                "enabled": {"type": "boolean", "default": True}
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
                    "default": "/webhook/my-workflow"
                },
                "authentication": {
                    "enum": ["none", "token", "signature"],
                    "default": "token"
                },
                "allowed_methods": {
                    "type": "array",
                    "items": {"enum": ["GET", "POST", "PUT", "PATCH"]},
                    "default": ["POST"]
                }
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
                    "ui_component": "target_selector"
                },
                "watch_path": {"type": "string"},
                "file_pattern": {"type": "string", "default": "*"},
                "watch_events": {
                    "type": "array",
                    "items": {"enum": ["created", "modified", "deleted", "moved"]},
                    "default": ["created", "modified"]
                },
                "recursive": {"type": "boolean", "default": False}
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
                    "ui_component": "target_selector"
                },
                "service_name": {"type": "string"},
                "monitor_events": {
                    "type": "array",
                    "items": {"enum": ["stopped", "started", "failed", "restarted", "crashed"]},
                    "default": ["stopped", "failed"]
                },
                "check_interval_sec": {"type": "integer", "default": 60, "minimum": 10}
            }
        }
    }
}

# =============================================================================
# INTEGRATION BLOCKS - Specific service integrations (extensible)
# =============================================================================

INTEGRATION_BLOCKS = {
    "integration.slack": {
        "name": "Slack",
        "category": "integrations",
        "description": "Send messages and interact with Slack",
        "icon": "slack",
        "color": "#4A154B",
        "inputs": [
            {"name": "trigger", "type": "flow", "required": True, "label": "Execute"},
            {"name": "message", "type": "data", "dataType": "string", "required": False, "label": "Message"},
            {"name": "channel", "type": "data", "dataType": "string", "required": False, "label": "Channel"}
        ],
        "outputs": [
            {"name": "success", "type": "flow", "label": "Success"},
            {"name": "error", "type": "flow", "label": "Error"},
            {"name": "response", "type": "data", "dataType": "object", "label": "Slack Response"}
        ],
        "config_schema": {
            "type": "object",
            "required": ["operation"],
            "properties": {
                "operation": {
                    "enum": ["send_message", "create_channel", "invite_user", "get_user_info"],
                    "default": "send_message"
                },
                "channel": {"type": "string", "default": "#general"},
                "message": {"type": "string", "default": "Hello from workflow!"},
                "username": {"type": "string", "default": "Workflow Bot"},
                "icon_emoji": {"type": "string", "default": ":robot_face:"},
                "webhook_url": {"type": "string", "ui_component": "password"}
            }
        }
    },
    
    "integration.jira": {
        "name": "Jira",
        "category": "integrations", 
        "description": "Create and manage Jira issues",
        "icon": "jira",
        "color": "#0052CC",
        "inputs": [
            {"name": "trigger", "type": "flow", "required": True, "label": "Execute"},
            {"name": "issue_data", "type": "data", "dataType": "object", "required": False, "label": "Issue Data"}
        ],
        "outputs": [
            {"name": "success", "type": "flow", "label": "Success"},
            {"name": "error", "type": "flow", "label": "Error"},
            {"name": "issue", "type": "data", "dataType": "object", "label": "Jira Issue"}
        ],
        "config_schema": {
            "type": "object",
            "required": ["operation", "jira_url"],
            "properties": {
                "operation": {
                    "enum": ["create_issue", "update_issue", "get_issue", "search_issues", "add_comment"],
                    "default": "create_issue"
                },
                "jira_url": {"type": "string", "default": "https://company.atlassian.net"},
                "project_key": {"type": "string", "default": "PROJ"},
                "issue_type": {"type": "string", "default": "Task"},
                "summary": {"type": "string", "default": "Issue created by workflow"},
                "description": {"type": "string", "default": ""},
                "priority": {"type": "string", "default": "Medium"},
                "assignee": {"type": "string", "default": ""},
                "api_token": {"type": "string", "ui_component": "password"}
            }
        }
    }
}

# =============================================================================
# COMBINE ALL BLOCKS
# =============================================================================

ALL_BLOCK_DEFINITIONS = {
    **CORE_BLOCKS,
    **GENERIC_ACTION_BLOCKS,
    **TRIGGER_BLOCKS,
    **INTEGRATION_BLOCKS
}

# =============================================================================
# BLOCK CATEGORIES FOR UI ORGANIZATION
# =============================================================================

BLOCK_CATEGORIES = {
    "flow-control": {
        "name": "Flow Control",
        "description": "Control workflow execution flow",
        "icon": "git-branch",
        "color": "#10B981",
        "order": 1
    },
    "logic": {
        "name": "Logic",
        "description": "Conditional logic and decision making",
        "icon": "cpu",
        "color": "#8B5CF6", 
        "order": 2
    },
    "data": {
        "name": "Data",
        "description": "Data transformation and manipulation",
        "icon": "database",
        "color": "#F59E0B",
        "order": 3
    },
    "triggers": {
        "name": "Triggers",
        "description": "Workflow triggers and event sources",
        "icon": "zap",
        "color": "#EF4444",
        "order": 4
    },
    "communication": {
        "name": "Communication",
        "description": "HTTP requests and notifications",
        "icon": "globe",
        "color": "#3B82F6",
        "order": 5
    },
    "system": {
        "name": "System",
        "description": "System operations and commands",
        "icon": "server",
        "color": "#1F2937",
        "order": 6
    },
    "files": {
        "name": "Files",
        "description": "File and directory operations",
        "icon": "folder",
        "color": "#059669",
        "order": 7
    },
    "integrations": {
        "name": "Integrations",
        "description": "Third-party service integrations",
        "icon": "puzzle",
        "color": "#7C3AED",
        "order": 8
    }
}