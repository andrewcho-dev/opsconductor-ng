#!/usr/bin/env python3
"""
Tool Definition Audit Script
Systematically checks all tool YAML definitions for completeness and correctness.
"""

import yaml
import os
from pathlib import Path
from typing import Dict, List, Any, Tuple
from collections import defaultdict

class ToolAuditor:
    def __init__(self, tools_dir: str):
        self.tools_dir = Path(tools_dir)
        self.results = {
            "excellent": [],
            "good": [],
            "needs_work": [],
            "broken": [],
            "untested": []
        }
        self.issues = defaultdict(list)
        
    def audit_all_tools(self):
        """Audit all tool YAML files"""
        yaml_files = list(self.tools_dir.rglob("*.yaml"))
        
        # Exclude templates and old files
        yaml_files = [f for f in yaml_files if "template" not in str(f).lower() and ".old" not in str(f)]
        
        print(f"Found {len(yaml_files)} tool definitions to audit\n")
        
        for yaml_file in sorted(yaml_files):
            self.audit_tool(yaml_file)
        
        return self.results, self.issues
    
    def audit_tool(self, yaml_file: Path):
        """Audit a single tool definition"""
        try:
            with open(yaml_file, 'r') as f:
                tool_def = yaml.safe_load(f)
            
            if not tool_def:
                self.results["broken"].append(str(yaml_file))
                self.issues[str(yaml_file)].append("Empty YAML file")
                return
            
            # Get relative path for display
            rel_path = yaml_file.relative_to(self.tools_dir)
            tool_name = tool_def.get("tool_name", "UNKNOWN")
            
            # Check required fields
            score = 0
            max_score = 0
            issues = []
            
            # CRITICAL FIELDS (must have)
            critical_fields = ["tool_name", "description", "category", "platform"]
            for field in critical_fields:
                max_score += 10
                if field in tool_def and tool_def[field]:
                    score += 10
                else:
                    issues.append(f"Missing critical field: {field}")
            
            # IMPORTANT FIELDS
            important_fields = ["parameters", "output_format"]
            for field in important_fields:
                max_score += 5
                if field in tool_def and tool_def[field]:
                    score += 5
                else:
                    issues.append(f"Missing important field: {field}")
            
            # EXECUTION METADATA (optional but recommended)
            max_score += 10
            if "execution" in tool_def:
                exec_meta = tool_def["execution"]
                score += 5
                
                # Check execution completeness
                if "connection" in exec_meta:
                    score += 2
                if "command_builder" in exec_meta:
                    score += 2
                if "credentials" in exec_meta:
                    score += 1
            else:
                # Check if it can be inferred
                platform = tool_def.get("platform", "").lower()
                category = tool_def.get("category", "").lower()
                
                if platform in ["windows", "linux"] or category in ["network", "database"]:
                    issues.append("No execution metadata (will be inferred from platform/category)")
                else:
                    issues.append("No execution metadata and cannot be reliably inferred")
            
            # PARAMETER QUALITY
            max_score += 10
            if "parameters" in tool_def and tool_def["parameters"]:
                params = tool_def["parameters"]
                score += 5
                
                # Check if parameters have descriptions
                param_quality = 0
                for param_name, param_def in params.items():
                    if isinstance(param_def, dict):
                        if "description" in param_def:
                            param_quality += 1
                        if "type" in param_def:
                            param_quality += 1
                
                if param_quality > 0:
                    score += min(5, param_quality)
            
            # EXAMPLES
            max_score += 5
            if "examples" in tool_def and tool_def["examples"]:
                score += 5
            else:
                issues.append("No examples provided")
            
            # Calculate percentage
            percentage = (score / max_score) * 100 if max_score > 0 else 0
            
            # Categorize
            tool_info = {
                "path": str(rel_path),
                "tool_name": tool_name,
                "score": percentage,
                "issues": issues
            }
            
            if percentage >= 90:
                self.results["excellent"].append(tool_info)
            elif percentage >= 75:
                self.results["good"].append(tool_info)
            elif percentage >= 50:
                self.results["needs_work"].append(tool_info)
            else:
                self.results["broken"].append(tool_info)
            
            # Store issues
            if issues:
                self.issues[str(rel_path)] = issues
                
        except Exception as e:
            self.results["broken"].append({
                "path": str(yaml_file.relative_to(self.tools_dir)),
                "tool_name": "ERROR",
                "score": 0,
                "issues": [f"Failed to parse: {str(e)}"]
            })
            self.issues[str(yaml_file.relative_to(self.tools_dir))] = [f"Parse error: {str(e)}"]

