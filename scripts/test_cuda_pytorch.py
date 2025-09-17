#!/usr/bin/env python3
"""
Test script to verify CUDA and PyTorch GPU functionality in containers
"""

import subprocess
import sys

def test_service_cuda(service_name, container_name):
    """Test CUDA functionality in a specific service container"""
    print(f"\n🧪 Testing CUDA in {service_name}...")
    
    # Test basic CUDA availability
    cmd = [
        "docker", "exec", container_name, "python", "-c",
        """
import torch
import os
print(f'PyTorch version: {torch.__version__}')
print(f'CUDA available: {torch.cuda.is_available()}')
print(f'CUDA devices: {torch.cuda.device_count()}')
if torch.cuda.is_available():
    print(f'Current device: {torch.cuda.current_device()}')
    print(f'Device name: {torch.cuda.get_device_name(0)}')
    print(f'Device memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB')
else:
    print('GPU not detected')

# Test environment variables
print(f'CUDA_HOME: {os.environ.get("CUDA_HOME", "Not set")}')
print(f'LD_LIBRARY_PATH: {os.environ.get("LD_LIBRARY_PATH", "Not set")}')
        """
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print(f"✅ {service_name} CUDA test results:")
            print(result.stdout)
        else:
            print(f"❌ {service_name} CUDA test failed:")
            print(result.stderr)
    except subprocess.TimeoutExpired:
        print(f"⏰ {service_name} CUDA test timed out")
    except Exception as e:
        print(f"❌ {service_name} CUDA test error: {e}")

def test_cuda_computation(service_name, container_name):
    """Test actual CUDA computation"""
    print(f"\n🔢 Testing CUDA computation in {service_name}...")
    
    cmd = [
        "docker", "exec", container_name, "python", "-c",
        """
import torch
import time

if torch.cuda.is_available():
    # Create tensors on GPU
    device = torch.device('cuda')
    a = torch.randn(1000, 1000, device=device)
    b = torch.randn(1000, 1000, device=device)
    
    # Time GPU computation
    start_time = time.time()
    c = torch.matmul(a, b)
    torch.cuda.synchronize()  # Wait for GPU computation to finish
    gpu_time = time.time() - start_time
    
    print(f'✅ GPU computation successful!')
    print(f'Matrix multiplication (1000x1000) took: {gpu_time:.4f} seconds')
    print(f'Result tensor shape: {c.shape}')
    print(f'Result tensor device: {c.device}')
else:
    print('❌ CUDA not available for computation test')
        """
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print(result.stdout)
        else:
            print(f"❌ Computation test failed:")
            print(result.stderr)
    except Exception as e:
        print(f"❌ Computation test error: {e}")

def main():
    """Main test function"""
    print("🚀 OpsConductor CUDA/PyTorch Test Suite")
    print("=" * 50)
    
    services = [
        ("NLP Service", "opsconductor-nlp"),
        ("Vector Service", "opsconductor-vector"),
        ("LLM Service", "opsconductor-llm")
    ]
    
    for service_name, container_name in services:
        test_service_cuda(service_name, container_name)
        test_cuda_computation(service_name, container_name)
    
    print("\n🎉 CUDA testing complete!")

if __name__ == "__main__":
    main()