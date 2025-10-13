"""
Pytest configuration for automation-service tests.

Sets up sys.path to allow imports from automation-service and shared modules.
"""

import os
import sys
from pathlib import Path

# IMPORTANT: Remove parent directory if it's in sys.path to avoid conflicts
# with the root-level selector module
automation_service_dir = Path(__file__).parent.parent.resolve()
parent_dir = automation_service_dir.parent

# Remove parent_dir from sys.path if present (to avoid root/selector conflict)
parent_dir_str = str(parent_dir)
while parent_dir_str in sys.path:
    sys.path.remove(parent_dir_str)

# Add automation-service directory at position 0
automation_service_dir_str = str(automation_service_dir)
if automation_service_dir_str in sys.path:
    sys.path.remove(automation_service_dir_str)
sys.path.insert(0, automation_service_dir_str)

# Add parent directory AFTER automation-service (for shared module)
sys.path.insert(1, parent_dir_str)