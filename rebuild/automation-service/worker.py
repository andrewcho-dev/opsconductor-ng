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

# Configure Celery with resource protection
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=20 * 60,  # 20 minutes max (reduced from 30)
    task_soft_time_limit=18 * 60,  # 18 minutes soft limit
    worker_prefetch_multiplier=1,  # Process one task at a time
    worker_max_tasks_per_child=100,  # Restart worker after 100 tasks (reduced from 1000)
    worker_max_memory_per_child=512000,  # 512MB memory limit per worker
    task_acks_late=True,  # Acknowledge tasks only after completion
    worker_disable_rate_limits=False,
    task_reject_on_worker_lost=True,
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
    """Execute a discovery job with parallel scanning and progress tracking"""
    import asyncio
    import asyncpg
    import json
    import subprocess
    import ipaddress
    import socket
    import concurrent.futures
    import threading
    import time
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
        
        # Get enabled services from configuration
        enabled_services = []
        if configuration and 'services' in configuration:
            enabled_services = [s for s in configuration['services'] if s.get('enabled', False)]
        
        # Calculate timeouts based on job size
        ping_timeout = 1 if total_ips > 50 else 2
        port_timeout = 1 if total_ips > 50 else 2
        hostname_timeout = 2 if total_ips > 50 else 5
        
        # RESOURCE PROTECTION: Limit workers based on system capacity
        # Prevent memory exhaustion and system overload
        if total_ips > 500:
            raise Exception(f"Discovery job too large: {total_ips} IPs exceeds maximum of 500")
        
        total_operations = total_ips * len(enabled_services)
        if total_operations > 5000:
            raise Exception(f"Discovery job too complex: {total_operations} operations exceeds maximum of 5000")
        
        # Conservative worker limits to prevent system crashes
        if total_ips <= 25:
            max_workers = 3
        elif total_ips <= 50:
            max_workers = 5
        elif total_ips <= 100:
            max_workers = 8
        elif total_ips <= 200:
            max_workers = 10
        else:
            max_workers = 12  # Never exceed 12 workers to prevent overload
        
        # Update progress
        self.update_state(state='PROGRESS', meta={
            'current': 5, 
            'total': 100, 
            'status': f'Initializing parallel scan of {total_ips} IPs with {max_workers} workers...',
            'phase': 'initialization',
            'targets_found': 0,
            'targets_scanned': 0,
            'total_targets': total_ips,
            'max_workers': max_workers
        })
        
        # Shared state for progress tracking
        progress_lock = threading.Lock()
        progress_state = {
            'scanned': 0,
            'found': 0,
            'discovered_targets': []
        }
        
        def scan_single_ip(ip):
            """Scan a single IP address with timeouts"""
            try:
                # Ping test first with timeout
                ping_result = subprocess.run(
                    ['ping', '-c', '1', '-W', str(ping_timeout), ip], 
                    capture_output=True, text=True, timeout=ping_timeout + 1
                )
                
                if ping_result.returncode == 0:
                    # Host is alive, scan services
                    target_info = {
                        'ip_address': ip,
                        'hostname': None,
                        'os_type': None,
                        'services': [],
                        'system_info': {}
                    }
                    
                    # Try to get hostname with timeout
                    try:
                        socket.setdefaulttimeout(hostname_timeout)
                        hostname = socket.gethostbyaddr(ip)[0]
                        target_info['hostname'] = hostname
                    except:
                        pass
                    finally:
                        socket.setdefaulttimeout(None)
                    
                    # Scan enabled services with timeout
                    for service in enabled_services:
                        try:
                            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                            sock.settimeout(port_timeout)
                            result = sock.connect_ex((ip, service['port']))
                            sock.close()
                            
                            if result == 0:
                                target_info['services'].append({
                                    'service_name': service['name'],
                                    'port': service['port'],
                                    'protocol': service.get('protocol', 'tcp'),
                                    'is_secure': service['port'] in [443, 993, 995, 5986]
                                })
                        except Exception:
                            pass
                    
                    # Update shared progress state
                    with progress_lock:
                        progress_state['scanned'] += 1
                        if target_info['services'] or target_info['hostname']:
                            progress_state['found'] += 1
                            progress_state['discovered_targets'].append(target_info)
                        return target_info if (target_info['services'] or target_info['hostname']) else None
                else:
                    # Host not reachable
                    with progress_lock:
                        progress_state['scanned'] += 1
                    return None
                    
            except Exception:
                with progress_lock:
                    progress_state['scanned'] += 1
                return None
        
        def update_progress_periodically():
            """Update progress every 2 seconds"""
            while progress_state['scanned'] < total_ips:
                with progress_lock:
                    scanned = progress_state['scanned']
                    found = progress_state['found']
                
                if scanned > 0:
                    progress = 10 + int((scanned / total_ips) * 80)  # 10-90% for scanning
                    self.update_state(state='PROGRESS', meta={
                        'current': progress, 
                        'total': 100, 
                        'status': f'Scanning in progress... ({scanned}/{total_ips})',
                        'phase': 'scanning',
                        'targets_found': found,
                        'targets_scanned': scanned,
                        'total_targets': total_ips,
                        'max_workers': max_workers,
                        'scan_rate': f'{scanned/max(1, time.time() - start_time):.1f} IPs/sec'
                    })
                
                time.sleep(2)  # Update every 2 seconds
        
        # Start progress update thread
        start_time = time.time()
        progress_thread = threading.Thread(target=update_progress_periodically, daemon=True)
        progress_thread.start()
        
        # Execute parallel scanning with memory management
        self.update_state(state='PROGRESS', meta={
            'current': 10, 
            'total': 100, 
            'status': f'Starting parallel scan with {max_workers} workers...',
            'phase': 'scanning',
            'targets_found': 0,
            'targets_scanned': 0,
            'total_targets': total_ips,
            'max_workers': max_workers
        })
        
        discovered_targets = []
        
        # Process IPs in batches to prevent memory exhaustion
        batch_size = min(50, max(10, total_ips // 4))  # Adaptive batch size
        
        for i in range(0, len(target_ips), batch_size):
            batch_ips = target_ips[i:i + batch_size]
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit batch scanning tasks
                future_to_ip = {executor.submit(scan_single_ip, ip): ip for ip in batch_ips}
                
                # Collect results as they complete with proper timeout
                try:
                    for future in concurrent.futures.as_completed(future_to_ip, timeout=configuration.get('timeout', 300)):
                        try:
                            result = future.result(timeout=15)  # Individual task timeout
                            if result:
                                discovered_targets.append(result)
                        except concurrent.futures.TimeoutError:
                            # Individual IP scan timeout - continue with others
                            pass
                        except Exception as e:
                            # Log individual IP scan failure but continue
                            pass
                except concurrent.futures.TimeoutError:
                    # Batch timeout - log and continue with next batch
                    self.update_state(state='PROGRESS', meta={
                        'current': 50, 
                        'total': 100, 
                        'status': f'Batch timeout occurred, continuing with remaining IPs...',
                        'phase': 'scanning',
                        'targets_found': len(discovered_targets),
                        'targets_scanned': progress_state['scanned'],
                        'total_targets': total_ips
                    })
                    continue
        
        # Wait for progress thread to finish
        progress_thread.join(timeout=1)
        
        # Final progress update
        scan_duration = time.time() - start_time
        
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