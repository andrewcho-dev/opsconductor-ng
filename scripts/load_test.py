#!/usr/bin/env python3
"""
Load Testing Script for Tool Catalog API
Simulates realistic user load and measures performance metrics
"""

import asyncio
import aiohttp
import time
import statistics
import json
import sys
from datetime import datetime
from typing import List, Dict, Any
from collections import defaultdict

# Configuration
API_BASE_URL = "http://localhost:3005/api/v1/tools"
CONCURRENT_USERS = 2  # Realistic concurrent user count
TEST_DURATION_SECONDS = 60  # 1 minute test
RAMP_UP_SECONDS = 10  # Gradual ramp-up period

# Test scenarios - realistic user workflows
TEST_SCENARIOS = [
    {
        "name": "List Tools",
        "method": "GET",
        "endpoint": "",
        "weight": 35  # 35% of requests
    },
    {
        "name": "Search by Name",
        "method": "GET",
        "endpoint": "?name=test",
        "weight": 20
    },
    {
        "name": "Get Tool by Name",
        "method": "GET",
        "endpoint": "/TOOL_NAME",  # Will be replaced with actual name
        "weight": 15
    },
    {
        "name": "Search Enabled Tools",
        "method": "GET",
        "endpoint": "?enabled=true",
        "weight": 15
    },
    {
        "name": "Search Latest Version",
        "method": "GET",
        "endpoint": "?latest=true",
        "weight": 10
    },
    {
        "name": "Performance Stats",
        "method": "GET",
        "endpoint": "/performance/stats",
        "weight": 5
    }
]


class LoadTestMetrics:
    """Collects and analyzes load test metrics"""
    
    def __init__(self):
        self.requests_sent = 0
        self.requests_completed = 0
        self.requests_failed = 0
        self.response_times = []
        self.errors = defaultdict(int)
        self.scenario_metrics = defaultdict(lambda: {
            "count": 0,
            "success": 0,
            "failed": 0,
            "response_times": []
        })
        self.start_time = None
        self.end_time = None
        
    def record_request(self, scenario: str, success: bool, response_time: float, error: str = None):
        """Record a request result"""
        self.requests_completed += 1
        self.response_times.append(response_time)
        
        metrics = self.scenario_metrics[scenario]
        metrics["count"] += 1
        metrics["response_times"].append(response_time)
        
        if success:
            metrics["success"] += 1
        else:
            self.requests_failed += 1
            metrics["failed"] += 1
            if error:
                self.errors[error] += 1
    
    def get_percentile(self, data: List[float], percentile: float) -> float:
        """Calculate percentile from data"""
        if not data:
            return 0.0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]
    
    def get_summary(self) -> Dict[str, Any]:
        """Get test summary statistics"""
        duration = (self.end_time - self.start_time) if self.end_time and self.start_time else 0
        
        summary = {
            "duration_seconds": round(duration, 2),
            "total_requests": self.requests_completed,
            "successful_requests": self.requests_completed - self.requests_failed,
            "failed_requests": self.requests_failed,
            "requests_per_second": round(self.requests_completed / duration, 2) if duration > 0 else 0,
            "response_times": {
                "min_ms": round(min(self.response_times) * 1000, 2) if self.response_times else 0,
                "max_ms": round(max(self.response_times) * 1000, 2) if self.response_times else 0,
                "mean_ms": round(statistics.mean(self.response_times) * 1000, 2) if self.response_times else 0,
                "median_ms": round(statistics.median(self.response_times) * 1000, 2) if self.response_times else 0,
                "p95_ms": round(self.get_percentile(self.response_times, 95) * 1000, 2),
                "p99_ms": round(self.get_percentile(self.response_times, 99) * 1000, 2)
            },
            "error_rate_percent": round((self.requests_failed / self.requests_completed * 100), 2) if self.requests_completed > 0 else 0,
            "errors": dict(self.errors),
            "scenarios": {}
        }
        
        # Add per-scenario metrics
        for scenario, metrics in self.scenario_metrics.items():
            if metrics["count"] > 0:
                summary["scenarios"][scenario] = {
                    "total": metrics["count"],
                    "success": metrics["success"],
                    "failed": metrics["failed"],
                    "success_rate_percent": round((metrics["success"] / metrics["count"] * 100), 2),
                    "avg_response_ms": round(statistics.mean(metrics["response_times"]) * 1000, 2) if metrics["response_times"] else 0,
                    "p95_response_ms": round(self.get_percentile(metrics["response_times"], 95) * 1000, 2)
                }
        
        return summary


