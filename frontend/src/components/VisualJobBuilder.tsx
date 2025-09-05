import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Job } from '../types';
import { stepLibraryService } from '../services/stepLibraryService';
import StepConfigModal from './StepConfigModal';
import { FileText, X, Play, Square, Target, MousePointer, AlertTriangle, RefreshCw, RotateCcw, Grid3X3, Package, Hand, ZoomIn, ZoomOut, Maximize2, AlignStartVertical, AlignCenterVertical, AlignEndVertical, AlignStartHorizontal, AlignCenterHorizontal, AlignEndHorizontal } from 'lucide-react';

// Inject CSS styles for the Visual Job Builder
const visualJobBuilderStyles = `
  .visual-job-builder {
    display: grid;
    grid-template-columns: 1fr 1fr 6fr 1fr;
    gap: 12px;
    height: calc(100vh - 110px);
    align-items: stretch;
  }

  .dashboard-section {
    background: white;
    border: 1px solid var(--neutral-200);
    border-radius: 6px;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    position: relative;
  }

  .section-header {
    padding: 12px 16px;
    border-bottom: 1px solid var(--neutral-200);
    background: var(--neutral-25);
    font-weight: 600;
    font-size: 13px;
    color: var(--neutral-700);
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: var(--space-2);
  }

  .section-content {
    flex: 1;
    padding: 16px;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
  }

  .node-properties h4 {
    margin: 0 0 var(--space-2) 0;
    font-size: 14px;
    font-weight: 600;
    color: var(--neutral-900);
  }

  .node-description {
    margin: 0 0 var(--space-1) 0;
    font-size: 12px;
    color: var(--neutral-600);
  }

  .no-selection {
    text-align: center;
    color: var(--neutral-500);
    font-size: 12px;
    margin-top: var(--space-4);
  }

  .no-selection p {
    margin: 0;
  }

  /* Canvas area styles */
  .job-canvas {
    flex: 1;
    position: relative;
    overflow: hidden;
    background-color: var(--neutral-0);
    background-image: radial-gradient(circle, var(--neutral-200) 1px, transparent 1px);
    background-size: 20px 20px;
  }

  /* Canvas Toolbar */
  .canvas-toolbar {
    position: absolute;
    top: 8px;
    left: 8px;
    background: white;
    border: 1px solid var(--neutral-300);
    border-radius: var(--radius-md);
    padding: 6px;
    display: flex;
    align-items: center;
    gap: 6px;
    z-index: 1000;
    box-shadow: var(--shadow-sm);
    white-space: nowrap;
  }

  .canvas-tool-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 32px;
    height: 32px;
    border: 1px solid var(--neutral-200);
    background: white;
    border-radius: var(--radius-sm);
    cursor: pointer;
    color: var(--neutral-700);
    transition: all 0.2s;
  }

  .canvas-tool-btn:hover {
    background-color: var(--neutral-100);
    color: var(--neutral-900);
  }

  .canvas-tool-btn.active {
    background-color: var(--primary-blue);
    color: white;
    border-color: var(--primary-blue);
  }

  .canvas-tool-btn:disabled {
    color: var(--neutral-400);
    cursor: not-allowed;
    opacity: 0.5;
  }

  .canvas-tool-btn:disabled:hover {
    background-color: transparent;
    color: var(--neutral-400);
  }

  .canvas-tool-separator {
    width: 1px;
    height: 24px;
    background-color: var(--neutral-300);
    margin: 0 4px;
  }

  /* Canvas Zoom Controls */
  .canvas-zoom-controls {
    position: absolute;
    bottom: 8px;
    right: 8px;
    background: white;
    border: 1px solid var(--neutral-300);
    border-radius: var(--radius-md);
    padding: 4px;
    display: flex;
    align-items: center;
    gap: 4px;
    z-index: 1000;
    box-shadow: var(--shadow-sm);
  }

  .zoom-level {
    font-size: 12px;
    font-weight: 500;
    color: var(--neutral-700);
    min-width: 40px;
    text-align: center;
  }

  /* Canvas Viewport */
  .canvas-viewport {
    width: 100%;
    height: 100%;
    position: relative;
    transform-origin: 0 0;
    transition: transform 0.2s ease-out;
  }

  .canvas-viewport.panning {
    transition: none;
  }

  .canvas-content {
    position: relative;
    width: 10000px;
    height: 10000px;
  }

  /* Cursor states */
  .job-canvas.hand-tool {
    cursor: grab;
  }

  .job-canvas.hand-tool.panning {
    cursor: grabbing;
  }

  .job-canvas.select-tool {
    cursor: default;
  }

  /* Selection rectangle */
  .selection-rectangle {
    position: absolute;
    border: 2px dashed var(--primary-blue-500);
    background-color: rgba(0, 123, 255, 0.1);
    pointer-events: none;
    z-index: 1000;
  }

  /* Multi-selected node styling */
  .canvas-node.selected {
    border: 2px solid var(--primary-blue-500) !important;
    box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.2) !important;
  }

  .canvas-node.multi-selected {
    border: 2px solid var(--warning-500) !important;
    box-shadow: 0 0 0 2px rgba(255, 193, 7, 0.2) !important;
  }

  /* Step library styles */}
  .step-library-search {
    width: 100%;
    padding: var(--space-2);
    border: 1px solid var(--neutral-300);
    border-radius: var(--radius-sm);
    font-size: 12px;
    margin-bottom: var(--space-2);
  }

  .step-library-filters {
    display: flex;
    gap: var(--space-2);
    margin-bottom: var(--space-3);
  }

  .step-library-filters select {
    flex: 1;
    padding: var(--space-1);
    border: 1px solid var(--neutral-300);
    border-radius: var(--radius-sm);
    font-size: 11px;
    background-color: var(--neutral-0);
  }

  .step-template {
    padding: var(--space-2);
    margin-bottom: var(--space-2);
    border: 1px solid var(--neutral-200);
    border-radius: var(--radius-sm);
    cursor: grab;
    transition: all 0.2s ease;
    background-color: var(--neutral-0);
  }

  .step-template:hover {
    border-color: var(--primary-blue-300);
    background-color: var(--primary-blue-25);
    transform: translateY(-1px);
  }

  .step-template:active {
    cursor: grabbing;
  }

  .step-template-header {
    display: flex;
    align-items: center;
    gap: var(--space-2);
    margin-bottom: var(--space-1);
  }

  .step-template-name {
    font-weight: 600;
    font-size: 11px;
    color: var(--neutral-900);
  }

  .step-template-meta {
    font-size: 10px;
    color: var(--neutral-600);
  }

  /* Library Navigator Styles */
  .library-list {
    display: flex;
    flex-direction: column;
    gap: 4px;
    margin-bottom: 16px;
  }

  .library-item {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 12px;
    border-radius: var(--radius-sm);
    cursor: pointer;
    transition: background-color 0.2s;
    font-size: 12px;
    font-weight: 500;
  }

  .library-item:hover {
    background-color: var(--neutral-100);
  }

  .library-item.selected {
    background-color: var(--primary-blue-100);
    color: var(--primary-blue-700);
  }

  .category-section {
    border-top: 1px solid var(--neutral-200);
    padding-top: 16px;
  }

  .category-header {
    font-size: 11px;
    font-weight: 600;
    color: var(--neutral-600);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin: 0 0 8px 0;
  }

  .category-list {
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  .category-item {
    padding: 6px 12px;
    border-radius: var(--radius-sm);
    cursor: pointer;
    transition: background-color 0.2s;
    font-size: 11px;
    font-weight: 500;
  }

  .category-item:hover {
    background-color: var(--neutral-100);
  }

  .category-item.selected {
    background-color: var(--primary-blue-100);
    color: var(--primary-blue-700);
  }

  /* Job Controls in Right Panel */
  .job-controls {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .form-group {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .form-label {
    font-size: 11px;
    font-weight: 600;
    color: var(--neutral-600);
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .form-input {
    padding: 6px 8px;
    border: 1px solid var(--neutral-300);
    border-radius: var(--radius-sm);
    font-size: 13px;
    background-color: var(--neutral-0);
    width: 100%;
    box-sizing: border-box;
  }

  .form-input:focus {
    outline: none;
    border-color: var(--primary-blue-400);
    box-shadow: 0 0 0 2px var(--primary-blue-100);
  }

  .job-actions {
    display: flex;
    gap: 8px;
    justify-content: flex-end;
  }

  /* Standard button styles */
  .btn-icon {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 24px;
    height: 24px;
    border: none;
    border-radius: var(--radius-sm);
    background-color: transparent;
    color: var(--neutral-600);
    cursor: pointer;
    margin: 0 1px;
    padding: 2px;
  }
  .btn-icon:hover {
    opacity: 0.7;
  }
  .btn-icon:disabled {
    opacity: 0.3;
    cursor: not-allowed;
  }



  /* Loading and error states */}
  .step-load-status {
    padding: var(--space-3);
    text-align: center;
    font-size: 12px;
  }

  .step-load-error {
    color: var(--semantic-error-600);
    background-color: var(--semantic-error-50);
    border: 1px solid var(--semantic-error-200);
    border-radius: var(--radius-sm);
    padding: var(--space-2);
    margin-bottom: var(--space-2);
  }

  .step-load-retry {
    margin-top: var(--space-2);
  }
`;

