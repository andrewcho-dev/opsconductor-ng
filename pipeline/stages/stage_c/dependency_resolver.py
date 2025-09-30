"""
Dependency Resolver for Stage C Planner

Manages step dependencies and creates proper execution sequencing.
Implements DAG (Directed Acyclic Graph) validation and topological sorting.
"""

from typing import Dict, List, Set, Optional, Tuple
from collections import defaultdict, deque

from ...schemas.plan_v1 import ExecutionStep


class DependencyError(Exception):
    """Raised when dependency resolution fails"""
    pass


class DependencyResolver:
    """
    Resolves step dependencies and creates proper execution ordering.
    
    This class is responsible for:
    - Validating dependency graphs for cycles
    - Performing topological sorting of steps
    - Identifying parallel execution opportunities
    - Resolving dependency conflicts
    - Creating execution phases
    """
    
    def __init__(self):
        """Initialize the dependency resolver"""
        self.dependency_graph = defaultdict(list)
        self.reverse_graph = defaultdict(list)
        self.step_map = {}
    
    def resolve_dependencies(self, steps: List[ExecutionStep]) -> List[ExecutionStep]:
        """
        Resolve dependencies and return steps in proper execution order.
        
        Args:
            steps: List of execution steps with dependencies
            
        Returns:
            Steps ordered for safe execution
            
        Raises:
            DependencyError: If circular dependencies or unresolvable conflicts exist
        """
        if not steps:
            return []
        
        # Build dependency graph
        self._build_dependency_graph(steps)
        
        # Validate for circular dependencies
        self._validate_no_cycles()
        
        # Perform topological sort
        ordered_steps = self._topological_sort()
        
        # Update execution order in steps
        self._update_execution_order(ordered_steps)
        
        return ordered_steps
    
    def identify_parallel_groups(self, steps: List[ExecutionStep]) -> List[List[ExecutionStep]]:
        """
        Identify groups of steps that can be executed in parallel.
        
        Args:
            steps: Dependency-resolved steps
            
        Returns:
            List of step groups, where each group can be executed in parallel
        """
        if not steps:
            return []
        
        # Build dependency graph
        self._build_dependency_graph(steps)
        
        # Group steps by dependency level
        levels = self._calculate_dependency_levels()
        
        # Create parallel groups
        parallel_groups = []
        max_level = max(levels.values()) if levels else 0
        
        for level in range(max_level + 1):
            level_steps = [
                step_id for step_id, step_level in levels.items() 
                if step_level == level
            ]
            if level_steps:
                parallel_groups.append([self.step_map[step_id] for step_id in level_steps])
        
        return parallel_groups
    
    def validate_dependencies(self, steps: List[ExecutionStep]) -> Tuple[bool, List[str]]:
        """
        Validate step dependencies and return validation results.
        
        Args:
            steps: Steps to validate
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        if not steps:
            return True, errors
        
        try:
            # Build dependency graph
            self._build_dependency_graph(steps)
            
            # Check for circular dependencies
            self._validate_no_cycles()
            
            # Check for missing dependencies
            missing_deps = self._find_missing_dependencies()
            if missing_deps:
                errors.extend([f"Missing dependency: {dep}" for dep in missing_deps])
            
            # Check for invalid step references
            invalid_refs = self._find_invalid_references()
            if invalid_refs:
                errors.extend([f"Invalid step reference: {ref}" for ref in invalid_refs])
            
        except DependencyError as e:
            errors.append(str(e))
        except Exception as e:
            errors.append(f"Dependency validation error: {str(e)}")
        
        return len(errors) == 0, errors
    
    def _build_dependency_graph(self, steps: List[ExecutionStep]) -> None:
        """Build internal dependency graph from steps"""
        self.dependency_graph.clear()
        self.reverse_graph.clear()
        self.step_map.clear()
        
        # Create step map
        for step in steps:
            self.step_map[step.id] = step
        
        # Build dependency graph
        for step in steps:
            step_id = step.id
            
            # Initialize node in graph
            if step_id not in self.dependency_graph:
                self.dependency_graph[step_id] = []
            
            # Add dependencies
            for dep_pattern in step.depends_on:
                # Handle wildcard dependencies (step_*_tool_*)
                if '*' in dep_pattern:
                    matching_deps = self._resolve_wildcard_dependency(dep_pattern, steps)
                    for dep_id in matching_deps:
                        if dep_id != step_id:  # Avoid self-dependency
                            self.dependency_graph[dep_id].append(step_id)
                            self.reverse_graph[step_id].append(dep_id)
                else:
                    # Direct dependency
                    if dep_pattern in self.step_map:
                        self.dependency_graph[dep_pattern].append(step_id)
                        self.reverse_graph[step_id].append(dep_pattern)
    
    def _resolve_wildcard_dependency(self, pattern: str, steps: List[ExecutionStep]) -> List[str]:
        """Resolve wildcard dependency patterns to actual step IDs"""
        matching_ids = []
        
        # Convert pattern to regex-like matching
        # Example: "step_*_systemctl_*" matches "step_001_systemctl_restart"
        pattern_parts = pattern.split('*')
        
        for step in steps:
            step_id = step.id
            matches = True
            
            # Check if step ID matches the pattern
            current_pos = 0
            for i, part in enumerate(pattern_parts):
                if not part:  # Empty part from consecutive wildcards
                    continue
                
                pos = step_id.find(part, current_pos)
                if pos == -1:
                    matches = False
                    break
                
                # For first part, must match from beginning
                if i == 0 and pos != 0:
                    matches = False
                    break
                
                # For last part, must match to end
                if i == len(pattern_parts) - 1 and not step_id.endswith(part):
                    matches = False
                    break
                
                current_pos = pos + len(part)
            
            if matches:
                matching_ids.append(step_id)
        
        return matching_ids
    
    def _validate_no_cycles(self) -> None:
        """Validate that the dependency graph has no cycles"""
        visited = set()
        rec_stack = set()
        
        def has_cycle(node):
            if node in rec_stack:
                return True
            if node in visited:
                return False
            
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in self.dependency_graph.get(node, []):
                if has_cycle(neighbor):
                    return True
            
            rec_stack.remove(node)
            return False
        
        for node in self.dependency_graph:
            if node not in visited:
                if has_cycle(node):
                    raise DependencyError(f"Circular dependency detected involving step: {node}")
    
    def _topological_sort(self) -> List[ExecutionStep]:
        """Perform topological sort using Kahn's algorithm"""
        # Calculate in-degrees
        in_degree = defaultdict(int)
        for node in self.step_map:
            in_degree[node] = 0
        
        for node in self.dependency_graph:
            for neighbor in self.dependency_graph[node]:
                in_degree[neighbor] += 1
        
        # Initialize queue with nodes having no dependencies
        queue = deque([node for node in in_degree if in_degree[node] == 0])
        result = []
        
        while queue:
            node = queue.popleft()
            result.append(self.step_map[node])
            
            # Reduce in-degree for neighbors
            for neighbor in self.dependency_graph.get(node, []):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        # Check if all nodes were processed
        if len(result) != len(self.step_map):
            unprocessed = [node for node in self.step_map if node not in [s.id for s in result]]
            raise DependencyError(f"Unable to resolve dependencies for steps: {unprocessed}")
        
        return result
    
    def _calculate_dependency_levels(self) -> Dict[str, int]:
        """Calculate dependency levels for parallel execution grouping"""
        levels = {}
        
        # Initialize all nodes at level 0
        for node in self.step_map:
            levels[node] = 0
        
        # Calculate levels using longest path
        def calculate_level(node, visited):
            if node in visited:
                return levels[node]
            
            visited.add(node)
            max_dep_level = -1
            
            for dep in self.reverse_graph.get(node, []):
                dep_level = calculate_level(dep, visited)
                max_dep_level = max(max_dep_level, dep_level)
            
            levels[node] = max_dep_level + 1
            return levels[node]
        
        for node in self.step_map:
            calculate_level(node, set())
        
        return levels
    
    def _update_execution_order(self, ordered_steps: List[ExecutionStep]) -> None:
        """Update execution_order field in steps based on resolved order"""
        for i, step in enumerate(ordered_steps, 1):
            step.execution_order = i
    
    def _find_missing_dependencies(self) -> List[str]:
        """Find dependencies that reference non-existent steps"""
        missing = []
        
        for step in self.step_map.values():
            for dep_pattern in step.depends_on:
                if '*' not in dep_pattern:  # Direct dependency
                    if dep_pattern not in self.step_map:
                        missing.append(dep_pattern)
                else:  # Wildcard dependency
                    matching = self._resolve_wildcard_dependency(dep_pattern, list(self.step_map.values()))
                    if not matching:
                        missing.append(dep_pattern)
        
        return list(set(missing))  # Remove duplicates
    
    def _find_invalid_references(self) -> List[str]:
        """Find invalid step references in dependencies"""
        invalid = []
        
        for step in self.step_map.values():
            for dep in step.depends_on:
                if dep == step.id:  # Self-dependency
                    invalid.append(f"Self-dependency in step {step.id}")
        
        return invalid
    
    def get_execution_phases(self, steps: List[ExecutionStep]) -> List[Dict[str, any]]:
        """
        Get execution phases with metadata for orchestration.
        
        Args:
            steps: Dependency-resolved steps
            
        Returns:
            List of execution phases with timing and dependency info
        """
        parallel_groups = self.identify_parallel_groups(steps)
        phases = []
        
        for i, group in enumerate(parallel_groups):
            phase = {
                "phase_id": f"phase_{i+1:03d}",
                "steps": [step.id for step in group],
                "can_run_parallel": len(group) > 1,
                "estimated_duration": max(step.estimated_duration for step in group),
                "total_steps": len(group),
                "dependencies_satisfied": i == 0 or f"phase_{i:03d}"
            }
            phases.append(phase)
        
        return phases