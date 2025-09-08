"""
Template rendering utility module
Handles Jinja2 template rendering for notifications
"""

import jinja2
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

def render_template(template_content: str, payload: Dict[str, Any]) -> str:
    """Render Jinja2 template with payload data"""
    try:
        template = jinja2.Template(template_content)
        return template.render(**payload)
    except Exception as e:
        logger.error(f"Template rendering error: {e}")
        return template_content

def validate_template(template_content: str, sample_payload: Dict[str, Any] = None) -> tuple[bool, str]:
    """Validate template syntax and test rendering"""
    try:
        # Test template compilation
        template = jinja2.Template(template_content)
        
        # Test rendering with sample payload if provided
        if sample_payload:
            rendered = template.render(**sample_payload)
            return True, f"Template valid. Sample render: {rendered[:100]}..."
        else:
            return True, "Template syntax is valid"
            
    except jinja2.TemplateSyntaxError as e:
        return False, f"Template syntax error: {e}"
    except jinja2.UndefinedError as e:
        return False, f"Template variable error: {e}"
    except Exception as e:
        return False, f"Template validation error: {e}"

def get_template_variables(template_content: str) -> list[str]:
    """Extract variable names from template"""
    try:
        env = jinja2.Environment()
        ast = env.parse(template_content)
        variables = jinja2.meta.find_undeclared_variables(ast)
        return list(variables)
    except Exception as e:
        logger.error(f"Error extracting template variables: {e}")
        return []