// Inject styles into head if not already present
if (typeof document !== 'undefined' && !document.getElementById('visual-job-builder-styles')) {
  const styleSheet = document.createElement('style');
  styleSheet.id = 'visual-job-builder-styles';
  styleSheet.textContent = visualJobBuilderStyles;
  document.head.appendChild(styleSheet);
}

interface VisualJobBuilderProps {
  onJobCreate: (jobData: any) => void;
  onCancel: () => void;
  editingJob?: Job | null;
  onRefreshSteps?: () => void;
  onSaveJob?: () => void;
}

interface FlowNode {
  id: string;
  type: string;
  name: string;
  x: number;
  y: number;
  width: number;
  height: number;
  config: any;
  inputs: number;
  outputs: number;
  category: string;
  library: string;
}

interface Connection {
  id: string;
  sourceNodeId: string;
  sourcePort: number;
  targetNodeId: string;
  targetPort: number;
}

interface NodeTemplate {
  id: string;
  name: string;
  type: string;
  category: string;
  library: string;
  icon: string;
  description: string;
  inputs: number;
  outputs: number;
  defaultConfig: any;
  color: string;
  parameters?: any[];
}

const getIconComponent = (iconName: string, size: number = 12) => {
  switch (iconName) {
    case 'play': return <Play size={size} />;
    case 'square': return <Square size={size} />;
    case 'target': return <Target size={size} />;
    default: return <FileText size={size} />;
  }
};