class LoadTester:
    """Executes load tests against the API"""
    
    def __init__(self, base_url: str, concurrent_users: int, duration: int, ramp_up: int):
        self.base_url = base_url
        self.concurrent_users = concurrent_users
        self.duration = duration
        self.ramp_up = ramp_up
        self.metrics = LoadTestMetrics()
        self.running = False
        self.tool_ids = []
        
    async def setup(self):
        """Setup test - fetch tool names for realistic testing"""
        print("🔧 Setting up load test...")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}") as response:
                    if response.status == 200:
                        data = await response.json()
                        self.tool_ids = [tool["tool_name"] for tool in data.get("tools", [])[:10]]
                        print(f"✓ Found {len(self.tool_ids)} tools for testing")
                    else:
                        print(f"⚠ Warning: Could not fetch tools (status {response.status})")
        except Exception as e:
            print(f"⚠ Warning: Setup failed: {e}")
    
    def select_scenario(self) -> Dict[str, Any]:
        """Select a random scenario based on weights"""
        import random
        total_weight = sum(s["weight"] for s in TEST_SCENARIOS)
        rand = random.randint(1, total_weight)
        
        current = 0
        for scenario in TEST_SCENARIOS:
            current += scenario["weight"]
            if rand <= current:
                # Replace placeholder with actual tool name
                endpoint = scenario["endpoint"]
                if "TOOL_NAME" in endpoint and self.tool_ids:
                    endpoint = endpoint.replace("TOOL_NAME", random.choice(self.tool_ids))
                
                return {
                    "name": scenario["name"],
                    "method": scenario["method"],
                    "url": f"{self.base_url}{endpoint}"
                }
        
        return {
            "name": TEST_SCENARIOS[0]["name"],
            "method": TEST_SCENARIOS[0]["method"],
            "url": f"{self.base_url}{TEST_SCENARIOS[0]['endpoint']}"
        }
    
    async def execute_request(self, session: aiohttp.ClientSession, scenario: Dict[str, Any]):
        """Execute a single request"""
        start_time = time.time()
        success = False
        error = None
        
        try:
            async with session.request(scenario["method"], scenario["url"], timeout=aiohttp.ClientTimeout(total=30)) as response:
                await response.read()  # Consume response body
                success = 200 <= response.status < 300
                if not success:
                    error = f"HTTP {response.status}"
        except asyncio.TimeoutError:
            error = "Timeout"
        except aiohttp.ClientError as e:
            error = f"Client Error: {type(e).__name__}"
        except Exception as e:
            error = f"Error: {type(e).__name__}"
        
        response_time = time.time() - start_time
        self.metrics.record_request(scenario["name"], success, response_time, error)
    
    async def user_session(self, user_id: int, start_delay: float):
        """Simulate a single user session"""
        # Ramp-up delay
        await asyncio.sleep(start_delay)
        
        async with aiohttp.ClientSession() as session:
            while self.running:
                scenario = self.select_scenario()
                await self.execute_request(session, scenario)
                
                # Think time - simulate user reading/processing
                await asyncio.sleep(0.5)  # 500ms between requests
    
    async def run(self):
        """Run the load test"""
        print(f"\n{'='*60}")
        print(f"🚀 Starting Load Test")
        print(f"{'='*60}")
        print(f"Target: {self.base_url}")
        print(f"Concurrent Users: {self.concurrent_users}")
        print(f"Test Duration: {self.duration}s")
        print(f"Ramp-up Period: {self.ramp_up}s")
        print(f"{'='*60}\n")
        
        # Setup
        await self.setup()
        
        # Start test
        self.running = True
        self.metrics.start_time = time.time()
        
        # Calculate ramp-up delays
        delays = [i * (self.ramp_up / self.concurrent_users) for i in range(self.concurrent_users)]
        
        # Start user sessions
        tasks = [
            asyncio.create_task(self.user_session(i, delays[i]))
            for i in range(self.concurrent_users)
        ]
        
        # Progress reporting
        start = time.time()
        while time.time() - start < self.duration:
            await asyncio.sleep(5)
            elapsed = time.time() - start
            progress = (elapsed / self.duration) * 100
            rps = self.metrics.requests_completed / elapsed if elapsed > 0 else 0
            print(f"⏱ Progress: {progress:.0f}% | Requests: {self.metrics.requests_completed} | RPS: {rps:.1f} | Errors: {self.metrics.requests_failed}")
        
        # Stop test
        self.running = False
        self.metrics.end_time = time.time()
        
        # Wait for tasks to complete
        await asyncio.gather(*tasks, return_exceptions=True)
        
        print(f"\n✓ Load test completed!\n")


