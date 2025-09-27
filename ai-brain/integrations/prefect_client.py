"""
OpsConductor AI Brain - Prefect Integration Client

This module provides integration with Prefect for advanced workflow orchestration.
It handles flow creation, registration, deployment, and execution through the
Prefect Flow Registry service.
"""

import logging
import asyncio
import json
import os
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import httpx

logger = logging.getLogger(__name__)


class FlowStatus(Enum):
    """Status of Prefect flows"""
    DRAFT = "draft"
    REGISTERED = "registered"
    DEPLOYED = "deployed"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class PrefectFlowDefinition:
    """Definition of a Prefect flow"""
    name: str
    description: str
    flow_code: str
    parameters: Dict[str, Any]
    tags: List[str]
    timeout_seconds: Optional[int] = 3600
    retries: int = 0
    retry_delay_seconds: int = 60
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API calls"""
        return asdict(self)


@dataclass
class PrefectFlowExecution:
    """Result of a Prefect flow execution"""
    execution_id: str
    flow_name: str
    status: FlowStatus
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    parameters: Dict[str, Any] = None
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    logs: List[str] = None
    
    def __post_init__(self):
        if self.parameters is None:
            self.parameters = {}
        if self.logs is None:
            self.logs = []
    
    @property
    def duration_seconds(self) -> Optional[float]:
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None
    
    @property
    def success(self) -> bool:
        return self.status == FlowStatus.COMPLETED


class PrefectClient:
    """
    Client for interacting with Prefect services
    
    Provides high-level interface for creating, registering, and executing
    Prefect flows through the Flow Registry service.
    """
    
    def __init__(self):
        """Initialize the Prefect client"""
        self.prefect_api_url = os.getenv("PREFECT_API_URL", "http://prefect-server:4200/api")
        self.flow_registry_url = os.getenv("PREFECT_FLOW_REGISTRY_URL", "http://prefect-flow-registry:4201")
        self.integration_enabled = os.getenv("PREFECT_INTEGRATION_ENABLED", "false").lower() == "true"
        
        # HTTP client for API calls
        self.http_client = httpx.AsyncClient(timeout=30.0)
        
        logger.info(f"Prefect client initialized - Integration enabled: {self.integration_enabled}")
        if self.integration_enabled:
            logger.info(f"Prefect API URL: {self.prefect_api_url}")
            logger.info(f"Flow Registry URL: {self.flow_registry_url}")
    
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.http_client.aclose()
    
    async def is_available(self) -> bool:
        """Check if Prefect services are available"""
        if not self.integration_enabled:
            return False
        
        try:
            # Check Flow Registry health
            response = await self.http_client.get(f"{self.flow_registry_url}/health")
            if response.status_code != 200:
                return False
            
            # Check Prefect Server health
            response = await self.http_client.get(f"{self.prefect_api_url}/health")
            return response.status_code == 200
            
        except Exception as e:
            logger.warning(f"Prefect services not available: {str(e)}")
            return False
    
    async def create_flow(self, flow_definition: PrefectFlowDefinition) -> Dict[str, Any]:
        """
        Create a new Prefect flow
        
        Args:
            flow_definition: Definition of the flow to create
            
        Returns:
            Dict containing flow creation result
        """
        if not self.integration_enabled:
            raise RuntimeError("Prefect integration is not enabled")
        
        try:
            logger.info(f"Creating Prefect flow: {flow_definition.name}")
            
            response = await self.http_client.post(
                f"{self.flow_registry_url}/api/v1/flows",
                json=flow_definition.to_dict()
            )
            
            if response.status_code == 201:
                result = response.json()
                logger.info(f"Flow created successfully: {result.get('flow_id')}")
                return result
            else:
                error_msg = f"Failed to create flow: {response.status_code} - {response.text}"
                logger.error(error_msg)
                raise RuntimeError(error_msg)
                
        except Exception as e:
            logger.error(f"Error creating flow: {str(e)}")
            raise
    
    async def register_flow(self, flow_id: str) -> Dict[str, Any]:
        """
        Register a flow with Prefect server
        
        Args:
            flow_id: ID of the flow to register
            
        Returns:
            Dict containing registration result
        """
        if not self.integration_enabled:
            raise RuntimeError("Prefect integration is not enabled")
        
        try:
            logger.info(f"Registering flow: {flow_id}")
            
            response = await self.http_client.post(
                f"{self.flow_registry_url}/api/v1/flows/{flow_id}/register"
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Flow registered successfully: {result.get('deployment_id')}")
                return result
            else:
                error_msg = f"Failed to register flow: {response.status_code} - {response.text}"
                logger.error(error_msg)
                raise RuntimeError(error_msg)
                
        except Exception as e:
            logger.error(f"Error registering flow: {str(e)}")
            raise
    
    async def execute_flow(
        self,
        flow_id: str,
        parameters: Dict[str, Any] = None,
        wait_for_completion: bool = False,
        timeout_seconds: int = 3600
    ) -> PrefectFlowExecution:
        """
        Execute a Prefect flow
        
        Args:
            flow_id: ID of the flow to execute
            parameters: Parameters to pass to the flow
            wait_for_completion: Whether to wait for flow completion
            timeout_seconds: Timeout for waiting (if wait_for_completion=True)
            
        Returns:
            PrefectFlowExecution with execution details
        """
        if not self.integration_enabled:
            raise RuntimeError("Prefect integration is not enabled")
        
        if parameters is None:
            parameters = {}
        
        try:
            logger.info(f"Executing flow: {flow_id}")
            
            # Start flow execution
            response = await self.http_client.post(
                f"{self.flow_registry_url}/api/v1/flows/{flow_id}/execute",
                json={"parameters": parameters}
            )
            
            if response.status_code != 200:
                error_msg = f"Failed to start flow execution: {response.status_code} - {response.text}"
                logger.error(error_msg)
                raise RuntimeError(error_msg)
            
            execution_data = response.json()
            execution_id = execution_data.get("execution_id")
            
            # Create execution result
            execution = PrefectFlowExecution(
                execution_id=execution_id,
                flow_name=execution_data.get("flow_name", "unknown"),
                status=FlowStatus(execution_data.get("status", "running")),
                start_time=datetime.now(),
                parameters=parameters
            )
            
            logger.info(f"Flow execution started: {execution_id}")
            
            # Wait for completion if requested
            if wait_for_completion:
                execution = await self._wait_for_completion(execution, timeout_seconds)
            
            return execution
            
        except Exception as e:
            logger.error(f"Error executing flow: {str(e)}")
            raise
    
    async def get_flow_status(self, execution_id: str) -> PrefectFlowExecution:
        """
        Get the status of a flow execution
        
        Args:
            execution_id: ID of the execution to check
            
        Returns:
            PrefectFlowExecution with current status
        """
        if not self.integration_enabled:
            raise RuntimeError("Prefect integration is not enabled")
        
        try:
            response = await self.http_client.get(
                f"{self.flow_registry_url}/api/v1/executions/{execution_id}"
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Parse timestamps
                start_time = None
                end_time = None
                if data.get("start_time"):
                    start_time = datetime.fromisoformat(data["start_time"].replace("Z", "+00:00"))
                if data.get("end_time"):
                    end_time = datetime.fromisoformat(data["end_time"].replace("Z", "+00:00"))
                
                return PrefectFlowExecution(
                    execution_id=execution_id,
                    flow_name=data.get("flow_name", "unknown"),
                    status=FlowStatus(data.get("status", "running")),
                    start_time=start_time,
                    end_time=end_time,
                    parameters=data.get("parameters", {}),
                    result=data.get("result"),
                    error_message=data.get("error_message"),
                    logs=data.get("logs", [])
                )
            else:
                error_msg = f"Failed to get execution status: {response.status_code} - {response.text}"
                logger.error(error_msg)
                raise RuntimeError(error_msg)
                
        except Exception as e:
            logger.error(f"Error getting flow status: {str(e)}")
            raise
    
    async def list_flows(self) -> List[Dict[str, Any]]:
        """
        List all available flows
        
        Returns:
            List of flow information dictionaries
        """
        if not self.integration_enabled:
            return []
        
        try:
            response = await self.http_client.get(f"{self.flow_registry_url}/api/v1/flows")
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to list flows: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"Error listing flows: {str(e)}")
            return []
    
    async def cancel_execution(self, execution_id: str) -> bool:
        """
        Cancel a running flow execution
        
        Args:
            execution_id: ID of the execution to cancel
            
        Returns:
            True if cancellation was successful
        """
        if not self.integration_enabled:
            return False
        
        try:
            response = await self.http_client.post(
                f"{self.flow_registry_url}/api/v1/executions/{execution_id}/cancel"
            )
            
            if response.status_code == 200:
                logger.info(f"Flow execution cancelled: {execution_id}")
                return True
            else:
                logger.error(f"Failed to cancel execution: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error cancelling execution: {str(e)}")
            return False
    
    async def _wait_for_completion(
        self,
        execution: PrefectFlowExecution,
        timeout_seconds: int
    ) -> PrefectFlowExecution:
        """Wait for flow execution to complete"""
        start_time = datetime.now()
        timeout_time = start_time + timedelta(seconds=timeout_seconds)
        
        while datetime.now() < timeout_time:
            try:
                # Get current status
                current_execution = await self.get_flow_status(execution.execution_id)
                
                # Check if completed
                if current_execution.status in [FlowStatus.COMPLETED, FlowStatus.FAILED, FlowStatus.CANCELLED]:
                    logger.info(f"Flow execution finished: {current_execution.status.value}")
                    return current_execution
                
                # Wait before next check
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.warning(f"Error checking flow status: {str(e)}")
                await asyncio.sleep(5)
        
        # Timeout reached
        logger.warning(f"Flow execution timeout reached: {execution.execution_id}")
        execution.status = FlowStatus.FAILED
        execution.error_message = f"Execution timeout after {timeout_seconds} seconds"
        execution.end_time = datetime.now()
        
        return execution


# Convenience function for creating client instances
async def create_prefect_client() -> PrefectClient:
    """Create and return a Prefect client instance"""
    return PrefectClient()