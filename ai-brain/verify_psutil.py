#!/usr/bin/env python3
"""
Verification script to ensure psutil is properly installed and working.
This script tests all the psutil functionality we need for production systems.
"""

def verify_psutil_installation():
    """Verify that psutil is installed and working correctly."""
    try:
        import psutil
        print(f"✅ psutil successfully imported - version: {psutil.__version__}")
        
        # Test basic system metrics
        print(f"✅ CPU count: {psutil.cpu_count()}")
        print(f"✅ CPU percent: {psutil.cpu_percent(interval=1):.1f}%")
        
        # Test memory metrics
        memory = psutil.virtual_memory()
        print(f"✅ Memory total: {memory.total // (1024**3)} GB")
        print(f"✅ Memory available: {memory.available // (1024**3)} GB")
        print(f"✅ Memory percent: {memory.percent:.1f}%")
        
        # Test disk metrics
        disk = psutil.disk_usage('/')
        print(f"✅ Disk total: {disk.total // (1024**3)} GB")
        print(f"✅ Disk free: {disk.free // (1024**3)} GB")
        print(f"✅ Disk percent: {(disk.used / disk.total * 100):.1f}%")
        
        # Test network metrics
        network = psutil.net_io_counters()
        print(f"✅ Network bytes sent: {network.bytes_sent // (1024**2)} MB")
        print(f"✅ Network bytes received: {network.bytes_recv // (1024**2)} MB")
        
        # Test process metrics
        process = psutil.Process()
        print(f"✅ Current process PID: {process.pid}")
        print(f"✅ Current process memory: {process.memory_info().rss // (1024**2)} MB")
        
        print("\n🎉 ALL PSUTIL TESTS PASSED! psutil is properly installed and functional.")
        return True
        
    except ImportError as e:
        print(f"❌ FAILED: psutil is not installed - {e}")
        return False
    except Exception as e:
        print(f"❌ FAILED: psutil error - {e}")
        return False

if __name__ == "__main__":
    print("🔍 Verifying psutil installation...")
    success = verify_psutil_installation()
    exit(0 if success else 1)