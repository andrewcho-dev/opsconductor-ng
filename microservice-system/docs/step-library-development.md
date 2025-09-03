# Step Library Development Guide

This guide explains how to create, package, and distribute step libraries for OpsConductor.

## Overview

Step libraries are modular packages that extend OpsConductor's capabilities by providing new step types for job workflows. Libraries can be:

- **Free**: Open-source libraries available to all users
- **Premium**: Commercial libraries requiring license keys
- **Custom**: Private libraries for specific organizations

## Library Structure

A step library is packaged as a ZIP file with the following structure:

```
my-library-1.0.0.zip
├── manifest.json          # Library metadata and configuration
├── steps/                 # Step definitions
│   ├── step1.json
│   ├── step2.json
│   └── ...
├── executors/             # Step execution code (optional)
│   ├── step1.py
│   ├── step2.py
│   └── ...
├── docs/                  # Documentation (optional)
│   ├── README.md
│   └── examples/
├── assets/                # Icons, images (optional)
│   └── icons/
└── tests/                 # Test files (optional)
    └── test_steps.py
```

## Manifest File (manifest.json)

The manifest file contains library metadata:

```json
{
  "name": "file-operations",
  "version": "1.2.0",
  "display_name": "File Operations Library",
  "description": "Comprehensive file and directory operations with 25+ commands",
  "author": "Your Name",
  "author_email": "your.email@example.com",
  "homepage": "https://github.com/yourname/opsconductor-file-ops",
  "repository": "https://github.com/yourname/opsconductor-file-ops.git",
  "license": "MIT",
  "categories": ["file", "directory", "utilities"],
  "tags": ["file", "copy", "move", "delete", "directory"],
  "dependencies": [],
  "min_opsconductor_version": "1.0.0",
  
  "is_premium": false,
  "price": null,
  "trial_days": null,
  
  "platform_support": ["windows", "linux", "macos"],
  "required_permissions": ["file_system"],
  
  "steps": [
    {
      "file": "steps/file_create.json",
      "executor": "executors/file_create.py"
    },
    {
      "file": "steps/file_read.json",
      "executor": "executors/file_read.py"
    }
  ]
}
```

## Step Definition Format

Each step is defined in a JSON file:

```json
{
  "name": "file.create",
  "display_name": "Create File",
  "category": "file",
  "description": "Create a new file with specified content",
  "icon": "📄",
  "color": "#007bff",
  
  "inputs": 1,
  "outputs": 1,
  
  "parameters": {
    "path": {
      "type": "string",
      "required": true,
      "description": "File path to create",
      "default": "/path/to/file.txt",
      "validation": {
        "pattern": "^[^<>:\"|?*]+$"
      }
    },
    "content": {
      "type": "string",
      "required": false,
      "description": "File content",
      "default": "",
      "multiline": true
    },
    "encoding": {
      "type": "string",
      "required": false,
      "description": "File encoding",
      "default": "utf-8",
      "options": ["utf-8", "ascii", "latin-1"]
    },
    "overwrite": {
      "type": "boolean",
      "required": false,
      "description": "Overwrite existing file",
      "default": false
    }
  },
  
  "platform_support": ["windows", "linux", "macos"],
  "required_permissions": ["file_write"],
  
  "examples": [
    {
      "name": "Create text file",
      "description": "Create a simple text file",
      "parameters": {
        "path": "/tmp/hello.txt",
        "content": "Hello, World!",
        "encoding": "utf-8",
        "overwrite": true
      }
    }
  ],
  
  "tags": ["file", "create", "write"]
}
```

## Parameter Types

Supported parameter types:

- `string`: Text input
- `number`: Numeric input
- `boolean`: Checkbox
- `array`: List of values
- `object`: JSON object
- `file`: File path selector
- `directory`: Directory path selector
- `select`: Dropdown with predefined options
- `multiselect`: Multiple selection dropdown

## Step Executor (Optional)

For libraries that include custom execution logic:

```python
# executors/file_create.py
import os
from pathlib import Path

def execute(parameters, context):
    """
    Execute the file creation step
    
    Args:
        parameters: Step parameters from the job
        context: Execution context with utilities
        
    Returns:
        dict: Execution result
    """
    try:
        path = parameters.get('path')
        content = parameters.get('content', '')
        encoding = parameters.get('encoding', 'utf-8')
        overwrite = parameters.get('overwrite', False)
        
        # Validate path
        if not path:
            return {
                'success': False,
                'error': 'File path is required'
            }
        
        file_path = Path(path)
        
        # Check if file exists and overwrite is disabled
        if file_path.exists() and not overwrite:
            return {
                'success': False,
                'error': f'File {path} already exists and overwrite is disabled'
            }
        
        # Create parent directories if needed
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write file
        with open(file_path, 'w', encoding=encoding) as f:
            f.write(content)
        
        return {
            'success': True,
            'message': f'File created successfully: {path}',
            'output': {
                'path': str(file_path.absolute()),
                'size': file_path.stat().st_size
            }
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f'Failed to create file: {str(e)}'
        }
```

## Premium Libraries

For premium libraries, add licensing information to the manifest:

```json
{
  "is_premium": true,
  "price": 99.99,
  "trial_days": 30,
  "license_validation_url": "https://api.yourcompany.com/validate-license",
  "support_email": "support@yourcompany.com"
}
```

## Building a Library

1. **Create the directory structure**
2. **Write the manifest.json**
3. **Define your steps in JSON files**
4. **Add executors if needed**
5. **Package as ZIP file**

Example build script:

```bash
#!/bin/bash
# build-library.sh

LIBRARY_NAME="file-operations"
VERSION="1.2.0"
OUTPUT_FILE="${LIBRARY_NAME}-${VERSION}.zip"

# Create temporary build directory
BUILD_DIR="build/${LIBRARY_NAME}"
mkdir -p "$BUILD_DIR"

# Copy files
cp manifest.json "$BUILD_DIR/"
cp -r steps/ "$BUILD_DIR/"
cp -r executors/ "$BUILD_DIR/"
cp -r docs/ "$BUILD_DIR/"

# Create ZIP package
cd build
zip -r "../${OUTPUT_FILE}" "${LIBRARY_NAME}/"

echo "Library packaged: ${OUTPUT_FILE}"
```

## Installation

Libraries can be installed through:

1. **Frontend UI**: Upload ZIP file through the Library Manager
2. **API**: POST to `/api/v1/libraries/install`
3. **CLI**: Using a command-line tool (future feature)

## Testing

Test your library before distribution:

```python
# tests/test_file_operations.py
import unittest
import tempfile
import os
from pathlib import Path

class TestFileOperations(unittest.TestCase):
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
    
    def test_file_create(self):
        from executors.file_create import execute
        
        parameters = {
            'path': os.path.join(self.temp_dir, 'test.txt'),
            'content': 'Hello, World!',
            'encoding': 'utf-8',
            'overwrite': True
        }
        
        result = execute(parameters, {})
        
        self.assertTrue(result['success'])
        self.assertTrue(os.path.exists(parameters['path']))
        
        with open(parameters['path'], 'r') as f:
            self.assertEqual(f.read(), 'Hello, World!')
```

## Best Practices

1. **Naming**: Use descriptive, hierarchical names (e.g., `file.create`, `network.ping`)
2. **Documentation**: Provide clear descriptions and examples
3. **Error Handling**: Return meaningful error messages
4. **Validation**: Validate parameters before execution
5. **Security**: Never execute arbitrary code from parameters
6. **Performance**: Consider execution time and resource usage
7. **Compatibility**: Test on all supported platforms
8. **Versioning**: Use semantic versioning (MAJOR.MINOR.PATCH)

## Distribution

- **GitHub Releases**: Host ZIP files on GitHub
- **Package Registry**: Use a package registry service
- **Direct Distribution**: Provide download links
- **Marketplace**: Submit to OpsConductor marketplace (future)

## Example Libraries

See the `examples/step-libraries/` directory for complete example libraries:

- `file-operations-basic/`: Simple file operations
- `network-tools-premium/`: Premium network utilities
- `custom-integrations/`: Custom API integrations

## Support

For questions about step library development:

- Documentation: https://docs.opsconductor.com/step-libraries
- Community Forum: https://community.opsconductor.com
- GitHub Issues: https://github.com/opsconductor/opsconductor/issues