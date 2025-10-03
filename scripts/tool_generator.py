#!/usr/bin/env python3
"""
Tool Generator CLI
Interactive tool for creating tool definitions for the Tool Catalog System

Features:
- Interactive prompts for all tool fields
- Template-based generation
- Validation before creation
- Direct database insertion or YAML export
- Support for multiple capabilities and patterns
"""

import sys
import os
import json
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline.services.tool_catalog_service import ToolCatalogService


class ToolGenerator:
    """Interactive tool generator"""
    
    def __init__(self):
        self.tool_data: Dict[str, Any] = {}
        self.capabilities: List[Dict[str, Any]] = []
        
    def run(self):
        """Run the interactive tool generator"""
        print("=" * 70)
        print("🛠️  Tool Catalog Generator")
        print("=" * 70)
        print()
        print("This wizard will help you create a new tool definition.")
        print("Press Ctrl+C at any time to cancel.")
        print()
        
        try:
            # Step 1: Basic Information
            self._collect_basic_info()
            
            # Step 2: Defaults
            self._collect_defaults()
            
            # Step 3: Dependencies
            self._collect_dependencies()
            
            # Step 4: Capabilities and Patterns
            self._collect_capabilities()
            
            # Step 5: Metadata
            self._collect_metadata()
            
            # Step 6: Review
            self._review_tool()
            
            # Step 7: Save
            self._save_tool()
            
        except KeyboardInterrupt:
            print("\n\n❌ Cancelled by user")
            sys.exit(1)
        except Exception as e:
            print(f"\n\n❌ Error: {e}")
            sys.exit(1)
    
    def _collect_basic_info(self):
        """Collect basic tool information"""
        print("📋 Step 1: Basic Information")
        print("-" * 70)
        
        self.tool_data['tool_name'] = self._prompt(
            "Tool name (e.g., 'grep', 'docker_ps')",
            required=True,
            validator=lambda x: x.replace('_', '').replace('-', '').isalnum()
        )
        
        self.tool_data['version'] = self._prompt(
            "Version",
            default="1.0",
            required=True
        )
        
        self.tool_data['description'] = self._prompt(
            "Description",
            required=True
        )
        
        self.tool_data['platform'] = self._prompt_choice(
            "Platform",
            choices=['linux', 'windows', 'network', 'scheduler', 'custom'],
            default='linux'
        )
        
        self.tool_data['category'] = self._prompt_choice(
            "Category",
            choices=['system', 'network', 'automation', 'monitoring', 'security', 'database', 'cloud'],
            default='system'
        )
        
        self.tool_data['status'] = self._prompt_choice(
            "Status",
            choices=['active', 'testing', 'deprecated', 'disabled'],
            default='active'
        )
        
        self.tool_data['enabled'] = self._prompt_bool(
            "Enabled",
            default=True
        )
        
        print()
    
    def _collect_defaults(self):
        """Collect tool defaults"""
        print("⚙️  Step 2: Defaults")
        print("-" * 70)
        
        if not self._prompt_bool("Configure defaults?", default=True):
            self.tool_data['defaults'] = {}
            print()
            return
        
        defaults = {}
        
        defaults['accuracy_level'] = self._prompt_choice(
            "Accuracy level",
            choices=['real-time', 'high', 'medium', 'low'],
            default='real-time'
        )
        
        defaults['freshness'] = self._prompt_choice(
            "Freshness",
            choices=['live', 'cached', 'historical'],
            default='live'
        )
        
        defaults['data_source'] = self._prompt_choice(
            "Data source",
            choices=['direct', 'api', 'database', 'filesystem', 'network'],
            default='direct'
        )
        
        self.tool_data['defaults'] = defaults
        print()
    
    def _collect_dependencies(self):
        """Collect tool dependencies"""
        print("📦 Step 3: Dependencies")
        print("-" * 70)
        
        dependencies = []
        
        while True:
            if not self._prompt_bool(
                "Add a dependency?" if not dependencies else "Add another dependency?",
                default=False
            ):
                break
            
            dep = {}
            dep['name'] = self._prompt("Dependency name", required=True)
            dep['type'] = self._prompt_choice(
                "Dependency type",
                choices=['service', 'package', 'binary', 'permission'],
                default='service'
            )
            dep['required'] = self._prompt_bool("Required?", default=True)
            
            version = self._prompt("Version (optional)")
            if version:
                dep['version'] = version
            
            dependencies.append(dep)
            print(f"  ✓ Added dependency: {dep['name']}")
        
        self.tool_data['dependencies'] = dependencies
        print()
    
    def _collect_capabilities(self):
        """Collect capabilities and patterns"""
        print("🎯 Step 4: Capabilities and Patterns")
        print("-" * 70)
        print("A tool must have at least one capability with at least one pattern.")
        print()
        
        while True:
            capability = self._collect_capability()
            self.capabilities.append(capability)
            
            if not self._prompt_bool("Add another capability?", default=False):
                break
        
        print()
    
    def _collect_capability(self):
        """Collect a single capability"""
        print("\n  📌 New Capability")
        print("  " + "-" * 66)
        
        capability = {}
        capability['capability_name'] = self._prompt("  Capability name", required=True)
        capability['description'] = self._prompt("  Description", required=True)
        
        # Collect patterns
        patterns = []
        while True:
            pattern = self._collect_pattern()
            patterns.append(pattern)
            
            if not self._prompt_bool("  Add another pattern to this capability?", default=False):
                break
        
        capability['patterns'] = patterns
        return capability
    
    def _collect_pattern(self):
        """Collect a single pattern"""
        print("\n    🔹 New Pattern")
        print("    " + "-" * 64)
        
        pattern = {}
        pattern['pattern_name'] = self._prompt("    Pattern name", required=True)
        pattern['description'] = self._prompt("    Description", required=True)
        
        # Use cases
        use_cases = []
        while True:
            use_case = self._prompt("    Typical use case (empty to finish)")
            if not use_case:
                break
            use_cases.append(use_case)
        pattern['typical_use_cases'] = use_cases
        
        # Performance estimates
        pattern['time_estimate_ms'] = self._prompt(
            "    Time estimate (ms or expression, e.g., '1000' or '100 + 10*N')",
            default="1000"
        )
        
        pattern['cost_estimate'] = self._prompt(
            "    Cost estimate (number or expression, e.g., '1' or 'ceil(N/100)')",
            default="1"
        )
        
        pattern['complexity_score'] = float(self._prompt(
            "    Complexity score (0.0-1.0)",
            default="0.5",
            validator=lambda x: 0.0 <= float(x) <= 1.0
        ))
        
        # Quality metrics
        pattern['scope'] = self._prompt_choice(
            "    Scope",
            choices=['single', 'multiple', 'all'],
            default='single'
        )
        
        pattern['completeness'] = self._prompt_choice(
            "    Completeness",
            choices=['full', 'partial', 'summary'],
            default='full'
        )
        
        # Limitations
        limitations = []
        while True:
            limitation = self._prompt("    Limitation (empty to finish)")
            if not limitation:
                break
            limitations.append(limitation)
        pattern['limitations'] = limitations
        
        # Policy
        policy = {}
        policy['max_cost'] = int(self._prompt("    Max cost", default="10"))
        policy['requires_approval'] = self._prompt_bool("    Requires approval?", default=False)
        policy['production_safe'] = self._prompt_bool("    Production safe?", default=True)
        pattern['policy'] = policy
        
        # Preference match
        print("    Preference match scores (0.0-1.0):")
        preference_match = {}
        for pref in ['speed', 'accuracy', 'cost', 'complexity', 'completeness']:
            preference_match[pref] = float(self._prompt(
                f"      {pref.capitalize()}",
                default="0.8",
                validator=lambda x: 0.0 <= float(x) <= 1.0
            ))
        pattern['preference_match'] = preference_match
        
        # Inputs/Outputs
        pattern['required_inputs'] = self._collect_io_schema("    Required inputs")
        pattern['expected_outputs'] = self._collect_io_schema("    Expected outputs")
        
        # Examples
        examples = []
        if self._prompt_bool("    Add examples?", default=True):
            while True:
                example = {}
                example['description'] = self._prompt("      Example description", required=True)
                example['input'] = self._prompt("      Example input", required=True)
                example['output'] = self._prompt("      Example output", required=True)
                examples.append(example)
                
                if not self._prompt_bool("      Add another example?", default=False):
                    break
        pattern['examples'] = examples
        
        return pattern
    
    def _collect_io_schema(self, prompt: str) -> List[Dict[str, Any]]:
        """Collect input/output schema"""
        schema = []
        
        if not self._prompt_bool(f"{prompt} - add fields?", default=True):
            return schema
        
        while True:
            field = {}
            field['name'] = self._prompt(f"{prompt} - field name", required=True)
            field['type'] = self._prompt_choice(
                f"{prompt} - field type",
                choices=['string', 'integer', 'float', 'boolean', 'array', 'object'],
                default='string'
            )
            field['required'] = self._prompt_bool(f"{prompt} - required?", default=True)
            
            desc = self._prompt(f"{prompt} - description (optional)")
            if desc:
                field['description'] = desc
            
            schema.append(field)
            
            if not self._prompt_bool(f"{prompt} - add another field?", default=False):
                break
        
        return schema
    
    def _collect_metadata(self):
        """Collect metadata"""
        print("📝 Step 5: Metadata")
        print("-" * 70)
        
        metadata = {}
        
        author = self._prompt("Author (optional)")
        if author:
            metadata['author'] = author
        
        tags = []
        while True:
            tag = self._prompt("Tag (empty to finish)")
            if not tag:
                break
            tags.append(tag)
        if tags:
            metadata['tags'] = tags
        
        doc_url = self._prompt("Documentation URL (optional)")
        if doc_url:
            metadata['documentation_url'] = doc_url
        
        self.tool_data['metadata'] = metadata
        
        # Created by
        self.tool_data['created_by'] = self._prompt(
            "Created by",
            default=os.getenv('USER', 'tool_generator')
        )
        
        print()
    
    def _review_tool(self):
        """Review the tool definition"""
        print("👀 Step 6: Review")
        print("=" * 70)
        
        # Build complete tool definition
        tool_def = {
            **self.tool_data,
            'capabilities': self.capabilities
        }
        
        # Display as YAML for readability
        print(yaml.dump(tool_def, default_flow_style=False, sort_keys=False))
        print("=" * 70)
        
        if not self._prompt_bool("Does this look correct?", default=True):
            print("\n❌ Tool creation cancelled")
            sys.exit(0)
    
    def _save_tool(self):
        """Save the tool"""
        print("\n💾 Step 7: Save")
        print("-" * 70)
        
        save_method = self._prompt_choice(
            "Save method",
            choices=['database', 'yaml', 'both'],
            default='database'
        )
        
        if save_method in ['database', 'both']:
            self._save_to_database()
        
        if save_method in ['yaml', 'both']:
            self._save_to_yaml()
        
        print("\n✅ Tool created successfully!")
    
    def _save_to_database(self):
        """Save tool to database"""
        print("\n  📊 Saving to database...")
        
        try:
            service = ToolCatalogService()
            
            # Create tool
            tool_id = service.create_tool(
                tool_name=self.tool_data['tool_name'],
                version=self.tool_data['version'],
                description=self.tool_data['description'],
                platform=self.tool_data['platform'],
                category=self.tool_data['category'],
                status=self.tool_data['status'],
                enabled=self.tool_data['enabled'],
                defaults=self.tool_data['defaults'],
                dependencies=self.tool_data['dependencies'],
                metadata=self.tool_data['metadata'],
                created_by=self.tool_data['created_by']
            )
            
            # Add capabilities and patterns
            for capability in self.capabilities:
                cap_id = service.add_capability(
                    tool_id=tool_id,
                    capability_name=capability['capability_name'],
                    description=capability['description']
                )
                
                for pattern in capability['patterns']:
                    service.add_pattern(
                        capability_id=cap_id,
                        pattern_name=pattern['pattern_name'],
                        description=pattern['description'],
                        typical_use_cases=pattern['typical_use_cases'],
                        time_estimate_ms=pattern['time_estimate_ms'],
                        cost_estimate=pattern['cost_estimate'],
                        complexity_score=pattern['complexity_score'],
                        scope=pattern['scope'],
                        completeness=pattern['completeness'],
                        limitations=pattern['limitations'],
                        policy=pattern['policy'],
                        preference_match=pattern['preference_match'],
                        required_inputs=pattern['required_inputs'],
                        expected_outputs=pattern['expected_outputs'],
                        examples=pattern['examples']
                    )
            
            print(f"  ✓ Tool saved to database (ID: {tool_id})")
            
        except Exception as e:
            print(f"  ❌ Failed to save to database: {e}")
            raise
    
    def _save_to_yaml(self):
        """Save tool to YAML file"""
        print("\n  📄 Saving to YAML...")
        
        # Build complete tool definition
        tool_def = {
            **self.tool_data,
            'capabilities': self.capabilities
        }
        
        # Determine output path
        tools_dir = Path(__file__).parent.parent / "pipeline" / "config" / "tools"
        tools_dir.mkdir(parents=True, exist_ok=True)
        
        output_path = tools_dir / f"{self.tool_data['tool_name']}.yaml"
        
        # Save to file
        with open(output_path, 'w') as f:
            yaml.dump(tool_def, f, default_flow_style=False, sort_keys=False)
        
        print(f"  ✓ Tool saved to {output_path}")
    
    # Helper methods
    
    def _prompt(
        self,
        message: str,
        default: Optional[str] = None,
        required: bool = False,
        validator: Optional[callable] = None
    ) -> str:
        """Prompt user for input"""
        while True:
            if default:
                prompt = f"{message} [{default}]: "
            else:
                prompt = f"{message}: "
            
            value = input(prompt).strip()
            
            if not value and default:
                value = default
            
            if required and not value:
                print("  ⚠️  This field is required")
                continue
            
            if validator and value:
                try:
                    if not validator(value):
                        print("  ⚠️  Invalid value")
                        continue
                except Exception as e:
                    print(f"  ⚠️  Invalid value: {e}")
                    continue
            
            return value
    
    def _prompt_choice(
        self,
        message: str,
        choices: List[str],
        default: Optional[str] = None
    ) -> str:
        """Prompt user to choose from options"""
        print(f"{message}:")
        for i, choice in enumerate(choices, 1):
            marker = " (default)" if choice == default else ""
            print(f"  {i}. {choice}{marker}")
        
        while True:
            value = input(f"Choice [1-{len(choices)}]: ").strip()
            
            if not value and default:
                return default
            
            try:
                idx = int(value) - 1
                if 0 <= idx < len(choices):
                    return choices[idx]
            except ValueError:
                pass
            
            print("  ⚠️  Invalid choice")
    
    def _prompt_bool(self, message: str, default: bool = False) -> bool:
        """Prompt user for yes/no"""
        default_str = "Y/n" if default else "y/N"
        value = input(f"{message} [{default_str}]: ").strip().lower()
        
        if not value:
            return default
        
        return value in ['y', 'yes', 'true', '1']


def main():
    """Main entry point"""
    generator = ToolGenerator()
    generator.run()


if __name__ == '__main__':
    main()