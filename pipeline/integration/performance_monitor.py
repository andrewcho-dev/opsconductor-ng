"""
Performance Monitor - Phase 5

Comprehensive performance monitoring and benchmarking for the OpsConductor pipeline.
Tracks latency, throughput, resource usage, and system characteristics.
"""

import asyncio
import time
import psutil
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import statistics

from pipeline.orchestrator import PipelineOrchestrator, PipelineResult


class PerformanceTestType(Enum):
    """Types of performance tests."""
    LATENCY = "latency"
    THROUGHPUT = "throughput"
    LOAD = "load"
    STRESS = "stress"
    ENDURANCE = "endurance"


@dataclass
class PerformanceMetrics:
    """Performance metrics for a test run."""
    test_type: PerformanceTestType
    test_name: str
    duration_seconds: float
    total_requests: int
    successful_requests: int
    failed_requests: int
    
    # Timing metrics (in milliseconds)
    avg_response_time_ms: float
    min_response_time_ms: float
    max_response_time_ms: float
    p50_response_time_ms: float
    p90_response_time_ms: float
    p95_response_time_ms: float
    p99_response_time_ms: float
    
    # Throughput metrics
    requests_per_second: float
    
    # Resource metrics
    avg_cpu_percent: float
    max_cpu_percent: float
    avg_memory_mb: float
    max_memory_mb: float
    
    # Error metrics
    error_rate_percent: float
    
    # Additional details
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ResourceSnapshot:
    """Snapshot of system resources at a point in time."""
    timestamp: float
    cpu_percent: float
    memory_mb: float
    memory_percent: float


