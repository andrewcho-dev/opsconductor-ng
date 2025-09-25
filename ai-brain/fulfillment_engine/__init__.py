"""
Fulfillment Engine - Turning Intent into Action

The Fulfillment Engine bridges the gap between understanding what the user wants
(Intent Brain) and actually making it happen (Automation Service).

Key Components:
- FulfillmentEngine: Main orchestrator
- WorkflowPlanner: Converts intents to executable workflows  
- ExecutionCoordinator: Manages workflow execution
- StatusTracker: Tracks progress and provides feedback
"""

from .fulfillment_engine import FulfillmentEngine
from .workflow_planner import WorkflowPlanner
from .execution_coordinator import ExecutionCoordinator
from .status_tracker import StatusTracker

__all__ = [
    'FulfillmentEngine',
    'WorkflowPlanner', 
    'ExecutionCoordinator',
    'StatusTracker'
]