const VisualJobBuilder: React.FC<VisualJobBuilderProps> = ({ onJobCreate, onCancel, editingJob, onRefreshSteps, onSaveJob }) => {
  const [jobName, setJobName] = useState('');
  const [nodes, setNodes] = useState<FlowNode[]>([]);
  const [connections, setConnections] = useState<Connection[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [selectedLibrary, setSelectedLibrary] = useState<string>('all');
  const [draggedTemplate, setDraggedTemplate] = useState<NodeTemplate | null>(null);
  const [selectedNode, setSelectedNode] = useState<FlowNode | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });
  const [isConnecting, setIsConnecting] = useState(false);
  const [connectionStart, setConnectionStart] = useState<{ nodeId: string, port: number } | null>(null);
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 });
  const [showConfigModal, setShowConfigModal] = useState(false);
  const [configNode, setConfigNode] = useState<FlowNode | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  
  // Canvas viewport state
  const [canvasTransform, setCanvasTransform] = useState({ x: 0, y: 0, scale: 1 });
  const [canvasTool, setCanvasTool] = useState<'select' | 'hand'>('select');
  const [isPanning, setIsPanning] = useState(false);
  const [panStart, setPanStart] = useState({ x: 0, y: 0 });
  const [selectedNodes, setSelectedNodes] = useState<string[]>([]);
  const [isSelecting, setIsSelecting] = useState(false);
  const [selectionStart, setSelectionStart] = useState({ x: 0, y: 0 });
  const [selectionEnd, setSelectionEnd] = useState({ x: 0, y: 0 });
  
  // Dynamic step loading state
  const [nodeTemplates, setNodeTemplates] = useState<NodeTemplate[]>([]);
  const [loadingSteps, setLoadingSteps] = useState(true);
  const [stepLoadError, setStepLoadError] = useState<string | null>(null);
  
  // Target selection state

  
  const canvasRef = useRef<HTMLDivElement>(null);
  const svgRef = useRef<SVGSVGElement>(null);

  // Load step definitions from service
  const loadStepDefinitions = useCallback(async () => {
    console.log('Loading step definitions from service...');
    setLoadingSteps(true);
    setStepLoadError(null);
    
    try {
      const response = await stepLibraryService.getAvailableSteps();
      console.log('Loaded step definitions:', response);
      
      // Convert step definitions to node templates
      const templates: NodeTemplate[] = response.steps.map(step => 
        stepLibraryService.convertToNodeTemplate(step)
      );
      
      setNodeTemplates(templates);
      setLoadingSteps(false);
    } catch (error) {
      console.error('Failed to load step definitions:', error);
      setStepLoadError('Failed to load step library. Using default steps.');
      
      // Use fallback steps if service fails
      const fallbackResponse = await stepLibraryService.getAvailableSteps();
      const templates: NodeTemplate[] = fallbackResponse.steps.map(step => 
        stepLibraryService.convertToNodeTemplate(step)
      );
      
      setNodeTemplates(templates);
      setLoadingSteps(false);
    }
  }, []);

  useEffect(() => {
    loadStepDefinitions();
    
    // Listen for library changes
    const handleLibraryChange = () => {
      loadStepDefinitions();
    };
    
    stepLibraryService.addChangeListener(handleLibraryChange);
    
    return () => {
      stepLibraryService.removeChangeListener(handleLibraryChange);
    };
  }, [loadStepDefinitions]);

  useEffect(() => {
    // Add default start node if no nodes exist
    if (nodes.length === 0 && nodeTemplates.length > 0) {
      const startTemplate = nodeTemplates.find(t => t.type === 'flow.start');
      if (startTemplate) {
        const startNode: FlowNode = {
          id: 'start-' + Date.now(),
          type: startTemplate.type,
          name: startTemplate.name,
          x: 100,
          y: 200,
          width: 120,
          height: 60,
          config: { ...startTemplate.defaultConfig },
          inputs: startTemplate.inputs,
          outputs: startTemplate.outputs,
          category: startTemplate.category,
          library: startTemplate.library
        };
        setNodes([startNode]);
      }
    }
  }, [nodeTemplates, nodes.length]);

  useEffect(() => {
    if (editingJob) {
      setJobName(editingJob.name);
      if (editingJob.definition?.flow?.nodes) {
        setNodes(editingJob.definition.flow.nodes);
      }
      if (editingJob.definition?.flow?.connections) {
        setConnections(editingJob.definition.flow.connections);
      }
    }
  }, [editingJob]);

  // Canvas viewport utility functions
  const transformPoint = useCallback((x: number, y: number) => {
    return {
      x: (x - canvasTransform.x) / canvasTransform.scale,
      y: (y - canvasTransform.y) / canvasTransform.scale
    };
  }, [canvasTransform]);

  const handleMouseMove = useCallback((e: MouseEvent) => {
    setMousePos({ x: e.clientX, y: e.clientY });
    
    if (isDragging && selectedNode && canvasRef.current) {
      const rect = canvasRef.current.getBoundingClientRect();
      const viewportPos = { x: e.clientX - rect.left, y: e.clientY - rect.top };
      const virtualPos = transformPoint(viewportPos.x, viewportPos.y);
      
      const newX = virtualPos.x - dragOffset.x;
      const newY = virtualPos.y - dragOffset.y;
      
      setNodes(prev => prev.map(node => 
        node.id === selectedNode.id 
          ? { ...node, x: Math.max(0, newX), y: Math.max(0, newY) }
          : node
      ));
    }
  }, [isDragging, selectedNode, dragOffset, transformPoint]);

  const handleMouseUp = useCallback(() => {
    setIsDragging(false);
    setIsConnecting(false);
    setConnectionStart(null);
  }, []);

  useEffect(() => {
    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
    
    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [handleMouseMove, handleMouseUp]);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.target !== document.body) return; // Only when not in input fields
      
      switch (e.key.toLowerCase()) {
        case 'v':
          setCanvasTool('select');
          break;
        case 'h':
          setCanvasTool('hand');
          break;
        case 'escape':
          setSelectedNodes([]);
          setSelectedNode(null);
          break;
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, []);

  const handleTemplateDragStart = (template: NodeTemplate, e: React.DragEvent) => {
    setDraggedTemplate(template);
    e.dataTransfer.effectAllowed = 'copy';
  };

  const handleCanvasDrop = (e: React.DragEvent) => {
    e.preventDefault();
    
    if (draggedTemplate && canvasRef.current) {
      const rect = canvasRef.current.getBoundingClientRect();
      const viewportX = e.clientX - rect.left;
      const viewportY = e.clientY - rect.top;
      
      // Convert viewport coordinates to virtual canvas coordinates
      const virtualPos = transformPoint(viewportX, viewportY);
      
      const newNode: FlowNode = {
        id: `${draggedTemplate.type}-${Date.now()}`,
        type: draggedTemplate.type,
        name: draggedTemplate.name,
        x: Math.max(0, virtualPos.x - 60),
        y: Math.max(0, virtualPos.y - 30),
        width: 120,
        height: 60,
        config: { ...draggedTemplate.defaultConfig },
        inputs: draggedTemplate.inputs,
        outputs: draggedTemplate.outputs,
        category: draggedTemplate.category,
        library: draggedTemplate.library
      };
      
      setNodes(prev => [...prev, newNode]);
      setDraggedTemplate(null);
    }
  };

  const handleNodeMouseDown = (node: FlowNode, e: React.MouseEvent) => {
    e.stopPropagation();
    
    // Handle multi-selection
    if (e.ctrlKey || e.metaKey) {
      const isSelected = selectedNodes.includes(node.id);
      if (isSelected) {
        setSelectedNodes(selectedNodes.filter(id => id !== node.id));
        if (selectedNode?.id === node.id) {
          setSelectedNode(null);
        }
      } else {
        setSelectedNodes([...selectedNodes, node.id]);
        setSelectedNode(node);
      }
      return; // Don't start dragging with Ctrl+click
    } else {
      // Single selection
      if (!selectedNodes.includes(node.id)) {
        setSelectedNodes([node.id]);
      }
      setSelectedNode(node);
      setIsDragging(true);
      
      if (canvasRef.current) {
        const rect = canvasRef.current.getBoundingClientRect();
        const viewportPos = { x: e.clientX - rect.left, y: e.clientY - rect.top };
        const virtualPos = transformPoint(viewportPos.x, viewportPos.y);
        
        setDragOffset({
          x: virtualPos.x - node.x,
          y: virtualPos.y - node.y
        });
      }
    }
  };

  const handleNodeDoubleClick = (node: FlowNode) => {
    setConfigNode(node);
    setShowConfigModal(true);
  };

  const handlePortClick = (nodeId: string, port: number, isOutput: boolean, e: React.MouseEvent) => {
    e.stopPropagation();
    
    if (isConnecting && connectionStart) {
      if (connectionStart.nodeId !== nodeId) {
        const newConnection: Connection = {
          id: `${connectionStart.nodeId}-${connectionStart.port}-${nodeId}-${port}`,
          sourceNodeId: connectionStart.nodeId,
          sourcePort: connectionStart.port,
          targetNodeId: nodeId,
          targetPort: port
        };
        
        setConnections(prev => [...prev, newConnection]);
      }
      setIsConnecting(false);
      setConnectionStart(null);
    } else if (isOutput) {
      setIsConnecting(true);
      setConnectionStart({ nodeId, port });
    }
  };

  const handleDeleteNode = (nodeId: string) => {
    setNodes(prev => prev.filter(node => node.id !== nodeId));
    setConnections(prev => prev.filter(conn => 
      conn.sourceNodeId !== nodeId && conn.targetNodeId !== nodeId
    ));
    if (selectedNode?.id === nodeId) {
      setSelectedNode(null);
    }
  };

  const handleDeleteConnection = (connectionId: string) => {
    setConnections(prev => prev.filter(conn => conn.id !== connectionId));
  };

  const updateNodeConfig = (nodeId: string, config: any) => {
    setNodes(prev => prev.map(node => 
      node.id === nodeId ? { ...node, config } : node
    ));
  };

  const handleConfigSave = (config: any) => {
    if (configNode) {
      updateNodeConfig(configNode.id, config);
    }
  };

  const handleSave = useCallback(() => {
    if (!jobName.trim()) {
      alert('Please enter a job name');
      return;
    }

    if (nodes.length === 0) {
      alert('Please add at least one step');
      return;
    }

    // Convert visual flow to job steps
    const steps = nodes
      .filter(node => node.type !== 'flow.start' && node.type !== 'flow.end')
      .map(node => ({
        type: node.type,
        name: node.config.name || node.name,
        ...node.config
      }));

    const jobData = {
      name: jobName,
      version: 1,
      definition: {
        name: jobName,
        version: 1,
        parameters: {},
        steps: steps,
        flow: {
          nodes: nodes,
          connections: connections
        }
      },
      is_active: true
    };

    onJobCreate(jobData);
  }, [jobName, nodes, connections, onJobCreate]);

  const setCanvasTransformWithLimits = useCallback((transform: { x: number, y: number, scale: number }) => {
    const minScale = 0.1;
    const maxScale = 3.0;
    const scale = Math.max(minScale, Math.min(maxScale, transform.scale));
    
    setCanvasTransform({ ...transform, scale });
  }, []);

  // Canvas tool handlers
  const handleZoomIn = useCallback(() => {
    const newScale = Math.min(canvasTransform.scale * 1.2, 3.0);
    setCanvasTransformWithLimits({ ...canvasTransform, scale: newScale });
  }, [canvasTransform, setCanvasTransformWithLimits]);

  const handleZoomOut = useCallback(() => {
    const newScale = Math.max(canvasTransform.scale / 1.2, 0.1);
    setCanvasTransformWithLimits({ ...canvasTransform, scale: newScale });
  }, [canvasTransform, setCanvasTransformWithLimits]);

  const handleFitToView = useCallback(() => {
    if (nodes.length === 0) {
      setCanvasTransform({ x: 0, y: 0, scale: 1 });
      return;
    }

    const bounds = nodes.reduce(
      (acc, node) => ({
        minX: Math.min(acc.minX, node.x),
        minY: Math.min(acc.minY, node.y),
        maxX: Math.max(acc.maxX, node.x + node.width),
        maxY: Math.max(acc.maxY, node.y + node.height)
      }),
      { minX: Infinity, minY: Infinity, maxX: -Infinity, maxY: -Infinity }
    );

    if (canvasRef.current) {
      const rect = canvasRef.current.getBoundingClientRect();
      const padding = 50;
      
      const contentWidth = bounds.maxX - bounds.minX;
      const contentHeight = bounds.maxY - bounds.minY;
      
      const scaleX = (rect.width - padding * 2) / contentWidth;
      const scaleY = (rect.height - padding * 2) / contentHeight;
      const scale = Math.min(scaleX, scaleY, 1.0);
      
      const centerX = rect.width / 2 - (contentWidth * scale) / 2;
      const centerY = rect.height / 2 - (contentHeight * scale) / 2;
      
      setCanvasTransformWithLimits({
        x: centerX - bounds.minX * scale,
        y: centerY - bounds.minY * scale,
        scale
      });
    }
  }, [nodes, setCanvasTransformWithLimits]);

  const handleResetView = useCallback(() => {
    setCanvasTransform({ x: 0, y: 0, scale: 1 });
  }, []);

  // Canvas pan handlers
  const handleCanvasMouseDown = useCallback((e: React.MouseEvent) => {
    if (canvasTool === 'hand' || e.button === 1) { // Middle mouse button
      setIsPanning(true);
      setPanStart({ x: e.clientX - canvasTransform.x, y: e.clientY - canvasTransform.y });
      e.preventDefault();
    } else if (canvasTool === 'select' && canvasRef.current) {
      // Start rectangle selection
      const rect = canvasRef.current.getBoundingClientRect();
      const viewportPos = { x: e.clientX - rect.left, y: e.clientY - rect.top };
      const virtualPos = transformPoint(viewportPos.x, viewportPos.y);
      
      setIsSelecting(true);
      setSelectionStart(virtualPos);
      setSelectionEnd(virtualPos);
      
      // Clear selection unless Ctrl/Cmd is held
      if (!e.ctrlKey && !e.metaKey) {
        setSelectedNodes([]);
        setSelectedNode(null);
      }
      
      e.preventDefault();
    }
  }, [canvasTool, canvasTransform, transformPoint]);

  const handleCanvasMouseMove = useCallback((e: React.MouseEvent) => {
    if (isPanning) {
      const newX = e.clientX - panStart.x;
      const newY = e.clientY - panStart.y;
      setCanvasTransform({ ...canvasTransform, x: newX, y: newY });
    } else if (isSelecting && canvasRef.current) {
      // Update rectangle selection
      const rect = canvasRef.current.getBoundingClientRect();
      const viewportPos = { x: e.clientX - rect.left, y: e.clientY - rect.top };
      const virtualPos = transformPoint(viewportPos.x, viewportPos.y);
      
      setSelectionEnd(virtualPos);
    }
  }, [isPanning, panStart, canvasTransform, isSelecting, transformPoint]);

  const handleCanvasMouseUp = useCallback(() => {
    setIsPanning(false);
    
    if (isSelecting) {
      // Complete rectangle selection
      const minX = Math.min(selectionStart.x, selectionEnd.x);
      const maxX = Math.max(selectionStart.x, selectionEnd.x);
      const minY = Math.min(selectionStart.y, selectionEnd.y);
      const maxY = Math.max(selectionStart.y, selectionEnd.y);
      
      const selectedNodeIds = nodes
        .filter(node => {
          const nodeRight = node.x + node.width;
          const nodeBottom = node.y + node.height;
          
          return (
            node.x < maxX &&
            nodeRight > minX &&
            node.y < maxY &&
            nodeBottom > minY
          );
        })
        .map(node => node.id);
      
      setSelectedNodes(selectedNodeIds);
      setSelectedNode(selectedNodeIds.length === 1 ? nodes.find(n => n.id === selectedNodeIds[0]) || null : null);
      setIsSelecting(false);
    }
  }, [isSelecting, selectionStart, selectionEnd, nodes]);

  // Canvas wheel zoom
  const handleCanvasWheel = useCallback((e: React.WheelEvent) => {
    if (e.ctrlKey || e.metaKey) {
      e.preventDefault();
      
      const delta = -e.deltaY / 1000;
      const newScale = Math.max(0.1, Math.min(3.0, canvasTransform.scale * (1 + delta)));
      
      if (canvasRef.current) {
        const rect = canvasRef.current.getBoundingClientRect();
        const mouseX = e.clientX - rect.left;
        const mouseY = e.clientY - rect.top;
        
        const scaleRatio = newScale / canvasTransform.scale;
        const newX = mouseX - (mouseX - canvasTransform.x) * scaleRatio;
        const newY = mouseY - (mouseY - canvasTransform.y) * scaleRatio;
        
        setCanvasTransformWithLimits({ x: newX, y: newY, scale: newScale });
      }
    }
  }, [canvasTransform, setCanvasTransformWithLimits]);

  // Alignment functions
  const alignSelectedNodes = useCallback((alignment: 'left' | 'center' | 'right' | 'top' | 'middle' | 'bottom') => {
    console.log('alignSelectedNodes called with:', alignment, 'selectedNodes:', selectedNodes.length);
    if (selectedNodes.length < 2) {
      console.log('Not enough nodes selected:', selectedNodes.length);
      return;
    }
    
    const selectedNodeData = nodes.filter(node => selectedNodes.includes(node.id));
    console.log('selectedNodeData:', selectedNodeData);
    
    let newNodes = [...nodes];
    
    switch (alignment) {
      case 'left':
        const leftmost = Math.min(...selectedNodeData.map(n => n.x));
        selectedNodeData.forEach(node => {
          const nodeIndex = newNodes.findIndex(n => n.id === node.id);
          newNodes[nodeIndex] = { ...newNodes[nodeIndex], x: leftmost };
        });
        break;
      
      case 'center':
        const centerX = selectedNodeData.reduce((sum, n) => sum + n.x + n.width / 2, 0) / selectedNodeData.length;
        selectedNodeData.forEach(node => {
          const nodeIndex = newNodes.findIndex(n => n.id === node.id);
          newNodes[nodeIndex] = { ...newNodes[nodeIndex], x: centerX - node.width / 2 };
        });
        break;
      
      case 'right':
        const rightmost = Math.max(...selectedNodeData.map(n => n.x + n.width));
        selectedNodeData.forEach(node => {
          const nodeIndex = newNodes.findIndex(n => n.id === node.id);
          newNodes[nodeIndex] = { ...newNodes[nodeIndex], x: rightmost - node.width };
        });
        break;
      
      case 'top':
        const topmost = Math.min(...selectedNodeData.map(n => n.y));
        selectedNodeData.forEach(node => {
          const nodeIndex = newNodes.findIndex(n => n.id === node.id);
          newNodes[nodeIndex] = { ...newNodes[nodeIndex], y: topmost };
        });
        break;
      
      case 'middle':
        const centerY = selectedNodeData.reduce((sum, n) => sum + n.y + n.height / 2, 0) / selectedNodeData.length;
        selectedNodeData.forEach(node => {
          const nodeIndex = newNodes.findIndex(n => n.id === node.id);
          newNodes[nodeIndex] = { ...newNodes[nodeIndex], y: centerY - node.height / 2 };
        });
        break;
      
      case 'bottom':
        const bottommost = Math.max(...selectedNodeData.map(n => n.y + n.height));
        selectedNodeData.forEach(node => {
          const nodeIndex = newNodes.findIndex(n => n.id === node.id);
          newNodes[nodeIndex] = { ...newNodes[nodeIndex], y: bottommost - node.height };
        });
        break;
    }
    
    console.log('Setting new nodes:', newNodes);
    setNodes(newNodes);
  }, [selectedNodes, nodes]);

  // Listen for custom events from header buttons
  useEffect(() => {
    const handleRefreshSteps = () => {
      loadStepDefinitions();
    };

    const handleSaveJob = () => {
      handleSave();
    };

    window.addEventListener('refreshSteps', handleRefreshSteps);
    window.addEventListener('saveJob', handleSaveJob);
    
    return () => {
      window.removeEventListener('refreshSteps', handleRefreshSteps);
      window.removeEventListener('saveJob', handleSaveJob);
    };
  }, [loadStepDefinitions, handleSave]);

  // Get unique categories and libraries
  const categories = ['all', ...Array.from(new Set(nodeTemplates.map(t => t.category)))];
  const libraries = ['all', ...Array.from(new Set(nodeTemplates.map(t => t.library)))];

  // Filter templates
  const filteredTemplates = nodeTemplates.filter(template => {
    const categoryMatch = selectedCategory === 'all' || template.category === selectedCategory;
    const libraryMatch = selectedLibrary === 'all' || template.library === selectedLibrary;
    const searchMatch = searchTerm === '' || 
      template.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      template.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
      template.type.toLowerCase().includes(searchTerm.toLowerCase());
    
    return categoryMatch && libraryMatch && searchMatch;
  });

  return (
    <div className="visual-job-builder dashboard-grid">
      {/* Step Libraries Navigator (1fr width) */}
      <div className="dashboard-section">
        <div className="section-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Package size={14} />
            Libraries
          </div>
        </div>
        <div className="section-content">
          {/* Libraries List */}
          <div className="library-list">
            {libraries.map(lib => (
              <div
                key={lib}
                className={`library-item ${selectedLibrary === lib ? 'selected' : ''}`}
                onClick={() => setSelectedLibrary(lib)}
              >
                <Package size={14} />
                <span>{lib === 'all' ? 'All Libraries' : lib}</span>
              </div>
            ))}
          </div>

          {/* Categories for selected library */}
          {selectedLibrary !== 'all' && (
            <div className="category-section">
              <h4 className="category-header">Categories</h4>
              <div className="category-list">
                {categories.map(cat => (
                  <div
                    key={cat}
                    className={`category-item ${selectedCategory === cat ? 'selected' : ''}`}
                    onClick={() => setSelectedCategory(cat)}
                  >
                    <span>{cat === 'all' ? 'All Categories' : cat}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Step Blocks (1fr width) */}
      <div className="dashboard-section">
        <div className="section-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Grid3X3 size={14} />
            Step Blocks
          </div>
        </div>
        <div className="section-content">
          {/* Search Bar */}
          <input
            type="text"
            placeholder="Search steps..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="step-library-search"
          />

          {/* Loading and Error States */}
          {loadingSteps ? (
            <div className="step-load-status">
              <div>Loading step libraries...</div>
            </div>
          ) : stepLoadError ? (
            <div className="step-load-error">
              <AlertTriangle size={14} style={{ marginRight: 'var(--space-1)' }} />
              {stepLoadError}
              <button 
                className="btn btn-ghost btn-sm step-load-retry"
                onClick={loadStepDefinitions}
              >
                <RefreshCw size={12} />
                Retry
              </button>
            </div>
          ) : null}

          {/* Step Templates */}
          <div className="step-templates-container">
            {!loadingSteps && !stepLoadError && filteredTemplates.length === 0 && (
              <div className="no-selection">
                <p>No steps found matching your filters</p>
              </div>
            )}
          
            {filteredTemplates.map(template => (
              <div
                key={template.id}
                className="step-template"
                draggable
                onDragStart={(e) => handleTemplateDragStart(template, e)}
                title={template.description}
                style={{ 
                  borderLeftColor: template.color || 'var(--primary-blue-500)',
                  borderLeftWidth: '3px'
                }}
              >
                <div className="step-template-header">
                  <span>{getIconComponent(template.icon, 12)}</span>
                  <div className="step-template-name">{template.name}</div>
                </div>
                <div className="step-template-meta">
                  {template.library} • {template.category}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Main Canvas Area (6fr width) */}
      <div className="dashboard-section">
        <div className="section-header">
          Canvas
        </div>

        {/* Canvas */}
        <div
          ref={canvasRef}
          className={`job-canvas ${canvasTool}-tool ${isPanning ? 'panning' : ''}`}
          onDrop={handleCanvasDrop}
          onDragOver={(e) => e.preventDefault()}
          onMouseDown={handleCanvasMouseDown}
          onMouseMove={handleCanvasMouseMove}
          onMouseUp={handleCanvasMouseUp}
          onWheel={handleCanvasWheel}
        >
          {/* Canvas Toolbar */}
          <div className="canvas-toolbar" onMouseDown={(e) => e.stopPropagation()}>
            {/* Selection Tools */}
            {(() => {
              console.log('Rendering toolbar - selectedNodes.length:', selectedNodes.length, 'disabled:', selectedNodes.length < 2);
              return null;
            })()}
            <button
              className={`canvas-tool-btn ${canvasTool === 'select' ? 'active' : ''}`}
              onClick={() => setCanvasTool('select')}
              title="Select Tool (V)"
            >
              <MousePointer size={16} />
            </button>
            <button
              className={`canvas-tool-btn ${canvasTool === 'hand' ? 'active' : ''}`}
              onClick={() => setCanvasTool('hand')}
              title="Hand Tool (H)"
            >
              <Hand size={16} />
            </button>
            
            <div className="canvas-tool-separator"></div>
            
            {/* Horizontal Alignment */}
            <button
              className="canvas-tool-btn"
              onClick={(e) => {
                e.stopPropagation();
                alignSelectedNodes('left');
              }}
              disabled={selectedNodes.length < 2}
              title="Align Left"
            >
              <AlignStartVertical size={16} />
            </button>
            <button
              className="canvas-tool-btn"
              onClick={(e) => {
                e.stopPropagation();
                alignSelectedNodes('center');
              }}
              disabled={selectedNodes.length < 2}
              title="Align Center Horizontal"
            >
              <AlignCenterVertical size={16} />
            </button>
            <button
              className="canvas-tool-btn"
              onClick={(e) => {
                e.stopPropagation();
                alignSelectedNodes('right');
              }}
              disabled={selectedNodes.length < 2}
              title="Align Right"
            >
              <AlignEndVertical size={16} />
            </button>
            
            <div className="canvas-tool-separator"></div>
            
            {/* Vertical Alignment */}
            <button
              className="canvas-tool-btn"
              onClick={(e) => {
                e.stopPropagation();
                alignSelectedNodes('top');
              }}
              disabled={selectedNodes.length < 2}
              title="Align Top"
            >
              <AlignStartHorizontal size={16} />
            </button>
            <button
              className="canvas-tool-btn"
              onClick={(e) => {
                e.stopPropagation();
                alignSelectedNodes('middle');
              }}
              disabled={selectedNodes.length < 2}
              title="Align Center Vertical"
            >
              <AlignCenterHorizontal size={16} />
            </button>
            <button
              className="canvas-tool-btn"
              onClick={(e) => {
                e.stopPropagation();
                alignSelectedNodes('bottom');
              }}
              disabled={selectedNodes.length < 2}
              title="Align Bottom"
            >
              <AlignEndHorizontal size={16} />
            </button>
          </div>

          {/* Canvas Zoom Controls */}
          <div className="canvas-zoom-controls">
            <button
              className="canvas-tool-btn"
              onClick={handleZoomOut}
              title="Zoom Out"
            >
              <ZoomOut size={16} />
            </button>
            <div className="zoom-level">{Math.round(canvasTransform.scale * 100)}%</div>
            <button
              className="canvas-tool-btn"
              onClick={handleZoomIn}
              title="Zoom In"
            >
              <ZoomIn size={16} />
            </button>
            
            <div className="canvas-tool-separator"></div>
            
            <button
              className="canvas-tool-btn"
              onClick={handleFitToView}
              title="Fit to View"
            >
              <Maximize2 size={16} />
            </button>
            <button
              className="canvas-tool-btn"
              onClick={handleResetView}
              title="Reset View"
            >
              <RotateCcw size={16} />
            </button>
          </div>

          {/* Canvas Viewport */}
          <div
            className={`canvas-viewport ${isPanning ? 'panning' : ''}`}
            style={{
              transform: `translate(${canvasTransform.x}px, ${canvasTransform.y}px) scale(${canvasTransform.scale})`,
            }}
          >
            <div className="canvas-content">
          {/* SVG for connections */}
          <svg
            ref={svgRef}
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              width: '100%',
              height: '100%',
              pointerEvents: 'none',
              zIndex: 1
            }}
          >
            {connections.map(conn => {
              const sourceNode = nodes.find(n => n.id === conn.sourceNodeId);
              const targetNode = nodes.find(n => n.id === conn.targetNodeId);
              
              if (!sourceNode || !targetNode) return null;
              
              const sourceX = sourceNode.x + sourceNode.width;
              const sourceY = sourceNode.y + sourceNode.height / 2;
              const targetX = targetNode.x;
              const targetY = targetNode.y + targetNode.height / 2;
              
              return (
                <g key={conn.id}>
                  <path
                    d={`M ${sourceX} ${sourceY} C ${sourceX + 50} ${sourceY} ${targetX - 50} ${targetY} ${targetX} ${targetY}`}
                    stroke="#007bff"
                    strokeWidth="2"
                    fill="none"
                    style={{ pointerEvents: 'stroke', cursor: 'pointer' }}
                    onClick={(e) => {
                      e.stopPropagation();
                      if (window.confirm('Delete this connection?')) {
                        handleDeleteConnection(conn.id);
                      }
                    }}
                  />
                </g>
              );
            })}
            
            {/* Active connection line */}
            {isConnecting && connectionStart && (
              <path
                d={`M ${nodes.find(n => n.id === connectionStart.nodeId)?.x! + 120} ${nodes.find(n => n.id === connectionStart.nodeId)?.y! + 30} L ${mousePos.x - (canvasRef.current?.getBoundingClientRect().left || 0)} ${mousePos.y - (canvasRef.current?.getBoundingClientRect().top || 0)}`}
                stroke="#007bff"
                strokeWidth="2"
                strokeDasharray="5,5"
                fill="none"
              />
            )}
          </svg>

          {/* Nodes */}
          {nodes.map(node => {
            const template = nodeTemplates.find(t => t.type === node.type);
            return (
              <div
                key={node.id}
                className={`canvas-node ${
                  selectedNodes.includes(node.id)
                    ? selectedNodes.length > 1
                      ? 'multi-selected'
                      : 'selected'
                    : ''
                }`}
                style={{
                  position: 'absolute',
                  left: node.x,
                  top: node.y,
                  width: node.width,
                  height: node.height,
                  backgroundColor: template?.color || '#007bff',
                  color: 'white',
                  borderRadius: '8px',
                  padding: '8px',
                  cursor: 'move',
                  userSelect: 'none',
                  border: '1px solid rgba(0,0,0,0.1)',
                  boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
                  zIndex: 2,
                  fontSize: '12px'
                }}
                onMouseDown={(e) => handleNodeMouseDown(node, e)}
                onDoubleClick={() => handleNodeDoubleClick(node)}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '4px', marginBottom: '4px' }}>
                  <span>{template?.icon ? getIconComponent(template.icon, 12) : <FileText size={12} />}</span>
                  <span style={{ fontWeight: 'bold', fontSize: '11px' }}>{node.name}</span>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      if (window.confirm('Delete this step?')) {
                        handleDeleteNode(node.id);
                      }
                    }}
                    style={{
                      marginLeft: 'auto',
                      background: 'rgba(255,255,255,0.2)',
                      border: 'none',
                      color: 'white',
                      borderRadius: '2px',
                      cursor: 'pointer',
                      fontSize: '10px',
                      padding: '2px 4px'
                    }}
                  >
                    <X size={10} />
                  </button>
                </div>
                
                <div style={{ fontSize: '10px', opacity: 0.8 }}>
                  {node.library} • {node.category}
                </div>

                {/* Input ports */}
                {Array.from({ length: node.inputs }, (_, i) => (
                  <div
                    key={`input-${i}`}
                    style={{
                      position: 'absolute',
                      left: -6,
                      top: 20 + i * 15,
                      width: 12,
                      height: 12,
                      backgroundColor: '#28a745',
                      borderRadius: '50%',
                      cursor: 'pointer',
                      border: '2px solid white'
                    }}
                    onClick={(e) => handlePortClick(node.id, i, false, e)}
                  />
                ))}

                {/* Output ports */}
                {Array.from({ length: node.outputs }, (_, i) => (
                  <div
                    key={`output-${i}`}
                    style={{
                      position: 'absolute',
                      right: -6,
                      top: 20 + i * 15,
                      width: 12,
                      height: 12,
                      backgroundColor: '#dc3545',
                      borderRadius: '50%',
                      cursor: 'pointer',
                      border: '2px solid white'
                    }}
                    onClick={(e) => handlePortClick(node.id, i, true, e)}
                  />
                ))}
              </div>
            );
          })}
          
          {/* Selection Rectangle */}
          {isSelecting && (
            <div
              className="selection-rectangle"
              style={{
                left: Math.min(selectionStart.x, selectionEnd.x),
                top: Math.min(selectionStart.y, selectionEnd.y),
                width: Math.abs(selectionEnd.x - selectionStart.x),
                height: Math.abs(selectionEnd.y - selectionStart.y),
              }}
            />
          )}
            </div>
          </div>
        </div>
      </div>

      {/* Right Panel - Properties/Tools (1fr width) */}
      <div className="dashboard-section">
        <div className="section-header">
          Job Properties
        </div>
        <div className="section-content">
          {/* Job Controls */}
          <div className="job-controls">
            <input
              type="text"
              placeholder="Enter job name"
              value={jobName}
              onChange={(e) => setJobName(e.target.value)}
              className="form-input"
            />
          </div>

          <hr style={{ margin: '16px 0', border: 'none', borderTop: '1px solid var(--neutral-200)' }} />

          {selectedNodes.length > 0 ? (
            selectedNodes.length === 1 && selectedNode ? (
              <div className="node-properties">
                <h4>{selectedNode.name}</h4>
                <p className="node-description">
                  Type: {selectedNode.type}
                </p>
                <p className="node-description">
                  Library: {selectedNode.library}
                </p>
                <button 
                  className="btn btn-primary btn-sm"
                  onClick={() => handleNodeDoubleClick(selectedNode)}
                  style={{ marginTop: 'var(--space-2)' }}
                >
                  Configure Step
                </button>
              </div>
            ) : (
              <div className="multi-selection">
                <h4>Multiple Steps Selected</h4>
                <p className="node-description">
                  {selectedNodes.length} steps selected
                </p>
                <p className="node-description" style={{ fontSize: '11px', color: 'var(--neutral-500)' }}>
                  Use alignment tools in the canvas toolbar to arrange them
                </p>
                <button 
                  className="btn btn-secondary btn-sm"
                  onClick={() => {
                    setSelectedNodes([]);
                    setSelectedNode(null);
                  }}
                  style={{ marginTop: 'var(--space-2)' }}
                >
                  Clear Selection
                </button>
              </div>
            )
          ) : (
            <div className="no-selection">
              <p>Select step blocks to view properties</p>
              <p style={{ fontSize: '11px', color: 'var(--neutral-500)', marginTop: '8px' }}>
                • Click to select single step
                <br />
                • Ctrl+Click for multi-select
                <br />
                • Drag to select area
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Step Configuration Modal */}
      <StepConfigModal
        isOpen={showConfigModal}
        onClose={() => {
          setShowConfigModal(false);
          setConfigNode(null);
        }}
        onSave={handleConfigSave}
        stepNode={configNode}
      />
    </div>
  );
};

export default VisualJobBuilder;