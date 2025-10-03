#!/usr/bin/env python3
"""
Bulk Tool Generator for OpsConductor Tool Catalog
Generates all 214 tools from the expansion plan
"""

import os
import yaml
from pathlib import Path
from datetime import datetime

# Base directory for tools
TOOLS_DIR = Path("/home/opsconductor/opsconductor-ng/pipeline/config/tools")

# Tool definitions organized by phase and category
TOOL_DEFINITIONS = {
    # PHASE 1: Critical Foundation Tools (30 tools)
    "phase1": {
        "windows": [
            {
                "name": "Get-Service",
                "description": "Query and manage Windows services",
                "category": "system",
                "priority": "HIGH",
                "capabilities": {
                    "service_management": {
                        "patterns": {
                            "query_service": {
                                "use_cases": ["check service status", "list services", "get service info"],
                                "time_ms": "500",
                                "cost": "1",
                                "complexity": 0.2,
                                "requires_approval": False,
                                "production_safe": True
                            },
                            "start_service": {
                                "use_cases": ["start service", "enable service"],
                                "time_ms": "2000",
                                "cost": "2",
                                "complexity": 0.3,
                                "requires_approval": True,
                                "production_safe": False
                            },
                            "stop_service": {
                                "use_cases": ["stop service", "disable service"],
                                "time_ms": "2000",
                                "cost": "2",
                                "complexity": 0.3,
                                "requires_approval": True,
                                "production_safe": False
                            }
                        }
                    }
                }
            },
            {
                "name": "Get-Process",
                "description": "List and manage Windows processes",
                "category": "system",
                "priority": "HIGH",
                "capabilities": {
                    "process_management": {
                        "patterns": {
                            "list_processes": {
                                "use_cases": ["list processes", "show processes", "get process info"],
                                "time_ms": "300",
                                "cost": "1",
                                "complexity": 0.1,
                                "requires_approval": False,
                                "production_safe": True
                            },
                            "stop_process": {
                                "use_cases": ["stop process", "kill process", "terminate process"],
                                "time_ms": "500",
                                "cost": "2",
                                "complexity": 0.2,
                                "requires_approval": True,
                                "production_safe": False
                            }
                        }
                    }
                }
            },
            {
                "name": "Get-EventLog",
                "description": "Query Windows Event Logs",
                "category": "monitoring",
                "priority": "HIGH",
                "capabilities": {
                    "log_analysis": {
                        "patterns": {
                            "query_events": {
                                "use_cases": ["check event log", "search events", "get log entries"],
                                "time_ms": "1000 + 10 * N",
                                "cost": "ceil(N / 100)",
                                "complexity": 0.3,
                                "requires_approval": False,
                                "production_safe": True
                            }
                        }
                    }
                }
            },
            {
                "name": "Test-NetConnection",
                "description": "Test network connectivity (ping, port)",
                "category": "network",
                "priority": "HIGH",
                "capabilities": {
                    "network_testing": {
                        "patterns": {
                            "test_connection": {
                                "use_cases": ["ping host", "test port", "check connectivity"],
                                "time_ms": "2000",
                                "cost": "1",
                                "complexity": 0.2,
                                "requires_approval": False,
                                "production_safe": True
                            }
                        }
                    }
                }
            },
            {
                "name": "Get-WmiObject",
                "description": "Query WMI for system information",
                "category": "system",
                "priority": "HIGH",
                "capabilities": {
                    "system_info": {
                        "patterns": {
                            "query_wmi": {
                                "use_cases": ["get system info", "query hardware", "wmi query"],
                                "time_ms": "800",
                                "cost": "2",
                                "complexity": 0.3,
                                "requires_approval": False,
                                "production_safe": True
                            }
                        }
                    }
                }
            },
            {
                "name": "Get-ComputerInfo",
                "description": "Get comprehensive computer information",
                "category": "system",
                "priority": "MEDIUM",
                "capabilities": {
                    "system_info": {
                        "patterns": {
                            "get_info": {
                                "use_cases": ["get computer info", "system details", "hardware info"],
                                "time_ms": "1000",
                                "cost": "2",
                                "complexity": 0.2,
                                "requires_approval": False,
                                "production_safe": True
                            }
                        }
                    }
                }
            },
            {
                "name": "Get-Disk",
                "description": "Query disk information",
                "category": "system",
                "priority": "MEDIUM",
                "capabilities": {
                    "disk_management": {
                        "patterns": {
                            "query_disks": {
                                "use_cases": ["list disks", "disk info", "storage info"],
                                "time_ms": "500",
                                "cost": "1",
                                "complexity": 0.2,
                                "requires_approval": False,
                                "production_safe": True
                            }
                        }
                    }
                }
            },
            {
                "name": "Get-Volume",
                "description": "Query volume/partition information",
                "category": "system",
                "priority": "MEDIUM",
                "capabilities": {
                    "disk_management": {
                        "patterns": {
                            "query_volumes": {
                                "use_cases": ["list volumes", "partition info", "drive info"],
                                "time_ms": "500",
                                "cost": "1",
                                "complexity": 0.2,
                                "requires_approval": False,
                                "production_safe": True
                            }
                        }
                    }
                }
            },
            {
                "name": "Get-NetAdapter",
                "description": "Query network adapter information",
                "category": "network",
                "priority": "HIGH",
                "capabilities": {
                    "network_info": {
                        "patterns": {
                            "query_adapters": {
                                "use_cases": ["list network adapters", "nic info", "network interfaces"],
                                "time_ms": "400",
                                "cost": "1",
                                "complexity": 0.2,
                                "requires_approval": False,
                                "production_safe": True
                            }
                        }
                    }
                }
            },
            {
                "name": "Get-NetIPAddress",
                "description": "Query IP address configuration",
                "category": "network",
                "priority": "HIGH",
                "capabilities": {
                    "network_info": {
                        "patterns": {
                            "query_ip": {
                                "use_cases": ["get ip address", "network config", "ip info"],
                                "time_ms": "300",
                                "cost": "1",
                                "complexity": 0.1,
                                "requires_approval": False,
                                "production_safe": True
                            }
                        }
                    }
                }
            }
        ],
        "linux": [
            # Already created: systemctl, ps, df
            {
                "name": "free",
                "description": "Display memory usage",
                "category": "system",
                "priority": "HIGH",
                "capabilities": {
                    "memory_monitoring": {
                        "patterns": {
                            "check_memory": {
                                "use_cases": ["check memory", "memory usage", "ram usage"],
                                "time_ms": "100",
                                "cost": "1",
                                "complexity": 0.1,
                                "requires_approval": False,
                                "production_safe": True
                            }
                        }
                    }
                }
            },
            {
                "name": "top",
                "description": "Display real-time process information",
                "category": "monitoring",
                "priority": "HIGH",
                "capabilities": {
                    "process_monitoring": {
                        "patterns": {
                            "monitor_processes": {
                                "use_cases": ["monitor processes", "real-time processes", "cpu usage"],
                                "time_ms": "500",
                                "cost": "1",
                                "complexity": 0.2,
                                "requires_approval": False,
                                "production_safe": True
                            }
                        }
                    }
                }
            },
            {
                "name": "journalctl",
                "description": "Query systemd journal logs",
                "category": "monitoring",
                "priority": "HIGH",
                "capabilities": {
                    "log_analysis": {
                        "patterns": {
                            "query_logs": {
                                "use_cases": ["check logs", "system logs", "service logs"],
                                "time_ms": "800 + 5 * N",
                                "cost": "ceil(N / 100)",
                                "complexity": 0.3,
                                "requires_approval": False,
                                "production_safe": True
                            }
                        }
                    }
                }
            },
            {
                "name": "curl",
                "description": "Transfer data with URLs (HTTP, FTP, etc.)",
                "category": "network",
                "priority": "HIGH",
                "capabilities": {
                    "http_client": {
                        "patterns": {
                            "http_request": {
                                "use_cases": ["http request", "api call", "download file"],
                                "time_ms": "1000 + response_time",
                                "cost": "1",
                                "complexity": 0.2,
                                "requires_approval": False,
                                "production_safe": True
                            }
                        }
                    }
                }
            },
            {
                "name": "ping",
                "description": "Test network connectivity (ICMP)",
                "category": "network",
                "priority": "HIGH",
                "capabilities": {
                    "network_testing": {
                        "patterns": {
                            "test_connectivity": {
                                "use_cases": ["ping host", "test connectivity", "check network"],
                                "time_ms": "1000 * count",
                                "cost": "1",
                                "complexity": 0.1,
                                "requires_approval": False,
                                "production_safe": True
                            }
                        }
                    }
                }
            },
            {
                "name": "netstat",
                "description": "Display network connections and statistics",
                "category": "network",
                "priority": "HIGH",
                "capabilities": {
                    "network_monitoring": {
                        "patterns": {
                            "list_connections": {
                                "use_cases": ["list connections", "network stats", "open ports"],
                                "time_ms": "400",
                                "cost": "1",
                                "complexity": 0.2,
                                "requires_approval": False,
                                "production_safe": True
                            }
                        }
                    }
                }
            },
            {
                "name": "ss",
                "description": "Display socket statistics (modern netstat)",
                "category": "network",
                "priority": "HIGH",
                "capabilities": {
                    "network_monitoring": {
                        "patterns": {
                            "list_sockets": {
                                "use_cases": ["list sockets", "network connections", "socket stats"],
                                "time_ms": "300",
                                "cost": "1",
                                "complexity": 0.2,
                                "requires_approval": False,
                                "production_safe": True
                            }
                        }
                    }
                }
            },
            {
                "name": "dig",
                "description": "DNS lookup utility (advanced)",
                "category": "network",
                "priority": "HIGH",
                "capabilities": {
                    "dns_query": {
                        "patterns": {
                            "lookup_dns": {
                                "use_cases": ["dns lookup", "resolve hostname", "query dns"],
                                "time_ms": "500",
                                "cost": "1",
                                "complexity": 0.2,
                                "requires_approval": False,
                                "production_safe": True
                            }
                        }
                    }
                }
            },
            {
                "name": "nslookup",
                "description": "Query DNS records",
                "category": "network",
                "priority": "HIGH",
                "capabilities": {
                    "dns_query": {
                        "patterns": {
                            "lookup_dns": {
                                "use_cases": ["dns lookup", "resolve hostname", "query dns"],
                                "time_ms": "500",
                                "cost": "1",
                                "complexity": 0.2,
                                "requires_approval": False,
                                "production_safe": True
                            }
                        }
                    }
                }
            },
            {
                "name": "uname",
                "description": "Display system information",
                "category": "system",
                "priority": "HIGH",
                "capabilities": {
                    "system_info": {
                        "patterns": {
                            "get_system_info": {
                                "use_cases": ["system info", "kernel version", "os info"],
                                "time_ms": "100",
                                "cost": "1",
                                "complexity": 0.1,
                                "requires_approval": False,
                                "production_safe": True
                            }
                        }
                    }
                }
            }
        ],
        "network": [
            {
                "name": "tcpdump",
                "description": "Command-line packet analyzer",
                "category": "network",
                "priority": "HIGH",
                "capabilities": {
                    "packet_capture": {
                        "patterns": {
                            "capture_packets": {
                                "use_cases": ["capture packets", "network sniffing", "packet analysis"],
                                "time_ms": "duration_ms",
                                "cost": "ceil(duration_ms / 10000)",
                                "complexity": 0.5,
                                "requires_approval": True,
                                "production_safe": False
                            }
                        }
                    }
                }
            },
            {
                "name": "tshark",
                "description": "Terminal-based Wireshark",
                "category": "network",
                "priority": "HIGH",
                "capabilities": {
                    "packet_capture": {
                        "patterns": {
                            "capture_packets": {
                                "use_cases": ["capture packets", "analyze traffic", "packet inspection"],
                                "time_ms": "duration_ms",
                                "cost": "ceil(duration_ms / 10000)",
                                "complexity": 0.5,
                                "requires_approval": True,
                                "production_safe": False
                            }
                        }
                    }
                }
            },
            {
                "name": "http-analyzer",
                "description": "Analyze HTTP protocol traffic",
                "category": "network",
                "priority": "HIGH",
                "capabilities": {
                    "protocol_analysis": {
                        "patterns": {
                            "analyze_http": {
                                "use_cases": ["analyze http", "http traffic", "web traffic analysis"],
                                "time_ms": "1000 + 0.5 * packet_count",
                                "cost": "ceil(packet_count / 1000)",
                                "complexity": 0.4,
                                "requires_approval": False,
                                "production_safe": True
                            }
                        }
                    }
                }
            },
            {
                "name": "dns-analyzer",
                "description": "Analyze DNS protocol traffic",
                "category": "network",
                "priority": "HIGH",
                "capabilities": {
                    "protocol_analysis": {
                        "patterns": {
                            "analyze_dns": {
                                "use_cases": ["analyze dns", "dns queries", "dns traffic"],
                                "time_ms": "800 + 0.3 * packet_count",
                                "cost": "ceil(packet_count / 1000)",
                                "complexity": 0.3,
                                "requires_approval": False,
                                "production_safe": True
                            }
                        }
                    }
                }
            },
            {
                "name": "tcp-analyzer",
                "description": "Analyze TCP protocol traffic",
                "category": "network",
                "priority": "HIGH",
                "capabilities": {
                    "protocol_analysis": {
                        "patterns": {
                            "analyze_tcp": {
                                "use_cases": ["analyze tcp", "tcp connections", "tcp traffic"],
                                "time_ms": "1000 + 0.4 * packet_count",
                                "cost": "ceil(packet_count / 1000)",
                                "complexity": 0.4,
                                "requires_approval": False,
                                "production_safe": True
                            }
                        }
                    }
                }
            },
            {
                "name": "udp-analyzer",
                "description": "Analyze UDP protocol traffic",
                "category": "network",
                "priority": "MEDIUM",
                "capabilities": {
                    "protocol_analysis": {
                        "patterns": {
                            "analyze_udp": {
                                "use_cases": ["analyze udp", "udp traffic", "udp packets"],
                                "time_ms": "800 + 0.3 * packet_count",
                                "cost": "ceil(packet_count / 1000)",
                                "complexity": 0.3,
                                "requires_approval": False,
                                "production_safe": True
                            }
                        }
                    }
                }
            },
            {
                "name": "ssh-analyzer",
                "description": "Analyze SSH protocol traffic",
                "category": "network",
                "priority": "MEDIUM",
                "capabilities": {
                    "protocol_analysis": {
                        "patterns": {
                            "analyze_ssh": {
                                "use_cases": ["analyze ssh", "ssh connections", "ssh traffic"],
                                "time_ms": "1000 + 0.5 * packet_count",
                                "cost": "ceil(packet_count / 1000)",
                                "complexity": 0.4,
                                "requires_approval": False,
                                "production_safe": True
                            }
                        }
                    }
                }
            },
            {
                "name": "ftp-analyzer",
                "description": "Analyze FTP protocol traffic",
                "category": "network",
                "priority": "MEDIUM",
                "capabilities": {
                    "protocol_analysis": {
                        "patterns": {
                            "analyze_ftp": {
                                "use_cases": ["analyze ftp", "ftp traffic", "ftp connections"],
                                "time_ms": "900 + 0.4 * packet_count",
                                "cost": "ceil(packet_count / 1000)",
                                "complexity": 0.3,
                                "requires_approval": False,
                                "production_safe": True
                            }
                        }
                    }
                }
            },
            {
                "name": "smtp-analyzer",
                "description": "Analyze SMTP protocol traffic",
                "category": "network",
                "priority": "MEDIUM",
                "capabilities": {
                    "protocol_analysis": {
                        "patterns": {
                            "analyze_smtp": {
                                "use_cases": ["analyze smtp", "email traffic", "smtp connections"],
                                "time_ms": "900 + 0.4 * packet_count",
                                "cost": "ceil(packet_count / 1000)",
                                "complexity": 0.3,
                                "requires_approval": False,
                                "production_safe": True
                            }
                        }
                    }
                }
            },
            {
                "name": "tls-analyzer",
                "description": "Analyze TLS/SSL protocol traffic",
                "category": "network",
                "priority": "HIGH",
                "capabilities": {
                    "protocol_analysis": {
                        "patterns": {
                            "analyze_tls": {
                                "use_cases": ["analyze tls", "ssl traffic", "encrypted traffic"],
                                "time_ms": "1200 + 0.6 * packet_count",
                                "cost": "ceil(packet_count / 1000)",
                                "complexity": 0.5,
                                "requires_approval": False,
                                "production_safe": True
                            }
                        }
                    }
                }
            }
        ]
    }
}


