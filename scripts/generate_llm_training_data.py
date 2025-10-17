#!/usr/bin/env python3
"""
LLM Training Data Generator for Intent Classification with Capabilities

Generates thousands of training examples that teach the LLM to properly map 
user requests to categories, actions, and capabilities.

This addresses the critical issue where LLM wasn't populating the capabilities 
field, causing the sophisticated 90%+ accuracy tool selection system to be bypassed.
"""

import json
import random
from typing import List, Dict, Any, Tuple
from pathlib import Path

class LLMTrainingDataGenerator:
    """Generate comprehensive training data for intent classification"""
    
    def __init__(self):
        # Available capabilities from the prompt
        self.capabilities = [
            "api_query", "asset_management", "asset_query", "credential_access",
            "disk_management", "disk_monitoring", "dns_query", "http_client",
            "infrastructure_info", "log_analysis", "memory_monitoring", "network_info",
            "network_monitoring", "network_testing", "packet_capture", "process_management",
            "process_monitoring", "protocol_analysis", "resource_listing", "secret_retrieval",
            "service_management", "system_info", "system_monitoring", "text_search",
            "windows_automation", "windows_service_management"
        ]
        
        # Categories and their actions
        self.categories = {
            "automation": [
                "restart_service", "start_service", "stop_service", "deploy_application", 
                "run_script", "execute_command", "backup_data", "restore_data", "emergency_response"
            ],
            "monitoring": [
                "check_status", "view_logs", "get_metrics", "check_health", 
                "monitor_performance", "view_dashboard", "check_alerts"
            ],
            "troubleshooting": [
                "diagnose_issue", "fix_problem", "investigate_error", "diagnose_performance", 
                "check_connectivity", "analyze_logs", "debug_application"
            ],
            "configuration": [
                "update_config", "change_settings", "modify_parameters", "update_environment", 
                "configure_service", "set_permissions", "update_security"
            ],
            "information": [
                "get_help", "explain_concept", "show_documentation", "list_resources", 
                "describe_system", "show_examples", "get_status_info", "calculate", 
                "compute", "math", "answer_question", "provide_information"
            ],
            "asset_management": [
                "list_assets", "get_asset", "search_assets", "count_assets", "get_credentials", 
                "list_credentials", "find_asset", "query_assets", "list_servers", "list_hosts", 
                "get_asset_info", "asset_count", "asset_discovery"
            ]
        }
        
        # Capability mappings for each category/action combination
        self.capability_mappings = self._build_capability_mappings()
        
        # Training example templates
        self.example_templates = self._build_example_templates()

    def _build_capability_mappings(self) -> Dict[str, Dict[str, List[str]]]:
        """Build detailed mappings from category/action to likely capabilities"""
        return {
            "automation": {
                "restart_service": ["service_management", "system_monitoring"],
                "start_service": ["service_management", "system_monitoring"],
                "stop_service": ["service_management", "system_monitoring"],
                "deploy_application": ["service_management", "disk_management", "system_monitoring"],
                "run_script": ["system_info", "process_management"],
                "execute_command": ["system_info", "process_management"],
                "backup_data": ["disk_management", "system_info"],
                "restore_data": ["disk_management", "system_info"],
                "emergency_response": ["service_management", "system_monitoring", "process_management"]
            },
            "monitoring": {
                "check_status": ["system_monitoring", "service_management"],
                "view_logs": ["log_analysis", "system_info"],
                "get_metrics": ["system_monitoring", "memory_monitoring", "disk_monitoring"],
                "check_health": ["system_monitoring", "service_management"],
                "monitor_performance": ["system_monitoring", "memory_monitoring", "process_monitoring"],
                "view_dashboard": ["system_monitoring", "api_query"],
                "check_alerts": ["system_monitoring", "log_analysis"]
            },
            "troubleshooting": {
                "diagnose_issue": ["system_monitoring", "log_analysis", "process_monitoring"],
                "fix_problem": ["service_management", "system_info", "process_management"],
                "investigate_error": ["log_analysis", "system_monitoring"],
                "diagnose_performance": ["system_monitoring", "memory_monitoring", "process_monitoring"],
                "check_connectivity": ["network_testing", "network_monitoring"],
                "analyze_logs": ["log_analysis", "text_search"],
                "debug_application": ["process_monitoring", "log_analysis", "system_monitoring"]
            },
            "configuration": {
                "update_config": ["system_info", "service_management"],
                "change_settings": ["system_info", "service_management"],
                "modify_parameters": ["system_info", "service_management"],
                "update_environment": ["system_info", "service_management"],
                "configure_service": ["service_management", "system_info"],
                "set_permissions": ["system_info", "disk_management"],
                "update_security": ["system_info", "service_management"]
            },
            "information": {
                "get_help": ["system_info"],
                "explain_concept": ["system_info"],
                "show_documentation": ["system_info"],
                "list_resources": ["resource_listing", "system_info"],
                "describe_system": ["system_info", "infrastructure_info"],
                "show_examples": ["system_info"],
                "get_status_info": ["system_info", "system_monitoring"],
                "calculate": ["system_info"],
                "compute": ["system_info"],
                "math": ["system_info"],
                "answer_question": ["system_info"],
                "provide_information": ["system_info", "infrastructure_info"]
            },
            "asset_management": {
                "list_assets": ["asset_management", "resource_listing"],
                "get_asset": ["asset_management", "asset_query"],
                "search_assets": ["asset_management", "asset_query"],
                "count_assets": ["asset_management", "asset_query"],
                "get_credentials": ["credential_access", "secret_retrieval"],
                "list_credentials": ["credential_access", "secret_retrieval"],
                "find_asset": ["asset_management", "asset_query"],
                "query_assets": ["asset_management", "asset_query"],
                "list_servers": ["asset_management", "resource_listing"],
                "list_hosts": ["asset_management", "resource_listing"],
                "get_asset_info": ["asset_management", "asset_query"],
                "asset_count": ["asset_management", "asset_query"],
                "asset_discovery": ["asset_management", "network_info"]
            }
        }

    def _build_example_templates(self) -> Dict[str, List[str]]:
        """Build example templates for each category"""
        return {
            "automation": [
                "restart {service} service",
                "start {service} on {host}",
                "stop {service}",
                "deploy {app} to {environment}",
                "run {script} on {host}",
                "execute {command}",
                "backup {path} to {destination}",
                "restore {path} from {backup}",
                "emergency shutdown of {service}"
            ],
            "monitoring": [
                "check status of {service}",
                "view logs for {service}",
                "get CPU metrics for {host}",
                "check health of {application}",
                "monitor performance of {host}",
                "show dashboard for {service}",
                "check alerts for {environment}"
            ],
            "troubleshooting": [
                "diagnose {service} issue",
                "fix {problem} on {host}",
                "investigate {error} in {application}",
                "diagnose performance issues on {host}",
                "check connectivity to {host}",
                "analyze logs for {error}",
                "debug {application} performance"
            ],
            "configuration": [
                "update {service} configuration",
                "change {setting} to {value}",
                "modify {parameter} in {service}",
                "update {environment} settings",
                "configure {service} on {host}",
                "set permissions for {path}",
                "update security settings for {service}"
            ],
            "information": [
                "how do I {action}",
                "explain {concept}",
                "show documentation for {topic}",
                "list available {resources}",
                "describe {system}",
                "show examples of {usage}",
                "what is the status of {item}",
                "calculate {metric}",
                "display contents of {file}",
                "show {information}",
                "get {data}",
                "read {file}"
            ],
            "asset_management": [
                "list all servers",
                "get asset {id}",
                "search for {hostname}",
                "count active servers",
                "get credentials for {service}",
                "list available credentials",
                "find asset by {criteria}",
                "query assets in {location}",
                "list hosts in {environment}",
                "get information about {asset}",
                "discover assets in {network}"
            ]
        }

    def generate_training_examples(self, count: int = 10000) -> List[Dict[str, Any]]:
        """Generate comprehensive training examples"""
        examples = []
        
        # Generate examples for each category
        for category, actions in self.categories.items():
            category_count = count // len(self.categories)
            
            for action in actions:
                action_count = category_count // len(actions)
                
                for _ in range(action_count):
                    # Generate example request
                    request = self._generate_request_example(category, action)
                    
                    # Get appropriate capabilities
                    capabilities = self._get_capabilities_for_action(category, action)
                    
                    # Generate confidence (vary for realism)
                    confidence = round(random.uniform(0.75, 0.98), 2)
                    
                    example = {
                        "request": request,
                        "expected_response": {
                            "category": category,
                            "action": action,
                            "confidence": confidence,
                            "capabilities": capabilities
                        }
                    }
                    examples.append(example)
        
        # Add specific high-priority examples
        examples.extend(self._generate_priority_examples())
        
        # Shuffle for better training
        random.shuffle(examples)
        
        return examples[:count]

    def _generate_request_example(self, category: str, action: str) -> str:
        """Generate a realistic request example"""
        templates = self.example_templates.get(category, [])
        if not templates:
            return f"{action} example"
        
        template = random.choice(templates)
        
        # Fill in template variables
        variables = {
            "service": random.choice(["nginx", "apache", "mysql", "postgresql", "redis", "docker", "ssh"]),
            "host": random.choice(["server1", "web-01", "db-server", "192.168.1.100", "prod-web-01"]),
            "app": random.choice(["webapp", "api", "microservice", "application"]),
            "environment": random.choice(["production", "staging", "development", "test"]),
            "script": random.choice(["backup.sh", "deploy.py", "maintenance.sh", "cleanup.py"]),
            "command": random.choice(["ls -la", "ps aux", "df -h", "systemctl status"]),
            "path": random.choice(["/var/log", "/etc/nginx", "/home/user", "/var/www"]),
            "destination": random.choice(["/backup", "/tmp", "/archive"]),
            "backup": random.choice(["/backup/daily", "/snapshots/latest"]),
            "problem": random.choice(["connection issue", "slow response", "memory leak", "disk space"]),
            "error": random.choice(["404 error", "connection timeout", "permission denied", "out of memory"]),
            "application": random.choice(["web app", "database", "API", "service"]),
            "setting": random.choice(["port", "timeout", "memory_limit", "max_connections"]),
            "value": random.choice(["8080", "30s", "512MB", "100"]),
            "parameter": random.choice(["max_connections", "timeout", "buffer_size"]),
            "action": random.choice(["restart a service", "check logs", "monitor CPU"]),
            "concept": random.choice(["load balancing", "SSL certificates", "firewall rules"]),
            "topic": random.choice(["nginx", "docker", "kubernetes", "monitoring"]),
            "resources": random.choice(["servers", "databases", "services", "containers"]),
            "system": random.choice(["load balancer", "database cluster", "web server"]),
            "usage": random.choice(["curl commands", "ssh keys", "cron jobs"]),
            "item": random.choice(["web server", "database", "application", "service"]),
            "metric": random.choice(["CPU usage", "disk space", "memory usage"]),
            "file": random.choice(["/etc/hostname", "/var/log/nginx/access.log", "/etc/passwd", "/proc/cpuinfo"]),
            "information": random.choice(["system info", "network config", "process list"]),
            "data": random.choice(["server list", "configuration", "status report"]),
            "id": random.choice(["server-001", "db-prod-01", "web-staging-02"]),
            "hostname": random.choice(["web-server", "db-primary", "load-balancer"]),
            "criteria": random.choice(["IP address", "hostname", "service type"]),
            "location": random.choice(["datacenter-1", "AWS us-east-1", "on-premises"]),
            "asset": random.choice(["server", "database", "load balancer"]),
            "network": random.choice(["192.168.1.0/24", "10.0.0.0/16", "production network"])
        }
        
        # Replace template variables
        for var, value in variables.items():
            template = template.replace(f"{{{var}}}", value)
        
        return template

    def _get_capabilities_for_action(self, category: str, action: str) -> List[str]:
        """Get appropriate capabilities for a category/action combination"""
        if category not in self.capability_mappings:
            return ["system_info"]  # Default fallback
        
        if action not in self.capability_mappings[category]:
            return ["system_info"]  # Default fallback
        
        base_capabilities = self.capability_mappings[category][action].copy()
        
        # Add some variation - sometimes include additional relevant capabilities
        if random.random() < 0.3:  # 30% chance of additional capabilities
            additional = random.choice([
                cap for cap in self.capabilities 
                if cap not in base_capabilities and self._is_compatible_capability(category, cap)
            ])
            if additional:
                base_capabilities.append(additional)
        
        return base_capabilities

    def _is_compatible_capability(self, category: str, capability: str) -> bool:
        """Check if a capability is compatible with a category"""
        compatibility = {
            "automation": ["service_management", "process_management", "system_info", "disk_management"],
            "monitoring": ["system_monitoring", "process_monitoring", "memory_monitoring", "disk_monitoring", "log_analysis"],
            "troubleshooting": ["log_analysis", "system_monitoring", "network_testing", "process_monitoring"],
            "configuration": ["system_info", "service_management", "disk_management"],
            "information": ["system_info", "infrastructure_info", "resource_listing"],
            "asset_management": ["asset_management", "asset_query", "resource_listing", "network_info"]
        }
        
        return capability in compatibility.get(category, [])

    def _generate_priority_examples(self) -> List[Dict[str, Any]]:
        """Generate high-priority examples that address the specific bypass issue"""
        priority_examples = [
            # File reading examples that were causing the bypass
            {
                "request": "Display contents of /etc/hostname",
                "expected_response": {
                    "category": "information",
                    "action": "provide_information", 
                    "confidence": 0.95,
                    "capabilities": ["system_info"]
                }
            },
            {
                "request": "Show me the contents of /etc/passwd",
                "expected_response": {
                    "category": "information",
                    "action": "provide_information",
                    "confidence": 0.93,
                    "capabilities": ["system_info"]
                }
            },
            {
                "request": "cat /var/log/nginx/access.log",
                "expected_response": {
                    "category": "information",
                    "action": "provide_information",
                    "confidence": 0.94,
                    "capabilities": ["system_info", "log_analysis"]
                }
            },
            {
                "request": "read file /proc/cpuinfo",
                "expected_response": {
                    "category": "information",
                    "action": "provide_information",
                    "confidence": 0.92,
                    "capabilities": ["system_info", "infrastructure_info"]
                }
            },
            # System monitoring examples  
            {
                "request": "check disk space on server",
                "expected_response": {
                    "category": "monitoring",
                    "action": "get_metrics",
                    "confidence": 0.91,
                    "capabilities": ["disk_monitoring", "system_monitoring"]
                }
            },
            {
                "request": "list running processes",
                "expected_response": {
                    "category": "information",
                    "action": "provide_information",
                    "confidence": 0.89,
                    "capabilities": ["process_monitoring", "system_info"]
                }
            },
            # Asset management examples
            {
                "request": "list all servers",
                "expected_response": {
                    "category": "asset_management",
                    "action": "list_servers",
                    "confidence": 0.96,
                    "capabilities": ["asset_management", "resource_listing"]
                }
            },
            {
                "request": "get server information",
                "expected_response": {
                    "category": "asset_management", 
                    "action": "get_asset_info",
                    "confidence": 0.88,
                    "capabilities": ["asset_management", "asset_query"]
                }
            }
        ]
        
        return priority_examples

    def save_training_data(self, examples: List[Dict[str, Any]], output_file: str):
        """Save training data in multiple formats"""
        output_path = Path(output_file)
        
        # JSON format for general use
        with open(output_path, 'w') as f:
            json.dump(examples, f, indent=2)
        
        # JSONL format for streaming/training
        jsonl_path = output_path.with_suffix('.jsonl')
        with open(jsonl_path, 'w') as f:
            for example in examples:
                f.write(json.dumps(example) + '\n')
        
        # CSV format for analysis
        csv_path = output_path.with_suffix('.csv')
        with open(csv_path, 'w') as f:
            f.write("request,category,action,confidence,capabilities\n")
            for example in examples:
                resp = example['expected_response']
                capabilities_str = '|'.join(resp['capabilities'])
                f.write(f'"{example["request"]}",{resp["category"]},{resp["action"]},{resp["confidence"]},"{capabilities_str}"\n')
        
        print(f"Training data saved to:")
        print(f"  JSON: {output_path}")
        print(f"  JSONL: {jsonl_path}")
        print(f"  CSV: {csv_path}")

    def generate_capability_statistics(self, examples: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate statistics about capability usage"""
        capability_counts = {}
        category_capability_counts = {}
        
        for example in examples:
            category = example['expected_response']['category']
            capabilities = example['expected_response']['capabilities']
            
            if category not in category_capability_counts:
                category_capability_counts[category] = {}
            
            for cap in capabilities:
                capability_counts[cap] = capability_counts.get(cap, 0) + 1
                category_capability_counts[category][cap] = category_capability_counts[category].get(cap, 0) + 1
        
        return {
            "total_examples": len(examples),
            "capability_distribution": capability_counts,
            "category_capability_distribution": category_capability_counts,
            "unique_capabilities": len(capability_counts),
            "avg_capabilities_per_example": sum(len(ex['expected_response']['capabilities']) for ex in examples) / len(examples)
        }

def main():
    """Generate comprehensive LLM training data"""
    print("🚀 Generating LLM Training Data for Intent Classification")
    print("=" * 60)
    
    generator = LLMTrainingDataGenerator()
    
    # Generate different sized datasets
    datasets = [
        (1000, "training_data_1k"),
        (5000, "training_data_5k"), 
        (10000, "training_data_10k"),
        (25000, "training_data_25k")
    ]
    
    for count, name in datasets:
        print(f"\n📊 Generating {count:,} training examples...")
        examples = generator.generate_training_examples(count)
        
        output_file = f"/home/opsconductor/opsconductor-ng/training_data/{name}.json"
        Path(output_file).parent.mkdir(exist_ok=True)
        
        generator.save_training_data(examples, output_file)
        
        # Generate statistics
        stats = generator.generate_capability_statistics(examples)
        print(f"✅ Generated {stats['total_examples']:,} examples")
        print(f"   📋 {stats['unique_capabilities']} unique capabilities")
        print(f"   📈 {stats['avg_capabilities_per_example']:.1f} avg capabilities per example")
        
        # Save statistics
        stats_file = f"/home/opsconductor/opsconductor-ng/training_data/{name}_stats.json"
        with open(stats_file, 'w') as f:
            json.dump(stats, f, indent=2)
    
    print(f"\n🎯 Training data generated successfully!")
    print(f"📁 Files saved to: /home/opsconductor/opsconductor-ng/training_data/")
    print(f"\n💡 Next steps:")
    print(f"   1. Use the JSONL files to fine-tune your LLM")
    print(f"   2. Focus on the priority examples for immediate fixes")
    print(f"   3. Monitor capability field population in Stage A output")

if __name__ == "__main__":
    main()