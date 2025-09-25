"""
Status Tracker - Real-time Status and Progress Tracking

Provides real-time tracking of fulfillment progress, status updates,
and historical execution data for analysis and monitoring.
"""

import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import json

logger = logging.getLogger(__name__)


class StatusLevel(Enum):
    """Status level indicators"""
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class StatusUpdate:
    """Individual status update"""
    timestamp: datetime
    level: StatusLevel
    message: str
    component: str  # fulfillment_engine, workflow_planner, execution_coordinator
    details: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format"""
        result = asdict(self)
        result['timestamp'] = self.timestamp.isoformat()
        result['level'] = self.level.value
        return result


@dataclass
class ExecutionMetrics:
    """Metrics for execution performance"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    cancelled_requests: int = 0
    average_execution_time: float = 0.0
    total_steps_executed: int = 0
    average_steps_per_workflow: float = 0.0
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage"""
        if self.total_requests == 0:
            return 0.0
        return (self.successful_requests / self.total_requests) * 100
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format"""
        return {
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "cancelled_requests": self.cancelled_requests,
            "success_rate_percentage": round(self.success_rate, 2),
            "average_execution_time_seconds": round(self.average_execution_time, 2),
            "total_steps_executed": self.total_steps_executed,
            "average_steps_per_workflow": round(self.average_steps_per_workflow, 2)
        }