def print_results(metrics: LoadTestMetrics):
    """Print formatted test results"""
    summary = metrics.get_summary()
    
    print(f"\n{'='*60}")
    print(f"📊 LOAD TEST RESULTS")
    print(f"{'='*60}\n")
    
    # Overall metrics
    print(f"⏱ Duration: {summary['duration_seconds']}s")
    print(f"📨 Total Requests: {summary['total_requests']}")
    print(f"✓ Successful: {summary['successful_requests']}")
    print(f"✗ Failed: {summary['failed_requests']}")
    print(f"📈 Throughput: {summary['requests_per_second']} req/s")
    print(f"❌ Error Rate: {summary['error_rate_percent']}%\n")
    
    # Response times
    rt = summary['response_times']
    print(f"⚡ Response Times:")
    print(f"  Min:    {rt['min_ms']}ms")
    print(f"  Mean:   {rt['mean_ms']}ms")
    print(f"  Median: {rt['median_ms']}ms")
    print(f"  P95:    {rt['p95_ms']}ms")
    print(f"  P99:    {rt['p99_ms']}ms")
    print(f"  Max:    {rt['max_ms']}ms\n")
    
    # Scenario breakdown
    print(f"📋 Scenario Breakdown:")
    for scenario, metrics in summary['scenarios'].items():
        print(f"\n  {scenario}:")
        print(f"    Requests: {metrics['total']} ({metrics['success']} success, {metrics['failed']} failed)")
        print(f"    Success Rate: {metrics['success_rate_percent']}%")
        print(f"    Avg Response: {metrics['avg_response_ms']}ms")
        print(f"    P95 Response: {metrics['p95_response_ms']}ms")
    
    # Errors
    if summary['errors']:
        print(f"\n❌ Errors:")
        for error, count in summary['errors'].items():
            print(f"  {error}: {count}")
    
    # Performance assessment
    print(f"\n{'='*60}")
    print(f"🎯 PERFORMANCE ASSESSMENT")
    print(f"{'='*60}\n")
    
    score = 0
    max_score = 100
    
    # Check P95 response time (40 points)
    if rt['p95_ms'] < 50:
        score += 40
        print(f"✓ P95 Response Time: {rt['p95_ms']}ms < 50ms target (40/40)")
    elif rt['p95_ms'] < 100:
        points = int(40 * (100 - rt['p95_ms']) / 50)
        score += points
        print(f"⚠ P95 Response Time: {rt['p95_ms']}ms (target: <50ms) ({points}/40)")
    else:
        print(f"✗ P95 Response Time: {rt['p95_ms']}ms > 100ms (0/40)")
    
    # Check error rate (30 points)
    if summary['error_rate_percent'] == 0:
        score += 30
        print(f"✓ Error Rate: 0% (30/30)")
    elif summary['error_rate_percent'] < 1:
        points = int(30 * (1 - summary['error_rate_percent']))
        score += points
        print(f"⚠ Error Rate: {summary['error_rate_percent']}% ({points}/30)")
    else:
        print(f"✗ Error Rate: {summary['error_rate_percent']}% > 1% (0/30)")
    
    # Check throughput (20 points)
    if summary['requests_per_second'] >= 10:
        score += 20
        print(f"✓ Throughput: {summary['requests_per_second']} req/s >= 10 req/s (20/20)")
    elif summary['requests_per_second'] >= 5:
        points = int(20 * summary['requests_per_second'] / 10)
        score += points
        print(f"⚠ Throughput: {summary['requests_per_second']} req/s (target: >=10) ({points}/20)")
    else:
        print(f"✗ Throughput: {summary['requests_per_second']} req/s < 5 req/s (0/20)")
    
    # Check consistency (10 points)
    if rt['p99_ms'] < rt['p95_ms'] * 2:
        score += 10
        print(f"✓ Consistency: P99/P95 ratio = {rt['p99_ms']/rt['p95_ms']:.2f} < 2.0 (10/10)")
    else:
        print(f"⚠ Consistency: P99/P95 ratio = {rt['p99_ms']/rt['p95_ms']:.2f} >= 2.0 (0/10)")
    
    print(f"\n{'='*60}")
    print(f"🏆 OVERALL SCORE: {score}/{max_score}")
    
    if score >= 90:
        print(f"✓ EXCELLENT - System performs exceptionally under load")
    elif score >= 70:
        print(f"✓ GOOD - System performs well under load")
    elif score >= 50:
        print(f"⚠ FAIR - System has some performance issues")
    else:
        print(f"✗ POOR - System needs significant optimization")
    
    print(f"{'='*60}\n")
    
    return score


async def main():
    """Main entry point"""
    # Parse command line arguments
    concurrent_users = CONCURRENT_USERS
    duration = TEST_DURATION_SECONDS
    
    if len(sys.argv) > 1:
        try:
            concurrent_users = int(sys.argv[1])
        except ValueError:
            print(f"Invalid concurrent users: {sys.argv[1]}")
            sys.exit(1)
    
    if len(sys.argv) > 2:
        try:
            duration = int(sys.argv[2])
        except ValueError:
            print(f"Invalid duration: {sys.argv[2]}")
            sys.exit(1)
    
    # Run load test
    tester = LoadTester(API_BASE_URL, concurrent_users, duration, RAMP_UP_SECONDS)
    await tester.run()
    
    # Print results
    score = print_results(tester.metrics)
    
    # Save results to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"/tmp/load_test_results_{timestamp}.json"
    
    with open(results_file, 'w') as f:
        json.dump(tester.metrics.get_summary(), f, indent=2)
    
    print(f"📄 Results saved to: {results_file}\n")
    
    # Exit with appropriate code
    sys.exit(0 if score >= 70 else 1)


if __name__ == "__main__":
    asyncio.run(main())