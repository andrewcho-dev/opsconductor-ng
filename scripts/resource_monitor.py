#!/usr/bin/env python3
"""
Resource Monitoring Script
Monitors system resources during load testing
"""

import asyncio
import aiohttp
import psutil
import time
import json
import sys
from datetime import datetime
from typing import List, Dict, Any

# Configuration
MONITOR_INTERVAL = 5  # seconds
API_STATS_URL = "http://localhost:3005/api/v1/tools/performance/stats"


class ResourceMonitor:
    """Monitors system and application resources"""
    
    def __init__(self, duration: int):
        self.duration = duration
        self.samples = []
        self.running = False
        
    async def get_api_stats(self) -> Dict[str, Any]:
        """Fetch API performance stats"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(API_STATS_URL, timeout=aiohttp.ClientTimeout(total=5)) as response:
                    if response.status == 200:
                        return await response.json()
        except Exception as e:
            print(f"⚠ Warning: Could not fetch API stats: {e}")
        return {}
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get system resource usage"""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Network stats
        net_io = psutil.net_io_counters()
        
        return {
            "cpu_percent": cpu_percent,
            "memory": {
                "total_mb": memory.total / (1024 * 1024),
                "available_mb": memory.available / (1024 * 1024),
                "used_mb": memory.used / (1024 * 1024),
                "percent": memory.percent
            },
            "disk": {
                "total_gb": disk.total / (1024 * 1024 * 1024),
                "used_gb": disk.used / (1024 * 1024 * 1024),
                "free_gb": disk.free / (1024 * 1024 * 1024),
                "percent": disk.percent
            },
            "network": {
                "bytes_sent": net_io.bytes_sent,
                "bytes_recv": net_io.bytes_recv,
                "packets_sent": net_io.packets_sent,
                "packets_recv": net_io.packets_recv
            }
        }
    
    def get_process_stats(self) -> Dict[str, Any]:
        """Get stats for Python processes"""
        python_processes = []
        
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'num_threads']):
            try:
                if 'python' in proc.info['name'].lower():
                    python_processes.append({
                        "pid": proc.info['pid'],
                        "name": proc.info['name'],
                        "cpu_percent": proc.info['cpu_percent'],
                        "memory_percent": proc.info['memory_percent'],
                        "num_threads": proc.info['num_threads']
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        return {
            "count": len(python_processes),
            "processes": python_processes[:5]  # Top 5
        }
    
    async def collect_sample(self):
        """Collect a single monitoring sample"""
        timestamp = datetime.now().isoformat()
        
        # Get all stats
        system_stats = self.get_system_stats()
        process_stats = self.get_process_stats()
        api_stats = await self.get_api_stats()
        
        sample = {
            "timestamp": timestamp,
            "system": system_stats,
            "processes": process_stats,
            "api": api_stats
        }
        
        self.samples.append(sample)
        return sample
    
    async def monitor(self):
        """Run monitoring loop"""
        print(f"\n{'='*60}")
        print(f"📊 Starting Resource Monitor")
        print(f"{'='*60}")
        print(f"Duration: {self.duration}s")
        print(f"Sample Interval: {MONITOR_INTERVAL}s")
        print(f"{'='*60}\n")
        
        self.running = True
        start_time = time.time()
        
        while time.time() - start_time < self.duration:
            sample = await self.collect_sample()
            
            # Print current stats
            elapsed = time.time() - start_time
            print(f"⏱ {elapsed:.0f}s | CPU: {sample['system']['cpu_percent']:.1f}% | "
                  f"Memory: {sample['system']['memory']['percent']:.1f}% | "
                  f"Python Processes: {sample['processes']['count']}")
            
            # Print API stats if available
            if sample['api']:
                cache = sample['api'].get('cache', {})
                pool = sample['api'].get('connection_pool', {})
                if cache:
                    print(f"  Cache: {cache.get('size', 0)} items, "
                          f"{cache.get('hit_rate', 0):.1f}% hit rate")
                if pool:
                    print(f"  Pool: {pool.get('min_connections', 0)}-{pool.get('max_connections', 0)} connections")
            
            await asyncio.sleep(MONITOR_INTERVAL)
        
        self.running = False
        print(f"\n✓ Monitoring completed!\n")
    
    def analyze(self) -> Dict[str, Any]:
        """Analyze collected samples"""
        if not self.samples:
            return {}
        
        # Extract metrics
        cpu_values = [s['system']['cpu_percent'] for s in self.samples]
        memory_values = [s['system']['memory']['percent'] for s in self.samples]
        
        # API metrics
        cache_hit_rates = []
        cache_sizes = []
        
        for sample in self.samples:
            if sample.get('api', {}).get('cache'):
                cache = sample['api']['cache']
                if 'hit_rate' in cache:
                    cache_hit_rates.append(cache['hit_rate'])
                if 'size' in cache:
                    cache_sizes.append(cache['size'])
        
        analysis = {
            "samples_collected": len(self.samples),
            "duration_seconds": (datetime.fromisoformat(self.samples[-1]['timestamp']) - 
                               datetime.fromisoformat(self.samples[0]['timestamp'])).total_seconds(),
            "cpu": {
                "min": min(cpu_values),
                "max": max(cpu_values),
                "avg": sum(cpu_values) / len(cpu_values),
                "samples": cpu_values
            },
            "memory": {
                "min": min(memory_values),
                "max": max(memory_values),
                "avg": sum(memory_values) / len(memory_values),
                "samples": memory_values
            }
        }
        
        if cache_hit_rates:
            analysis["cache"] = {
                "min_hit_rate": min(cache_hit_rates),
                "max_hit_rate": max(cache_hit_rates),
                "avg_hit_rate": sum(cache_hit_rates) / len(cache_hit_rates),
                "avg_size": sum(cache_sizes) / len(cache_sizes) if cache_sizes else 0
            }
        
        return analysis
    
    def print_analysis(self):
        """Print analysis results"""
        analysis = self.analyze()
        
        if not analysis:
            print("⚠ No data collected")
            return
        
        print(f"\n{'='*60}")
        print(f"📊 RESOURCE MONITORING ANALYSIS")
        print(f"{'='*60}\n")
        
        print(f"⏱ Duration: {analysis['duration_seconds']:.1f}s")
        print(f"📊 Samples: {analysis['samples_collected']}\n")
        
        # CPU
        cpu = analysis['cpu']
        print(f"💻 CPU Usage:")
        print(f"  Min: {cpu['min']:.1f}%")
        print(f"  Avg: {cpu['avg']:.1f}%")
        print(f"  Max: {cpu['max']:.1f}%\n")
        
        # Memory
        mem = analysis['memory']
        print(f"🧠 Memory Usage:")
        print(f"  Min: {mem['min']:.1f}%")
        print(f"  Avg: {mem['avg']:.1f}%")
        print(f"  Max: {mem['max']:.1f}%\n")
        
        # Cache
        if 'cache' in analysis:
            cache = analysis['cache']
            print(f"💾 Cache Performance:")
            print(f"  Avg Hit Rate: {cache['avg_hit_rate']:.1f}%")
            print(f"  Avg Size: {cache['avg_size']:.0f} items\n")
        
        # Assessment
        print(f"{'='*60}")
        print(f"🎯 RESOURCE ASSESSMENT")
        print(f"{'='*60}\n")
        
        issues = []
        
        if cpu['max'] > 80:
            issues.append(f"⚠ High CPU usage detected: {cpu['max']:.1f}%")
        else:
            print(f"✓ CPU usage healthy (max {cpu['max']:.1f}%)")
        
        if mem['max'] > 80:
            issues.append(f"⚠ High memory usage detected: {mem['max']:.1f}%")
        else:
            print(f"✓ Memory usage healthy (max {mem['max']:.1f}%)")
        
        if 'cache' in analysis:
            if cache['avg_hit_rate'] < 80:
                issues.append(f"⚠ Low cache hit rate: {cache['avg_hit_rate']:.1f}%")
            else:
                print(f"✓ Cache hit rate good ({cache['avg_hit_rate']:.1f}%)")
        
        if issues:
            print(f"\n⚠ Issues Found:")
            for issue in issues:
                print(f"  {issue}")
        else:
            print(f"\n✓ All resource metrics are healthy!")
        
        print(f"\n{'='*60}\n")
    
    def save_results(self, filename: str):
        """Save results to file"""
        analysis = self.analyze()
        
        results = {
            "analysis": analysis,
            "samples": self.samples
        }
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"📄 Results saved to: {filename}")


async def main():
    """Main entry point"""
    duration = 60  # Default 60 seconds
    
    if len(sys.argv) > 1:
        try:
            duration = int(sys.argv[1])
        except ValueError:
            print(f"Invalid duration: {sys.argv[1]}")
            sys.exit(1)
    
    monitor = ResourceMonitor(duration)
    await monitor.monitor()
    
    monitor.print_analysis()
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"/tmp/resource_monitor_{timestamp}.json"
    monitor.save_results(results_file)


if __name__ == "__main__":
    asyncio.run(main())