def main():
    tools_dir = "/home/opsconductor/opsconductor-ng/pipeline/config/tools"
    
    auditor = ToolAuditor(tools_dir)
    results, issues = auditor.audit_all_tools()
    
    # Print summary
    print("=" * 80)
    print("TOOL AUDIT SUMMARY")
    print("=" * 80)
    print()
    
    total = sum(len(v) if isinstance(v, list) else len([x for x in v if isinstance(x, dict)]) for v in results.values())
    
    print(f"Total Tools Audited: {total}")
    print()
    
    # Excellent tools
    excellent = [t for t in results["excellent"] if isinstance(t, dict)]
    print(f"✅ EXCELLENT (90-100%): {len(excellent)} tools")
    if excellent:
        for tool in sorted(excellent, key=lambda x: x["score"], reverse=True):
            print(f"   {tool['score']:.0f}% - {tool['tool_name']} ({tool['path']})")
    print()
    
    # Good tools
    good = [t for t in results["good"] if isinstance(t, dict)]
    print(f"✓  GOOD (75-89%): {len(good)} tools")
    if good:
        for tool in sorted(good, key=lambda x: x["score"], reverse=True)[:10]:
            print(f"   {tool['score']:.0f}% - {tool['tool_name']} ({tool['path']})")
        if len(good) > 10:
            print(f"   ... and {len(good) - 10} more")
    print()
    
    # Needs work
    needs_work = [t for t in results["needs_work"] if isinstance(t, dict)]
    print(f"⚠️  NEEDS WORK (50-74%): {len(needs_work)} tools")
    if needs_work:
        for tool in sorted(needs_work, key=lambda x: x["score"], reverse=True)[:10]:
            print(f"   {tool['score']:.0f}% - {tool['tool_name']} ({tool['path']})")
            if tool["issues"]:
                for issue in tool["issues"][:2]:
                    print(f"      - {issue}")
        if len(needs_work) > 10:
            print(f"   ... and {len(needs_work) - 10} more")
    print()
    
    # Broken
    broken = [t for t in results["broken"] if isinstance(t, dict)]
    print(f"❌ BROKEN (<50%): {len(broken)} tools")
    if broken:
        for tool in sorted(broken, key=lambda x: x["score"])[:10]:
            print(f"   {tool['score']:.0f}% - {tool['tool_name']} ({tool['path']})")
            if tool["issues"]:
                for issue in tool["issues"][:3]:
                    print(f"      - {issue}")
        if len(broken) > 10:
            print(f"   ... and {len(broken) - 10} more")
    print()
    
    print("=" * 80)
    print("READINESS ASSESSMENT")
    print("=" * 80)
    print()
    
    ready = len(excellent) + len(good)
    ready_pct = (ready / total * 100) if total > 0 else 0
    
    print(f"Ready for Production: {ready}/{total} ({ready_pct:.1f}%)")
    print(f"Need Minor Fixes: {len(needs_work)}")
    print(f"Need Major Fixes: {len(broken)}")
    print()
    
    if ready_pct >= 80:
        print("✅ Overall Status: GOOD - Most tools are production ready")
    elif ready_pct >= 60:
        print("⚠️  Overall Status: FAIR - Many tools need work")
    else:
        print("❌ Overall Status: POOR - Significant work needed")
    print()

if __name__ == "__main__":
    main()