class PerformanceMonitor:
    """
    Comprehensive performance monitoring for the OpsConductor pipeline.
    
    Capabilities:
    - Latency testing and measurement
    - Throughput benchmarking
    - Load testing with concurrent requests
    - Stress testing to find system limits
    - Resource usage monitoring
    - Performance regression detection
    """
    
    def __init__(self):
        """Initialize the performance monitor."""
        self.orchestrator = PipelineOrchestrator()
        self.test_results: List[PerformanceMetrics] = []
        self.resource_snapshots: List[ResourceSnapshot] = []
        
        # Performance targets
        self.targets = {
            "max_avg_response_time_ms": 5000,  # 5 seconds
            "max_p95_response_time_ms": 10000,  # 10 seconds
            "min_requests_per_second": 1.0,
            "max_error_rate_percent": 5.0,
            "max_memory_mb": 512
        }
    
    def _take_resource_snapshot(self) -> ResourceSnapshot:
        """Take a snapshot of current system resources - FAIL HARD if psutil fails."""
        process = psutil.Process()
        cpu_percent = process.cpu_percent()
        memory_info = process.memory_info()
        memory_mb = memory_info.rss / 1024 / 1024
        memory_percent = process.memory_percent()
        
        return ResourceSnapshot(
            timestamp=time.time(),
            cpu_percent=cpu_percent,
            memory_mb=memory_mb,
            memory_percent=memory_percent
        )
    
    def _calculate_percentile(self, data: List[float], percentile: float) -> float:
        """Calculate percentile from a list of values."""
        if not data:
            return 0.0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]
    
    async def _monitor_resources_during_test(
        self, 
        test_duration_seconds: float,
        sample_interval_seconds: float = 1.0
    ) -> List[ResourceSnapshot]:
        """Monitor system resources during a test."""
        snapshots = []
        start_time = time.time()
        
        while time.time() - start_time < test_duration_seconds:
            snapshot = self._take_resource_snapshot()
            snapshots.append(snapshot)
            await asyncio.sleep(sample_interval_seconds)
        
        return snapshots
    
    async def test_latency(
        self, 
        user_request: str = "Check server status",
        num_requests: int = 10
    ) -> PerformanceMetrics:
        """
        Test response latency with sequential requests.
        
        Args:
            user_request: The request to test with
            num_requests: Number of sequential requests to make
            
        Returns:
            PerformanceMetrics with latency test results
        """
        print(f"⏱️  Running latency test with {num_requests} sequential requests...")
        
        start_time = time.time()
        response_times = []
        successful_requests = 0
        failed_requests = 0
        
        # Start resource monitoring
        resource_task = asyncio.create_task(
            self._monitor_resources_during_test(num_requests * 2)  # Estimate duration
        )
        
        # Execute sequential requests
        for i in range(num_requests):
            request_start = time.time()
            
            try:
                result = await self.orchestrator.process_request(
                    user_request, 
                    f"latency_test_{i}"
                )
                
                request_time = (time.time() - request_start) * 1000
                response_times.append(request_time)
                
                if result.success:
                    successful_requests += 1
                else:
                    failed_requests += 1
                    
            except Exception as e:
                failed_requests += 1
                # Use timeout as response time for failed requests
                response_times.append(30000)  # 30 seconds
        
        total_duration = time.time() - start_time
        
        # Stop resource monitoring
        resource_task.cancel()
        try:
            await resource_task
        except asyncio.CancelledError:
            pass
        
        # Calculate metrics
        if response_times:
            avg_response_time = statistics.mean(response_times)
            min_response_time = min(response_times)
            max_response_time = max(response_times)
            p50_response_time = self._calculate_percentile(response_times, 50)
            p90_response_time = self._calculate_percentile(response_times, 90)
            p95_response_time = self._calculate_percentile(response_times, 95)
            p99_response_time = self._calculate_percentile(response_times, 99)
        else:
            avg_response_time = min_response_time = max_response_time = 0.0
            p50_response_time = p90_response_time = p95_response_time = p99_response_time = 0.0
        
        requests_per_second = num_requests / total_duration if total_duration > 0 else 0.0
        error_rate = (failed_requests / num_requests * 100) if num_requests > 0 else 0.0
        
        # Resource metrics
        if self.resource_snapshots:
            cpu_values = [s.cpu_percent for s in self.resource_snapshots]
            memory_values = [s.memory_mb for s in self.resource_snapshots]
            avg_cpu = statistics.mean(cpu_values) if cpu_values else 0.0
            max_cpu = max(cpu_values) if cpu_values else 0.0
            avg_memory = statistics.mean(memory_values) if memory_values else 0.0
            max_memory = max(memory_values) if memory_values else 0.0
        else:
            avg_cpu = max_cpu = avg_memory = max_memory = 0.0
        
        metrics = PerformanceMetrics(
            test_type=PerformanceTestType.LATENCY,
            test_name="sequential_latency_test",
            duration_seconds=total_duration,
            total_requests=num_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            avg_response_time_ms=avg_response_time,
            min_response_time_ms=min_response_time,
            max_response_time_ms=max_response_time,
            p50_response_time_ms=p50_response_time,
            p90_response_time_ms=p90_response_time,
            p95_response_time_ms=p95_response_time,
            p99_response_time_ms=p99_response_time,
            requests_per_second=requests_per_second,
            avg_cpu_percent=avg_cpu,
            max_cpu_percent=max_cpu,
            avg_memory_mb=avg_memory,
            max_memory_mb=max_memory,
            error_rate_percent=error_rate,
            details={
                "response_times": response_times,
                "test_request": user_request
            }
        )
        
        self.test_results.append(metrics)
        
        print(f"  Avg Response Time: {avg_response_time:.1f}ms")
        print(f"  P95 Response Time: {p95_response_time:.1f}ms")
        print(f"  Success Rate: {successful_requests}/{num_requests} ({100-error_rate:.1f}%)")
        
        return metrics
    
    async def test_throughput(
        self, 
        user_request: str = "Check server status",
        concurrent_requests: int = 5,
        test_duration_seconds: float = 30.0
    ) -> PerformanceMetrics:
        """
        Test system throughput with concurrent requests over time.
        
        Args:
            user_request: The request to test with
            concurrent_requests: Number of concurrent requests to maintain
            test_duration_seconds: How long to run the test
            
        Returns:
            PerformanceMetrics with throughput test results
        """
        print(f"🚀 Running throughput test: {concurrent_requests} concurrent requests for {test_duration_seconds}s...")
        
        start_time = time.time()
        response_times = []
        successful_requests = 0
        failed_requests = 0
        request_counter = 0
        
        # Start resource monitoring
        resource_task = asyncio.create_task(
            self._monitor_resources_during_test(test_duration_seconds)
        )
        
        async def make_request():
            nonlocal request_counter, successful_requests, failed_requests
            request_id = request_counter
            request_counter += 1
            
            request_start = time.time()
            
            try:
                result = await self.orchestrator.process_request(
                    user_request, 
                    f"throughput_test_{request_id}"
                )
                
                request_time = (time.time() - request_start) * 1000
                response_times.append(request_time)
                
                if result.success:
                    successful_requests += 1
                else:
                    failed_requests += 1
                    
            except Exception as e:
                failed_requests += 1
                response_times.append(30000)  # 30 seconds timeout
        
        # Maintain concurrent requests for the test duration
        active_tasks = set()
        
        while time.time() - start_time < test_duration_seconds:
            # Start new requests to maintain concurrency
            while len(active_tasks) < concurrent_requests:
                task = asyncio.create_task(make_request())
                active_tasks.add(task)
            
            # Remove completed tasks
            done_tasks = {task for task in active_tasks if task.done()}
            active_tasks -= done_tasks
            
            # Small delay to prevent busy waiting
            await asyncio.sleep(0.1)
        
        # Wait for remaining tasks to complete
        if active_tasks:
            await asyncio.gather(*active_tasks, return_exceptions=True)
        
        total_duration = time.time() - start_time
        
        # Stop resource monitoring
        resource_task.cancel()
        try:
            await resource_task
        except asyncio.CancelledError:
            pass
        
        # Calculate metrics
        total_requests = successful_requests + failed_requests
        
        if response_times:
            avg_response_time = statistics.mean(response_times)
            min_response_time = min(response_times)
            max_response_time = max(response_times)
            p50_response_time = self._calculate_percentile(response_times, 50)
            p90_response_time = self._calculate_percentile(response_times, 90)
            p95_response_time = self._calculate_percentile(response_times, 95)
            p99_response_time = self._calculate_percentile(response_times, 99)
        else:
            avg_response_time = min_response_time = max_response_time = 0.0
            p50_response_time = p90_response_time = p95_response_time = p99_response_time = 0.0
        
        requests_per_second = total_requests / total_duration if total_duration > 0 else 0.0
        error_rate = (failed_requests / total_requests * 100) if total_requests > 0 else 0.0
        
        # Resource metrics
        if self.resource_snapshots:
            cpu_values = [s.cpu_percent for s in self.resource_snapshots]
            memory_values = [s.memory_mb for s in self.resource_snapshots]
            avg_cpu = statistics.mean(cpu_values) if cpu_values else 0.0
            max_cpu = max(cpu_values) if cpu_values else 0.0
            avg_memory = statistics.mean(memory_values) if memory_values else 0.0
            max_memory = max(memory_values) if memory_values else 0.0
        else:
            avg_cpu = max_cpu = avg_memory = max_memory = 0.0
        
        metrics = PerformanceMetrics(
            test_type=PerformanceTestType.THROUGHPUT,
            test_name="concurrent_throughput_test",
            duration_seconds=total_duration,
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            avg_response_time_ms=avg_response_time,
            min_response_time_ms=min_response_time,
            max_response_time_ms=max_response_time,
            p50_response_time_ms=p50_response_time,
            p90_response_time_ms=p90_response_time,
            p95_response_time_ms=p95_response_time,
            p99_response_time_ms=p99_response_time,
            requests_per_second=requests_per_second,
            avg_cpu_percent=avg_cpu,
            max_cpu_percent=max_cpu,
            avg_memory_mb=avg_memory,
            max_memory_mb=max_memory,
            error_rate_percent=error_rate,
            details={
                "concurrent_requests": concurrent_requests,
                "test_request": user_request,
                "total_response_times": len(response_times)
            }
        )
        
        self.test_results.append(metrics)
        
        print(f"  Total Requests: {total_requests}")
        print(f"  Throughput: {requests_per_second:.1f} req/s")
        print(f"  Avg Response Time: {avg_response_time:.1f}ms")
        print(f"  Success Rate: {successful_requests}/{total_requests} ({100-error_rate:.1f}%)")
        
        return metrics
    
    async def test_load(
        self, 
        user_requests: List[str] = None,
        max_concurrent: int = 10,
        ramp_up_seconds: float = 10.0,
        steady_state_seconds: float = 30.0
    ) -> PerformanceMetrics:
        """
        Test system under increasing load with ramp-up.
        
        Args:
            user_requests: List of requests to cycle through
            max_concurrent: Maximum concurrent requests to reach
            ramp_up_seconds: Time to ramp up to max concurrent
            steady_state_seconds: Time to maintain max concurrent
            
        Returns:
            PerformanceMetrics with load test results
        """
        if user_requests is None:
            user_requests = [
                "Check server status",
                "List running services",
                "Show system metrics",
                "Check disk usage",
                "Monitor network traffic"
            ]
        
        print(f"📈 Running load test: ramp up to {max_concurrent} concurrent over {ramp_up_seconds}s, then steady for {steady_state_seconds}s...")
        
        start_time = time.time()
        response_times = []
        successful_requests = 0
        failed_requests = 0
        request_counter = 0
        
        total_test_duration = ramp_up_seconds + steady_state_seconds
        
        # Start resource monitoring
        resource_task = asyncio.create_task(
            self._monitor_resources_during_test(total_test_duration)
        )
        
        async def make_request():
            nonlocal request_counter, successful_requests, failed_requests
            request_id = request_counter
            request_counter += 1
            
            # Cycle through user requests
            user_request = user_requests[request_id % len(user_requests)]
            
            request_start = time.time()
            
            try:
                result = await self.orchestrator.process_request(
                    user_request, 
                    f"load_test_{request_id}"
                )
                
                request_time = (time.time() - request_start) * 1000
                response_times.append(request_time)
                
                if result.success:
                    successful_requests += 1
                else:
                    failed_requests += 1
                    
            except Exception as e:
                failed_requests += 1
                response_times.append(30000)  # 30 seconds timeout
        
        # Execute load test with ramp-up
        active_tasks = set()
        
        while time.time() - start_time < total_test_duration:
            elapsed = time.time() - start_time
            
            # Calculate target concurrency based on ramp-up
            if elapsed < ramp_up_seconds:
                # Ramp up phase
                target_concurrent = int((elapsed / ramp_up_seconds) * max_concurrent)
            else:
                # Steady state phase
                target_concurrent = max_concurrent
            
            # Adjust active tasks to match target concurrency
            while len(active_tasks) < target_concurrent:
                task = asyncio.create_task(make_request())
                active_tasks.add(task)
            
            # Remove completed tasks
            done_tasks = {task for task in active_tasks if task.done()}
            active_tasks -= done_tasks
            
            # Small delay
            await asyncio.sleep(0.1)
        
        # Wait for remaining tasks to complete
        if active_tasks:
            await asyncio.gather(*active_tasks, return_exceptions=True)
        
        total_duration = time.time() - start_time
        
        # Stop resource monitoring
        resource_task.cancel()
        try:
            await resource_task
        except asyncio.CancelledError:
            pass
        
        # Calculate metrics
        total_requests = successful_requests + failed_requests
        
        if response_times:
            avg_response_time = statistics.mean(response_times)
            min_response_time = min(response_times)
            max_response_time = max(response_times)
            p50_response_time = self._calculate_percentile(response_times, 50)
            p90_response_time = self._calculate_percentile(response_times, 90)
            p95_response_time = self._calculate_percentile(response_times, 95)
            p99_response_time = self._calculate_percentile(response_times, 99)
        else:
            avg_response_time = min_response_time = max_response_time = 0.0
            p50_response_time = p90_response_time = p95_response_time = p99_response_time = 0.0
        
        requests_per_second = total_requests / total_duration if total_duration > 0 else 0.0
        error_rate = (failed_requests / total_requests * 100) if total_requests > 0 else 0.0
        
        # Resource metrics
        if self.resource_snapshots:
            cpu_values = [s.cpu_percent for s in self.resource_snapshots]
            memory_values = [s.memory_mb for s in self.resource_snapshots]
            avg_cpu = statistics.mean(cpu_values) if cpu_values else 0.0
            max_cpu = max(cpu_values) if cpu_values else 0.0
            avg_memory = statistics.mean(memory_values) if memory_values else 0.0
            max_memory = max(memory_values) if memory_values else 0.0
        else:
            avg_cpu = max_cpu = avg_memory = max_memory = 0.0
        
        metrics = PerformanceMetrics(
            test_type=PerformanceTestType.LOAD,
            test_name="ramp_up_load_test",
            duration_seconds=total_duration,
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            avg_response_time_ms=avg_response_time,
            min_response_time_ms=min_response_time,
            max_response_time_ms=max_response_time,
            p50_response_time_ms=p50_response_time,
            p90_response_time_ms=p90_response_time,
            p95_response_time_ms=p95_response_time,
            p99_response_time_ms=p99_response_time,
            requests_per_second=requests_per_second,
            avg_cpu_percent=avg_cpu,
            max_cpu_percent=max_cpu,
            avg_memory_mb=avg_memory,
            max_memory_mb=max_memory,
            error_rate_percent=error_rate,
            details={
                "max_concurrent": max_concurrent,
                "ramp_up_seconds": ramp_up_seconds,
                "steady_state_seconds": steady_state_seconds,
                "request_types": len(user_requests)
            }
        )
        
        self.test_results.append(metrics)
        
        print(f"  Total Requests: {total_requests}")
        print(f"  Peak Throughput: {requests_per_second:.1f} req/s")
        print(f"  P95 Response Time: {p95_response_time:.1f}ms")
        print(f"  Success Rate: {successful_requests}/{total_requests} ({100-error_rate:.1f}%)")
        print(f"  Peak Memory Usage: {max_memory:.1f}MB")
        
        return metrics
    
    def check_performance_targets(self, metrics: PerformanceMetrics) -> Dict[str, Any]:
        """
        Check if performance metrics meet defined targets.
        
        Args:
            metrics: Performance metrics to check
            
        Returns:
            Dictionary with target check results
        """
        checks = {}
        
        # Check average response time
        checks["avg_response_time"] = {
            "target": self.targets["max_avg_response_time_ms"],
            "actual": metrics.avg_response_time_ms,
            "passed": metrics.avg_response_time_ms <= self.targets["max_avg_response_time_ms"]
        }
        
        # Check P95 response time
        checks["p95_response_time"] = {
            "target": self.targets["max_p95_response_time_ms"],
            "actual": metrics.p95_response_time_ms,
            "passed": metrics.p95_response_time_ms <= self.targets["max_p95_response_time_ms"]
        }
        
        # Check requests per second
        checks["requests_per_second"] = {
            "target": self.targets["min_requests_per_second"],
            "actual": metrics.requests_per_second,
            "passed": metrics.requests_per_second >= self.targets["min_requests_per_second"]
        }
        
        # Check error rate
        checks["error_rate"] = {
            "target": self.targets["max_error_rate_percent"],
            "actual": metrics.error_rate_percent,
            "passed": metrics.error_rate_percent <= self.targets["max_error_rate_percent"]
        }
        
        # Check memory usage
        checks["memory_usage"] = {
            "target": self.targets["max_memory_mb"],
            "actual": metrics.max_memory_mb,
            "passed": metrics.max_memory_mb <= self.targets["max_memory_mb"]
        }
        
        # Overall pass/fail
        all_passed = all(check["passed"] for check in checks.values())
        
        return {
            "overall_passed": all_passed,
            "checks": checks,
            "summary": f"{'✅ PASSED' if all_passed else '❌ FAILED'} performance targets"
        }
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get a summary of all performance test results."""
        if not self.test_results:
            return {"message": "No performance test results available"}
        
        # Group results by test type
        results_by_type = {}
        for result in self.test_results:
            test_type = result.test_type.value
            if test_type not in results_by_type:
                results_by_type[test_type] = []
            results_by_type[test_type].append(result)
        
        # Calculate overall statistics
        all_response_times = []
        all_throughputs = []
        all_error_rates = []
        
        for result in self.test_results:
            all_response_times.append(result.avg_response_time_ms)
            all_throughputs.append(result.requests_per_second)
            all_error_rates.append(result.error_rate_percent)
        
        return {
            "total_tests": len(self.test_results),
            "test_types": list(results_by_type.keys()),
            "overall_stats": {
                "avg_response_time_ms": statistics.mean(all_response_times) if all_response_times else 0.0,
                "avg_throughput_rps": statistics.mean(all_throughputs) if all_throughputs else 0.0,
                "avg_error_rate_percent": statistics.mean(all_error_rates) if all_error_rates else 0.0
            },
            "results_by_type": {
                test_type: {
                    "count": len(results),
                    "avg_response_time_ms": statistics.mean([r.avg_response_time_ms for r in results]),
                    "avg_throughput_rps": statistics.mean([r.requests_per_second for r in results]),
                    "avg_error_rate_percent": statistics.mean([r.error_rate_percent for r in results])
                }
                for test_type, results in results_by_type.items()
            }
        }