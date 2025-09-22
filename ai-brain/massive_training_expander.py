#!/usr/bin/env python3
"""
🚀 MASSIVE TRAINING DATA EXPANDER
Generate thousands of training examples for comprehensive AI learning
"""

import random
import json
from typing import List, Dict, Any
from datetime import datetime

class MassiveTrainingExpander:
    """Generate massive amounts of training data for AI learning"""
    
    def __init__(self):
        self.generated_examples = []
        
        # Massive intent categories with extensive variations
        self.intent_templates = {
            'asset_query': {
                'patterns': [
                    "show me {asset_type}",
                    "list all {asset_type}",
                    "what {asset_type} do we have",
                    "display {asset_type} inventory",
                    "get {asset_type} information",
                    "find {asset_type} in our system",
                    "retrieve {asset_type} data",
                    "show {asset_type} details",
                    "give me {asset_type} overview",
                    "present {asset_type} summary",
                    "enumerate {asset_type}",
                    "catalog {asset_type}",
                    "inventory {asset_type}",
                    "browse {asset_type}",
                    "explore {asset_type}",
                    "discover {asset_type}",
                    "locate {asset_type}",
                    "identify {asset_type}",
                    "reveal {asset_type}",
                    "expose {asset_type}"
                ],
                'asset_types': [
                    'servers', 'systems', 'machines', 'hosts', 'nodes', 'instances',
                    'infrastructure', 'hardware', 'equipment', 'devices', 'assets',
                    'production servers', 'development servers', 'test servers',
                    'web servers', 'database servers', 'application servers',
                    'linux servers', 'windows servers', 'unix servers',
                    'virtual machines', 'containers', 'pods', 'clusters',
                    'network devices', 'switches', 'routers', 'firewalls',
                    'load balancers', 'storage systems', 'backup systems',
                    'monitoring systems', 'security systems', 'cloud resources'
                ],
                'confidence': 0.9
            },
            
            'troubleshooting': {
                'patterns': [
                    "{issue_type} is {problem_state}",
                    "fix {issue_type} {problem_state}",
                    "resolve {issue_type} issue",
                    "troubleshoot {issue_type}",
                    "diagnose {issue_type} problem",
                    "repair {issue_type}",
                    "investigate {issue_type}",
                    "debug {issue_type}",
                    "analyze {issue_type} failure",
                    "solve {issue_type} error",
                    "address {issue_type} malfunction",
                    "handle {issue_type} outage",
                    "manage {issue_type} incident",
                    "restore {issue_type} service",
                    "recover {issue_type} system",
                    "remediate {issue_type}",
                    "correct {issue_type}",
                    "mend {issue_type}",
                    "patch {issue_type}",
                    "heal {issue_type}"
                ],
                'issue_types': [
                    'server', 'service', 'application', 'database', 'network',
                    'website', 'API', 'connection', 'performance', 'memory',
                    'CPU', 'disk', 'storage', 'backup', 'security', 'firewall',
                    'load balancer', 'DNS', 'SSL', 'certificate', 'authentication',
                    'authorization', 'logging', 'monitoring', 'alerting'
                ],
                'problem_states': [
                    'down', 'slow', 'failing', 'broken', 'unresponsive',
                    'crashed', 'hanging', 'frozen', 'stuck', 'offline',
                    'unavailable', 'inaccessible', 'corrupted', 'damaged',
                    'malfunctioning', 'degraded', 'unstable', 'intermittent'
                ],
                'confidence': 0.85
            },
            
            'automation_request': {
                'patterns': [
                    "create {automation_type} for {target}",
                    "automate {task} on {target}",
                    "setup {automation_type} automation",
                    "build {automation_type} workflow",
                    "implement {automation_type} process",
                    "configure {automation_type} job",
                    "establish {automation_type} routine",
                    "deploy {automation_type} script",
                    "schedule {automation_type} task",
                    "orchestrate {automation_type}",
                    "streamline {automation_type}",
                    "systematize {automation_type}",
                    "mechanize {automation_type}",
                    "robotize {automation_type}",
                    "program {automation_type}",
                    "script {automation_type}",
                    "batch {automation_type}",
                    "queue {automation_type}",
                    "pipeline {automation_type}",
                    "workflow {automation_type}"
                ],
                'automation_types': [
                    'backup', 'deployment', 'monitoring', 'patching', 'updates',
                    'maintenance', 'cleanup', 'archival', 'replication', 'sync',
                    'migration', 'scaling', 'provisioning', 'configuration',
                    'security scan', 'vulnerability assessment', 'compliance check',
                    'performance test', 'health check', 'log rotation',
                    'certificate renewal', 'password rotation', 'user management'
                ],
                'targets': [
                    'all servers', 'production systems', 'development environment',
                    'database cluster', 'web farm', 'application tier',
                    'network infrastructure', 'cloud resources', 'containers',
                    'virtual machines', 'kubernetes cluster', 'docker swarm'
                ],
                'confidence': 0.8
            },
            
            'monitoring': {
                'patterns': [
                    "monitor {metric} on {target}",
                    "setup {monitoring_type} monitoring",
                    "track {metric} performance",
                    "watch {metric} levels",
                    "observe {metric} trends",
                    "measure {metric} usage",
                    "gauge {metric} consumption",
                    "survey {metric} statistics",
                    "inspect {metric} data",
                    "examine {metric} patterns",
                    "review {metric} history",
                    "analyze {metric} behavior",
                    "assess {metric} health",
                    "evaluate {metric} status",
                    "check {metric} conditions",
                    "verify {metric} thresholds",
                    "validate {metric} limits",
                    "confirm {metric} boundaries",
                    "ensure {metric} compliance",
                    "maintain {metric} oversight"
                ],
                'metrics': [
                    'CPU', 'memory', 'disk', 'network', 'bandwidth', 'latency',
                    'throughput', 'response time', 'error rate', 'uptime',
                    'availability', 'performance', 'load', 'capacity',
                    'utilization', 'temperature', 'power', 'storage',
                    'connections', 'sessions', 'transactions', 'queries'
                ],
                'monitoring_types': [
                    'real-time', 'continuous', 'periodic', 'scheduled',
                    'automated', 'proactive', 'reactive', 'predictive',
                    'comprehensive', 'detailed', 'granular', 'high-level'
                ],
                'targets': [
                    'servers', 'applications', 'databases', 'networks',
                    'services', 'infrastructure', 'cloud resources',
                    'containers', 'microservices', 'APIs', 'endpoints'
                ],
                'confidence': 0.75
            },
            
            'security': {
                'patterns': [
                    "apply {security_action} to {target}",
                    "implement {security_measure}",
                    "configure {security_feature}",
                    "enable {security_protection}",
                    "setup {security_system}",
                    "deploy {security_solution}",
                    "install {security_tool}",
                    "activate {security_control}",
                    "enforce {security_policy}",
                    "establish {security_protocol}",
                    "strengthen {security_aspect}",
                    "harden {security_target}",
                    "secure {security_component}",
                    "protect {security_asset}",
                    "safeguard {security_resource}",
                    "shield {security_element}",
                    "defend {security_infrastructure}",
                    "fortify {security_perimeter}",
                    "reinforce {security_boundary}",
                    "bolster {security_framework}"
                ],
                'security_actions': [
                    'patches', 'updates', 'fixes', 'hotfixes', 'security updates',
                    'vulnerability patches', 'critical updates', 'emergency patches'
                ],
                'security_measures': [
                    'firewall rules', 'access controls', 'authentication',
                    'authorization', 'encryption', 'SSL certificates',
                    'VPN connections', 'intrusion detection', 'antivirus',
                    'malware protection', 'backup encryption', 'audit logging'
                ],
                'security_features': [
                    'two-factor authentication', 'single sign-on', 'RBAC',
                    'network segmentation', 'DMZ', 'honeypots', 'sandboxing'
                ],
                'confidence': 0.8
            },
            
            'performance': {
                'patterns': [
                    "optimize {performance_target}",
                    "tune {performance_aspect}",
                    "improve {performance_metric}",
                    "enhance {performance_component}",
                    "boost {performance_element}",
                    "accelerate {performance_process}",
                    "speed up {performance_operation}",
                    "streamline {performance_workflow}",
                    "refine {performance_system}",
                    "polish {performance_feature}",
                    "perfect {performance_function}",
                    "maximize {performance_efficiency}",
                    "minimize {performance_overhead}",
                    "reduce {performance_bottleneck}",
                    "eliminate {performance_constraint}",
                    "resolve {performance_issue}",
                    "address {performance_problem}",
                    "fix {performance_degradation}",
                    "repair {performance_slowdown}",
                    "restore {performance_baseline}"
                ],
                'performance_targets': [
                    'database queries', 'web server response', 'application startup',
                    'network throughput', 'disk I/O', 'memory usage',
                    'CPU utilization', 'cache hit ratio', 'load balancing',
                    'connection pooling', 'query execution', 'data processing'
                ],
                'confidence': 0.75
            },
            
            'backup_recovery': {
                'patterns': [
                    "create {backup_type} backup",
                    "setup {backup_schedule} backups",
                    "configure {backup_strategy}",
                    "implement {backup_solution}",
                    "establish {backup_routine}",
                    "schedule {backup_frequency} backups",
                    "automate {backup_process}",
                    "manage {backup_lifecycle}",
                    "maintain {backup_integrity}",
                    "verify {backup_validity}",
                    "test {backup_restoration}",
                    "validate {backup_completeness}",
                    "ensure {backup_reliability}",
                    "guarantee {backup_availability}",
                    "secure {backup_storage}",
                    "encrypt {backup_data}",
                    "compress {backup_files}",
                    "archive {backup_history}",
                    "replicate {backup_copies}",
                    "synchronize {backup_mirrors}"
                ],
                'backup_types': [
                    'full', 'incremental', 'differential', 'snapshot',
                    'continuous', 'real-time', 'scheduled', 'automated'
                ],
                'backup_schedules': [
                    'daily', 'weekly', 'monthly', 'hourly', 'continuous',
                    'real-time', 'on-demand', 'triggered', 'event-based'
                ],
                'confidence': 0.8
            }
        }
        
        # Contextual scenarios for realistic training
        self.contextual_scenarios = [
            {
                'context': 'morning system check',
                'queries': [
                    "good morning, show me system status",
                    "morning report on all servers",
                    "daily infrastructure overview",
                    "start of day system health check"
                ]
            },
            {
                'context': 'incident response',
                'queries': [
                    "emergency - server cluster is down",
                    "urgent: database connection failing",
                    "critical alert: network outage detected",
                    "immediate attention: service unavailable"
                ]
            },
            {
                'context': 'maintenance window',
                'queries': [
                    "prepare systems for maintenance",
                    "schedule downtime for updates",
                    "maintenance mode activation",
                    "planned outage coordination"
                ]
            },
            {
                'context': 'capacity planning',
                'queries': [
                    "analyze resource utilization trends",
                    "forecast infrastructure needs",
                    "capacity planning assessment",
                    "growth projection analysis"
                ]
            },
            {
                'context': 'security audit',
                'queries': [
                    "security compliance check",
                    "vulnerability assessment report",
                    "audit trail analysis",
                    "security posture evaluation"
                ]
            }
        ]
        
        # Advanced linguistic variations
        self.linguistic_variations = {
            'formality_levels': ['formal', 'casual', 'technical', 'business'],
            'question_types': ['direct', 'indirect', 'implied', 'contextual'],
            'urgency_levels': ['low', 'medium', 'high', 'critical'],
            'specificity_levels': ['general', 'specific', 'detailed', 'granular']
        }
    
    async def generate_massive_expansion(self, target_examples: int = 2000) -> List[Dict[str, Any]]:
        """Generate massive training data expansion"""
        
        print(f"🚀 Generating {target_examples} training examples...")
        
        examples = []
        
        # Generate template-based examples
        template_examples = await self._generate_template_examples(target_examples // 3)
        examples.extend(template_examples)
        
        # Generate contextual examples
        contextual_examples = await self._generate_contextual_examples(target_examples // 3)
        examples.extend(contextual_examples)
        
        # Generate linguistic variations
        variation_examples = await self._generate_linguistic_variations(target_examples // 3)
        examples.extend(variation_examples)
        
        # Generate edge cases and complex scenarios
        edge_examples = await self._generate_edge_cases(target_examples - len(examples))
        examples.extend(edge_examples)
        
        print(f"✅ Generated {len(examples)} total training examples")
        
        return examples
    
    async def _generate_template_examples(self, count: int) -> List[Dict[str, Any]]:
        """Generate examples from templates"""
        examples = []
        
        for _ in range(count):
            intent = random.choice(list(self.intent_templates.keys()))
            template_data = self.intent_templates[intent]
            
            pattern = random.choice(template_data['patterns'])
            
            # Fill in template variables
            if '{asset_type}' in pattern:
                asset_type = random.choice(template_data['asset_types'])
                user_input = pattern.format(asset_type=asset_type)
            elif '{issue_type}' in pattern and '{problem_state}' in pattern:
                issue_type = random.choice(template_data['issue_types'])
                problem_state = random.choice(template_data['problem_states'])
                user_input = pattern.format(issue_type=issue_type, problem_state=problem_state)
            elif '{automation_type}' in pattern and '{target}' in pattern:
                automation_type = random.choice(template_data['automation_types'])
                target = random.choice(template_data['targets'])
                user_input = pattern.format(automation_type=automation_type, target=target)
            elif '{metric}' in pattern and '{target}' in pattern:
                metric = random.choice(template_data['metrics'])
                target = random.choice(template_data['targets'])
                user_input = pattern.format(metric=metric, target=target)
            elif '{monitoring_type}' in pattern:
                monitoring_type = random.choice(template_data['monitoring_types'])
                user_input = pattern.format(monitoring_type=monitoring_type)
            else:
                # Handle other template variables
                for key, values in template_data.items():
                    if key != 'patterns' and key != 'confidence' and f'{{{key[:-1]}}' in pattern:
                        value = random.choice(values)
                        user_input = pattern.format(**{key[:-1]: value})
                        break
                else:
                    user_input = pattern
            
            examples.append({
                'user_input': user_input,
                'intent': intent,
                'confidence': template_data['confidence'] + random.uniform(-0.1, 0.1),
                'source': 'template_generation'
            })
        
        return examples
    
    async def _generate_contextual_examples(self, count: int) -> List[Dict[str, Any]]:
        """Generate contextual scenario examples"""
        examples = []
        
        for _ in range(count):
            scenario = random.choice(self.contextual_scenarios)
            query = random.choice(scenario['queries'])
            
            # Determine intent based on query content
            intent = self._infer_intent_from_query(query)
            confidence = random.uniform(0.7, 0.9)
            
            examples.append({
                'user_input': query,
                'intent': intent,
                'confidence': confidence,
                'context': scenario['context'],
                'source': 'contextual_generation'
            })
        
        return examples
    
    async def _generate_linguistic_variations(self, count: int) -> List[Dict[str, Any]]:
        """Generate linguistic variations"""
        examples = []
        
        base_queries = [
            "show servers", "list systems", "fix server", "create backup",
            "monitor performance", "apply patches", "optimize database"
        ]
        
        for _ in range(count):
            base_query = random.choice(base_queries)
            
            # Apply linguistic variations
            formality = random.choice(self.linguistic_variations['formality_levels'])
            question_type = random.choice(self.linguistic_variations['question_types'])
            urgency = random.choice(self.linguistic_variations['urgency_levels'])
            
            varied_query = self._apply_linguistic_variation(
                base_query, formality, question_type, urgency
            )
            
            intent = self._infer_intent_from_query(varied_query)
            confidence = random.uniform(0.6, 0.8)
            
            examples.append({
                'user_input': varied_query,
                'intent': intent,
                'confidence': confidence,
                'formality': formality,
                'question_type': question_type,
                'urgency': urgency,
                'source': 'linguistic_variation'
            })
        
        return examples
    
    async def _generate_edge_cases(self, count: int) -> List[Dict[str, Any]]:
        """Generate edge cases and complex scenarios"""
        examples = []
        
        edge_patterns = [
            "can you help me with {task}?",
            "I need assistance with {problem}",
            "what should I do about {issue}?",
            "how do I handle {situation}?",
            "please help me {action}",
            "I'm having trouble with {component}",
            "could you guide me through {process}?",
            "what's the best way to {objective}?",
            "I need to {requirement} but don't know how",
            "can you walk me through {procedure}?"
        ]
        
        tasks = [
            "server management", "system monitoring", "backup creation",
            "performance tuning", "security hardening", "troubleshooting",
            "automation setup", "network configuration", "database optimization"
        ]
        
        for _ in range(count):
            pattern = random.choice(edge_patterns)
            task = random.choice(tasks)
            
            user_input = pattern.format(
                task=task, problem=task, issue=task, situation=task,
                action=task, component=task, process=task, objective=task,
                requirement=task, procedure=task
            )
            
            intent = self._infer_intent_from_query(user_input)
            confidence = random.uniform(0.5, 0.7)
            
            examples.append({
                'user_input': user_input,
                'intent': intent,
                'confidence': confidence,
                'source': 'edge_case_generation'
            })
        
        return examples
    
    def _infer_intent_from_query(self, query: str) -> str:
        """Infer intent from query content"""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['show', 'list', 'display', 'get', 'find']):
            return 'asset_query'
        elif any(word in query_lower for word in ['fix', 'repair', 'troubleshoot', 'resolve']):
            return 'troubleshooting'
        elif any(word in query_lower for word in ['create', 'setup', 'automate', 'build']):
            return 'automation_request'
        elif any(word in query_lower for word in ['monitor', 'track', 'watch', 'observe']):
            return 'monitoring'
        elif any(word in query_lower for word in ['security', 'patch', 'secure', 'protect']):
            return 'security'
        elif any(word in query_lower for word in ['optimize', 'tune', 'improve', 'enhance']):
            return 'performance'
        elif any(word in query_lower for word in ['backup', 'restore', 'recover', 'archive']):
            return 'backup_recovery'
        elif any(word in query_lower for word in ['hello', 'hi', 'good morning', 'hey']):
            return 'greeting'
        elif any(word in query_lower for word in ['help', 'assist', 'guide', 'support']):
            return 'general_help'
        else:
            return 'general_help'
    
    def _apply_linguistic_variation(self, base_query: str, formality: str, 
                                  question_type: str, urgency: str) -> str:
        """Apply linguistic variations to base query"""
        
        query = base_query
        
        # Apply formality
        if formality == 'formal':
            query = f"Could you please {query}"
        elif formality == 'casual':
            query = f"hey, {query}"
        elif formality == 'technical':
            query = f"execute {query} operation"
        elif formality == 'business':
            query = f"I need to {query} for business requirements"
        
        # Apply urgency
        if urgency == 'high':
            query = f"urgent: {query}"
        elif urgency == 'critical':
            query = f"emergency - {query} immediately"
        
        # Apply question type
        if question_type == 'indirect':
            query = f"I was wondering if you could {query}"
        elif question_type == 'implied':
            query = f"it would be great to {query}"
        
        return query

# Add method to InternetTrainingHarvester
async def generate_massive_training_expansion(self) -> List[Dict[str, Any]]:
    """Generate massive training expansion using the expander"""
    expander = MassiveTrainingExpander()
    return await expander.generate_massive_expansion(target_examples=2000)

# Monkey patch the method
import sys
if 'internet_training_harvester' in sys.modules:
    sys.modules['internet_training_harvester'].InternetTrainingHarvester.generate_massive_training_expansion = generate_massive_training_expansion