def generate_tool_yaml(tool_def, platform):
    """Generate YAML content for a tool definition"""
    
    tool_name = tool_def["name"]
    description = tool_def["description"]
    category = tool_def["category"]
    capabilities = tool_def["capabilities"]
    
    # Build YAML structure
    yaml_content = {
        "tool_name": tool_name,
        "version": "1.0",
        "description": description,
        "platform": platform,
        "category": category,
        "defaults": {
            "accuracy_level": "real-time",
            "freshness": "live",
            "data_source": "direct"
        },
        "capabilities": {}
    }
    
    # Add capabilities
    for cap_name, cap_data in capabilities.items():
        yaml_content["capabilities"][cap_name] = {
            "description": cap_data.get("description", f"{cap_name} capability"),
            "patterns": {}
        }
        
        for pattern_name, pattern_data in cap_data["patterns"].items():
            pattern_content = {
                "description": pattern_data.get("description", f"{pattern_name} pattern"),
                "typical_use_cases": pattern_data["use_cases"],
                "time_estimate_ms": pattern_data["time_ms"],
                "cost_estimate": str(pattern_data["cost"]),
                "complexity_score": pattern_data["complexity"],
                "scope": "single_item",
                "completeness": "complete",
                "policy": {
                    "max_cost": 10,
                    "requires_approval": pattern_data["requires_approval"],
                    "production_safe": pattern_data["production_safe"],
                    "max_execution_time": 60
                },
                "preference_match": {
                    "speed": 0.8,
                    "accuracy": 0.9,
                    "cost": 0.9,
                    "complexity": 0.8,
                    "completeness": 0.9
                },
                "required_inputs": [
                    {
                        "name": "host",
                        "type": "string",
                        "description": "Target host",
                        "validation": ".*"
                    }
                ]
            }
            
            yaml_content["capabilities"][cap_name]["patterns"][pattern_name] = pattern_content
    
    # Add metadata
    yaml_content["metadata"] = {
        "author": "OpsConductor Team",
        "created": datetime.now().strftime("%Y-%m-%d"),
        "updated": datetime.now().strftime("%Y-%m-%d"),
        "tags": [platform, category, tool_name.lower()],
        "documentation_url": f"https://docs.opsconductor.io/tools/{tool_name.lower()}"
    }
    
    return yaml_content


