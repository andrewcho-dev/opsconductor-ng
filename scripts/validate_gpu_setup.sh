#!/bin/bash

# GPU Validation Script for OpsConductor AI Services
# Validates GPU setup before starting Docker services

set -e

echo "🔍 OpsConductor GPU Validation Script"
echo "======================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Check if running as root or with docker permissions
check_docker_permissions() {
    print_status $BLUE "📋 Checking Docker permissions..."
    
    if ! docker ps >/dev/null 2>&1; then
        print_status $RED "❌ Cannot access Docker. Please ensure:"
        echo "   • Docker is running"
        echo "   • User is in docker group: sudo usermod -aG docker \$USER"
        echo "   • You've logged out and back in after adding to docker group"
        exit 1
    fi
    
    print_status $GREEN "✅ Docker access confirmed"
}

# Check for NVIDIA Docker runtime
check_nvidia_docker() {
    print_status $BLUE "🚀 Checking NVIDIA Docker runtime..."
    
    if ! docker info | grep -q "nvidia"; then
        print_status $YELLOW "⚠️  NVIDIA Docker runtime not detected in Docker info"
        print_status $YELLOW "   This might be normal if using Docker Compose deploy syntax"
    else
        print_status $GREEN "✅ NVIDIA Docker runtime detected"
    fi
}

# Check for GPU availability on host
check_host_gpu() {
    print_status $BLUE "💾 Checking host GPU availability..."
    
    if command -v nvidia-smi >/dev/null 2>&1; then
        print_status $GREEN "✅ nvidia-smi found"
        
        # Get GPU info
        gpu_count=$(nvidia-smi --list-gpus | wc -l)
        print_status $GREEN "🚀 Found $gpu_count GPU(s):"
        nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader,nounits | while read line; do
            echo "   • $line"
        done
        
        # Check CUDA version
        if command -v nvcc >/dev/null 2>&1; then
            cuda_version=$(nvcc --version | grep "release" | awk '{print $6}' | cut -c2-)
            print_status $GREEN "✅ CUDA version: $cuda_version"
        else
            print_status $YELLOW "⚠️  nvcc not found (CUDA toolkit not installed on host)"
            print_status $YELLOW "   This is OK if using containerized CUDA"
        fi
        
    else
        print_status $RED "❌ nvidia-smi not found. GPU support not available."
        print_status $RED "   Please install NVIDIA drivers and nvidia-docker2"
        exit 1
    fi
}

# Test GPU access in container
test_container_gpu() {
    print_status $BLUE "🧪 Testing GPU access in container..."
    
    # Test with a simple CUDA container
    if docker run --rm --gpus all nvidia/cuda:12.1.1-base-ubuntu22.04 nvidia-smi >/dev/null 2>&1; then
        print_status $GREEN "✅ GPU access confirmed in container"
    else
        print_status $RED "❌ Cannot access GPU in container"
        print_status $RED "   Please check:"
        echo "   • NVIDIA Container Toolkit is installed"
        echo "   • Docker daemon has been restarted after nvidia-docker2 installation"
        echo "   • GPU is not being used by other processes"
        exit 1
    fi
}

# Check Docker Compose version
check_docker_compose() {
    print_status $BLUE "📦 Checking Docker Compose version..."
    
    if command -v docker-compose >/dev/null 2>&1; then
        compose_version=$(docker-compose --version | awk '{print $3}' | cut -d',' -f1)
        print_status $GREEN "✅ Docker Compose version: $compose_version"
        
        # Check if version supports GPU
        major_version=$(echo $compose_version | cut -d'.' -f1)
        minor_version=$(echo $compose_version | cut -d'.' -f2)
        
        if [ "$major_version" -gt 1 ] || ([ "$major_version" -eq 1 ] && [ "$minor_version" -ge 28 ]); then
            print_status $GREEN "✅ Docker Compose version supports GPU"
        else
            print_status $YELLOW "⚠️  Docker Compose version may not support GPU syntax"
            print_status $YELLOW "   Consider upgrading to version 1.28+ or use Docker Compose V2"
        fi
    elif command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
        compose_version=$(docker compose version --short)
        print_status $GREEN "✅ Docker Compose V2 version: $compose_version"
    else
        print_status $RED "❌ Docker Compose not found"
        exit 1
    fi
}

# Validate AI service requirements
check_ai_requirements() {
    print_status $BLUE "🤖 Checking AI service requirements..."
    
    # Check if required directories exist
    local required_dirs=("ai-command" "vector-service" "llm-service")
    
    for dir in "${required_dirs[@]}"; do
        if [ -d "$dir" ]; then
            print_status $GREEN "✅ $dir directory found"
            
            # Check if Dockerfile uses CUDA base image
            if [ -f "$dir/Dockerfile" ]; then
                if grep -q "nvidia/cuda" "$dir/Dockerfile"; then
                    print_status $GREEN "   🚀 Uses CUDA base image"
                else
                    print_status $YELLOW "   ⚠️  Does not use CUDA base image"
                fi
                
                # Check requirements.txt for GPU packages
                if [ -f "$dir/requirements.txt" ]; then
                    if grep -q -E "(torch|tensorflow|cupy)" "$dir/requirements.txt"; then
                        print_status $GREEN "   🧠 GPU-accelerated ML packages found"
                    else
                        print_status $YELLOW "   ⚠️  No obvious GPU ML packages in requirements"
                    fi
                fi
            fi
        else
            print_status $RED "❌ $dir directory not found"
            exit 1
        fi
    done
}

# Main validation function
main() {
    echo
    print_status $BLUE "Starting GPU validation for OpsConductor AI services..."
    echo
    
    check_docker_permissions
    echo
    
    check_host_gpu
    echo
    
    check_nvidia_docker
    echo
    
    test_container_gpu
    echo
    
    check_docker_compose
    echo
    
    check_ai_requirements
    echo
    
    print_status $GREEN "🎉 All GPU validation checks passed!"
    print_status $GREEN "✅ System is ready for GPU-accelerated AI services"
    echo
    
    print_status $BLUE "💡 To start services with GPU support:"
    echo "   docker-compose -f docker-compose.yml -f docker-compose.gpu.yml up -d"
    echo
    
    print_status $BLUE "💡 To check GPU status after startup:"
    echo "   python3 scripts/check_gpu_status.py"
    echo
}

# Run main function
main "$@"