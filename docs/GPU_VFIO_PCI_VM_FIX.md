# GPU Support for OpsConductor in Virtualized Environments (vfio-pci)

## Problem Description
When running OpsConductor in a virtualized environment (VM) with GPU passthrough via vfio-pci, standard Docker GPU configurations fail to detect the GPU. This occurs because:

1. **Virtualization Layer**: The GPU is passed through to the VM via vfio-pci, not native hardware access
2. **Driver Isolation**: Additional isolation layers between the container and hardware
3. **Standard Configurations**: Default Docker GPU configurations don't account for virtualized environments
4. **CUDA Initialization**: CUDA library initialization fails without proper device mappings and permissions

### Symptoms
- `torch.cuda.is_available()` returns `False` despite GPU being present
- `nvidia-smi` works on host but containers cannot access GPU
- Error messages about missing CUDA devices or libraries
- GPU visible via `/proc/driver/nvidia` but not accessible to PyTorch/TensorFlow

## Solution Overview
The solution involves configuring Docker containers with:
1. Privileged mode for vfio-pci access
2. Explicit device mappings for all NVIDIA devices
3. Direct library volume mounts
4. Proper environment variables
5. Full driver capabilities

## Detailed Fix Implementation

### 1. System Requirements Verification
First, ensure your system has proper GPU passthrough:

```bash
# Check GPU presence in VM
lspci | grep -i nvidia
# Should show: 01:00.0 VGA compatible controller: NVIDIA Corporation GA106 [GeForce RTX 3060]

# Check NVIDIA driver
nvidia-smi
# Should display GPU information

# Check Docker nvidia runtime
docker info | grep nvidia
# Should show nvidia runtime available
```

### 2. Create CDI Configuration (Optional but Recommended)
Container Device Interface (CDI) improves GPU detection in VMs:

```bash
sudo mkdir -p /etc/cdi
sudo nvidia-ctk cdi generate --output=/etc/cdi/nvidia.yaml
```

### 3. Docker Compose GPU Configuration
Create or update `docker-compose.gpu.yml`:

```yaml
# Docker Compose GPU Override for VMs with vfio-pci passthrough
# Usage: docker-compose -f docker-compose.yml -f docker-compose.gpu.yml up

services:
  # Example for any AI service that needs GPU
  ai-service:
    runtime: nvidia
    privileged: true  # CRITICAL: Required for vfio-pci GPU passthrough in VMs
    environment:
      - CUDA_VISIBLE_DEVICES=0
      - NVIDIA_VISIBLE_DEVICES=0
      - NVIDIA_DRIVER_CAPABILITIES=all  # Use 'all' for VM compatibility
      - NVIDIA_DISABLE_REQUIRE=1  # Disable some checks that fail in VMs
      - LD_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu:/usr/local/cuda/lib64
    devices:
      # Map all NVIDIA devices explicitly
      - /dev/nvidia0:/dev/nvidia0
      - /dev/nvidiactl:/dev/nvidiactl
      - /dev/nvidia-uvm:/dev/nvidia-uvm
      - /dev/nvidia-modeset:/dev/nvidia-modeset
      - /dev/nvidia-caps:/dev/nvidia-caps
    volumes:
      # Direct library mounts for driver version 580.82.09 (adjust version as needed)
      - /usr/lib/x86_64-linux-gnu/libnvidia-ml.so.580.82.09:/usr/lib/x86_64-linux-gnu/libnvidia-ml.so.1:ro
      - /usr/lib/x86_64-linux-gnu/libcuda.so.580.82.09:/usr/lib/x86_64-linux-gnu/libcuda.so.1:ro
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

### 4. Key Configuration Elements Explained

#### Privileged Mode
```yaml
privileged: true
```
- **Required** for vfio-pci GPU passthrough in VMs
- Allows container to access hardware devices passed through to the VM
- Without this, containers cannot access virtualized GPU resources

#### Device Mappings
```yaml
devices:
  - /dev/nvidia0:/dev/nvidia0        # Primary GPU device
  - /dev/nvidiactl:/dev/nvidiactl    # NVIDIA control device
  - /dev/nvidia-uvm:/dev/nvidia-uvm  # Unified Memory device
  - /dev/nvidia-modeset:/dev/nvidia-modeset  # Mode setting device
  - /dev/nvidia-caps:/dev/nvidia-caps  # Capabilities device
```
- Explicit device mapping ensures all NVIDIA devices are accessible
- Critical for CUDA initialization in virtualized environments

#### Environment Variables
```yaml
environment:
  - CUDA_VISIBLE_DEVICES=0            # Specify GPU index
  - NVIDIA_VISIBLE_DEVICES=0          # NVIDIA runtime GPU selection
  - NVIDIA_DRIVER_CAPABILITIES=all    # Enable all driver capabilities
  - NVIDIA_DISABLE_REQUIRE=1          # Disable strict requirement checks
  - LD_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu:/usr/local/cuda/lib64
```

#### Library Volume Mounts
```yaml
volumes:
  - /usr/lib/x86_64-linux-gnu/libnvidia-ml.so.580.82.09:/usr/lib/x86_64-linux-gnu/libnvidia-ml.so.1:ro
  - /usr/lib/x86_64-linux-gnu/libcuda.so.580.82.09:/usr/lib/x86_64-linux-gnu/libcuda.so.1:ro