def save_tool_yaml(tool_def, platform, phase):
    """Save tool YAML to appropriate directory"""
    
    tool_name = tool_def["name"]
    
    # Determine directory
    if platform == "windows":
        tool_dir = TOOLS_DIR / "windows"
    elif platform == "linux":
        tool_dir = TOOLS_DIR / "linux"
    elif platform == "network":
        tool_dir = TOOLS_DIR / "network"
    else:
        tool_dir = TOOLS_DIR / "custom"
    
    # Create directory if it doesn't exist
    tool_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate YAML content
    yaml_content = generate_tool_yaml(tool_def, platform)
    
    # Save to file
    file_path = tool_dir / f"{tool_name.lower().replace('-', '_')}.yaml"
    
    with open(file_path, 'w') as f:
        # Add header comment
        f.write(f"# {tool_name} - {tool_def['description']}\n")
        yaml.dump(yaml_content, f, default_flow_style=False, sort_keys=False, indent=2)
    
    print(f"✅ Created: {file_path}")
    return file_path


def generate_phase1_tools():
    """Generate all Phase 1 tools"""
    
    print("=" * 80)
    print("PHASE 1: Critical Foundation Tools (30 tools)")
    print("=" * 80)
    
    phase_data = TOOL_DEFINITIONS["phase1"]
    
    # Generate Windows tools
    print("\n📦 Windows Tools (10 tools)")
    print("-" * 80)
    for tool_def in phase_data["windows"]:
        save_tool_yaml(tool_def, "windows", "phase1")
    
    # Generate Linux tools
    print("\n🐧 Linux Tools (10 tools)")
    print("-" * 80)
    for tool_def in phase_data["linux"]:
        save_tool_yaml(tool_def, "linux", "phase1")
    
    # Generate Network tools
    print("\n🌐 Network Tools (10 tools)")
    print("-" * 80)
    for tool_def in phase_data["network"]:
        save_tool_yaml(tool_def, "network", "phase1")
    
    print("\n" + "=" * 80)
    print("✅ Phase 1 Complete: 30 tools generated")
    print("=" * 80)


if __name__ == "__main__":
    generate_phase1_tools()