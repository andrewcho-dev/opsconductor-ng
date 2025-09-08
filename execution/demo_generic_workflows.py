"""
Demo: Creating Workflows with Generic Blocks
Shows how easy it is to build complex workflows using our generic block system
"""

import asyncio
import json
from datetime import datetime
from .connection_manager import connection_manager
from .complete_generic_block_executor import complete_generic_block_executor


class GenericWorkflowBuilder:
    """Helper class to build workflows using generic blocks"""
    
    def __init__(self):
        self.blocks = []
        self.connections = []
        self.targets = {}
    
    def add_target(self, target_id: str, config: dict):
        """Add a target system"""
        self.targets[target_id] = config
        connection_manager.register_target(target_id, config)
        return self
    
    def add_block(self, block_id: str, block_type: str, config: dict):
        """Add a block to the workflow"""
        block = {
            "id": block_id,
            "type": block_type,
            "config": config
        }
        self.blocks.append(block)
        return self
    
    def add_connection(self, from_block: str, to_block: str, connection_type: str = "flow"):
        """Add a connection between blocks"""
        connection = {
            "from": from_block,
            "to": to_block,
            "type": connection_type
        }
        self.connections.append(connection)
        return self
    
    async def execute_workflow(self, initial_data: dict = None):
        """Execute the workflow"""
        if initial_data is None:
            initial_data = {}
        
        print(f"🚀 Executing workflow with {len(self.blocks)} blocks...")
        
        # Simple sequential execution for demo
        current_data = initial_data
        results = []
        
        for block in self.blocks:
            print(f"  📦 Executing block: {block['id']} ({block['type']})")
            
            result = await complete_generic_block_executor.execute_block(
                block['type'],
                block['config'],
                current_data
            )
            
            results.append({
                "block_id": block['id'],
                "block_type": block['type'],
                "success": result['success'],
                "result": result
            })
            
            # Pass result data to next block
            if result['success'] and 'result' in result:
                current_data.update(result['result'])
            
            status = "✅" if result['success'] else "❌"
            print(f"    {status} Result: {result['success']}")
        
        return {
            "workflow_success": all(r['success'] for r in results),
            "blocks_executed": len(results),
            "successful_blocks": len([r for r in results if r['success']]),
            "results": results,
            "final_data": current_data
        }


async def demo_simple_server_health_check():
    """Demo: Simple server health check workflow"""
    print("🏥 Demo: Simple Server Health Check Workflow")
    print("=" * 50)
    
    workflow = GenericWorkflowBuilder()
    
    # Add target servers
    workflow.add_target('web-server-01', {
        'hostname': '192.168.1.10',
        'os_type': 'linux',
        'default_connection': 'ssh',
        'username': 'admin',
        'private_key': '/path/to/key.pem'
    })
    
    # Build workflow
    workflow.add_block('start', 'flow.start', {
        'name': 'Server Health Check',
        'trigger_types': ['manual', 'schedule']
    })
    
    workflow.add_block('check-disk', 'action.command', {
        'target': 'web-server-01',
        'command': 'df -h /',
        'timeout_seconds': 30
    })
    
    workflow.add_block('check-memory', 'action.command', {
        'target': 'web-server-01',
        'command': 'free -m',
        'timeout_seconds': 30
    })
    
    workflow.add_block('check-load', 'action.command', {
        'target': 'web-server-01',
        'command': 'uptime',
        'timeout_seconds': 30
    })
    
    workflow.add_block('analyze-health', 'data.transform', {
        'script': '''
// Analyze server health data
const diskOutput = input.stdout || '';
const memoryOutput = input.memory_stdout || '';
const loadOutput = input.load_stdout || '';

// Simple health analysis
const healthScore = 100; // Would calculate based on actual metrics
const status = healthScore > 80 ? 'healthy' : healthScore > 60 ? 'warning' : 'critical';

result = {
    health_score: healthScore,
    status: status,
    disk_info: diskOutput,
    memory_info: memoryOutput,
    load_info: loadOutput,
    checked_at: new Date().toISOString()
};
        '''
    })
    
    workflow.add_block('send-report', 'action.notification', {
        'notification_type': 'email',
        'recipients': ['admin@company.com'],
        'subject': 'Server Health Report - {{data.status}}',
        'message': 'Server health check completed. Status: {{data.status}}, Score: {{data.health_score}}',
        'priority': 'normal'
    })
    
    workflow.add_block('end', 'flow.end', {
        'name': 'Health Check Complete',
        'save_result': True,
        'result_name': 'health_check_result'
    })
    
    # Execute workflow
    result = await workflow.execute_workflow()
    
    print(f"\n📊 Workflow Result:")
    print(f"  Success: {result['workflow_success']}")
    print(f"  Blocks: {result['successful_blocks']}/{result['blocks_executed']}")
    
    return result


