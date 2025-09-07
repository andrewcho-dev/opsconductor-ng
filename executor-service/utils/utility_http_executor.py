"""
HTTP Request Execution Utility
Handles HTTP request execution with authentication, templating, and response processing
"""

import json
import requests
from typing import Dict, Any, Optional, Tuple
from jinja2 import Template
from datetime import datetime
import sys
import os

# Add shared module to path
sys.path.append('/home/opsconductor')
from shared.logging import get_logger

logger = get_logger("executor.http")

class HTTPExecutor:
    """Handles HTTP request execution with advanced features"""
    
    def __init__(self):
        self.session = requests.Session()
    
    def execute_http_request(self, step: Dict[str, Any], method: str) -> Dict[str, Any]:
        """
        Execute HTTP request with full feature support
        
        Args:
            step: Step execution context with job definition and parameters
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            
        Returns:
            Dict containing execution results and metrics
        """
        try:
            # Parse step context
            job_definition = json.loads(step['job_definition'])
            run_parameters = json.loads(step['run_parameters'])
            step_definition = job_definition['steps'][step['idx']]
            
            # Prepare request components
            url = self._render_url(step_definition, run_parameters)
            headers = self._prepare_headers(step_definition, run_parameters)
            request_body = self._prepare_request_body(step_definition, run_parameters, method)
            auth = self._setup_authentication(step_definition, run_parameters)
            
            # Configure request options
            request_config = self._build_request_config(step_definition)
            
            # Execute the request
            start_time = datetime.utcnow()
            response = self._execute_request(method, url, headers, request_body, auth, request_config)
            end_time = datetime.utcnow()
            
            # Process response
            result = self._process_response(response, start_time, end_time, step_definition)
            
            logger.info(f"HTTP {method} request completed: {url} -> {response.status_code}")
            return result
            
        except Exception as e:
            logger.error(f"HTTP request execution failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'status_code': None,
                'response_body': None,
                'response_headers': {},
                'execution_time_ms': 0
            }
    
    def _render_url(self, step_definition: Dict[str, Any], run_parameters: Dict[str, Any]) -> str:
        """Render URL template with parameters"""
        url_template = Template(step_definition['url'])
        return url_template.render(**run_parameters)
    
    def _prepare_headers(self, step_definition: Dict[str, Any], run_parameters: Dict[str, Any]) -> Dict[str, str]:
        """Prepare and render request headers"""
        headers = step_definition.get('headers', {})
        if not isinstance(headers, dict):
            return {}
        
        rendered_headers = {}
        for key, value in headers.items():
            if isinstance(value, str):
                header_template = Template(value)
                rendered_headers[key] = header_template.render(**run_parameters)
            else:
                rendered_headers[key] = str(value)
        
        return rendered_headers
    
    def _prepare_request_body(self, step_definition: Dict[str, Any], run_parameters: Dict[str, Any], method: str) -> Optional[str]:
        """Prepare request body for POST/PUT/PATCH requests"""
        if method not in ['POST', 'PUT', 'PATCH'] or 'body' not in step_definition:
            return None
        
        body_data = step_definition['body']
        
        if isinstance(body_data, str):
            # String template body
            body_template = Template(body_data)
            return body_template.render(**run_parameters)
        
        elif isinstance(body_data, dict):
            # JSON object body - render each value
            rendered_body = {}
            for key, value in body_data.items():
                if isinstance(value, str):
                    value_template = Template(value)
                    rendered_body[key] = value_template.render(**run_parameters)
                else:
                    rendered_body[key] = value
            return json.dumps(rendered_body)
        
        return None
    
    def _setup_authentication(self, step_definition: Dict[str, Any], run_parameters: Dict[str, Any]) -> Optional[Tuple]:
        """Setup request authentication"""
        auth_config = step_definition.get('authentication', {})
        auth_type = auth_config.get('type')
        
        if auth_type == 'basic':
            username_template = Template(auth_config['username'])
            password_template = Template(auth_config['password'])
            username = username_template.render(**run_parameters)
            password = password_template.render(**run_parameters)
            return (username, password)
        
        elif auth_type == 'bearer':
            # Bearer token will be added to headers instead
            return None
        
        return None
    
    def _build_request_config(self, step_definition: Dict[str, Any]) -> Dict[str, Any]:
        """Build request configuration options"""
        return {
            'timeout': step_definition.get('timeout_sec', 30),
            'verify': step_definition.get('ssl_verify', True),
            'allow_redirects': step_definition.get('max_redirects', 5) > 0,
            'max_redirects': step_definition.get('max_redirects', 5)
        }
    
    def _execute_request(self, method: str, url: str, headers: Dict[str, str], 
                        request_body: Optional[str], auth: Optional[Tuple], 
                        config: Dict[str, Any]) -> requests.Response:
        """Execute the actual HTTP request"""
        request_kwargs = {
            'url': url,
            'headers': headers,
            'timeout': config['timeout'],
            'verify': config['verify'],
            'allow_redirects': config['allow_redirects']
        }
        
        if request_body:
            request_kwargs['data'] = request_body
        
        if auth:
            request_kwargs['auth'] = auth
        
        # Execute request based on method
        if method == 'GET':
            return self.session.get(**request_kwargs)
        elif method == 'POST':
            return self.session.post(**request_kwargs)
        elif method == 'PUT':
            return self.session.put(**request_kwargs)
        elif method == 'DELETE':
            return self.session.delete(**request_kwargs)
        elif method == 'PATCH':
            return self.session.patch(**request_kwargs)
        elif method == 'HEAD':
            return self.session.head(**request_kwargs)
        elif method == 'OPTIONS':
            return self.session.options(**request_kwargs)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
    
    def _process_response(self, response: requests.Response, start_time: datetime, 
                         end_time: datetime, step_definition: Dict[str, Any]) -> Dict[str, Any]:
        """Process HTTP response and extract relevant data"""
        execution_time_ms = int((end_time - start_time).total_seconds() * 1000)
        
        # Get response body safely
        try:
            response_body = response.text
        except Exception:
            response_body = "<Unable to decode response body>"
        
        # Determine success based on status code and expected codes
        expected_codes = step_definition.get('expected_status_codes', [200, 201, 202, 204])
        if not isinstance(expected_codes, list):
            expected_codes = [expected_codes]
        
        success = response.status_code in expected_codes
        
        # Extract response headers
        response_headers = dict(response.headers)
        
        # Process response based on content type
        parsed_response = self._parse_response_content(response)
        
        return {
            'success': success,
            'status_code': response.status_code,
            'response_body': response_body,
            'parsed_response': parsed_response,
            'response_headers': response_headers,
            'execution_time_ms': execution_time_ms,
            'url': response.url,
            'request_method': response.request.method if response.request else None
        }
    
    def _parse_response_content(self, response: requests.Response) -> Any:
        """Parse response content based on content type"""
        content_type = response.headers.get('content-type', '').lower()
        
        try:
            if 'application/json' in content_type:
                return response.json()
            elif 'application/xml' in content_type or 'text/xml' in content_type:
                # Could add XML parsing here if needed
                return response.text
            else:
                return response.text
        except Exception as e:
            logger.warning(f"Failed to parse response content: {e}")
            return response.text
    
    def close(self):
        """Close the HTTP session"""
        if self.session:
            self.session.close()