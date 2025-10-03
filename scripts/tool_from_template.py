#!/usr/bin/env python3
"""
Tool From Template
Quick tool creation from predefined templates

Usage:
    python tool_from_template.py <template_name> <tool_name> [options]

Templates:
    - simple_command: Simple command-line tool
    - api_tool: REST API integration tool
    - database_tool: Database query tool
    - monitoring_tool: System monitoring tool
    - automation_tool: Automation/orchestration tool
"""

import sys
import os
import argparse
import yaml
from pathlib import Path
from typing import Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline.services.tool_catalog_service import ToolCatalogService


# Template definitions
TEMPLATES = {
    'simple_command': {
        'description': 'Execute {tool_name} command',
        'platform': 'linux',
        'category': 'system',
        'defaults': {
            'accuracy_level': 'real-time',
            'freshness': 'live',
            'data_source': 'direct'
        },
        'dependencies': [
            {'name': '{tool_name}_binary', 'type': 'binary', 'required': True}
        ],
        'capabilities': [
            {
                'capability_name': '{tool_name}_execution',
                'description': 'Execute {tool_name} with various options',
                'patterns': [
                    {
                        'pattern_name': 'basic_execution',
                        'description': 'Basic {tool_name} execution',
                        'typical_use_cases': ['Run {tool_name} command'],
                        'time_estimate_ms': '1000',
                        'cost_estimate': '1',
                        'complexity_score': 0.3,
                        'scope': 'single',
                        'completeness': 'full',
                        'limitations': [],
                        'policy': {
                            'max_cost': 5,
                            'requires_approval': False,
                            'production_safe': True
                        },
                        'preference_match': {
                            'speed': 0.9,
                            'accuracy': 0.9,
                            'cost': 0.9,
                            'complexity': 0.8,
                            'completeness': 0.9
                        },
                        'required_inputs': [
                            {'name': 'command', 'type': 'string', 'required': True, 'description': 'Command to execute'}
                        ],
                        'expected_outputs': [
                            {'name': 'stdout', 'type': 'string', 'required': True, 'description': 'Command output'},
                            {'name': 'exit_code', 'type': 'integer', 'required': True, 'description': 'Exit code'}
                        ],
                        'examples': [
                            {
                                'description': 'Basic {tool_name} usage',
                                'input': '{{command: "{tool_name} --help"}}',
                                'output': '{{stdout: "...", exit_code: 0}}'
                            }
                        ]
                    }
                ]
            }
        ]
    },
    
    'api_tool': {
        'description': 'Interact with {tool_name} API',
        'platform': 'custom',
        'category': 'network',
        'defaults': {
            'accuracy_level': 'high',
            'freshness': 'live',
            'data_source': 'api'
        },
        'dependencies': [
            {'name': 'http_client', 'type': 'package', 'required': True},
            {'name': '{tool_name}_api_access', 'type': 'permission', 'required': True}
        ],
        'capabilities': [
            {
                'capability_name': 'api_query',
                'description': 'Query {tool_name} API',
                'patterns': [
                    {
                        'pattern_name': 'get_request',
                        'description': 'GET request to {tool_name} API',
                        'typical_use_cases': ['Fetch data from {tool_name}'],
                        'time_estimate_ms': '500 + 100*N',
                        'cost_estimate': 'ceil(N/10)',
                        'complexity_score': 0.4,
                        'scope': 'multiple',
                        'completeness': 'full',
                        'limitations': ['Rate limited', 'Requires authentication'],
                        'policy': {
                            'max_cost': 20,
                            'requires_approval': False,
                            'production_safe': True
                        },
                        'preference_match': {
                            'speed': 0.7,
                            'accuracy': 0.9,
                            'cost': 0.7,
                            'complexity': 0.6,
                            'completeness': 0.9
                        },
                        'required_inputs': [
                            {'name': 'endpoint', 'type': 'string', 'required': True, 'description': 'API endpoint'},
                            {'name': 'params', 'type': 'object', 'required': False, 'description': 'Query parameters'}
                        ],
                        'expected_outputs': [
                            {'name': 'data', 'type': 'object', 'required': True, 'description': 'Response data'},
                            {'name': 'status_code', 'type': 'integer', 'required': True, 'description': 'HTTP status'}
                        ],
                        'examples': [
                            {
                                'description': 'Fetch data from {tool_name}',
                                'input': '{{endpoint: "/api/v1/data", params: {{limit: 10}}}}',
                                'output': '{{data: [...], status_code: 200}}'
                            }
                        ]
                    }
                ]
            }
        ]
    },
    
    'database_tool': {
        'description': 'Query {tool_name} database',
        'platform': 'custom',
        'category': 'database',
        'defaults': {
            'accuracy_level': 'high',
            'freshness': 'cached',
            'data_source': 'database'
        },
        'dependencies': [
            {'name': '{tool_name}_client', 'type': 'package', 'required': True},
            {'name': '{tool_name}_connection', 'type': 'service', 'required': True}
        ],
        'capabilities': [
            {
                'capability_name': 'database_query',
                'description': 'Execute queries on {tool_name}',
                'patterns': [
                    {
                        'pattern_name': 'select_query',
                        'description': 'SELECT query on {tool_name}',
                        'typical_use_cases': ['Fetch data from {tool_name}'],
                        'time_estimate_ms': '100 + 50*N',
                        'cost_estimate': 'ceil(N/100)',
                        'complexity_score': 0.5,
                        'scope': 'multiple',
                        'completeness': 'full',
                        'limitations': ['Connection pool limited', 'Query timeout'],
                        'policy': {
                            'max_cost': 15,
                            'requires_approval': False,
                            'production_safe': True
                        },
                        'preference_match': {
                            'speed': 0.8,
                            'accuracy': 1.0,
                            'cost': 0.8,
                            'complexity': 0.7,
                            'completeness': 1.0
                        },
                        'required_inputs': [
                            {'name': 'query', 'type': 'string', 'required': True, 'description': 'SQL query'},
                            {'name': 'params', 'type': 'array', 'required': False, 'description': 'Query parameters'}
                        ],
                        'expected_outputs': [
                            {'name': 'rows', 'type': 'array', 'required': True, 'description': 'Query results'},
                            {'name': 'row_count', 'type': 'integer', 'required': True, 'description': 'Number of rows'}
                        ],
                        'examples': [
                            {
                                'description': 'Query {tool_name} database',
                                'input': '{{query: "SELECT * FROM users LIMIT 10"}}',
                                'output': '{{rows: [...], row_count: 10}}'
                            }
                        ]
                    }
                ]
            }
        ]
    },
    
    'monitoring_tool': {
        'description': 'Monitor system using {tool_name}',
        'platform': 'linux',
        'category': 'monitoring',
        'defaults': {
            'accuracy_level': 'real-time',
            'freshness': 'live',
            'data_source': 'direct'
        },
        'dependencies': [
            {'name': '{tool_name}_agent', 'type': 'service', 'required': True}
        ],
        'capabilities': [
            {
                'capability_name': 'system_monitoring',
                'description': 'Monitor system metrics with {tool_name}',
                'patterns': [
                    {
                        'pattern_name': 'get_metrics',
                        'description': 'Retrieve system metrics',
                        'typical_use_cases': ['Check system health', 'Monitor resources'],
                        'time_estimate_ms': '200',
                        'cost_estimate': '1',
                        'complexity_score': 0.3,
                        'scope': 'single',
                        'completeness': 'full',
                        'limitations': ['Requires agent running'],
                        'policy': {
                            'max_cost': 5,
                            'requires_approval': False,
                            'production_safe': True
                        },
                        'preference_match': {
                            'speed': 0.9,
                            'accuracy': 0.9,
                            'cost': 0.9,
                            'complexity': 0.7,
                            'completeness': 0.9
                        },
                        'required_inputs': [
                            {'name': 'metric_type', 'type': 'string', 'required': True, 'description': 'Type of metric to retrieve'}
                        ],
                        'expected_outputs': [
                            {'name': 'metrics', 'type': 'object', 'required': True, 'description': 'Metric values'},
                            {'name': 'timestamp', 'type': 'string', 'required': True, 'description': 'Collection time'}
                        ],
                        'examples': [
                            {
                                'description': 'Get CPU metrics',
                                'input': '{{metric_type: "cpu"}}',
                                'output': '{{metrics: {{usage: 45.2, cores: 8}}, timestamp: "2025-10-03T19:00:00Z"}}'
                            }
                        ]
                    }
                ]
            }
        ]
    },
    
    'automation_tool': {
        'description': 'Automate tasks with {tool_name}',
        'platform': 'custom',
        'category': 'automation',
        'defaults': {
            'accuracy_level': 'high',
            'freshness': 'live',
            'data_source': 'direct'
        },
        'dependencies': [
            {'name': '{tool_name}_runtime', 'type': 'service', 'required': True}
        ],
        'capabilities': [
            {
                'capability_name': 'task_automation',
                'description': 'Automate tasks using {tool_name}',
                'patterns': [
                    {
                        'pattern_name': 'execute_workflow',
                        'description': 'Execute automation workflow',
                        'typical_use_cases': ['Run automated tasks', 'Orchestrate operations'],
                        'time_estimate_ms': '1000 + 500*N',
                        'cost_estimate': 'N',
                        'complexity_score': 0.6,
                        'scope': 'multiple',
                        'completeness': 'full',
                        'limitations': ['Async execution', 'May require approval'],
                        'policy': {
                            'max_cost': 25,
                            'requires_approval': True,
                            'production_safe': False
                        },
                        'preference_match': {
                            'speed': 0.6,
                            'accuracy': 0.8,
                            'cost': 0.6,
                            'complexity': 0.5,
                            'completeness': 0.9
                        },
                        'required_inputs': [
                            {'name': 'workflow', 'type': 'string', 'required': True, 'description': 'Workflow definition'},
                            {'name': 'parameters', 'type': 'object', 'required': False, 'description': 'Workflow parameters'}
                        ],
                        'expected_outputs': [
                            {'name': 'result', 'type': 'object', 'required': True, 'description': 'Execution result'},
                            {'name': 'status', 'type': 'string', 'required': True, 'description': 'Execution status'}
                        ],
                        'examples': [
                            {
                                'description': 'Execute workflow',
                                'input': '{{workflow: "deploy_app", parameters: {{version: "1.0"}}}}',
                                'output': '{{result: {{deployed: true}}, status: "success"}}'
                            }
                        ]
                    }
                ]
            }
        ]
    }
}


