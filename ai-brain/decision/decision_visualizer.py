"""
OUIOE Phase 4: Decision Visualizer

Advanced decision tree visualization system that provides real-time,
interactive visualization of AI decision processes with intelligent progress tracking.

Key Features:
- Real-time decision tree generation and rendering
- Interactive decision path exploration and navigation
- Dynamic progress visualization with intelligent milestones
- Confidence and uncertainty visualization with heat maps
- Multi-dimensional decision analytics and insights
"""

import asyncio
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Callable, Union, Tuple
import json
import logging
from datetime import datetime, timedelta
import math

logger = logging.getLogger(__name__)


class NodeType(Enum):
    """Types of decision tree nodes"""
    ROOT = "root"                 # Root decision node
    ANALYSIS = "analysis"         # Analysis step node
    OPTION = "option"            # Decision option node
    CRITERIA = "criteria"        # Evaluation criteria node
    EVIDENCE = "evidence"        # Supporting evidence node
    ALTERNATIVE = "alternative"  # Alternative path node
    DECISION = "decision"        # Final decision node
    OUTCOME = "outcome"          # Predicted outcome node


class NodeStatus(Enum):
    """Status of decision tree nodes"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    SELECTED = "selected"
    REJECTED = "rejected"
    UNCERTAIN = "uncertain"


class VisualizationMode(Enum):
    """Visualization display modes"""
    TREE = "tree"                # Traditional tree layout
    RADIAL = "radial"           # Radial/circular layout
    FORCE_DIRECTED = "force_directed"  # Force-directed graph
    HIERARCHICAL = "hierarchical"     # Hierarchical layout
    TIMELINE = "timeline"       # Timeline-based layout
    SANKEY = "sankey"          # Sankey diagram flow


@dataclass
class DecisionNode:
    """Individual node in decision tree"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    label: str = ""
    node_type: NodeType = NodeType.ANALYSIS
    status: NodeStatus = NodeStatus.PENDING
    confidence: float = 0.0
    weight: float = 1.0
    
    # Content
    description: str = ""
    reasoning: str = ""
    evidence: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Tree structure
    parent_id: Optional[str] = None
    children_ids: List[str] = field(default_factory=list)
    
    # Visualization properties
    position: Tuple[float, float] = (0.0, 0.0)
    size: float = 1.0
    color: str = "#3498db"
    opacity: float = 1.0
    
    # Timing
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    processing_time: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'id': self.id,
            'label': self.label,
            'node_type': self.node_type.value,
            'status': self.status.value,
            'confidence': self.confidence,
            'weight': self.weight,
            'description': self.description,
            'reasoning': self.reasoning,
            'evidence': self.evidence,
            'metadata': self.metadata,
            'parent_id': self.parent_id,
            'children_ids': self.children_ids,
            'position': self.position,
            'size': self.size,
            'color': self.color,
            'opacity': self.opacity,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'processing_time': self.processing_time
        }


