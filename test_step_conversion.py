#!/usr/bin/env python3

import json
import sys
from pathlib import Path
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List

class StepParameter(BaseModel):
    """Step parameter definition"""
    type: str = Field(..., description="Parameter type (string, number, boolean, array, object)")
    required: bool = Field(default=False, description="Whether parameter is required")
    default: Any = Field(default=None, description="Default value")
    description: str = Field(default="", description="Parameter description")
    validation: Optional[Dict[str, Any]] = Field(default=None, description="Validation rules")
    options: Optional[List[Any]] = Field(default=None, description="Allowed values for enum types")

class StepDefinition(BaseModel):
    """Individual step definition within a library"""
    name: str = Field(..., description="Step identifier (e.g., 'file.create')")
    display_name: str = Field(..., description="Human-readable step name")
    category: str = Field(..., description="Step category")
    description: str = Field(..., description="Step description")
    icon: str = Field(default="📄", description="Step icon")
    color: str = Field(default="#007bff", description="Step color")
    inputs: int = Field(default=1, description="Number of input ports")
    outputs: int = Field(default=1, description="Number of output ports")
    parameters: Dict[str, StepParameter] = Field(default_factory=dict, description="Step parameters")
    platform_support: List[str] = Field(default_factory=lambda: ["windows", "linux", "macos"], description="Supported platforms")
    required_permissions: List[str] = Field(default_factory=list, description="Required permissions")
    examples: List[Dict[str, Any]] = Field(default_factory=list, description="Usage examples")
    tags: List[str] = Field(default_factory=list, description="Search tags")

def test_step_conversion():
    """Test the step conversion process"""
    
    # Load the manifest
    manifest_path = Path("starter-libraries/windows-core/manifest.json")
    with open(manifest_path, 'r') as f:
        manifest_data = json.load(f)
    
    print("=== TESTING STEP CONVERSION ===")
    
    try:
        # Test conversion of first step
        step_data = manifest_data['steps'][0].copy()
        print(f"Converting step: {step_data['name']}")
        
        # Convert parameter dictionaries to StepParameter objects
        if 'parameters' in step_data:
            print(f"Original parameters: {len(step_data['parameters'])}")
            parameters = {}
            for param_name, param_dict in step_data['parameters'].items():
                print(f"  Converting parameter: {param_name}")
                print(f"    Data: {param_dict}")
                try:
                    param_obj = StepParameter(**param_dict)
                    parameters[param_name] = param_obj
                    print(f"    ✅ Successfully converted")
                except Exception as e:
                    print(f"    ❌ Failed to convert: {e}")
                    return False
            step_data['parameters'] = parameters
            print(f"Converted parameters: {len(parameters)}")
        
        # Try to create StepDefinition
        print("Creating StepDefinition...")
        step_def = StepDefinition(**step_data)
        print("✅ Successfully created StepDefinition")
        
        # Test JSON serialization of parameters
        print("Testing parameter serialization...")
        parameters_dict = {}
        for param_name, param_obj in step_def.parameters.items():
            if hasattr(param_obj, 'dict'):
                parameters_dict[param_name] = param_obj.dict()
            else:
                parameters_dict[param_name] = param_obj
        
        json_str = json.dumps(parameters_dict)
        print("✅ Successfully serialized parameters to JSON")
        print(f"JSON length: {len(json_str)} characters")
        
        return True
        
    except Exception as e:
        import traceback
        print(f"❌ Error during conversion: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = test_step_conversion()
    sys.exit(0 if success else 1)