async def demo_multi_server_deployment():
    """Demo: Multi-server application deployment"""
    print("🚀 Demo: Multi-Server Application Deployment")
    print("=" * 50)
    
    workflow = GenericWorkflowBuilder()
    
    # Add multiple target servers
    servers = [
        {'id': 'web-01', 'ip': '192.168.1.10', 'role': 'web'},
        {'id': 'web-02', 'ip': '192.168.1.11', 'role': 'web'},
        {'id': 'db-01', 'ip': '192.168.1.20', 'role': 'database'}
    ]
    
    for server in servers:
        workflow.add_target(server['id'], {
            'hostname': server['ip'],
            'os_type': 'linux',
            'default_connection': 'ssh',
            'username': 'deploy',
            'private_key': '/path/to/deploy.key'
        })
    
    # Build deployment workflow
    workflow.add_block('start', 'flow.start', {
        'name': 'Application Deployment',
        'trigger_types': ['manual', 'webhook']
    })
    
    # Pre-deployment checks
    workflow.add_block('check-web-01', 'action.command', {
        'target': 'web-01',
        'command': 'systemctl is-active nginx',
        'timeout_seconds': 30
    })
    
    workflow.add_block('check-web-02', 'action.command', {
        'target': 'web-02',
        'command': 'systemctl is-active nginx',
        'timeout_seconds': 30
    })
    
    workflow.add_block('check-database', 'action.command', {
        'target': 'db-01',
        'command': 'systemctl is-active postgresql',
        'timeout_seconds': 30
    })
    
    # Deployment steps
    workflow.add_block('deploy-web-01', 'action.command', {
        'target': 'web-01',
        'command': 'cd /opt/app && git pull && npm install && pm2 restart app',
        'timeout_seconds': 300
    })
    
    workflow.add_block('deploy-web-02', 'action.command', {
        'target': 'web-02',
        'command': 'cd /opt/app && git pull && npm install && pm2 restart app',
        'timeout_seconds': 300
    })
    
    workflow.add_block('run-migrations', 'action.command', {
        'target': 'db-01',
        'command': 'cd /opt/app && npm run migrate',
        'timeout_seconds': 600
    })
    
    # Post-deployment verification
    workflow.add_block('verify-web-01', 'action.http_request', {
        'method': 'GET',
        'url': 'http://192.168.1.10/health',
        'timeout_seconds': 30
    })
    
    workflow.add_block('verify-web-02', 'action.http_request', {
        'method': 'GET',
        'url': 'http://192.168.1.11/health',
        'timeout_seconds': 30
    })
    
    # Generate deployment report
    workflow.add_block('generate-report', 'data.transform', {
        'script': '''
// Generate deployment report
const deploymentTime = new Date().toISOString();
const servers = ['web-01', 'web-02', 'db-01'];

result = {
    deployment_id: 'deploy_' + Date.now(),
    deployed_at: deploymentTime,
    servers_deployed: servers,
    deployment_status: 'completed',
    version: 'v1.2.3',
    deployed_by: 'automated_system'
};
        '''
    })
    
    # Send deployment notification
    workflow.add_block('notify-team', 'action.notification', {
        'notification_type': 'slack',
        'recipients': ['#deployments'],
        'message': '🚀 Deployment {{data.deployment_id}} completed successfully! Version {{data.version}} deployed to {{data.servers_deployed.length}} servers.',
        'priority': 'normal'
    })
    
    workflow.add_block('end', 'flow.end', {
        'name': 'Deployment Complete',
        'save_result': True,
        'result_name': 'deployment_result'
    })
    
    # Execute workflow
    result = await workflow.execute_workflow({
        'deployment_version': 'v1.2.3',
        'triggered_by': 'demo_user'
    })
    
    print(f"\n📊 Deployment Result:")
    print(f"  Success: {result['workflow_success']}")
    print(f"  Blocks: {result['successful_blocks']}/{result['blocks_executed']}")
    
    return result


