#!/usr/bin/env python3
"""
Tool Quality Audit Script

This script analyzes tool YAML files and scores them based on quality metrics.
It helps identify tools that need improvement and tracks progress over time.

Usage:
    python3 scripts/audit_tool_quality.py                    # Audit all tools
    python3 scripts/audit_tool_quality.py --tool curl        # Audit specific tool
    python3 scripts/audit_tool_quality.py --category linux   # Audit category
    python3 scripts/audit_tool_quality.py --report           # Generate detailed report
"""

import os
import sys
import yaml
import argparse
from pathlib import Path
from typing import Dict, List, Tuple
from collections import defaultdict

# Quality scoring weights
WEIGHTS = {
    'parameter_description': 0.4,
    'tool_completeness': 0.3,
    'llm_usability': 0.3
}

class ToolAuditor:
    def __init__(self, tools_dir: str):
        self.tools_dir = Path(tools_dir)
        self.results = []
        
    def audit_all_tools(self) -> List[Dict]:
        """Audit all tools in the tools directory."""
        for yaml_file in self.tools_dir.rglob('*.yaml'):
            if yaml_file.name == 'tool_template.yaml':
                continue
            try:
                result = self.audit_tool(yaml_file)
                self.results.append(result)
            except Exception as e:
                print(f"Error auditing {yaml_file}: {e}")
        return self.results
    
    def audit_tool(self, yaml_file: Path) -> Dict:
        """Audit a single tool and return quality scores."""
        with open(yaml_file, 'r') as f:
            tool_spec = yaml.safe_load(f)
        
        tool_name = tool_spec.get('tool_name', yaml_file.stem)
        category = yaml_file.parent.name
        
        # Calculate scores
        param_score = self._score_parameter_descriptions(tool_spec)
        completeness_score = self._score_tool_completeness(tool_spec)
        usability_score = self._score_llm_usability(tool_spec)
        
        # Calculate overall score
        overall_score = (
            param_score * WEIGHTS['parameter_description'] +
            completeness_score * WEIGHTS['tool_completeness'] +
            usability_score * WEIGHTS['llm_usability']
        )
        
        # Determine quality level
        quality_level = self._determine_quality_level(overall_score)
        
        # Identify issues
        issues = self._identify_issues(tool_spec, param_score, completeness_score, usability_score)
        
        return {
            'tool_name': tool_name,
            'file_path': str(yaml_file.relative_to(self.tools_dir.parent)),
            'category': category,
            'scores': {
                'parameter_description': param_score,
                'tool_completeness': completeness_score,
                'llm_usability': usability_score,
                'overall': overall_score
            },
            'quality_level': quality_level,
            'issues': issues,
            'pattern_count': self._count_patterns(tool_spec),
            'parameter_count': self._count_parameters(tool_spec)
        }
    
    def _score_parameter_descriptions(self, tool_spec: Dict) -> float:
        """Score parameter description quality (0-100)."""
        score = 0
        total_params = 0
        
        capabilities = tool_spec.get('capabilities', {})
        for cap_name, cap_data in capabilities.items():
            patterns = cap_data.get('patterns', {})
            for pattern_name, pattern_data in patterns.items():
                # Check required inputs
                required_inputs = pattern_data.get('required_inputs', [])
                for param in required_inputs:
                    total_params += 1
                    param_score = self._score_single_parameter(param)
                    score += param_score
                
                # Check optional inputs
                optional_inputs = pattern_data.get('optional_inputs', [])
                for param in optional_inputs:
                    total_params += 1
                    param_score = self._score_single_parameter(param)
                    score += param_score
        
        if total_params == 0:
            return 0
        
        return (score / total_params)
    
    def _score_single_parameter(self, param: Dict) -> float:
        """Score a single parameter (0-100)."""
        score = 0
        description = param.get('description', '')
        
        # Basic description exists (20 points)
        if description and len(description) > 10:
            score += 20
        
        # Has examples (25 points)
        if 'example' in description.lower() or '→' in description or 'Examples:' in description:
            score += 25
        
        # Has value ranges (25 points)
        if any(keyword in description.lower() for keyword in ['range', 'minimum', 'maximum', 'typical', 'default']):
            score += 25
        
        # Has "when to use" guidance (15 points)
        if any(keyword in description.lower() for keyword in ['use this', 'use when', 'for', 'to']):
            score += 15
        
        # Has natural language mapping (15 points)
        if any(keyword in description.lower() for keyword in ['natural language', 'mapping', 'request:', '"']):
            score += 15
        
        return min(score, 100)
    
    def _score_tool_completeness(self, tool_spec: Dict) -> float:
        """Score tool completeness (0-100)."""
        score = 0
        
        # Has specific patterns (not "execute" or "primary_capability") (20 points)
        capabilities = tool_spec.get('capabilities', {})
        has_generic_pattern = False
        pattern_count = 0
        
        for cap_name, cap_data in capabilities.items():
            if cap_name in ['primary_capability', 'main_capability']:
                has_generic_pattern = True
            
            patterns = cap_data.get('patterns', {})
            for pattern_name in patterns.keys():
                pattern_count += 1
                if pattern_name in ['execute', 'run', 'main']:
                    has_generic_pattern = True
        
        if not has_generic_pattern and pattern_count > 0:
            score += 20
        
        # Has examples section (20 points)
        if 'examples' in tool_spec and len(tool_spec['examples']) > 0:
            score += 20
        
        # Has limitations documented (20 points)
        has_limitations = False
        for cap_name, cap_data in capabilities.items():
            patterns = cap_data.get('patterns', {})
            for pattern_name, pattern_data in patterns.items():
                if 'limitations' in pattern_data and len(pattern_data['limitations']) > 0:
                    has_limitations = True
                    break
        if has_limitations:
            score += 20
        
        # Has validation rules (20 points)
        has_validation = False
        for cap_name, cap_data in capabilities.items():
            patterns = cap_data.get('patterns', {})
            for pattern_name, pattern_data in patterns.items():
                required_inputs = pattern_data.get('required_inputs', [])
                for param in required_inputs:
                    if 'validation' in param and param['validation'] != '.*':
                        has_validation = True
                        break
        if has_validation:
            score += 20
        
        # Has specific typical use cases (not generic) (20 points)
        has_specific_use_cases = False
        for cap_name, cap_data in capabilities.items():
            patterns = cap_data.get('patterns', {})
            for pattern_name, pattern_data in patterns.items():
                use_cases = pattern_data.get('typical_use_cases', [])
                for use_case in use_cases:
                    # Check if use case is not generic
                    if not any(generic in use_case.lower() for generic in ['use ', 'command', 'tool']):
                        has_specific_use_cases = True
                        break
        if has_specific_use_cases:
            score += 20
        
        return score
    
    def _score_llm_usability(self, tool_spec: Dict) -> float:
        """Score LLM usability (0-100)."""
        score = 0
        
        # Parameter descriptions teach the LLM (50 points)
        param_score = self._score_parameter_descriptions(tool_spec)
        if param_score >= 80:
            score += 50
        elif param_score >= 60:
            score += 35
        elif param_score >= 40:
            score += 20
        
        # Examples show natural language → parameters (50 points)
        examples = tool_spec.get('examples', [])
        if len(examples) > 0:
            has_good_examples = False
            for example in examples:
                if 'description' in example and 'inputs' in example:
                    # Check if description is natural language
                    desc = example['description'].lower()
                    if len(desc) > 10 and not desc.startswith('execute'):
                        has_good_examples = True
                        break
            
            if has_good_examples:
                score += 50
            else:
                score += 25
        
        return score
    
    def _determine_quality_level(self, overall_score: float) -> str:
        """Determine quality level based on overall score."""
        if overall_score >= 80:
            return "Level 4: Excellent"
        elif overall_score >= 60:
            return "Level 3: Good"
        elif overall_score >= 40:
            return "Level 2: Basic"
        else:
            return "Level 1: Minimal"
    
    def _identify_issues(self, tool_spec: Dict, param_score: float, 
                        completeness_score: float, usability_score: float) -> List[str]:
        """Identify specific issues with the tool."""
        issues = []
        
        if param_score < 60:
            issues.append("Parameter descriptions need enrichment")
        
        if completeness_score < 60:
            # Check specific issues
            capabilities = tool_spec.get('capabilities', {})
            for cap_name, cap_data in capabilities.items():
                if cap_name in ['primary_capability', 'main_capability']:
                    issues.append("Generic capability name")
                
                patterns = cap_data.get('patterns', {})
                for pattern_name in patterns.keys():
                    if pattern_name in ['execute', 'run', 'main']:
                        issues.append("Generic pattern name")
            
            if 'examples' not in tool_spec or len(tool_spec['examples']) == 0:
                issues.append("No examples provided")
        
        if usability_score < 60:
            issues.append("Low LLM usability - needs better examples and descriptions")
        
        return issues
    
    def _count_patterns(self, tool_spec: Dict) -> int:
        """Count total patterns in the tool."""
        count = 0
        capabilities = tool_spec.get('capabilities', {})
        for cap_data in capabilities.values():
            patterns = cap_data.get('patterns', {})
            count += len(patterns)
        return count
    
    def _count_parameters(self, tool_spec: Dict) -> int:
        """Count total parameters in the tool."""
        count = 0
        capabilities = tool_spec.get('capabilities', {})
        for cap_data in capabilities.values():
            patterns = cap_data.get('patterns', {})
            for pattern_data in patterns.values():
                count += len(pattern_data.get('required_inputs', []))
                count += len(pattern_data.get('optional_inputs', []))
        return count
    
    def generate_report(self, output_file: str = None):
        """Generate a detailed audit report."""
        if not self.results:
            print("No audit results available. Run audit_all_tools() first.")
            return
        
        # Sort by overall score (lowest first)
        sorted_results = sorted(self.results, key=lambda x: x['scores']['overall'])
        
        # Group by category
        by_category = defaultdict(list)
        for result in sorted_results:
            by_category[result['category']].append(result)
        
        # Generate report
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("TOOL CATALOG QUALITY AUDIT REPORT")
        report_lines.append("=" * 80)
        report_lines.append("")
        
        # Summary statistics
        total_tools = len(self.results)
        avg_score = sum(r['scores']['overall'] for r in self.results) / total_tools
        level_counts = defaultdict(int)
        for result in self.results:
            level_counts[result['quality_level']] += 1
        
        report_lines.append(f"Total Tools Audited: {total_tools}")
        report_lines.append(f"Average Overall Score: {avg_score:.1f}/100")
        report_lines.append("")
        report_lines.append("Quality Level Distribution:")
        for level in ["Level 4: Excellent", "Level 3: Good", "Level 2: Basic", "Level 1: Minimal"]:
            count = level_counts[level]
            percentage = (count / total_tools) * 100
            report_lines.append(f"  {level}: {count} ({percentage:.1f}%)")
        report_lines.append("")
        
        # Top 10 worst tools
        report_lines.append("=" * 80)
        report_lines.append("TOP 10 TOOLS NEEDING IMPROVEMENT (Lowest Scores)")
        report_lines.append("=" * 80)
        report_lines.append("")
        
        for i, result in enumerate(sorted_results[:10], 1):
            report_lines.append(f"{i}. {result['tool_name']} ({result['category']})")
            report_lines.append(f"   Overall Score: {result['scores']['overall']:.1f}/100")
            report_lines.append(f"   Quality Level: {result['quality_level']}")
            report_lines.append(f"   Issues: {', '.join(result['issues'])}")
            report_lines.append("")
        
        # By category
        report_lines.append("=" * 80)
        report_lines.append("RESULTS BY CATEGORY")
        report_lines.append("=" * 80)
        report_lines.append("")
        
        for category, tools in sorted(by_category.items()):
            avg_category_score = sum(t['scores']['overall'] for t in tools) / len(tools)
            report_lines.append(f"\n{category.upper()} ({len(tools)} tools, avg score: {avg_category_score:.1f})")
            report_lines.append("-" * 80)
            
            for tool in sorted(tools, key=lambda x: x['scores']['overall']):
                report_lines.append(
                    f"  {tool['tool_name']:30s} | "
                    f"Score: {tool['scores']['overall']:5.1f} | "
                    f"{tool['quality_level']:20s} | "
                    f"Patterns: {tool['pattern_count']:2d} | "
                    f"Params: {tool['parameter_count']:2d}"
                )
        
        report_lines.append("")
        report_lines.append("=" * 80)
        report_lines.append("END OF REPORT")
        report_lines.append("=" * 80)
        
        report_text = "\n".join(report_lines)
        
        if output_file:
            with open(output_file, 'w') as f:
                f.write(report_text)
            print(f"Report saved to: {output_file}")
        else:
            print(report_text)


