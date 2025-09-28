#!/usr/bin/env python3
"""
GPU Status Checker for OpsConductor AI Services
Verifies that all AI services have proper GPU access and utilization
"""

import asyncio
import aiohttp
import json
import sys
from typing import Dict, List, Any
import time

# AI Services to check
import subprocess
def get_host_ip():
    try:
        result = subprocess.run(['hostname', '-I'], capture_output=True, text=True)
        return result.stdout.strip().split()[0]
    except:
        return "127.0.0.1"

HOST_IP = get_host_ip()
AI_SERVICES = {
    "ai-brain": f"http://{HOST_IP}:3000"
}

class GPUStatusChecker:
    def __init__(self):
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def check_service_health(self, service_name: str, base_url: str) -> Dict[str, Any]:
        """Check if service is healthy and responding"""
        try:
            async with self.session.get(f"{base_url}/health", timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "healthy": True,
                        "status": data.get("status", "unknown"),
                        "response_time": response.headers.get("X-Response-Time", "N/A")
                    }
                else:
                    return {
                        "healthy": False,
                        "error": f"HTTP {response.status}",
                        "response_time": "N/A"
                    }
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
                "response_time": "N/A"
            }
    
    async def check_gpu_status(self, service_name: str, base_url: str) -> Dict[str, Any]:
        """Check GPU status for a specific service"""
        try:
            async with self.session.get(f"{base_url}/gpu-status", timeout=10) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return {
                        "error": f"HTTP {response.status}",
                        "gpu_available": False
                    }
        except Exception as e:
            return {
                "error": str(e),
                "gpu_available": False
            }
    
    async def check_service_info(self, service_name: str, base_url: str) -> Dict[str, Any]:
        """Get service information including GPU status"""
        try:
            async with self.session.get(f"{base_url}/info", timeout=10) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return {
                        "error": f"HTTP {response.status}"
                    }
        except Exception as e:
            return {
                "error": str(e)
            }
    
    async def run_comprehensive_check(self) -> Dict[str, Any]:
        """Run comprehensive GPU status check across all AI services"""
        print("🔍 Starting comprehensive GPU status check for OpsConductor AI services...")
        print("=" * 80)
        
        results = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
            "services": {},
            "summary": {
                "total_services": len(AI_SERVICES),
                "healthy_services": 0,
                "gpu_enabled_services": 0,
                "gpu_available": False,
                "issues": []
            }
        }
        
        for service_name, base_url in AI_SERVICES.items():
            print(f"\n📊 Checking {service_name}...")
            
            service_result = {
                "name": service_name,
                "url": base_url,
                "health": {},
                "gpu_status": {},
                "service_info": {}
            }
            
            # Check health
            health = await self.check_service_health(service_name, base_url)
            service_result["health"] = health
            
            if health["healthy"]:
                results["summary"]["healthy_services"] += 1
                print(f"  ✅ Service is healthy")
                
                # Check GPU status
                gpu_status = await self.check_gpu_status(service_name, base_url)
                service_result["gpu_status"] = gpu_status
                
                if gpu_status.get("gpu_available", False):
                    results["summary"]["gpu_enabled_services"] += 1
                    results["summary"]["gpu_available"] = True
                    print(f"  🚀 GPU available: {gpu_status.get('device_name', 'Unknown')}")
                    print(f"     Device: {gpu_status.get('device', 'N/A')}")
                    print(f"     Memory: {gpu_status.get('memory_free_gb', 0):.2f}GB free / {gpu_status.get('memory_total_gb', 0):.2f}GB total")
                    
                    if gpu_status.get("embedding_model"):
                        print(f"     Embedding Model: {gpu_status.get('embedding_model')}")
                    if gpu_status.get("spacy_gpu_enabled"):
                        print(f"     spaCy GPU: {'Enabled' if gpu_status.get('spacy_gpu_enabled') else 'Disabled'}")
                else:
                    print(f"  ⚠️  GPU not available: {gpu_status.get('message', gpu_status.get('error', 'Unknown reason'))}")
                    results["summary"]["issues"].append(f"{service_name}: GPU not available")
                
                # Get service info
                service_info = await self.check_service_info(service_name, base_url)
                service_result["service_info"] = service_info
                
                if "capabilities" in service_info:
                    print(f"     Capabilities: {', '.join(service_info['capabilities'][:3])}...")
                
            else:
                print(f"  ❌ Service unhealthy: {health.get('error', 'Unknown error')}")
                results["summary"]["issues"].append(f"{service_name}: Service unhealthy - {health.get('error', 'Unknown')}")
            
            results["services"][service_name] = service_result
        
        return results
    
    def print_summary(self, results: Dict[str, Any]):
        """Print a comprehensive summary of the GPU status check"""
        print("\n" + "=" * 80)
        print("📋 SUMMARY REPORT")
        print("=" * 80)
        
        summary = results["summary"]
        
        print(f"🕐 Timestamp: {results['timestamp']}")
        print(f"🔧 Total AI Services: {summary['total_services']}")
        print(f"✅ Healthy Services: {summary['healthy_services']}/{summary['total_services']}")
        print(f"🚀 GPU-Enabled Services: {summary['gpu_enabled_services']}/{summary['total_services']}")
        print(f"💾 GPU Available: {'Yes' if summary['gpu_available'] else 'No'}")
        
        if summary["issues"]:
            print(f"\n⚠️  Issues Found ({len(summary['issues'])}):")
            for issue in summary["issues"]:
                print(f"   • {issue}")
        else:
            print(f"\n🎉 All services are healthy and GPU-enabled!")
        
        # Detailed service breakdown
        print(f"\n📊 DETAILED SERVICE STATUS")
        print("-" * 80)
        
        for service_name, service_data in results["services"].items():
            status_icon = "✅" if service_data["health"]["healthy"] else "❌"
            gpu_icon = "🚀" if service_data["gpu_status"].get("gpu_available", False) else "⚠️"
            
            print(f"{status_icon} {gpu_icon} {service_name.upper()}")
            print(f"     URL: {service_data['url']}")
            print(f"     Health: {'Healthy' if service_data['health']['healthy'] else 'Unhealthy'}")
            
            if service_data["gpu_status"].get("gpu_available"):
                gpu = service_data["gpu_status"]
                print(f"     GPU: {gpu.get('device_name', 'Unknown')} ({gpu.get('device', 'N/A')})")
                print(f"     Memory: {gpu.get('memory_allocated_gb', 0):.1f}GB used / {gpu.get('memory_total_gb', 0):.1f}GB total")
            else:
                print(f"     GPU: Not available")
            print()

async def main():
    """Main function to run GPU status check"""
    try:
        async with GPUStatusChecker() as checker:
            results = await checker.run_comprehensive_check()
            checker.print_summary(results)
            
            # Save results to file
            output_file = "/tmp/gpu_status_report.json"
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2)
            
            print(f"\n💾 Detailed report saved to: {output_file}")
            
            # Exit with error code if issues found
            if results["summary"]["issues"]:
                print(f"\n❌ Exiting with error code due to {len(results['summary']['issues'])} issues found")
                sys.exit(1)
            else:
                print(f"\n✅ All checks passed successfully!")
                sys.exit(0)
                
    except KeyboardInterrupt:
        print("\n\n⏹️  Check interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Unexpected error during GPU status check: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())