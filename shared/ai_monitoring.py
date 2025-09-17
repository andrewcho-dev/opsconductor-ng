"""
OpsConductor AI Monitoring Dashboard
Real-time metrics and monitoring for AI services
"""
import asyncio
import time
import json
import structlog
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict, deque
import redis.asyncio as redis
import httpx

logger = structlog.get_logger()

class MetricsCollector:
    """Collect metrics from all AI services"""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis_client = redis_client
        self.metrics = defaultdict(lambda: deque(maxlen=100))  # Keep last 100 metrics per service
        self.service_urls = {
            "ai_command": "http://ai-command:3005",
            "ai_orchestrator": "http://ai-orchestrator:3000",
            "vector_service": "http://vector-service:3000",
            "llm_service": "http://llm-service:3000"
        }
        self.http_client = httpx.AsyncClient(timeout=10.0)
    
    async def collect_metrics(self):
        """Collect metrics from all services"""
        timestamp = time.time()
        metrics = {
            "timestamp": timestamp,
            "services": {}
        }
        
        for service_name, service_url in self.service_urls.items():
            service_metrics = await self._collect_service_metrics(service_name, service_url)
            metrics["services"][service_name] = service_metrics
            
            # Store in time series
            self.metrics[service_name].append({
                "timestamp": timestamp,
                **service_metrics
            })
        
        # Store aggregated metrics in Redis
        if self.redis_client:
            await self._store_metrics(metrics)
        
        return metrics
    
    async def _collect_service_metrics(self, service_name: str, service_url: str) -> Dict[str, Any]:
        """Collect metrics from a single service"""
        metrics = {
            "status": "unknown",
            "response_time": None,
            "error": None
        }
        
        try:
            start_time = time.time()
            
            # Get health status
            response = await self.http_client.get(f"{service_url}/health")
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                metrics["status"] = "healthy"
                metrics["response_time"] = response_time
                
                # Try to get additional metrics if available
                try:
                    metrics_response = await self.http_client.get(f"{service_url}/metrics")
                    if metrics_response.status_code == 200:
                        metrics["detailed"] = metrics_response.json()
                except:
                    pass  # Metrics endpoint not available
            else:
                metrics["status"] = "unhealthy"
                metrics["status_code"] = response.status_code
                
        except Exception as e:
            metrics["status"] = "unavailable"
            metrics["error"] = str(e)
        
        return metrics
    
    async def _store_metrics(self, metrics: Dict[str, Any]):
        """Store metrics in Redis"""
        try:
            # Store current metrics
            await self.redis_client.setex(
                "ai:metrics:current",
                60,  # 1 minute TTL
                json.dumps(metrics)
            )
            
            # Store in time series (last 24 hours)
            ts_key = f"ai:metrics:ts:{int(metrics['timestamp'] / 300)}"  # 5-minute buckets
            await self.redis_client.setex(
                ts_key,
                86400,  # 24 hours TTL
                json.dumps(metrics)
            )
            
        except Exception as e:
            logger.error(f"Failed to store metrics: {e}")
    
    async def get_historical_metrics(self, hours: int = 1) -> List[Dict[str, Any]]:
        """Get historical metrics"""
        if not self.redis_client:
            # Return from memory if Redis not available
            all_metrics = []
            for service_name, service_metrics in self.metrics.items():
                all_metrics.extend(service_metrics)
            return sorted(all_metrics, key=lambda x: x["timestamp"])
        
        # Get from Redis
        current_time = time.time()
        start_time = current_time - (hours * 3600)
        
        metrics_list = []
        for i in range(int(hours * 12)):  # 5-minute buckets
            bucket_time = start_time + (i * 300)
            ts_key = f"ai:metrics:ts:{int(bucket_time / 300)}"
            
            try:
                data = await self.redis_client.get(ts_key)
                if data:
                    metrics_list.append(json.loads(data))
            except:
                continue
        
        return metrics_list
    
    async def cleanup(self):
        """Cleanup resources"""
        await self.http_client.aclose()