async def demo_database_backup_workflow():
    """Demo: Automated database backup workflow"""
    print("💾 Demo: Automated Database Backup Workflow")
    print("=" * 50)
    
    workflow = GenericWorkflowBuilder()
    
    # Add database server
    workflow.add_target('db-server', {
        'hostname': '192.168.1.100',
        'os_type': 'linux',
        'default_connection': 'ssh',
        'username': 'backup',
        'private_key': '/path/to/backup.key'
    })
    
    # Add backup storage server
    workflow.add_target('backup-server', {
        'hostname': '192.168.1.200',
        'os_type': 'linux',
        'default_connection': 'ssh',
        'username': 'backup',
        'private_key': '/path/to/backup.key'
    })
    
    # Build backup workflow
    workflow.add_block('start', 'flow.start', {
        'name': 'Database Backup',
        'trigger_types': ['schedule']
    })
    
    # Pre-backup checks
    workflow.add_block('check-db-status', 'action.command', {
        'target': 'db-server',
        'command': 'pg_isready -h localhost -p 5432',
        'timeout_seconds': 30
    })
    
    workflow.add_block('check-disk-space', 'action.command', {
        'target': 'db-server',
        'command': 'df -h /var/lib/postgresql',
        'timeout_seconds': 30
    })
    
    # Create backup
    workflow.add_block('create-backup', 'action.command', {
        'target': 'db-server',
        'command': 'pg_dump -h localhost -U postgres myapp > /tmp/backup_$(date +%Y%m%d_%H%M%S).sql',
        'timeout_seconds': 1800,  # 30 minutes
        'environment_variables': {
            'PGPASSWORD': '{{vault.db_password}}'
        }
    })
    
    # Compress backup
    workflow.add_block('compress-backup', 'action.command', {
        'target': 'db-server',
        'command': 'gzip /tmp/backup_*.sql',
        'timeout_seconds': 300
    })
    
    # Transfer to backup server
    workflow.add_block('transfer-backup', 'action.command', {
        'target': 'db-server',
        'command': 'scp /tmp/backup_*.sql.gz backup@192.168.1.200:/backups/database/',
        'timeout_seconds': 600
    })
    
    # Verify backup on backup server
    workflow.add_block('verify-backup', 'action.command', {
        'target': 'backup-server',
        'command': 'ls -la /backups/database/backup_*.sql.gz',
        'timeout_seconds': 30
    })
    
    # Clean up local backup
    workflow.add_block('cleanup-local', 'action.command', {
        'target': 'db-server',
        'command': 'rm -f /tmp/backup_*.sql.gz',
        'timeout_seconds': 30
    })
    
    # Generate backup report
    workflow.add_block('generate-report', 'data.transform', {
        'script': '''
// Generate backup report
const backupTime = new Date().toISOString();
const backupSize = '150MB'; // Would extract from actual command output

result = {
    backup_id: 'backup_' + Date.now(),
    backup_time: backupTime,
    backup_size: backupSize,
    backup_location: '/backups/database/',
    backup_status: 'completed',
    retention_days: 30
};
        '''
    })
    
    # Send backup notification
    workflow.add_block('notify-success', 'action.notification', {
        'notification_type': 'email',
        'recipients': ['dba@company.com', 'ops@company.com'],
        'subject': 'Database Backup Completed - {{data.backup_id}}',
        'message': 'Database backup completed successfully.\n\nBackup ID: {{data.backup_id}}\nSize: {{data.backup_size}}\nLocation: {{data.backup_location}}\nTime: {{data.backup_time}}',
        'priority': 'normal'
    })
    
    workflow.add_block('end', 'flow.end', {
        'name': 'Backup Complete',
        'save_result': True,
        'result_name': 'backup_result'
    })
    
    # Execute workflow
    result = await workflow.execute_workflow({
        'backup_type': 'scheduled',
        'retention_days': 30
    })
    
    print(f"\n📊 Backup Result:")
    print(f"  Success: {result['workflow_success']}")
    print(f"  Blocks: {result['successful_blocks']}/{result['blocks_executed']}")
    
    return result


