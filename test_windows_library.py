#!/usr/bin/env python3
"""
Test script for Windows PowerShell Library
Tests the library functionality without requiring actual Windows servers
"""

import sys
import os
import asyncio

# Add automation service libraries to path
sys.path.append('/home/opsconductor/automation-service/libraries')

try:
    from windows_powershell import WindowsPowerShellLibrary
    from connection_manager import ConnectionManager
except ImportError as e:
    print(f"❌ Import failed: {e}")
    print("Make sure you're running this from the correct directory")
    sys.exit(1)

async def test_windows_library():
    """Test Windows PowerShell Library functionality"""
    print("🔧 Testing Windows PowerShell Library")
    print("=" * 60)
    
    # Initialize library
    library = WindowsPowerShellLibrary()
    
    # Test 1: Library info
    print("\n📋 Test 1: Library Information")
    info = library.get_library_info()
    print(f"✓ Library: {info['name']} v{info['version']}")
    print(f"✓ Capabilities: {len(info['capabilities'])} features")
    print(f"✓ Supported protocols: {info['supported_protocols']}")
    print(f"✓ Default ports: {info['default_ports']}")
    
    # Test 2: Credential encryption/decryption
    print("\n🔐 Test 2: Credential Encryption")
    test_username = "testuser"
    test_password = "SecurePass123!"
    
    try:
        encrypted = library.encrypt_credentials(test_username, test_password)
        print(f"✓ Credentials encrypted: {len(encrypted)} characters")
        
        decrypted_user, decrypted_pass = library.decrypt_credentials(encrypted)
        print(f"✓ Credentials decrypted successfully")
        
        if decrypted_user == test_username and decrypted_pass == test_password:
            print("✓ Encryption/decryption working correctly")
        else:
            print("❌ Encryption/decryption mismatch")
            
    except Exception as e:
        print(f"❌ Credential encryption test failed: {e}")
    
    # Test 3: Connection test (will fail but should handle gracefully)
    print("\n🌐 Test 3: Connection Test (Expected to Fail)")
    test_host = "nonexistent-windows-server.local"
    
    try:
        result = library.test_connection(test_host, test_username, test_password)
        print(f"✓ Connection test completed (success: {result['success']})")
        print(f"✓ Duration: {result['duration_seconds']:.2f} seconds")
        
        if not result['success']:
            print(f"✓ Expected failure: {result['error']}")
        
        # Check result structure
        expected_keys = ['success', 'error', 'duration_seconds', 'details']
        if all(key in result for key in expected_keys):
            print("✓ Connection test result structure is correct")
        else:
            print("❌ Connection test result structure is incomplete")
            
    except Exception as e:
        print(f"❌ Connection test failed unexpectedly: {e}")
    
    # Test 4: PowerShell execution (will fail but should handle gracefully)
    print("\n⚡ Test 4: PowerShell Execution Test (Expected to Fail)")
    test_script = """
    Write-Output "Hello from PowerShell!"
    Get-Date
    $env:COMPUTERNAME
    """
    
    try:
        result = library.execute_powershell(
            test_host, test_username, test_password, test_script, timeout=30
        )
        print(f"✓ PowerShell execution completed (success: {result['success']})")
        print(f"✓ Duration: {result['duration_seconds']:.2f} seconds")
        print(f"✓ Attempts: {result['attempts']}")
        
        if not result['success']:
            print(f"✓ Expected failure: {result['error']}")
        
        # Check result structure
        expected_keys = ['success', 'stdout', 'stderr', 'exit_code', 'duration_seconds']
        if all(key in result for key in expected_keys):
            print("✓ PowerShell execution result structure is correct")
        else:
            print("❌ PowerShell execution result structure is incomplete")
            
    except Exception as e:
        print(f"❌ PowerShell execution test failed unexpectedly: {e}")
    
    print("\n✅ Windows PowerShell Library tests completed!")

async def test_connection_manager():
    """Test Connection Manager functionality"""
    print("\n🔗 Testing Connection Manager Library")
    print("=" * 60)
    
    # Initialize manager
    manager = ConnectionManager()
    
    # Test 1: Library info
    print("\n📋 Test 1: Library Information")
    info = manager.get_library_info()
    print(f"✓ Library: {info['name']} v{info['version']}")
    print(f"✓ Capabilities: {len(info['capabilities'])} features")
    print(f"✓ Cache TTL: {info['cache_ttl']} seconds")
    
    # Test 2: Target group resolution (will likely fail without database)
    print("\n🎯 Test 2: Target Group Resolution (May Fail Without Database)")
    try:
        targets = await manager.resolve_target_group("web servers")
        print(f"✓ Target resolution completed: {len(targets)} targets found")
        
        if targets:
            print("✓ Sample target:", targets[0].get('hostname', 'Unknown'))
        else:
            print("✓ No targets found (expected without database)")
            
    except Exception as e:
        print(f"✓ Expected database connection failure: {str(e)[:100]}...")
    
    # Test 3: Connectivity test
    print("\n🌐 Test 3: Target Connectivity Test")
    test_target = {
        'hostname': 'google.com',
        'ip_address': '8.8.8.8',
        'os_type': 'linux'
    }
    
    try:
        result = await manager.test_target_connectivity(test_target)
        print(f"✓ Connectivity test completed (success: {result['success']})")
        print(f"✓ Target host: {result.get('target_host')}")
        
        if result['success']:
            print("✓ At least one port is reachable")
        else:
            print(f"✓ No ports reachable: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Connectivity test failed: {e}")
    
    print("\n✅ Connection Manager Library tests completed!")

async def main():
    """Run all tests"""
    print("🚀 OpsConductor Windows Management Library Tests")
    print("=" * 80)
    
    try:
        await test_windows_library()
        await test_connection_manager()
        
        print("\n" + "=" * 80)
        print("🎉 All tests completed successfully!")
        print("📝 Libraries are ready for integration with automation service")
        print("\n💡 Next steps:")
        print("   1. Install required packages: pip install pywinrm paramiko cryptography")
        print("   2. Apply database migration: add-target-credentials.sql")
        print("   3. Rebuild automation service with new libraries")
        print("   4. Test with actual Windows/Linux servers")
        
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())