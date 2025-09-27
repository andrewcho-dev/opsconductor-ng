"""
Prefect Flow Engine - Manages Prefect workflow creation and execution.
Provides integration between AI Brain service and Prefect server.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timedelta
import json

from prefect import flow, task, get_run_logger
from prefect.client.orchestration import PrefectClient as PrefectOrchestrationClient
from prefect.deployments import Deployment
from prefect.server.schemas.core import FlowRun
from prefect.server.schemas.states import StateType

logger = logging.getLogger(__name__)

class PrefectFlowEngine:
    """
    Manages Prefect workflow creation, deployment, and execution.
    Provides high-level interface for AI Brain service to interact with Prefect.
    """
    
    def __init__(self):
        """Initialize the Prefect Flow Engine."""
        self.client: Optional[PrefectOrchestrationClient] = None
        self.registered_flows: Dict[str, Callable] = {}
        self.active_deployments: Dict[str, str] = {}
        self.initialized = False
        
        logger.info("Prefect Flow Engine initialized")
    
    async def initialize(self) -> bool:
        """
        Initialize connection to Prefect server and register base flows.
        
        Returns:
            bool: True if initialization successful
        """
        try:
            # Initialize Prefect client
            self.client = PrefectOrchestrationClient()
            
            # Test connection
            server_info = await self.client.hello()
            logger.info(f"Connected to Prefect server: {server_info}")
            
            # Register base flows
            await self._register_base_flows()
            
            self.initialized = True
            logger.info("Prefect Flow Engine initialization complete")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Prefect Flow Engine: {e}")
            return False
    
    async def create_dynamic_flow(self, flow_name: str, tasks: List[Dict[str, Any]], 
                                 parameters: Optional[Dict[str, Any]] = None) -> str:
        """
        Create a dynamic Prefect flow from task definitions.
        
        Args:
            flow_name: Name for the flow
            tasks: List of task definitions
            parameters: Optional flow parameters
            
        Returns:
            str: Flow ID
        """
        try:
            # Create dynamic flow function
            @flow(name=flow_name)
            async def dynamic_flow(**kwargs):
                flow_logger = get_run_logger()
                flow_logger.info(f"Starting dynamic flow: {flow_name}")
                
                results = {}
                for task_def in tasks:
                    task_name = task_def.get("name", "unnamed_task")
                    task_type = task_def.get("type", "generic")
                    task_params = task_def.get("parameters", {})
                    
                    # Execute task based on type
                    result = await self._execute_dynamic_task(
                        task_name, task_type, task_params, results
                    )
                    results[task_name] = result
                    
                    flow_logger.info(f"Completed task: {task_name}")
                
                return results
            
            # Register the flow
            flow_id = f"dynamic_{flow_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.registered_flows[flow_id] = dynamic_flow
            
            logger.info(f"Created dynamic flow: {flow_id}")
            return flow_id
            
        except Exception as e:
            logger.error(f"Failed to create dynamic flow: {e}")
            raise
    
    async def deploy_flow(self, flow_id: str, deployment_name: Optional[str] = None) -> str:
        """
        Deploy a registered flow to Prefect server.
        
        Args:
            flow_id: ID of the flow to deploy
            deployment_name: Optional deployment name
            
        Returns:
            str: Deployment ID
        """
        try:
            if flow_id not in self.registered_flows:
                raise ValueError(f"Flow {flow_id} not found in registered flows")
            
            flow_func = self.registered_flows[flow_id]
            deployment_name = deployment_name or f"{flow_id}_deployment"
            
            # Create deployment
            deployment = Deployment.build_from_flow(
                flow=flow_func,
                name=deployment_name,
                work_queue_name="default"
            )
            
            # Deploy to server
            deployment_id = await deployment.apply()
            self.active_deployments[flow_id] = deployment_id
            
            logger.info(f"Deployed flow {flow_id} as deployment {deployment_id}")
            return deployment_id
            
        except Exception as e:
            logger.error(f"Failed to deploy flow {flow_id}: {e}")
            raise
    
    async def execute_flow(self, flow_id: str, parameters: Optional[Dict[str, Any]] = None) -> str:
        """
        Execute a deployed flow.
        
        Args:
            flow_id: ID of the flow to execute
            parameters: Optional flow parameters
            
        Returns:
            str: Flow run ID
        """
        try:
            if flow_id not in self.active_deployments:
                # Try to deploy the flow first
                await self.deploy_flow(flow_id)
            
            deployment_id = self.active_deployments[flow_id]
            
            # Create flow run
            flow_run = await self.client.create_flow_run_from_deployment(
                deployment_id=deployment_id,
                parameters=parameters or {}
            )
            
            logger.info(f"Started flow run {flow_run.id} for flow {flow_id}")
            return str(flow_run.id)
            
        except Exception as e:
            logger.error(f"Failed to execute flow {flow_id}: {e}")
            raise
    
    async def get_flow_run_status(self, flow_run_id: str) -> Dict[str, Any]:
        """
        Get the status of a flow run.
        
        Args:
            flow_run_id: ID of the flow run
            
        Returns:
            Dict containing flow run status information
        """
        try:
            flow_run = await self.client.read_flow_run(flow_run_id)
            
            return {
                "id": str(flow_run.id),
                "name": flow_run.name,
                "state": flow_run.state.type.value if flow_run.state else "unknown",
                "start_time": flow_run.start_time.isoformat() if flow_run.start_time else None,
                "end_time": flow_run.end_time.isoformat() if flow_run.end_time else None,
                "total_run_time": str(flow_run.total_run_time) if flow_run.total_run_time else None,
                "parameters": flow_run.parameters
            }
            
        except Exception as e:
            logger.error(f"Failed to get flow run status for {flow_run_id}: {e}")
            raise
    
    async def _register_base_flows(self):
        """Register base flows that are commonly used."""
        
        @flow(name="ai_brain_health_check")
        async def health_check_flow():
            """Basic health check flow."""
            flow_logger = get_run_logger()
            flow_logger.info("AI Brain health check flow executed")
            return {"status": "healthy", "timestamp": datetime.now().isoformat()}
        
        @flow(name="ai_brain_workflow_template")
        async def workflow_template_flow(workflow_type: str, parameters: Dict[str, Any]):
            """Template flow for AI Brain workflows."""
            flow_logger = get_run_logger()
            flow_logger.info(f"Executing workflow template: {workflow_type}")
            
            # Placeholder for workflow execution logic
            result = {
                "workflow_type": workflow_type,
                "parameters": parameters,
                "status": "completed",
                "timestamp": datetime.now().isoformat()
            }
            
            return result
        
        # Register base flows
        self.registered_flows["health_check"] = health_check_flow
        self.registered_flows["workflow_template"] = workflow_template_flow
        
        logger.info("Registered base flows")
    
    async def _execute_dynamic_task(self, task_name: str, task_type: str, 
                                   parameters: Dict[str, Any], 
                                   previous_results: Dict[str, Any]) -> Any:
        """
        Execute a dynamic task based on its type.
        
        Args:
            task_name: Name of the task
            task_type: Type of the task
            parameters: Task parameters
            previous_results: Results from previous tasks
            
        Returns:
            Task execution result
        """
        try:
            if task_type == "http_request":
                return await self._execute_http_task(task_name, parameters)
            elif task_type == "data_processing":
                return await self._execute_data_processing_task(task_name, parameters, previous_results)
            elif task_type == "notification":
                return await self._execute_notification_task(task_name, parameters)
            else:
                # Generic task execution
                return await self._execute_generic_task(task_name, parameters)
                
        except Exception as e:
            logger.error(f"Failed to execute task {task_name}: {e}")
            raise
    
    async def _execute_http_task(self, task_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute HTTP request task."""
        # Placeholder implementation
        return {"task": task_name, "type": "http_request", "status": "completed"}
    
    async def _execute_data_processing_task(self, task_name: str, parameters: Dict[str, Any], 
                                          previous_results: Dict[str, Any]) -> Dict[str, Any]:
        """Execute data processing task."""
        # Placeholder implementation
        return {"task": task_name, "type": "data_processing", "status": "completed"}
    
    async def _execute_notification_task(self, task_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute notification task."""
        # Placeholder implementation
        return {"task": task_name, "type": "notification", "status": "completed"}
    
    async def _execute_generic_task(self, task_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute generic task."""
        # Placeholder implementation
        return {"task": task_name, "type": "generic", "status": "completed"}
    
    async def cleanup(self):
        """Cleanup resources and close connections."""
        try:
            if self.client:
                await self.client.close()
            
            self.registered_flows.clear()
            self.active_deployments.clear()
            self.initialized = False
            
            logger.info("Prefect Flow Engine cleanup complete")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    def __del__(self):
        """Destructor to ensure cleanup."""
        if self.initialized:
            try:
                asyncio.create_task(self.cleanup())
            except Exception:
                pass