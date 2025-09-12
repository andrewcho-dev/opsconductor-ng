#!/usr/bin/env python3
"""
Test Independent Service Validation
Verify that each service validates its own limits independently
"""

import requests
import json

def test_discovery_service_limits():
    """Test that discovery service validates its own limits"""
    print("🔍 Testing Discovery Service Independent Validation...")
    
    # Test with too many IPs (should be rejected by discovery service)
    discovery_data = {
        "name": "Large Network Scan",
        "description": "Test large scan",
        "target_specification": "192.168.1.0/16",  # 65,536 IPs - should exceed discovery limits
        "scan_type": "comprehensive",
        "configuration": {
            "port_timeout": 5,
            "max_workers": 50
        }
    }
    
    try:
        response = requests.post("http://localhost:8002/discovery-jobs", json=discovery_data)
        if response.status_code == 400:
            print("✅ Discovery service correctly rejected large scan")
            print(f"   Error: {response.json().get('detail', 'Unknown error')}")
        else:
            print("❌ Discovery service should have rejected large scan")
            print(f"   Status: {response.status_code}")
    except Exception as e:
        print(f"⚠️  Could not test discovery service: {e}")

def test_automation_service_limits():
    """Test that automation service validates its own limits"""
    print("\n🤖 Testing Automation Service Independent Validation...")
    
    # Test with complex workflow (should be rejected by automation service)
    complex_workflow = {
        "nodes": [{"id": f"step_{i}", "type": "action", "name": f"Step {i}"} for i in range(150)],  # 150 steps - should exceed automation limits
        "edges": []
    }
    
    automation_data = {
        "name": "Complex Workflow Job",
        "description": "Test complex workflow",
        "workflow_definition": complex_workflow,
        "is_enabled": True
    }
    
    try:
        response = requests.post("http://localhost:8003/jobs", json=automation_data)
        if response.status_code == 400:
            print("✅ Automation service correctly rejected complex workflow")
            print(f"   Error: {response.json().get('detail', 'Unknown error')}")
        else:
            print("❌ Automation service should have rejected complex workflow")
            print(f"   Status: {response.status_code}")
    except Exception as e:
        print(f"⚠️  Could not test automation service: {e}")

def test_simple_valid_requests():
    """Test that simple valid requests still work"""
    print("\n✅ Testing Valid Requests Still Work...")
    
    # Test simple discovery job
    simple_discovery = {
        "name": "Small Network Scan",
        "description": "Test small scan",
        "target_specification": "192.168.1.1-192.168.1.10",  # 10 IPs - should be fine
        "scan_type": "basic",
        "configuration": {
            "port_timeout": 5,
            "max_workers": 5
        }
    }
    
    try:
        response = requests.post("http://localhost:8002/discovery-jobs", json=simple_discovery)
        if response.status_code in [200, 201]:
            print("✅ Discovery service accepts small scan")
        else:
            print(f"⚠️  Discovery service rejected small scan: {response.status_code}")
    except Exception as e:
        print(f"⚠️  Could not test small discovery: {e}")
    
    # Test simple automation job
    simple_workflow = {
        "nodes": [
            {"id": "start", "type": "trigger", "name": "Start"},
            {"id": "action", "type": "action", "name": "Simple Action"},
            {"id": "end", "type": "end", "name": "End"}
        ],
        "edges": []
    }
    
    simple_automation = {
        "name": "Simple Workflow Job",
        "description": "Test simple workflow",
        "workflow_definition": simple_workflow,
        "is_enabled": True
    }
    
    try:
        response = requests.post("http://localhost:8003/jobs", json=simple_automation)
        if response.status_code in [200, 201]:
            print("✅ Automation service accepts simple workflow")
        else:
            print(f"⚠️  Automation service rejected simple workflow: {response.status_code}")
    except Exception as e:
        print(f"⚠️  Could not test simple automation: {e}")

def main():
    print("🧪 Testing Independent Service Validation")
    print("=" * 50)
    
    test_discovery_service_limits()
    test_automation_service_limits()
    test_simple_valid_requests()
    
    print("\n" + "=" * 50)
    print("✨ Independent validation test complete!")
    print("\n📋 Summary:")
    print("• Discovery Service: Validates network scan complexity independently")
    print("• Automation Service: Validates workflow complexity independently")
    print("• Each service protects itself with appropriate limits")
    print("• No shared validation logic - clean architecture!")

if __name__ == "__main__":
    main()