def main():
    parser = argparse.ArgumentParser(description='Audit tool catalog quality')
    parser.add_argument('--tool', help='Audit specific tool by name')
    parser.add_argument('--category', help='Audit specific category')
    parser.add_argument('--report', action='store_true', help='Generate detailed report')
    parser.add_argument('--output', help='Output file for report')
    parser.add_argument('--tools-dir', default='pipeline/config/tools', 
                       help='Path to tools directory')
    
    args = parser.parse_args()
    
    # Get absolute path to tools directory
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    tools_dir = project_root / args.tools_dir
    
    if not tools_dir.exists():
        print(f"Error: Tools directory not found: {tools_dir}")
        sys.exit(1)
    
    auditor = ToolAuditor(str(tools_dir))
    
    if args.tool:
        # Audit specific tool
        tool_files = list(tools_dir.rglob(f'{args.tool}.yaml'))
        if not tool_files:
            print(f"Error: Tool '{args.tool}' not found")
            sys.exit(1)
        
        result = auditor.audit_tool(tool_files[0])
        print(f"\nTool: {result['tool_name']}")
        print(f"Category: {result['category']}")
        print(f"Quality Level: {result['quality_level']}")
        print(f"\nScores:")
        print(f"  Parameter Description: {result['scores']['parameter_description']:.1f}/100")
        print(f"  Tool Completeness: {result['scores']['tool_completeness']:.1f}/100")
        print(f"  LLM Usability: {result['scores']['llm_usability']:.1f}/100")
        print(f"  Overall: {result['scores']['overall']:.1f}/100")
        print(f"\nIssues:")
        for issue in result['issues']:
            print(f"  - {issue}")
        print(f"\nPatterns: {result['pattern_count']}")
        print(f"Parameters: {result['parameter_count']}")
    
    elif args.category:
        # Audit specific category
        category_dir = tools_dir / args.category
        if not category_dir.exists():
            print(f"Error: Category '{args.category}' not found")
            sys.exit(1)
        
        print(f"Auditing category: {args.category}")
        for yaml_file in category_dir.glob('*.yaml'):
            result = auditor.audit_tool(yaml_file)
            auditor.results.append(result)
        
        auditor.generate_report(args.output)
    
    else:
        # Audit all tools
        print("Auditing all tools...")
        auditor.audit_all_tools()
        
        if args.report:
            auditor.generate_report(args.output)
        else:
            # Print summary
            total = len(auditor.results)
            avg_score = sum(r['scores']['overall'] for r in auditor.results) / total
            print(f"\nAudited {total} tools")
            print(f"Average overall score: {avg_score:.1f}/100")
            print("\nUse --report flag to generate detailed report")


if __name__ == '__main__':
    main()