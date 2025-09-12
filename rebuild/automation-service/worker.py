#!/usr/bin/env python3
"""
Celery Worker for Automation Service
Handles background job execution
"""

import os
from celery import Celery

# Create Celery app
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/3")
app = Celery('automation-worker', broker=redis_url, backend=redis_url)

# Configure Celery
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

@app.task(bind=True)
def execute_job(self, job_id, workflow_definition, input_data=None):
    """Execute a job workflow"""
    try:
        # Update task state
        self.update_state(state='PROGRESS', meta={'current': 0, 'total': 100})
        
        # Simulate job execution
        import time
        import json
        
        steps = workflow_definition.get('steps', [])
        total_steps = len(steps)
        
        results = []
        for i, step in enumerate(steps):
            # Simulate step execution
            time.sleep(1)  # Simulate work
            
            step_result = {
                'step_id': step.get('id', f'step_{i}'),
                'step_name': step.get('name', f'Step {i+1}'),
                'status': 'completed',
                'output': f'Step {i+1} completed successfully'
            }
            results.append(step_result)
            
            # Update progress
            progress = int((i + 1) / total_steps * 100)
            self.update_state(state='PROGRESS', meta={'current': progress, 'total': 100})
        
        return {
            'status': 'completed',
            'results': results,
            'message': f'Job {job_id} completed successfully'
        }
        
    except Exception as exc:
        self.update_state(
            state='FAILURE',
            meta={'error': str(exc), 'job_id': job_id}
        )
        raise

