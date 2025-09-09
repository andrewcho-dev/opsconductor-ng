"""
Enhanced Visual Workflow Engine
Comprehensive translation of visual workflows to executable steps
"""
import json
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass
from enum import Enum
import re
from jinja2 import Template, Environment, StrictUndefined

from .logging import get_logger
from .database import get_db_cursor

logger = get_logger(__name__)

class NodeType(Enum):
    # Flow control
    FLOW_START = "flow.start"
    FLOW_END = "flow.end"
    FLOW_DECISION = "flow.decision"
    FLOW_PARALLEL = "flow.parallel"
    FLOW_JOIN = "flow.join"
    
    # Actions
    ACTION_COMMAND = "action.command"
    ACTION_SCRIPT = "action.script"
    ACTION_HTTP = "action.http"
    ACTION_FILE_TRANSFER = "action.file_transfer"
    ACTION_DATABASE = "action.database"
    ACTION_NOTIFICATION = "action.notification"
    
    # Conditions
    CONDITION_IF = "condition.if"
    CONDITION_WHILE = "condition.while"
    CONDITION_FOR_EACH = "condition.for_each"
    
    # Data operations
    DATA_TRANSFORM = "data.transform"
    DATA_VALIDATE = "data.validate"
    DATA_AGGREGATE = "data.aggregate"

@dataclass
class WorkflowNode:
    """Represents a node in the visual workflow"""
    id: str
    type: NodeType
    data: Dict[str, Any]
    position: Dict[str, float]
    
@dataclass
class WorkflowEdge:
    """Represents an edge/connection in the visual workflow"""
    id: str
    source: str
    target: str
    source_handle: Optional[str] = None
    target_handle: Optional[str] = None
    data: Optional[Dict[str, Any]] = None

@dataclass
class ExecutionStep:
    """Represents an executable step"""
    id: str
    type: str
    order: int
    target_id: Optional[int]
    command: Optional[str]
    timeout: int
    connection_type: str
    parameters: Dict[str, Any]
    conditions: Optional[Dict[str, Any]] = None
    retry_config: Optional[Dict[str, Any]] = None

