#!/usr/bin/env python3
"""
Test ping command execution to debug the automation service failure
"""

import asyncio
import subprocess
import sys
import os

async def test_ping_execution():
    """Test ping command execution locally"""
    print("🧪 Testing Ping Command Execution")
    print("=" * 50)
    
    # Test 1: Basic ping command
    print("\n📍 Test 1: Basic ping command")
    try:
        result = subprocess.run(
            ["ping", "-c", "1", "192.168.50.210"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        print(f"   Return code: {result.returncode}")
        print(f"   STDOUT: {result.stdout}")
        print(f"   STDERR: {result.stderr}")
        
        if result.returncode == 0:
            print("   ✅ Ping command executed successfully")
        else:
            print("   ❌ Ping command failed")
            
    except subprocess.TimeoutExpired:
        print("   ⏰ Ping command timed out")
    except FileNotFoundError:
        print("   ❌ Ping command not found")
    except Exception as e:
        print(f"   💥 Unexpected error: {e}")
    
    # Test 2: Test with localhost
    print("\n📍 Test 2: Ping localhost")
    try:
        result = subprocess.run(
            ["ping", "-c", "1", "127.0.0.1"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        print(f"   Return code: {result.returncode}")
        if result.returncode == 0:
            print("   ✅ Localhost ping successful")
        else:
            print("   ❌ Localhost ping failed")
            print(f"   STDERR: {result.stderr}")
            
    except Exception as e:
        print(f"   💥 Localhost ping error: {e}")
    
    # Test 3: Test with Google DNS
    print("\n📍 Test 3: Ping Google DNS (8.8.8.8)")
    try:
        result = subprocess.run(
            ["ping", "-c", "1", "8.8.8.8"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        print(f"   Return code: {result.returncode}")
        if result.returncode == 0:
            print("   ✅ Google DNS ping successful")
        else:
            print("   ❌ Google DNS ping failed")
            print(f"   STDERR: {result.stderr}")
            
    except Exception as e:
        print(f"   💥 Google DNS ping error: {e}")
    
    # Test 4: Check network interfaces
    print("\n📍 Test 4: Network interface information")
    try:
        result = subprocess.run(
            ["ip", "addr", "show"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            print("   ✅ Network interfaces:")
            for line in result.stdout.split('\n')[:10]:  # Show first 10 lines
                if line.strip():
                    print(f"      {line}")
        else:
            print("   ❌ Could not get network interfaces")
            
    except Exception as e:
        print(f"   💥 Network interface error: {e}")
    
    # Test 5: Check if we're in a container
    print("\n📍 Test 5: Container environment check")
    if os.path.exists("/.dockerenv"):
        print("   🐳 Running inside Docker container")
    else:
        print("   🖥️  Running on host system")
    
    print("\n" + "=" * 50)
    print("🏁 Ping execution test complete")

if __name__ == "__main__":
    asyncio.run(test_ping_execution())