class StatusTracker:
    """
    Status Tracker - Real-time status and progress tracking
    
    Tracks the status of fulfillment requests, workflow executions,
    and provides metrics and historical data for monitoring.
    """
    
    def __init__(self, max_history_hours: int = 24):
        """Initialize the Status Tracker"""
        self.max_history_hours = max_history_hours
        
        # Status updates history
        self.status_history: List[StatusUpdate] = []
        
        # Execution metrics
        self.metrics = ExecutionMetrics()
        
        # Active status tracking
        self.active_statuses: Dict[str, List[StatusUpdate]] = {}
        
        logger.info("Status Tracker initialized")
    
    def add_status_update(self, request_id: str, level: StatusLevel, message: str, 
                         component: str, details: Optional[Dict[str, Any]] = None):
        """Add a status update for a request"""
        update = StatusUpdate(
            timestamp=datetime.now(),
            level=level,
            message=message,
            component=component,
            details=details
        )
        
        # Add to global history
        self.status_history.append(update)
        
        # Add to request-specific tracking
        if request_id not in self.active_statuses:
            self.active_statuses[request_id] = []
        self.active_statuses[request_id].append(update)
        
        # Log the update
        log_level = {
            StatusLevel.INFO: logging.INFO,
            StatusLevel.SUCCESS: logging.INFO,
            StatusLevel.WARNING: logging.WARNING,
            StatusLevel.ERROR: logging.ERROR
        }.get(level, logging.INFO)
        
        logger.log(log_level, f"[{request_id}] {component}: {message}")
        
        # Clean up old history
        self._cleanup_old_history()
    
    def get_request_status(self, request_id: str) -> List[StatusUpdate]:
        """Get all status updates for a specific request"""
        return self.active_statuses.get(request_id, [])
    
    def get_latest_status(self, request_id: str) -> Optional[StatusUpdate]:
        """Get the latest status update for a request"""
        updates = self.get_request_status(request_id)
        return updates[-1] if updates else None
    
    def get_recent_history(self, hours: int = 1) -> List[StatusUpdate]:
        """Get recent status history"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [
            update for update in self.status_history
            if update.timestamp >= cutoff_time
        ]
    
    def get_status_by_level(self, level: StatusLevel, hours: int = 1) -> List[StatusUpdate]:
        """Get status updates by level within time period"""
        recent_updates = self.get_recent_history(hours)
        return [update for update in recent_updates if update.level == level]
    
    def get_component_status(self, component: str, hours: int = 1) -> List[StatusUpdate]:
        """Get status updates for a specific component"""
        recent_updates = self.get_recent_history(hours)
        return [update for update in recent_updates if update.component == component]
    
    def update_metrics(self, request_id: str, success: bool, execution_time: float, 
                      steps_executed: int, cancelled: bool = False):
        """Update execution metrics"""
        self.metrics.total_requests += 1
        
        if cancelled:
            self.metrics.cancelled_requests += 1
        elif success:
            self.metrics.successful_requests += 1
        else:
            self.metrics.failed_requests += 1
        
        # Update averages
        total_completed = self.metrics.successful_requests + self.metrics.failed_requests
        if total_completed > 0:
            # Update average execution time
            current_total_time = self.metrics.average_execution_time * (total_completed - 1)
            self.metrics.average_execution_time = (current_total_time + execution_time) / total_completed
        
        # Update step metrics
        self.metrics.total_steps_executed += steps_executed
        if self.metrics.total_requests > 0:
            self.metrics.average_steps_per_workflow = self.metrics.total_steps_executed / self.metrics.total_requests
        
        # Add metrics update to status
        self.add_status_update(
            request_id=request_id,
            level=StatusLevel.INFO,
            message=f"Metrics updated: Success rate {self.metrics.success_rate:.1f}%",
            component="status_tracker",
            details=self.metrics.to_dict()
        )
    
    def get_metrics(self) -> ExecutionMetrics:
        """Get current execution metrics"""
        return self.metrics
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get overall health status"""
        recent_errors = len(self.get_status_by_level(StatusLevel.ERROR, hours=1))
        recent_warnings = len(self.get_status_by_level(StatusLevel.WARNING, hours=1))
        recent_successes = len(self.get_status_by_level(StatusLevel.SUCCESS, hours=1))
        
        # Determine health status
        if recent_errors > 5:
            health = "unhealthy"
        elif recent_errors > 2 or recent_warnings > 10:
            health = "degraded"
        else:
            health = "healthy"
        
        return {
            "status": health,
            "recent_errors": recent_errors,
            "recent_warnings": recent_warnings,
            "recent_successes": recent_successes,
            "active_requests": len(self.active_statuses),
            "total_status_updates": len(self.status_history),
            "metrics": self.metrics.to_dict()
        }
    
    def get_active_requests_summary(self) -> Dict[str, Any]:
        """Get summary of active requests"""
        active_requests = []
        
        for request_id, updates in self.active_statuses.items():
            if updates:
                latest = updates[-1]
                active_requests.append({
                    "request_id": request_id,
                    "latest_status": latest.to_dict(),
                    "total_updates": len(updates),
                    "first_update": updates[0].timestamp.isoformat(),
                    "last_update": latest.timestamp.isoformat()
                })
        
        return {
            "total_active_requests": len(active_requests),
            "requests": active_requests
        }
    
    def export_status_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Export status history as JSON-serializable data"""
        recent_history = self.get_recent_history(hours)
        return [update.to_dict() for update in recent_history]
    
    def clear_request_status(self, request_id: str):
        """Clear status tracking for a completed request"""
        if request_id in self.active_statuses:
            # Keep the updates in global history but remove from active tracking
            del self.active_statuses[request_id]
            
            self.add_status_update(
                request_id=request_id,
                level=StatusLevel.INFO,
                message="Request status cleared from active tracking",
                component="status_tracker"
            )
    
    def _cleanup_old_history(self):
        """Clean up old status history to prevent memory bloat"""
        cutoff_time = datetime.now() - timedelta(hours=self.max_history_hours)
        
        # Remove old updates from global history
        old_count = len(self.status_history)
        self.status_history = [
            update for update in self.status_history
            if update.timestamp >= cutoff_time
        ]
        
        # Remove old updates from active statuses
        for request_id in list(self.active_statuses.keys()):
            old_updates = self.active_statuses[request_id]
            new_updates = [
                update for update in old_updates
                if update.timestamp >= cutoff_time
            ]
            
            if new_updates:
                self.active_statuses[request_id] = new_updates
            else:
                # No recent updates, remove from active tracking
                del self.active_statuses[request_id]
        
        removed_count = old_count - len(self.status_history)
        if removed_count > 0:
            logger.debug(f"Cleaned up {removed_count} old status updates")
    
    def get_performance_insights(self) -> Dict[str, Any]:
        """Get performance insights and recommendations"""
        insights = {
            "performance_summary": self.metrics.to_dict(),
            "recommendations": [],
            "trends": {}
        }
        
        # Analyze success rate
        if self.metrics.success_rate < 80:
            insights["recommendations"].append({
                "type": "success_rate",
                "message": f"Success rate is {self.metrics.success_rate:.1f}%. Consider reviewing failed workflows.",
                "priority": "high"
            })
        elif self.metrics.success_rate < 95:
            insights["recommendations"].append({
                "type": "success_rate", 
                "message": f"Success rate is {self.metrics.success_rate:.1f}%. Room for improvement.",
                "priority": "medium"
            })
        
        # Analyze execution time
        if self.metrics.average_execution_time > 300:  # 5 minutes
            insights["recommendations"].append({
                "type": "execution_time",
                "message": f"Average execution time is {self.metrics.average_execution_time:.1f}s. Consider optimizing workflows.",
                "priority": "medium"
            })
        
        # Analyze error trends
        recent_errors = self.get_status_by_level(StatusLevel.ERROR, hours=24)
        if len(recent_errors) > 10:
            insights["recommendations"].append({
                "type": "error_rate",
                "message": f"{len(recent_errors)} errors in the last 24 hours. Investigation recommended.",
                "priority": "high"
            })
        
        return insights