#!/usr/bin/env python3
"""
Test script for OpsConductor Remote Network Analytics Probe
Tests basic functionality and connectivity
"""

import sys
import requests
import json
import time
from datetime import datetime

def test_central_analyzer_connectivity(analyzer_url):
    """Test connectivity to central analyzer"""
    print(f"Testing connectivity to {analyzer_url}...")
    
    try:
        response = requests.get(f"{analyzer_url}/health", timeout=10)
        if response.status_code == 200:
            print("✓ Central analyzer is reachable")
            return True
        else:
            print(f"✗ Central analyzer returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Failed to connect to central analyzer: {e}")
        return False

def test_probe_registration(analyzer_url, probe_id):
    """Test probe registration"""
    print(f"Testing probe registration for {probe_id}...")
    
    probe_info = {
        "probe_id": probe_id,
        "name": "Test Probe",
        "location": "Test Location",
        "capabilities": ["packet_capture", "interface_monitoring"],
        "interfaces": [
            {
                "name": "test-interface",
                "addresses": [{"family": "AF_INET", "address": "192.168.1.100"}],
                "status": "up"
            }
        ],
        "status": "active",
        "last_heartbeat": datetime.now().isoformat(),
        "platform": "test",
        "platform_version": "1.0"
    }
    
    try:
        response = requests.post(
            f"{analyzer_url}/api/v1/remote/register-probe",
            json=probe_info,
            timeout=10
        )
        
        if response.status_code == 200:
            print("✓ Probe registration successful")
            return True
        else:
            print(f"✗ Probe registration failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"✗ Probe registration error: {e}")
        return False

def test_heartbeat(analyzer_url, probe_id):
    """Test heartbeat functionality"""
    print(f"Testing heartbeat for {probe_id}...")
    
    heartbeat_data = {
        "probe_id": probe_id,
        "status": "active",
        "timestamp": datetime.now().isoformat(),
        "active_captures": 0,
        "interfaces": []
    }
    
    try:
        response = requests.post(
            f"{analyzer_url}/api/v1/remote/heartbeat",
            json=heartbeat_data,
            timeout=10
        )
        
        if response.status_code == 200:
            print("✓ Heartbeat successful")
            return True
        else:
            print(f"✗ Heartbeat failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"✗ Heartbeat error: {e}")
        return False

def test_probe_listing(analyzer_url):
    """Test probe listing endpoint"""
    print("Testing probe listing...")
    
    try:
        response = requests.get(f"{analyzer_url}/api/v1/remote/probes", timeout=10)
        
        if response.status_code == 200:
            probes = response.json()
            print(f"✓ Retrieved {len(probes.get('probes', []))} registered probes")
            return True
        else:
            print(f"✗ Failed to list probes: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Probe listing error: {e}")
        return False

def main():
    """Main test function"""
    if len(sys.argv) < 2:
        print("Usage: python test-probe.py <central_analyzer_url> [probe_id]")
        print("Example: python test-probe.py http://YOUR_HOST_IP:3006 test-probe-001")
        sys.exit(1)
    
    analyzer_url = sys.argv[1].rstrip('/')
    probe_id = sys.argv[2] if len(sys.argv) > 2 else "test-probe-001"
    
    print("OpsConductor Remote Probe Connectivity Test")
    print("=" * 50)
    print(f"Central Analyzer: {analyzer_url}")
    print(f"Test Probe ID: {probe_id}")
    print()
    
    tests_passed = 0
    total_tests = 4
    
    # Test 1: Central analyzer connectivity
    if test_central_analyzer_connectivity(analyzer_url):
        tests_passed += 1
    print()
    
    # Test 2: Probe registration
    if test_probe_registration(analyzer_url, probe_id):
        tests_passed += 1
    print()
    
    # Test 3: Heartbeat
    if test_heartbeat(analyzer_url, probe_id):
        tests_passed += 1
    print()
    
    # Test 4: Probe listing
    if test_probe_listing(analyzer_url):
        tests_passed += 1
    print()
    
    # Summary
    print("Test Summary")
    print("=" * 20)
    print(f"Tests passed: {tests_passed}/{total_tests}")
    
    if tests_passed == total_tests:
        print("✓ All tests passed! Remote probe connectivity is working.")
        sys.exit(0)
    else:
        print("✗ Some tests failed. Check the central analyzer configuration.")
        sys.exit(1)

if __name__ == "__main__":
    main()