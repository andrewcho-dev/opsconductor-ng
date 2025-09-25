#!/usr/bin/env python3
"""
Automation Service Client for AI Service
Handles job submission and execution monitoring with the automation service
"""

import httpx
import asyncio
import structlog
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
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
                
                # Extract execution data from nested response
                execution_data = result.get('data', {})
                execution_id = execution_data.get('execution_id')
                
                logger.info("Job execution started", 
                           job_id=job_id,
                           execution_id=execution_id,
                           task_id=result.get('task_id'))
                
                # Return the execution data with execution_id at top level for compatibility
                return {
                    'execution_id': execution_id,
                    'task_id': result.get('task_id'),
                    'success': result.get('success', True),
                    'message': result.get('message', ''),
                    'data': execution_data
                }
                
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
                    f"{self.base_url}/executions",
                    params={'execution_id': execution_id}
                )
                
                if response.status_code != 200:
                    raise AutomationServiceError(
                        f"Failed to get execution status: {response.status_code} - {response.text}"
                    )
                
                result = response.json()
                executions = result.get('executions', [])
                
                if not executions:
                    return {
                        'success': False,
                        'error': 'Execution not found',
                        'execution_id': execution_id
                    }
                
                # Return the first (and should be only) execution
                execution = executions[0]
                return {
                    'success': True,
                    'execution_id': execution_id,
                    'status': execution.get('status'),
                    'job_id': execution.get('job_id'),
                    'job_name': execution.get('job_name'),
                    'error_message': execution.get('error_message'),
                    'started_at': execution.get('started_at'),
                    'completed_at': execution.get('completed_at'),
                    'output_data': execution.get('output_data', {}),
                    'data': execution  # Include full execution data
                }
                
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
            execution_id: Execution ID (UUID)
            
        Returns:
            List of step execution details
        """
        try:
            # First get the execution status to find the integer ID
            execution_status = await self.get_execution_status(execution_id)
            if not execution_status.get('success'):
                logger.warning("Could not get execution status for steps", 
                              execution_id=execution_id)
                return []
            
            # Extract the integer ID from the execution data
            execution_data = execution_status.get('data', {})
            integer_id = execution_data.get('id')
            
            if not integer_id:
                logger.warning("No integer ID found in execution data", 
                              execution_id=execution_id)
                return []
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/executions/{integer_id}/steps"
                )
                
                if response.status_code != 200:
                    logger.warning("Failed to get execution steps", 
                                  execution_id=execution_id,
                                  integer_id=integer_id,
                                  status_code=response.status_code)
                    return []
                
                result = response.json()
                steps_data = result.get('data', {})
                return steps_data.get('steps', [])
                
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

    async def get_execution_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get execution history"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/executions",
                    params={'limit': limit, 'order': 'desc'}
                )
                
                if response.status_code != 200:
                    logger.warning("Failed to get execution history", 
                                  status_code=response.status_code)
                    return []
                
                result = response.json()
                return result.get('executions', [])
                
        except Exception as e:
            logger.error("Failed to get execution history", error=str(e))
            return []
    
    async def get_scheduled_jobs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get scheduled jobs"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/jobs",
                    params={'scheduled': 'true', 'limit': limit}
                )
                
                if response.status_code != 200:
                    logger.warning("Failed to get scheduled jobs", 
                                  status_code=response.status_code)
                    return []
                
                result = response.json()
                return result.get('jobs', [])
                
        except Exception as e:
            logger.error("Failed to get scheduled jobs", error=str(e))
            return []
    
    async def get_workflows_with_steps(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get workflows with step details"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/workflows",
                    params={'include_steps': 'true', 'limit': limit}
                )
                
                if response.status_code != 200:
                    logger.warning("Failed to get workflows with steps", 
                                  status_code=response.status_code)
                    return []
                
                result = response.json()
                return result.get('workflows', [])
                
        except Exception as e:
            logger.error("Failed to get workflows with steps", error=str(e))
            return []
    
    async def get_workflow_execution_stats(self, workflow_id: str) -> Dict[str, Any]:
        """Get execution statistics for a specific workflow"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/workflows/{workflow_id}/stats"
                )
                
                if response.status_code != 200:
                    logger.warning("Failed to get workflow execution stats", 
                                  workflow_id=workflow_id,
                                  status_code=response.status_code)
                    return {}
                
                return response.json()
                
        except Exception as e:
            logger.error("Failed to get workflow execution stats", 
                        workflow_id=workflow_id, error=str(e))
            return {}
    
    async def get_task_queue_status(self) -> Dict[str, Any]:
        """Get current task queue status"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/queue/status")
                
                if response.status_code != 200:
                    logger.warning("Failed to get task queue status", 
                                  status_code=response.status_code)
                    return {}
                
                return response.json()
                
        except Exception as e:
            logger.error("Failed to get task queue status", error=str(e))
            return {}
    
    async def get_execution_steps(self, execution_id: str) -> List[Dict[str, Any]]:
        """Get detailed steps for a specific execution"""
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
                        execution_id=execution_id, error=str(e))
            return []

    async def load_job_template(self, template_path: str) -> Optional[Dict[str, Any]]:
        """
        Load a job template from the automation-jobs directory
        
        Args:
            template_path: Path to the job template JSON file
            
        Returns:
            Dict with job template data or None if failed
        """
        try:
            import json
            import os
            
            # Ensure the path is absolute and within the automation-jobs directory
            if not os.path.isabs(template_path):
                base_dir = "/home/opsconductor/opsconductor-ng/automation-jobs"
                template_path = os.path.join(base_dir, template_path)
            
            if not os.path.exists(template_path):
                logger.error("Job template not found", template_path=template_path)
                return None
            
            with open(template_path, 'r') as f:
                template_data = json.load(f)
            
            logger.info("Job template loaded successfully", 
                       template_path=template_path,
                       job_name=template_data.get('name', 'Unknown'))
            
            return template_data
            
        except Exception as e:
            logger.error("Failed to load job template", 
                        template_path=template_path, 
                        error=str(e))
            return None

    async def execute_job_template(self, template_path: str, 
                                 parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute an existing job template with optional parameter substitution
        
        Args:
            template_path: Path to the job template JSON file
            parameters: Optional parameters to substitute in the template
            
        Returns:
            Dict with job creation and execution results
        """
        try:
            # Load the job template
            template_data = await self.load_job_template(template_path)
            if not template_data:
                return {
                    'success': False,
                    'error': f'Failed to load job template: {template_path}'
                }
            
            # Apply parameter substitution if provided
            if parameters:
                template_data = self._substitute_template_parameters(template_data, parameters)
            
            logger.info("Executing job template", 
                       template_path=template_path,
                       job_name=template_data.get('name'),
                       parameters=parameters)
            
            # Create job from template
            job_data = {
                'name': template_data.get('name', 'Template Job'),
                'description': template_data.get('description', 'Job created from template'),
                'workflow_definition': template_data.get('workflow_definition', {}),
                'job_type': template_data.get('job_type', 'template_based'),
                'is_enabled': True,
                'tags': template_data.get('tags', []) + ['template-based', 'ai-executed'],
                'metadata': {
                    'template_source': template_path,
                    'template_based': True,
                    'executed_by_ai': True,
                    'original_metadata': template_data.get('metadata', {}),
                    'submission_time': datetime.utcnow().isoformat(),
                    'parameters_applied': parameters or {}
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
                        f"Failed to create job from template: {response.status_code} - {response.text}"
                    )
                
                job_result = response.json()
                # Handle nested response format from automation service
                if 'data' in job_result:
                    job_data_response = job_result['data']
                    job_id = job_data_response['id']
                else:
                    job_id = job_result['id']
                
                logger.info("Template-based job created successfully", 
                           job_id=job_id, 
                           template_path=template_path)
                
                # Start job execution
                execution_result = await self.execute_job(job_id)
                
                return {
                    'success': True,
                    'job_id': job_id,
                    'job_name': template_data.get('name'),
                    'execution_id': execution_result.get('execution_id'),
                    'task_id': execution_result.get('task_id'),
                    'message': f"Template-based job submitted and started execution",
                    'template_path': template_path,
                    'job_details': job_result,
                    'execution_details': execution_result,
                    'template_data': template_data
                }
                
        except Exception as e:
            logger.error("Failed to execute job template", 
                        template_path=template_path,
                        error=str(e))
            
            return {
                'success': False,
                'error': f"Failed to execute template: {str(e)}",
                'template_path': template_path
            }

    def _substitute_template_parameters(self, template_data: Dict[str, Any], 
                                      parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Substitute parameters in template data using simple string replacement
        
        Args:
            template_data: The job template data
            parameters: Parameters to substitute (e.g., {'target_host': '192.168.50.211'})
            
        Returns:
            Template data with parameters substituted
        """
        try:
            import json
            import re
            
            # Convert template to JSON string for easy substitution
            template_json = json.dumps(template_data)
            
            # Apply parameter substitutions
            for key, value in parameters.items():
                # Replace both {{ key }} and {{ parameters.key }} patterns
                patterns = [
                    f"{{{{ {key} }}}}",
                    f"{{{{ parameters.{key} }}}}",
                    f"{{{{parameters.{key}}}}}",
                    f"{{{{{key}}}}}"
                ]
                
                for pattern in patterns:
                    template_json = template_json.replace(pattern, str(value))
            
            # Also handle credential substitutions if provided
            if 'credentials' in parameters:
                creds = parameters['credentials']
                for cred_key, cred_value in creds.items():
                    patterns = [
                        f"{{{{ credentials.{cred_key} }}}}",
                        f"{{{{credentials.{cred_key}}}}}"
                    ]
                    for pattern in patterns:
                        template_json = template_json.replace(pattern, str(cred_value))
            
            # Convert back to dict
            return json.loads(template_json)
            
        except Exception as e:
            logger.error("Failed to substitute template parameters", 
                        error=str(e))
            return template_data

    async def list_available_templates(self) -> List[Dict[str, Any]]:
        """
        List all available job templates in the automation-jobs directory
        
        Returns:
            List of template information
        """
        try:
            import os
            import json
            
            templates = []
            templates_dir = "/home/opsconductor/opsconductor-ng/automation-jobs"
            
            if not os.path.exists(templates_dir):
                logger.warning("Templates directory not found", path=templates_dir)
                return []
            
            for filename in os.listdir(templates_dir):
                if filename.endswith('.json'):
                    template_path = os.path.join(templates_dir, filename)
                    try:
                        with open(template_path, 'r') as f:
                            template_data = json.load(f)
                        
                        templates.append({
                            'filename': filename,
                            'path': template_path,
                            'name': template_data.get('name', filename),
                            'description': template_data.get('description', 'No description'),
                            'job_type': template_data.get('job_type', 'unknown'),
                            'tags': template_data.get('tags', []),
                            'metadata': template_data.get('metadata', {}),
                            'target_os': template_data.get('metadata', {}).get('target_os'),
                            'estimated_duration': template_data.get('metadata', {}).get('estimated_duration')
                        })
                        
                    except Exception as e:
                        logger.warning("Failed to parse template", 
                                     filename=filename, 
                                     error=str(e))
                        continue
            
            logger.info("Found job templates", count=len(templates))
            return templates
            
        except Exception as e:
            logger.error("Failed to list available templates", error=str(e))
            return []

    def get_client_info(self) -> Dict[str, Any]:
        """Get client information"""
        return {
            'name': 'Automation Service Client',
            'version': '1.1.0',
            'description': 'Client for AI Service to Automation Service integration with template support',
            'base_url': self.base_url,
            'capabilities': [
                'AI workflow submission',
                'Job execution management',
                'Execution status monitoring',
                'Step-by-step execution tracking',
                'AI job listing',
                'Execution history tracking',
                'Job scheduling queries',
                'Workflow step analysis',
                'Task queue monitoring',
                'Job template loading',
                'Template-based job execution',
                'Template parameter substitution',
                'Available templates listing'
            ],
            'timeouts': {
                'request_timeout': self.timeout,
                'max_retries': self.max_retries
            },
            'template_support': {
                'templates_directory': '/home/opsconductor/opsconductor-ng/automation-jobs',
                'parameter_substitution': True,
                'credential_substitution': True,
                'supported_formats': ['json']
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