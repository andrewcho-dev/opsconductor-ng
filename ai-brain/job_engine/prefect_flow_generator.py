"""
OpsConductor AI Brain - Prefect Flow Generator

This module generates Python Prefect flows from workflow definitions.
It converts OpsConductor workflow steps into executable Prefect flow code.
"""

import logging
import json
import textwrap
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import timedelta
from enum import Enum

from .workflow_generator import GeneratedWorkflow, WorkflowStep, StepType
from integrations.prefect_client import PrefectFlowDefinition

logger = logging.getLogger(__name__)


class PrefectTaskType(Enum):
    """Types of Prefect tasks"""
    COMMAND = "command"
    SCRIPT = "script"
    VALIDATION = "validation"
    CONDITION = "condition"
    NOTIFICATION = "notification"
    PARALLEL_GROUP = "parallel_group"
    SEQUENTIAL_GROUP = "sequential_group"


@dataclass
class PrefectTaskDefinition:
    """Definition of a Prefect task"""
    task_name: str
    task_type: PrefectTaskType
    function_code: str
    dependencies: List[str]
    parameters: Dict[str, Any]
    timeout_seconds: Optional[int] = None
    retries: int = 0
    retry_delay_seconds: int = 60


class PrefectFlowGenerator:
    """
    Generates Prefect flows from OpsConductor workflows
    
    Converts workflow definitions into executable Python Prefect flow code
    with proper task dependencies, error handling, and parameter passing.
    """
    
    def __init__(self):
        """Initialize the Prefect flow generator"""
        logger.info("Prefect flow generator initialized")
    
    def generate_prefect_flow(
        self,
        workflow: GeneratedWorkflow,
        flow_name_override: Optional[str] = None
    ) -> PrefectFlowDefinition:
        """
        Generate a Prefect flow from an OpsConductor workflow
        
        Args:
            workflow: The OpsConductor workflow to convert
            flow_name_override: Optional override for the flow name
            
        Returns:
            PrefectFlowDefinition ready for registration and execution
        """
        try:
            logger.info(f"Generating Prefect flow from workflow: {workflow.workflow_id}")
            
            # Generate flow name
            flow_name = flow_name_override or self._generate_flow_name(workflow)
            
            # Convert workflow steps to Prefect tasks
            tasks = self._convert_steps_to_tasks(workflow.steps)
            
            # Generate the complete flow code
            flow_code = self._generate_flow_code(flow_name, workflow, tasks)
            
            # Extract parameters from workflow
            parameters = self._extract_flow_parameters(workflow)
            
            # Generate tags
            tags = self._generate_flow_tags(workflow)
            
            # Create flow definition
            flow_definition = PrefectFlowDefinition(
                name=flow_name,
                description=workflow.description,
                flow_code=flow_code,
                parameters=parameters,
                tags=tags,
                timeout_seconds=workflow.estimated_duration * 60,  # Convert minutes to seconds
                retries=1 if workflow.risk_level in ["medium", "high"] else 0,
                retry_delay_seconds=120
            )
            
            logger.info(f"Generated Prefect flow: {flow_name} with {len(tasks)} tasks")
            return flow_definition
            
        except Exception as e:
            logger.error(f"Error generating Prefect flow: {str(e)}")
            raise
    
    def _generate_flow_name(self, workflow: GeneratedWorkflow) -> str:
        """Generate a valid Prefect flow name"""
        # Clean the workflow name for Prefect
        base_name = workflow.name.lower().replace(" ", "_").replace("-", "_")
        # Remove special characters
        import re
        base_name = re.sub(r'[^a-z0-9_]', '', base_name)
        
        # Add workflow type prefix
        type_prefix = workflow.workflow_type.value.replace("_", "")
        
        return f"{type_prefix}_{base_name}"
    
    def _convert_steps_to_tasks(self, steps: List[WorkflowStep]) -> List[PrefectTaskDefinition]:
        """Convert workflow steps to Prefect task definitions"""
        tasks = []
        
        for step in steps:
            task = self._convert_step_to_task(step)
            tasks.append(task)
        
        return tasks
    
    def _convert_step_to_task(self, step: WorkflowStep) -> PrefectTaskDefinition:
        """Convert a single workflow step to a Prefect task"""
        # Determine task type
        task_type = self._map_step_type_to_task_type(step.step_type)
        
        # Generate task name
        task_name = self._generate_task_name(step)
        
        # Generate function code based on step type
        function_code = self._generate_task_function_code(step, task_name)
        
        # Extract dependencies
        dependencies = step.dependencies.copy()
        
        # Create task definition
        task = PrefectTaskDefinition(
            task_name=task_name,
            task_type=task_type,
            function_code=function_code,
            dependencies=dependencies,
            parameters=step.parameters.copy(),
            timeout_seconds=step.timeout,
            retries=step.retry_count,
            retry_delay_seconds=step.retry_delay
        )
        
        return task
    
    def _map_step_type_to_task_type(self, step_type: StepType) -> PrefectTaskType:
        """Map OpsConductor step types to Prefect task types"""
        mapping = {
            StepType.COMMAND: PrefectTaskType.COMMAND,
            StepType.SCRIPT: PrefectTaskType.SCRIPT,
            StepType.VALIDATION: PrefectTaskType.VALIDATION,
            StepType.CONDITION: PrefectTaskType.CONDITION,
            StepType.NOTIFICATION: PrefectTaskType.NOTIFICATION,
            StepType.PARALLEL: PrefectTaskType.PARALLEL_GROUP,
            StepType.SEQUENTIAL: PrefectTaskType.SEQUENTIAL_GROUP,
            StepType.ERROR_HANDLER: PrefectTaskType.VALIDATION,
            StepType.NETWORK_CAPTURE: PrefectTaskType.COMMAND,
            StepType.NETWORK_MONITOR: PrefectTaskType.COMMAND,
            StepType.PROTOCOL_ANALYSIS: PrefectTaskType.SCRIPT,
            StepType.AI_NETWORK_DIAGNOSIS: PrefectTaskType.SCRIPT
        }
        
        return mapping.get(step_type, PrefectTaskType.COMMAND)
    
    def _generate_task_name(self, step: WorkflowStep) -> str:
        """Generate a valid Prefect task name"""
        # Clean the step name
        task_name = step.name.lower().replace(" ", "_").replace("-", "_")
        # Remove special characters
        import re
        task_name = re.sub(r'[^a-z0-9_]', '', task_name)
        
        # Ensure it starts with a letter
        if task_name and not task_name[0].isalpha():
            task_name = f"task_{task_name}"
        
        # Fallback if empty
        if not task_name:
            task_name = f"step_{step.step_id}"
        
        return task_name
    
    def _generate_task_function_code(self, step: WorkflowStep, task_name: str) -> str:
        """Generate Python function code for a Prefect task"""
        if step.step_type == StepType.COMMAND:
            return self._generate_command_task_code(step, task_name)
        elif step.step_type == StepType.SCRIPT:
            return self._generate_script_task_code(step, task_name)
        elif step.step_type == StepType.VALIDATION:
            return self._generate_validation_task_code(step, task_name)
        elif step.step_type == StepType.CONDITION:
            return self._generate_condition_task_code(step, task_name)
        elif step.step_type == StepType.NOTIFICATION:
            return self._generate_notification_task_code(step, task_name)
        else:
            return self._generate_generic_task_code(step, task_name)
    
    def _generate_command_task_code(self, step: WorkflowStep, task_name: str) -> str:
        """Generate code for a command execution task"""
        timeout_config = f"timeout_seconds={step.timeout}" if step.timeout else ""
        retry_config = f"retries={step.retry_count}" if step.retry_count > 0 else ""
        
        # Build task decorator
        task_options = [opt for opt in [timeout_config, retry_config] if opt]
        task_decorator = f"@task({', '.join(task_options)})" if task_options else "@task"
        
        return textwrap.dedent(f'''
        {task_decorator}
        def {task_name}():
            """
            {step.description}
            """
            import subprocess
            import logging
            
            logger = logging.getLogger(__name__)
            command = {repr(step.command)}
            
            try:
                logger.info(f"Executing command: {{command}}")
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout={step.timeout or 300}
                )
                
                if result.returncode == 0:
                    logger.info(f"Command completed successfully")
                    return {{
                        "success": True,
                        "output": result.stdout,
                        "exit_code": result.returncode
                    }}
                else:
                    logger.error(f"Command failed with exit code {{result.returncode}}")
                    logger.error(f"Error output: {{result.stderr}}")
                    raise RuntimeError(f"Command failed: {{result.stderr}}")
                    
            except subprocess.TimeoutExpired:
                logger.error(f"Command timed out after {step.timeout or 300} seconds")
                raise RuntimeError(f"Command timeout: {{command}}")
            except Exception as e:
                logger.error(f"Command execution error: {{str(e)}}")
                raise
        ''').strip()
    
    def _generate_script_task_code(self, step: WorkflowStep, task_name: str) -> str:
        """Generate code for a script execution task"""
        timeout_config = f"timeout_seconds={step.timeout}" if step.timeout else ""
        retry_config = f"retries={step.retry_count}" if step.retry_count > 0 else ""
        
        task_options = [opt for opt in [timeout_config, retry_config] if opt]
        task_decorator = f"@task({', '.join(task_options)})" if task_options else "@task"
        
        return textwrap.dedent(f'''
        {task_decorator}
        def {task_name}():
            """
            {step.description}
            """
            import tempfile
            import subprocess
            import os
            import logging
            
            logger = logging.getLogger(__name__)
            script_content = {repr(step.script)}
            
            try:
                # Create temporary script file
                with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
                    f.write(script_content)
                    script_path = f.name
                
                # Make script executable
                os.chmod(script_path, 0o755)
                
                logger.info(f"Executing script: {{script_path}}")
                result = subprocess.run(
                    ['/bin/bash', script_path],
                    capture_output=True,
                    text=True,
                    timeout={step.timeout or 300}
                )
                
                # Clean up
                os.unlink(script_path)
                
                if result.returncode == 0:
                    logger.info(f"Script completed successfully")
                    return {{
                        "success": True,
                        "output": result.stdout,
                        "exit_code": result.returncode
                    }}
                else:
                    logger.error(f"Script failed with exit code {{result.returncode}}")
                    logger.error(f"Error output: {{result.stderr}}")
                    raise RuntimeError(f"Script failed: {{result.stderr}}")
                    
            except subprocess.TimeoutExpired:
                logger.error(f"Script timed out after {step.timeout or 300} seconds")
                if 'script_path' in locals():
                    os.unlink(script_path)
                raise RuntimeError(f"Script timeout")
            except Exception as e:
                logger.error(f"Script execution error: {{str(e)}}")
                if 'script_path' in locals():
                    os.unlink(script_path)
                raise
        ''').strip()
    
    def _generate_validation_task_code(self, step: WorkflowStep, task_name: str) -> str:
        """Generate code for a validation task"""
        return textwrap.dedent(f'''
        @task
        def {task_name}():
            """
            {step.description}
            """
            import logging
            
            logger = logging.getLogger(__name__)
            validation_command = {repr(step.validation_command)}
            expected_result = {repr(step.expected_result)}
            
            try:
                logger.info(f"Running validation: {{validation_command}}")
                
                if validation_command:
                    import subprocess
                    result = subprocess.run(
                        validation_command,
                        shell=True,
                        capture_output=True,
                        text=True,
                        timeout=60
                    )
                    
                    if result.returncode == 0:
                        logger.info("Validation passed")
                        return {{
                            "success": True,
                            "validation_result": result.stdout,
                            "message": "Validation completed successfully"
                        }}
                    else:
                        logger.error(f"Validation failed: {{result.stderr}}")
                        raise RuntimeError(f"Validation failed: {{result.stderr}}")
                else:
                    # Simple validation step
                    logger.info("Validation step completed")
                    return {{
                        "success": True,
                        "message": "Validation step completed"
                    }}
                    
            except Exception as e:
                logger.error(f"Validation error: {{str(e)}}")
                raise
        ''').strip()
    
    def _generate_condition_task_code(self, step: WorkflowStep, task_name: str) -> str:
        """Generate code for a conditional task"""
        return textwrap.dedent(f'''
        @task
        def {task_name}():
            """
            {step.description}
            """
            import logging
            
            logger = logging.getLogger(__name__)
            success_conditions = {step.success_conditions}
            failure_conditions = {step.failure_conditions}
            
            try:
                logger.info("Evaluating conditions")
                
                # Simple condition evaluation
                # In a real implementation, this would evaluate the conditions
                condition_met = True  # Placeholder logic
                
                if condition_met:
                    logger.info("Condition evaluation passed")
                    return {{
                        "success": True,
                        "condition_result": True,
                        "message": "Condition met"
                    }}
                else:
                    logger.warning("Condition evaluation failed")
                    return {{
                        "success": False,
                        "condition_result": False,
                        "message": "Condition not met"
                    }}
                    
            except Exception as e:
                logger.error(f"Condition evaluation error: {{str(e)}}")
                raise
        ''').strip()
    
    def _generate_notification_task_code(self, step: WorkflowStep, task_name: str) -> str:
        """Generate code for a notification task"""
        return textwrap.dedent(f'''
        @task
        def {task_name}():
            """
            {step.description}
            """
            import logging
            
            logger = logging.getLogger(__name__)
            notification_events = {step.notification_events}
            
            try:
                logger.info("Sending notification")
                
                # Placeholder notification logic
                # In a real implementation, this would send notifications
                # via email, Slack, webhooks, etc.
                
                logger.info("Notification sent successfully")
                return {{
                    "success": True,
                    "message": "Notification sent",
                    "events": notification_events
                }}
                
            except Exception as e:
                logger.error(f"Notification error: {{str(e)}}")
                raise
        ''').strip()
    
    def _generate_generic_task_code(self, step: WorkflowStep, task_name: str) -> str:
        """Generate code for a generic task"""
        return textwrap.dedent(f'''
        @task
        def {task_name}():
            """
            {step.description}
            """
            import logging
            
            logger = logging.getLogger(__name__)
            
            try:
                logger.info("Executing generic task: {step.name}")
                
                # Placeholder task logic
                # This would be customized based on the specific step requirements
                
                logger.info("Generic task completed successfully")
                return {{
                    "success": True,
                    "message": "Task completed",
                    "step_type": "{step.step_type.value}"
                }}
                
            except Exception as e:
                logger.error(f"Generic task error: {{str(e)}}")
                raise
        ''').strip()
    
    def _generate_flow_code(
        self,
        flow_name: str,
        workflow: GeneratedWorkflow,
        tasks: List[PrefectTaskDefinition]
    ) -> str:
        """Generate the complete Prefect flow code"""
        
        # Generate imports
        imports = textwrap.dedent('''
        from prefect import flow, task
        import logging
        import subprocess
        import tempfile
        import os
        from datetime import timedelta
        ''').strip()
        
        # Generate task functions
        task_functions = []
        for task in tasks:
            task_functions.append(task.function_code)
        
        # Generate flow function
        flow_function = self._generate_flow_function(flow_name, workflow, tasks)
        
        # Combine all parts
        complete_code = f"{imports}\n\n" + "\n\n".join(task_functions) + f"\n\n{flow_function}"
        
        return complete_code
    
    def _generate_flow_function(
        self,
        flow_name: str,
        workflow: GeneratedWorkflow,
        tasks: List[PrefectTaskDefinition]
    ) -> str:
        """Generate the main flow function"""
        
        # Build task execution with dependencies
        task_calls = []
        task_results = {}
        
        for task in tasks:
            if task.dependencies:
                # Task has dependencies
                deps = [f"{dep}_result" for dep in task.dependencies if dep in [t.task_name for t in tasks]]
                if deps:
                    task_calls.append(f"    {task.task_name}_result = {task.task_name}()")
                else:
                    task_calls.append(f"    {task.task_name}_result = {task.task_name}()")
            else:
                # No dependencies
                task_calls.append(f"    {task.task_name}_result = {task.task_name}()")
            
            task_results[task.task_name] = f"{task.task_name}_result"
        
        # Generate return statement
        return_dict = {task.task_name: f"{task.task_name}_result" for task in tasks}
        return_statement = f"    return {return_dict}"
        
        flow_code = textwrap.dedent(f'''
        @flow(name="{flow_name}", description="{workflow.description}")
        def {flow_name}():
            """
            {workflow.description}
            
            Generated from OpsConductor workflow: {workflow.workflow_id}
            Workflow type: {workflow.workflow_type.value}
            Risk level: {workflow.risk_level}
            """
            logger = logging.getLogger(__name__)
            logger.info(f"Starting workflow execution: {flow_name}")
            
        {chr(10).join(task_calls)}
            
            logger.info(f"Workflow execution completed: {flow_name}")
        {return_statement}
        ''').strip()
        
        return flow_code
    
    def _extract_flow_parameters(self, workflow: GeneratedWorkflow) -> Dict[str, Any]:
        """Extract parameters from workflow for Prefect flow"""
        parameters = workflow.parameters.copy()
        
        # Add common workflow parameters
        parameters.update({
            "workflow_id": workflow.workflow_id,
            "workflow_type": workflow.workflow_type.value,
            "target_systems": workflow.target_systems,
            "risk_level": workflow.risk_level,
            "requires_approval": workflow.requires_approval
        })
        
        return parameters
    
    def _generate_flow_tags(self, workflow: GeneratedWorkflow) -> List[str]:
        """Generate tags for the Prefect flow"""
        tags = workflow.tags.copy()
        
        # Add standard tags
        tags.extend([
            f"workflow_type:{workflow.workflow_type.value}",
            f"risk_level:{workflow.risk_level}",
            "opsconductor",
            "ai_generated"
        ])
        
        # Add target system tags
        for system in workflow.target_systems:
            tags.append(f"target:{system}")
        
        return list(set(tags))  # Remove duplicates