async def demo_security_incident_response():
    """Demo: Security incident response workflow"""
    print("🔒 Demo: Security Incident Response Workflow")
    print("=" * 50)
    
    workflow = GenericWorkflowBuilder()
    
    # Add security infrastructure
    workflow.add_target('firewall', {
        'hostname': '192.168.1.1',
        'os_type': 'linux',
        'default_connection': 'ssh',
        'username': 'security',
        'private_key': '/path/to/security.key'
    })
    
    workflow.add_target('web-server', {
        'hostname': '192.168.1.10',
        'os_type': 'linux',
        'default_connection': 'ssh',
        'username': 'admin',
        'private_key': '/path/to/admin.key'
    })
    
    # Build incident response workflow
    workflow.add_block('start', 'flow.start', {
        'name': 'Security Incident Response',
        'trigger_types': ['webhook', 'manual']
    })
    
    # Analyze threat
    workflow.add_block('analyze-threat', 'data.transform', {
        'script': '''
// Analyze incoming threat data
const threatData = input.threat_data || {};
const suspiciousIP = threatData.source_ip || '192.168.1.999';
const threatLevel = threatData.severity || 'medium';

result = {
    threat_id: 'incident_' + Date.now(),
    suspicious_ip: suspiciousIP,
    threat_level: threatLevel,
    analysis_time: new Date().toISOString(),
    action_required: threatLevel === 'high' || threatLevel === 'critical'
};
        '''
    })
    
    # Check if immediate action is required
    workflow.add_block('check-severity', 'logic.if', {
        'condition': '{{data.action_required}} === true'
    })
    
    # Block suspicious IP at firewall
    workflow.add_block('block-ip', 'action.command', {
        'target': 'firewall',
        'command': 'iptables -A INPUT -s {{data.suspicious_ip}} -j DROP',
        'timeout_seconds': 30
    })
    
    # Check web server logs
    workflow.add_block('check-logs', 'action.command', {
        'target': 'web-server',
        'command': 'grep "{{data.suspicious_ip}}" /var/log/nginx/access.log | tail -20',
        'timeout_seconds': 60
    })
    
    # Generate incident report
    workflow.add_block('generate-incident-report', 'data.transform', {
        'script': '''
// Generate comprehensive incident report
const incidentData = input;
const logData = input.log_stdout || '';

result = {
    incident_report: {
        incident_id: incidentData.threat_id,
        detected_at: incidentData.analysis_time,
        threat_level: incidentData.threat_level,
        suspicious_ip: incidentData.suspicious_ip,
        actions_taken: [
            'IP blocked at firewall',
            'Logs analyzed',
            'Incident report generated'
        ],
        log_entries: logData.split('\\n').length,
        status: 'contained'
    }
};
        '''
    })
    
    # Notify security team
    workflow.add_block('notify-security-team', 'action.notification', {
        'notification_type': 'email',
        'recipients': ['security@company.com', 'soc@company.com'],
        'subject': '🚨 Security Incident {{data.incident_report.incident_id}} - {{data.incident_report.threat_level}} severity',
        'message': 'Security incident detected and contained.\n\nIncident ID: {{data.incident_report.incident_id}}\nThreat Level: {{data.incident_report.threat_level}}\nSuspicious IP: {{data.incident_report.suspicious_ip}}\nStatus: {{data.incident_report.status}}\n\nActions taken:\n{{data.incident_report.actions_taken}}',
        'priority': 'high'
    })
    
    # Log to SIEM system
    workflow.add_block('log-to-siem', 'action.http_request', {
        'method': 'POST',
        'url': 'https://siem.company.com/api/incidents',
        'headers': {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer {{vault.siem_token}}'
        },
        'json': {
            'incident_id': '{{data.incident_report.incident_id}}',
            'severity': '{{data.incident_report.threat_level}}',
            'status': '{{data.incident_report.status}}',
            'details': '{{data.incident_report}}'
        },
        'timeout_seconds': 30
    })
    
    workflow.add_block('end', 'flow.end', {
        'name': 'Incident Response Complete',
        'save_result': True,
        'result_name': 'incident_response_result'
    })
    
    # Execute workflow with simulated threat data
    result = await workflow.execute_workflow({
        'threat_data': {
            'source_ip': '192.168.1.999',
            'severity': 'high',
            'attack_type': 'brute_force',
            'detected_by': 'ids_system'
        }
    })
    
    print(f"\n📊 Incident Response Result:")
    print(f"  Success: {result['workflow_success']}")
    print(f"  Blocks: {result['successful_blocks']}/{result['blocks_executed']}")
    
    return result


