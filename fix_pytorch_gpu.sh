#!/bin/bash

echo "Fixing PyTorch GPU detection in containers..."

# Get all NVIDIA library paths
NVIDIA_LIB_PATHS=$(docker exec opsconductor-nlp find /usr/local/lib/python3.12/site-packages/nvidia -name 'lib' -type d 2>/dev/null | tr '\n' ':')

echo "Found NVIDIA library paths:"
echo "$NVIDIA_LIB_PATHS"

# Create a startup script that sets the environment
cat << 'EOF' > /tmp/fix_gpu.py
import os
import sys

# Set all NVIDIA library paths
nvidia_paths = []
import site
for site_dir in site.getsitepackages():
    nvidia_dir = os.path.join(site_dir, 'nvidia')
    if os.path.exists(nvidia_dir):
        for subdir in os.listdir(nvidia_dir):
            lib_path = os.path.join(nvidia_dir, subdir, 'lib')
            if os.path.exists(lib_path):
                nvidia_paths.append(lib_path)

if nvidia_paths:
    ld_library_path = ':'.join(nvidia_paths)
    os.environ['LD_LIBRARY_PATH'] = ld_library_path
    print(f"Set LD_LIBRARY_PATH to: {ld_library_path}")

import torch
print(f"PyTorch version: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"GPU count: {torch.cuda.device_count()}")
    print(f"GPU name: {torch.cuda.get_device_name(0)}")
    print(f"CUDA version: {torch.version.cuda}")
else:
    # Try to diagnose the issue
    print("\nDiagnosing CUDA issue...")
    import subprocess
    try:
        result = subprocess.run(['nvidia-smi', '--query-gpu=name,driver_version,compute_cap', '--format=csv,noheader'], 
                              capture_output=True, text=True)
        print(f"GPU Info: {result.stdout}")
    except:
        print("nvidia-smi not available")
    
    # Check if CUDA libs are accessible
    import ctypes
    try:
        ctypes.CDLL('libcudart.so.12')
        print("libcudart.so.12 loaded successfully")
    except Exception as e:
        print(f"Failed to load libcudart.so.12: {e}")
EOF

# Copy and run the fix script
docker cp /tmp/fix_gpu.py opsconductor-nlp:/tmp/fix_gpu.py
echo -e "\n=== Testing GPU detection with fix ==="
docker exec opsconductor-nlp python /tmp/fix_gpu.py