#!/usr/bin/env python3
"""
Tool Validation Script
Validates tool YAML definitions before importing to database

Usage:
    python scripts/validate_tool.py pipeline/config/tools/linux/grep.yaml
    python scripts/validate_tool.py pipeline/config/tools/linux/*.yaml
"""

import sys
import yaml
import argparse
from pathlib import Path
from typing import Dict, Any, List

# ANSI color codes
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'


class ToolValidator:
    """Validates tool YAML definitions"""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
    
    def validate_file(self, file_path: str) -> bool:
        """
        Validate a single YAML file
        
        Returns:
            True if valid
        """
        self.errors = []
        self.warnings = []
        
        print(f"\nValidating: {file_path}")
        print("-" * 60)
        
        # Load YAML
        try:
            with open(file_path, 'r') as f:
                data = yaml.safe_load(f)
        except Exception as e:
            self.errors.append(f"Failed to parse YAML: {e}")
            return False
        
        if not data:
            self.errors.append("Empty YAML file")
            return False
        
        # Validate structure
        self._validate_basic_info(data)
        self._validate_defaults(data)
        self._validate_capabilities(data)
        self._validate_dependencies(data)
        self._validate_metadata(data)
        
        # Print results
        if self.errors:
            print(f"\n{RED}✗ VALIDATION FAILED{RESET}")
            print(f"\n{RED}Errors:{RESET}")
            for error in self.errors:
                print(f"  • {error}")
        
        if self.warnings:
            print(f"\n{YELLOW}Warnings:{RESET}")
            for warning in self.warnings:
                print(f"  • {warning}")
        
        if not self.errors:
            print(f"\n{GREEN}✓ VALIDATION PASSED{RESET}")
            return True
        
        return False
    
    def _validate_basic_info(self, data: Dict[str, Any]):
        """Validate basic tool information"""
        required_fields = ['tool_name', 'version', 'description', 'platform', 'category']
        
        for field in required_fields:
            if field not in data:
                self.errors.append(f"Missing required field: '{field}'")
            elif not data[field]:
                self.errors.append(f"Field '{field}' cannot be empty")
        
        # Validate platform
        if 'platform' in data:
            valid_platforms = ['linux', 'windows', 'network', 'scheduler', 'custom', 'multi-platform']
            if data['platform'] not in valid_platforms:
                self.errors.append(
                    f"Invalid platform '{data['platform']}'. "
                    f"Must be one of: {', '.join(valid_platforms)}"
                )
        
        # Validate category
        if 'category' in data:
            valid_categories = ['system', 'network', 'automation', 'monitoring', 'security', 'database', 'cloud', 'container']
            if data['category'] not in valid_categories:
                self.errors.append(
                    f"Invalid category '{data['category']}'. "
                    f"Must be one of: {', '.join(valid_categories)}"
                )
        
        # Validate version format
        if 'version' in data:
            version = str(data['version'])
            if not version or version == '<VERSION>':
                self.errors.append("Version must be specified (e.g., '1.0', '2.1')")
    
    def _validate_defaults(self, data: Dict[str, Any]):
        """Validate defaults section"""
        if 'defaults' not in data:
            self.errors.append("Missing required section: 'defaults'")
            return
        
        defaults = data['defaults']
        if not isinstance(defaults, dict):
            self.errors.append("'defaults' must be a dictionary")
            return
        
        required_defaults = ['accuracy_level', 'freshness', 'data_source']
        for field in required_defaults:
            if field not in defaults:
                self.warnings.append(f"Missing recommended default: '{field}'")
        
        # Validate accuracy_level
        if 'accuracy_level' in defaults:
            valid_levels = ['real-time', 'cached', 'estimated']
            if defaults['accuracy_level'] not in valid_levels:
                self.warnings.append(
                    f"Unusual accuracy_level '{defaults['accuracy_level']}'. "
                    f"Recommended: {', '.join(valid_levels)}"
                )
        
        # Validate freshness
        if 'freshness' in defaults:
            valid_freshness = ['live', 'recent', 'historical']
            if defaults['freshness'] not in valid_freshness:
                self.warnings.append(
                    f"Unusual freshness '{defaults['freshness']}'. "
                    f"Recommended: {', '.join(valid_freshness)}"
                )
    
    def _validate_capabilities(self, data: Dict[str, Any]):
        """Validate capabilities section"""
        if 'capabilities' not in data:
            self.errors.append("Missing required section: 'capabilities'")
            return
        
        capabilities = data['capabilities']
        if not isinstance(capabilities, dict):
            self.errors.append("'capabilities' must be a dictionary")
            return
        
        if len(capabilities) == 0:
            self.errors.append("At least one capability must be defined")
            return
        
        for cap_name, cap_data in capabilities.items():
            self._validate_capability(cap_name, cap_data)
    
    def _validate_capability(self, cap_name: str, cap_data: Dict[str, Any]):
        """Validate a single capability"""
        if not isinstance(cap_data, dict):
            self.errors.append(f"Capability '{cap_name}' must be a dictionary")
            return
        
        if 'description' not in cap_data:
            self.warnings.append(f"Capability '{cap_name}' missing description")
        
        if 'patterns' not in cap_data:
            self.errors.append(f"Capability '{cap_name}' missing 'patterns' section")
            return
        
        patterns = cap_data['patterns']
        if not isinstance(patterns, dict):
            self.errors.append(f"Capability '{cap_name}' patterns must be a dictionary")
            return
        
        if len(patterns) == 0:
            self.errors.append(f"Capability '{cap_name}' must have at least one pattern")
            return
        
        for pattern_name, pattern_data in patterns.items():
            self._validate_pattern(cap_name, pattern_name, pattern_data)
    
    def _validate_pattern(self, cap_name: str, pattern_name: str, pattern_data: Dict[str, Any]):
        """Validate a single pattern"""
        prefix = f"Capability '{cap_name}', Pattern '{pattern_name}'"
        
        if not isinstance(pattern_data, dict):
            self.errors.append(f"{prefix} must be a dictionary")
            return
        
        # Required fields
        required_fields = [
            'description', 'typical_use_cases', 'time_estimate_ms',
            'cost_estimate', 'complexity_score', 'scope', 'completeness',
            'policy', 'preference_match', 'required_inputs', 'expected_outputs'
        ]
        
        for field in required_fields:
            if field not in pattern_data:
                self.errors.append(f"{prefix}: Missing required field '{field}'")
        
        # Validate complexity_score
        if 'complexity_score' in pattern_data:
            score = pattern_data['complexity_score']
            try:
                score_float = float(score)
                if not (0.0 <= score_float <= 1.0):
                    self.errors.append(f"{prefix}: complexity_score must be between 0.0 and 1.0")
            except (ValueError, TypeError):
                self.errors.append(f"{prefix}: complexity_score must be a number")
        
        # Validate scope
        if 'scope' in pattern_data:
            valid_scopes = ['single_item', 'batch', 'exhaustive']
            if pattern_data['scope'] not in valid_scopes:
                self.errors.append(
                    f"{prefix}: Invalid scope '{pattern_data['scope']}'. "
                    f"Must be one of: {', '.join(valid_scopes)}"
                )
        
        # Validate completeness
        if 'completeness' in pattern_data:
            valid_completeness = ['complete', 'partial', 'summary']
            if pattern_data['completeness'] not in valid_completeness:
                self.errors.append(
                    f"{prefix}: Invalid completeness '{pattern_data['completeness']}'. "
                    f"Must be one of: {', '.join(valid_completeness)}"
                )
        
        # Validate policy
        if 'policy' in pattern_data:
            policy = pattern_data['policy']
            if not isinstance(policy, dict):
                self.errors.append(f"{prefix}: 'policy' must be a dictionary")
            else:
                if 'max_cost' not in policy:
                    self.warnings.append(f"{prefix}: policy missing 'max_cost'")
                if 'requires_approval' not in policy:
                    self.warnings.append(f"{prefix}: policy missing 'requires_approval'")
                if 'production_safe' not in policy:
                    self.warnings.append(f"{prefix}: policy missing 'production_safe'")
        
        # Validate preference_match
        if 'preference_match' in pattern_data:
            pref = pattern_data['preference_match']
            if not isinstance(pref, dict):
                self.errors.append(f"{prefix}: 'preference_match' must be a dictionary")
            else:
                required_prefs = ['speed', 'accuracy', 'cost', 'complexity', 'completeness']
                for pref_name in required_prefs:
                    if pref_name not in pref:
                        self.warnings.append(f"{prefix}: preference_match missing '{pref_name}'")
                    else:
                        try:
                            pref_value = float(pref[pref_name])
                            if not (0.0 <= pref_value <= 1.0):
                                self.errors.append(
                                    f"{prefix}: preference_match.{pref_name} must be between 0.0 and 1.0"
                                )
                        except (ValueError, TypeError):
                            self.errors.append(f"{prefix}: preference_match.{pref_name} must be a number")
        
        # Validate required_inputs
        if 'required_inputs' in pattern_data:
            inputs = pattern_data['required_inputs']
            if not isinstance(inputs, list):
                self.errors.append(f"{prefix}: 'required_inputs' must be a list")
        
        # Validate expected_outputs
        if 'expected_outputs' in pattern_data:
            outputs = pattern_data['expected_outputs']
            if not isinstance(outputs, list):
                self.errors.append(f"{prefix}: 'expected_outputs' must be a list")
    
    def _validate_dependencies(self, data: Dict[str, Any]):
        """Validate dependencies section"""
        if 'dependencies' in data:
            deps = data['dependencies']
            if not isinstance(deps, list):
                self.errors.append("'dependencies' must be a list")
    
    def _validate_metadata(self, data: Dict[str, Any]):
        """Validate metadata section"""
        if 'metadata' in data:
            metadata = data['metadata']
            if not isinstance(metadata, dict):
                self.errors.append("'metadata' must be a dictionary")


def main():
    parser = argparse.ArgumentParser(
        description='Validate tool YAML definitions'
    )
    parser.add_argument('files', nargs='+', help='YAML files to validate')
    
    args = parser.parse_args()
    
    validator = ToolValidator()
    all_valid = True
    
    for file_path in args.files:
        path = Path(file_path)
        
        if not path.exists():
            print(f"\n{RED}✗ File not found: {file_path}{RESET}")
            all_valid = False
            continue
        
        if not validator.validate_file(str(path)):
            all_valid = False
    
    print("\n" + "="*60)
    if all_valid:
        print(f"{GREEN}All files are valid!{RESET}")
        sys.exit(0)
    else:
        print(f"{RED}Some files have validation errors{RESET}")
        sys.exit(1)


if __name__ == '__main__':
    main()