#!/bin/bash
# Fix PyTorch GPU detection by setting proper library paths

# Set library paths for NVIDIA libraries installed by pip
export LD_LIBRARY_PATH="/usr/local/lib/python3.12/site-packages/nvidia/cuda_runtime/lib:$LD_LIBRARY_PATH"
export LD_LIBRARY_PATH="/usr/local/lib/python3.12/site-packages/nvidia/cublas/lib:$LD_LIBRARY_PATH"
export LD_LIBRARY_PATH="/usr/local/lib/python3.12/site-packages/nvidia/cudnn/lib:$LD_LIBRARY_PATH"
export LD_LIBRARY_PATH="/usr/local/lib/python3.12/site-packages/nvidia/cufft/lib:$LD_LIBRARY_PATH"
export LD_LIBRARY_PATH="/usr/local/lib/python3.12/site-packages/nvidia/curand/lib:$LD_LIBRARY_PATH"
export LD_LIBRARY_PATH="/usr/local/lib/python3.12/site-packages/nvidia/cusolver/lib:$LD_LIBRARY_PATH"
export LD_LIBRARY_PATH="/usr/local/lib/python3.12/site-packages/nvidia/cusparse/lib:$LD_LIBRARY_PATH"
export LD_LIBRARY_PATH="/usr/local/lib/python3.12/site-packages/nvidia/nccl/lib:$LD_LIBRARY_PATH"
export LD_LIBRARY_PATH="/usr/local/lib/python3.12/site-packages/nvidia/nvtx/lib:$LD_LIBRARY_PATH"

# Run the main service
exec python main.py