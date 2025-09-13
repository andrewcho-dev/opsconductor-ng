"""
OpsConductor AI Service
Converts natural language requests into automation workflows
"""

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import httpx
import re
import json
import logging
from datetime import datetime
import os

# Import shared utilities
from shared.base_service import BaseService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="OpsConductor AI Service", version="1.0.0")

# Configuration
ASSET_SERVICE_URL = os.getenv("ASSET_SERVICE_URL", "http://asset-service:3001")
AUTOMATION_SERVICE_URL = os.getenv("AUTOMATION_SERVICE_URL", "http://automation-service:3003")

class JobRequest(BaseModel):
    description: str
    user_id: Optional[int] = 1

class WorkflowStep(BaseModel):
    name: str
    type: str
    parameters: Dict[str, Any]
    targets: List[str]

class GeneratedWorkflow(BaseModel):
    name: str
    description: str
    steps: List[WorkflowStep]
    estimated_duration: int  # in minutes

class AIJobService:
    """AI service for converting natural language to automation workflows"""
    
    def __init__(self):
        self.asset_client = httpx.AsyncClient(base_url=ASSET_SERVICE_URL)
        self.automation_client = httpx.AsyncClient(base_url=AUTOMATION_SERVICE_URL)
        
        # Simple pattern matching for prototype (will be replaced with proper NLP)
        self.patterns = {
            'service_operations': {
                'stop': r'stop\s+(?:service\s+)?(\w+)',
                'start': r'start\s+(?:service\s+)?(\w+)', 
                'restart': r'restart\s+(?:service\s+)?(\w+)',
            },
            'file_operations': {
                'copy': r'copy\s+(.+?)\s+(?:to\s+)?(.+?)(?:\s+on|\s*$)',
                'update': r'update\s+(\w+)',
                'backup': r'backup\s+(.+)',
            },
            'process_operations': {
                'check': r'check\s+(?:if\s+)?(\w+)(?:\s+is\s+running)?',
                'kill': r'(?:kill|stop)\s+(?:process\s+)?(\w+)',
            },
            'target_groups': r'(?:on\s+|in\s+)(?:group\s+)?[\'"]?([^\'"\s]+)[\'"]?\s*(?:servers?|systems?|group)?',
            'package_operations': {
                'install': r'install\s+(\w+)',
                'update': r'update\s+(\w+)(?:\s+to\s+latest)?',
                'remove': r'(?:remove|uninstall)\s+(\w+)',
            }
        }
    
    async def parse_request(self, description: str) -> Dict[str, Any]:
        """Parse natural language request into structured intent"""
        logger.info(f"Parsing request: {description}")
        
        intent = {
            'operations': [],
            'targets': [],
            'files': [],
            'services': [],
            'processes': [],
            'packages': []
        }
        
        # Extract target groups
        target_match = re.search(self.patterns['target_groups'], description, re.IGNORECASE)
        if target_match:
            group_name = target_match.group(1)
            intent['target_group'] = group_name
            logger.info(f"Found target group: {group_name}")
        
        # Extract service operations
        for operation, pattern in self.patterns['service_operations'].items():
            matches = re.findall(pattern, description, re.IGNORECASE)
            for match in matches:
                intent['operations'].append({
                    'type': 'service',
                    'action': operation,
                    'target': match
                })
                intent['services'].append(match)
        
        # Extract file operations
        for operation, pattern in self.patterns['file_operations'].items():
            matches = re.findall(pattern, description, re.IGNORECASE)
            for match in matches:
                if operation == 'copy' and len(match) == 2:
                    intent['operations'].append({
                        'type': 'file',
                        'action': operation,
                        'source': match[0].strip(),
                        'destination': match[1].strip()
                    })
                else:
                    intent['operations'].append({
                        'type': 'file',
                        'action': operation,
                        'target': match if isinstance(match, str) else match[0]
                    })
        
        # Extract process operations
        for operation, pattern in self.patterns['process_operations'].items():
            matches = re.findall(pattern, description, re.IGNORECASE)
            for match in matches:
                intent['operations'].append({
                    'type': 'process',
                    'action': operation,
                    'target': match
                })
                intent['processes'].append(match)
        
        # Extract package operations
        for operation, pattern in self.patterns['package_operations'].items():
            matches = re.findall(pattern, description, re.IGNORECASE)
            for match in matches:
                intent['operations'].append({
                    'type': 'package',
                    'action': operation,
                    'target': match
                })
                intent['packages'].append(match)
        
        logger.info(f"Parsed intent: {intent}")
        return intent
    
    async def get_target_group(self, group_name: str) -> List[Dict[str, Any]]:
        """Get targets from asset service"""
        try:
            response = await self.asset_client.get(f"/target-groups/{group_name}")
            if response.status_code == 200:
                group_data = response.json()
                return group_data.get('targets', [])
            else:
                logger.warning(f"Target group '{group_name}' not found")
                return []
        except Exception as e:
            logger.error(f"Error fetching target group: {e}")
            return []
    
    async def generate_workflow(self, intent: Dict[str, Any]) -> GeneratedWorkflow:
        """Generate workflow from parsed intent"""
        logger.info("Generating workflow from intent")
        
        workflow_steps = []
        estimated_duration = 0
        
        # Get targets if target group specified
        targets = []
        if 'target_group' in intent:
            targets = await self.get_target_group(intent['target_group'])
            target_ids = [str(target['id']) for target in targets]
        else:
            target_ids = ['all']  # Default to all targets
        
        # Generate steps based on operations
        for i, operation in enumerate(intent['operations']):
            step_name = f"Step {i+1}: {operation['action'].title()} {operation.get('target', '')}"
            
            if operation['type'] == 'service':
                workflow_steps.append(WorkflowStep(
                    name=step_name,
                    type="service_management",
                    parameters={
                        "action": operation['action'],
                        "service_name": operation['target'],
                        "timeout": 60
                    },
                    targets=target_ids
                ))
                estimated_duration += 2  # 2 minutes per service operation
                
            elif operation['type'] == 'file':
                if operation['action'] == 'copy':
                    workflow_steps.append(WorkflowStep(
                        name=step_name,
                        type="file_operation",
                        parameters={
                            "action": "copy",
                            "source": operation['source'],
                            "destination": operation['destination'],
                            "backup": True
                        },
                        targets=target_ids
                    ))
                    estimated_duration += 3  # 3 minutes per file operation
                else:
                    workflow_steps.append(WorkflowStep(
                        name=step_name,
                        type="file_operation",
                        parameters={
                            "action": operation['action'],
                            "target": operation['target']
                        },
                        targets=target_ids
                    ))
                    estimated_duration += 2
                    
            elif operation['type'] == 'process':
                workflow_steps.append(WorkflowStep(
                    name=step_name,
                    type="process_management",
                    parameters={
                        "action": operation['action'],
                        "process_name": operation['target']
                    },
                    targets=target_ids
                ))
                estimated_duration += 1  # 1 minute per process check
                
            elif operation['type'] == 'package':
                workflow_steps.append(WorkflowStep(
                    name=step_name,
                    type="package_management",
                    parameters={
                        "action": operation['action'],
                        "package_name": operation['target']
                    },
                    targets=target_ids
                ))
                estimated_duration += 5  # 5 minutes per package operation
        
        # Create workflow name from description
        workflow_name = f"AI Generated: {intent.get('target_group', 'Multiple Targets')}"
        
        return GeneratedWorkflow(
            name=workflow_name,
            description=f"Auto-generated workflow with {len(workflow_steps)} steps",
            steps=workflow_steps,
            estimated_duration=max(estimated_duration, 1)
        )
    
    async def submit_workflow(self, workflow: GeneratedWorkflow, user_id: int) -> Dict[str, Any]:
        """Submit workflow to automation service"""
        try:
            # Convert to automation service format
            workflow_data = {
                "name": workflow.name,
                "description": workflow.description,
                "steps": [
                    {
                        "name": step.name,
                        "type": step.type,
                        "parameters": step.parameters,
                        "targets": step.targets
                    }
                    for step in workflow.steps
                ],
                "user_id": user_id,
                "created_by": "ai-service"
            }
            
            response = await self.automation_client.post("/jobs", json=workflow_data)
            if response.status_code == 201:
                return response.json()
            else:
                logger.error(f"Failed to submit workflow: {response.text}")
                raise HTTPException(status_code=500, detail="Failed to submit workflow")
                
        except Exception as e:
            logger.error(f"Error submitting workflow: {e}")
            raise HTTPException(status_code=500, detail=str(e))

