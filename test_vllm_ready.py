#!/usr/bin/env python3
"""
Simple test to check if vLLM is ready
"""

import requests
import time
import sys

def test_vllm_connection():
    """Test if vLLM is accessible"""
    try:
        response = requests.get("http://localhost:8007/health", timeout=5)
        if response.status_code == 200:
            print("✅ vLLM is ready!")
            return True
        else:
            print(f"❌ vLLM health check failed: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("⏳ vLLM not yet ready (connection refused)")
        return False
    except requests.exceptions.Timeout:
        print("⏳ vLLM not yet ready (timeout)")
        return False
    except Exception as e:
        print(f"❌ Error connecting to vLLM: {e}")
        return False

def wait_for_vllm(max_wait=300):
    """Wait for vLLM to be ready"""
    print("🚀 Waiting for vLLM to be ready...")
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        if test_vllm_connection():
            return True
        time.sleep(10)
    
    print(f"❌ vLLM not ready after {max_wait} seconds")
    return False

if __name__ == "__main__":
    if test_vllm_connection():
        sys.exit(0)
    else:
        print("Waiting for vLLM...")
        if wait_for_vllm():
            sys.exit(0)
        else:
            sys.exit(1)