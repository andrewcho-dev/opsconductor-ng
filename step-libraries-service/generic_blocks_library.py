"""
Generic Blocks Library for OpsConductor
Implements the StepLibraryBase interface for generic blocks
"""

from typing import Dict, List, Any
from datetime import datetime

from main import StepLibraryBase, LibraryMetadata, StepDefinition, StepParameter
from generic_blocks import GenericBlockExecutor, GENERIC_BLOCKS
from .logging import get_logger

logger = get_logger("generic-blocks-library")

class GenericBlocksLibrary(StepLibraryBase):
    """Generic blocks library implementation"""
    
    def __init__(self):
        self.executor = GenericBlockExecutor()
        self.metadata = LibraryMetadata(
            name="generic-blocks",
            version="1.0.0",
            display_name="Generic Blocks",
            description="Universal blocks that handle all automation scenarios through connection abstraction",
            author="OpsConductor Team",
            author_email="team@opsconductor.com",
            homepage="https://opsconductor.com",
            repository="https://github.com/opsconductor/generic-blocks",
            license="MIT",
            categories=["Actions", "Data", "Logic", "Flow"],
            tags=["generic", "universal", "ssh", "winrm", "http", "automation"],
            dependencies=[],
            min_opsconductor_version="1.0.0",
            is_premium=False
        )
    
    def get_metadata(self) -> LibraryMetadata:
        """Return library metadata"""
        return self.metadata
    
    def get_step_definitions(self) -> List[StepDefinition]:
        """Return all step definitions in this library"""
        step_definitions = []
        
        for block_type, block_config in GENERIC_BLOCKS.items():
            # Convert inputs to parameters
            parameters = {}
            
            # Add configuration parameters from config_schema
            if "config_schema" in block_config and "properties" in block_config["config_schema"]:
                for param_name, param_config in block_config["config_schema"]["properties"].items():
                    param_type = param_config.get("type", "string")
                    param_required = param_name in block_config["config_schema"].get("required", [])
                    param_default = param_config.get("default")
                    param_description = param_config.get("description", "")
                    param_enum = param_config.get("enum")
                    
                    parameters[param_name] = StepParameter(
                        type=param_type,
                        required=param_required,
                        default=param_default,
                        description=param_description,
                        options=param_enum
                    )
            
            # Create step definition
            step_def = StepDefinition(
                name=block_type,
                display_name=block_config["name"],
                category=block_config["category"],
                description=block_config["description"],
                icon=block_config["icon"],
                color=block_config["color"],
                inputs=len(block_config.get("inputs", [])),
                outputs=len(block_config.get("outputs", [])),
                parameters=parameters,
                platform_support=["windows", "linux", "macos"],
                required_permissions=[],
                examples=[
                    {
                        "name": f"Basic {block_config['name']} Example",
                        "description": f"Simple example of {block_config['name']} usage",
                        "config": self._get_example_config(block_type)
                    }
                ],
                tags=["generic", block_config["category"]]
            )
            
            step_definitions.append(step_def)
        
        return step_definitions
    
    async def execute_step(self, step_name: str, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a step from this library"""
        logger.info(f"Executing generic block step: {step_name}")
        
        if step_name not in GENERIC_BLOCKS:
            return {
                "success": False,
                "error": f"Unknown step: {step_name}",
                "result": None
            }
        
        try:
            # Execute the generic block
            result = await self.executor.execute_block(step_name, parameters, context.get("input_data", {}))
            
            logger.info(f"Generic block {step_name} executed successfully: {result.get('success', False)}")
            return result
            
        except Exception as e:
            logger.error(f"Generic block execution failed: {str(e)}")
            return {
                "success": False,
                "error": f"Execution failed: {str(e)}",
                "result": None
            }
    
    async def validate_step(self, step_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate step parameters"""
        if step_name not in GENERIC_BLOCKS:
            return {
                "valid": False,
                "errors": [f"Unknown step: {step_name}"]
            }
        
        block_config = GENERIC_BLOCKS[step_name]
        config_schema = block_config.get("config_schema", {})
        required_params = config_schema.get("required", [])
        properties = config_schema.get("properties", {})
        
        errors = []
        
        # Check required parameters
        for required_param in required_params:
            if required_param not in parameters:
                errors.append(f"Missing required parameter: {required_param}")
        
        # Validate parameter types and values
        for param_name, param_value in parameters.items():
            if param_name in properties:
                param_schema = properties[param_name]
                param_type = param_schema.get("type")
                param_enum = param_schema.get("enum")
                
                # Type validation
                if param_type == "string" and not isinstance(param_value, str):
                    errors.append(f"Parameter {param_name} must be a string")
                elif param_type == "integer" and not isinstance(param_value, int):
                    errors.append(f"Parameter {param_name} must be an integer")
                elif param_type == "number" and not isinstance(param_value, (int, float)):
                    errors.append(f"Parameter {param_name} must be a number")
                elif param_type == "boolean" and not isinstance(param_value, bool):
                    errors.append(f"Parameter {param_name} must be a boolean")
                elif param_type == "array" and not isinstance(param_value, list):
                    errors.append(f"Parameter {param_name} must be an array")
                elif param_type == "object" and not isinstance(param_value, dict):
                    errors.append(f"Parameter {param_name} must be an object")
                
                # Enum validation
                if param_enum and param_value not in param_enum:
                    errors.append(f"Parameter {param_name} must be one of: {', '.join(param_enum)}")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
    
    def _get_example_config(self, block_type: str) -> Dict[str, Any]:
        """Get example configuration for a block type"""
        examples = {
            "action.command": {
                "target": "localhost",
                "connection_method": "local",
                "command": "echo 'Hello World'",
                "timeout_seconds": 30
            },
            "action.http_request": {
                "method": "GET",
                "url": "https://httpbin.org/json",
                "headers": {"Content-Type": "application/json"},
                "timeout_seconds": 30
            },
            "action.notification": {
                "notification_type": "email",
                "recipients": ["admin@example.com"],
                "subject": "Test Notification",
                "message": "This is a test notification from OpsConductor"
            },
            "data.transform": {
                "script": "# Transform input data\\nresult = {'processed': True, 'timestamp': datetime.now().isoformat()}"
            },
            "logic.if": {
                "condition": "{{data.status}} === 'active'"
            },
            "flow.delay": {
                "delay_seconds": 5
            },
            "flow.start": {
                "name": "Example Workflow",
                "trigger_types": ["manual"]
            },
            "flow.end": {
                "name": "Workflow Complete"
            }
        }
        
        return examples.get(block_type, {})


# Factory function to create the library instance
def create_generic_blocks_library() -> GenericBlocksLibrary:
    """Create and return a generic blocks library instance"""
    return GenericBlocksLibrary()