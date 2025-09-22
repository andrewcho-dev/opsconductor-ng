#!/usr/bin/env python3
"""
Complete AI Network Analysis Demonstration
Shows the full workflow of AI creating and executing a network analysis job
"""

import asyncio
import json
import time
import requests
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:3000"
AI_URL = f"{BASE_URL}/api/v1/ai"
NETWORK_URL = f"{BASE_URL}/api/v1/network"
JOBS_URL = f"{BASE_URL}/api/v1/jobs"

class NetworkAnalysisDemo:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
    
    def print_step(self, step, message):
        """Print formatted step information"""
        print(f"\n{'='*60}")
        print(f"STEP {step}: {message}")
        print(f"{'='*60}")
    
    def print_success(self, message):
        """Print success message"""
        print(f"✅ {message}")
    
    def print_info(self, message):
        """Print info message"""
        print(f"ℹ️  {message}")
    
    def print_error(self, message):
        """Print error message"""
        print(f"❌ {message}")
    
    def check_service_health(self):
        """Check if all required services are healthy"""
        self.print_step(1, "Checking Service Health")
        
        try:
            response = self.session.get(f"{BASE_URL}/health", timeout=10)
            if response.status_code == 200:
                health_data = response.json()
                print(f"Overall Status: {health_data.get('status', 'unknown')}")
                
                # Check specific services we need
                required_services = ['ai-brain', '172.18.0.1', 'automation-service']
                for check in health_data.get('checks', []):
                    service_name = check.get('name', 'unknown')
                    status = check.get('status', 'unknown')
                    response_time = check.get('response_time_ms', 'N/A')
                    
                    if any(req in service_name for req in required_services):
                        if status == 'healthy':
                            self.print_success(f"{service_name}: {status} ({response_time}ms)")
                        else:
                            self.print_error(f"{service_name}: {status}")
                
                return health_data.get('status') == 'healthy'
            else:
                self.print_error(f"Health check failed: {response.status_code}")
                return False
        except Exception as e:
            self.print_error(f"Health check error: {e}")
            return False
    
    def check_network_interfaces(self):
        """Check available network interfaces"""
        self.print_step(2, "Checking Network Interfaces")
        
        try:
            response = self.session.get(f"{NETWORK_URL}/api/v1/monitoring/status", timeout=10)
            if response.status_code == 200:
                status_data = response.json()
                interfaces = status_data.get('interfaces', [])
                self.print_success(f"Found {len(interfaces)} network interfaces:")
                
                target_interface = None
                for interface in interfaces:
                    name = interface.get('name', 'unknown')
                    ip = interface.get('ip_address', 'N/A')
                    status = interface.get('status', 'unknown')
                    rx_bytes = interface.get('rx_bytes', 0)
                    tx_bytes = interface.get('tx_bytes', 0)
                    
                    print(f"  - {name}: {ip} ({status}) - RX: {rx_bytes:,} bytes, TX: {tx_bytes:,} bytes")
                    
                    # Look for interface in 192.168.50.0 network or main interface
                    if ip and (ip.startswith('192.168.50.') or ip.startswith('192.168.10.')):
                        target_interface = name
                        self.print_info(f"Target interface found: {name} ({ip})")
                
                # If no specific target found, use the main interface (highest traffic)
                if not target_interface and interfaces:
                    main_interface = max(interfaces, key=lambda x: x.get('rx_bytes', 0) + x.get('tx_bytes', 0))
                    target_interface = main_interface.get('name')
                    self.print_info(f"Using main interface: {target_interface} ({main_interface.get('ip_address', 'N/A')})")
                
                return target_interface, interfaces
            else:
                self.print_error(f"Interface check failed: {response.status_code}")
                return None, []
        except Exception as e:
            self.print_error(f"Interface check error: {e}")
            return None, []
    
    def test_network_analyzer_direct(self, target_interface):
        """Test network analyzer service directly"""
        self.print_step(3, "Testing Network Analyzer Service")
        
        try:
            # Test starting a packet capture session
            capture_request = {
                "interface": target_interface,
                "filter": "tcp or udp",
                "duration": 30,  # 30 seconds for demo
                "max_packets": 1000
            }
            
            self.print_info(f"Starting packet capture on {target_interface}...")
            response = self.session.post(f"{NETWORK_URL}/api/v1/analysis/start-capture", 
                                       json=capture_request, timeout=10)
            
            if response.status_code == 200:
                capture_data = response.json()
                session_id = capture_data.get('session_id')
                self.print_success(f"Packet capture started! Session ID: {session_id}")
                
                # Wait a moment and check capture status
                time.sleep(5)
                status_response = self.session.get(f"{NETWORK_URL}/api/v1/analysis/capture/{session_id}", timeout=10)
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    packets_captured = status_data.get('packets_captured', 0)
                    self.print_success(f"Capture active: {packets_captured} packets captured so far")
                
                return session_id
            else:
                self.print_error(f"Packet capture failed: {response.status_code}")
                print(f"Response: {response.text}")
                return None
                
        except Exception as e:
            self.print_error(f"Network analyzer test error: {e}")
            return None
    
    def create_ai_network_analysis_request(self, target_interface):
        """Send AI request to create network analysis job"""
        self.print_step(4, "AI Network Analysis Job Creation")
        
        # Craft a natural language request for network analysis
        ai_request = {
            "message": f"""I need to perform a comprehensive network analysis of the 192.168.50.0/24 network segment. 
            Please create a network analysis job that will:
            
            1. Scan the entire 192.168.50.0/24 network to discover all active hosts
            2. Perform port scanning on discovered hosts to identify running services
            3. Analyze network traffic patterns and bandwidth usage
            4. Generate a security assessment report
            5. Use the interface {target_interface} for packet capture if available
            
            The analysis should run for at least 5 minutes to gather meaningful data. 
            Please create this as an automation job that I can monitor and get results from.""",
            "context": {
                "user_intent": "network_analysis",
                "target_network": "192.168.50.0/24",
                "interface": target_interface,
                "analysis_type": "comprehensive"
            }
        }
        
        try:
            self.print_info("Sending AI request for network analysis job creation...")
            print(f"Request: {ai_request['message'][:100]}...")
            
            response = self.session.post(f"{AI_URL}/chat", json=ai_request, timeout=30)
            
            if response.status_code == 200:
                ai_response = response.json()
                self.print_success("AI processed the request successfully!")
                
                # Print AI response
                ai_message = ai_response.get('response', 'No response')
                print(f"\nAI Response:\n{ai_message}")
                
                # Check if AI created any jobs
                actions = ai_response.get('actions', [])
                if actions:
                    self.print_success(f"AI created {len(actions)} actions:")
                    for i, action in enumerate(actions, 1):
                        print(f"  {i}. {action.get('type', 'unknown')}: {action.get('description', 'N/A')}")
                
                return ai_response
            else:
                self.print_error(f"AI request failed: {response.status_code}")
                print(f"Response: {response.text}")
                return None
                
        except Exception as e:
            self.print_error(f"AI request error: {e}")
            return None
    
    def check_created_jobs(self):
        """Check for recently created jobs"""
        self.print_step(5, "Checking Created Jobs")
        
        try:
            response = self.session.get(f"{JOBS_URL}", timeout=10)
            if response.status_code == 200:
                jobs = response.json()
                
                # Look for recent network analysis jobs
                recent_jobs = []
                current_time = time.time()
                
                for job in jobs:
                    job_name = job.get('name', '')
                    job_type = job.get('job_type', '')
                    created_at = job.get('created_at', '')
                    status = job.get('status', 'unknown')
                    
                    # Check if it's a network-related job created recently
                    if any(keyword in job_name.lower() for keyword in ['network', 'scan', 'analysis']):
                        recent_jobs.append(job)
                        self.print_success(f"Found network job: {job_name} (Status: {status})")
                        print(f"  ID: {job.get('id')}")
                        print(f"  Type: {job_type}")
                        print(f"  Created: {created_at}")
                
                return recent_jobs
            else:
                self.print_error(f"Job check failed: {response.status_code}")
                return []
        except Exception as e:
            self.print_error(f"Job check error: {e}")
            return []
    
    def monitor_job_execution(self, job_id):
        """Monitor job execution progress"""
        self.print_step(6, f"Monitoring Job Execution (ID: {job_id})")
        
        max_checks = 20  # Monitor for up to 10 minutes (30s intervals)
        check_count = 0
        
        while check_count < max_checks:
            try:
                response = self.session.get(f"{JOBS_URL}/{job_id}", timeout=10)
                if response.status_code == 200:
                    job = response.json()
                    status = job.get('status', 'unknown')
                    progress = job.get('progress', 0)
                    
                    print(f"Check {check_count + 1}: Status = {status}, Progress = {progress}%")
                    
                    if status in ['completed', 'failed', 'cancelled']:
                        if status == 'completed':
                            self.print_success(f"Job completed successfully! (Progress: {progress}%)")
                        else:
                            self.print_error(f"Job ended with status: {status}")
                        
                        # Get job results
                        return self.get_job_results(job_id)
                    
                    check_count += 1
                    if check_count < max_checks:
                        time.sleep(30)  # Wait 30 seconds between checks
                else:
                    self.print_error(f"Job status check failed: {response.status_code}")
                    break
                    
            except Exception as e:
                self.print_error(f"Job monitoring error: {e}")
                break
        
        self.print_info("Job monitoring timeout reached")
        return None
    
    def get_job_results(self, job_id):
        """Get job execution results"""
        self.print_step(7, f"Getting Job Results (ID: {job_id})")
        
        try:
            # Get job executions
            response = self.session.get(f"{JOBS_URL}/{job_id}/executions", timeout=10)
            if response.status_code == 200:
                executions = response.json()
                
                if executions:
                    latest_execution = executions[0]  # Most recent execution
                    execution_id = latest_execution.get('id')
                    
                    self.print_success(f"Found execution: {execution_id}")
                    
                    # Get execution results
                    result_response = self.session.get(f"{BASE_URL}/api/v1/executions/{execution_id}/results", timeout=10)
                    if result_response.status_code == 200:
                        results = result_response.json()
                        self.print_success("Job results retrieved!")
                        
                        # Display results summary
                        print(f"\nResults Summary:")
                        print(f"  Execution ID: {execution_id}")
                        print(f"  Status: {latest_execution.get('status', 'unknown')}")
                        print(f"  Started: {latest_execution.get('started_at', 'N/A')}")
                        print(f"  Completed: {latest_execution.get('completed_at', 'N/A')}")
                        
                        if results:
                            print(f"  Results: {json.dumps(results, indent=2)}")
                        
                        return results
                    else:
                        self.print_error(f"Results retrieval failed: {result_response.status_code}")
                else:
                    self.print_info("No executions found for this job")
            else:
                self.print_error(f"Execution check failed: {response.status_code}")
        except Exception as e:
            self.print_error(f"Results retrieval error: {e}")
        
        return None
    
    def demonstrate_network_analysis_creation(self):
        """Run the complete network analysis demonstration"""
        print(f"\n🚀 STARTING AI NETWORK ANALYSIS DEMONSTRATION")
        print(f"Target Network: 192.168.50.0/24")
        print(f"Timestamp: {datetime.now().isoformat()}")
        
        # Step 1: Check service health
        if not self.check_service_health():
            self.print_error("Services are not healthy. Cannot proceed.")
            return False
        
        # Step 2: Check network interfaces
        target_interface, interfaces = self.check_network_interfaces()
        if not interfaces:
            self.print_error("No network interfaces found. Cannot proceed.")
            return False
        
        # Step 3: Test network analyzer service directly
        session_id = self.test_network_analyzer_direct(target_interface)
        if session_id:
            self.print_success("Network analyzer service is working correctly!")
        else:
            self.print_error("Network analyzer service test failed. Continuing with AI demo...")
        
        # Step 4: Create AI network analysis request
        ai_response = self.create_ai_network_analysis_request(target_interface)
        if not ai_response:
            self.print_error("AI request failed. Cannot proceed.")
            return False
        
        # Step 5: Check for created jobs
        jobs = self.check_created_jobs()
        if not jobs:
            self.print_info("No network analysis jobs found. AI may have provided instructions instead.")
            return True
        
        # Step 6: Monitor the most recent job
        latest_job = jobs[0]
        job_id = latest_job.get('id')
        
        if job_id:
            results = self.monitor_job_execution(job_id)
            if results:
                self.print_success("🎉 DEMONSTRATION COMPLETED SUCCESSFULLY!")
                return True
        
        self.print_info("Demonstration completed with partial success")
        return True

def main():
    """Main demonstration function"""
    demo = NetworkAnalysisDemo()
    success = demo.demonstrate_network_analysis_creation()
    
    if success:
        print(f"\n{'='*60}")
        print("✅ AI NETWORK ANALYSIS DEMONSTRATION COMPLETED")
        print(f"{'='*60}")
    else:
        print(f"\n{'='*60}")
        print("❌ DEMONSTRATION FAILED")
        print(f"{'='*60}")

if __name__ == "__main__":
    main()