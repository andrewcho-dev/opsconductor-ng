"""
Network Tools Step Library
Provides network connectivity testing and monitoring tools
"""

import subprocess
import socket
import time
import threading
import dns.resolver
import requests
from typing import Dict, Any, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed


class NetworkToolsSteps:
    """Network Tools step implementations"""
    
    def ping_test(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Test network connectivity using ping"""
        target = params.get('target', '')
        count = params.get('count', 4)
        timeout = params.get('timeout', 5000)
        packet_size = params.get('packet_size', 32)
        
        if not target:
            return {
                'success': False,
                'error': 'Target host is required'
            }
        
        try:
            # Build ping command based on OS
            import platform
            system = platform.system().lower()
            
            if system == 'windows':
                cmd = [
                    'ping',
                    '-n', str(count),
                    '-w', str(timeout),
                    '-l', str(packet_size),
                    target
                ]
            else:  # Linux/macOS
                cmd = [
                    'ping',
                    '-c', str(count),
                    '-W', str(timeout // 1000),  # Convert to seconds
                    '-s', str(packet_size),
                    target
                ]
            
            # Execute ping command
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Parse results
            output_lines = result.stdout.split('\\n')
            success_count = 0
            failed_count = 0
            response_times = []
            
            for line in output_lines:
                if 'time=' in line.lower() or 'time<' in line.lower():
                    success_count += 1
                    # Extract response time
                    try:
                        if 'time=' in line:
                            time_part = line.split('time=')[1].split()[0]
                            response_times.append(float(time_part.replace('ms', '')))
                    except:
                        pass
                elif 'request timed out' in line.lower() or 'destination host unreachable' in line.lower():
                    failed_count += 1
            
            # Calculate statistics
            packet_loss = (failed_count / count) * 100 if count > 0 else 0
            avg_time = sum(response_times) / len(response_times) if response_times else 0
            min_time = min(response_times) if response_times else 0
            max_time = max(response_times) if response_times else 0
            
            return {
                'success': result.returncode == 0,
                'target': target,
                'packets_sent': count,
                'packets_received': success_count,
                'packet_loss_percent': packet_loss,
                'response_times': response_times,
                'avg_response_time': round(avg_time, 2),
                'min_response_time': round(min_time, 2),
                'max_response_time': round(max_time, 2),
                'output': result.stdout,
                'message': f'Ping test completed: {success_count}/{count} packets received'
            }
            
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'Ping test timed out',
                'target': target
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to ping target: {str(e)}',
                'target': target
            }
    
    def port_test(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Test if a specific port is open and accessible"""
        target = params.get('target', '')
        port = params.get('port', 80)
        timeout = params.get('timeout', 10)
        protocol = params.get('protocol', 'TCP').upper()
        
        if not target:
            return {
                'success': False,
                'error': 'Target host is required'
            }
        
        try:
            start_time = time.time()
            
            if protocol == 'TCP':
                # Test TCP connection
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(timeout)
                
                try:
                    result = sock.connect_ex((target, port))
                    connection_time = round((time.time() - start_time) * 1000, 2)
                    
                    if result == 0:
                        return {
                            'success': True,
                            'target': target,
                            'port': port,
                            'protocol': protocol,
                            'status': 'open',
                            'connection_time_ms': connection_time,
                            'message': f'Port {port} is open on {target}'
                        }
                    else:
                        return {
                            'success': False,
                            'target': target,
                            'port': port,
                            'protocol': protocol,
                            'status': 'closed',
                            'connection_time_ms': connection_time,
                            'message': f'Port {port} is closed on {target}'
                        }
                finally:
                    sock.close()
            
            elif protocol == 'UDP':
                # Test UDP connection (basic check)
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.settimeout(timeout)
                
                try:
                    # Send a test packet
                    sock.sendto(b'test', (target, port))
                    connection_time = round((time.time() - start_time) * 1000, 2)
                    
                    return {
                        'success': True,
                        'target': target,
                        'port': port,
                        'protocol': protocol,
                        'status': 'reachable',
                        'connection_time_ms': connection_time,
                        'message': f'UDP port {port} is reachable on {target}',
                        'note': 'UDP test only verifies reachability, not if service is listening'
                    }
                finally:
                    sock.close()
            
            else:
                return {
                    'success': False,
                    'error': f'Unsupported protocol: {protocol}',
                    'target': target,
                    'port': port
                }
                
        except socket.timeout:
            return {
                'success': False,
                'target': target,
                'port': port,
                'protocol': protocol,
                'status': 'timeout',
                'error': f'Connection timed out after {timeout} seconds',
                'message': f'Port {port} test timed out on {target}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to test port: {str(e)}',
                'target': target,
                'port': port,
                'protocol': protocol
            }
    
    def dns_lookup(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Perform DNS resolution and lookup operations"""
        hostname = params.get('hostname', '')
        record_type = params.get('record_type', 'A')
        dns_server = params.get('dns_server', '')
        timeout = params.get('timeout', 5)
        
        if not hostname:
            return {
                'success': False,
                'error': 'Hostname is required'
            }
        
        try:
            # Configure DNS resolver
            resolver = dns.resolver.Resolver()
            resolver.timeout = timeout
            resolver.lifetime = timeout
            
            if dns_server:
                resolver.nameservers = [dns_server]
            
            # Perform DNS query
            start_time = time.time()
            answers = resolver.resolve(hostname, record_type)
            query_time = round((time.time() - start_time) * 1000, 2)
            
            # Extract results
            records = []
            for answer in answers:
                records.append(str(answer))
            
            return {
                'success': True,
                'hostname': hostname,
                'record_type': record_type,
                'dns_server': dns_server or 'System default',
                'records': records,
                'record_count': len(records),
                'query_time_ms': query_time,
                'message': f'DNS lookup successful: found {len(records)} {record_type} records'
            }
            
        except dns.resolver.NXDOMAIN:
            return {
                'success': False,
                'error': f'Domain not found: {hostname}',
                'hostname': hostname,
                'record_type': record_type
            }
        except dns.resolver.Timeout:
            return {
                'success': False,
                'error': f'DNS query timed out after {timeout} seconds',
                'hostname': hostname,
                'record_type': record_type
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'DNS lookup failed: {str(e)}',
                'hostname': hostname,
                'record_type': record_type
            }
    
    def network_scan(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Scan for open ports on a target system"""
        target = params.get('target', '')
        port_range = params.get('port_range', '1-1000')
        timeout = params.get('timeout', 1000) / 1000  # Convert to seconds
        threads = params.get('threads', 50)
        
        if not target:
            return {
                'success': False,
                'error': 'Target host is required'
            }
        
        try:
            # Parse port range
            ports = []
            if ',' in port_range:
                # Individual ports: 80,443,22
                ports = [int(p.strip()) for p in port_range.split(',')]
            elif '-' in port_range:
                # Range: 1-1000
                start, end = map(int, port_range.split('-'))
                ports = list(range(start, end + 1))
            else:
                # Single port
                ports = [int(port_range)]
            
            # Scan ports using thread pool
            open_ports = []
            closed_ports = []
            
            def scan_port(port):
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(timeout)
                    result = sock.connect_ex((target, port))
                    sock.close()
                    
                    if result == 0:
                        return {'port': port, 'status': 'open'}
                    else:
                        return {'port': port, 'status': 'closed'}
                except:
                    return {'port': port, 'status': 'error'}
            
            start_time = time.time()
            
            with ThreadPoolExecutor(max_workers=threads) as executor:
                future_to_port = {executor.submit(scan_port, port): port for port in ports}
                
                for future in as_completed(future_to_port):
                    result = future.result()
                    if result['status'] == 'open':
                        open_ports.append(result['port'])
                    else:
                        closed_ports.append(result['port'])
            
            scan_time = round(time.time() - start_time, 2)
            
            return {
                'success': True,
                'target': target,
                'ports_scanned': len(ports),
                'open_ports': sorted(open_ports),
                'closed_ports': len(closed_ports),
                'scan_time_seconds': scan_time,
                'message': f'Port scan completed: {len(open_ports)} open ports found out of {len(ports)} scanned'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Port scan failed: {str(e)}',
                'target': target,
                'port_range': port_range
            }
    
    def traceroute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Trace the network path to a destination"""
        target = params.get('target', '')
        max_hops = params.get('max_hops', 30)
        timeout = params.get('timeout', 5)
        resolve_hostnames = params.get('resolve_hostnames', True)
        
        if not target:
            return {
                'success': False,
                'error': 'Target host is required'
            }
        
        try:
            # Build traceroute command based on OS
            import platform
            system = platform.system().lower()
            
            if system == 'windows':
                cmd = ['tracert', '-h', str(max_hops), '-w', str(timeout * 1000), target]
                if not resolve_hostnames:
                    cmd.insert(1, '-d')
            else:  # Linux/macOS
                cmd = ['traceroute', '-m', str(max_hops), '-w', str(timeout), target]
                if not resolve_hostnames:
                    cmd.insert(1, '-n')
            
            # Execute traceroute command
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=max_hops * timeout + 30
            )
            
            # Parse results
            hops = []
            lines = result.stdout.split('\\n')
            
            for line in lines:
                line = line.strip()
                if not line or 'Tracing route' in line or 'traceroute to' in line:
                    continue
                
                # Extract hop information
                if system == 'windows':
                    # Windows tracert format
                    parts = line.split()
                    if len(parts) >= 2 and parts[0].isdigit():
                        hop_num = int(parts[0])
                        times = []
                        hostname = ''
                        ip = ''
                        
                        for part in parts[1:]:
                            if 'ms' in part:
                                try:
                                    times.append(float(part.replace('ms', '')))
                                except:
                                    pass
                            elif '.' in part and not part.endswith('ms'):
                                if '[' in part and ']' in part:
                                    ip = part.strip('[]')
                                elif not hostname:
                                    hostname = part
                        
                        hops.append({
                            'hop': hop_num,
                            'hostname': hostname,
                            'ip': ip,
                            'response_times': times,
                            'avg_time': round(sum(times) / len(times), 2) if times else 0
                        })
                else:
                    # Linux/macOS traceroute format
                    if line and line[0].isdigit():
                        parts = line.split()
                        if len(parts) >= 2:
                            hop_num = int(parts[0])
                            hostname = parts[1] if len(parts) > 1 else ''
                            ip = parts[2].strip('()') if len(parts) > 2 else ''
                            
                            times = []
                            for part in parts:
                                if 'ms' in part:
                                    try:
                                        times.append(float(part.replace('ms', '')))
                                    except:
                                        pass
                            
                            hops.append({
                                'hop': hop_num,
                                'hostname': hostname,
                                'ip': ip,
                                'response_times': times,
                                'avg_time': round(sum(times) / len(times), 2) if times else 0
                            })
            
            return {
                'success': result.returncode == 0,
                'target': target,
                'max_hops': max_hops,
                'hops_traced': len(hops),
                'hops': hops,
                'output': result.stdout,
                'message': f'Traceroute completed: {len(hops)} hops traced to {target}'
            }
            
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'Traceroute timed out',
                'target': target
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Traceroute failed: {str(e)}',
                'target': target
            }


# Export step implementations
def get_step_implementations():
    """Return dictionary of step implementations"""
    steps = NetworkToolsSteps()
    return {
        'ping_test': steps.ping_test,
        'port_test': steps.port_test,
        'dns_lookup': steps.dns_lookup,
        'network_scan': steps.network_scan,
        'traceroute': steps.traceroute
    }