#!/usr/bin/env python3
"""
Endpoint Analysis Script - Analyzes all microservice endpoints for CRUD consistency
"""

import requests
import json
import time
from typing import Dict, List, Any
import sys

# Base configuration
BASE_URL = "http://localhost"
ADMIN_CREDENTIALS = {
    "username": "admin",
    "password": "admin123"
}

class EndpointAnalyzer:
    def __init__(self):
        self.token = None
        self.results = []
        
    def authenticate(self):
        """Authenticate and get JWT token"""
        try:
            response = requests.post(f"{BASE_URL}/api/v1/auth/login", json=ADMIN_CREDENTIALS)
            if response.status_code == 200:
                self.token = response.json()["access_token"]
                print("✅ Authentication successful")
                return True
            else:
                print(f"❌ Authentication failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return False
    
    def get_headers(self):
        """Get headers with authentication"""
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def test_endpoint(self, method: str, url: str, expected_status: int = 200) -> Dict:
        """Test a single endpoint"""
        try:
            headers = self.get_headers()
            
            if method == "GET":
                response = requests.get(url, headers=headers, timeout=10)
            elif method == "POST":
                # Use minimal test data
                test_data = {"test": "data"}
                response = requests.post(url, headers=headers, json=test_data, timeout=10)
            elif method == "PUT":
                test_data = {"test": "update"}
                response = requests.put(url, headers=headers, json=test_data, timeout=10)
            elif method == "DELETE":
                response = requests.delete(url, headers=headers, timeout=10)
            else:
                return {"status": "UNSUPPORTED_METHOD", "error": f"Method {method} not supported"}
            
            return {
                "status": "SUCCESS" if response.status_code in [200, 201, 204, 404] else "FAILED",
                "status_code": response.status_code,
                "response_time": response.elapsed.total_seconds(),
                "has_response": len(response.text) > 0,
                "error": response.text[:100] if response.status_code >= 400 else None
            }
            
        except Exception as e:
            return {"status": "ERROR", "error": str(e)[:100]}
    
    def analyze_service_endpoints(self, service_name: str, endpoints: List[Dict]):
        """Analyze endpoints for a specific service"""
        print(f"\n🔍 Analyzing {service_name.upper()} Service")
        
        for endpoint in endpoints:
            result = self.test_endpoint(endpoint["method"], endpoint["url"], endpoint.get("expected_status", 200))
            
            self.results.append({
                "service": service_name,
                "operation": endpoint["operation"],
                "method": endpoint["method"],
                "path": endpoint["path"],
                "full_url": endpoint["url"],
                "nginx_exposed": True,  # All are exposed through nginx
                "status": result["status"],
                "status_code": result.get("status_code", 0),
                "response_time": result.get("response_time", 0),
                "has_response": result.get("has_response", False),
                "error": result.get("error")
            })
    
    def run_analysis(self):
        """Run comprehensive endpoint analysis"""
        print("🚀 Starting Comprehensive Endpoint Analysis")
        print("=" * 60)
        
        if not self.authenticate():
            return
        
        # Define all endpoints to test
        services_endpoints = {
            "users": [
                {"operation": "CREATE", "method": "POST", "path": "/api/v1/users", "url": f"{BASE_URL}/api/v1/users"},
                {"operation": "READ_LIST", "method": "GET", "path": "/api/v1/users", "url": f"{BASE_URL}/api/v1/users"},
                {"operation": "READ_SINGLE", "method": "GET", "path": "/api/v1/users/{{id}}", "url": f"{BASE_URL}/api/v1/users/1"},
                {"operation": "UPDATE", "method": "PUT", "path": "/api/v1/users/{{id}}", "url": f"{BASE_URL}/api/v1/users/1"},
                {"operation": "DELETE", "method": "DELETE", "path": "/api/v1/users/{{id}}", "url": f"{BASE_URL}/api/v1/users/999", "expected_status": 404}
            ],
            "credentials": [
                {"operation": "CREATE", "method": "POST", "path": "/api/v1/credentials", "url": f"{BASE_URL}/api/v1/credentials"},
                {"operation": "READ_LIST", "method": "GET", "path": "/api/v1/credentials", "url": f"{BASE_URL}/api/v1/credentials"},
                {"operation": "READ_SINGLE", "method": "GET", "path": "/api/v1/credentials/{{id}}", "url": f"{BASE_URL}/api/v1/credentials/1"},
                {"operation": "UPDATE", "method": "PUT", "path": "/api/v1/credentials/{{id}}", "url": f"{BASE_URL}/api/v1/credentials/1"},
                {"operation": "DELETE", "method": "DELETE", "path": "/api/v1/credentials/{{id}}", "url": f"{BASE_URL}/api/v1/credentials/999", "expected_status": 404}
            ],
            "targets": [
                {"operation": "CREATE", "method": "POST", "path": "/api/v1/targets", "url": f"{BASE_URL}/api/v1/targets"},
                {"operation": "READ_LIST", "method": "GET", "path": "/api/v1/targets", "url": f"{BASE_URL}/api/v1/targets"},
                {"operation": "READ_SINGLE", "method": "GET", "path": "/api/v1/targets/{{id}}", "url": f"{BASE_URL}/api/v1/targets/1"},
                {"operation": "UPDATE", "method": "PUT", "path": "/api/v1/targets/{{id}}", "url": f"{BASE_URL}/api/v1/targets/1"},
                {"operation": "DELETE", "method": "DELETE", "path": "/api/v1/targets/{{id}}", "url": f"{BASE_URL}/api/v1/targets/999", "expected_status": 404}
            ],
            "jobs": [
                {"operation": "CREATE", "method": "POST", "path": "/api/v1/jobs", "url": f"{BASE_URL}/api/v1/jobs"},
                {"operation": "READ_LIST", "method": "GET", "path": "/api/v1/jobs", "url": f"{BASE_URL}/api/v1/jobs"},
                {"operation": "READ_SINGLE", "method": "GET", "path": "/api/v1/jobs/{{id}}", "url": f"{BASE_URL}/api/v1/jobs/1"},
                {"operation": "UPDATE", "method": "PUT", "path": "/api/v1/jobs/{{id}}", "url": f"{BASE_URL}/api/v1/jobs/1"},
                {"operation": "DELETE", "method": "DELETE", "path": "/api/v1/jobs/{{id}}", "url": f"{BASE_URL}/api/v1/jobs/999", "expected_status": 404}
            ],
            "scheduler": [
                {"operation": "CREATE", "method": "POST", "path": "/api/v1/schedules", "url": f"{BASE_URL}/api/v1/schedules"},
                {"operation": "READ_LIST", "method": "GET", "path": "/api/v1/schedules", "url": f"{BASE_URL}/api/v1/schedules"},
                {"operation": "READ_SINGLE", "method": "GET", "path": "/api/v1/schedules/{{id}}", "url": f"{BASE_URL}/api/v1/schedules/1"},
                {"operation": "UPDATE", "method": "PUT", "path": "/api/v1/schedules/{{id}}", "url": f"{BASE_URL}/api/v1/schedules/1"},
                {"operation": "DELETE", "method": "DELETE", "path": "/api/v1/schedules/{{id}}", "url": f"{BASE_URL}/api/v1/schedules/999", "expected_status": 404}
            ],
            "discovery": [
                {"operation": "READ_JOBS_LIST", "method": "GET", "path": "/api/v1/discovery/discovery-jobs", "url": f"{BASE_URL}/api/v1/discovery/discovery-jobs"},
                {"operation": "READ_JOB_SINGLE", "method": "GET", "path": "/api/v1/discovery/discovery-jobs/{{id}}", "url": f"{BASE_URL}/api/v1/discovery/discovery-jobs/1"},
                {"operation": "READ_TARGETS_LIST", "method": "GET", "path": "/api/v1/discovery/targets", "url": f"{BASE_URL}/api/v1/discovery/targets"},
                {"operation": "READ_TARGET_SINGLE", "method": "GET", "path": "/api/v1/discovery/targets/{{id}}", "url": f"{BASE_URL}/api/v1/discovery/targets/1"},
                {"operation": "UPDATE_TARGET", "method": "PUT", "path": "/api/v1/discovery/targets/{{id}}", "url": f"{BASE_URL}/api/v1/discovery/targets/1"},
                {"operation": "DELETE_TARGET", "method": "DELETE", "path": "/api/v1/discovery/targets/{{id}}", "url": f"{BASE_URL}/api/v1/discovery/targets/999", "expected_status": 404}
            ],
            "notification": [
                {"operation": "CREATE_NOTIFICATION", "method": "POST", "path": "/api/v1/notification/notifications/enhanced", "url": f"{BASE_URL}/api/v1/notification/notifications/enhanced"},
                {"operation": "READ_PREFERENCES", "method": "GET", "path": "/api/v1/notification/preferences/{{user_id}}", "url": f"{BASE_URL}/api/v1/notification/preferences/1"},
                {"operation": "UPDATE_PREFERENCES", "method": "PUT", "path": "/api/v1/notification/preferences/{{user_id}}", "url": f"{BASE_URL}/api/v1/notification/preferences/1"},
                {"operation": "READ_SMTP", "method": "GET", "path": "/api/v1/notification/smtp/settings", "url": f"{BASE_URL}/api/v1/notification/smtp/settings"}
            ],
            "executor": [
                {"operation": "EXECUTE_JOB", "method": "POST", "path": "/api/v1/executor/execute", "url": f"{BASE_URL}/api/v1/executor/execute"},
                {"operation": "READ_EXECUTION", "method": "GET", "path": "/api/v1/executor/executions/{{id}}", "url": f"{BASE_URL}/api/v1/executor/executions/1"},
                {"operation": "READ_EXECUTIONS_LIST", "method": "GET", "path": "/api/v1/executor/executions", "url": f"{BASE_URL}/api/v1/executor/executions"}
            ]
        }
        
        # Test each service
        for service_name, endpoints in services_endpoints.items():
            self.analyze_service_endpoints(service_name, endpoints)
        
        # Generate report
        self.generate_report()
    
    def generate_report(self):
        """Generate comprehensive analysis report"""
        print("\n" + "=" * 100)
        print("📊 COMPREHENSIVE ENDPOINT ANALYSIS REPORT")
        print("=" * 100)
        
        # Summary statistics
        total_endpoints = len(self.results)
        successful_endpoints = len([r for r in self.results if r["status"] in ["SUCCESS"]])
        failed_endpoints = total_endpoints - successful_endpoints
        
        print(f"\n📈 SUMMARY STATISTICS")
        print(f"Total Endpoints Tested: {total_endpoints}")
        print(f"Accessible: {successful_endpoints} ({successful_endpoints/total_endpoints*100:.1f}%)")
        print(f"Failed/Inaccessible: {failed_endpoints} ({failed_endpoints/total_endpoints*100:.1f}%)")
        
        # Detailed table
        print(f"\n📋 DETAILED ENDPOINT TABLE")
        print("-" * 140)
        print(f"{'SERVICE':<12} {'OPERATION':<18} {'METHOD':<6} {'PATH':<40} {'STATUS':<8} {'CODE':<5} {'TIME(s)':<8}")
        print("-" * 140)
        
        for result in self.results:
            status_icon = "✅" if result["status"] == "SUCCESS" else "❌"
            print(f"{result['service']:<12} {result['operation']:<18} {result['method']:<6} "
                  f"{result['path']:<40} {status_icon:<8} {result['status_code']:<5} {result['response_time']:<8.3f}")
        
        # Service-by-service breakdown
        print(f"\n🔧 SERVICE BREAKDOWN")
        print("-" * 80)
        
        services = {}
        for result in self.results:
            service = result['service']
            if service not in services:
                services[service] = {'total': 0, 'success': 0, 'operations': []}
            
            services[service]['total'] += 1
            services[service]['operations'].append(result['operation'])
            if result['status'] == 'SUCCESS':
                services[service]['success'] += 1
        
        for service, stats in services.items():
            success_rate = (stats['success'] / stats['total']) * 100
            operations = ', '.join(sorted(set(stats['operations'])))
            print(f"{service.upper():<15} {stats['success']}/{stats['total']} ({success_rate:.1f}%) - {operations}")
        
        # CRUD completeness analysis
        print(f"\n🎯 CRUD COMPLETENESS ANALYSIS")
        print("-" * 80)
        
        crud_patterns = {
            'CREATE': ['CREATE', 'CREATE_'],
            'READ_LIST': ['READ_LIST', 'READ_', '_LIST'],
            'READ_SINGLE': ['READ_SINGLE', 'READ_', '_SINGLE'],
            'UPDATE': ['UPDATE', 'UPDATE_'],
            'DELETE': ['DELETE', 'DELETE_']
        }
        
        for service in services.keys():
            service_ops = [r['operation'] for r in self.results if r['service'] == service]
            crud_coverage = []
            
            for crud_op, patterns in crud_patterns.items():
                has_operation = any(
                    any(pattern in op for pattern in patterns)
                    for op in service_ops
                )
                crud_coverage.append("✅" if has_operation else "❌")
            
            coverage_str = " ".join(crud_coverage)
            print(f"{service.upper():<15} C R R U D -> {coverage_str}")
        
        print(f"\nLegend: C=Create, R=Read(List), R=Read(Single), U=Update, D=Delete")
        
        # Nginx routing analysis
        print(f"\n🌐 NGINX ROUTING ANALYSIS")
        print("-" * 80)
        
        # Group by service and show routing patterns
        for service in services.keys():
            service_results = [r for r in self.results if r['service'] == service]
            print(f"\n{service.upper()} Service:")
            for result in service_results:
                status = "✅" if result['status'] == 'SUCCESS' else "❌"
                print(f"  {status} {result['method']:<6} {result['path']}")
        
        # Save JSON report
        report_data = {
            "summary": {
                "total_endpoints": total_endpoints,
                "successful_endpoints": successful_endpoints,
                "failed_endpoints": failed_endpoints,
                "success_rate": successful_endpoints/total_endpoints*100
            },
            "endpoints": self.results,
            "services": {k: {**v, 'operations': list(set(v['operations']))} for k, v in services.items()}
        }
        
        with open('/home/opsconductor/endpoint_analysis_report.json', 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print(f"\n💾 Detailed JSON report saved to: /home/opsconductor/endpoint_analysis_report.json")

def main():
    analyzer = EndpointAnalyzer()
    analyzer.run_analysis()

if __name__ == "__main__":
    main()