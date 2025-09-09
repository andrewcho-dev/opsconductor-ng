#!/usr/bin/env python3
"""
Visual Job Schema - New node-based workflow format
Replaces the old step-based format completely
"""

# Visual Job Definition Schema (Node-based workflow format)
VISUAL_JOB_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "VisualJobDefinition",
    "type": "object",
    "required": ["name", "version", "nodes", "edges"],
    "properties": {
        "name": {"type": "string", "minLength": 1, "maxLength": 255},
        "description": {"type": "string", "maxLength": 1000},
        "version": {"type": "integer", "minimum": 1},
        "parameters": {
            "type": "object",
            "additionalProperties": {
                "type": "object",
                "properties": {
                    "type": {"enum": ["string", "number", "boolean", "array", "object"]},
                    "default": {},
                    "description": {"type": "string"},
                    "required": {"type": "boolean", "default": False}
                }
            }
        },
        "nodes": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "required": ["id", "type", "position", "data"],
                "properties": {
                    "id": {"type": "string", "pattern": "^[a-zA-Z0-9_-]+$"},
                    "type": {"enum": [
                        "flow.start",
                        "flow.end", 
                        "flow.delay",
                        "action.command",
                        "action.http",
                        "action.notification",
                        "data.transform",
                        "logic.if"
                    ]},
                    "position": {
                        "type": "object",
                        "required": ["x", "y"],
                        "properties": {
                            "x": {"type": "number"},
                            "y": {"type": "number"}
                        }
                    },
                    "data": {
                        "type": "object",
                        "required": ["name"],
                        "properties": {
                            "name": {"type": "string", "minLength": 1},
                            "description": {"type": "string"}
                        },
                        "allOf": [
                            {
                                "if": {"properties": {"type": {"const": "flow.start"}}},
                                "then": {
                                    "properties": {
                                        "data": {
                                            "properties": {
                                                "trigger_type": {"enum": ["manual", "scheduled", "webhook"], "default": "manual"},
                                                "webhook_config": {
                                                    "type": "object",
                                                    "properties": {
                                                        "secret": {"type": "string"},
                                                        "validation": {"type": "boolean", "default": True}
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            },
                            {
                                "if": {"properties": {"type": {"const": "flow.end"}}},
                                "then": {
                                    "properties": {
                                        "data": {
                                            "properties": {
                                                "status": {"enum": ["success", "failure", "conditional"], "default": "success"},
                                                "message": {"type": "string"}
                                            }
                                        }
                                    }
                                }
                            },
                            {
                                "if": {"properties": {"type": {"const": "flow.delay"}}},
                                "then": {
                                    "properties": {
                                        "data": {
                                            "required": ["delay_seconds"],
                                            "properties": {
                                                "delay_seconds": {"type": "integer", "minimum": 1, "maximum": 3600},
                                                "delay_type": {"enum": ["fixed", "exponential"], "default": "fixed"}
                                            }
                                        }
                                    }
                                }
                            },
                            {
                                "if": {"properties": {"type": {"const": "action.command"}}},
                                "then": {
                                    "properties": {
                                        "data": {
                                            "required": ["command", "connection_type"],
                                            "properties": {
                                                "command": {"type": "string", "minLength": 1},
                                                "connection_type": {"enum": ["ssh", "winrm", "local", "docker", "kubernetes"]},
                                                "shell": {"type": "string", "default": "bash"},
                                                "target": {"type": "string"},
                                                "timeout": {"type": "integer", "minimum": 1, "maximum": 3600, "default": 30},
                                                "working_directory": {"type": "string"},
                                                "environment": {
                                                    "type": "object",
                                                    "additionalProperties": {"type": "string"}
                                                },
                                                "retry_count": {"type": "integer", "minimum": 0, "maximum": 5, "default": 0},
                                                "retry_delay": {"type": "integer", "minimum": 1, "maximum": 300, "default": 5}
                                            }
                                        }
                                    }
                                }
                            },
                            {
                                "if": {"properties": {"type": {"const": "action.http"}}},
                                "then": {
                                    "properties": {
                                        "data": {
                                            "required": ["url", "method"],
                                            "properties": {
                                                "url": {"type": "string", "format": "uri"},
                                                "method": {"enum": ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"]},
                                                "headers": {
                                                    "type": "object",
                                                    "additionalProperties": {"type": "string"}
                                                },
                                                "body": {"type": "string"},
                                                "auth_type": {"enum": ["none", "basic", "bearer", "api_key"], "default": "none"},
                                                "auth_config": {
                                                    "type": "object",
                                                    "properties": {
                                                        "username": {"type": "string"},
                                                        "password": {"type": "string"},
                                                        "token": {"type": "string"},
                                                        "api_key": {"type": "string"},
                                                        "header_name": {"type": "string"}
                                                    }
                                                },
                                                "timeout": {"type": "integer", "minimum": 1, "maximum": 300, "default": 30},
                                                "ssl_verify": {"type": "boolean", "default": True},
                                                "follow_redirects": {"type": "boolean", "default": True},
                                                "expected_status": {
                                                    "oneOf": [
                                                        {"type": "integer"},
                                                        {"type": "array", "items": {"type": "integer"}}
                                                    ],
                                                    "default": [200]
                                                }
                                            }
                                        }
                                    }
                                }
                            },
                            {
                                "if": {"properties": {"type": {"const": "action.notification"}}},
                                "then": {
                                    "properties": {
                                        "data": {
                                            "required": ["notification_type"],
                                            "properties": {
                                                "notification_type": {"enum": ["email", "slack", "teams", "webhook", "sms"]},
                                                "recipients": {
                                                    "type": "array",
                                                    "items": {"type": "string"},
                                                    "minItems": 1
                                                },
                                                "subject": {"type": "string"},
                                                "message": {"type": "string"},
                                                "webhook_url": {"type": "string", "format": "uri"},
                                                "channel": {"type": "string"},
                                                "priority": {"enum": ["low", "normal", "high", "critical"], "default": "normal"},
                                                "send_on": {
                                                    "type": "array",
                                                    "items": {"enum": ["success", "failure", "always"]},
                                                    "default": ["always"]
                                                }
                                            }
                                        }
                                    }
                                }
                            },
                            {
                                "if": {"properties": {"type": {"const": "data.transform"}}},
                                "then": {
                                    "properties": {
                                        "data": {
                                            "required": ["script"],
                                            "properties": {
                                                "script": {"type": "string", "minLength": 1},
                                                "language": {"enum": ["python", "javascript", "jq"], "default": "python"},
                                                "input_variables": {
                                                    "type": "array",
                                                    "items": {"type": "string"}
                                                },
                                                "output_variables": {
                                                    "type": "array",
                                                    "items": {"type": "string"}
                                                },
                                                "timeout": {"type": "integer", "minimum": 1, "maximum": 300, "default": 30}
                                            }
                                        }
                                    }
                                }
                            },
                            {
                                "if": {"properties": {"type": {"const": "logic.if"}}},
                                "then": {
                                    "properties": {
                                        "data": {
                                            "required": ["condition"],
                                            "properties": {
                                                "condition": {"type": "string", "minLength": 1},
                                                "condition_type": {"enum": ["expression", "script"], "default": "expression"},
                                                "true_path": {"type": "string"},
                                                "false_path": {"type": "string"}
                                            }
                                        }
                                    }
                                }
                            }
                        ]
                    }
                }
            }
        },
        "edges": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["id", "source", "target"],
                "properties": {
                    "id": {"type": "string", "pattern": "^[a-zA-Z0-9_-]+$"},
                    "source": {"type": "string"},
                    "target": {"type": "string"},
                    "condition": {"enum": ["true", "false", "always"], "default": "always"},
                    "label": {"type": "string"}
                }
            }
        },
        "metadata": {
            "type": "object",
            "properties": {
                "tags": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "category": {"type": "string"},
                "author": {"type": "string"},
                "documentation_url": {"type": "string", "format": "uri"}
            }
        }
    }
}

# Export format schema for import/export functionality
EXPORT_FORMAT_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "JobExportFormat",
    "type": "object",
    "required": ["format_version", "export_timestamp", "jobs"],
    "properties": {
        "format_version": {"type": "string", "const": "1.0"},
        "export_timestamp": {"type": "string", "format": "date-time"},
        "export_metadata": {
            "type": "object",
            "properties": {
                "exported_by": {"type": "string"},
                "opsconductor_version": {"type": "string"},
                "description": {"type": "string"}
            }
        },
        "jobs": {
            "type": "array",
            "items": VISUAL_JOB_SCHEMA
        }
    }
}