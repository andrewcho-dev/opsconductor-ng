#!/usr/bin/env python3
"""
Test script to verify the communication settings implementation.
This script tests the new communication channel types and their configurations.
"""

import json
import sys
from pathlib import Path

def test_frontend_components():
    """Test that all frontend components exist and have the expected structure"""
    frontend_dir = Path("frontend/src/components")
    
    required_components = [
        "SlackSettings.tsx",
        "TeamsSettings.tsx", 
        "DiscordSettings.tsx",
        "WebhookSettings.tsx"
    ]
    
    print("🔍 Testing Frontend Components...")
    
    for component in required_components:
        component_path = frontend_dir / component
        if not component_path.exists():
            print(f"❌ Missing component: {component}")
            return False
        
        # Check if component has basic React structure
        content = component_path.read_text()
        if "import React" not in content:
            print(f"❌ Component {component} missing React import")
            return False
        
        if "export default" not in content:
            print(f"❌ Component {component} missing default export")
            return False
            
        print(f"✅ Component {component} exists and has basic structure")
    
    return True

def test_types_definitions():
    """Test that TypeScript types are properly defined"""
    types_file = Path("frontend/src/types/index.ts")
    
    if not types_file.exists():
        print("❌ Types file not found")
        return False
    
    content = types_file.read_text()
    
    required_types = [
        "SlackSettings",
        "TeamsSettings", 
        "DiscordSettings",
        "WebhookSettings",
        "CommunicationTestRequest"
    ]
    
    print("🔍 Testing TypeScript Types...")
    
    for type_name in required_types:
        if f"export interface {type_name}" not in content and f"export type {type_name}" not in content:
            print(f"❌ Missing type definition: {type_name}")
            return False
        print(f"✅ Type {type_name} is defined")
    
    return True

def test_api_service():
    """Test that API service has the required methods"""
    api_file = Path("frontend/src/services/api.ts")
    
    if not api_file.exists():
        print("❌ API service file not found")
        return False
    
    content = api_file.read_text()
    
    required_methods = [
        "getChannelByType",
        "saveChannel", 
        "testChannel"
    ]
    
    print("🔍 Testing API Service Methods...")
    
    for method in required_methods:
        if method not in content:
            print(f"❌ Missing API method: {method}")
            return False
        print(f"✅ API method {method} exists")
    
    return True

def test_backend_endpoints():
    """Test that backend has the required endpoints"""
    backend_file = Path("communication-service/main.py")
    
    if not backend_file.exists():
        print("❌ Backend service file not found")
        return False
    
    content = backend_file.read_text()
    
    required_endpoints = [
        "test_communication_channel",
        "_test_slack",
        "_test_teams",
        "_test_discord", 
        "_test_webhook"
    ]
    
    print("🔍 Testing Backend Endpoints...")
    
    for endpoint in required_endpoints:
        if endpoint not in content:
            print(f"❌ Missing backend endpoint: {endpoint}")
            return False
        print(f"✅ Backend endpoint {endpoint} exists")
    
    return True

def test_system_settings_page():
    """Test that SystemSettings page has been updated"""
    settings_file = Path("frontend/src/pages/SystemSettings.tsx")
    
    if not settings_file.exists():
        print("❌ SystemSettings page not found")
        return False
    
    content = settings_file.read_text()
    
    required_imports = [
        "SlackSettings",
        "TeamsSettings",
        "DiscordSettings", 
        "WebhookSettings"
    ]
    
    print("🔍 Testing SystemSettings Page...")
    
    for import_name in required_imports:
        if import_name not in content:
            print(f"❌ Missing import in SystemSettings: {import_name}")
            return False
        print(f"✅ SystemSettings imports {import_name}")
    
    # Check for navigation structure
    if "settings-nav" not in content:
        print("❌ Missing navigation structure in SystemSettings")
        return False
    
    print("✅ SystemSettings has navigation structure")
    return True

def test_requirements():
    """Test that required dependencies are added"""
    req_file = Path("communication-service/requirements.txt")
    
    if not req_file.exists():
        print("❌ Requirements file not found")
        return False
    
    content = req_file.read_text()
    
    print("🔍 Testing Requirements...")
    
    if "aiohttp" not in content:
        print("❌ Missing aiohttp dependency")
        return False
    
    print("✅ aiohttp dependency added")
    return True

def main():
    """Run all tests"""
    print("🚀 Testing Communication Settings Implementation")
    print("=" * 50)
    
    tests = [
        ("Frontend Components", test_frontend_components),
        ("TypeScript Types", test_types_definitions),
        ("API Service", test_api_service),
        ("Backend Endpoints", test_backend_endpoints),
        ("SystemSettings Page", test_system_settings_page),
        ("Requirements", test_requirements)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 30)
        
        try:
            if test_func():
                print(f"✅ {test_name} - PASSED")
                passed += 1
            else:
                print(f"❌ {test_name} - FAILED")
        except Exception as e:
            print(f"❌ {test_name} - ERROR: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Implementation looks good.")
        return 0
    else:
        print("⚠️  Some tests failed. Please review the implementation.")
        return 1

if __name__ == "__main__":
    sys.exit(main())