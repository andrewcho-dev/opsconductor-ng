"""
Response Parser for LLM Outputs
Parses and validates LLM responses for different pipeline stages
"""

import json
import re
from typing import Dict, Any, List, Optional, Union
from pydantic import ValidationError

class ResponseParser:
    """Parses and validates LLM responses"""
    
    @staticmethod
    def parse_json_response(response: str) -> Dict[str, Any]:
        """
        Parse JSON response from LLM
        
        Args:
            response: Raw LLM response string
            
        Returns:
            Parsed JSON dictionary
            
        Raises:
            ValueError: If JSON is invalid
        """
        # Clean the response - remove markdown code blocks if present
        cleaned = response.strip()
        
        # Remove markdown code block markers
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        
        cleaned = cleaned.strip()
        
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            # Try to extract JSON from the response using regex
            json_match = re.search(r'\{.*\}', cleaned, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass
            
            raise ValueError(f"Invalid JSON response: {e}")
    
    @staticmethod
    def parse_intent_response(response: str) -> Dict[str, Any]:
        """
        Parse intent classification response
        
        Args:
            response: Raw LLM response
            
        Returns:
            Dictionary with category, action, confidence, and capabilities
            
        Raises:
            ValueError: If response format is invalid
        """
        try:
            data = ResponseParser.parse_json_response(response)
            
            # Validate required fields
            required_fields = ["category", "action", "confidence"]
            for field in required_fields:
                if field not in data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Validate confidence is a number between 0 and 1
            confidence = data["confidence"]
            if not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
                raise ValueError(f"Invalid confidence value: {confidence}")
            
            # Capabilities is optional but should be a list if present
            capabilities = data.get("capabilities", [])
            if not isinstance(capabilities, list):
                raise ValueError(f"capabilities must be a list, got: {type(capabilities)}")
            
            return {
                "category": str(data["category"]).lower(),
                "action": str(data["action"]).lower(),
                "confidence": float(confidence),
                "capabilities": [str(cap).lower() for cap in capabilities]
            }
            
        except Exception as e:
            raise ValueError(f"Failed to parse intent response: {e}")
    
    @staticmethod
    def parse_entities_response(response: str) -> List[Dict[str, Any]]:
        """
        Parse entity extraction response
        
        Args:
            response: Raw LLM response
            
        Returns:
            List of entity dictionaries
            
        Raises:
            ValueError: If response format is invalid
        """
        try:
            # Handle empty response
            cleaned = response.strip()
            if not cleaned or cleaned == "[]":
                return []
            
            data = ResponseParser.parse_json_response(response)
            
            # Ensure it's a list
            if not isinstance(data, list):
                raise ValueError("Entities response must be a list")
            
            entities = []
            for entity in data:
                # Validate required fields
                required_fields = ["type", "value", "confidence"]
                for field in required_fields:
                    if field not in entity:
                        raise ValueError(f"Missing required field in entity: {field}")
                
                # Validate confidence
                confidence = entity["confidence"]
                if not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
                    raise ValueError(f"Invalid confidence value in entity: {confidence}")
                
                entities.append({
                    "type": str(entity["type"]).lower(),
                    "value": str(entity["value"]),
                    "confidence": float(confidence)
                })
            
            return entities
            
        except Exception as e:
            raise ValueError(f"Failed to parse entities response: {e}")
    
    @staticmethod
    def parse_confidence_response(response: str) -> float:
        """
        Parse confidence scoring response
        
        Args:
            response: Raw LLM response
            
        Returns:
            Confidence score as float
            
        Raises:
            ValueError: If response format is invalid
        """
        try:
            cleaned = response.strip()
            
            # Try to extract number from response
            number_match = re.search(r'(\d+\.?\d*)', cleaned)
            if number_match:
                confidence = float(number_match.group(1))
                
                # Ensure it's between 0 and 1
                if confidence > 1.0:
                    confidence = confidence / 100.0  # Convert percentage to decimal
                
                if not 0 <= confidence <= 1:
                    raise ValueError(f"Confidence must be between 0 and 1: {confidence}")
                
                return confidence
            
            raise ValueError("No valid number found in response")
            
        except Exception as e:
            raise ValueError(f"Failed to parse confidence response: {e}")
    
    @staticmethod
    def parse_risk_response(response: str) -> str:
        """
        Parse risk assessment response
        
        Args:
            response: Raw LLM response
            
        Returns:
            Risk level string
            
        Raises:
            ValueError: If response format is invalid
        """
        try:
            cleaned = response.strip().lower()
            
            # Valid risk levels
            valid_risks = ["low", "medium", "high", "critical"]
            
            # Check if response contains a valid risk level
            for risk in valid_risks:
                if risk in cleaned:
                    return risk
            
            raise ValueError(f"No valid risk level found in response: {cleaned}")
            
        except Exception as e:
            raise ValueError(f"Failed to parse risk response: {e}")
    
    @staticmethod
    def parse_tool_selection(response: str) -> Dict[str, Any]:
        """
        Parse tool selection response from Stage B
        
        Args:
            response: Raw LLM response with tool selection
            
        Returns:
            Parsed tool selection data
            
        Raises:
            ValueError: If response format is invalid
        """
        try:
            # Parse JSON response
            data = ResponseParser.parse_json_response(response)
            
            # Validate required fields
            if "selected_tools" not in data:
                raise ValueError("Missing 'selected_tools' field in response")
            
            selected_tools = data["selected_tools"]
            if not isinstance(selected_tools, list):
                raise ValueError("'selected_tools' must be a list")
            
            # Validate each selected tool
            for i, tool in enumerate(selected_tools):
                if not isinstance(tool, dict):
                    raise ValueError(f"Tool {i} must be a dictionary")
                
                required_fields = ["tool_name", "justification"]
                for field in required_fields:
                    if field not in tool:
                        raise ValueError(f"Tool {i} missing required field: {field}")
                
                # Set defaults for optional fields
                tool.setdefault("inputs_needed", [])
                tool.setdefault("execution_order", i + 1)
                tool.setdefault("depends_on", [])
                
                # Validate field types
                if not isinstance(tool["tool_name"], str):
                    raise ValueError(f"Tool {i} 'tool_name' must be a string")
                if not isinstance(tool["justification"], str):
                    raise ValueError(f"Tool {i} 'justification' must be a string")
                if not isinstance(tool["inputs_needed"], list):
                    raise ValueError(f"Tool {i} 'inputs_needed' must be a list")
                if not isinstance(tool["execution_order"], int):
                    tool["execution_order"] = int(tool["execution_order"])
                if not isinstance(tool["depends_on"], list):
                    raise ValueError(f"Tool {i} 'depends_on' must be a list")
            
            return data
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in tool selection response: {e}")
        except Exception as e:
            raise ValueError(f"Failed to parse tool selection response: {e}")
    
    @staticmethod
    def parse_planning_response(response: str) -> Dict[str, Any]:
        """
        Parse planning response from Stage C
        
        Args:
            response: Raw LLM response with execution plan
            
        Returns:
            Parsed planning data
            
        Raises:
            ValueError: If response format is invalid
        """
        try:
            # Parse JSON response
            data = ResponseParser.parse_json_response(response)
            
            # Validate required fields
            required_fields = ["steps", "safety_checks", "rollback_plan"]
            for field in required_fields:
                if field not in data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Validate steps
            steps = data["steps"]
            if not isinstance(steps, list):
                raise ValueError("'steps' must be a list")
            
            for i, step in enumerate(steps):
                if not isinstance(step, dict):
                    raise ValueError(f"Step {i} must be a dictionary")
                
                step_required = ["id", "description", "tool", "estimated_duration"]
                for field in step_required:
                    if field not in step:
                        raise ValueError(f"Step {i} missing required field: {field}")
                
                # Set defaults for optional fields
                step.setdefault("inputs", {})
                step.setdefault("preconditions", [])
                step.setdefault("success_criteria", [])
                step.setdefault("failure_handling", "Log error and continue")
                step.setdefault("depends_on", [])
                
                # Validate types
                if not isinstance(step["estimated_duration"], int):
                    try:
                        step["estimated_duration"] = int(step["estimated_duration"])
                    except ValueError:
                        raise ValueError(f"Step {i} 'estimated_duration' must be an integer")
            
            # Validate safety checks
            safety_checks = data["safety_checks"]
            if not isinstance(safety_checks, list):
                raise ValueError("'safety_checks' must be a list")
            
            for i, check in enumerate(safety_checks):
                if not isinstance(check, dict):
                    raise ValueError(f"Safety check {i} must be a dictionary")
                
                check_required = ["check", "stage", "failure_action"]
                for field in check_required:
                    if field not in check:
                        raise ValueError(f"Safety check {i} missing required field: {field}")
                
                # Validate stage values
                valid_stages = ["before", "during", "after"]
                if check["stage"] not in valid_stages:
                    raise ValueError(f"Safety check {i} 'stage' must be one of: {valid_stages}")
                
                # Validate failure action values
                valid_actions = ["abort", "warn", "continue"]
                if check["failure_action"] not in valid_actions:
                    raise ValueError(f"Safety check {i} 'failure_action' must be one of: {valid_actions}")
            
            # Validate rollback plan
            rollback_plan = data["rollback_plan"]
            if not isinstance(rollback_plan, list):
                raise ValueError("'rollback_plan' must be a list")
            
            for i, rollback in enumerate(rollback_plan):
                if not isinstance(rollback, dict):
                    raise ValueError(f"Rollback {i} must be a dictionary")
                
                rollback_required = ["step_id", "rollback_action"]
                for field in rollback_required:
                    if field not in rollback:
                        raise ValueError(f"Rollback {i} missing required field: {field}")
            
            return data
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in planning response: {e}")
        except Exception as e:
            raise ValueError(f"Failed to parse planning response: {e}")
    
    @staticmethod
    def validate_response_format(response: str, expected_type: str) -> bool:
        """
        Validate response format without parsing
        
        Args:
            response: Raw LLM response
            expected_type: Expected response type (json, number, text)
            
        Returns:
            True if format is valid, False otherwise
        """
        try:
            if expected_type == "json":
                ResponseParser.parse_json_response(response)
            elif expected_type == "number":
                float(response.strip())
            elif expected_type == "text":
                return len(response.strip()) > 0
            else:
                return False
            
            return True
        except:
            return False