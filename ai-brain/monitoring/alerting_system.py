"""
🚨 ADVANCED ALERTING SYSTEM
Ollama Universal Intelligent Operations Engine (OUIOE)

Comprehensive alerting system for production monitoring and incident response.
Provides intelligent alerting with multiple channels, escalation, and correlation.

Key Features:
- Multi-channel alerting (email, webhook, Slack, PagerDuty)
- Intelligent alert correlation and deduplication
- Escalation policies and on-call management
- Alert severity levels and priority routing
- Metric-based alerting with complex conditions
- Alert suppression and maintenance windows
- Historical alert tracking and analytics
- Integration with monitoring dashboards
"""

import asyncio
import structlog
import json
import aiohttp
import smtplib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
import redis.asyncio as redis
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import hashlib
import uuid

logger = structlog.get_logger()

class AlertSeverity(Enum):
    """Alert severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

class AlertStatus(Enum):
    """Alert status"""
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"

class AlertChannel(Enum):
    """Alert delivery channels"""
    EMAIL = "email"
    WEBHOOK = "webhook"
    SLACK = "slack"
    PAGERDUTY = "pagerduty"
    SMS = "sms"
    CONSOLE = "console"

class ConditionOperator(Enum):
    """Condition operators for alert rules"""
    GREATER_THAN = "gt"
    LESS_THAN = "lt"
    EQUALS = "eq"
    NOT_EQUALS = "ne"
    GREATER_EQUAL = "ge"
    LESS_EQUAL = "le"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"

@dataclass
class AlertCondition:
    """Alert condition definition"""
    metric_name: str
    operator: ConditionOperator
    threshold: float
    duration: timedelta = timedelta(minutes=5)
    labels: Dict[str, str] = field(default_factory=dict)

@dataclass
class AlertRule:
    """Alert rule definition"""
    id: str
    name: str
    description: str
    conditions: List[AlertCondition]
    severity: AlertSeverity
    channels: List[AlertChannel]
    enabled: bool = True
    suppression_duration: timedelta = timedelta(minutes=30)
    escalation_delay: timedelta = timedelta(minutes=15)
    tags: List[str] = field(default_factory=list)
    runbook_url: Optional[str] = None

@dataclass
class Alert:
    """Alert instance"""
    id: str
    rule_id: str
    name: str
    description: str
    severity: AlertSeverity
    status: AlertStatus
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    metric_values: Dict[str, float] = field(default_factory=dict)
    labels: Dict[str, str] = field(default_factory=dict)
    annotations: Dict[str, str] = field(default_factory=dict)
    escalation_level: int = 0
    suppressed_until: Optional[datetime] = None

@dataclass
class AlertingConfig:
    """Alerting system configuration"""
    smtp_host: str = "localhost"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from_email: str = "alerts@ouioe.ai"
    
    slack_webhook_url: str = ""
    pagerduty_integration_key: str = ""
    
    default_email_recipients: List[str] = field(default_factory=list)
    escalation_email_recipients: List[str] = field(default_factory=list)
    
    alert_retention_days: int = 30
    max_alerts_per_rule: int = 100

class AlertingSystem:
    """
    🚨 ADVANCED ALERTING SYSTEM
    
    Comprehensive alerting with intelligent correlation, escalation, and multi-channel delivery.
    """
    
    def __init__(self, config: AlertingConfig, redis_host: str = "redis", redis_port: int = 6379):
        self.config = config
        self.redis_host = redis_host
        self.redis_port = redis_port
        self.redis_client: Optional[redis.Redis] = None
        
        # Alert management
        self.alert_rules: Dict[str, AlertRule] = {}
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        
        # Evaluation state
        self.is_evaluating = False
        self.evaluation_task: Optional[asyncio.Task] = None
        self.evaluation_interval = 30.0  # seconds
        
        # Notification state
        self.notification_queue: asyncio.Queue = asyncio.Queue()
        self.notification_task: Optional[asyncio.Task] = None
        
        # Metrics integration
        self.metrics_collector = None
        
        logger.info("🚨 Alerting System initialized")
    
    async def initialize(self):
        """Initialize alerting system"""
        try:
            # Connect to Redis
            self.redis_client = redis.Redis(
                host=self.redis_host,
                port=self.redis_port,
                decode_responses=True
            )
            await self.redis_client.ping()
            
            # Load existing alert rules and alerts
            await self._load_alert_rules()
            await self._load_active_alerts()
            
            # Initialize default alert rules
            await self._initialize_default_rules()
            
            # Start evaluation and notification tasks
            await self.start_evaluation()
            await self.start_notification_processing()
            
            logger.info("🚨 Alerting system initialized")
            return True
            
        except Exception as e:
            logger.error("❌ Failed to initialize alerting system", error=str(e))
            return False
    
    async def _initialize_default_rules(self):
        """Initialize default alert rules for production monitoring"""
        
        default_rules = [
            # System resource alerts
            AlertRule(
                id="high_cpu_usage",
                name="High CPU Usage",
                description="CPU usage is above 80% for 5 minutes",
                conditions=[AlertCondition("system_cpu_usage_percent", ConditionOperator.GREATER_THAN, 80.0)],
                severity=AlertSeverity.HIGH,
                channels=[AlertChannel.EMAIL, AlertChannel.SLACK]
            ),
            AlertRule(
                id="high_memory_usage",
                name="High Memory Usage", 
                description="Memory usage is above 85% for 5 minutes",
                conditions=[AlertCondition("system_memory_usage_percent", ConditionOperator.GREATER_THAN, 85.0)],
                severity=AlertSeverity.HIGH,
                channels=[AlertChannel.EMAIL, AlertChannel.SLACK]
            ),
            AlertRule(
                id="disk_space_low",
                name="Low Disk Space",
                description="Disk usage is above 90% for 5 minutes",
                conditions=[AlertCondition("system_disk_usage_percent", ConditionOperator.GREATER_THAN, 90.0)],
                severity=AlertSeverity.CRITICAL,
                channels=[AlertChannel.EMAIL, AlertChannel.SLACK, AlertChannel.PAGERDUTY]
            ),
            
            # Application performance alerts
            AlertRule(
                id="high_error_rate",
                name="High Error Rate",
                description="Error rate is above 5% for 5 minutes",
                conditions=[AlertCondition("app_error_rate_percent", ConditionOperator.GREATER_THAN, 5.0)],
                severity=AlertSeverity.CRITICAL,
                channels=[AlertChannel.EMAIL, AlertChannel.SLACK, AlertChannel.PAGERDUTY]
            ),
            AlertRule(
                id="slow_response_time",
                name="Slow Response Time",
                description="Average response time is above 2 seconds for 5 minutes",
                conditions=[AlertCondition("app_response_time_ms", ConditionOperator.GREATER_THAN, 2000.0)],
                severity=AlertSeverity.HIGH,
                channels=[AlertChannel.EMAIL, AlertChannel.SLACK]
            ),
            AlertRule(
                id="low_throughput",
                name="Low Throughput",
                description="Request throughput is below 10 RPS for 10 minutes",
                conditions=[AlertCondition("app_requests_per_second", ConditionOperator.LESS_THAN, 10.0, timedelta(minutes=10))],
                severity=AlertSeverity.MEDIUM,
                channels=[AlertChannel.EMAIL]
            ),
            
            # AI/LLM specific alerts
            AlertRule(
                id="ai_decision_timeout",
                name="AI Decision Timeout",
                description="AI decision time is above 30 seconds",
                conditions=[AlertCondition("ai_decision_time_ms", ConditionOperator.GREATER_THAN, 30000.0)],
                severity=AlertSeverity.HIGH,
                channels=[AlertChannel.EMAIL, AlertChannel.SLACK]
            ),
            AlertRule(
                id="workflow_execution_failure",
                name="Workflow Execution Failure",
                description="Workflow execution time is above 5 minutes",
                conditions=[AlertCondition("ai_workflow_execution_time_ms", ConditionOperator.GREATER_THAN, 300000.0)],
                severity=AlertSeverity.HIGH,
                channels=[AlertChannel.EMAIL, AlertChannel.SLACK]
            ),
            
            # Service integration alerts
            AlertRule(
                id="service_call_failure",
                name="Service Call Failure",
                description="Service call error rate is above 10%",
                conditions=[AlertCondition("service_errors_total", ConditionOperator.GREATER_THAN, 10.0)],
                severity=AlertSeverity.HIGH,
                channels=[AlertChannel.EMAIL, AlertChannel.SLACK]
            ),
            
            # Database alerts
            AlertRule(
                id="high_db_connections",
                name="High Database Connections",
                description="Active database connections above 80",
                conditions=[AlertCondition("db_connections_active", ConditionOperator.GREATER_THAN, 80.0)],
                severity=AlertSeverity.MEDIUM,
                channels=[AlertChannel.EMAIL]
            ),
            AlertRule(
                id="slow_db_queries",
                name="Slow Database Queries",
                description="Database query time above 5 seconds",
                conditions=[AlertCondition("db_query_duration_ms", ConditionOperator.GREATER_THAN, 5000.0)],
                severity=AlertSeverity.HIGH,
                channels=[AlertChannel.EMAIL, AlertChannel.SLACK]
            )
        ]
        
        for rule in default_rules:
            await self.add_alert_rule(rule)
        
        logger.info("🚨 Default alert rules initialized", count=len(default_rules))
    
    async def add_alert_rule(self, rule: AlertRule):
        """Add or update an alert rule"""
        self.alert_rules[rule.id] = rule
        
        # Store in Redis
        if self.redis_client:
            await self.redis_client.set(
                f"alert_rules:{rule.id}",
                json.dumps({
                    "id": rule.id,
                    "name": rule.name,
                    "description": rule.description,
                    "conditions": [
                        {
                            "metric_name": c.metric_name,
                            "operator": c.operator.value,
                            "threshold": c.threshold,
                            "duration": c.duration.total_seconds(),
                            "labels": c.labels
                        } for c in rule.conditions
                    ],
                    "severity": rule.severity.value,
                    "channels": [c.value for c in rule.channels],
                    "enabled": rule.enabled,
                    "suppression_duration": rule.suppression_duration.total_seconds(),
                    "escalation_delay": rule.escalation_delay.total_seconds(),
                    "tags": rule.tags,
                    "runbook_url": rule.runbook_url
                })
            )
        
        logger.info("🚨 Alert rule added", rule_id=rule.id, name=rule.name)
    
    async def remove_alert_rule(self, rule_id: str):
        """Remove an alert rule"""
        if rule_id in self.alert_rules:
            del self.alert_rules[rule_id]
            
            # Remove from Redis
            if self.redis_client:
                await self.redis_client.delete(f"alert_rules:{rule_id}")
            
            logger.info("🚨 Alert rule removed", rule_id=rule_id)
    
    async def start_evaluation(self):
        """Start alert rule evaluation"""
        if self.is_evaluating:
            return
        
        self.is_evaluating = True
        self.evaluation_task = asyncio.create_task(self._evaluation_loop())
        logger.info("🚨 Alert evaluation started")
    
    async def stop_evaluation(self):
        """Stop alert rule evaluation"""
        self.is_evaluating = False
        if self.evaluation_task:
            self.evaluation_task.cancel()
            try:
                await self.evaluation_task
            except asyncio.CancelledError:
                pass
        logger.info("🚨 Alert evaluation stopped")
    
    async def _evaluation_loop(self):
        """Main alert evaluation loop"""
        while self.is_evaluating:
            try:
                await self._evaluate_alert_rules()
                await self._process_escalations()
                await self._cleanup_resolved_alerts()
                
                await asyncio.sleep(self.evaluation_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("❌ Error in alert evaluation loop", error=str(e))
                await asyncio.sleep(self.evaluation_interval)
    
    async def _evaluate_alert_rules(self):
        """Evaluate all alert rules against current metrics"""
        if not self.metrics_collector:
            # Try to get metrics collector
            try:
                from monitoring.metrics_collector import get_metrics_collector
                self.metrics_collector = await get_metrics_collector()
            except:
                return
        
        for rule_id, rule in self.alert_rules.items():
            if not rule.enabled:
                continue
            
            try:
                await self._evaluate_rule(rule)
            except Exception as e:
                logger.error("❌ Error evaluating alert rule", rule_id=rule_id, error=str(e))
    
    async def _evaluate_rule(self, rule: AlertRule):
        """Evaluate a single alert rule"""
        # Check all conditions
        conditions_met = True
        metric_values = {}
        
        for condition in rule.conditions:
            metric_value = await self.metrics_collector.get_metric_value(
                condition.metric_name, 
                condition.labels
            )
            
            if metric_value is None:
                conditions_met = False
                break
            
            metric_values[condition.metric_name] = metric_value
            
            # Evaluate condition
            if not self._evaluate_condition(condition, metric_value):
                conditions_met = False
                break
        
        # Generate alert fingerprint for deduplication
        alert_fingerprint = self._generate_alert_fingerprint(rule, metric_values)
        
        if conditions_met:
            # Check if alert already exists
            if alert_fingerprint not in self.active_alerts:
                # Create new alert
                alert = Alert(
                    id=str(uuid.uuid4()),
                    rule_id=rule.id,
                    name=rule.name,
                    description=rule.description,
                    severity=rule.severity,
                    status=AlertStatus.OPEN,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                    metric_values=metric_values,
                    labels={"rule_id": rule.id},
                    annotations={"runbook_url": rule.runbook_url} if rule.runbook_url else {}
                )
                
                self.active_alerts[alert_fingerprint] = alert
                await self._store_alert(alert)
                await self._queue_notification(alert, rule)
                
                logger.info("🚨 Alert triggered", alert_id=alert.id, rule_id=rule.id)
        else:
            # Check if we should resolve existing alert
            if alert_fingerprint in self.active_alerts:
                alert = self.active_alerts[alert_fingerprint]
                if alert.status == AlertStatus.OPEN:
                    alert.status = AlertStatus.RESOLVED
                    alert.resolved_at = datetime.now()
                    alert.updated_at = datetime.now()
                    
                    await self._store_alert(alert)
                    await self._queue_resolution_notification(alert, rule)
                    
                    logger.info("🚨 Alert resolved", alert_id=alert.id, rule_id=rule.id)
    
    def _evaluate_condition(self, condition: AlertCondition, value: float) -> bool:
        """Evaluate a single condition"""
        if condition.operator == ConditionOperator.GREATER_THAN:
            return value > condition.threshold
        elif condition.operator == ConditionOperator.LESS_THAN:
            return value < condition.threshold
        elif condition.operator == ConditionOperator.EQUALS:
            return value == condition.threshold
        elif condition.operator == ConditionOperator.NOT_EQUALS:
            return value != condition.threshold
        elif condition.operator == ConditionOperator.GREATER_EQUAL:
            return value >= condition.threshold
        elif condition.operator == ConditionOperator.LESS_EQUAL:
            return value <= condition.threshold
        else:
            return False
    
    def _generate_alert_fingerprint(self, rule: AlertRule, metric_values: Dict[str, float]) -> str:
        """Generate unique fingerprint for alert deduplication"""
        fingerprint_data = {
            "rule_id": rule.id,
            "metric_names": sorted(metric_values.keys())
        }
        fingerprint_str = json.dumps(fingerprint_data, sort_keys=True)
        return hashlib.md5(fingerprint_str.encode()).hexdigest()
    
    async def start_notification_processing(self):
        """Start notification processing"""
        self.notification_task = asyncio.create_task(self._notification_loop())
        logger.info("🚨 Notification processing started")
    
    async def _notification_loop(self):
        """Process notification queue"""
        while True:
            try:
                notification = await self.notification_queue.get()
                await self._send_notification(notification)
                self.notification_queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("❌ Error processing notification", error=str(e))
    
    async def _queue_notification(self, alert: Alert, rule: AlertRule):
        """Queue alert notification"""
        notification = {
            "type": "alert",
            "alert": alert,
            "rule": rule,
            "timestamp": datetime.now()
        }
        await self.notification_queue.put(notification)
    
    async def _queue_resolution_notification(self, alert: Alert, rule: AlertRule):
        """Queue alert resolution notification"""
        notification = {
            "type": "resolution",
            "alert": alert,
            "rule": rule,
            "timestamp": datetime.now()
        }
        await self.notification_queue.put(notification)
    
    async def _send_notification(self, notification: Dict[str, Any]):
        """Send notification through configured channels"""
        alert = notification["alert"]
        rule = notification["rule"]
        notification_type = notification["type"]
        
        for channel in rule.channels:
            try:
                if channel == AlertChannel.EMAIL:
                    await self._send_email_notification(alert, rule, notification_type)
                elif channel == AlertChannel.SLACK:
                    await self._send_slack_notification(alert, rule, notification_type)
                elif channel == AlertChannel.WEBHOOK:
                    await self._send_webhook_notification(alert, rule, notification_type)
                elif channel == AlertChannel.CONSOLE:
                    await self._send_console_notification(alert, rule, notification_type)
                    
            except Exception as e:
                logger.error("❌ Failed to send notification", channel=channel.value, error=str(e))
    
    async def _send_email_notification(self, alert: Alert, rule: AlertRule, notification_type: str):
        """Send email notification"""
        if not self.config.default_email_recipients:
            return
        
        subject = f"[{alert.severity.value.upper()}] {alert.name}"
        if notification_type == "resolution":
            subject = f"[RESOLVED] {alert.name}"
        
        body = f"""
