"""
OUIOE Phase 5: Intelligent Workflow Generator

Revolutionary workflow generation system that creates intelligent,
context-aware workflows based on user intent, system state, and
available services. Uses AI-driven analysis to generate optimal
workflow structures with built-in adaptation points.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import json
import uuid

from .workflow_models import (
    IntelligentWorkflow, WorkflowTemplate, WorkflowStep, WorkflowDependency,
    WorkflowContext, WorkflowType, StepType, WorkflowPriority, WorkflowStatus,
    WorkflowGraph, WorkflowNode, WorkflowEdge, WorkflowMetrics
)
from ..decision import DecisionEngine, DecisionRequest, DecisionType
from ..integrations.thinking_llm_client import ThinkingLLMClient

logger = logging.getLogger(__name__)


class IntelligentWorkflowGenerator:
    """
    Intelligent workflow generation system that creates context-aware,
    adaptive workflows using AI-driven analysis and decision-making.
    """
    
    def __init__(self, decision_engine: DecisionEngine, llm_client: ThinkingLLMClient):
        self.decision_engine = decision_engine
        self.llm_client = llm_client
        self.workflow_templates = {}
        self.generation_history = []
        self.optimization_patterns = {}
        
        # Initialize built-in templates
        self._initialize_builtin_templates()
        
        logger.info("Intelligent Workflow Generator initialized")
    
    async def generate_workflow(
        self, 
        context: WorkflowContext,
        template_hint: Optional[str] = None
    ) -> IntelligentWorkflow:
        """
        Generate an intelligent workflow based on context and intent.
        
        Args:
            context: Workflow generation context
            template_hint: Optional template to use as starting point
            
        Returns:
            Generated intelligent workflow
        """
        try:
            logger.info(f"Generating workflow for intent: {context.primary_intent}")
            
            # Step 1: Analyze intent and determine workflow type
            workflow_analysis = await self._analyze_workflow_requirements(context)
            
            # Step 2: Select or generate workflow template
            template = await self._select_workflow_template(context, workflow_analysis, template_hint)
            
            # Step 3: Generate workflow steps
            steps = await self._generate_workflow_steps(context, template, workflow_analysis)
            
            # Step 4: Create dependencies and graph structure
            dependencies = await self._generate_dependencies(steps, context, workflow_analysis)
            graph = await self._create_workflow_graph(steps, dependencies)
            
            # Step 5: Add adaptation points and optimization hints
            await self._add_adaptation_points(graph, context, workflow_analysis)
            
            # Step 6: Create complete workflow
            workflow = IntelligentWorkflow(
                name=f"Workflow for {context.primary_intent}",
                description=f"Intelligent workflow generated for: {context.primary_intent}",
                workflow_type=workflow_analysis["workflow_type"],
                priority=self._determine_priority(context, workflow_analysis),
                context=context,
                template=template,
                graph=graph,
                metrics=WorkflowMetrics(workflow_id="")  # Will be set after creation
            )
            
            # Set workflow ID in metrics
            workflow.metrics.workflow_id = workflow.workflow_id
            workflow.metrics.total_steps = len(graph.nodes)
            
            # Step 7: Validate and optimize workflow
            await self._validate_workflow(workflow)
            await self._optimize_workflow(workflow)
            
            # Record generation for learning
            self._record_generation(workflow, context, workflow_analysis)
            
            logger.info(f"Generated workflow {workflow.workflow_id} with {len(steps)} steps")
            return workflow
            
        except Exception as e:
            logger.error(f"Error generating workflow: {str(e)}")
            raise
    
    async def _analyze_workflow_requirements(self, context: WorkflowContext) -> Dict[str, Any]:
        """Analyze context to determine workflow requirements"""
        
        # Use decision engine for intelligent analysis
        decision_request = DecisionRequest(
            request_id=f"workflow_analysis_{context.request_id}",
            decision_type=DecisionType.ANALYTICAL,
            context={
                "intent": context.primary_intent,
                "system_context": context.system_context,
                "available_services": context.available_services,
                "constraints": {
                    "safety": context.safety_constraints,
                    "resources": context.resource_constraints,
                    "time": context.time_constraints.total_seconds() if context.time_constraints else None
                }
            },
            question="Analyze this request and determine the optimal workflow structure, complexity, and requirements.",
            options=[
                "Simple sequential workflow",
                "Complex multi-step workflow", 
                "Parallel execution workflow",
                "Conditional branching workflow",
                "Iterative processing workflow",
                "Adaptive learning workflow"
            ]
        )
        
        decision_result = await self.decision_engine.make_decision(decision_request)
        
        # Parse LLM analysis for workflow characteristics
        analysis_prompt = f"""
        Analyze this operational request and provide workflow requirements:
        
        Intent: {context.primary_intent}
        Available Services: {context.available_services}
        System Context: {json.dumps(context.system_context, indent=2)}
        
        Provide analysis in JSON format:
        {{
            "workflow_type": "simple|complex|parallel|sequential|conditional|iterative|adaptive",
            "complexity_level": "low|medium|high|very_high",
            "estimated_steps": <number>,
            "required_services": [<list of services>],
            "critical_dependencies": [<list of dependencies>],
            "risk_factors": [<list of risks>],
            "optimization_opportunities": [<list of optimizations>],
            "adaptation_points": [<list of adaptation needs>],
            "success_criteria": [<list of success measures>]
        }}
        """
        
        llm_response = await self.llm_client.generate_response(
            analysis_prompt,
            context={"session_id": context.session_id}
        )
        
        try:
            analysis = json.loads(llm_response.content)
        except json.JSONDecodeError:
            # Fallback analysis
            analysis = {
                "workflow_type": "sequential",
                "complexity_level": "medium",
                "estimated_steps": 3,
                "required_services": context.available_services[:2],
                "critical_dependencies": [],
                "risk_factors": ["service_availability"],
                "optimization_opportunities": ["parallel_execution"],
                "adaptation_points": ["error_recovery"],
                "success_criteria": ["task_completion"]
            }
        
        # Combine decision engine and LLM analysis
        analysis["decision_confidence"] = decision_result.confidence
        analysis["decision_reasoning"] = decision_result.reasoning
        analysis["alternative_approaches"] = decision_result.alternatives
        
        return analysis
    
    async def _select_workflow_template(
        self, 
        context: WorkflowContext, 
        analysis: Dict[str, Any],
        template_hint: Optional[str] = None
    ) -> Optional[WorkflowTemplate]:
        """Select the best workflow template for the context"""
        
        if template_hint and template_hint in self.workflow_templates:
            return self.workflow_templates[template_hint]
        
        # Find matching templates
        matching_templates = []
        for template_id, template in self.workflow_templates.items():
            if self._template_matches_context(template, context, analysis):
                matching_templates.append((template_id, template))
        
        if not matching_templates:
            logger.info("No matching template found, will generate from scratch")
            return None
        
        # Use decision engine to select best template
        if len(matching_templates) > 1:
            decision_request = DecisionRequest(
                request_id=f"template_selection_{context.request_id}",
                decision_type=DecisionType.STRATEGIC,
                context={
                    "intent": context.primary_intent,
                    "analysis": analysis,
                    "templates": [{"id": tid, "name": t.name, "description": t.description} 
                                for tid, t in matching_templates]
                },
                question="Which workflow template is best suited for this request?",
                options=[f"{tid}: {t.name}" for tid, t in matching_templates]
            )
            
            decision_result = await self.decision_engine.make_decision(decision_request)
            
            # Extract template ID from decision
            selected_template_id = decision_result.selected_option.split(":")[0]
            return self.workflow_templates.get(selected_template_id)
        
        return matching_templates[0][1]
    
    async def _generate_workflow_steps(
        self, 
        context: WorkflowContext, 
        template: Optional[WorkflowTemplate],
        analysis: Dict[str, Any]
    ) -> List[WorkflowStep]:
        """Generate workflow steps based on context and template"""
        
        if template:
            # Adapt template steps to context
            steps = await self._adapt_template_steps(template, context, analysis)
        else:
            # Generate steps from scratch
            steps = await self._generate_steps_from_scratch(context, analysis)
        
        # Enhance steps with AI-driven optimizations
        enhanced_steps = await self._enhance_steps(steps, context, analysis)
        
        return enhanced_steps
    
    async def _adapt_template_steps(
        self, 
        template: WorkflowTemplate, 
        context: WorkflowContext,
        analysis: Dict[str, Any]
    ) -> List[WorkflowStep]:
        """Adapt template steps to specific context"""
        
        adapted_steps = []
        
        for step in template.steps:
            # Use LLM to adapt step parameters
            adaptation_prompt = f"""
            Adapt this workflow step for the specific context:
            
            Original Step:
            - Name: {step.name}
            - Type: {step.step_type}
            - Service: {step.service}
            - Action: {step.action}
            - Parameters: {json.dumps(step.parameters, indent=2)}
            
            Context:
            - Intent: {context.primary_intent}
            - System Context: {json.dumps(context.system_context, indent=2)}
            - User Preferences: {json.dumps(context.user_preferences, indent=2)}
            
            Provide adapted step in JSON format:
            {{
                "name": "<adapted name>",
                "parameters": {{<adapted parameters>}},
                "validation_rules": [<validation rules>],
                "success_criteria": [<success criteria>],
                "adaptation_notes": "<explanation of adaptations>"
            }}
            """
            
            llm_response = await self.llm_client.generate_response(
                adaptation_prompt,
                context={"session_id": context.session_id}
            )
            
            try:
                adaptation = json.loads(llm_response.content)
                
                adapted_step = WorkflowStep(
                    step_id=f"{step.step_id}_{context.request_id}",
                    name=adaptation.get("name", step.name),
                    step_type=step.step_type,
                    service=step.service,
                    action=step.action,
                    parameters={**step.parameters, **adaptation.get("parameters", {})},
                    dependencies=step.dependencies.copy(),
                    timeout=step.timeout,
                    retry_policy=step.retry_policy.copy(),
                    validation_rules=adaptation.get("validation_rules", step.validation_rules.copy()),
                    error_handling=step.error_handling.copy(),
                    adaptation_points=step.adaptation_points.copy(),
                    success_criteria=adaptation.get("success_criteria", step.success_criteria.copy()),
                    metadata={
                        **step.metadata,
                        "adapted_from_template": template.template_id,
                        "adaptation_notes": adaptation.get("adaptation_notes", "")
                    }
                )
                
                adapted_steps.append(adapted_step)
                
            except json.JSONDecodeError:
                # Use original step if adaptation fails
                adapted_steps.append(step)
        
        return adapted_steps
    
    async def _generate_steps_from_scratch(
        self, 
        context: WorkflowContext,
        analysis: Dict[str, Any]
    ) -> List[WorkflowStep]:
        """Generate workflow steps from scratch using AI"""
        
        generation_prompt = f"""
        Generate workflow steps for this operational request:
        
        Intent: {context.primary_intent}
        Available Services: {context.available_services}
        Required Services: {analysis.get('required_services', [])}
        Estimated Steps: {analysis.get('estimated_steps', 3)}
        Complexity: {analysis.get('complexity_level', 'medium')}
        
        System Context: {json.dumps(context.system_context, indent=2)}
        
        Generate {analysis.get('estimated_steps', 3)} workflow steps in JSON format:
        {{
            "steps": [
                {{
                    "name": "<step name>",
                    "step_type": "action|decision|validation|transformation|integration|monitoring",
                    "service": "<service name>",
                    "action": "<action to perform>",
                    "parameters": {{<step parameters>}},
                    "timeout_seconds": <timeout>,
                    "retry_policy": {{
                        "max_retries": <number>,
                        "retry_delay": <seconds>,
                        "backoff_multiplier": <multiplier>
                    }},
                    "validation_rules": [<validation rules>],
                    "success_criteria": [<success criteria>],
                    "error_handling": {{
                        "on_failure": "<action on failure>",
                        "recovery_steps": [<recovery steps>]
                    }}
                }}
            ]
        }}
        """
        
        llm_response = await self.llm_client.generate_response(
            generation_prompt,
            context={"session_id": context.session_id}
        )
        
        try:
            generation_result = json.loads(llm_response.content)
            steps = []
            
            for i, step_data in enumerate(generation_result.get("steps", [])):
                step = WorkflowStep(
                    step_id=f"step_{i+1}_{context.request_id}",
                    name=step_data.get("name", f"Step {i+1}"),
                    step_type=StepType(step_data.get("step_type", "action")),
                    service=step_data.get("service", "unknown"),
                    action=step_data.get("action", "execute"),
                    parameters=step_data.get("parameters", {}),
                    timeout=timedelta(seconds=step_data.get("timeout_seconds", 300)),
                    retry_policy=step_data.get("retry_policy", {
                        "max_retries": 3,
                        "retry_delay": 5,
                        "backoff_multiplier": 2
                    }),
                    validation_rules=step_data.get("validation_rules", []),
                    error_handling=step_data.get("error_handling", {}),
                    success_criteria=step_data.get("success_criteria", []),
                    metadata={
                        "generated_from_scratch": True,
                        "generation_context": context.primary_intent
                    }
                )
                steps.append(step)
            
            return steps
            
        except json.JSONDecodeError:
            # Fallback: generate basic steps
            return self._generate_fallback_steps(context, analysis)
    
    def _generate_fallback_steps(
        self, 
        context: WorkflowContext,
        analysis: Dict[str, Any]
    ) -> List[WorkflowStep]:
        """Generate basic fallback steps when AI generation fails"""
        
        steps = []
        required_services = analysis.get('required_services', context.available_services[:2])
        
        for i, service in enumerate(required_services):
            step = WorkflowStep(
                step_id=f"fallback_step_{i+1}_{context.request_id}",
                name=f"Execute on {service}",
                step_type=StepType.ACTION,
                service=service,
                action="execute_request",
                parameters={"intent": context.primary_intent},
                timeout=timedelta(minutes=5),
                retry_policy={"max_retries": 3, "retry_delay": 5, "backoff_multiplier": 2},
                validation_rules=["check_service_response"],
                success_criteria=["operation_completed"],
                metadata={"fallback_generated": True}
            )
            steps.append(step)
        
        return steps
    
    async def _enhance_steps(
        self, 
        steps: List[WorkflowStep], 
        context: WorkflowContext,
        analysis: Dict[str, Any]
    ) -> List[WorkflowStep]:
        """Enhance steps with AI-driven optimizations"""
        
        enhanced_steps = []
        
        for step in steps:
            # Add adaptation points based on analysis
            adaptation_points = step.adaptation_points.copy()
            for point in analysis.get('adaptation_points', []):
                if point not in adaptation_points:
                    adaptation_points.append(point)
            
            # Enhance error handling
            error_handling = step.error_handling.copy()
            if 'fallback_service' not in error_handling and len(context.available_services) > 1:
                # Add fallback service if available
                current_service_index = context.available_services.index(step.service) if step.service in context.available_services else 0
                if current_service_index < len(context.available_services) - 1:
                    error_handling['fallback_service'] = context.available_services[current_service_index + 1]
            
            # Add monitoring based on risk factors
            monitoring_rules = []
            for risk in analysis.get('risk_factors', []):
                if risk == 'service_availability':
                    monitoring_rules.append('monitor_service_health')
                elif risk == 'resource_constraints':
                    monitoring_rules.append('monitor_resource_usage')
                elif risk == 'timeout':
                    monitoring_rules.append('monitor_execution_time')
            
            enhanced_step = WorkflowStep(
                step_id=step.step_id,
                name=step.name,
                step_type=step.step_type,
                service=step.service,
                action=step.action,
                parameters=step.parameters,
                dependencies=step.dependencies,
                timeout=step.timeout,
                retry_policy=step.retry_policy,
                validation_rules=step.validation_rules,
                error_handling=error_handling,
                adaptation_points=adaptation_points,
                success_criteria=step.success_criteria,
                metadata={
                    **step.metadata,
                    "enhanced": True,
                    "monitoring_rules": monitoring_rules,
                    "enhancement_timestamp": datetime.now().isoformat()
                }
            )
            
            enhanced_steps.append(enhanced_step)
        
        return enhanced_steps
    
    async def _generate_dependencies(
        self, 
        steps: List[WorkflowStep], 
        context: WorkflowContext,
        analysis: Dict[str, Any]
    ) -> List[WorkflowDependency]:
        """Generate dependencies between workflow steps"""
        
        dependencies = []
        workflow_type = analysis.get('workflow_type', 'sequential')
        
        if workflow_type == 'sequential':
            # Sequential dependencies
            for i in range(len(steps) - 1):
                dependency = WorkflowDependency(
                    from_step=steps[i].step_id,
                    to_step=steps[i + 1].step_id,
                    dependency_type="completion",
                    timeout=timedelta(minutes=1)
                )
                dependencies.append(dependency)
        
        elif workflow_type == 'parallel':
            # Parallel execution with final synchronization
            if len(steps) > 2:
                # All steps except last depend on first
                for i in range(1, len(steps) - 1):
                    dependency = WorkflowDependency(
                        from_step=steps[0].step_id,
                        to_step=steps[i].step_id,
                        dependency_type="completion"
                    )
                    dependencies.append(dependency)
                
                # Last step depends on all parallel steps
                for i in range(1, len(steps) - 1):
                    dependency = WorkflowDependency(
                        from_step=steps[i].step_id,
                        to_step=steps[-1].step_id,
                        dependency_type="completion"
                    )
                    dependencies.append(dependency)
        
        elif workflow_type == 'conditional':
            # Add conditional dependencies based on step types
            for i, step in enumerate(steps):
                if step.step_type == StepType.DECISION and i < len(steps) - 1:
                    # Decision step creates conditional dependency
                    dependency = WorkflowDependency(
                        from_step=step.step_id,
                        to_step=steps[i + 1].step_id,
                        dependency_type="condition",
                        condition="decision_result == 'proceed'"
                    )
                    dependencies.append(dependency)
                elif i > 0 and steps[i - 1].step_type != StepType.DECISION:
                    # Regular completion dependency
                    dependency = WorkflowDependency(
                        from_step=steps[i - 1].step_id,
                        to_step=step.step_id,
                        dependency_type="completion"
                    )
                    dependencies.append(dependency)
        
        else:
            # Default to sequential for other types
            for i in range(len(steps) - 1):
                dependency = WorkflowDependency(
                    from_step=steps[i].step_id,
                    to_step=steps[i + 1].step_id,
                    dependency_type="completion"
                )
                dependencies.append(dependency)
        
        # Add data dependencies based on step parameters
        await self._add_data_dependencies(dependencies, steps, analysis)
        
        return dependencies
    
    async def _add_data_dependencies(
        self, 
        dependencies: List[WorkflowDependency], 
        steps: List[WorkflowStep],
        analysis: Dict[str, Any]
    ):
        """Add data dependencies between steps"""
        
        # Analyze step parameters to identify data flow
        for i, step in enumerate(steps):
            for j, other_step in enumerate(steps):
                if i != j and self._steps_have_data_dependency(step, other_step):
                    # Check if dependency already exists
                    existing = any(
                        d.from_step == step.step_id and d.to_step == other_step.step_id
                        for d in dependencies
                    )
                    
                    if not existing:
                        dependency = WorkflowDependency(
                            from_step=step.step_id,
                            to_step=other_step.step_id,
                            dependency_type="data",
                            data_mapping=self._create_data_mapping(step, other_step)
                        )
                        dependencies.append(dependency)
    
    def _steps_have_data_dependency(self, step1: WorkflowStep, step2: WorkflowStep) -> bool:
        """Check if two steps have data dependency"""
        
        # Simple heuristic: if step2 parameters reference step1 outputs
        step1_outputs = step1.metadata.get('expected_outputs', [])
        step2_inputs = list(step2.parameters.keys())
        
        return any(output in step2_inputs for output in step1_outputs)
    
    def _create_data_mapping(self, from_step: WorkflowStep, to_step: WorkflowStep) -> Dict[str, str]:
        """Create data mapping between steps"""
        
        mapping = {}
        from_outputs = from_step.metadata.get('expected_outputs', [])
        to_inputs = list(to_step.parameters.keys())
        
        for output in from_outputs:
            if output in to_inputs:
                mapping[output] = output
        
        return mapping
    
    async def _create_workflow_graph(
        self, 
        steps: List[WorkflowStep], 
        dependencies: List[WorkflowDependency]
    ) -> WorkflowGraph:
        """Create workflow graph from steps and dependencies"""
        
        graph = WorkflowGraph()
        
        # Create nodes
        for step in steps:
            node = WorkflowNode(step=step)
            graph.nodes[step.step_id] = node
        
        # Create edges
        for dependency in dependencies:
            edge = WorkflowEdge(
                from_node=dependency.from_step,
                to_node=dependency.to_step,
                dependency=dependency
            )
            graph.edges[edge.edge_id] = edge
        
        # Identify entry and exit points
        graph.entry_points = self._find_entry_points(steps, dependencies)
        graph.exit_points = self._find_exit_points(steps, dependencies)
        
        # Calculate critical path
        graph.critical_path = await self._calculate_critical_path(graph)
        
        # Identify parallel branches
        graph.parallel_branches = self._identify_parallel_branches(graph)
        
        return graph
    
    def _find_entry_points(self, steps: List[WorkflowStep], dependencies: List[WorkflowDependency]) -> List[str]:
        """Find workflow entry points (steps with no incoming dependencies)"""
        
        steps_with_incoming = {dep.to_step for dep in dependencies}
        entry_points = [step.step_id for step in steps if step.step_id not in steps_with_incoming]
        
        return entry_points if entry_points else [steps[0].step_id] if steps else []
    
    def _find_exit_points(self, steps: List[WorkflowStep], dependencies: List[WorkflowDependency]) -> List[str]:
        """Find workflow exit points (steps with no outgoing dependencies)"""
        
        steps_with_outgoing = {dep.from_step for dep in dependencies}
        exit_points = [step.step_id for step in steps if step.step_id not in steps_with_outgoing]
        
        return exit_points if exit_points else [steps[-1].step_id] if steps else []
    
    async def _calculate_critical_path(self, graph: WorkflowGraph) -> List[str]:
        """Calculate critical path through workflow"""
        
        # Simple implementation: longest path from entry to exit
        if not graph.entry_points or not graph.exit_points:
            return []
        
        # For now, return simple path from first entry to first exit
        entry = graph.entry_points[0]
        exit_point = graph.exit_points[0]
        
        # Find path using BFS
        path = self._find_path(graph, entry, exit_point)
        return path
    
    def _find_path(self, graph: WorkflowGraph, start: str, end: str) -> List[str]:
        """Find path between two nodes"""
        
        if start == end:
            return [start]
        
        visited = set()
        queue = [(start, [start])]
        
        while queue:
            node, path = queue.pop(0)
            
            if node in visited:
                continue
            
            visited.add(node)
            
            # Find outgoing edges
            for edge in graph.edges.values():
                if edge.from_node == node:
                    next_node = edge.to_node
                    new_path = path + [next_node]
                    
                    if next_node == end:
                        return new_path
                    
                    queue.append((next_node, new_path))
        
        return []
    
    def _identify_parallel_branches(self, graph: WorkflowGraph) -> List[List[str]]:
        """Identify parallel execution branches"""
        
        branches = []
        
        # Find nodes that can execute in parallel
        for entry in graph.entry_points:
            # Find all nodes reachable from this entry
            reachable = self._find_reachable_nodes(graph, entry)
            
            # Group nodes that don't depend on each other
            parallel_groups = self._group_parallel_nodes(graph, reachable)
            branches.extend(parallel_groups)
        
        return branches
    
    def _find_reachable_nodes(self, graph: WorkflowGraph, start: str) -> List[str]:
        """Find all nodes reachable from start node"""
        
        visited = set()
        queue = [start]
        reachable = []
        
        while queue:
            node = queue.pop(0)
            
            if node in visited:
                continue
            
            visited.add(node)
            reachable.append(node)
            
            # Add connected nodes
            for edge in graph.edges.values():
                if edge.from_node == node:
                    queue.append(edge.to_node)
        
        return reachable
    
    def _group_parallel_nodes(self, graph: WorkflowGraph, nodes: List[str]) -> List[List[str]]:
        """Group nodes that can execute in parallel"""
        
        # Simple implementation: nodes with same depth level
        depth_groups = {}
        
        for node in nodes:
            depth = self._calculate_node_depth(graph, node)
            if depth not in depth_groups:
                depth_groups[depth] = []
            depth_groups[depth].append(node)
        
        # Return groups with more than one node
        return [group for group in depth_groups.values() if len(group) > 1]
    
    def _calculate_node_depth(self, graph: WorkflowGraph, node: str) -> int:
        """Calculate depth of node from entry points"""
        
        if node in graph.entry_points:
            return 0
        
        # Find minimum depth from any entry point
        min_depth = float('inf')
        
        for entry in graph.entry_points:
            path = self._find_path(graph, entry, node)
            if path:
                min_depth = min(min_depth, len(path) - 1)
        
        return min_depth if min_depth != float('inf') else 0
    
    async def _add_adaptation_points(
        self, 
        graph: WorkflowGraph, 
        context: WorkflowContext,
        analysis: Dict[str, Any]
    ):
        """Add adaptation points to workflow graph"""
        
        adaptation_opportunities = analysis.get('adaptation_points', [])
        
        for node_id, node in graph.nodes.items():
            # Add adaptation points based on step type and risk factors
            if node.step.step_type in [StepType.ACTION, StepType.INTEGRATION]:
                node.step.adaptation_points.extend([
                    'service_failure_recovery',
                    'timeout_handling',
                    'resource_optimization'
                ])
            
            if node.step.step_type == StepType.DECISION:
                node.step.adaptation_points.extend([
                    'decision_confidence_threshold',
                    'alternative_decision_paths'
                ])
            
            # Add context-specific adaptation points
            for opportunity in adaptation_opportunities:
                if opportunity not in node.step.adaptation_points:
                    node.step.adaptation_points.append(opportunity)
    
    async def _validate_workflow(self, workflow: IntelligentWorkflow):
        """Validate workflow structure and configuration"""
        
        # Check for cycles
        if self._has_cycles(workflow.graph):
            logger.warning(f"Workflow {workflow.workflow_id} contains cycles")
        
        # Check for unreachable nodes
        unreachable = self._find_unreachable_nodes(workflow.graph)
        if unreachable:
            logger.warning(f"Workflow {workflow.workflow_id} has unreachable nodes: {unreachable}")
        
        # Validate service availability
        await self._validate_service_availability(workflow)
        
        # Check resource requirements
        self._validate_resource_requirements(workflow)
    
    def _has_cycles(self, graph: WorkflowGraph) -> bool:
        """Check if workflow graph has cycles"""
        
        visited = set()
        rec_stack = set()
        
        def has_cycle_util(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)
            
            # Check all adjacent nodes
            for edge in graph.edges.values():
                if edge.from_node == node:
                    next_node = edge.to_node
                    if next_node not in visited:
                        if has_cycle_util(next_node):
                            return True
                    elif next_node in rec_stack:
                        return True
            
            rec_stack.remove(node)
            return False
        
        # Check all nodes
        for node_id in graph.nodes:
            if node_id not in visited:
                if has_cycle_util(node_id):
                    return True
        
        return False
    
    def _find_unreachable_nodes(self, graph: WorkflowGraph) -> List[str]:
        """Find nodes that are not reachable from entry points"""
        
        reachable = set()
        
        for entry in graph.entry_points:
            reachable.update(self._find_reachable_nodes(graph, entry))
        
        all_nodes = set(graph.nodes.keys())
        unreachable = all_nodes - reachable
        
        return list(unreachable)
    
    async def _validate_service_availability(self, workflow: IntelligentWorkflow):
        """Validate that required services are available"""
        
        required_services = set()
        for node in workflow.graph.nodes.values():
            required_services.add(node.step.service)
        
        available_services = set(workflow.context.available_services)
        unavailable = required_services - available_services
        
        if unavailable:
            logger.warning(f"Workflow {workflow.workflow_id} requires unavailable services: {unavailable}")
    
    def _validate_resource_requirements(self, workflow: IntelligentWorkflow):
        """Validate resource requirements against constraints"""
        
        # Calculate estimated resource usage
        estimated_memory = 0
        estimated_cpu = 0
        estimated_time = timedelta()
        
        for node in workflow.graph.nodes.values():
            # Simple estimation based on step type
            if node.step.step_type == StepType.ACTION:
                estimated_memory += 100  # MB
                estimated_cpu += 0.1  # CPU cores
            elif node.step.step_type == StepType.INTEGRATION:
                estimated_memory += 50
                estimated_cpu += 0.05
            
            if node.step.timeout:
                estimated_time += node.step.timeout
        
        # Check against constraints
        resource_constraints = workflow.context.resource_constraints
        if 'max_memory_mb' in resource_constraints:
            if estimated_memory > resource_constraints['max_memory_mb']:
                logger.warning(f"Workflow {workflow.workflow_id} may exceed memory limit")
        
        if 'max_cpu_cores' in resource_constraints:
            if estimated_cpu > resource_constraints['max_cpu_cores']:
                logger.warning(f"Workflow {workflow.workflow_id} may exceed CPU limit")
    
    async def _optimize_workflow(self, workflow: IntelligentWorkflow):
        """Optimize workflow structure and configuration"""
        
        # Optimize parallel execution opportunities
        await self._optimize_parallelization(workflow)
        
        # Optimize resource allocation
        self._optimize_resource_allocation(workflow)
        
        # Optimize timeout values
        self._optimize_timeouts(workflow)
        
        # Add caching opportunities
        self._add_caching_opportunities(workflow)
    
    async def _optimize_parallelization(self, workflow: IntelligentWorkflow):
        """Optimize workflow for parallel execution"""
        
        # Find steps that can be parallelized
        for branch in workflow.graph.parallel_branches:
            if len(branch) > 1:
                # Mark steps as parallelizable
                for node_id in branch:
                    node = workflow.graph.nodes[node_id]
                    node.step.metadata['parallelizable'] = True
                    node.step.metadata['parallel_group'] = branch
    
    def _optimize_resource_allocation(self, workflow: IntelligentWorkflow):
        """Optimize resource allocation for workflow steps"""
        
        total_steps = len(workflow.graph.nodes)
        resource_constraints = workflow.context.resource_constraints
        
        if 'max_memory_mb' in resource_constraints:
            memory_per_step = resource_constraints['max_memory_mb'] / total_steps
            
            for node in workflow.graph.nodes.values():
                node.step.metadata['allocated_memory_mb'] = memory_per_step
        
        if 'max_cpu_cores' in resource_constraints:
            cpu_per_step = resource_constraints['max_cpu_cores'] / total_steps
            
            for node in workflow.graph.nodes.values():
                node.step.metadata['allocated_cpu_cores'] = cpu_per_step
    
    def _optimize_timeouts(self, workflow: IntelligentWorkflow):
        """Optimize timeout values based on step complexity"""
        
        for node in workflow.graph.nodes.values():
            if not node.step.timeout:
                # Set default timeout based on step type
                if node.step.step_type == StepType.ACTION:
                    node.step.timeout = timedelta(minutes=5)
                elif node.step.step_type == StepType.INTEGRATION:
                    node.step.timeout = timedelta(minutes=10)
                elif node.step.step_type == StepType.DECISION:
                    node.step.timeout = timedelta(minutes=2)
                else:
                    node.step.timeout = timedelta(minutes=3)
    
    def _add_caching_opportunities(self, workflow: IntelligentWorkflow):
        """Add caching opportunities to workflow steps"""
        
        for node in workflow.graph.nodes.values():
            # Add caching for expensive operations
            if node.step.step_type in [StepType.INTEGRATION, StepType.TRANSFORMATION]:
                node.step.metadata['cacheable'] = True
                node.step.metadata['cache_ttl'] = 300  # 5 minutes
    
    def _determine_priority(self, context: WorkflowContext, analysis: Dict[str, Any]) -> WorkflowPriority:
        """Determine workflow priority based on context"""
        
        # Check for priority indicators in context
        if 'emergency' in context.primary_intent.lower():
            return WorkflowPriority.EMERGENCY
        elif 'urgent' in context.primary_intent.lower() or 'critical' in context.primary_intent.lower():
            return WorkflowPriority.CRITICAL
        elif 'high' in context.user_preferences.get('priority', '').lower():
            return WorkflowPriority.HIGH
        elif analysis.get('complexity_level') == 'very_high':
            return WorkflowPriority.HIGH
        else:
            return WorkflowPriority.NORMAL
    
    def _template_matches_context(
        self, 
        template: WorkflowTemplate, 
        context: WorkflowContext,
        analysis: Dict[str, Any]
    ) -> bool:
        """Check if template matches the current context"""
        
        # Check intent matching
        intent_match = any(
            intent.lower() in context.primary_intent.lower()
            for intent in template.applicable_intents
        )
        
        # Check service availability
        service_match = all(
            service in context.available_services
            for service in template.required_services
        )
        
        # Check workflow type compatibility
        type_match = template.workflow_type.value == analysis.get('workflow_type', 'sequential')
        
        return intent_match and service_match and type_match
    
    def _record_generation(
        self, 
        workflow: IntelligentWorkflow, 
        context: WorkflowContext,
        analysis: Dict[str, Any]
    ):
        """Record workflow generation for learning"""
        
        generation_record = {
            'workflow_id': workflow.workflow_id,
            'context': {
                'intent': context.primary_intent,
                'services': context.available_services,
                'constraints': context.resource_constraints
            },
            'analysis': analysis,
            'generated_steps': len(workflow.graph.nodes),
            'workflow_type': workflow.workflow_type.value,
            'generation_time': datetime.now().isoformat(),
            'template_used': workflow.template.template_id if workflow.template else None
        }
        
        self.generation_history.append(generation_record)
        
        # Keep only recent history
        if len(self.generation_history) > 1000:
            self.generation_history = self.generation_history[-1000:]
    
    def _initialize_builtin_templates(self):
        """Initialize built-in workflow templates"""
        
        # Asset Management Template
        asset_template = WorkflowTemplate(
            template_id="asset_management",
            name="Asset Management Workflow",
            description="Template for asset-related operations",
            workflow_type=WorkflowType.SEQUENTIAL,
            applicable_intents=["list assets", "get asset", "update asset", "manage assets"],
            required_services=["asset-service"],
            steps=[
                WorkflowStep(
                    step_id="validate_request",
                    name="Validate Request",
                    step_type=StepType.VALIDATION,
                    service="asset-service",
                    action="validate_request",
                    parameters={"validation_rules": ["check_permissions", "validate_parameters"]},
                    timeout=timedelta(seconds=30)
                ),
                WorkflowStep(
                    step_id="execute_operation",
                    name="Execute Asset Operation",
                    step_type=StepType.ACTION,
                    service="asset-service",
                    action="execute_operation",
                    parameters={},
                    dependencies=["validate_request"],
                    timeout=timedelta(minutes=5)
                ),
                WorkflowStep(
                    step_id="verify_result",
                    name="Verify Result",
                    step_type=StepType.VALIDATION,
                    service="asset-service",
                    action="verify_result",
                    parameters={"verification_rules": ["check_completion", "validate_output"]},
                    dependencies=["execute_operation"],
                    timeout=timedelta(seconds=30)
                )
            ],
            dependencies=[
                WorkflowDependency("validate_request", "execute_operation", "completion"),
                WorkflowDependency("execute_operation", "verify_result", "completion")
            ]
        )
        
        # Automation Template
        automation_template = WorkflowTemplate(
            template_id="automation_execution",
            name="Automation Execution Workflow",
            description="Template for automation job execution",
            workflow_type=WorkflowType.SEQUENTIAL,
            applicable_intents=["run job", "execute automation", "start task", "automate"],
            required_services=["automation-service"],
            steps=[
                WorkflowStep(
                    step_id="prepare_job",
                    name="Prepare Job",
                    step_type=StepType.ACTION,
                    service="automation-service",
                    action="prepare_job",
                    parameters={"preparation_steps": ["validate_targets", "prepare_environment"]},
                    timeout=timedelta(minutes=2)
                ),
                WorkflowStep(
                    step_id="execute_job",
                    name="Execute Job",
                    step_type=StepType.ACTION,
                    service="automation-service",
                    action="execute_job",
                    parameters={},
                    dependencies=["prepare_job"],
                    timeout=timedelta(minutes=30)
                ),
                WorkflowStep(
                    step_id="monitor_execution",
                    name="Monitor Execution",
                    step_type=StepType.MONITORING,
                    service="automation-service",
                    action="monitor_execution",
                    parameters={"monitoring_interval": 10},
                    dependencies=["execute_job"],
                    timeout=timedelta(minutes=35)
                )
            ],
            dependencies=[
                WorkflowDependency("prepare_job", "execute_job", "completion"),
                WorkflowDependency("execute_job", "monitor_execution", "completion")
            ]
        )
        
        # Multi-Service Template
        multi_service_template = WorkflowTemplate(
            template_id="multi_service_coordination",
            name="Multi-Service Coordination Workflow",
            description="Template for operations requiring multiple services",
            workflow_type=WorkflowType.PARALLEL,
            applicable_intents=["comprehensive analysis", "full system check", "complete operation"],
            required_services=["asset-service", "automation-service", "network-analyzer-service"],
            steps=[
                WorkflowStep(
                    step_id="gather_assets",
                    name="Gather Asset Information",
                    step_type=StepType.ACTION,
                    service="asset-service",
                    action="get_all_assets",
                    parameters={},
                    timeout=timedelta(minutes=2)
                ),
                WorkflowStep(
                    step_id="analyze_network",
                    name="Analyze Network",
                    step_type=StepType.ACTION,
                    service="network-analyzer-service",
                    action="analyze_network",
                    parameters={},
                    timeout=timedelta(minutes=5)
                ),
                WorkflowStep(
                    step_id="check_automation_status",
                    name="Check Automation Status",
                    step_type=StepType.ACTION,
                    service="automation-service",
                    action="get_job_status",
                    parameters={},
                    timeout=timedelta(minutes=1)
                ),
                WorkflowStep(
                    step_id="correlate_results",
                    name="Correlate Results",
                    step_type=StepType.TRANSFORMATION,
                    service="ai-brain",
                    action="correlate_data",
                    parameters={},
                    dependencies=["gather_assets", "analyze_network", "check_automation_status"],
                    timeout=timedelta(minutes=3)
                )
            ],
            dependencies=[
                WorkflowDependency("gather_assets", "correlate_results", "completion"),
                WorkflowDependency("analyze_network", "correlate_results", "completion"),
                WorkflowDependency("check_automation_status", "correlate_results", "completion")
            ]
        )
        
        # Store templates
        self.workflow_templates = {
            "asset_management": asset_template,
            "automation_execution": automation_template,
            "multi_service_coordination": multi_service_template
        }
        
        logger.info(f"Initialized {len(self.workflow_templates)} built-in workflow templates")
    
    async def add_template(self, template: WorkflowTemplate):
        """Add a new workflow template"""
        self.workflow_templates[template.template_id] = template
        logger.info(f"Added workflow template: {template.template_id}")
    
    async def get_template(self, template_id: str) -> Optional[WorkflowTemplate]:
        """Get workflow template by ID"""
        return self.workflow_templates.get(template_id)
    
    async def list_templates(self) -> List[WorkflowTemplate]:
        """List all available workflow templates"""
        return list(self.workflow_templates.values())
    
    async def get_generation_history(self) -> List[Dict[str, Any]]:
        """Get workflow generation history"""
        return self.generation_history.copy()
    
    async def get_optimization_patterns(self) -> Dict[str, Any]:
        """Get learned optimization patterns"""
        return self.optimization_patterns.copy()