def create_tool_from_template(
    template_name: str,
    tool_name: str,
    version: str = "1.0",
    author: str = None,
    save_to_db: bool = True,
    save_to_yaml: bool = False
):
    """Create a tool from a template"""
    
    if template_name not in TEMPLATES:
        print(f"❌ Unknown template: {template_name}")
        print(f"Available templates: {', '.join(TEMPLATES.keys())}")
        sys.exit(1)
    
    print(f"🛠️  Creating tool '{tool_name}' from template '{template_name}'...")
    
    # Get template
    template = TEMPLATES[template_name]
    
    # Replace placeholders
    tool_def = _replace_placeholders(template, tool_name)
    
    # Add metadata
    tool_def['tool_name'] = tool_name
    tool_def['version'] = version
    tool_def['status'] = 'active'
    tool_def['enabled'] = True
    tool_def['metadata'] = {}
    
    if author:
        tool_def['metadata']['author'] = author
        tool_def['created_by'] = author
    else:
        tool_def['created_by'] = os.getenv('USER', 'tool_generator')
    
    tool_def['metadata']['template'] = template_name
    tool_def['metadata']['tags'] = [template_name.replace('_', '-')]
    
    # Save
    if save_to_db:
        _save_to_database(tool_def)
    
    if save_to_yaml:
        _save_to_yaml(tool_def)
    
    print(f"✅ Tool '{tool_name}' created successfully!")