@app.task(bind=True)
def execute_discovery_job(self, discovery_job_id, target_range, scan_type, configuration):
    """Execute a discovery job with progress tracking"""
    import asyncio
    import asyncpg
    import json
    import subprocess
    import ipaddress
    import socket
    from datetime import datetime
    
    try:
        # Update task state to running
        self.update_state(state='PROGRESS', meta={
            'current': 0, 
            'total': 100, 
            'status': 'Starting discovery scan...',
            'phase': 'initialization'
        })
        
        # Parse target range to get list of IPs
        target_ips = []
        try:
            if '/' in target_range:  # CIDR notation
                network = ipaddress.ip_network(target_range, strict=False)
                target_ips = [str(ip) for ip in network.hosts()]
            elif '-' in target_range:  # Range notation
                start_ip, end_ip = target_range.split('-')
                start = ipaddress.ip_address(start_ip.strip())
                end = ipaddress.ip_address(end_ip.strip())
                current = start
                while current <= end:
                    target_ips.append(str(current))
                    current += 1
            else:  # Single IP or comma-separated IPs
                target_ips = [ip.strip() for ip in target_range.split(',')]
        except Exception as e:
            raise Exception(f"Invalid target range format: {str(e)}")
        
        total_ips = len(target_ips)
        if total_ips == 0:
            raise Exception("No valid IP addresses found in target range")
        
        # Update progress
        self.update_state(state='PROGRESS', meta={
            'current': 10, 
            'total': 100, 
            'status': f'Scanning {total_ips} IP addresses...',
            'phase': 'scanning',
            'targets_found': 0,
            'targets_scanned': 0,
            'total_targets': total_ips
        })
        
        # Get enabled services from configuration
        enabled_services = []
        if configuration and 'services' in configuration:
            enabled_services = [s for s in configuration['services'] if s.get('enabled', False)]
        
        discovered_targets = []
        
        # Scan each IP
        for i, ip in enumerate(target_ips):
            try:
                # Update progress
                progress = 10 + int((i / total_ips) * 80)  # 10-90% for scanning
                self.update_state(state='PROGRESS', meta={
                    'current': progress, 
                    'total': 100, 
                    'status': f'Scanning {ip}... ({i+1}/{total_ips})',
                    'phase': 'scanning',
                    'targets_found': len(discovered_targets),
                    'targets_scanned': i + 1,
                    'total_targets': total_ips,
                    'current_target': ip
                })
                
                # Ping test first
                ping_result = subprocess.run(['ping', '-c', '1', '-W', '1', ip], 
                                           capture_output=True, text=True, timeout=2)
                
                if ping_result.returncode == 0:
                    # Host is alive, scan services
                    target_info = {
                        'ip_address': ip,
                        'hostname': None,
                        'os_type': None,
                        'services': [],
                        'system_info': {}
                    }
                    
                    # Try to get hostname
                    try:
                        hostname = socket.gethostbyaddr(ip)[0]
                        target_info['hostname'] = hostname
                    except:
                        pass
                    
                    # Scan enabled services
                    for service in enabled_services:
                        try:
                            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                            sock.settimeout(1)
                            result = sock.connect_ex((ip, service['port']))
                            sock.close()
                            
                            if result == 0:
                                target_info['services'].append({
                                    'protocol': service.get('protocol', 'tcp'),
                                    'port': service['port'],
                                    'service_name': service['name'],
                                    'is_secure': service.get('name', '').lower().endswith('s')
                                })
                        except:
                            pass
                    
                    # Only add targets that have at least one open service or if no services configured
                    if target_info['services'] or not enabled_services:
                        discovered_targets.append(target_info)
                
            except Exception as e:
                # Continue with next IP on error
                continue
        
        # Update progress to saving results
        self.update_state(state='PROGRESS', meta={
            'current': 95, 
            'total': 100, 
            'status': 'Saving results...',
            'phase': 'saving',
            'targets_found': len(discovered_targets),
            'targets_scanned': total_ips,
            'total_targets': total_ips
        })
        
        # Save results to database
        async def save_results():
            conn = await asyncpg.connect(
                host=os.getenv('DB_HOST', 'localhost'),
                port=os.getenv('DB_PORT', 5432),
                user=os.getenv('DB_USER', 'postgres'),
                password=os.getenv('DB_PASSWORD', 'postgres'),
                database=os.getenv('DB_NAME', 'opsconductor')
            )
            
            try:
                # Update discovery job status and results
                results_summary = {
                    'total_hosts': len(discovered_targets),
                    'windows_hosts': len([t for t in discovered_targets if t.get('os_type') == 'Windows']),
                    'linux_hosts': len([t for t in discovered_targets if t.get('os_type') == 'Linux']),
                    'services_detected': sum(len(t['services']) for t in discovered_targets),
                    'scan_completed_at': datetime.utcnow().isoformat()
                }
                
                await conn.execute("""
                    UPDATE assets.discovery_scans 
                    SET status = 'completed', 
                        results = $1, 
                        completed_at = NOW()
                    WHERE id = $2
                """, json.dumps(results_summary), discovery_job_id)
                
                # Save discovered targets
                for target in discovered_targets:
                    await conn.execute("""
                        INSERT INTO assets.discovered_targets 
                        (discovery_job_id, hostname, ip_address, os_type, services, system_info, 
                         duplicate_status, import_status, discovered_at)
                        VALUES ($1, $2, $3, $4, $5, $6, 'unique', 'pending', NOW())
                    """, discovery_job_id, target.get('hostname'), target['ip_address'], 
                         target.get('os_type'), json.dumps(target['services']), 
                         json.dumps(target['system_info']))
                
            finally:
                await conn.close()
        
        # Run the async save function
        asyncio.run(save_results())
        
        # Final success state
        return {
            'status': 'completed',
            'targets_found': len(discovered_targets),
            'targets_scanned': total_ips,
            'message': f'Discovery scan completed. Found {len(discovered_targets)} targets.'
        }
        
    except Exception as exc:
        # Update discovery job status to failed
        async def mark_failed():
            conn = await asyncpg.connect(
                host=os.getenv('DB_HOST', 'localhost'),
                port=os.getenv('DB_PORT', 5432),
                user=os.getenv('DB_USER', 'postgres'),
                password=os.getenv('DB_PASSWORD', 'postgres'),
                database=os.getenv('DB_NAME', 'opsconductor')
            )
            try:
                await conn.execute("""
                    UPDATE assets.discovery_scans 
                    SET status = 'failed', 
                        results = $1, 
                        completed_at = NOW()
                    WHERE id = $2
                """, json.dumps({'error': str(exc)}), discovery_job_id)
            finally:
                await conn.close()
        
        asyncio.run(mark_failed())
        
        self.update_state(
            state='FAILURE',
            meta={'error': str(exc), 'discovery_job_id': discovery_job_id}
        )
        raise

@app.task
def test_task():
    """Simple test task"""
    return "Hello from Celery worker!"

if __name__ == '__main__':
    app.start()