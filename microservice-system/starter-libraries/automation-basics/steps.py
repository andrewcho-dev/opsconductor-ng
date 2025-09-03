"""
Automation Basics Step Library
Provides essential automation steps including delays, conditions, loops, and data manipulation
"""

import time
import re
import json
import subprocess
import os
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone


class AutomationBasicsSteps:
    """Automation Basics step implementations"""
    
    def delay(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Pause execution for a specified amount of time"""
        duration = params.get('duration', 5)
        unit = params.get('unit', 'seconds')
        message = params.get('message', '')
        
        try:
            # Convert to seconds
            if unit == 'minutes':
                sleep_time = duration * 60
            elif unit == 'hours':
                sleep_time = duration * 3600
            else:  # seconds
                sleep_time = duration
            
            start_time = time.time()
            
            if message:
                print(f"Waiting: {message}")
            
            time.sleep(sleep_time)
            
            actual_time = time.time() - start_time
            
            return {
                'success': True,
                'duration_requested': duration,
                'unit': unit,
                'duration_actual_seconds': round(actual_time, 2),
                'message': message or f'Waited {duration} {unit}',
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to delay: {str(e)}',
                'duration': duration,
                'unit': unit
            }
    
    def condition_check(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate conditions and branch execution flow"""
        condition_type = params.get('condition_type', 'string_equals')
        left_value = params.get('left_value', '')
        right_value = params.get('right_value', '')
        case_sensitive = params.get('case_sensitive', False)
        custom_script = params.get('custom_script', '')
        
        try:
            result = False
            details = {}
            
            if condition_type == 'string_equals':
                if case_sensitive:
                    result = str(left_value) == str(right_value)
                else:
                    result = str(left_value).lower() == str(right_value).lower()
                details = {
                    'left_value': left_value,
                    'right_value': right_value,
                    'case_sensitive': case_sensitive
                }
            
            elif condition_type == 'string_contains':
                if case_sensitive:
                    result = str(right_value) in str(left_value)
                else:
                    result = str(right_value).lower() in str(left_value).lower()
                details = {
                    'text': left_value,
                    'search_for': right_value,
                    'case_sensitive': case_sensitive
                }
            
            elif condition_type == 'number_equals':
                try:
                    result = float(left_value) == float(right_value)
                    details = {
                        'left_number': float(left_value),
                        'right_number': float(right_value)
                    }
                except ValueError:
                    return {
                        'success': False,
                        'error': 'Invalid numbers for comparison',
                        'left_value': left_value,
                        'right_value': right_value
                    }
            
            elif condition_type == 'number_greater':
                try:
                    result = float(left_value) > float(right_value)
                    details = {
                        'left_number': float(left_value),
                        'right_number': float(right_value)
                    }
                except ValueError:
                    return {
                        'success': False,
                        'error': 'Invalid numbers for comparison',
                        'left_value': left_value,
                        'right_value': right_value
                    }
            
            elif condition_type == 'number_less':
                try:
                    result = float(left_value) < float(right_value)
                    details = {
                        'left_number': float(left_value),
                        'right_number': float(right_value)
                    }
                except ValueError:
                    return {
                        'success': False,
                        'error': 'Invalid numbers for comparison',
                        'left_value': left_value,
                        'right_value': right_value
                    }
            
            elif condition_type == 'file_exists':
                result = os.path.exists(left_value)
                details = {
                    'file_path': left_value,
                    'exists': result
                }
            
            elif condition_type == 'service_running':
                # Check if Windows service is running
                try:
                    cmd = f'Get-Service -Name "{left_value}" | Select-Object Status'
                    proc_result = subprocess.run(
                        ['powershell.exe', '-Command', cmd],
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    result = 'Running' in proc_result.stdout
                    details = {
                        'service_name': left_value,
                        'output': proc_result.stdout.strip()
                    }
                except Exception as e:
                    return {
                        'success': False,
                        'error': f'Failed to check service status: {str(e)}',
                        'service_name': left_value
                    }
            
            elif condition_type == 'custom_script':
                if not custom_script:
                    return {
                        'success': False,
                        'error': 'Custom script is required for custom_script condition type'
                    }
                
                try:
                    # Execute PowerShell script
                    proc_result = subprocess.run(
                        ['powershell.exe', '-Command', custom_script],
                        capture_output=True,
                        text=True,
                        timeout=60
                    )
                    
                    # Consider script successful if exit code is 0
                    result = proc_result.returncode == 0
                    details = {
                        'script': custom_script,
                        'exit_code': proc_result.returncode,
                        'output': proc_result.stdout.strip(),
                        'error': proc_result.stderr.strip()
                    }
                except Exception as e:
                    return {
                        'success': False,
                        'error': f'Failed to execute custom script: {str(e)}',
                        'script': custom_script
                    }
            
            else:
                return {
                    'success': False,
                    'error': f'Unknown condition type: {condition_type}'
                }
            
            return {
                'success': True,
                'condition_type': condition_type,
                'condition_result': result,
                'details': details,
                'branch': 'true' if result else 'false',
                'message': f'Condition evaluated to {result}'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to evaluate condition: {str(e)}',
                'condition_type': condition_type
            }
    
    def set_variable(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Set or modify variables for use in subsequent steps"""
        variable_name = params.get('variable_name', '')
        variable_value = params.get('variable_value', '')
        variable_type = params.get('variable_type', 'string')
        scope = params.get('scope', 'job')
        
        if not variable_name:
            return {
                'success': False,
                'error': 'Variable name is required'
            }
        
        try:
            # Convert value based on type
            converted_value = variable_value
            
            if variable_type == 'number':
                try:
                    converted_value = float(variable_value)
                    if converted_value.is_integer():
                        converted_value = int(converted_value)
                except ValueError:
                    return {
                        'success': False,
                        'error': f'Cannot convert "{variable_value}" to number',
                        'variable_name': variable_name
                    }
            
            elif variable_type == 'boolean':
                converted_value = str(variable_value).lower() in ['true', '1', 'yes', 'on']
            
            elif variable_type == 'json':
                try:
                    converted_value = json.loads(variable_value)
                except json.JSONDecodeError as e:
                    return {
                        'success': False,
                        'error': f'Invalid JSON: {str(e)}',
                        'variable_name': variable_name
                    }
            
            elif variable_type == 'array':
                if isinstance(variable_value, str):
                    # Split by lines or commas
                    if '\\n' in variable_value:
                        converted_value = [line.strip() for line in variable_value.split('\\n') if line.strip()]
                    else:
                        converted_value = [item.strip() for item in variable_value.split(',') if item.strip()]
                else:
                    converted_value = list(variable_value)
            
            # In a real implementation, this would store the variable in the job context
            # For now, we'll just return the variable information
            
            return {
                'success': True,
                'variable_name': variable_name,
                'variable_value': converted_value,
                'variable_type': variable_type,
                'scope': scope,
                'message': f'Variable "{variable_name}" set to {converted_value}',
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to set variable: {str(e)}',
                'variable_name': variable_name
            }
    
    def loop_control(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create loops for repeating operations"""
        loop_type = params.get('loop_type', 'for_count')
        count = params.get('count', 5)
        items = params.get('items', '')
        condition = params.get('condition', '')
        max_iterations = params.get('max_iterations', 100)
        
        try:
            loop_data = {}
            
            if loop_type == 'for_count':
                loop_data = {
                    'type': 'for_count',
                    'iterations': count,
                    'current_iteration': 0,
                    'items': list(range(1, count + 1))
                }
            
            elif loop_type == 'for_each':
                if not items:
                    return {
                        'success': False,
                        'error': 'Items list is required for for_each loop'
                    }
                
                # Parse items (assume newline or comma separated)
                if isinstance(items, str):
                    if '\\n' in items:
                        item_list = [item.strip() for item in items.split('\\n') if item.strip()]
                    else:
                        item_list = [item.strip() for item in items.split(',') if item.strip()]
                else:
                    item_list = list(items)
                
                loop_data = {
                    'type': 'for_each',
                    'items': item_list,
                    'total_items': len(item_list),
                    'current_item_index': 0,
                    'current_item': item_list[0] if item_list else None
                }
            
            elif loop_type in ['while_condition', 'until_condition']:
                if not condition:
                    return {
                        'success': False,
                        'error': f'Condition is required for {loop_type} loop'
                    }
                
                loop_data = {
                    'type': loop_type,
                    'condition': condition,
                    'max_iterations': max_iterations,
                    'current_iteration': 0
                }
            
            else:
                return {
                    'success': False,
                    'error': f'Unknown loop type: {loop_type}'
                }
            
            return {
                'success': True,
                'loop_type': loop_type,
                'loop_data': loop_data,
                'message': f'Loop initialized: {loop_type}',
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to initialize loop: {str(e)}',
                'loop_type': loop_type
            }
    
    def text_manipulation(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Manipulate and transform text data"""
        operation = params.get('operation', 'trim')
        input_text = params.get('input_text', '')
        find_text = params.get('find_text', '')
        replace_text = params.get('replace_text', '')
        start_position = params.get('start_position', 0)
        length = params.get('length', 0)
        separator = params.get('separator', ',')
        
        if not input_text:
            return {
                'success': False,
                'error': 'Input text is required'
            }
        
        try:
            result_text = input_text
            operation_details = {}
            
            if operation == 'uppercase':
                result_text = input_text.upper()
            
            elif operation == 'lowercase':
                result_text = input_text.lower()
            
            elif operation == 'trim':
                result_text = input_text.strip()
            
            elif operation == 'replace':
                if not find_text:
                    return {
                        'success': False,
                        'error': 'Find text is required for replace operation'
                    }
                result_text = input_text.replace(find_text, replace_text)
                operation_details = {
                    'find_text': find_text,
                    'replace_text': replace_text,
                    'replacements_made': input_text.count(find_text)
                }
            
            elif operation == 'substring':
                end_position = start_position + length if length > 0 else len(input_text)
                result_text = input_text[start_position:end_position]
                operation_details = {
                    'start_position': start_position,
                    'end_position': end_position,
                    'length': len(result_text)
                }
            
            elif operation == 'split':
                result_text = input_text.split(separator)
                operation_details = {
                    'separator': separator,
                    'parts_count': len(result_text)
                }
            
            elif operation == 'join':
                if isinstance(input_text, list):
                    result_text = separator.join(str(item) for item in input_text)
                else:
                    # Assume input is separated text that needs to be re-joined
                    parts = input_text.split()
                    result_text = separator.join(parts)
                operation_details = {
                    'separator': separator
                }
            
            elif operation == 'regex_match':
                if not find_text:
                    return {
                        'success': False,
                        'error': 'Regex pattern is required for regex_match operation'
                    }
                
                try:
                    matches = re.findall(find_text, input_text)
                    result_text = matches
                    operation_details = {
                        'pattern': find_text,
                        'matches_found': len(matches)
                    }
                except re.error as e:
                    return {
                        'success': False,
                        'error': f'Invalid regex pattern: {str(e)}',
                        'pattern': find_text
                    }
            
            elif operation == 'regex_replace':
                if not find_text:
                    return {
                        'success': False,
                        'error': 'Regex pattern is required for regex_replace operation'
                    }
                
                try:
                    result_text = re.sub(find_text, replace_text, input_text)
                    operation_details = {
                        'pattern': find_text,
                        'replacement': replace_text
                    }
                except re.error as e:
                    return {
                        'success': False,
                        'error': f'Invalid regex pattern: {str(e)}',
                        'pattern': find_text
                    }
            
            else:
                return {
                    'success': False,
                    'error': f'Unknown operation: {operation}'
                }
            
            return {
                'success': True,
                'operation': operation,
                'input_text': input_text,
                'result_text': result_text,
                'operation_details': operation_details,
                'message': f'Text manipulation completed: {operation}'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to manipulate text: {str(e)}',
                'operation': operation
            }
    
    def log_message(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Log messages with different severity levels"""
        message = params.get('message', '')
        level = params.get('level', 'INFO')
        include_timestamp = params.get('include_timestamp', True)
        include_variables = params.get('include_variables', False)
        
        if not message:
            return {
                'success': False,
                'error': 'Log message is required'
            }
        
        try:
            timestamp = datetime.now(timezone.utc).isoformat() if include_timestamp else None
            
            # Format log message
            log_parts = []
            
            if timestamp:
                log_parts.append(f'[{timestamp}]')
            
            log_parts.append(f'[{level}]')
            log_parts.append(message)
            
            if include_variables:
                # In a real implementation, this would include actual job variables
                log_parts.append('[Variables: job_id=123, step_count=5]')
            
            formatted_message = ' '.join(log_parts)
            
            # In a real implementation, this would write to the actual log system
            print(formatted_message)
            
            return {
                'success': True,
                'message': message,
                'level': level,
                'formatted_message': formatted_message,
                'timestamp': timestamp,
                'logged_at': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to log message: {str(e)}',
                'message': message,
                'level': level
            }


# Export step implementations
def get_step_implementations():
    """Return dictionary of step implementations"""
    steps = AutomationBasicsSteps()
    return {
        'delay': steps.delay,
        'condition_check': steps.condition_check,
        'set_variable': steps.set_variable,
        'loop_control': steps.loop_control,
        'text_manipulation': steps.text_manipulation,
        'log_message': steps.log_message
    }