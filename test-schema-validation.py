#!/usr/bin/env python3
"""
Test schema validation directly
"""

import json
import jsonschema

# Test the notification step schema directly
notification_step = {
    "type": "notify.email",
    "recipients": ["test@example.com"],
    "subject_template": "Test from OpsConductor",
    "body_template": "This is a test notification."
}

# Simple schema for testing
schema = {
    "type": "object",
    "required": ["type", "recipients"],
    "properties": {
        "type": {"const": "notify.email"},
        "recipients": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 1
        },
        "subject_template": {"type": "string"},
        "body_template": {"type": "string"}
    },
    "additionalProperties": True
}

try:
    jsonschema.validate(notification_step, schema)
    print("✅ Schema validation passed!")
except jsonschema.ValidationError as e:
    print(f"❌ Schema validation failed: {e}")
except Exception as e:
    print(f"❌ Error: {e}")