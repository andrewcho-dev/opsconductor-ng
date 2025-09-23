#!/usr/bin/env python3
"""
Submit Windows Remote Probe Installation Job to OpsConductor Automation Service
"""

import json
import requests
import sys
from pathlib import Path

def submit_job():
    """Submit the Windows remote probe installation job"""
    
    # Load the job definition
    job_file = Path(__file__).parent / "automation-jobs" / "install-windows-remote-probe.json"
    
    if not job_file.exists():
        print(f"❌ Job file not found: {job_file}")
        return False
    
    try:
        with open(job_file, 'r') as f:
            job_data = json.load(f)
    except Exception as e:
        print(f"❌ Failed to load job file: {e}")
        return False
    
    # API endpoint
    api_url = "http://localhost/api/v1/jobs"
    
    print("🚀 Submitting Windows Remote Probe Installation Job...")
    print(f"📁 Job file: {job_file}")
    print(f"🎯 Target: 192.168.50.211")
    print(f"📡 API endpoint: {api_url}")
    
    try:
        # Submit the job
        response = requests.post(api_url, json=job_data, timeout=30)
        
        if response.status_code == 200 or response.status_code == 201:
            result = response.json()
            job_id = result.get('id', 'unknown')
            
            print(f"✅ Job submitted successfully!")
            print(f"📋 Job ID: {job_id}")
            print(f"📝 Job Name: {job_data['name']}")
            print(f"🏷️  Job Type: {job_data['job_type']}")
            print(f"🔧 Steps: {len(job_data['workflow_definition']['steps'])}")
            
            print("\n📊 Job Steps:")
            for i, step in enumerate(job_data['workflow_definition']['steps'], 1):
                print(f"  {i}. {step['name']} ({step['type']})")
            
            print(f"\n🌐 You can monitor the job execution at:")
            print(f"   http://localhost/jobs/{job_id}")
            
            return True
            
        else:
            print(f"❌ Failed to submit job: {response.status_code}")
            print(f"📄 Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed. Is OpsConductor running?")
        print("💡 Make sure the services are up: docker compose up -d")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def main():
    """Main function"""
    print("=" * 60)
    print("🔧 OpsConductor Windows Remote Probe Installation")
    print("=" * 60)
    
    # Check if job file exists
    job_file = Path(__file__).parent / "automation-jobs" / "install-windows-remote-probe.json"
    if not job_file.exists():
        print(f"❌ Job definition file not found: {job_file}")
        print("💡 Make sure you're running this from the OpsConductor root directory")
        sys.exit(1)
    
    print("\n📋 Job Overview:")
    try:
        with open(job_file, 'r') as f:
            job_data = json.load(f)
        
        print(f"   Name: {job_data['name']}")
        print(f"   Description: {job_data['description']}")
        print(f"   Type: {job_data['job_type']}")
        print(f"   Steps: {len(job_data['workflow_definition']['steps'])}")
        print(f"   Target: 192.168.50.211")
        
    except Exception as e:
        print(f"❌ Failed to read job file: {e}")
        sys.exit(1)
    
    print("\n⚠️  IMPORTANT NOTES:")
    print("   • This job requires Administrator privileges on the target Windows machine")
    print("   • WinRM must be enabled on 192.168.50.211")
    print("   • The target machine must have internet access to download Python")
    print("   • Ensure the central analyzer is running on 192.168.50.210:3006")
    
    # Ask for confirmation
    response = input("\n❓ Do you want to submit this job? (y/N): ").strip().lower()
    if response not in ['y', 'yes']:
        print("❌ Job submission cancelled")
        sys.exit(0)
    
    # Ask for credentials
    print("\n🔐 Windows Credentials for 192.168.50.211:")
    username = input("Username: ").strip()
    if not username:
        print("❌ Username is required")
        sys.exit(1)
    
    import getpass
    password = getpass.getpass("Password: ")
    if not password:
        print("❌ Password is required")
        sys.exit(1)
    
    # Update job with credentials (in a real implementation, these would be stored securely)
    print("\n⚠️  NOTE: In production, credentials should be stored securely in the credential manager")
    print("For this demo, credentials will be embedded in the job (not recommended for production)")
    
    # Replace credential placeholders in the job
    job_json = json.dumps(job_data)
    job_json = job_json.replace("{{ credentials.username }}", username)
    job_json = job_json.replace("{{ credentials.password }}", password)
    job_data = json.loads(job_json)
    
    # Submit the job
    if submit_job_with_credentials(job_data):
        print("\n🎉 Job submitted successfully!")
        print("📊 Monitor the job execution in the OpsConductor dashboard")
        print("🔍 Check logs for detailed progress information")
    else:
        print("\n❌ Job submission failed")
        sys.exit(1)

def submit_job_with_credentials(job_data):
    """Submit job with embedded credentials"""
    api_url = "http://localhost/api/v1/jobs"
    
    try:
        response = requests.post(api_url, json=job_data, timeout=30)
        
        if response.status_code == 200 or response.status_code == 201:
            result = response.json()
            job_id = result.get('id', 'unknown')
            
            print(f"✅ Job submitted successfully!")
            print(f"📋 Job ID: {job_id}")
            
            # Execute the job immediately
            execute_url = f"http://localhost/api/v1/jobs/{job_id}/execute"
            print(f"🚀 Starting job execution...")
            
            exec_response = requests.post(execute_url, json={}, timeout=30)
            if exec_response.status_code == 200:
                exec_result = exec_response.json()
                execution_id = exec_result.get('execution_id', 'unknown')
                print(f"▶️  Job execution started!")
                print(f"🆔 Execution ID: {execution_id}")
                print(f"🌐 Monitor at: http://localhost/executions/{execution_id}")
            else:
                print(f"⚠️  Job created but execution failed to start: {exec_response.status_code}")
                print(f"💡 You can manually start it from the dashboard")
            
            return True
        else:
            print(f"❌ Failed to submit job: {response.status_code}")
            print(f"📄 Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error submitting job: {e}")
        return False

if __name__ == "__main__":
    main()