def _replace_placeholders(obj: Any, tool_name: str) -> Any:
    """Recursively replace {tool_name} placeholders"""
    if isinstance(obj, dict):
        return {k: _replace_placeholders(v, tool_name) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_replace_placeholders(item, tool_name) for item in obj]
    elif isinstance(obj, str):
        return obj.replace('{tool_name}', tool_name)
    else:
        return obj


def _save_to_database(tool_def: Dict[str, Any]):
    """Save tool to database"""
    print("  📊 Saving to database...")
    
    try:
        service = ToolCatalogService()
        
        # Create tool (status and enabled are set via database defaults)
        tool_id = service.create_tool(
            tool_name=tool_def['tool_name'],
            version=tool_def['version'],
            description=tool_def['description'],
            platform=tool_def['platform'],
            category=tool_def['category'],
            defaults=tool_def['defaults'],
            dependencies=tool_def['dependencies'],
            metadata=tool_def['metadata'],
            created_by=tool_def['created_by']
        )
        
        # Add capabilities and patterns
        for capability in tool_def['capabilities']:
            cap_id = service.add_capability(
                tool_id=tool_id,
                capability_name=capability['capability_name'],
                description=capability['description']
            )
            
            for pattern in capability['patterns']:
                service.add_pattern(
                    capability_id=cap_id,
                    pattern_name=pattern['pattern_name'],
                    description=pattern['description'],
                    typical_use_cases=pattern['typical_use_cases'],
                    time_estimate_ms=pattern['time_estimate_ms'],
                    cost_estimate=pattern['cost_estimate'],
                    complexity_score=pattern['complexity_score'],
                    scope=pattern['scope'],
                    completeness=pattern['completeness'],
                    limitations=pattern['limitations'],
                    policy=pattern['policy'],
                    preference_match=pattern['preference_match'],
                    required_inputs=pattern['required_inputs'],
                    expected_outputs=pattern['expected_outputs']
                )
        
        print(f"  ✓ Tool saved to database (ID: {tool_id})")
        
    except Exception as e:
        print(f"  ❌ Failed to save to database: {e}")
        raise


