"""
📊 COMPREHENSIVE MONITORING DASHBOARD SYSTEM
Ollama Universal Intelligent Operations Engine (OUIOE)

Advanced monitoring dashboards for real-time system visibility and observability.
Provides interactive dashboards, real-time metrics, and comprehensive system insights.

Key Features:
- Real-time system metrics dashboards
- Interactive charts and visualizations
- Custom dashboard creation and management
- Alert integration and status displays
- Performance trend analysis
- Service health monitoring
- Resource utilization tracking
- Business metrics and KPIs
"""

import asyncio
import structlog
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import redis.asyncio as redis
from collections import defaultdict
import uuid

logger = structlog.get_logger()

class ChartType(Enum):
    """Chart types for dashboard widgets"""
    LINE = "line"
    BAR = "bar"
    PIE = "pie"
    GAUGE = "gauge"
    COUNTER = "counter"
    TABLE = "table"
    HEATMAP = "heatmap"
    SCATTER = "scatter"

class TimeRange(Enum):
    """Time ranges for dashboard data"""
    LAST_5_MINUTES = "5m"
    LAST_15_MINUTES = "15m"
    LAST_30_MINUTES = "30m"
    LAST_1_HOUR = "1h"
    LAST_6_HOURS = "6h"
    LAST_24_HOURS = "24h"
    LAST_7_DAYS = "7d"
    LAST_30_DAYS = "30d"

class RefreshInterval(Enum):
    """Dashboard refresh intervals"""
    REAL_TIME = 1  # 1 second
    FAST = 5       # 5 seconds
    NORMAL = 30    # 30 seconds
    SLOW = 60      # 1 minute
    MANUAL = 0     # Manual refresh only

@dataclass
class DashboardWidget:
    """Dashboard widget configuration"""
    id: str
    title: str
    chart_type: ChartType
    metric_queries: List[str]
    time_range: TimeRange = TimeRange.LAST_1_HOUR
    refresh_interval: RefreshInterval = RefreshInterval.NORMAL
    width: int = 6  # Grid width (1-12)
    height: int = 4  # Grid height
    position_x: int = 0
    position_y: int = 0
    options: Dict[str, Any] = field(default_factory=dict)
    filters: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Dashboard:
    """Dashboard configuration"""
    id: str
    name: str
    description: str
    widgets: List[DashboardWidget]
    tags: List[str] = field(default_factory=list)
    is_public: bool = False
    created_by: str = "system"
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    refresh_interval: RefreshInterval = RefreshInterval.NORMAL

@dataclass
class MetricData:
    """Metric data point for dashboard"""
    timestamp: datetime
    value: float
    labels: Dict[str, str] = field(default_factory=dict)

@dataclass
class ChartData:
    """Chart data for dashboard widgets"""
    labels: List[str]
    datasets: List[Dict[str, Any]]
    metadata: Dict[str, Any] = field(default_factory=dict)