@dataclass
class DecisionEdge:
    """Edge connecting decision tree nodes"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source_id: str = ""
    target_id: str = ""
    label: str = ""
    weight: float = 1.0
    confidence: float = 0.0
    
    # Visualization properties
    color: str = "#95a5a6"
    thickness: float = 1.0
    style: str = "solid"  # solid, dashed, dotted
    opacity: float = 1.0
    
    # Metadata
    relationship_type: str = "leads_to"
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'id': self.id,
            'source_id': self.source_id,
            'target_id': self.target_id,
            'label': self.label,
            'weight': self.weight,
            'confidence': self.confidence,
            'color': self.color,
            'thickness': self.thickness,
            'style': self.style,
            'opacity': self.opacity,
            'relationship_type': self.relationship_type,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat()
        }


@dataclass
class DecisionTree:
    """Complete decision tree structure"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    description: str = ""
    
    # Tree structure
    nodes: Dict[str, DecisionNode] = field(default_factory=dict)
    edges: Dict[str, DecisionEdge] = field(default_factory=dict)
    root_node_id: Optional[str] = None
    
    # Visualization settings
    layout_mode: VisualizationMode = VisualizationMode.TREE
    zoom_level: float = 1.0
    center_position: Tuple[float, float] = (0.0, 0.0)
    
    # Analytics
    total_nodes: int = 0
    total_edges: int = 0
    max_depth: int = 0
    average_confidence: float = 0.0
    completion_percentage: float = 0.0
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_node(self, node: DecisionNode) -> str:
        """Add a node to the tree"""
        self.nodes[node.id] = node
        self.total_nodes = len(self.nodes)
        self.updated_at = datetime.now()
        
        # Set as root if first node
        if not self.root_node_id:
            self.root_node_id = node.id
        
        return node.id
    
    def add_edge(self, edge: DecisionEdge) -> str:
        """Add an edge to the tree"""
        self.edges[edge.id] = edge
        self.total_edges = len(self.edges)
        self.updated_at = datetime.now()
        
        # Update parent-child relationships
        if edge.source_id in self.nodes and edge.target_id in self.nodes:
            source_node = self.nodes[edge.source_id]
            target_node = self.nodes[edge.target_id]
            
            if edge.target_id not in source_node.children_ids:
                source_node.children_ids.append(edge.target_id)
            
            target_node.parent_id = edge.source_id
        
        return edge.id
    
    def get_node(self, node_id: str) -> Optional[DecisionNode]:
        """Get a node by ID"""
        return self.nodes.get(node_id)
    
    def get_children(self, node_id: str) -> List[DecisionNode]:
        """Get child nodes of a given node"""
        node = self.nodes.get(node_id)
        if not node:
            return []
        
        return [self.nodes[child_id] for child_id in node.children_ids 
                if child_id in self.nodes]
    
    def get_path_to_root(self, node_id: str) -> List[DecisionNode]:
        """Get path from node to root"""
        path = []
        current_id = node_id
        
        while current_id and current_id in self.nodes:
            node = self.nodes[current_id]
            path.append(node)
            current_id = node.parent_id
        
        return list(reversed(path))
    
    def calculate_depth(self, node_id: str) -> int:
        """Calculate depth of a node"""
        return len(self.get_path_to_root(node_id)) - 1
    
    def update_analytics(self):
        """Update tree analytics"""
        if not self.nodes:
            return
        
        # Calculate max depth
        self.max_depth = max(self.calculate_depth(node_id) for node_id in self.nodes.keys())
        
        # Calculate average confidence
        confidences = [node.confidence for node in self.nodes.values()]
        self.average_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        
        # Calculate completion percentage
        completed_nodes = sum(1 for node in self.nodes.values() 
                            if node.status == NodeStatus.COMPLETED)
        self.completion_percentage = (completed_nodes / len(self.nodes)) * 100 if self.nodes else 0.0
        
        self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'nodes': {node_id: node.to_dict() for node_id, node in self.nodes.items()},
            'edges': {edge_id: edge.to_dict() for edge_id, edge in self.edges.items()},
            'root_node_id': self.root_node_id,
            'layout_mode': self.layout_mode.value,
            'zoom_level': self.zoom_level,
            'center_position': self.center_position,
            'total_nodes': self.total_nodes,
            'total_edges': self.total_edges,
            'max_depth': self.max_depth,
            'average_confidence': self.average_confidence,
            'completion_percentage': self.completion_percentage,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'metadata': self.metadata
        }


