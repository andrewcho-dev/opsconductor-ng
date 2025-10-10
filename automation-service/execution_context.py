#!/usr/bin/env python3
"""
Execution Context Manager for Multi-Step Workflows
Handles template variable resolution, step dependencies, and loop execution
"""

import re
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from copy import deepcopy

logger = logging.getLogger(__name__)


class ExecutionContext:
    """
    Manages execution context for multi-step workflows
    
    Features:
    - Store step results
    - Resolve template variables ({{variable}})
    - Handle step dependencies
    - Expand loops for multiple targets
    """
    
    def __init__(self, execution_id: str):
        self.execution_id = execution_id
        self.step_results: Dict[int, Dict[str, Any]] = {}
        self.variables: Dict[str, Any] = {}
        
    def store_step_result(self, step_index: int, result: Dict[str, Any]):
        """Store the result of a step for later reference"""
        self.step_results[step_index] = result
        logger.info(f"[{self.execution_id}] Stored result for step {step_index}")
        
    def get_step_result(self, step_index: int) -> Optional[Dict[str, Any]]:
        """Retrieve the result of a previous step"""
        return self.step_results.get(step_index)
    
    def set_variable(self, name: str, value: Any):
        """Set a variable in the context"""
        self.variables[name] = value
        logger.info(f"[{self.execution_id}] Set variable '{name}' = {value}")
    
    def get_variable(self, name: str) -> Any:
        """Get a variable from the context"""
        return self.variables.get(name)
    
    def extract_variables_from_step_result(self, step_index: int, step_result: Dict[str, Any]):
        """
        Extract variables from a step result and store them in context
        
        For asset-query results, extracts:
        - assets: List of all assets
        - hostnames: List of hostnames
        - ip_addresses: List of IP addresses
        - asset_count: Number of assets found
        """
        try:
            # Check if this is an asset-query result
            if step_result.get("tool") in ["asset-query", "asset_query"]:
                output = step_result.get("output", {})
                
                # Extract assets from the result
                assets = output.get("assets", [])
                
                if assets:
                    # Store the full assets list
                    self.set_variable("assets", assets)
                    self.set_variable("asset_count", len(assets))
                    
                    # Extract hostnames and IPs
                    hostnames = []
                    ip_addresses = []
                    
                    for asset in assets:
                        if asset.get("hostname"):
                            hostnames.append(asset["hostname"])
                        if asset.get("ip_address"):
                            ip_addresses.append(asset["ip_address"])
                    
                    self.set_variable("hostnames", hostnames)
                    self.set_variable("ip_addresses", ip_addresses)
                    
                    logger.info(f"[{self.execution_id}] Extracted {len(assets)} assets from step {step_index}")
                    logger.info(f"[{self.execution_id}] Hostnames: {hostnames}")
                    logger.info(f"[{self.execution_id}] IPs: {ip_addresses}")
                else:
                    logger.warning(f"[{self.execution_id}] No assets found in step {step_index} result")
                    self.set_variable("assets", [])
                    self.set_variable("asset_count", 0)
                    self.set_variable("hostnames", [])
                    self.set_variable("ip_addresses", [])
            
            # Store the raw result for custom variable extraction
            self.set_variable(f"step_{step_index}_result", step_result)
            
        except Exception as e:
            logger.error(f"[{self.execution_id}] Error extracting variables from step {step_index}: {e}", exc_info=True)
    
    def find_template_variables(self, text: str) -> List[str]:
        """
        Find all template variables in a string
        
        Template variables use {{variable_name}} syntax
        
        Returns:
            List of variable names (without the {{ }})
        """
        pattern = r'\{\{([^}]+)\}\}'
        matches = re.findall(pattern, text)
        return [m.strip() for m in matches]
    
    def resolve_template_variable(self, var_name: str) -> Any:
        """
        Resolve a template variable to its value
        
        Supports:
        - Simple variables: {{hostname}}
        - Array access: {{hostnames[0]}}
        - Nested access: {{assets[0].hostname}}
        """
        try:
            # Check if it's a simple variable
            if var_name in self.variables:
                return self.variables[var_name]
            
            # Check for array access: variable[index]
            array_match = re.match(r'(\w+)\[(\d+)\]', var_name)
            if array_match:
                var_base = array_match.group(1)
                index = int(array_match.group(2))
                
                if var_base in self.variables:
                    value = self.variables[var_base]
                    if isinstance(value, list) and 0 <= index < len(value):
                        return value[index]
            
            # Check for nested access: variable[index].field
            nested_match = re.match(r'(\w+)\[(\d+)\]\.(\w+)', var_name)
            if nested_match:
                var_base = nested_match.group(1)
                index = int(nested_match.group(2))
                field = nested_match.group(3)
                
                if var_base in self.variables:
                    value = self.variables[var_base]
                    if isinstance(value, list) and 0 <= index < len(value):
                        item = value[index]
                        if isinstance(item, dict) and field in item:
                            return item[field]
            
            logger.warning(f"[{self.execution_id}] Template variable '{var_name}' not found in context")
            return None
            
        except Exception as e:
            logger.error(f"[{self.execution_id}] Error resolving template variable '{var_name}': {e}")
            return None
    
    def resolve_template_string(self, text: str) -> str:
        """
        Resolve all template variables in a string
        
        Example:
            "Connect to {{hostname}}" -> "Connect to server1.example.com"
        """
        if not isinstance(text, str):
            return text
        
        # Find all template variables
        variables = self.find_template_variables(text)
        
        if not variables:
            return text
        
        result = text
        for var_name in variables:
            value = self.resolve_template_variable(var_name)
            if value is not None:
                # Replace the template variable with its value
                result = result.replace(f"{{{{{var_name}}}}}", str(value))
        
        return result
    
    def resolve_template_in_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively resolve template variables in a dictionary
        
        Handles:
        - String values with templates
        - Lists of strings with templates
        - Nested dictionaries
        """
        if not isinstance(data, dict):
            return data
        
        result = {}
        for key, value in data.items():
            if isinstance(value, str):
                result[key] = self.resolve_template_string(value)
            elif isinstance(value, list):
                result[key] = [
                    self.resolve_template_string(item) if isinstance(item, str) else item
                    for item in value
                ]
            elif isinstance(value, dict):
                result[key] = self.resolve_template_in_dict(value)
            else:
                result[key] = value
        
        return result
    
    def detect_loop_execution(self, step: Dict[str, Any]) -> Tuple[bool, Optional[str], Optional[List[Any]]]:
        """
        Detect if a step should be executed in a loop
        
        Returns:
            (is_loop, loop_variable_name, loop_values)
            
        Example:
            If target_hosts = ["{{hostname}}", "{{ip_address}}"] and we have 3 assets,
            returns (True, "asset", [asset1, asset2, asset3])
        """
        try:
            parameters = step.get("inputs", step.get("parameters", {}))
            
            # Check for target_hosts with template variables
            target_hosts = parameters.get("target_hosts", parameters.get("target_host"))
            
            if not target_hosts:
                return False, None, None
            
            # Convert single host to list
            if isinstance(target_hosts, str):
                target_hosts = [target_hosts]
            
            # Check if any target contains template variables
            has_templates = False
            for host in target_hosts:
                if isinstance(host, str) and "{{" in host:
                    has_templates = True
                    break
            
            if not has_templates:
                return False, None, None
            
            # Check if we have assets to loop over
            assets = self.get_variable("assets")
            if assets and isinstance(assets, list) and len(assets) > 0:
                logger.info(f"[{self.execution_id}] Detected loop execution over {len(assets)} assets")
                return True, "asset", assets
            
            return False, None, None
            
        except Exception as e:
            logger.error(f"[{self.execution_id}] Error detecting loop execution: {e}", exc_info=True)
            return False, None, None
    
    def expand_step_for_loop(self, step: Dict[str, Any], loop_items: List[Any]) -> List[Dict[str, Any]]:
        """
        Expand a single step into multiple steps for loop execution
        
        Args:
            step: The step definition with template variables
            loop_items: List of items to loop over (e.g., list of assets)
            
        Returns:
            List of expanded step definitions, one per loop item
        """
        expanded_steps = []
        
        try:
            for index, item in enumerate(loop_items):
                # Create a copy of the step
                expanded_step = deepcopy(step)
                
                # Create a temporary context for this iteration
                temp_context = ExecutionContext(f"{self.execution_id}_loop_{index}")
                
                # If item is a dict (like an asset), add all its fields as variables
                if isinstance(item, dict):
                    for key, value in item.items():
                        temp_context.set_variable(key, value)
                else:
                    # If item is a simple value, use it as the default variable
                    temp_context.set_variable("item", item)
                
                # Resolve templates in the step parameters
                parameters = expanded_step.get("inputs", expanded_step.get("parameters", {}))
                resolved_params = temp_context.resolve_template_in_dict(parameters)
                
                # Handle target_hosts specially - convert list to single target
                if "target_hosts" in resolved_params:
                    target_hosts = resolved_params["target_hosts"]
                    if isinstance(target_hosts, list) and len(target_hosts) > 0:
                        # Use the first resolved value as the target_host
                        resolved_params["target_host"] = target_hosts[0]
                        del resolved_params["target_hosts"]
                
                # Update the step with resolved parameters
                if "inputs" in expanded_step:
                    expanded_step["inputs"] = resolved_params
                else:
                    expanded_step["parameters"] = resolved_params
                
                # Add loop metadata
                expanded_step["_loop_index"] = index
                expanded_step["_loop_total"] = len(loop_items)
                expanded_step["_loop_item"] = item
                
                expanded_steps.append(expanded_step)
                
                logger.info(f"[{self.execution_id}] Expanded step {index + 1}/{len(loop_items)}: {resolved_params.get('target_host', 'unknown')}")
        
        except Exception as e:
            logger.error(f"[{self.execution_id}] Error expanding step for loop: {e}", exc_info=True)
            return [step]  # Return original step if expansion fails
        
        return expanded_steps


def create_execution_context(execution_id: str) -> ExecutionContext:
    """Factory function to create an execution context"""
    return ExecutionContext(execution_id)