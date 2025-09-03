#!/usr/bin/env python3
"""
CRUD Endpoint Analysis Script
Analyzes all microservices for CRUD operations consistency
"""

import os
import re
import json
from pathlib import Path

def extract_endpoints_from_file(file_path):
    """Extract FastAPI endpoints from a Python file"""
    endpoints = []
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Pattern to match FastAPI route decorators
        route_pattern = r'@app\.(get|post|put|delete|patch)\(["\']([^"\']+)["\'](?:.*?response_model=([^,\)]+))?.*?\)'
        
        # Find all route matches
        matches = re.finditer(route_pattern, content, re.MULTILINE | re.DOTALL)
        
        for match in matches:
            method = match.group(1).upper()
            path = match.group(2)
            response_model = match.group(3) if match.group(3) else None
            
            # Extract function name from the next line
            start_pos = match.end()
            remaining_content = content[start_pos:]
            func_match = re.search(r'async def ([^(]+)', remaining_content)
            func_name = func_match.group(1) if func_match else "unknown"
            
            endpoints.append({
                'method': method,
                'path': path,
                'function': func_name,
                'response_model': response_model
            })
    
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
    
    return endpoints

def analyze_service(service_path):
    """Analyze a single service for CRUD endpoints"""
    main_py = os.path.join(service_path, 'main.py')
    service_name = os.path.basename(service_path)
    
    if not os.path.exists(main_py):
        return {
            'service': service_name,
            'status': 'NO_MAIN_PY',
            'endpoints': []
        }
    
    endpoints = extract_endpoints_from_file(main_py)
    
    # Categorize endpoints
    crud_operations = {
        'CREATE': [],
        'READ': [],
        'UPDATE': [],
        'DELETE': [],
        'OTHER': []
    }
    
    for endpoint in endpoints:
        method = endpoint['method']
        path = endpoint['path']
        
        if method == 'POST':
            crud_operations['CREATE'].append(endpoint)
        elif method == 'GET':
            crud_operations['READ'].append(endpoint)
        elif method in ['PUT', 'PATCH']:
            crud_operations['UPDATE'].append(endpoint)
        elif method == 'DELETE':
            crud_operations['DELETE'].append(endpoint)
        else:
            crud_operations['OTHER'].append(endpoint)
    
    return {
        'service': service_name,
        'status': 'ANALYZED',
        'endpoints': endpoints,
        'crud_operations': crud_operations,
        'total_endpoints': len(endpoints)
    }

def analyze_nginx_routes():
    """Analyze nginx configuration for route mappings"""
    nginx_conf = '/home/opsconductor/microservice-system/nginx/nginx.conf'
    routes = {}
    
    try:
        with open(nginx_conf, 'r') as f:
            content = f.read()
        
        # Pattern to match location blocks
        location_pattern = r'location\s+([^\s{]+)\s*{[^}]*proxy_pass\s+http://([^;]+);'
        
        matches = re.finditer(location_pattern, content, re.MULTILINE | re.DOTALL)
        
        for match in matches:
            location = match.group(1)
            upstream = match.group(2)
            routes[location] = upstream
    
    except Exception as e:
        print(f"Error reading nginx config: {e}")
    
    return routes

def main():
    """Main analysis function"""
    microservices_path = '/home/opsconductor/microservice-system'
    
    # List of expected services
    services = [
        'auth-service',
        'user-service', 
        'credentials-service',
        'targets-service',
        'jobs-service',
        'executor-service',
        'scheduler-service',
        'notification-service',
        'discovery-service'
    ]
    
    analysis_results = []
    
    print("🔍 CRUD ENDPOINT ANALYSIS")
    print("=" * 50)
    
    # Analyze each service
    for service in services:
        service_path = os.path.join(microservices_path, service)
        if os.path.exists(service_path):
            result = analyze_service(service_path)
            analysis_results.append(result)
            print(f"✅ {service}: {result['total_endpoints']} endpoints found")
        else:
            print(f"❌ {service}: Directory not found")
    
    # Analyze nginx routes
    print("\n🌐 NGINX ROUTE ANALYSIS")
    print("=" * 30)
    nginx_routes = analyze_nginx_routes()
    for route, upstream in nginx_routes.items():
        print(f"{route} -> {upstream}")
    
    # Generate detailed report
    print("\n📊 DETAILED CRUD ANALYSIS")
    print("=" * 40)
    
    for result in analysis_results:
        if result['status'] == 'ANALYZED':
            service = result['service']
            crud = result['crud_operations']
            
            print(f"\n🔧 {service.upper()}")
            print(f"   CREATE: {len(crud['CREATE'])} endpoints")
            print(f"   READ:   {len(crud['READ'])} endpoints") 
            print(f"   UPDATE: {len(crud['UPDATE'])} endpoints")
            print(f"   DELETE: {len(crud['DELETE'])} endpoints")
            print(f"   OTHER:  {len(crud['OTHER'])} endpoints")
            
            # Show specific endpoints
            for op_type, endpoints in crud.items():
                if endpoints and op_type != 'OTHER':
                    print(f"     {op_type}:")
                    for ep in endpoints:
                        print(f"       {ep['method']} {ep['path']} -> {ep['function']}")
    
    # Save detailed JSON report
    with open('/home/opsconductor/crud_analysis_report.json', 'w') as f:
        json.dump({
            'services': analysis_results,
            'nginx_routes': nginx_routes,
            'analysis_timestamp': '2024-01-01'
        }, f, indent=2)
    
    print(f"\n💾 Detailed report saved to: /home/opsconductor/crud_analysis_report.json")

if __name__ == "__main__":
    main()