class DashboardSystem:
    """
    📊 COMPREHENSIVE MONITORING DASHBOARD SYSTEM
    
    Provides real-time monitoring dashboards with interactive visualizations.
    """
    
    def __init__(self, redis_host: str = "redis", redis_port: int = 6379):
        self.redis_host = redis_host
        self.redis_port = redis_port
        self.redis_client: Optional[redis.Redis] = None
        
        # Dashboard storage
        self.dashboards: Dict[str, Dashboard] = {}
        self.dashboard_data_cache: Dict[str, Dict[str, Any]] = {}
        
        # Metrics integration
        self.metrics_collector = None
        self.alerting_system = None
        
        logger.info("📊 Dashboard System initialized")
    
    async def initialize(self):
        """Initialize dashboard system"""
        try:
            # Connect to Redis
            self.redis_client = redis.Redis(
                host=self.redis_host,
                port=self.redis_port,
                decode_responses=True
            )
            await self.redis_client.ping()
            
            # Load existing dashboards
            await self._load_dashboards()
            
            # Create default dashboards
            await self._create_default_dashboards()
            
            # Initialize metrics integration
            await self._initialize_integrations()
            
            logger.info("📊 Dashboard system initialized")
            return True
            
        except Exception as e:
            logger.error("❌ Failed to initialize dashboard system", error=str(e))
            return False
    
    async def _initialize_integrations(self):
        """Initialize integrations with metrics and alerting systems"""
        try:
            # Import and initialize metrics collector
            from monitoring.metrics_collector import get_metrics_collector
            self.metrics_collector = await get_metrics_collector()
            
            # Import and initialize alerting system
            from monitoring.alerting_system import get_alerting_system
            self.alerting_system = await get_alerting_system()
            
            logger.info("📊 Dashboard integrations initialized")
            
        except Exception as e:
            logger.warning("⚠️ Some dashboard integrations failed", error=str(e))
    
    async def _create_default_dashboards(self):
        """Create default monitoring dashboards"""
        
        # System Overview Dashboard
        system_overview = Dashboard(
            id="system_overview",
            name="System Overview",
            description="High-level system health and performance metrics",
            widgets=[
                DashboardWidget(
                    id="system_health_gauge",
                    title="System Health",
                    chart_type=ChartType.GAUGE,
                    metric_queries=["system_health_percent"],
                    width=4,
                    height=4,
                    position_x=0,
                    position_y=0,
                    options={"min": 0, "max": 100, "thresholds": [{"value": 80, "color": "green"}, {"value": 60, "color": "yellow"}, {"value": 0, "color": "red"}]}
                ),
                DashboardWidget(
                    id="cpu_usage_line",
                    title="CPU Usage",
                    chart_type=ChartType.LINE,
                    metric_queries=["system_cpu_usage_percent"],
                    width=4,
                    height=4,
                    position_x=4,
                    position_y=0,
                    time_range=TimeRange.LAST_1_HOUR
                ),
                DashboardWidget(
                    id="memory_usage_line",
                    title="Memory Usage",
                    chart_type=ChartType.LINE,
                    metric_queries=["system_memory_usage_percent"],
                    width=4,
                    height=4,
                    position_x=8,
                    position_y=0,
                    time_range=TimeRange.LAST_1_HOUR
                ),
                DashboardWidget(
                    id="request_rate_line",
                    title="Request Rate",
                    chart_type=ChartType.LINE,
                    metric_queries=["app_requests_per_second"],
                    width=6,
                    height=4,
                    position_x=0,
                    position_y=4,
                    time_range=TimeRange.LAST_1_HOUR
                ),
                DashboardWidget(
                    id="error_rate_line",
                    title="Error Rate",
                    chart_type=ChartType.LINE,
                    metric_queries=["app_error_rate_percent"],
                    width=6,
                    height=4,
                    position_x=6,
                    position_y=4,
                    time_range=TimeRange.LAST_1_HOUR
                ),
                DashboardWidget(
                    id="active_alerts_counter",
                    title="Active Alerts",
                    chart_type=ChartType.COUNTER,
                    metric_queries=["alerts_active_count"],
                    width=3,
                    height=2,
                    position_x=0,
                    position_y=8
                ),
                DashboardWidget(
                    id="response_time_gauge",
                    title="Avg Response Time",
                    chart_type=ChartType.GAUGE,
                    metric_queries=["app_response_time_ms"],
                    width=3,
                    height=2,
                    position_x=3,
                    position_y=8,
                    options={"min": 0, "max": 5000, "unit": "ms"}
                ),
                DashboardWidget(
                    id="throughput_counter",
                    title="Total Requests",
                    chart_type=ChartType.COUNTER,
                    metric_queries=["app_requests_total"],
                    width=3,
                    height=2,
                    position_x=6,
                    position_y=8
                ),
                DashboardWidget(
                    id="uptime_counter",
                    title="System Uptime",
                    chart_type=ChartType.COUNTER,
                    metric_queries=["system_uptime_seconds"],
                    width=3,
                    height=2,
                    position_x=9,
                    position_y=8,
                    options={"unit": "seconds", "format": "duration"}
                )
            ],
            tags=["system", "overview", "health"],
            refresh_interval=RefreshInterval.NORMAL
        )
        
        # AI Operations Dashboard
        ai_operations = Dashboard(
            id="ai_operations",
            name="AI Operations",
            description="AI-specific metrics and performance indicators",
            widgets=[
                DashboardWidget(
                    id="ai_decisions_rate",
                    title="AI Decisions per Minute",
                    chart_type=ChartType.LINE,
                    metric_queries=["ai_decisions_total"],
                    width=6,
                    height=4,
                    position_x=0,
                    position_y=0,
                    time_range=TimeRange.LAST_1_HOUR
                ),
                DashboardWidget(
                    id="ai_decision_time",
                    title="AI Decision Time",
                    chart_type=ChartType.LINE,
                    metric_queries=["ai_decision_time_ms"],
                    width=6,
                    height=4,
                    position_x=6,
                    position_y=0,
                    time_range=TimeRange.LAST_1_HOUR
                ),
                DashboardWidget(
                    id="workflow_executions",
                    title="Workflow Executions",
                    chart_type=ChartType.BAR,
                    metric_queries=["ai_workflows_executed"],
                    width=6,
                    height=4,
                    position_x=0,
                    position_y=4,
                    time_range=TimeRange.LAST_6_HOURS
                ),
                DashboardWidget(
                    id="workflow_execution_time",
                    title="Workflow Execution Time",
                    chart_type=ChartType.LINE,
                    metric_queries=["ai_workflow_execution_time_ms"],
                    width=6,
                    height=4,
                    position_x=6,
                    position_y=4,
                    time_range=TimeRange.LAST_1_HOUR
                ),
                DashboardWidget(
                    id="active_conversations",
                    title="Active Conversations",
                    chart_type=ChartType.GAUGE,
                    metric_queries=["ai_conversations_active"],
                    width=4,
                    height=3,
                    position_x=0,
                    position_y=8,
                    options={"min": 0, "max": 100}
                ),
                DashboardWidget(
                    id="thinking_stream_events",
                    title="Thinking Stream Events",
                    chart_type=ChartType.COUNTER,
                    metric_queries=["ai_thinking_stream_events"],
                    width=4,
                    height=3,
                    position_x=4,
                    position_y=8
                ),
                DashboardWidget(
                    id="ai_performance_heatmap",
                    title="AI Performance Heatmap",
                    chart_type=ChartType.HEATMAP,
                    metric_queries=["ai_decision_time_ms", "ai_workflow_execution_time_ms"],
                    width=4,
                    height=3,
                    position_x=8,
                    position_y=8,
                    time_range=TimeRange.LAST_24_HOURS
                )
            ],
            tags=["ai", "operations", "performance"],
            refresh_interval=RefreshInterval.FAST
        )
        
        # Service Health Dashboard
        service_health = Dashboard(
            id="service_health",
            name="Service Health",
            description="Health and performance of all integrated services",
            widgets=[
                DashboardWidget(
                    id="service_status_table",
                    title="Service Status",
                    chart_type=ChartType.TABLE,
                    metric_queries=["service_health_status"],
                    width=12,
                    height=6,
                    position_x=0,
                    position_y=0,
                    options={"columns": ["Service", "Status", "Response Time", "Last Check", "Uptime"]}
                ),
                DashboardWidget(
                    id="service_response_times",
                    title="Service Response Times",
                    chart_type=ChartType.LINE,
                    metric_queries=["service_call_duration_ms"],
                    width=6,
                    height=4,
                    position_x=0,
                    position_y=6,
                    time_range=TimeRange.LAST_1_HOUR
                ),
                DashboardWidget(
                    id="service_error_rates",
                    title="Service Error Rates",
                    chart_type=ChartType.LINE,
                    metric_queries=["service_errors_total"],
                    width=6,
                    height=4,
                    position_x=6,
                    position_y=6,
                    time_range=TimeRange.LAST_1_HOUR
                ),
                DashboardWidget(
                    id="circuit_breaker_status",
                    title="Circuit Breaker Status",
                    chart_type=ChartType.PIE,
                    metric_queries=["circuit_breaker_states"],
                    width=4,
                    height=3,
                    position_x=0,
                    position_y=10
                ),
                DashboardWidget(
                    id="rate_limit_status",
                    title="Rate Limit Status",
                    chart_type=ChartType.BAR,
                    metric_queries=["rate_limit_usage"],
                    width=4,
                    height=3,
                    position_x=4,
                    position_y=10
                ),
                DashboardWidget(
                    id="database_connections",
                    title="Database Connections",
                    chart_type=ChartType.GAUGE,
                    metric_queries=["db_connections_active"],
                    width=4,
                    height=3,
                    position_x=8,
                    position_y=10,
                    options={"min": 0, "max": 100}
                )
            ],
            tags=["services", "health", "monitoring"],
            refresh_interval=RefreshInterval.NORMAL
        )
        
        # Alerts Dashboard
        alerts_dashboard = Dashboard(
            id="alerts_overview",
            name="Alerts Overview",
            description="Comprehensive view of system alerts and incidents",
            widgets=[
                DashboardWidget(
                    id="alert_summary_counters",
                    title="Alert Summary",
                    chart_type=ChartType.COUNTER,
                    metric_queries=["alerts_by_severity"],
                    width=12,
                    height=2,
                    position_x=0,
                    position_y=0,
                    options={"layout": "horizontal"}
                ),
                DashboardWidget(
                    id="alerts_timeline",
                    title="Alerts Timeline",
                    chart_type=ChartType.LINE,
                    metric_queries=["alerts_triggered_count"],
                    width=8,
                    height=4,
                    position_x=0,
                    position_y=2,
                    time_range=TimeRange.LAST_24_HOURS
                ),
                DashboardWidget(
                    id="alerts_by_severity_pie",
                    title="Alerts by Severity",
                    chart_type=ChartType.PIE,
                    metric_queries=["alerts_by_severity"],
                    width=4,
                    height=4,
                    position_x=8,
                    position_y=2
                ),
                DashboardWidget(
                    id="active_alerts_table",
                    title="Active Alerts",
                    chart_type=ChartType.TABLE,
                    metric_queries=["active_alerts_details"],
                    width=12,
                    height=6,
                    position_x=0,
                    position_y=6,
                    options={"columns": ["Alert", "Severity", "Status", "Created", "Duration", "Actions"]}
                )
            ],
            tags=["alerts", "incidents", "monitoring"],
            refresh_interval=RefreshInterval.FAST
        )
        
        # Add all dashboards
        dashboards = [system_overview, ai_operations, service_health, alerts_dashboard]
        
        for dashboard in dashboards:
            await self.create_dashboard(dashboard)
        
        logger.info("📊 Default dashboards created", count=len(dashboards))
    
    async def create_dashboard(self, dashboard: Dashboard) -> str:
        """Create a new dashboard"""
        self.dashboards[dashboard.id] = dashboard
        
        # Store in Redis
        if self.redis_client:
            dashboard_data = {
                "id": dashboard.id,
                "name": dashboard.name,
                "description": dashboard.description,
                "widgets": [
                    {
                        "id": w.id,
                        "title": w.title,
                        "chart_type": w.chart_type.value,
                        "metric_queries": w.metric_queries,
                        "time_range": w.time_range.value,
                        "refresh_interval": w.refresh_interval.value,
                        "width": w.width,
                        "height": w.height,
                        "position_x": w.position_x,
                        "position_y": w.position_y,
                        "options": w.options,
                        "filters": w.filters
                    } for w in dashboard.widgets
                ],
                "tags": dashboard.tags,
                "is_public": dashboard.is_public,
                "created_by": dashboard.created_by,
                "created_at": dashboard.created_at.isoformat(),
                "updated_at": dashboard.updated_at.isoformat(),
                "refresh_interval": dashboard.refresh_interval.value
            }
            
            await self.redis_client.set(
                f"dashboard:{dashboard.id}",
                json.dumps(dashboard_data)
            )
        
        logger.info("📊 Dashboard created", id=dashboard.id, name=dashboard.name)
        return dashboard.id
    
    async def get_dashboard(self, dashboard_id: str) -> Optional[Dashboard]:
        """Get dashboard by ID"""
        return self.dashboards.get(dashboard_id)
    
    async def list_dashboards(self, tags: Optional[List[str]] = None) -> List[Dashboard]:
        """List dashboards, optionally filtered by tags"""
        dashboards = list(self.dashboards.values())
        
        if tags:
            dashboards = [
                d for d in dashboards 
                if any(tag in d.tags for tag in tags)
            ]
        
        return dashboards
    
    async def get_widget_data(self, dashboard_id: str, widget_id: str) -> Optional[ChartData]:
        """Get data for a specific widget"""
        dashboard = await self.get_dashboard(dashboard_id)
        if not dashboard:
            return None
        
        widget = next((w for w in dashboard.widgets if w.id == widget_id), None)
        if not widget:
            return None
        
        return await self._fetch_widget_data(widget)
    
    async def _fetch_widget_data(self, widget: DashboardWidget) -> ChartData:
        """Fetch data for a widget based on its configuration"""
        try:
            if widget.chart_type == ChartType.COUNTER:
                return await self._fetch_counter_data(widget)
            elif widget.chart_type == ChartType.GAUGE:
                return await self._fetch_gauge_data(widget)
            elif widget.chart_type == ChartType.LINE:
                return await self._fetch_line_data(widget)
            elif widget.chart_type == ChartType.BAR:
                return await self._fetch_bar_data(widget)
            elif widget.chart_type == ChartType.PIE:
                return await self._fetch_pie_data(widget)
            elif widget.chart_type == ChartType.TABLE:
                return await self._fetch_table_data(widget)
            elif widget.chart_type == ChartType.HEATMAP:
                return await self._fetch_heatmap_data(widget)
            else:
                return ChartData(labels=[], datasets=[])
                
        except Exception as e:
            logger.error("❌ Error fetching widget data", widget_id=widget.id, error=str(e))
            return ChartData(labels=[], datasets=[])
    
    async def _fetch_counter_data(self, widget: DashboardWidget) -> ChartData:
        """Fetch counter data"""
        if not self.metrics_collector:
            return ChartData(labels=[], datasets=[])
        
        values = []
        for metric_query in widget.metric_queries:
            value = await self.metrics_collector.get_metric_value(metric_query)
            values.append(value or 0)
        
        return ChartData(
            labels=widget.metric_queries,
            datasets=[{
                "data": values,
                "type": "counter"
            }]
        )
    
    async def _fetch_gauge_data(self, widget: DashboardWidget) -> ChartData:
        """Fetch gauge data"""
        if not self.metrics_collector or not widget.metric_queries:
            return ChartData(labels=[], datasets=[])
        
        metric_query = widget.metric_queries[0]
        value = await self.metrics_collector.get_metric_value(metric_query)
        
        return ChartData(
            labels=[metric_query],
            datasets=[{
                "data": [value or 0],
                "type": "gauge",
                "options": widget.options
            }]
        )
    
    async def _fetch_line_data(self, widget: DashboardWidget) -> ChartData:
        """Fetch line chart data"""
        if not self.metrics_collector:
            return ChartData(labels=[], datasets=[])
        
        # Convert time range to duration
        duration_map = {
            TimeRange.LAST_5_MINUTES: timedelta(minutes=5),
            TimeRange.LAST_15_MINUTES: timedelta(minutes=15),
            TimeRange.LAST_30_MINUTES: timedelta(minutes=30),
            TimeRange.LAST_1_HOUR: timedelta(hours=1),
            TimeRange.LAST_6_HOURS: timedelta(hours=6),
            TimeRange.LAST_24_HOURS: timedelta(hours=24),
            TimeRange.LAST_7_DAYS: timedelta(days=7),
            TimeRange.LAST_30_DAYS: timedelta(days=30)
        }
        
        duration = duration_map.get(widget.time_range, timedelta(hours=1))
        
        datasets = []
        labels = []
        
        for metric_query in widget.metric_queries:
            history = await self.metrics_collector.get_metric_history(metric_query, duration)
            
            if history:
                # Create time labels
                if not labels:
                    labels = [point.timestamp.strftime("%H:%M:%S") for point in history]
                
                # Create dataset
                datasets.append({
                    "label": metric_query,
                    "data": [point.value for point in history],
                    "borderColor": self._get_color_for_metric(metric_query),
                    "fill": False
                })
        
        return ChartData(labels=labels, datasets=datasets)
    
    async def _fetch_bar_data(self, widget: DashboardWidget) -> ChartData:
        """Fetch bar chart data"""
        # Similar to line data but formatted for bar chart
        return await self._fetch_line_data(widget)
    
    async def _fetch_pie_data(self, widget: DashboardWidget) -> ChartData:
        """Fetch pie chart data"""
        if not self.metrics_collector:
            return ChartData(labels=[], datasets=[])
        
        # For pie charts, we typically show distribution of a single metric
        if widget.metric_queries:
            metric_query = widget.metric_queries[0]
            
            # This would need to be implemented based on specific metric structure
            # For now, return sample data
            return ChartData(
                labels=["Category A", "Category B", "Category C"],
                datasets=[{
                    "data": [30, 45, 25],
                    "backgroundColor": ["#FF6384", "#36A2EB", "#FFCE56"]
                }]
            )
        
        return ChartData(labels=[], datasets=[])
    
    async def _fetch_table_data(self, widget: DashboardWidget) -> ChartData:
        """Fetch table data"""
        # Table data would be fetched from specific sources
        # This is a placeholder implementation
        return ChartData(
            labels=widget.options.get("columns", []),
            datasets=[{
                "data": [
                    ["Service A", "Healthy", "120ms", "2 min ago", "99.9%"],
                    ["Service B", "Warning", "250ms", "1 min ago", "98.5%"],
                    ["Service C", "Healthy", "95ms", "30 sec ago", "99.8%"]
                ],
                "type": "table"
            }]
        )
    
    async def _fetch_heatmap_data(self, widget: DashboardWidget) -> ChartData:
        """Fetch heatmap data"""
        # Heatmap implementation would depend on specific requirements
        return ChartData(labels=[], datasets=[])
    
    def _get_color_for_metric(self, metric_name: str) -> str:
        """Get consistent color for metric"""
        colors = [
            "#FF6384", "#36A2EB", "#FFCE56", "#4BC0C0", 
            "#9966FF", "#FF9F40", "#FF6384", "#C9CBCF"
        ]
        
        # Simple hash-based color assignment
        hash_value = hash(metric_name) % len(colors)
        return colors[hash_value]
    
    async def get_dashboard_data(self, dashboard_id: str) -> Optional[Dict[str, Any]]:
        """Get complete dashboard data"""
        dashboard = await self.get_dashboard(dashboard_id)
        if not dashboard:
            return None
        
        widget_data = {}
        for widget in dashboard.widgets:
            widget_data[widget.id] = await self._fetch_widget_data(widget)
        
        return {
            "dashboard": {
                "id": dashboard.id,
                "name": dashboard.name,
                "description": dashboard.description,
                "refresh_interval": dashboard.refresh_interval.value,
                "tags": dashboard.tags
            },
            "widgets": widget_data,
            "last_updated": datetime.now().isoformat()
        }
    
    async def _load_dashboards(self):
        """Load dashboards from Redis"""
        if not self.redis_client:
            return
        
        try:
            keys = await self.redis_client.keys("dashboard:*")
            for key in keys:
                dashboard_data = await self.redis_client.get(key)
                if dashboard_data:
                    data = json.loads(dashboard_data)
                    # Reconstruct Dashboard object
                    # Implementation would convert JSON back to Dashboard object
                    pass
        except Exception as e:
            logger.error("❌ Error loading dashboards", error=str(e))
    
    async def export_dashboard(self, dashboard_id: str) -> Optional[Dict[str, Any]]:
        """Export dashboard configuration"""
        dashboard = await self.get_dashboard(dashboard_id)
        if not dashboard:
            return None
        
        return {
            "id": dashboard.id,
            "name": dashboard.name,
            "description": dashboard.description,
            "widgets": [
                {
                    "id": w.id,
                    "title": w.title,
                    "chart_type": w.chart_type.value,
                    "metric_queries": w.metric_queries,
                    "time_range": w.time_range.value,
                    "refresh_interval": w.refresh_interval.value,
                    "width": w.width,
                    "height": w.height,
                    "position_x": w.position_x,
                    "position_y": w.position_y,
                    "options": w.options,
                    "filters": w.filters
                } for w in dashboard.widgets
            ],
            "tags": dashboard.tags,
            "refresh_interval": dashboard.refresh_interval.value,
            "export_timestamp": datetime.now().isoformat()
        }
    
    async def get_system_summary(self) -> Dict[str, Any]:
        """Get system summary for dashboard overview"""
        summary = {
            "total_dashboards": len(self.dashboards),
            "dashboard_categories": {},
            "system_status": "healthy",
            "last_updated": datetime.now().isoformat()
        }
        
        # Count dashboards by tags
        for dashboard in self.dashboards.values():
            for tag in dashboard.tags:
                summary["dashboard_categories"][tag] = summary["dashboard_categories"].get(tag, 0) + 1
        
        return summary

# Global dashboard system instance
_dashboard_system: Optional[DashboardSystem] = None

async def get_dashboard_system() -> DashboardSystem:
    """Get the global dashboard system instance"""
    global _dashboard_system
    if _dashboard_system is None:
        _dashboard_system = DashboardSystem()
        await _dashboard_system.initialize()
    return _dashboard_system

async def initialize_dashboard_system() -> bool:
    """Initialize the global dashboard system"""
    try:
        system = await get_dashboard_system()
        logger.info("📊 Global dashboard system initialized")
        return True
    except Exception as e:
        logger.error("❌ Failed to initialize global dashboard system", error=str(e))
        return False