---
description: "Utility module patterns and standards for OpsConductor services"
globs: ["**/utility_*.py", "**/main.py", "**/*service*/**.py"]
alwaysApply: false
---

# Utility Module Patterns

## 🏗️ Module Structure Standard

All utility modules MUST follow this pattern:

```python
"""
Feature description utility module
Brief description of what this module handles
"""

import logging
from typing import Dict, Any, Optional, List

# Global variables for configuration
CONFIG = {}
db_cursor_func = None

logger = logging.getLogger(__name__)

def set_config(config: Dict[str, Any]) -> None:
    """Set configuration from main module"""
    global CONFIG
    CONFIG.update(config)

def set_db_cursor_func(cursor_func):
    """Set database cursor function from main module"""
    global db_cursor_func
    db_cursor_func = cursor_func

async def main_function(param1: str, param2: Dict[str, Any]) -> bool:
    """Main functionality with proper error handling"""
    try:
        # Implementation here
        logger.info(f"Processing {param1}")
        return True
        
    except Exception as e:
        logger.error(f"Error in main_function: {e}")
        return False
```

## 📝 Naming Conventions

- **Module files**: `utility_feature_name.py`
- **Import alias**: `import utility_feature_name as feature_utility`
- **Functions**: Descriptive names with proper type hints
- **Variables**: Clear, meaningful names

## 🔧 Integration Pattern

In `main.py`:

```python
# Import utility modules
import utility_email_sender as email_utility
import utility_webhook_sender as webhook_utility

# Initialize utilities (after configuration is loaded)
email_utility.set_smtp_config(SMTP_CONFIG)
webhook_utility.set_db_cursor_func(get_db_cursor)

# Use in endpoint functions
@app.post("/feature/action")
async def feature_action(request: Request) -> Dict[str, Any]:
    """Feature action using utility module"""
    await verify_token(request)
    
    result = await email_utility.send_email_notification(id, dest, payload)
    if result:
        return create_success_response("Action completed")
    else:
        raise DatabaseError("Action failed")
```

## 🚨 Error Handling

Utility modules should:
- **Log errors** but not raise HTTP exceptions
- **Return None or False** on failure
- **Let calling endpoints** decide how to handle errors

```python
def utility_function(param: str) -> Optional[Dict[str, Any]]:
    """Utility function with proper error handling"""
    try:
        # Implementation
        return {"result": "success"}
    except Exception as e:
        logger.error(f"Error in utility_function: {e}")
        # Don't raise HTTP errors from utilities
        return None
```

## 🗄️ Database Patterns

```python
async def database_operation(param: str) -> Optional[Dict[str, Any]]:
    """Database operation with proper error handling"""
    try:
        with get_db_cursor(commit=False) as cursor:
            cursor.execute("SELECT * FROM table WHERE param = %s", (param,))
            return cursor.fetchone()
    except Exception as e:
        logger.error(f"Database error: {e}")
        return None
```

## 📋 Required Elements

Every utility module MUST have:
- ✅ Proper docstring with description and examples
- ✅ Type hints for all functions
- ✅ Error handling with logging
- ✅ Configuration setup functions
- ✅ Consistent return patterns

## 🧪 Testing Pattern

```python
import pytest
from unittest.mock import Mock, patch
import utility_feature_name as feature_utility

@pytest.fixture
def setup_utility():
    """Setup utility with mocked dependencies"""
    feature_utility.set_config({"test": "config"})
    return feature_utility

def test_main_function(setup_utility):
    """Test main utility function"""
    result = setup_utility.main_function("test_param", {"data": "value"})
    assert result is True
```

## 🔍 Before Creating New Utilities

1. **Search existing utilities**: `find . -name "utility_*.py"`
2. **Check other services**: Look for similar functionality
3. **Review shared modules**: Check `/shared/` directory
4. **Plan the interface**: Design clear, reusable functions

## 📚 Documentation Requirements

- **Module docstring**: Purpose, dependencies, usage examples
- **Function docstrings**: Parameters, returns, raises, examples
- **Update Developer Guide**: Add new utilities to the guide
- **README updates**: Update service README if needed

---

**Follow these patterns to ensure consistency and reusability across all OpsConductor services.**