def _save_to_yaml(tool_def: Dict[str, Any]):
    """Save tool to YAML file"""
    print("  📄 Saving to YAML...")
    
    # Determine output path
    tools_dir = Path(__file__).parent.parent / "pipeline" / "config" / "tools"
    tools_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = tools_dir / f"{tool_def['tool_name']}.yaml"
    
    # Save to file
    with open(output_path, 'w') as f:
        yaml.dump(tool_def, f, default_flow_style=False, sort_keys=False)
    
    print(f"  ✓ Tool saved to {output_path}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Create a tool from a predefined template',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Available templates:
  simple_command   - Simple command-line tool
  api_tool         - REST API integration tool
  database_tool    - Database query tool
  monitoring_tool  - System monitoring tool
  automation_tool  - Automation/orchestration tool

Examples:
  # Create a simple command tool
  python tool_from_template.py simple_command ls --author "John Doe"
  
  # Create an API tool and save to YAML
  python tool_from_template.py api_tool github_api --yaml
  
  # Create a database tool with custom version
  python tool_from_template.py database_tool mysql_query --version 2.0
        """
    )
    
    parser.add_argument('template', help='Template name')
    parser.add_argument('tool_name', help='Tool name')
    parser.add_argument('--version', default='1.0', help='Tool version (default: 1.0)')
    parser.add_argument('--author', help='Tool author')
    parser.add_argument('--no-db', action='store_true', help='Do not save to database')
    parser.add_argument('--yaml', action='store_true', help='Also save to YAML file')
    
    args = parser.parse_args()
    
    create_tool_from_template(
        template_name=args.template,
        tool_name=args.tool_name,
        version=args.version,
        author=args.author,
        save_to_db=not args.no_db,
        save_to_yaml=args.yaml
    )


if __name__ == '__main__':
    main()