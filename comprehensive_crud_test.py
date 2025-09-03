#!/usr/bin/env python3
"""
Comprehensive CRUD Endpoint Testing Script
Tests all endpoints across all microservices for consistency and functionality
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

class CRUDTester:
    def __init__(self):
        self.token = None
        self.test_results = {}
        self.endpoint_summary = []
        
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
    
    def test_endpoint(self, method: str, url: str, data: Dict = None, expected_status: int = 200) -> Dict:
        """Test a single endpoint"""
        try:
            headers = self.get_headers()
            
            if method == "GET":
                response = requests.get(url, headers=headers)
            elif method == "POST":
                response = requests.post(url, headers=headers, json=data)
            elif method == "PUT":
                response = requests.put(url, headers=headers, json=data)
            elif method == "DELETE":
                response = requests.delete(url, headers=headers)
            else:
                return {"status": "UNSUPPORTED_METHOD", "error": f"Method {method} not supported"}
            
            result = {
                "status": "SUCCESS" if response.status_code == expected_status else "FAILED",
                "status_code": response.status_code,
                "expected_status": expected_status,
                "response_time": response.elapsed.total_seconds(),
                "has_response_body": len(response.text) > 0
            }
            
            if response.status_code != expected_status:
                result["error"] = response.text[:200]  # First 200 chars of error
                
            return result
            
        except Exception as e:
            return {"status": "ERROR", "error": str(e)}
    
    def test_service_health(self, service_name: str) -> bool:
        """Test if service is healthy"""
        try:
            response = requests.get(f"{BASE_URL}/api/v1/{service_name}/health", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def test_user_service_crud(self):
        """Test User Service CRUD operations"""
        service = "users"
        print(f"\n🧪 Testing {service.upper()} Service CRUD")
        
        # Test data
        test_user = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpass123",
            "role": "operator"
        }
        
        # CREATE - POST /users
        create_result = self.test_endpoint("POST", f"{BASE_URL}/api/v1/users", test_user, 201)
        self.endpoint_summary.append({
            "service": service,
            "operation": "CREATE",
            "method": "POST",
            "path": "/api/v1/users",
            "nginx_exposed": True,
            "status": create_result["status"],
            "response_time": create_result.get("response_time", 0)
        })
        
        # READ - GET /users (list)
        list_result = self.test_endpoint("GET", f"{BASE_URL}/api/v1/users")
        self.endpoint_summary.append({
            "service": service,
            "operation": "READ_LIST",
            "method": "GET", 
            "path": "/api/v1/users",
            "nginx_exposed": True,
            "status": list_result["status"],
            "response_time": list_result.get("response_time", 0)
        })
        
        # READ - GET /users/{id} (single)
        read_result = self.test_endpoint("GET", f"{BASE_URL}/api/v1/users/1")
        self.endpoint_summary.append({
            "service": service,
            "operation": "READ_SINGLE",
            "method": "GET",
            "path": "/api/v1/users/{id}",
            "nginx_exposed": True,
            "status": read_result["status"],
            "response_time": read_result.get("response_time", 0)
        })
        
        # UPDATE - PUT /users/{id}
        update_data = {"email": "updated@example.com"}
        update_result = self.test_endpoint("PUT", f"{BASE_URL}/api/v1/users/1", update_data)
        self.endpoint_summary.append({
            "service": service,
            "operation": "UPDATE",
            "method": "PUT",
            "path": "/api/v1/users/{id}",
            "nginx_exposed": True,
            "status": update_result["status"],
            "response_time": update_result.get("response_time", 0)
        })
        
        # DELETE - DELETE /users/{id}
        delete_result = self.test_endpoint("DELETE", f"{BASE_URL}/api/v1/users/2", expected_status=204)
        self.endpoint_summary.append({
            "service": service,
            "operation": "DELETE",
            "method": "DELETE",
            "path": "/api/v1/users/{id}",
            "nginx_exposed": True,
            "status": delete_result["status"],
            "response_time": delete_result.get("response_time", 0)
        })
    
    def test_credentials_service_crud(self):
        """Test Credentials Service CRUD operations"""
        service = "credentials"
        print(f"\n🧪 Testing {service.upper()} Service CRUD")
        
        test_credential = {
            "name": "test-cred",
            "username": "testuser",
            "password": "testpass",
            "description": "Test credential"
        }
        
        # CREATE
        create_result = self.test_endpoint("POST", f"{BASE_URL}/api/v1/credentials", test_credential, 201)
        self.endpoint_summary.append({
            "service": service,
            "operation": "CREATE",
            "method": "POST",
            "path": "/api/v1/credentials",
            "nginx_exposed": True,
            "status": create_result["status"],
            "response_time": create_result.get("response_time", 0)
        })
        
        # READ LIST
        list_result = self.test_endpoint("GET", f"{BASE_URL}/api/v1/credentials")
        self.endpoint_summary.append({
            "service": service,
            "operation": "READ_LIST",
            "method": "GET",
            "path": "/api/v1/credentials",
            "nginx_exposed": True,
            "status": list_result["status"],
            "response_time": list_result.get("response_time", 0)
        })
        
        # READ SINGLE
        read_result = self.test_endpoint("GET", f"{BASE_URL}/api/v1/credentials/1")
        self.endpoint_summary.append({
            "service": service,
            "operation": "READ_SINGLE",
            "method": "GET",
            "path": "/api/v1/credentials/{id}",
            "nginx_exposed": True,
            "status": read_result["status"],
            "response_time": read_result.get("response_time", 0)
        })
        
        # UPDATE
        update_data = {"description": "Updated description"}
        update_result = self.test_endpoint("PUT", f"{BASE_URL}/api/v1/credentials/1", update_data)
        self.endpoint_summary.append({
            "service": service,
            "operation": "UPDATE",
            "method": "PUT",
            "path": "/api/v1/credentials/{id}",
            "nginx_exposed": True,
            "status": update_result["status"],
            "response_time": update_result.get("response_time", 0)
        })
        
        # DELETE
        delete_result = self.test_endpoint("DELETE", f"{BASE_URL}/api/v1/credentials/1", expected_status=204)
        self.endpoint_summary.append({
            "service": service,
            "operation": "DELETE",
            "method": "DELETE",
            "path": "/api/v1/credentials/{id}",
            "nginx_exposed": True,
            "status": delete_result["status"],
            "response_time": delete_result.get("response_time", 0)
        })
    
    def test_targets_service_crud(self):
        """Test Targets Service CRUD operations"""
        service = "targets"
        print(f"\n🧪 Testing {service.upper()} Service CRUD")
        
        test_target = {
            "hostname": "test-server",
            "ip_address": "192.168.1.100",
            "credential_id": 1,
            "service_definitions": ["winrm"]
        }
        
        # CREATE
        create_result = self.test_endpoint("POST", f"{BASE_URL}/api/v1/targets", test_target, 201)
        self.endpoint_summary.append({
            "service": service,
            "operation": "CREATE",
            "method": "POST",
            "path": "/api/v1/targets",
            "nginx_exposed": True,
            "status": create_result["status"],
            "response_time": create_result.get("response_time", 0)
        })
        
        # READ LIST
        list_result = self.test_endpoint("GET", f"{BASE_URL}/api/v1/targets")
        self.endpoint_summary.append({
            "service": service,
            "operation": "READ_LIST",
            "method": "GET",
            "path": "/api/v1/targets",
            "nginx_exposed": True,
            "status": list_result["status"],
            "response_time": list_result.get("response_time", 0)
        })
        
        # READ SINGLE
        read_result = self.test_endpoint("GET", f"{BASE_URL}/api/v1/targets/1")
        self.endpoint_summary.append({
            "service": service,
            "operation": "READ_SINGLE",
            "method": "GET",
            "path": "/api/v1/targets/{id}",
            "nginx_exposed": True,
            "status": read_result["status"],
            "response_time": read_result.get("response_time", 0)
        })
        
        # UPDATE
        update_data = {"hostname": "updated-server"}
        update_result = self.test_endpoint("PUT", f"{BASE_URL}/api/v1/targets/1", update_data)
        self.endpoint_summary.append({
            "service": service,
            "operation": "UPDATE",
            "method": "PUT",
            "path": "/api/v1/targets/{id}",
            "nginx_exposed": True,
            "status": update_result["status"],
            "response_time": update_result.get("response_time", 0)
        })
        
        # DELETE
        delete_result = self.test_endpoint("DELETE", f"{BASE_URL}/api/v1/targets/1", expected_status=204)
        self.endpoint_summary.append({
            "service": service,
            "operation": "DELETE",
            "method": "DELETE",
            "path": "/api/v1/targets/{id}",
            "nginx_exposed": True,
            "status": delete_result["status"],
            "response_time": delete_result.get("response_time", 0)
        })
    
    def test_jobs_service_crud(self):
        """Test Jobs Service CRUD operations"""
        service = "jobs"
        print(f"\n🧪 Testing {service.upper()} Service CRUD")
        
        test_job = {
            "name": "test-job",
            "description": "Test job",
            "target_id": 1,
            "steps": [
                {
                    "name": "test-step",
                    "command": "echo 'test'",
                    "order": 1
                }
            ]
        }
        
        # CREATE
        create_result = self.test_endpoint("POST", f"{BASE_URL}/api/v1/jobs", test_job, 201)
        self.endpoint_summary.append({
            "service": service,
            "operation": "CREATE",
            "method": "POST",
            "path": "/api/v1/jobs",
            "nginx_exposed": True,
            "status": create_result["status"],
            "response_time": create_result.get("response_time", 0)
        })
        
        # READ LIST
        list_result = self.test_endpoint("GET", f"{BASE_URL}/api/v1/jobs")
        self.endpoint_summary.append({
            "service": service,
            "operation": "READ_LIST",
            "method": "GET",
            "path": "/api/v1/jobs",
            "nginx_exposed": True,
            "status": list_result["status"],
            "response_time": list_result.get("response_time", 0)
        })
        
        # READ SINGLE
        read_result = self.test_endpoint("GET", f"{BASE_URL}/api/v1/jobs/1")
        self.endpoint_summary.append({
            "service": service,
            "operation": "READ_SINGLE",
            "method": "GET",
            "path": "/api/v1/jobs/{id}",
            "nginx_exposed": True,
            "status": read_result["status"],
            "response_time": read_result.get("response_time", 0)
        })
        
        # UPDATE
        update_data = {"description": "Updated job description"}
        update_result = self.test_endpoint("PUT", f"{BASE_URL}/api/v1/jobs/1", update_data)
        self.endpoint_summary.append({
            "service": service,
            "operation": "UPDATE",
            "method": "PUT",
            "path": "/api/v1/jobs/{id}",
            "nginx_exposed": True,
            "status": update_result["status"],
            "response_time": update_result.get("response_time", 0)
        })
        
        # DELETE
        delete_result = self.test_endpoint("DELETE", f"{BASE_URL}/api/v1/jobs/1", expected_status=204)
        self.endpoint_summary.append({
            "service": service,
            "operation": "DELETE",
            "method": "DELETE",
            "path": "/api/v1/jobs/{id}",
            "nginx_exposed": True,
            "status": delete_result["status"],
            "response_time": delete_result.get("response_time", 0)
        })
    
    def test_scheduler_service_crud(self):
        """Test Scheduler Service CRUD operations"""
        service = "scheduler"
        print(f"\n🧪 Testing {service.upper()} Service CRUD")
        
        test_schedule = {
            "name": "test-schedule",
            "job_id": 1,
            "cron_expression": "0 0 * * *",
            "enabled": True
        }
        
        # CREATE
        create_result = self.test_endpoint("POST", f"{BASE_URL}/api/v1/schedules", test_schedule, 201)
        self.endpoint_summary.append({
            "service": service,
            "operation": "CREATE",
            "method": "POST",
            "path": "/api/v1/schedules",
            "nginx_exposed": True,
            "status": create_result["status"],
            "response_time": create_result.get("response_time", 0)
        })
        
        # READ LIST
        list_result = self.test_endpoint("GET", f"{BASE_URL}/api/v1/schedules")
        self.endpoint_summary.append({
            "service": service,
            "operation": "READ_LIST",
            "method": "GET",
            "path": "/api/v1/schedules",
            "nginx_exposed": True,
            "status": list_result["status"],
            "response_time": list_result.get("response_time", 0)
        })
        
        # READ SINGLE
        read_result = self.test_endpoint("GET", f"{BASE_URL}/api/v1/schedules/1")
        self.endpoint_summary.append({
            "service": service,
            "operation": "READ_SINGLE",
            "method": "GET",
            "path": "/api/v1/schedules/{id}",
            "nginx_exposed": True,
            "status": read_result["status"],
            "response_time": read_result.get("response_time", 0)
        })
        
        # UPDATE
        update_data = {"enabled": False}
        update_result = self.test_endpoint("PUT", f"{BASE_URL}/api/v1/schedules/1", update_data)
        self.endpoint_summary.append({
            "service": service,
            "operation": "UPDATE",
            "method": "PUT",
            "path": "/api/v1/schedules/{id}",
            "nginx_exposed": True,
            "status": update_result["status"],
            "response_time": update_result.get("response_time", 0)
        })
        
        # DELETE
        delete_result = self.test_endpoint("DELETE", f"{BASE_URL}/api/v1/schedules/1", expected_status=204)
        self.endpoint_summary.append({
            "service": service,
            "operation": "DELETE",
            "method": "DELETE",
            "path": "/api/v1/schedules/{id}",
            "nginx_exposed": True,
            "status": delete_result["status"],
            "response_time": delete_result.get("response_time", 0)
        })
    
    def test_discovery_service_crud(self):
        """Test Discovery Service CRUD operations"""
        service = "discovery"
        print(f"\n🧪 Testing {service.upper()} Service CRUD")
        
        # READ LIST (discovery jobs)
        list_result = self.test_endpoint("GET", f"{BASE_URL}/api/v1/discovery/discovery-jobs")
        self.endpoint_summary.append({
            "service": service,
            "operation": "READ_LIST",
            "method": "GET",
            "path": "/api/v1/discovery/discovery-jobs",
            "nginx_exposed": True,
            "status": list_result["status"],
            "response_time": list_result.get("response_time", 0)
        })
        
        # READ SINGLE (discovery job)
        read_result = self.test_endpoint("GET", f"{BASE_URL}/api/v1/discovery/discovery-jobs/1")
        self.endpoint_summary.append({
            "service": service,
            "operation": "READ_SINGLE",
            "method": "GET",
            "path": "/api/v1/discovery/discovery-jobs/{id}",
            "nginx_exposed": True,
            "status": read_result["status"],
            "response_time": read_result.get("response_time", 0)
        })
        
        # READ SINGLE (discovered target)
        target_result = self.test_endpoint("GET", f"{BASE_URL}/api/v1/discovery/targets/1")
        self.endpoint_summary.append({
            "service": service,
            "operation": "READ_TARGET",
            "method": "GET",
            "path": "/api/v1/discovery/targets/{id}",
            "nginx_exposed": True,
            "status": target_result["status"],
            "response_time": target_result.get("response_time", 0)
        })
        
        # UPDATE (discovered target)
        update_data = {"import_status": "approved"}
        update_result = self.test_endpoint("PUT", f"{BASE_URL}/api/v1/discovery/targets/1", update_data)
        self.endpoint_summary.append({
            "service": service,
            "operation": "UPDATE_TARGET",
            "method": "PUT",
            "path": "/api/v1/discovery/targets/{id}",
            "nginx_exposed": True,
            "status": update_result["status"],
            "response_time": update_result.get("response_time", 0)
        })
        
        # DELETE (discovered target)
        delete_result = self.test_endpoint("DELETE", f"{BASE_URL}/api/v1/discovery/targets/1", expected_status=204)
        self.endpoint_summary.append({
            "service": service,
            "operation": "DELETE_TARGET",
            "method": "DELETE",
            "path": "/api/v1/discovery/targets/{id}",
            "nginx_exposed": True,
            "status": delete_result["status"],
            "response_time": delete_result.get("response_time", 0)
        })
    
    def test_notification_service_crud(self):
        """Test Notification Service CRUD operations"""
        service = "notification"
        print(f"\n🧪 Testing {service.upper()} Service CRUD")
        
        # CREATE (notification)
        test_notification = {
            "user_id": 1,
            "type": "info",
            "title": "Test Notification",
            "message": "This is a test notification"
        }
        create_result = self.test_endpoint("POST", f"{BASE_URL}/api/v1/notification/notifications/enhanced", test_notification, 201)
        self.endpoint_summary.append({
            "service": service,
            "operation": "CREATE",
            "method": "POST",
            "path": "/api/v1/notification/notifications/enhanced",
            "nginx_exposed": True,
            "status": create_result["status"],
            "response_time": create_result.get("response_time", 0)
        })
        
        # READ (user preferences)
        read_result = self.test_endpoint("GET", f"{BASE_URL}/api/v1/notification/preferences/1")
        self.endpoint_summary.append({
            "service": service,
            "operation": "READ_PREFERENCES",
            "method": "GET",
            "path": "/api/v1/notification/preferences/{user_id}",
            "nginx_exposed": True,
            "status": read_result["status"],
            "response_time": read_result.get("response_time", 0)
        })
        
        # UPDATE (user preferences)
        update_data = {"email_enabled": True, "in_app_enabled": True}
        update_result = self.test_endpoint("PUT", f"{BASE_URL}/api/v1/notification/preferences/1", update_data)
        self.endpoint_summary.append({
            "service": service,
            "operation": "UPDATE_PREFERENCES",
            "method": "PUT",
            "path": "/api/v1/notification/preferences/{user_id}",
            "nginx_exposed": True,
            "status": update_result["status"],
            "response_time": update_result.get("response_time", 0)
        })
        
        # READ (SMTP settings)
        smtp_result = self.test_endpoint("GET", f"{BASE_URL}/api/v1/notification/smtp/settings")
        self.endpoint_summary.append({
            "service": service,
            "operation": "READ_SMTP",
            "method": "GET",
            "path": "/api/v1/notification/smtp/settings",
            "nginx_exposed": True,
            "status": smtp_result["status"],
            "response_time": smtp_result.get("response_time", 0)
        })
    
    def run_all_tests(self):
        """Run all CRUD tests"""
        print("🚀 Starting Comprehensive CRUD Testing")
        print("=" * 50)
        
        # Check authentication
        if not self.authenticate():
            print("❌ Cannot proceed without authentication")
            return
        
        # Wait for services to be ready
        print("\n⏳ Waiting for services to be ready...")
        time.sleep(5)
        
        # Test each service
        try:
            self.test_user_service_crud()
            self.test_credentials_service_crud()
            self.test_targets_service_crud()
            self.test_jobs_service_crud()
            self.test_scheduler_service_crud()
            self.test_discovery_service_crud()
            self.test_notification_service_crud()
        except Exception as e:
            print(f"❌ Error during testing: {e}")
        
        # Generate summary report
        self.generate_summary_report()
    
    def generate_summary_report(self):
        """Generate comprehensive summary report"""
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE CRUD ENDPOINT ANALYSIS REPORT")
        print("=" * 80)
        
        # Summary statistics
        total_endpoints = len(self.endpoint_summary)
        successful_endpoints = len([e for e in self.endpoint_summary if e["status"] == "SUCCESS"])
        failed_endpoints = total_endpoints - successful_endpoints
        
        print(f"\n📈 SUMMARY STATISTICS")
        print(f"Total Endpoints Tested: {total_endpoints}")
        print(f"Successful: {successful_endpoints} ({successful_endpoints/total_endpoints*100:.1f}%)")
        print(f"Failed: {failed_endpoints} ({failed_endpoints/total_endpoints*100:.1f}%)")
        
        # Detailed table
        print(f"\n📋 DETAILED ENDPOINT TABLE")
        print("-" * 120)
        print(f"{'SERVICE':<12} {'OPERATION':<15} {'METHOD':<6} {'PATH':<35} {'NGINX':<6} {'STATUS':<8} {'TIME(s)':<8}")
        print("-" * 120)
        
        for endpoint in self.endpoint_summary:
            status_icon = "✅" if endpoint["status"] == "SUCCESS" else "❌"
            print(f"{endpoint['service']:<12} {endpoint['operation']:<15} {endpoint['method']:<6} "
                  f"{endpoint['path']:<35} {'YES':<6} {status_icon:<8} {endpoint['response_time']:<8.3f}")
        
        # Service-by-service breakdown
        print(f"\n🔧 SERVICE BREAKDOWN")
        print("-" * 60)
        
        services = {}
        for endpoint in self.endpoint_summary:
            service = endpoint['service']
            if service not in services:
                services[service] = {'total': 0, 'success': 0, 'operations': set()}
            
            services[service]['total'] += 1
            services[service]['operations'].add(endpoint['operation'])
            if endpoint['status'] == 'SUCCESS':
                services[service]['success'] += 1
        
        for service, stats in services.items():
            success_rate = (stats['success'] / stats['total']) * 100
            operations = ', '.join(sorted(stats['operations']))
            print(f"{service.upper():<15} {stats['success']}/{stats['total']} ({success_rate:.1f}%) - {operations}")
        
        # CRUD completeness analysis
        print(f"\n🎯 CRUD COMPLETENESS ANALYSIS")
        print("-" * 60)
        
        crud_operations = ['CREATE', 'READ_LIST', 'READ_SINGLE', 'UPDATE', 'DELETE']
        
        for service in services.keys():
            service_ops = [e['operation'] for e in self.endpoint_summary if e['service'] == service]
            crud_coverage = []
            
            for op in crud_operations:
                if any(op in service_op for service_op in service_ops):
                    crud_coverage.append("✅")
                else:
                    crud_coverage.append("❌")
            
            coverage_str = " ".join(crud_coverage)
            print(f"{service.upper():<15} C R R U D -> {coverage_str}")
        
        print(f"\nLegend: C=Create, R=Read(List), R=Read(Single), U=Update, D=Delete")
        
        # Save detailed JSON report
        report_data = {
            "summary": {
                "total_endpoints": total_endpoints,
                "successful_endpoints": successful_endpoints,
                "failed_endpoints": failed_endpoints,
                "success_rate": successful_endpoints/total_endpoints*100
            },
            "endpoints": self.endpoint_summary,
            "services": services
        }
        
        with open('/home/opsconductor/comprehensive_crud_report.json', 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print(f"\n💾 Detailed JSON report saved to: /home/opsconductor/comprehensive_crud_report.json")

def main():
    tester = CRUDTester()
    tester.run_all_tests()

if __name__ == "__main__":
    main()