#!/usr/bin/env python3
"""Simple script to check PyTorch GPU availability - run inside container"""

import sys

try:
    import torch
    print(f"✓ PyTorch version: {torch.__version__}")
    print(f"✓ CUDA available: {torch.cuda.is_available()}")
    
    if torch.cuda.is_available():
        print(f"✓ CUDA version: {torch.version.cuda}")
        print(f"✓ GPU count: {torch.cuda.device_count()}")
        print(f"✓ Current GPU: {torch.cuda.current_device()}")
        print(f"✓ GPU name: {torch.cuda.get_device_name(0)}")
        
        # Test tensor operations on GPU
        x = torch.randn(3, 3).cuda()
        y = torch.randn(3, 3).cuda()
        z = x + y
        print(f"✓ GPU tensor math test successful: {z.device}")
        print("\n🎉 SUCCESS: PyTorch can use GPU!")
    else:
        print("\n⚠️  WARNING: GPU not detected by PyTorch")
        print("\nPossible causes:")
        print("1. Container not started with GPU runtime")
        print("2. NVIDIA drivers not properly installed")
        print("3. CUDA toolkit mismatch")
        print("4. PyTorch not installed with CUDA support")
        
except ImportError:
    print("✗ PyTorch is not installed!")
    print("Install with: pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121")
    sys.exit(1)
except Exception as e:
    print(f"✗ Error: {e}")
    sys.exit(1)