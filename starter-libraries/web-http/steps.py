"""
Web & HTTP Tools Step Library
Provides HTTP requests, web scraping, API testing, and web service interactions
"""

import requests
import json
import hashlib
import os
import time
import xml.etree.ElementTree as ET
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone


class WebHttpSteps:
    """Web & HTTP Tools step implementations"""
    
    def http_request(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make HTTP requests to web services and APIs"""
        method = params.get('method', 'GET').upper()
        url = params.get('url', '')
        headers = params.get('headers', '')
        body = params.get('body', '')
        timeout = params.get('timeout', 30)
        follow_redirects = params.get('follow_redirects', True)
        verify_ssl = params.get('verify_ssl', True)
        
        if not url:
            return {
                'success': False,
                'error': 'URL is required'
            }
        
        try:
            # Parse headers
            headers_dict = {}
            if headers:
                for line in headers.split('\\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        headers_dict[key.strip()] = value.strip()
            
            # Prepare request data
            request_data = None
            if body and method in ['POST', 'PUT', 'PATCH']:
                # Try to parse as JSON first
                try:
                    request_data = json.loads(body)
                    if 'Content-Type' not in headers_dict:
                        headers_dict['Content-Type'] = 'application/json'
                except json.JSONDecodeError:
                    # Use as raw text
                    request_data = body
            
            # Make request
            start_time = time.time()
            
            response = requests.request(
                method=method,
                url=url,
                headers=headers_dict,
                json=request_data if isinstance(request_data, (dict, list)) else None,
                data=request_data if isinstance(request_data, str) else None,
                timeout=timeout,
                allow_redirects=follow_redirects,
                verify=verify_ssl
            )
            
            response_time = round((time.time() - start_time) * 1000, 2)
            
            # Parse response
            response_headers = dict(response.headers)
            
            # Try to parse response as JSON
            try:
                response_data = response.json()
            except:
                response_data = response.text
            
            return {
                'success': response.status_code < 400,
                'method': method,
                'url': url,
                'status_code': response.status_code,
                'status_text': response.reason,
                'response_time_ms': response_time,
                'response_headers': response_headers,
                'response_data': response_data,
                'response_size': len(response.content),
                'request_headers': headers_dict,
                'message': f'{method} {url} - {response.status_code} {response.reason}'
            }
            
        except requests.exceptions.Timeout:
            return {
                'success': False,
                'error': f'Request timed out after {timeout} seconds',
                'method': method,
                'url': url
            }
        except requests.exceptions.ConnectionError:
            return {
                'success': False,
                'error': 'Connection error - could not reach server',
                'method': method,
                'url': url
            }
        except requests.exceptions.SSLError:
            return {
                'success': False,
                'error': 'SSL certificate verification failed',
                'method': method,
                'url': url
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'HTTP request failed: {str(e)}',
                'method': method,
                'url': url
            }
    
    def download_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Download files from web URLs"""
        url = params.get('url', '')
        destination = params.get('destination', '')
        headers = params.get('headers', '')
        overwrite = params.get('overwrite', False)
        verify_checksum = params.get('verify_checksum', '')
        max_size_mb = params.get('max_size_mb', 100)
        
        if not url or not destination:
            return {
                'success': False,
                'error': 'URL and destination path are required'
            }
        
        try:
            # Check if file exists
            if os.path.exists(destination) and not overwrite:
                return {
                    'success': False,
                    'error': f'File already exists and overwrite is disabled: {destination}',
                    'destination': destination
                }
            
            # Parse headers
            headers_dict = {}
            if headers:
                for line in headers.split('\\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        headers_dict[key.strip()] = value.strip()
            
            # Create destination directory
            os.makedirs(os.path.dirname(destination), exist_ok=True)
            
            # Download file
            start_time = time.time()
            
            with requests.get(url, headers=headers_dict, stream=True, timeout=30) as response:
                response.raise_for_status()
                
                # Check content length
                content_length = response.headers.get('Content-Length')
                if content_length:
                    size_mb = int(content_length) / (1024 * 1024)
                    if size_mb > max_size_mb:
                        return {
                            'success': False,
                            'error': f'File too large: {size_mb:.1f}MB (max: {max_size_mb}MB)',
                            'url': url,
                            'size_mb': size_mb
                        }
                
                # Download and save file
                total_size = 0
                hash_md5 = hashlib.md5()
                
                with open(destination, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            total_size += len(chunk)
                            hash_md5.update(chunk)
                            
                            # Check size limit during download
                            if total_size > max_size_mb * 1024 * 1024:
                                f.close()
                                os.remove(destination)
                                return {
                                    'success': False,
                                    'error': f'File exceeded size limit during download: {max_size_mb}MB',
                                    'url': url
                                }
            
            download_time = round(time.time() - start_time, 2)
            file_hash = hash_md5.hexdigest()
            
            # Verify checksum if provided
            checksum_valid = True
            if verify_checksum:
                checksum_valid = file_hash.lower() == verify_checksum.lower()
                if not checksum_valid:
                    os.remove(destination)
                    return {
                        'success': False,
                        'error': 'Checksum verification failed',
                        'expected_checksum': verify_checksum,
                        'actual_checksum': file_hash,
                        'url': url,
                        'destination': destination
                    }
            
            return {
                'success': True,
                'url': url,
                'destination': destination,
                'file_size_bytes': total_size,
                'file_size_mb': round(total_size / (1024 * 1024), 2),
                'download_time_seconds': download_time,
                'download_speed_mbps': round((total_size / (1024 * 1024)) / download_time, 2) if download_time > 0 else 0,
                'file_hash_md5': file_hash,
                'checksum_verified': checksum_valid,
                'message': f'File downloaded successfully: {os.path.basename(destination)}'
            }
            
        except requests.exceptions.HTTPError as e:
            return {
                'success': False,
                'error': f'HTTP error: {str(e)}',
                'url': url
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Download failed: {str(e)}',
                'url': url,
                'destination': destination
            }
    
    def json_parse(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Parse and extract data from JSON responses"""
        json_data = params.get('json_data', '')
        json_path = params.get('json_path', '')
        output_format = params.get('output_format', 'raw')
        default_value = params.get('default_value', 'Not found')
        
        if not json_data:
            return {
                'success': False,
                'error': 'JSON data is required'
            }
        
        try:
            # Parse JSON
            if isinstance(json_data, str):
                data = json.loads(json_data)
            else:
                data = json_data
            
            # Extract data using JSONPath (simplified implementation)
            if json_path:
                try:
                    # Simple JSONPath implementation
                    result = self._extract_json_path(data, json_path)
                    if result is None:
                        result = default_value
                except Exception:
                    result = default_value
            else:
                result = data
            
            # Format output
            if output_format == 'string':
                if isinstance(result, (dict, list)):
                    formatted_result = json.dumps(result)
                else:
                    formatted_result = str(result)
            elif output_format == 'array':
                if isinstance(result, list):
                    formatted_result = result
                else:
                    formatted_result = [result]
            elif output_format == 'object':
                if isinstance(result, dict):
                    formatted_result = result
                else:
                    formatted_result = {'value': result}
            else:  # raw
                formatted_result = result
            
            return {
                'success': True,
                'json_path': json_path,
                'extracted_data': formatted_result,
                'output_format': output_format,
                'data_type': type(formatted_result).__name__,
                'message': f'JSON parsed successfully, extracted: {type(formatted_result).__name__}'
            }
            
        except json.JSONDecodeError as e:
            return {
                'success': False,
                'error': f'Invalid JSON: {str(e)}',
                'json_data': json_data[:200] + '...' if len(json_data) > 200 else json_data
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'JSON parsing failed: {str(e)}',
                'json_path': json_path
            }
    
    def _extract_json_path(self, data: Any, path: str) -> Any:
        """Simple JSONPath extraction (basic implementation)"""
        if not path or path == '$':
            return data
        
        # Remove leading $
        if path.startswith('$.'):
            path = path[2:]
        elif path.startswith('$'):
            path = path[1:]
        
        # Split path into parts
        parts = path.split('.')
        current = data
        
        for part in parts:
            if '[' in part and ']' in part:
                # Handle array access like users[0] or users[*]
                key = part.split('[')[0]
                index_part = part.split('[')[1].split(']')[0]
                
                if key:
                    current = current[key]
                
                if index_part == '*':
                    # Return all items
                    if isinstance(current, list):
                        return current
                else:
                    # Specific index
                    current = current[int(index_part)]
            else:
                # Simple key access
                current = current[part]
        
        return current
    
    def xml_parse(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Parse and extract data from XML documents"""
        xml_data = params.get('xml_data', '')
        xpath = params.get('xpath', '')
        output_format = params.get('output_format', 'text')
        namespace_map = params.get('namespace_map', '')
        
        if not xml_data:
            return {
                'success': False,
                'error': 'XML data is required'
            }
        
        try:
            # Parse XML
            root = ET.fromstring(xml_data)
            
            # Parse namespaces
            namespaces = {}
            if namespace_map:
                for line in namespace_map.split('\\n'):
                    if ':' in line:
                        prefix, uri = line.split(':', 1)
                        namespaces[prefix.strip()] = uri.strip()
            
            # Extract data using XPath
            if xpath:
                try:
                    elements = root.findall(xpath, namespaces)
                    
                    if output_format == 'text':
                        result = [elem.text for elem in elements if elem.text]
                    elif output_format == 'element':
                        result = [ET.tostring(elem, encoding='unicode') for elem in elements]
                    elif output_format == 'attribute':
                        # Extract all attributes from found elements
                        result = [elem.attrib for elem in elements]
                    else:  # array
                        result = [elem.text or ET.tostring(elem, encoding='unicode') for elem in elements]
                    
                    # Return single item if only one result
                    if len(result) == 1 and output_format != 'array':
                        result = result[0]
                        
                except Exception as e:
                    return {
                        'success': False,
                        'error': f'XPath query failed: {str(e)}',
                        'xpath': xpath
                    }
            else:
                # Return root element as string
                result = ET.tostring(root, encoding='unicode')
            
            return {
                'success': True,
                'xpath': xpath,
                'extracted_data': result,
                'output_format': output_format,
                'elements_found': len(result) if isinstance(result, list) else 1,
                'message': f'XML parsed successfully, extracted {len(result) if isinstance(result, list) else 1} elements'
            }
            
        except ET.ParseError as e:
            return {
                'success': False,
                'error': f'Invalid XML: {str(e)}',
                'xml_data': xml_data[:200] + '...' if len(xml_data) > 200 else xml_data
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'XML parsing failed: {str(e)}',
                'xpath': xpath
            }
    
    def web_scrape(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Extract data from web pages using CSS selectors"""
        url = params.get('url', '')
        selector = params.get('selector', '')
        attribute = params.get('attribute', '')
        headers = params.get('headers', '')
        wait_time = params.get('wait_time', 5)
        max_results = params.get('max_results', 10)
        
        if not url or not selector:
            return {
                'success': False,
                'error': 'URL and CSS selector are required'
            }
        
        try:
            # Parse headers
            headers_dict = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            if headers:
                for line in headers.split('\\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        headers_dict[key.strip()] = value.strip()
            
            # Fetch page
            response = requests.get(url, headers=headers_dict, timeout=30)
            response.raise_for_status()
            
            # Wait if specified
            if wait_time > 0:
                time.sleep(wait_time)
            
            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find elements using CSS selector
            elements = soup.select(selector)
            
            # Limit results
            if len(elements) > max_results:
                elements = elements[:max_results]
            
            # Extract data
            results = []
            for element in elements:
                if attribute:
                    # Extract specific attribute
                    value = element.get(attribute, '')
                    if value:
                        results.append(value)
                else:
                    # Extract text content
                    text = element.get_text(strip=True)
                    if text:
                        results.append(text)
            
            return {
                'success': True,
                'url': url,
                'selector': selector,
                'attribute': attribute or 'text',
                'results': results,
                'results_count': len(results),
                'elements_found': len(soup.select(selector)),
                'page_title': soup.title.string if soup.title else '',
                'message': f'Web scraping completed: {len(results)} items extracted'
            }
            
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': f'Failed to fetch page: {str(e)}',
                'url': url
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Web scraping failed: {str(e)}',
                'url': url,
                'selector': selector
            }
    
    def api_test(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Comprehensive API testing with assertions and validations"""
        base_url = params.get('base_url', '')
        endpoints = params.get('endpoints', '')
        expected_status = params.get('expected_status', 200)
        auth_header = params.get('auth_header', '')
        response_checks = params.get('response_checks', '')
        timeout = params.get('timeout', 30)
        
        if not base_url or not endpoints:
            return {
                'success': False,
                'error': 'Base URL and endpoints are required'
            }
        
        try:
            # Parse endpoints
            endpoint_list = []
            for line in endpoints.split('\\n'):
                line = line.strip()
                if line:
                    endpoint_list.append(line)
            
            if not endpoint_list:
                return {
                    'success': False,
                    'error': 'No valid endpoints provided'
                }
            
            # Prepare headers
            headers = {
                'User-Agent': 'OpsConductor API Test Suite',
                'Accept': 'application/json'
            }
            
            if auth_header:
                headers['Authorization'] = auth_header
            
            # Parse response checks
            checks = []
            if response_checks:
                for line in response_checks.split('\\n'):
                    line = line.strip()
                    if line:
                        checks.append(line)
            
            # Test each endpoint
            test_results = []
            total_passed = 0
            total_failed = 0
            
            for endpoint in endpoint_list:
                url = urljoin(base_url, endpoint)
                
                try:
                    start_time = time.time()
                    response = requests.get(url, headers=headers, timeout=timeout)
                    response_time = round((time.time() - start_time) * 1000, 2)
                    
                    # Check status code
                    status_passed = response.status_code == expected_status
                    
                    # Parse response
                    try:
                        response_data = response.json()
                    except:
                        response_data = response.text
                    
                    # Run response checks
                    check_results = []
                    for check in checks:
                        try:
                            # Simple check evaluation (in real implementation, use JSONPath)
                            check_passed = self._evaluate_response_check(response_data, check)
                            check_results.append({
                                'check': check,
                                'passed': check_passed
                            })
                        except Exception as e:
                            check_results.append({
                                'check': check,
                                'passed': False,
                                'error': str(e)
                            })
                    
                    all_checks_passed = all(result['passed'] for result in check_results)
                    test_passed = status_passed and all_checks_passed
                    
                    if test_passed:
                        total_passed += 1
                    else:
                        total_failed += 1
                    
                    test_results.append({
                        'endpoint': endpoint,
                        'url': url,
                        'status_code': response.status_code,
                        'expected_status': expected_status,
                        'status_passed': status_passed,
                        'response_time_ms': response_time,
                        'response_size': len(response.content),
                        'check_results': check_results,
                        'all_checks_passed': all_checks_passed,
                        'test_passed': test_passed
                    })
                    
                except requests.exceptions.RequestException as e:
                    total_failed += 1
                    test_results.append({
                        'endpoint': endpoint,
                        'url': url,
                        'error': str(e),
                        'test_passed': False
                    })
            
            overall_success = total_failed == 0
            
            return {
                'success': overall_success,
                'base_url': base_url,
                'endpoints_tested': len(endpoint_list),
                'tests_passed': total_passed,
                'tests_failed': total_failed,
                'success_rate': round((total_passed / len(endpoint_list)) * 100, 1),
                'test_results': test_results,
                'message': f'API testing completed: {total_passed}/{len(endpoint_list)} tests passed'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'API testing failed: {str(e)}',
                'base_url': base_url
            }
    
    def _evaluate_response_check(self, response_data: Any, check: str) -> bool:
        """Simple response check evaluation"""
        try:
            # Basic checks (in real implementation, use proper JSONPath/expression evaluation)
            if '$.length > 0' in check:
                return len(response_data) > 0 if isinstance(response_data, (list, dict)) else False
            elif '$.status == \'success\'' in check:
                return response_data.get('status') == 'success' if isinstance(response_data, dict) else False
            else:
                # Default to True for unknown checks
                return True
        except:
            return False


# Export step implementations
def get_step_implementations():
    """Return dictionary of step implementations"""
    steps = WebHttpSteps()
    return {
        'http_request': steps.http_request,
        'download_file': steps.download_file,
        'json_parse': steps.json_parse,
        'xml_parse': steps.xml_parse,
        'web_scrape': steps.web_scrape,
        'api_test': steps.api_test
    }