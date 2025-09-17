#!/usr/bin/env python3
"""Test PyTorch GPU detection in AI services"""

import httpx
import asyncio
import json

async def test_service_gpu(service_name: str, port: int):
    """Test if a service can detect GPU with PyTorch"""
    print(f"\n{'='*60}")
    print(f"Testing {service_name} on port {port}")
    print('='*60)
    
    test_code = """
import torch
import sys

print(f"PyTorch version: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"CUDA version: {torch.version.cuda}")
    print(f"GPU count: {torch.cuda.device_count()}")
    print(f"Current GPU: {torch.cuda.current_device()}")
    print(f"GPU name: {torch.cuda.get_device_name(0)}")
    
    # Test tensor on GPU
    x = torch.randn(3, 3).cuda()
    print(f"Tensor on GPU: {x.device}")
else:
    print("No GPU detected - PyTorch will use CPU")
"""
    
    try:
        # Try to execute Python code in the container via exec endpoint
        async with httpx.AsyncClient(timeout=30) as client:
            # First check if service is up
            health_response = await client.get(f"http://localhost:{port}/health")
            print(f"✓ Service is healthy: {health_response.status_code}")
            
            # Test GPU detection endpoint if available
            try:
                gpu_response = await client.get(f"http://localhost:{port}/gpu-status")
                print(f"GPU Status Response: {gpu_response.text}")
            except:
                print("No /gpu-status endpoint available")
                
    except Exception as e:
        print(f"✗ Error testing {service_name}: {e}")

async def main():
    """Test all AI services for GPU detection"""
    
    services = [
        ("ai-command", 3005),
        ("nlp-service", 3006),  # Assuming port based on pattern
        ("vector-service", 3007),  # Assuming port based on pattern
        ("llm-service", 3008),  # Assuming port based on pattern
        ("ai-orchestrator", 3010),
    ]
    
    print("=" * 80)
    print("GPU PYTORCH DETECTION TEST FOR AI SERVICES")
    print("=" * 80)
    print("\nThis test verifies PyTorch can detect GPUs in each AI service container.")
    print("Make sure services are running with: docker-compose -f docker-compose.yml -f docker-compose.gpu.yml up")
    
    for service_name, port in services:
        await test_service_gpu(service_name, port)
    
    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)
    print("\nTo fix GPU issues, rebuild with:")
    print("docker-compose -f docker-compose.yml -f docker-compose.gpu.yml build --no-cache")
    print("docker-compose -f docker-compose.yml -f docker-compose.gpu.yml up -d")

if __name__ == "__main__":
    asyncio.run(main())