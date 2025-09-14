#!/usr/bin/env python3
"""
Automation Service Client for AI Service
Handles job submission and execution monitoring with the automation service
"""

import httpx
import asyncio
import structlog
from typing import Dict, Any, Optional, List
from datetime import datetime
import json

# Configure structured logging
logger = structlog.get_logger(__name__)

class AutomationServiceError(Exception):
    """Raised when automation service operations fail"""
    pass

class AutomationServiceClient:
    """
    Client for interacting with the OpsConductor Automation Service
    Handles job submission, execution monitoring, and result retrieval
    """
    
    def __init__(self, automation_service_url: str = "http://automation-service:3003"):
        self.base_url = automation_service_url.rstrip('/')
        self.timeout = 30.0
        self.max_retries = 3
        
        logger.info("Automation Service Client initialized", 
                   base_url=self.base_url)

    async def health_check(self) -> bool:
        """Check if automation service is healthy"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/health")
                return response.status_code == 200
        except Exception as e:
            logger.warning("Automation service health check failed", error=str(e))
            return False

    async def submit_ai_workflow(self, workflow: Dict[str, Any], 
                                job_name: str = None) -> Dict[str, Any]:
        """
        Submit an AI-generated workflow to the automation service
        
        Args:
            workflow: AI-generated workflow definition
            job_name: Optional job name (will be generated if not provided)
            
        Returns:
            Dict with job creation results and execution info
        """
        try:
            # Generate job name if not provided
            if not job_name:
                job_name = workflow.get('name', f"AI Job - {datetime.utcnow().strftime('%Y%m%d-%H%M%S')}")
            
            logger.info("Submitting AI workflow to automation service",
                       job_name=job_name,
                       workflow_id=workflow.get('id'),
                       step_count=len(workflow.get('steps', [])))
            
            # Prepare job data
            job_data = {
                'name': job_name,
                'description': workflow.get('description', 'AI-generated automation job'),
                'workflow_definition': workflow,
                'job_type': 'ai_generated',
                'is_enabled': True,
                'tags': ['ai-generated', 'automated'],
                'metadata': {
                    'ai_generated': True,
                    'source_request': workflow.get('source_request'),
                    'confidence': workflow.get('confidence'),
                    'created_by_ai': True,
                    'submission_time': datetime.utcnow().isoformat()
                }
            }
            
            # Submit job to automation service
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/jobs",
                    json=job_data
                )
                
                if response.status_code != 200:
                    raise AutomationServiceError(
                        f"Failed to create job: {response.status_code} - {response.text}"
                    )
                
                job_result = response.json()
                # Handle nested response format from automation service
                if 'data' in job_result:
                    job_data_response = job_result['data']
                    job_id = job_data_response['id']
                else:
                    job_id = job_result['id']
                
                logger.info("Job created successfully", 
                           job_id=job_id, 
                           job_name=job_name)
                
                # Start job execution
                execution_result = await self.execute_job(job_id)
                
                return {
                    'success': True,
                    'job_id': job_id,
                    'job_name': job_name,
                    'execution_id': execution_result.get('execution_id'),
                    'task_id': execution_result.get('task_id'),
                    'message': f"AI workflow submitted and started execution",
                    'job_details': job_result,
                    'execution_details': execution_result
                }
                
        except Exception as e:
            logger.error("Failed to submit AI workflow", 
                        error=str(e),
                        job_name=job_name)
            
            return {
                'success': False,
                'error': f"Failed to submit workflow: {str(e)}",
                'job_name': job_name
            }

    async def execute_job(self, job_id: int) -> Dict[str, Any]:
        """
        Execute a job in the automation service
        
        Args:
            job_id: ID of the job to execute
            
        Returns:
            Dict with execution results
        """
        try:
            logger.info("Starting job execution", job_id=job_id)
            
            execution_data = {
                'job_id': job_id,
                'trigger_type': 'ai_triggered',
                'input_data': {
                    'triggered_by': 'ai_service',
                    'trigger_time': datetime.utcnow().isoformat()
                }
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/executions",
                    json=execution_data
                )
                
                if response.status_code != 200:
                    raise AutomationServiceError(
                        f"Failed to start execution: {response.status_code} - {response.text}"
                    )
                
                result = response.json()
                
                logger.info("Job execution started", 
                           job_id=job_id,
                           execution_id=result.get('execution_id'),
                           task_id=result.get('task_id'))
                
                return result
                
        except Exception as e:
            logger.error("Failed to execute job", 
                        job_id=job_id, 
                        error=str(e))
            raise AutomationServiceError(f"Failed to execute job {job_id}: {str(e)}")

    async def get_execution_status(self, execution_id: str) -> Dict[str, Any]:
        """
        Get the status of a job execution
        
        Args:
            execution_id: Execution ID to check
            
        Returns:
            Dict with execution status and details
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/executions/{execution_id}"
                )
                
                if response.status_code == 404:
                    return {
                        'success': False,
                        'error': 'Execution not found',
                        'execution_id': execution_id
                    }
                elif response.status_code != 200:
                    raise AutomationServiceError(
                        f"Failed to get execution status: {response.status_code} - {response.text}"
                    )
                
                return response.json()
                
        except Exception as e:
            logger.error("Failed to get execution status", 
                        execution_id=execution_id, 
                        error=str(e))
            return {
                'success': False,
                'error': f"Failed to get status: {str(e)}",
                'execution_id': execution_id
            }

    async def get_execution_steps(self, execution_id: str) -> List[Dict[str, Any]]:
        """
        Get the step execution details for a job execution
        
        Args:
            execution_id: Execution ID
            
        Returns:
            List of step execution details
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/executions/{execution_id}/steps"
                )
                
                if response.status_code != 200:
                    logger.warning("Failed to get execution steps", 
                                  execution_id=execution_id,
                                  status_code=response.status_code)
                    return []
                
                result = response.json()
                return result.get('steps', [])
                
        except Exception as e:
            logger.error("Failed to get execution steps", 
                        execution_id=execution_id, 
                        error=str(e))
            return []

    async def wait_for_completion(self, execution_id: str, 
                                 timeout: int = 300, 
                                 poll_interval: int = 5) -> Dict[str, Any]:
        """
        Wait for job execution to complete
        
        Args:
            execution_id: Execution ID to monitor
            timeout: Maximum time to wait in seconds
            poll_interval: How often to check status in seconds
            
        Returns:
            Dict with final execution status
        """
        start_time = datetime.utcnow()
        timeout_time = start_time + timedelta(seconds=timeout)
        
        logger.info("Waiting for execution completion", 
                   execution_id=execution_id,
                   timeout=timeout)
        
        while datetime.utcnow() < timeout_time:
            status = await self.get_execution_status(execution_id)
            
            if not status.get('success', True):
                return status
            
            execution_status = status.get('status', 'unknown')
            
            if execution_status in ['completed', 'failed', 'cancelled']:
                logger.info("Execution completed", 
                           execution_id=execution_id,
                           final_status=execution_status,
                           duration=(datetime.utcnow() - start_time).total_seconds())
                
                # Get step details for completed execution
                steps = await self.get_execution_steps(execution_id)
                status['steps'] = steps
                
                return status
            
            # Wait before next poll
            await asyncio.sleep(poll_interval)
        
        # Timeout reached
        logger.warning("Execution monitoring timeout", 
                      execution_id=execution_id,
                      timeout=timeout)
        
        return {
            'success': False,
            'error': f"Execution monitoring timeout after {timeout} seconds",
            'execution_id': execution_id,
            'timeout': True
        }

    async def list_ai_jobs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        List AI-generated jobs
        
        Args:
            limit: Maximum number of jobs to return
            
        Returns:
            List of AI-generated jobs
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/jobs",
                    params={'job_type': 'ai_generated', 'limit': limit}
                )
                
                if response.status_code != 200:
                    logger.warning("Failed to list AI jobs", 
                                  status_code=response.status_code)
                    return []
                
                result = response.json()
                return result.get('jobs', [])
                
        except Exception as e:
            logger.error("Failed to list AI jobs", error=str(e))
            return []

    def get_client_info(self) -> Dict[str, Any]:
        """Get client information"""
        return {
            'name': 'Automation Service Client',
            'version': '1.0.0',
            'description': 'Client for AI Service to Automation Service integration',
            'base_url': self.base_url,
            'capabilities': [
                'AI workflow submission',
                'Job execution management',
                'Execution status monitoring',
                'Step-by-step execution tracking',
                'AI job listing'
            ],
            'timeouts': {
                'request_timeout': self.timeout,
                'max_retries': self.max_retries
            }
        }


# Example usage
if __name__ == "__main__":
    async def demo():
        client = AutomationServiceClient()
        
        print("Automation Service Client Demo")
        print("=" * 50)
        
        # Show client info
        info = client.get_client_info()
        print(f"Client: {info['name']} v{info['version']}")
        print(f"Base URL: {info['base_url']}")
        print(f"Capabilities: {', '.join(info['capabilities'])}")
        
        # Test health check
        healthy = await client.health_check()
        print(f"Automation Service Health: {'✓ Healthy' if healthy else '✗ Unhealthy'}")
        
        print("\nClient ready for AI service integration!")
    
    asyncio.run(demo())