class VisualWorkflowEngine:
    """Enhanced visual workflow engine with comprehensive node support"""
    
    def __init__(self):
        self.jinja_env = Environment(undefined=StrictUndefined)
        
        # Node type handlers
        self.node_handlers = {
            NodeType.ACTION_COMMAND: self._handle_command_node,
            NodeType.ACTION_SCRIPT: self._handle_script_node,
            NodeType.ACTION_HTTP: self._handle_http_node,
            NodeType.ACTION_FILE_TRANSFER: self._handle_file_transfer_node,
            NodeType.ACTION_DATABASE: self._handle_database_node,
            NodeType.ACTION_NOTIFICATION: self._handle_notification_node,
            NodeType.CONDITION_IF: self._handle_if_node,
            NodeType.CONDITION_WHILE: self._handle_while_node,
            NodeType.CONDITION_FOR_EACH: self._handle_for_each_node,
            NodeType.DATA_TRANSFORM: self._handle_data_transform_node,
            NodeType.DATA_VALIDATE: self._handle_data_validate_node,
            NodeType.FLOW_DECISION: self._handle_decision_node,
            NodeType.FLOW_PARALLEL: self._handle_parallel_node,
        }
    
    def translate_workflow(
        self, 
        workflow_definition: Dict[str, Any], 
        parameters: Dict[str, Any]
    ) -> List[ExecutionStep]:
        """
        Translate visual workflow to executable steps
        
        Args:
            workflow_definition: Visual workflow with nodes and edges
            parameters: Runtime parameters for template substitution
            
        Returns:
            List of executable steps in proper order
        """
        try:
            # Parse nodes and edges
            nodes = self._parse_nodes(workflow_definition.get('nodes', []))
            edges = self._parse_edges(workflow_definition.get('edges', []))
            
            # Validate workflow structure
            self._validate_workflow(nodes, edges)
            
            # Build execution graph
            execution_graph = self._build_execution_graph(nodes, edges)
            
            # Resolve execution order
            execution_order = self._resolve_execution_order(execution_graph, nodes, edges)
            
            # Convert nodes to executable steps
            steps = []
            for order, node_id in enumerate(execution_order):
                node = nodes[node_id]
                
                if node.type in self.node_handlers:
                    step = self.node_handlers[node.type](node, parameters, order)
                    if step:
                        steps.append(step)
                else:
                    logger.warning(f"Unsupported node type: {node.type}")
            
            logger.info(f"Translated workflow to {len(steps)} executable steps")
            return steps
            
        except Exception as e:
            logger.error(f"Error translating workflow: {str(e)}")
            raise
    
    def _parse_nodes(self, nodes_data: List[Dict[str, Any]]) -> Dict[str, WorkflowNode]:
        """Parse nodes from workflow definition"""
        nodes = {}
        
        for node_data in nodes_data:
            try:
                node_type = NodeType(node_data.get('type', ''))
                node = WorkflowNode(
                    id=node_data['id'],
                    type=node_type,
                    data=node_data.get('data', {}),
                    position=node_data.get('position', {'x': 0, 'y': 0})
                )
                nodes[node.id] = node
                
            except ValueError:
                logger.warning(f"Unknown node type: {node_data.get('type')}")
                continue
        
        return nodes
    
    def _parse_edges(self, edges_data: List[Dict[str, Any]]) -> List[WorkflowEdge]:
        """Parse edges from workflow definition"""
        edges = []
        
        for edge_data in edges_data:
            edge = WorkflowEdge(
                id=edge_data.get('id', f"{edge_data['source']}-{edge_data['target']}"),
                source=edge_data['source'],
                target=edge_data['target'],
                source_handle=edge_data.get('sourceHandle'),
                target_handle=edge_data.get('targetHandle'),
                data=edge_data.get('data', {})
            )
            edges.append(edge)
        
        return edges
    
    def _validate_workflow(self, nodes: Dict[str, WorkflowNode], edges: List[WorkflowEdge]):
        """Validate workflow structure"""
        # Check for start node
        start_nodes = [n for n in nodes.values() if n.type == NodeType.FLOW_START]
        if not start_nodes:
            raise ValueError("Workflow must have at least one start node")
        
        # Check for orphaned nodes
        connected_nodes = set()
        for edge in edges:
            connected_nodes.add(edge.source)
            connected_nodes.add(edge.target)
        
        # Start nodes don't need incoming connections
        for node in nodes.values():
            if node.type != NodeType.FLOW_START and node.id not in connected_nodes:
                logger.warning(f"Orphaned node detected: {node.id}")
        
        # Check for cycles (basic check)
        self._check_for_cycles(nodes, edges)
    
    def _check_for_cycles(self, nodes: Dict[str, WorkflowNode], edges: List[WorkflowEdge]):
        """Basic cycle detection"""
        # Build adjacency list
        graph = {}
        for node_id in nodes:
            graph[node_id] = []
        
        for edge in edges:
            if edge.source in graph:
                graph[edge.source].append(edge.target)
        
        # DFS cycle detection
        visited = set()
        rec_stack = set()
        
        def has_cycle(node):
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    if has_cycle(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True
            
            rec_stack.remove(node)
            return False
        
        for node_id in nodes:
            if node_id not in visited:
                if has_cycle(node_id):
                    logger.warning("Cycle detected in workflow - this may cause infinite loops")
                    break
    
    def _build_execution_graph(
        self, 
        nodes: Dict[str, WorkflowNode], 
        edges: List[WorkflowEdge]
    ) -> Dict[str, List[str]]:
        """Build execution dependency graph"""
        graph = {}
        
        # Initialize graph
        for node_id in nodes:
            graph[node_id] = []
        
        # Add dependencies based on edges
        for edge in edges:
            if edge.target in graph:
                graph[edge.target].append(edge.source)
        
        return graph
    
    def _resolve_execution_order(
        self, 
        graph: Dict[str, List[str]], 
        nodes: Dict[str, WorkflowNode],
        edges: List[WorkflowEdge]
    ) -> List[str]:
        """Resolve execution order using topological sort"""
        # Find start nodes
        start_nodes = [n.id for n in nodes.values() if n.type == NodeType.FLOW_START]
        
        # Topological sort
        visited = set()
        order = []
        
        def dfs(node_id):
            if node_id in visited:
                return
            
            visited.add(node_id)
            
            # Visit dependencies first
            for dep in graph.get(node_id, []):
                dfs(dep)
            
            # Skip flow control nodes in execution order
            node = nodes[node_id]
            if node.type not in [NodeType.FLOW_START, NodeType.FLOW_END]:
                order.append(node_id)
        
        # Start DFS from all reachable nodes
        for start_node in start_nodes:
            # Find all nodes reachable from this start node
            reachable = self._find_reachable_nodes(start_node, edges)
            for node_id in reachable:
                dfs(node_id)
        
        return order
    
    def _find_reachable_nodes(self, start_node: str, edges: List[WorkflowEdge]) -> Set[str]:
        """Find all nodes reachable from start node"""
        reachable = set()
        queue = [start_node]
        
        while queue:
            current = queue.pop(0)
            if current in reachable:
                continue
            
            reachable.add(current)
            
            # Add connected nodes
            for edge in edges:
                if edge.source == current and edge.target not in reachable:
                    queue.append(edge.target)
        
        return reachable
    
    def _apply_template_substitution(self, text: str, parameters: Dict[str, Any]) -> str:
        """Apply Jinja2 template substitution"""
        if not text or not parameters:
            return text
        
        try:
            template = self.jinja_env.from_string(text)
            return template.render(**parameters)
        except Exception as e:
            logger.warning(f"Template substitution failed: {str(e)}")
            return text
    
    # Node handlers
    def _handle_command_node(
        self, 
        node: WorkflowNode, 
        parameters: Dict[str, Any], 
        order: int
    ) -> Optional[ExecutionStep]:
        """Handle command execution node"""
        data = node.data
        
        command = self._apply_template_substitution(data.get('command', ''), parameters)
        target_host = self._apply_template_substitution(data.get('target', ''), parameters)
        
        # Resolve target_id from target_host
        target_id = self._resolve_target_id(target_host)
        
        # Determine step type based on connection type
        connection_type = data.get('connection_type', 'ssh')
        if connection_type == 'winrm':
            step_type = 'winrm.exec'
        elif connection_type == 'ssh':
            step_type = 'ssh.exec'
        else:
            step_type = 'shell'  # fallback
        
        return ExecutionStep(
            id=node.id,
            type=step_type,
            order=order,
            target_id=target_id,
            command=command,
            timeout=data.get('timeout', 60),
            connection_type=connection_type,
            parameters={
                'working_directory': data.get('working_directory'),
                'environment_variables': data.get('environment_variables', {}),
                'username': self._apply_template_substitution(data.get('username', ''), parameters),
                'password': self._apply_template_substitution(data.get('password', ''), parameters),
                'port': data.get('port', 22),
                'use_ssl': data.get('use_ssl', False)
            }
        )
    
    def _handle_script_node(
        self, 
        node: WorkflowNode, 
        parameters: Dict[str, Any], 
        order: int
    ) -> Optional[ExecutionStep]:
        """Handle script execution node"""
        data = node.data
        
        script_content = self._apply_template_substitution(data.get('script', ''), parameters)
        target_host = self._apply_template_substitution(data.get('target', ''), parameters)
        
        target_id = self._resolve_target_id(target_host)
        
        return ExecutionStep(
            id=node.id,
            type='script',
            order=order,
            target_id=target_id,
            command=script_content,
            timeout=data.get('timeout', 300),
            connection_type=data.get('connection_type', 'ssh'),
            parameters={
                'script_type': data.get('script_type', 'bash'),
                'interpreter': data.get('interpreter', '/bin/bash'),
                'arguments': data.get('arguments', []),
                'working_directory': data.get('working_directory')
            }
        )
    
    def _handle_http_node(
        self, 
        node: WorkflowNode, 
        parameters: Dict[str, Any], 
        order: int
    ) -> Optional[ExecutionStep]:
        """Handle HTTP request node"""
        data = node.data
        
        url = self._apply_template_substitution(data.get('url', ''), parameters)
        
        return ExecutionStep(
            id=node.id,
            type='http',
            order=order,
            target_id=None,
            command=url,
            timeout=data.get('timeout', 30),
            connection_type='http',
            parameters={
                'method': data.get('method', 'GET'),
                'headers': data.get('headers', {}),
                'body': self._apply_template_substitution(str(data.get('body', '')), parameters),
                'auth': data.get('auth'),
                'verify_ssl': data.get('verify_ssl', True),
                'follow_redirects': data.get('follow_redirects', True)
            }
        )
    
    def _handle_file_transfer_node(
        self, 
        node: WorkflowNode, 
        parameters: Dict[str, Any], 
        order: int
    ) -> Optional[ExecutionStep]:
        """Handle file transfer node"""
        data = node.data
        
        source_path = self._apply_template_substitution(data.get('source_path', ''), parameters)
        dest_path = self._apply_template_substitution(data.get('dest_path', ''), parameters)
        target_host = self._apply_template_substitution(data.get('target', ''), parameters)
        
        target_id = self._resolve_target_id(target_host)
        
        return ExecutionStep(
            id=node.id,
            type='file_transfer',
            order=order,
            target_id=target_id,
            command=f"{source_path} -> {dest_path}",
            timeout=data.get('timeout', 300),
            connection_type=data.get('connection_type', 'sftp'),
            parameters={
                'source_path': source_path,
                'dest_path': dest_path,
                'direction': data.get('direction', 'upload'),  # upload/download
                'preserve_permissions': data.get('preserve_permissions', True),
                'recursive': data.get('recursive', False),
                'overwrite': data.get('overwrite', True)
            }
        )
    
    def _handle_database_node(
        self, 
        node: WorkflowNode, 
        parameters: Dict[str, Any], 
        order: int
    ) -> Optional[ExecutionStep]:
        """Handle database operation node"""
        data = node.data
        
        query = self._apply_template_substitution(data.get('query', ''), parameters)
        
        return ExecutionStep(
            id=node.id,
            type='database',
            order=order,
            target_id=None,
            command=query,
            timeout=data.get('timeout', 60),
            connection_type='database',
            parameters={
                'database_type': data.get('database_type', 'postgresql'),
                'connection_string': self._apply_template_substitution(data.get('connection_string', ''), parameters),
                'operation_type': data.get('operation_type', 'select'),  # select/insert/update/delete
                'fetch_results': data.get('fetch_results', True)
            }
        )
    
    def _handle_notification_node(
        self, 
        node: WorkflowNode, 
        parameters: Dict[str, Any], 
        order: int
    ) -> Optional[ExecutionStep]:
        """Handle notification node"""
        data = node.data
        
        message = self._apply_template_substitution(data.get('message', ''), parameters)
        
        return ExecutionStep(
            id=node.id,
            type='notification',
            order=order,
            target_id=None,
            command=message,
            timeout=data.get('timeout', 30),
            connection_type='notification',
            parameters={
                'notification_type': data.get('notification_type', 'email'),
                'recipients': data.get('recipients', []),
                'subject': self._apply_template_substitution(data.get('subject', ''), parameters),
                'priority': data.get('priority', 'normal')
            }
        )
    
    def _handle_if_node(
        self, 
        node: WorkflowNode, 
        parameters: Dict[str, Any], 
        order: int
    ) -> Optional[ExecutionStep]:
        """Handle conditional if node"""
        data = node.data
        
        condition = self._apply_template_substitution(data.get('condition', ''), parameters)
        
        return ExecutionStep(
            id=node.id,
            type='condition',
            order=order,
            target_id=None,
            command=condition,
            timeout=5,
            connection_type='condition',
            parameters={
                'condition_type': 'if',
                'condition_expression': condition,
                'true_branch': data.get('true_branch'),
                'false_branch': data.get('false_branch')
            },
            conditions={'expression': condition}
        )
    
    def _handle_while_node(
        self, 
        node: WorkflowNode, 
        parameters: Dict[str, Any], 
        order: int
    ) -> Optional[ExecutionStep]:
        """Handle while loop node"""
        data = node.data
        
        condition = self._apply_template_substitution(data.get('condition', ''), parameters)
        
        return ExecutionStep(
            id=node.id,
            type='loop',
            order=order,
            target_id=None,
            command=condition,
            timeout=data.get('max_iterations', 100) * 10,
            connection_type='loop',
            parameters={
                'loop_type': 'while',
                'condition_expression': condition,
                'max_iterations': data.get('max_iterations', 100),
                'loop_body': data.get('loop_body')
            },
            conditions={'expression': condition}
        )
    
    def _handle_for_each_node(
        self, 
        node: WorkflowNode, 
        parameters: Dict[str, Any], 
        order: int
    ) -> Optional[ExecutionStep]:
        """Handle for-each loop node"""
        data = node.data
        
        items = data.get('items', [])
        if isinstance(items, str):
            items = self._apply_template_substitution(items, parameters)
        
        return ExecutionStep(
            id=node.id,
            type='loop',
            order=order,
            target_id=None,
            command=str(items),
            timeout=len(items) * data.get('timeout_per_item', 60) if isinstance(items, list) else 300,
            connection_type='loop',
            parameters={
                'loop_type': 'for_each',
                'items': items,
                'item_variable': data.get('item_variable', 'item'),
                'loop_body': data.get('loop_body')
            }
        )
    
    def _handle_data_transform_node(
        self, 
        node: WorkflowNode, 
        parameters: Dict[str, Any], 
        order: int
    ) -> Optional[ExecutionStep]:
        """Handle data transformation node"""
        data = node.data
        
        return ExecutionStep(
            id=node.id,
            type='data_transform',
            order=order,
            target_id=None,
            command=data.get('transformation', ''),
            timeout=data.get('timeout', 30),
            connection_type='data',
            parameters={
                'input_data': data.get('input_data'),
                'transformation_type': data.get('transformation_type', 'json'),
                'transformation_script': data.get('transformation_script', ''),
                'output_format': data.get('output_format', 'json')
            }
        )
    
    def _handle_data_validate_node(
        self, 
        node: WorkflowNode, 
        parameters: Dict[str, Any], 
        order: int
    ) -> Optional[ExecutionStep]:
        """Handle data validation node"""
        data = node.data
        
        return ExecutionStep(
            id=node.id,
            type='data_validate',
            order=order,
            target_id=None,
            command=data.get('validation_rules', ''),
            timeout=data.get('timeout', 30),
            connection_type='data',
            parameters={
                'input_data': data.get('input_data'),
                'validation_schema': data.get('validation_schema'),
                'validation_rules': data.get('validation_rules', []),
                'fail_on_error': data.get('fail_on_error', True)
            }
        )
    
    def _handle_decision_node(
        self, 
        node: WorkflowNode, 
        parameters: Dict[str, Any], 
        order: int
    ) -> Optional[ExecutionStep]:
        """Handle decision/branching node"""
        data = node.data
        
        return ExecutionStep(
            id=node.id,
            type='decision',
            order=order,
            target_id=None,
            command=data.get('decision_logic', ''),
            timeout=5,
            connection_type='decision',
            parameters={
                'decision_type': data.get('decision_type', 'condition'),
                'branches': data.get('branches', []),
                'default_branch': data.get('default_branch')
            }
        )
    
    def _handle_parallel_node(
        self, 
        node: WorkflowNode, 
        parameters: Dict[str, Any], 
        order: int
    ) -> Optional[ExecutionStep]:
        """Handle parallel execution node"""
        data = node.data
        
        return ExecutionStep(
            id=node.id,
            type='parallel',
            order=order,
            target_id=None,
            command='parallel_execution',
            timeout=data.get('timeout', 300),
            connection_type='parallel',
            parameters={
                'parallel_branches': data.get('parallel_branches', []),
                'wait_for_all': data.get('wait_for_all', True),
                'max_concurrent': data.get('max_concurrent', 5)
            }
        )
    
    def _resolve_target_id(self, target_host: str) -> Optional[int]:
        """Resolve target hostname to target ID"""
        if not target_host:
            return None
        
        try:
            with get_db_cursor(commit=False) as cursor:
                cursor.execute("""
                    SELECT id FROM targets 
                    WHERE hostname = %s OR ip_address = %s
                    LIMIT 1
                """, (target_host, target_host))
                
                result = cursor.fetchone()
                return result['id'] if result else None
                
        except Exception as e:
            logger.warning(f"Could not resolve target '{target_host}': {str(e)}")
            return None

# Global workflow engine instance
workflow_engine = VisualWorkflowEngine()