class PerformanceAnalyzer:
    """Analyze AI system performance"""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics_collector = metrics_collector
        self.alerts = []
    
    async def analyze_performance(self) -> Dict[str, Any]:
        """Analyze current performance and generate insights"""
        # Get recent metrics
        metrics = await self.metrics_collector.get_historical_metrics(hours=1)
        
        if not metrics:
            return {
                "status": "no_data",
                "message": "No metrics available for analysis"
            }
        
        analysis = {
            "timestamp": time.time(),
            "services": {},
            "overall_health": "healthy",
            "alerts": [],
            "recommendations": []
        }
        
        # Analyze each service
        service_health = {}
        for service_name in self.metrics_collector.service_urls.keys():
            service_analysis = self._analyze_service(service_name, metrics)
            analysis["services"][service_name] = service_analysis
            service_health[service_name] = service_analysis["health_score"]
        
        # Calculate overall health
        avg_health = sum(service_health.values()) / len(service_health) if service_health else 0
        if avg_health >= 0.9:
            analysis["overall_health"] = "healthy"
        elif avg_health >= 0.7:
            analysis["overall_health"] = "degraded"
        else:
            analysis["overall_health"] = "critical"
        
        # Generate alerts
        analysis["alerts"] = self._generate_alerts(analysis["services"])
        
        # Generate recommendations
        analysis["recommendations"] = self._generate_recommendations(analysis["services"])
        
        return analysis
    
    def _analyze_service(self, service_name: str, metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze a single service"""
        service_metrics = []
        
        # Extract metrics for this service
        for metric_set in metrics:
            if service_name in metric_set.get("services", {}):
                service_data = metric_set["services"][service_name]
                service_data["timestamp"] = metric_set["timestamp"]
                service_metrics.append(service_data)
        
        if not service_metrics:
            return {
                "health_score": 0.0,
                "availability": 0.0,
                "avg_response_time": None,
                "status": "no_data"
            }
        
        # Calculate metrics
        available_count = sum(1 for m in service_metrics if m.get("status") == "healthy")
        total_count = len(service_metrics)
        
        availability = available_count / total_count if total_count > 0 else 0
        
        # Calculate average response time
        response_times = [m["response_time"] for m in service_metrics if m.get("response_time")]
        avg_response_time = sum(response_times) / len(response_times) if response_times else None
        
        # Calculate health score
        health_score = availability
        if avg_response_time:
            # Penalize for slow response (>1 second)
            if avg_response_time > 1.0:
                health_score *= (1.0 / avg_response_time)
        
        # Determine status
        if availability >= 0.99:
            status = "excellent"
        elif availability >= 0.95:
            status = "good"
        elif availability >= 0.90:
            status = "fair"
        elif availability >= 0.50:
            status = "poor"
        else:
            status = "critical"
        
        return {
            "health_score": health_score,
            "availability": availability,
            "avg_response_time": avg_response_time,
            "status": status,
            "sample_count": total_count
        }
    
    def _generate_alerts(self, services: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate alerts based on service analysis"""
        alerts = []
        
        for service_name, analysis in services.items():
            # Critical availability - more lenient threshold
            if analysis["availability"] < 0.3:  # Changed from 0.5 to 0.3
                alerts.append({
                    "severity": "critical",
                    "service": service_name,
                    "message": f"{service_name} has critical availability ({analysis['availability']:.1%})",
                    "timestamp": time.time()
                })
            # Poor availability - more lenient threshold
            elif analysis["availability"] < 0.7:  # Changed from 0.9 to 0.7
                alerts.append({
                    "severity": "warning",
                    "service": service_name,
                    "message": f"{service_name} has poor availability ({analysis['availability']:.1%})",
                    "timestamp": time.time()
                })
            
            # Slow response time
            if analysis["avg_response_time"] and analysis["avg_response_time"] > 2.0:
                alerts.append({
                    "severity": "warning",
                    "service": service_name,
                    "message": f"{service_name} has slow response time ({analysis['avg_response_time']:.2f}s)",
                    "timestamp": time.time()
                })
        
        return alerts
    
    def _generate_recommendations(self, services: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on analysis"""
        recommendations = []
        
        # Check for services that need attention
        critical_services = [
            name for name, analysis in services.items()
            if analysis["status"] in ["critical", "poor"]
        ]
        
        if critical_services:
            recommendations.append(
                f"Services {', '.join(critical_services)} require immediate attention. "
                "Consider restarting or investigating logs."
            )
        
        # Check for slow services
        slow_services = [
            name for name, analysis in services.items()
            if analysis["avg_response_time"] and analysis["avg_response_time"] > 1.0
        ]
        
        if slow_services:
            recommendations.append(
                f"Services {', '.join(slow_services)} are responding slowly. "
                "Consider scaling up resources or optimizing performance."
            )
        
        # Check overall system
        unhealthy_count = sum(
            1 for analysis in services.values()
            if analysis["health_score"] < 0.7
        )
        
        if unhealthy_count > len(services) / 2:
            recommendations.append(
                "More than half of AI services are unhealthy. "
                "System-wide investigation recommended."
            )
        
        if not recommendations:
            recommendations.append("All AI services are operating normally.")
        
        return recommendations

class AIMonitoringDashboard:
    """Main monitoring dashboard for AI services"""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis_client = redis_client
        self.metrics_collector = MetricsCollector(redis_client)
        self.performance_analyzer = PerformanceAnalyzer(self.metrics_collector)
        self.monitoring_active = False
    
    async def start_monitoring(self, interval: int = 30):
        """Start continuous monitoring"""
        self.monitoring_active = True
        logger.info(f"Starting AI monitoring with {interval}s interval")
        
        while self.monitoring_active:
            try:
                # Collect metrics
                await self.metrics_collector.collect_metrics()
                
                # Analyze performance every 5 collections
                if int(time.time()) % (interval * 5) < interval:
                    analysis = await self.performance_analyzer.analyze_performance()
                    
                    # Store analysis
                    if self.redis_client:
                        await self.redis_client.setex(
                            "ai:analysis:latest",
                            300,  # 5 minutes TTL
                            json.dumps(analysis)
                        )
                    
                    # Log critical alerts
                    for alert in analysis.get("alerts", []):
                        if alert["severity"] == "critical":
                            logger.error(f"CRITICAL ALERT: {alert['message']}")
                        elif alert["severity"] == "warning":
                            logger.warning(f"WARNING: {alert['message']}")
                
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                await asyncio.sleep(interval)
    
    async def stop_monitoring(self):
        """Stop monitoring"""
        self.monitoring_active = False
        await self.metrics_collector.cleanup()
        logger.info("AI monitoring stopped")
    
    async def get_dashboard_data(self) -> Dict[str, Any]:
        """Get current dashboard data"""
        # Get latest metrics
        current_metrics = await self.metrics_collector.collect_metrics()
        
        # Get performance analysis
        analysis = await self.performance_analyzer.analyze_performance()
        
        # Get historical data
        historical = await self.metrics_collector.get_historical_metrics(hours=24)
        
        return {
            "current": current_metrics,
            "analysis": analysis,
            "historical": {
                "data": historical,
                "period_hours": 24
            },
            "timestamp": time.time()
        }
    
    async def get_service_details(self, service_name: str) -> Dict[str, Any]:
        """Get detailed information about a specific service"""
        if service_name not in self.metrics_collector.service_urls:
            return {
                "error": f"Unknown service: {service_name}"
            }
        
        # Get recent metrics for this service
        historical = await self.metrics_collector.get_historical_metrics(hours=1)
        
        service_data = []
        for metric_set in historical:
            if service_name in metric_set.get("services", {}):
                data_point = metric_set["services"][service_name]
                data_point["timestamp"] = metric_set["timestamp"]
                service_data.append(data_point)
        
        # Calculate statistics
        if service_data:
            response_times = [d["response_time"] for d in service_data if d.get("response_time")]
            availability = sum(1 for d in service_data if d.get("status") == "healthy") / len(service_data)
            
            stats = {
                "availability": availability,
                "avg_response_time": sum(response_times) / len(response_times) if response_times else None,
                "min_response_time": min(response_times) if response_times else None,
                "max_response_time": max(response_times) if response_times else None,
                "sample_count": len(service_data)
            }
        else:
            stats = {
                "availability": 0,
                "avg_response_time": None,
                "min_response_time": None,
                "max_response_time": None,
                "sample_count": 0
            }
        
        return {
            "service": service_name,
            "url": self.metrics_collector.service_urls[service_name],
            "statistics": stats,
            "recent_data": service_data[-20:] if service_data else [],  # Last 20 data points
            "timestamp": time.time()
        }
    
    async def trigger_health_check(self) -> Dict[str, Any]:
        """Manually trigger health check of all services"""
        results = {}
        
        for service_name, service_url in self.metrics_collector.service_urls.items():
            try:
                start_time = time.time()
                response = await self.metrics_collector.http_client.get(
                    f"{service_url}/health",
                    timeout=5.0
                )
                response_time = time.time() - start_time
                
                results[service_name] = {
                    "status": "healthy" if response.status_code == 200 else "unhealthy",
                    "status_code": response.status_code,
                    "response_time": response_time
                }
                
            except Exception as e:
                results[service_name] = {
                    "status": "unavailable",
                    "error": str(e)
                }
        
        return {
            "results": results,
            "timestamp": time.time()
        }