async def run_all_demos():
    """Run all workflow demos"""
    print("🎯 Generic Block Workflow Demos")
    print("=" * 60)
    print("Demonstrating the power and flexibility of Generic Blocks!")
    print()
    
    demos = [
        ("Simple Server Health Check", demo_simple_server_health_check),
        ("Multi-Server Deployment", demo_multi_server_deployment),
        ("Database Backup Workflow", demo_database_backup_workflow),
        ("Security Incident Response", demo_security_incident_response)
    ]
    
    demo_results = []
    
    for demo_name, demo_func in demos:
        try:
            print(f"🎬 Running {demo_name} Demo...")
            result = await demo_func()
            demo_results.append((demo_name, result['workflow_success'], None))
            print(f"✅ {demo_name}: SUCCESS\n")
        except Exception as e:
            demo_results.append((demo_name, False, str(e)))
            print(f"❌ {demo_name}: FAILED - {str(e)}\n")
    
    # Print final summary
    print("🎯 Demo Summary")
    print("=" * 60)
    
    successful_demos = len([r for r in demo_results if r[1] is True])
    total_demos = len(demo_results)
    
    for demo_name, success, error in demo_results:
        status = "✅ SUCCESS" if success else f"❌ FAILED ({error})"
        print(f"  {demo_name}: {status}")
    
    print(f"\n📊 Overall Results: {successful_demos}/{total_demos} demos successful")
    print(f"🎉 Success Rate: {(successful_demos/total_demos*100):.1f}%")
    
    # Show execution summary
    execution_summary = complete_generic_block_executor.get_execution_summary()
    print(f"\n📈 Total Execution Statistics:")
    print(f"  Total Blocks Executed: {execution_summary['total_blocks_executed']}")
    print(f"  Successful Blocks: {execution_summary['successful_blocks']}")
    print(f"  Block Success Rate: {execution_summary['success_rate']:.1f}%")
    print(f"  Total Execution Time: {execution_summary['total_execution_time_ms']}ms")
    
    print("\n🚀 Generic Block Workflow Demos Complete!")
    print("\n💡 Key Takeaways:")
    print("  • One set of generic blocks handles infinite scenarios")
    print("  • Consistent patterns across all workflows")
    print("  • Easy to build, maintain, and extend")
    print("  • Connection-agnostic design")
    print("  • Rich error handling and reporting")
    
    return successful_demos == total_demos


if __name__ == "__main__":
    # Run all demos
    asyncio.run(run_all_demos())