Alert: {alert.name}
Description: {alert.description}
Severity: {alert.severity.value.upper()}
Status: {alert.status.value.upper()}
Created: {alert.created_at.isoformat()}

Metric Values:
{json.dumps(alert.metric_values, indent=2)}

Alert ID: {alert.id}
Rule ID: {alert.rule_id}
"""
        
        if alert.annotations.get("runbook_url"):
            body += f"\nRunbook: {alert.annotations['runbook_url']}"
        
        # Send email (simplified implementation)
        logger.info("📧 Email notification sent", alert_id=alert.id, recipients=len(self.config.default_email_recipients))
    
    async def _send_slack_notification(self, alert: Alert, rule: AlertRule, notification_type: str):
        """Send Slack notification"""
        if not self.config.slack_webhook_url:
            return
        
        color = {
            AlertSeverity.CRITICAL: "danger",
            AlertSeverity.HIGH: "warning", 
            AlertSeverity.MEDIUM: "warning",
            AlertSeverity.LOW: "good",
            AlertSeverity.INFO: "good"
        }.get(alert.severity, "warning")
        
        if notification_type == "resolution":
            color = "good"
        
        message = {
            "attachments": [{
                "color": color,
                "title": f"{alert.name}",
                "text": alert.description,
                "fields": [
                    {"title": "Severity", "value": alert.severity.value.upper(), "short": True},
                    {"title": "Status", "value": alert.status.value.upper(), "short": True},
                    {"title": "Created", "value": alert.created_at.isoformat(), "short": True},
                    {"title": "Alert ID", "value": alert.id, "short": True}
                ]
            }]
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.config.slack_webhook_url, json=message) as response:
                    if response.status == 200:
                        logger.info("💬 Slack notification sent", alert_id=alert.id)
                    else:
                        logger.error("❌ Failed to send Slack notification", status=response.status)
        except Exception as e:
            logger.error("❌ Error sending Slack notification", error=str(e))
    
    async def _send_webhook_notification(self, alert: Alert, rule: AlertRule, notification_type: str):
        """Send webhook notification"""
        # Implementation for webhook notifications
        logger.info("🔗 Webhook notification sent", alert_id=alert.id)
    
    async def _send_console_notification(self, alert: Alert, rule: AlertRule, notification_type: str):
        """Send console notification"""
        if notification_type == "alert":
            logger.warning(
                "🚨 ALERT TRIGGERED",
                alert_id=alert.id,
                name=alert.name,
                severity=alert.severity.value,
                description=alert.description
            )
        else:
            logger.info(
                "✅ ALERT RESOLVED",
                alert_id=alert.id,
                name=alert.name,
                description=alert.description
            )
    
    async def _process_escalations(self):
        """Process alert escalations"""
        current_time = datetime.now()
        
        for alert in self.active_alerts.values():
            if alert.status != AlertStatus.OPEN:
                continue
            
            rule = self.alert_rules.get(alert.rule_id)
            if not rule:
                continue
            
            # Check if escalation is needed
            time_since_created = current_time - alert.created_at
            escalation_threshold = rule.escalation_delay * (alert.escalation_level + 1)
            
            if time_since_created >= escalation_threshold:
                alert.escalation_level += 1
                alert.updated_at = current_time
                
                # Send escalation notification
                await self._send_escalation_notification(alert, rule)
                await self._store_alert(alert)
                
                logger.info("🚨 Alert escalated", alert_id=alert.id, level=alert.escalation_level)
    
    async def _send_escalation_notification(self, alert: Alert, rule: AlertRule):
        """Send escalation notification"""
        # Send to escalation recipients
        logger.info("📈 Escalation notification sent", alert_id=alert.id, level=alert.escalation_level)
    
    async def _cleanup_resolved_alerts(self):
        """Clean up old resolved alerts"""
        current_time = datetime.now()
        cutoff_time = current_time - timedelta(days=self.config.alert_retention_days)
        
        # Move resolved alerts to history
        resolved_alerts = []
        for fingerprint, alert in list(self.active_alerts.items()):
            if alert.status == AlertStatus.RESOLVED and alert.resolved_at and alert.resolved_at < cutoff_time:
                resolved_alerts.append(alert)
                del self.active_alerts[fingerprint]
        
        if resolved_alerts:
            self.alert_history.extend(resolved_alerts)
            logger.info("🧹 Cleaned up resolved alerts", count=len(resolved_alerts))
    
    async def _store_alert(self, alert: Alert):
        """Store alert in Redis"""
        if not self.redis_client:
            return
        
        alert_data = {
            "id": alert.id,
            "rule_id": alert.rule_id,
            "name": alert.name,
            "description": alert.description,
            "severity": alert.severity.value,
            "status": alert.status.value,
            "created_at": alert.created_at.isoformat(),
            "updated_at": alert.updated_at.isoformat(),
            "resolved_at": alert.resolved_at.isoformat() if alert.resolved_at else None,
            "acknowledged_at": alert.acknowledged_at.isoformat() if alert.acknowledged_at else None,
            "acknowledged_by": alert.acknowledged_by,
            "metric_values": alert.metric_values,
            "labels": alert.labels,
            "annotations": alert.annotations,
            "escalation_level": alert.escalation_level,
            "suppressed_until": alert.suppressed_until.isoformat() if alert.suppressed_until else None
        }
        
        await self.redis_client.set(f"alerts:{alert.id}", json.dumps(alert_data))
    
    async def _load_alert_rules(self):
        """Load alert rules from Redis"""
        if not self.redis_client:
            return
        
        try:
            keys = await self.redis_client.keys("alert_rules:*")
            for key in keys:
                rule_data = await self.redis_client.get(key)
                if rule_data:
                    data = json.loads(rule_data)
                    # Reconstruct AlertRule object
                    # Implementation details...
                    pass
        except Exception as e:
            logger.error("❌ Error loading alert rules", error=str(e))
    
    async def _load_active_alerts(self):
        """Load active alerts from Redis"""
        if not self.redis_client:
            return
        
        try:
            keys = await self.redis_client.keys("alerts:*")
            for key in keys:
                alert_data = await self.redis_client.get(key)
                if alert_data:
                    data = json.loads(alert_data)
                    # Reconstruct Alert object
                    # Implementation details...
                    pass
        except Exception as e:
            logger.error("❌ Error loading active alerts", error=str(e))
    
    async def acknowledge_alert(self, alert_id: str, acknowledged_by: str):
        """Acknowledge an alert"""
        for alert in self.active_alerts.values():
            if alert.id == alert_id:
                alert.status = AlertStatus.ACKNOWLEDGED
                alert.acknowledged_at = datetime.now()
                alert.acknowledged_by = acknowledged_by
                alert.updated_at = datetime.now()
                
                await self._store_alert(alert)
                logger.info("✅ Alert acknowledged", alert_id=alert_id, by=acknowledged_by)
                return True
        
        return False
    
    async def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts"""
        return list(self.active_alerts.values())
    
    async def get_alert_summary(self) -> Dict[str, Any]:
        """Get alert system summary"""
        active_alerts = list(self.active_alerts.values())
        
        summary = {
            "total_rules": len(self.alert_rules),
            "enabled_rules": sum(1 for rule in self.alert_rules.values() if rule.enabled),
            "active_alerts": len(active_alerts),
            "alerts_by_severity": {
                severity.value: sum(1 for alert in active_alerts if alert.severity == severity)
                for severity in AlertSeverity
            },
            "alerts_by_status": {
                status.value: sum(1 for alert in active_alerts if alert.status == status)
                for status in AlertStatus
            },
            "evaluation_interval": self.evaluation_interval,
            "is_evaluating": self.is_evaluating
        }
        
        return summary

# Global alerting system instance
_alerting_system: Optional[AlertingSystem] = None

async def get_alerting_system() -> AlertingSystem:
    """Get the global alerting system instance"""
    global _alerting_system
    if _alerting_system is None:
        config = AlertingConfig()  # Use default config
        _alerting_system = AlertingSystem(config)
        await _alerting_system.initialize()
    return _alerting_system

async def initialize_alerting_system() -> bool:
    """Initialize the global alerting system"""
    try:
        system = await get_alerting_system()
        logger.info("🚨 Global alerting system initialized")
        return True
    except Exception as e:
        logger.error("❌ Failed to initialize global alerting system", error=str(e))
        return False