class DecisionVisualizer:
    """
    Advanced Decision Visualizer - Real-time decision tree visualization system
    
    Provides:
    - Real-time decision tree generation and rendering
    - Interactive decision path exploration
    - Dynamic progress visualization with intelligent milestones
    - Confidence and uncertainty visualization
    - Multi-dimensional decision analytics
    """
    
    def __init__(self, visualization_callback: Optional[Callable] = None):
        """Initialize the decision visualizer"""
        self.visualization_callback = visualization_callback
        
        # Active visualizations
        self.active_trees: Dict[str, DecisionTree] = {}
        self.tree_history: List[str] = []
        
        # Visualization settings
        self.default_layout = VisualizationMode.TREE
        self.color_schemes = self._initialize_color_schemes()
        self.layout_algorithms = self._initialize_layout_algorithms()
        
        # Performance tracking
        self.visualization_metrics = {
            'total_trees_created': 0,
            'total_nodes_rendered': 0,
            'average_render_time': 0.0,
            'interactive_sessions': 0
        }
        
        logger.info("🎨 Decision Visualizer initialized - Ready for real-time decision visualization!")
    
    def _initialize_color_schemes(self) -> Dict[str, Dict[str, str]]:
        """Initialize color schemes for different visualization modes"""
        return {
            'default': {
                'root': '#e74c3c',
                'analysis': '#3498db',
                'option': '#2ecc71',
                'criteria': '#f39c12',
                'evidence': '#9b59b6',
                'alternative': '#95a5a6',
                'decision': '#27ae60',
                'outcome': '#e67e22'
            },
            'confidence': {
                'high': '#27ae60',      # Green for high confidence
                'medium': '#f39c12',    # Orange for medium confidence
                'low': '#e74c3c',       # Red for low confidence
                'uncertain': '#95a5a6'  # Gray for uncertain
            },
            'status': {
                'pending': '#bdc3c7',
                'processing': '#3498db',
                'completed': '#27ae60',
                'selected': '#2ecc71',
                'rejected': '#e74c3c',
                'uncertain': '#f39c12'
            }
        }
    
    def _initialize_layout_algorithms(self) -> Dict[VisualizationMode, Callable]:
        """Initialize layout algorithms for different visualization modes"""
        return {
            VisualizationMode.TREE: self._calculate_tree_layout,
            VisualizationMode.RADIAL: self._calculate_radial_layout,
            VisualizationMode.FORCE_DIRECTED: self._calculate_force_directed_layout,
            VisualizationMode.HIERARCHICAL: self._calculate_hierarchical_layout,
            VisualizationMode.TIMELINE: self._calculate_timeline_layout,
            VisualizationMode.SANKEY: self._calculate_sankey_layout
        }
    
    async def create_decision_tree(self, decision_id: str, title: str = "", 
                                 description: str = "") -> DecisionTree:
        """Create a new decision tree for visualization"""
        tree = DecisionTree(
            id=decision_id,
            title=title or f"Decision Tree {decision_id[:8]}",
            description=description,
            layout_mode=self.default_layout
        )
        
        self.active_trees[decision_id] = tree
        self.tree_history.append(decision_id)
        self.visualization_metrics['total_trees_created'] += 1
        
        # Visualization callback
        if self.visualization_callback:
            await self.visualization_callback({
                'type': 'tree_created',
                'tree_id': decision_id,
                'tree': tree.to_dict()
            })
        
        logger.info(f"🌳 Created decision tree: {title} ({decision_id})")
        return tree
    
    async def add_decision_node(self, tree_id: str, node_type: NodeType, 
                              label: str, description: str = "", 
                              parent_id: Optional[str] = None,
                              confidence: float = 0.0) -> Optional[str]:
        """Add a node to the decision tree"""
        if tree_id not in self.active_trees:
            return None
        
        tree = self.active_trees[tree_id]
        
        # Create node
        node = DecisionNode(
            label=label,
            node_type=node_type,
            description=description,
            confidence=confidence,
            parent_id=parent_id,
            color=self._get_node_color(node_type, confidence)
        )
        
        # Add to tree
        node_id = tree.add_node(node)
        
        # Create edge if parent exists
        if parent_id and parent_id in tree.nodes:
            edge = DecisionEdge(
                source_id=parent_id,
                target_id=node_id,
                label="",
                confidence=confidence
            )
            tree.add_edge(edge)
        
        # Update layout
        await self._update_tree_layout(tree)
        
        # Update analytics
        tree.update_analytics()
        
        # Visualization callback
        if self.visualization_callback:
            await self.visualization_callback({
                'type': 'node_added',
                'tree_id': tree_id,
                'node': node.to_dict(),
                'tree_analytics': {
                    'total_nodes': tree.total_nodes,
                    'completion_percentage': tree.completion_percentage,
                    'average_confidence': tree.average_confidence
                }
            })
        
        self.visualization_metrics['total_nodes_rendered'] += 1
        
        logger.debug(f"➕ Added node: {label} to tree {tree_id}")
        return node_id
    
    async def update_node_status(self, tree_id: str, node_id: str, 
                               status: NodeStatus, confidence: float = None):
        """Update node status and confidence"""
        if tree_id not in self.active_trees:
            return
        
        tree = self.active_trees[tree_id]
        node = tree.get_node(node_id)
        
        if not node:
            return
        
        # Update node
        node.status = status
        node.updated_at = datetime.now()
        
        if confidence is not None:
            node.confidence = confidence
        
        # Update visual properties
        node.color = self._get_node_color(node.node_type, node.confidence, status)
        node.opacity = self._get_node_opacity(status)
        
        # Update analytics
        tree.update_analytics()
        
        # Visualization callback
        if self.visualization_callback:
            await self.visualization_callback({
                'type': 'node_updated',
                'tree_id': tree_id,
                'node_id': node_id,
                'status': status.value,
                'confidence': node.confidence,
                'tree_analytics': {
                    'completion_percentage': tree.completion_percentage,
                    'average_confidence': tree.average_confidence
                }
            })
    
    async def add_decision_path(self, tree_id: str, path_nodes: List[Dict[str, Any]]) -> List[str]:
        """Add a complete decision path to the tree"""
        if tree_id not in self.active_trees:
            return []
        
        added_node_ids = []
        parent_id = None
        
        for i, node_data in enumerate(path_nodes):
            node_id = await self.add_decision_node(
                tree_id=tree_id,
                node_type=NodeType(node_data.get('type', 'analysis')),
                label=node_data.get('label', f'Step {i+1}'),
                description=node_data.get('description', ''),
                parent_id=parent_id,
                confidence=node_data.get('confidence', 0.0)
            )
            
            if node_id:
                added_node_ids.append(node_id)
                parent_id = node_id
        
        return added_node_ids
    
    async def highlight_decision_path(self, tree_id: str, node_ids: List[str]):
        """Highlight a specific decision path"""
        if tree_id not in self.active_trees:
            return
        
        tree = self.active_trees[tree_id]
        
        # Reset all node highlights
        for node in tree.nodes.values():
            node.opacity = 0.6
        
        # Highlight path nodes
        for node_id in node_ids:
            node = tree.get_node(node_id)
            if node:
                node.opacity = 1.0
                node.size = 1.5
        
        # Visualization callback
        if self.visualization_callback:
            await self.visualization_callback({
                'type': 'path_highlighted',
                'tree_id': tree_id,
                'highlighted_nodes': node_ids
            })
    
    async def set_tree_layout(self, tree_id: str, layout_mode: VisualizationMode):
        """Change the layout mode of a decision tree"""
        if tree_id not in self.active_trees:
            return
        
        tree = self.active_trees[tree_id]
        tree.layout_mode = layout_mode
        
        # Recalculate layout
        await self._update_tree_layout(tree)
        
        # Visualization callback
        if self.visualization_callback:
            await self.visualization_callback({
                'type': 'layout_changed',
                'tree_id': tree_id,
                'layout_mode': layout_mode.value,
                'tree': tree.to_dict()
            })
    
    async def _update_tree_layout(self, tree: DecisionTree):
        """Update tree layout based on current layout mode"""
        if not tree.nodes:
            return
        
        layout_algorithm = self.layout_algorithms.get(tree.layout_mode, 
                                                    self._calculate_tree_layout)
        
        # Calculate positions
        positions = layout_algorithm(tree)
        
        # Update node positions
        for node_id, position in positions.items():
            node = tree.get_node(node_id)
            if node:
                node.position = position
        
        tree.updated_at = datetime.now()
    
    def _calculate_tree_layout(self, tree: DecisionTree) -> Dict[str, Tuple[float, float]]:
        """Calculate traditional tree layout positions"""
        positions = {}
        
        if not tree.root_node_id or tree.root_node_id not in tree.nodes:
            return positions
        
        # BFS to assign levels
        levels = {}
        queue = [(tree.root_node_id, 0)]
        
        while queue:
            node_id, level = queue.pop(0)
            levels[node_id] = level
            
            children = tree.get_children(node_id)
            for child in children:
                queue.append((child.id, level + 1))
        
        # Group nodes by level
        level_groups = {}
        for node_id, level in levels.items():
            if level not in level_groups:
                level_groups[level] = []
            level_groups[level].append(node_id)
        
        # Calculate positions
        y_spacing = 100
        x_spacing = 150
        
        for level, node_ids in level_groups.items():
            y = level * y_spacing
            total_width = (len(node_ids) - 1) * x_spacing
            start_x = -total_width / 2
            
            for i, node_id in enumerate(node_ids):
                x = start_x + i * x_spacing
                positions[node_id] = (x, y)
        
        return positions
    
    def _calculate_radial_layout(self, tree: DecisionTree) -> Dict[str, Tuple[float, float]]:
        """Calculate radial layout positions"""
        positions = {}
        
        if not tree.root_node_id:
            return positions
        
        # Place root at center
        positions[tree.root_node_id] = (0.0, 0.0)
        
        # Calculate positions for each level
        levels = {}
        queue = [(tree.root_node_id, 0)]
        
        while queue:
            node_id, level = queue.pop(0)
            levels[node_id] = level
            
            children = tree.get_children(node_id)
            for child in children:
                queue.append((child.id, level + 1))
        
        # Group by level and calculate radial positions
        level_groups = {}
        for node_id, level in levels.items():
            if level not in level_groups:
                level_groups[level] = []
            level_groups[level].append(node_id)
        
        for level, node_ids in level_groups.items():
            if level == 0:  # Root already positioned
                continue
            
            radius = level * 80
            angle_step = 2 * math.pi / len(node_ids) if node_ids else 0
            
            for i, node_id in enumerate(node_ids):
                angle = i * angle_step
                x = radius * math.cos(angle)
                y = radius * math.sin(angle)
                positions[node_id] = (x, y)
        
        return positions
    
    def _calculate_force_directed_layout(self, tree: DecisionTree) -> Dict[str, Tuple[float, float]]:
        """Calculate force-directed layout positions"""
        # Simplified force-directed algorithm
        positions = {}
        
        # Initialize random positions
        import random
        for node_id in tree.nodes.keys():
            x = random.uniform(-200, 200)
            y = random.uniform(-200, 200)
            positions[node_id] = (x, y)
        
        # Simple spring-based adjustment (simplified)
        for _ in range(10):  # Limited iterations for performance
            forces = {node_id: [0.0, 0.0] for node_id in tree.nodes.keys()}
            
            # Repulsive forces between all nodes
            for node1_id in tree.nodes.keys():
                for node2_id in tree.nodes.keys():
                    if node1_id != node2_id:
                        x1, y1 = positions[node1_id]
                        x2, y2 = positions[node2_id]
                        
                        dx = x1 - x2
                        dy = y1 - y2
                        distance = math.sqrt(dx*dx + dy*dy) + 0.1
                        
                        force = 1000 / (distance * distance)
                        forces[node1_id][0] += force * dx / distance
                        forces[node1_id][1] += force * dy / distance
            
            # Attractive forces for connected nodes
            for edge in tree.edges.values():
                x1, y1 = positions[edge.source_id]
                x2, y2 = positions[edge.target_id]
                
                dx = x2 - x1
                dy = y2 - y1
                distance = math.sqrt(dx*dx + dy*dy) + 0.1
                
                force = distance * 0.01
                forces[edge.source_id][0] += force * dx / distance
                forces[edge.source_id][1] += force * dy / distance
                forces[edge.target_id][0] -= force * dx / distance
                forces[edge.target_id][1] -= force * dy / distance
            
            # Apply forces
            for node_id in tree.nodes.keys():
                x, y = positions[node_id]
                fx, fy = forces[node_id]
                positions[node_id] = (x + fx * 0.1, y + fy * 0.1)
        
        return positions
    
    def _calculate_hierarchical_layout(self, tree: DecisionTree) -> Dict[str, Tuple[float, float]]:
        """Calculate hierarchical layout positions"""
        # Similar to tree layout but with more structured hierarchy
        return self._calculate_tree_layout(tree)
    
    def _calculate_timeline_layout(self, tree: DecisionTree) -> Dict[str, Tuple[float, float]]:
        """Calculate timeline-based layout positions"""
        positions = {}
        
        # Sort nodes by creation time
        sorted_nodes = sorted(tree.nodes.values(), key=lambda n: n.created_at)
        
        x_spacing = 120
        y_base = 0
        
        for i, node in enumerate(sorted_nodes):
            x = i * x_spacing
            y = y_base + (hash(node.node_type.value) % 3 - 1) * 50  # Slight vertical variation
            positions[node.id] = (x, y)
        
        return positions
    
    def _calculate_sankey_layout(self, tree: DecisionTree) -> Dict[str, Tuple[float, float]]:
        """Calculate Sankey diagram layout positions"""
        # Simplified Sankey-style layout
        return self._calculate_tree_layout(tree)
    
    def _get_node_color(self, node_type: NodeType, confidence: float = 0.0, 
                       status: NodeStatus = None) -> str:
        """Get color for node based on type, confidence, and status"""
        if status:
            return self.color_schemes['status'].get(status.value, '#95a5a6')
        
        if confidence > 0:
            if confidence >= 0.8:
                return self.color_schemes['confidence']['high']
            elif confidence >= 0.6:
                return self.color_schemes['confidence']['medium']
            elif confidence >= 0.3:
                return self.color_schemes['confidence']['low']
            else:
                return self.color_schemes['confidence']['uncertain']
        
        return self.color_schemes['default'].get(node_type.value, '#3498db')
    
    def _get_node_opacity(self, status: NodeStatus) -> float:
        """Get opacity for node based on status"""
        opacity_map = {
            NodeStatus.PENDING: 0.5,
            NodeStatus.PROCESSING: 0.8,
            NodeStatus.COMPLETED: 1.0,
            NodeStatus.SELECTED: 1.0,
            NodeStatus.REJECTED: 0.3,
            NodeStatus.UNCERTAIN: 0.6
        }
        return opacity_map.get(status, 1.0)
    
    def get_decision_tree(self, tree_id: str) -> Optional[DecisionTree]:
        """Get decision tree by ID"""
        return self.active_trees.get(tree_id)
    
    def get_tree_analytics(self, tree_id: str) -> Optional[Dict[str, Any]]:
        """Get analytics for a decision tree"""
        tree = self.active_trees.get(tree_id)
        if not tree:
            return None
        
        tree.update_analytics()
        
        return {
            'total_nodes': tree.total_nodes,
            'total_edges': tree.total_edges,
            'max_depth': tree.max_depth,
            'average_confidence': tree.average_confidence,
            'completion_percentage': tree.completion_percentage,
            'node_type_distribution': self._calculate_node_type_distribution(tree),
            'confidence_distribution': self._calculate_confidence_distribution(tree),
            'status_distribution': self._calculate_status_distribution(tree)
        }
    
    def _calculate_node_type_distribution(self, tree: DecisionTree) -> Dict[str, int]:
        """Calculate distribution of node types"""
        distribution = {}
        for node in tree.nodes.values():
            node_type = node.node_type.value
            distribution[node_type] = distribution.get(node_type, 0) + 1
        return distribution
    
    def _calculate_confidence_distribution(self, tree: DecisionTree) -> Dict[str, int]:
        """Calculate distribution of confidence levels"""
        distribution = {'high': 0, 'medium': 0, 'low': 0, 'uncertain': 0}
        
        for node in tree.nodes.values():
            if node.confidence >= 0.8:
                distribution['high'] += 1
            elif node.confidence >= 0.6:
                distribution['medium'] += 1
            elif node.confidence >= 0.3:
                distribution['low'] += 1
            else:
                distribution['uncertain'] += 1
        
        return distribution
    
    def _calculate_status_distribution(self, tree: DecisionTree) -> Dict[str, int]:
        """Calculate distribution of node statuses"""
        distribution = {}
        for node in tree.nodes.values():
            status = node.status.value
            distribution[status] = distribution.get(status, 0) + 1
        return distribution
    
    def get_visualizer_metrics(self) -> Dict[str, Any]:
        """Get visualizer performance metrics"""
        return self.visualization_metrics.copy()