# Initialize AI service
ai_service = AIJobService()

@app.post("/create-job")
async def create_job(request: JobRequest):
    """
    Create a job from natural language description
    
    Example: "Stop stationcontroller service on CIS servers"
    """
    try:
        logger.info(f"Received job request: {request.description}")
        
        # Parse the natural language request
        intent = await ai_service.parse_request(request.description)
        
        if not intent['operations']:
            raise HTTPException(
                status_code=400, 
                detail="Could not understand the request. Please try rephrasing."
            )
        
        # Generate workflow
        workflow = await ai_service.generate_workflow(intent)
        
        # Submit to automation service
        job_result = await ai_service.submit_workflow(workflow, request.user_id)
        
        return {
            "success": True,
            "message": f"Created workflow with {len(workflow.steps)} steps",
            "workflow": workflow.dict(),
            "job_id": job_result.get("id"),
            "estimated_duration": f"{workflow.estimated_duration} minutes"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating job: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/preview-workflow")
async def preview_workflow(request: JobRequest):
    """
    Preview workflow without executing it
    """
    try:
        logger.info(f"Previewing workflow for: {request.description}")
        
        # Parse the natural language request
        intent = await ai_service.parse_request(request.description)
        
        if not intent['operations']:
            raise HTTPException(
                status_code=400, 
                detail="Could not understand the request. Please try rephrasing."
            )
        
        # Generate workflow
        workflow = await ai_service.generate_workflow(intent)
        
        return {
            "success": True,
            "workflow": workflow.dict(),
            "explanation": f"This workflow will perform {len(workflow.steps)} operations",
            "estimated_duration": f"{workflow.estimated_duration} minutes"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error previewing workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "ai-service", "timestamp": datetime.utcnow()}

@app.get("/patterns")
async def get_patterns():
    """Get supported patterns for debugging"""
    return {"patterns": ai_service.patterns}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3005)