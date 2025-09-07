"""
Webhook Execution Utility
Handles webhook calls with payload templating, signature generation, and response processing
"""

import json
import requests
import hmac
import hashlib
from typing import Dict, Any, Optional
from jinja2 import Template
from datetime import datetime
import sys
import os

# Add shared module to path
sys.path.append('/home/opsconductor')
from shared.logging import get_logger

logger = get_logger("executor.webhook")

class WebhookExecutor:
    """Handles webhook execution with payload templating and signature support"""
    
    def __init__(self):
        self.session = requests.Session()
    
    def execute_webhook_call(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute webhook call with full feature support
        
        Args:
            step: Step execution context with job definition and parameters
            
        Returns:
            Dict containing execution results and metrics
        """
        try:
            # Parse step context
            job_definition = json.loads(step['job_definition'])
            run_parameters = json.loads(step['run_parameters'])
            
            # Add current timestamp to parameters
            run_parameters['current_timestamp'] = datetime.utcnow().isoformat()
            
            step_definition = job_definition['steps'][step['idx']]
            
            # Prepare webhook components
            url = self._render_webhook_url(step_definition, run_parameters)
            payload = self._prepare_webhook_payload(step_definition, run_parameters)
            headers = self._prepare_webhook_headers(step_definition, run_parameters, payload)
            
            # Configure webhook options
            webhook_config = self._build_webhook_config(step_definition)
            
            # Execute the webhook
            start_time = datetime.utcnow()
            response = self._execute_webhook_request(url, payload, headers, webhook_config)
            end_time = datetime.utcnow()
            
            # Process response
            result = self._process_webhook_response(response, start_time, end_time, step_definition)
            
            logger.info(f"Webhook call completed: {url} -> {response.status_code}")
            return result
            
        except Exception as e:
            logger.error(f"Webhook execution failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'status_code': None,
                'response_body': None,
                'response_headers': {},
                'execution_time_ms': 0
            }
    
    def _render_webhook_url(self, step_definition: Dict[str, Any], run_parameters: Dict[str, Any]) -> str:
        """Render webhook URL template with parameters"""
        url_template = Template(step_definition['url'])
        return url_template.render(**run_parameters)
    
    def _prepare_webhook_payload(self, step_definition: Dict[str, Any], run_parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare and render webhook payload"""
        payload_data = step_definition.get('payload', {})
        
        if isinstance(payload_data, dict):
            # Render payload templates
            rendered_payload = {}
            for key, value in payload_data.items():
                if isinstance(value, str):
                    value_template = Template(value)
                    rendered_payload[key] = value_template.render(**run_parameters)
                elif isinstance(value, dict):
                    # Recursively render nested objects
                    rendered_payload[key] = self._render_nested_payload(value, run_parameters)
                else:
                    rendered_payload[key] = value
            return rendered_payload
        else:
            return payload_data or {}
    
    def _render_nested_payload(self, payload_obj: Dict[str, Any], run_parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively render nested payload objects"""
        rendered = {}
        for key, value in payload_obj.items():
            if isinstance(value, str):
                value_template = Template(value)
                rendered[key] = value_template.render(**run_parameters)
            elif isinstance(value, dict):
                rendered[key] = self._render_nested_payload(value, run_parameters)
            elif isinstance(value, list):
                rendered[key] = [
                    self._render_nested_payload(item, run_parameters) if isinstance(item, dict)
                    else Template(str(item)).render(**run_parameters) if isinstance(item, str)
                    else item
                    for item in value
                ]
            else:
                rendered[key] = value
        return rendered
    
    def _prepare_webhook_headers(self, step_definition: Dict[str, Any], run_parameters: Dict[str, Any], payload: Dict[str, Any]) -> Dict[str, str]:
        """Prepare webhook headers including signatures"""
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'OpsConductor-Webhook/1.0'
        }
        
        # Add custom headers
        custom_headers = step_definition.get('headers', {})
        for key, value in custom_headers.items():
            if isinstance(value, str):
                header_template = Template(value)
                headers[key] = header_template.render(**run_parameters)
            else:
                headers[key] = str(value)
        
        # Add webhook signature if secret is provided
        secret = step_definition.get('secret')
        if secret:
            signature = self._generate_webhook_signature(payload, secret, run_parameters)
            headers['X-Webhook-Signature'] = signature
            headers['X-Hub-Signature-256'] = f"sha256={signature}"
        
        return headers
    
    def _generate_webhook_signature(self, payload: Dict[str, Any], secret: str, run_parameters: Dict[str, Any]) -> str:
        """Generate webhook signature for payload verification"""
        # Render secret template if it contains variables
        if isinstance(secret, str) and '{{' in secret:
            secret_template = Template(secret)
            secret = secret_template.render(**run_parameters)
        
        # Create signature
        payload_json = json.dumps(payload, sort_keys=True)
        signature = hmac.new(
            secret.encode('utf-8'),
            payload_json.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return signature
    
    def _build_webhook_config(self, step_definition: Dict[str, Any]) -> Dict[str, Any]:
        """Build webhook configuration options"""
        return {
            'timeout': step_definition.get('timeout_sec', 30),
            'verify': step_definition.get('ssl_verify', True),
            'allow_redirects': step_definition.get('allow_redirects', True),
            'retry_count': step_definition.get('retry_count', 0),
            'retry_delay': step_definition.get('retry_delay_sec', 1)
        }
    
    def _execute_webhook_request(self, url: str, payload: Dict[str, Any], headers: Dict[str, str], config: Dict[str, Any]) -> requests.Response:
        """Execute the webhook request with retry logic"""
        payload_json = json.dumps(payload)
        
        for attempt in range(config['retry_count'] + 1):
            try:
                response = self.session.post(
                    url=url,
                    data=payload_json,
                    headers=headers,
                    timeout=config['timeout'],
                    verify=config['verify'],
                    allow_redirects=config['allow_redirects']
                )
                
                # If successful or client error (4xx), don't retry
                if response.status_code < 500:
                    return response
                
                # Server error (5xx) - retry if attempts remaining
                if attempt < config['retry_count']:
                    logger.warning(f"Webhook attempt {attempt + 1} failed with {response.status_code}, retrying...")
                    import time
                    time.sleep(config['retry_delay'])
                    continue
                
                return response
                
            except requests.RequestException as e:
                if attempt < config['retry_count']:
                    logger.warning(f"Webhook attempt {attempt + 1} failed with exception: {e}, retrying...")
                    import time
                    time.sleep(config['retry_delay'])
                    continue
                raise
        
        # This shouldn't be reached, but just in case
        raise Exception("All webhook retry attempts failed")
    
    def _process_webhook_response(self, response: requests.Response, start_time: datetime, 
                                 end_time: datetime, step_definition: Dict[str, Any]) -> Dict[str, Any]:
        """Process webhook response and extract relevant data"""
        execution_time_ms = int((end_time - start_time).total_seconds() * 1000)
        
        # Get response body safely
        try:
            response_body = response.text
        except Exception:
            response_body = "<Unable to decode response body>"
        
        # Determine success based on status code
        expected_codes = step_definition.get('expected_status_codes', [200, 201, 202, 204])
        if not isinstance(expected_codes, list):
            expected_codes = [expected_codes]
        
        success = response.status_code in expected_codes
        
        # Extract response headers
        response_headers = dict(response.headers)
        
        # Parse response content
        parsed_response = self._parse_webhook_response_content(response)
        
        # Extract webhook-specific metadata
        webhook_metadata = self._extract_webhook_metadata(response)
        
        return {
            'success': success,
            'status_code': response.status_code,
            'response_body': response_body,
            'parsed_response': parsed_response,
            'response_headers': response_headers,
            'execution_time_ms': execution_time_ms,
            'url': response.url,
            'webhook_metadata': webhook_metadata
        }
    
    def _parse_webhook_response_content(self, response: requests.Response) -> Any:
        """Parse webhook response content"""
        content_type = response.headers.get('content-type', '').lower()
        
        try:
            if 'application/json' in content_type:
                return response.json()
            else:
                return response.text
        except Exception as e:
            logger.warning(f"Failed to parse webhook response content: {e}")
            return response.text
    
    def _extract_webhook_metadata(self, response: requests.Response) -> Dict[str, Any]:
        """Extract webhook-specific metadata from response"""
        metadata = {}
        
        # Common webhook response headers
        webhook_headers = [
            'x-webhook-id',
            'x-delivery-id', 
            'x-github-delivery',
            'x-hub-signature',
            'x-event-key'
        ]
        
        for header in webhook_headers:
            value = response.headers.get(header)
            if value:
                metadata[header.replace('-', '_')] = value
        
        return metadata
    
    def close(self):
        """Close the HTTP session"""
        if self.session:
            self.session.close()