```
- Direct mounting of NVIDIA libraries
- Adjust version numbers (580.82.09) to match your driver version
- Find your version: `ls /usr/lib/x86_64-linux-gnu/libnvidia-ml.so.*`

### 5. Complete Configuration for OpsConductor AI Services

The complete `docker-compose.gpu.yml` includes configurations for all AI services:
- ai-brain
- ollama

Each service follows the same pattern with the configuration elements above.

### 6. Deployment Steps

```bash
# 1. Stop all services
docker compose -f docker-compose.yml -f docker-compose.gpu.yml down --remove-orphans

# 2. Clean Docker system (optional but recommended)
docker system prune -af --volumes

# 3. Rebuild services with GPU support
docker compose -f docker-compose.yml -f docker-compose.gpu.yml build

# 4. Start services
docker compose -f docker-compose.yml -f docker-compose.gpu.yml up -d

# 5. Verify GPU access
docker exec opsconductor-nlp python -c "
import torch
print(f'PyTorch version: {torch.__version__}')
print(f'CUDA available: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'GPU: {torch.cuda.get_device_name(0)}')
"
```

### 7. Testing GPU Functionality

Create a test script to verify GPU access:

```python
# test_gpu.py
import torch
import tensorflow as tf

# PyTorch test
print("=== PyTorch GPU Test ===")
print(f"PyTorch version: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"GPU count: {torch.cuda.device_count()}")
    print(f"GPU name: {torch.cuda.get_device_name(0)}")
    print(f"GPU memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
    
    # Create tensor on GPU
    tensor = torch.zeros(2, 3).cuda()
    print(f"Created tensor on: {tensor.device}")

# TensorFlow test (if installed)
try:
    print("\n=== TensorFlow GPU Test ===")
    print(f"TensorFlow version: {tf.__version__}")
    gpus = tf.config.list_physical_devices('GPU')
    print(f"GPUs available: {len(gpus)}")
    for gpu in gpus:
        print(f"  {gpu}")
except ImportError:
    print("TensorFlow not installed")
```

Run the test in any AI container:
```bash
docker exec opsconductor-ai-brain python test_gpu.py
```

### 8. Troubleshooting

#### GPU Not Detected
1. Verify privileged mode is enabled
2. Check all device mappings are present
3. Ensure library versions match your driver
4. Verify nvidia runtime is configured in Docker

#### Library Version Mismatch
Find correct library versions:
```bash
ls -la /usr/lib/x86_64-linux-gnu/libnvidia-ml.so.*
ls -la /usr/lib/x86_64-linux-gnu/libcuda.so.*
```
Update volume mounts accordingly.

#### Permission Denied Errors
Ensure:
- Container runs in privileged mode
- User has access to GPU devices
- SELinux/AppArmor not blocking access

#### CUDA Out of Memory
- Reduce batch sizes in AI models
- Implement gradient checkpointing
- Use mixed precision training
- Monitor GPU memory: `nvidia-smi -l 1`

### 9. Environment-Specific Notes

#### VM Types
- **KVM/QEMU with vfio-pci**: This configuration is designed for this setup
- **VMware with DirectPath I/O**: May require additional VMware tools
- **Hyper-V with DDA**: Might need different device paths

#### Cloud Environments
- **AWS EC2 GPU instances**: Usually work with standard configuration
- **Azure GPU VMs**: May require Azure-specific drivers
- **GCP GPU instances**: Standard configuration typically works

### 10. Performance Optimization

#### GPU Utilization
Monitor GPU usage:
```bash
# Real-time GPU monitoring
nvidia-smi -l 1

# Detailed process view
nvidia-smi pmon -i 0
```

#### Multi-GPU Setup
For multiple GPUs, adjust:
```yaml
environment:
  - CUDA_VISIBLE_DEVICES=0,1  # Use GPUs 0 and 1
devices:
  - /dev/nvidia0:/dev/nvidia0
  - /dev/nvidia1:/dev/nvidia1  # Add second GPU
```

### 11. Security Considerations

While `privileged: true` is required for vfio-pci GPU access:
1. Only use in trusted environments
2. Consider using Pod Security Policies in Kubernetes
3. Implement network isolation for GPU containers
4. Regular security updates for NVIDIA drivers
5. Monitor container activities

## Conclusion

This configuration successfully enables GPU access for OpsConductor AI services running in virtualized environments with vfio-pci GPU passthrough. The key elements are:

1. **Privileged mode** for hardware access
2. **Explicit device mappings** for all NVIDIA devices
3. **Direct library mounts** matching driver versions
4. **Proper environment variables** for CUDA configuration
5. **Full driver capabilities** for VM compatibility

This solution has been tested and verified with:
- NVIDIA GeForce RTX 3060 (11.6 GB)
- Driver version 580.82.09
- CUDA 12.1
- PyTorch 2.5.1+cu121
- Docker 28.4.0
- VM with SeaBIOS and vfio-pci passthrough

## References

- [NVIDIA Container Toolkit Documentation](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/)
- [Docker GPU Support](https://docs.docker.com/compose/gpu-support/)
- [VFIO GPU Passthrough Guide](https://wiki.archlinux.org/title/PCI_passthrough_via_OVMF)
- [PyTorch CUDA Documentation](https://pytorch.org/docs/stable/cuda.html)

---
*Document created: 2025-01-17*
*Last updated: 2025-01-17*
*Validated on: OpsConductor NG with vfio-pci GPU passthrough*