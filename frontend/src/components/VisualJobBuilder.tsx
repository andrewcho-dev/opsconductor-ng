import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Job, JobStep } from '../types';
import { stepLibraryService, StepDefinition } from '../services/stepLibraryService';
import StepConfigModal from './StepConfigModal';
import { FileText, X, Play, Square, Target, BookOpen, AlertTriangle, RefreshCw, Save, RotateCcw, Settings } from 'lucide-react';

// Inject CSS styles for the Visual Job Builder
const visualJobBuilderStyles = `
  .visual-job-builder {
    display: grid;
    grid-template-columns: 1fr 7fr 1fr;
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
  
  // Dynamic step loading state
  const [nodeTemplates, setNodeTemplates] = useState<NodeTemplate[]>([]);
  const [loadingSteps, setLoadingSteps] = useState(true);
  const [stepLoadError, setStepLoadError] = useState<string | null>(null);
  
  // Target selection state

  
  const canvasRef = useRef<HTMLDivElement>(null);
  const svgRef = useRef<SVGSVGElement>(null);

  // Load step definitions from service
  const loadStepDefinitions = useCallback(async () => {
    try {
      setLoadingSteps(true);
      setStepLoadError(null);
      
      const response = await stepLibraryService.getAvailableSteps();
      const templates: NodeTemplate[] = response.steps.map(step => 
        stepLibraryService.convertToNodeTemplate(step)
      );
      
      setNodeTemplates(templates);
    } catch (error) {
      console.error('Failed to load step definitions:', error);
      setStepLoadError('Failed to load step libraries. Using fallback steps.');
      
      // Load fallback steps
      const fallbackResponse = await stepLibraryService.getAvailableSteps(undefined, undefined, undefined, false);
      const fallbackTemplates: NodeTemplate[] = fallbackResponse.steps.map(step => 
        stepLibraryService.convertToNodeTemplate(step)
      );
      setNodeTemplates(fallbackTemplates);
    } finally {
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

  const handleMouseMove = useCallback((e: MouseEvent) => {
    setMousePos({ x: e.clientX, y: e.clientY });
    
    if (isDragging && selectedNode && canvasRef.current) {
      const rect = canvasRef.current.getBoundingClientRect();
      const newX = e.clientX - rect.left - dragOffset.x;
      const newY = e.clientY - rect.top - dragOffset.y;
      
      setNodes(prev => prev.map(node => 
        node.id === selectedNode.id 
          ? { ...node, x: Math.max(0, newX), y: Math.max(0, newY) }
          : node
      ));
    }
  }, [isDragging, selectedNode, dragOffset]);

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

  const handleTemplateDragStart = (template: NodeTemplate, e: React.DragEvent) => {
    setDraggedTemplate(template);
    e.dataTransfer.effectAllowed = 'copy';
  };

  const handleCanvasDrop = (e: React.DragEvent) => {
    e.preventDefault();
    
    if (draggedTemplate && canvasRef.current) {
      const rect = canvasRef.current.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      
      const newNode: FlowNode = {
        id: `${draggedTemplate.type}-${Date.now()}`,
        type: draggedTemplate.type,
        name: draggedTemplate.name,
        x: Math.max(0, x - 60),
        y: Math.max(0, y - 30),
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
    setSelectedNode(node);
    setIsDragging(true);
    
    if (canvasRef.current) {
      const rect = canvasRef.current.getBoundingClientRect();
      setDragOffset({
        x: e.clientX - rect.left - node.x,
        y: e.clientY - rect.top - node.y
      });
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
      {/* Left Panel - Step Library (1/9 width) */}
      <div className="dashboard-section">
        <div className="section-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <BookOpen size={14} />
            Step Library
          </div>
        </div>
        <div className="section-content">
          
          {/* Search */}
          <input
            type="text"
            placeholder="Search steps..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="step-library-search"
          />
          
          {/* Filters */}
          <div className="step-library-filters">
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
            >
              {categories.map(cat => (
                <option key={cat} value={cat}>
                  {cat === 'all' ? 'All Categories' : cat}
                </option>
              ))}
            </select>
            
            <select
              value={selectedLibrary}
              onChange={(e) => setSelectedLibrary(e.target.value)}
            >
              {libraries.map(lib => (
                <option key={lib} value={lib}>
                  {lib === 'all' ? 'All Libraries' : lib}
                </option>
              ))}
            </select>
          </div>
          
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
          <div>
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

      {/* Main Canvas Area (7/9 width) */}
      <div className="dashboard-section">
        <div className="section-header">
          Canvas
        </div>

        {/* Canvas */}
        <div
          ref={canvasRef}
          className="job-canvas"
          onDrop={handleCanvasDrop}
          onDragOver={(e) => e.preventDefault()}
          onClick={() => {
            setSelectedNode(null);
          }}
        >
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
                  border: selectedNode?.id === node.id ? '2px solid #ffc107' : '1px solid rgba(0,0,0,0.1)',
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
        </div>
      </div>

      {/* Right Panel - Properties/Tools (1/9 width) */}
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

          {selectedNode ? (
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
            <div className="no-selection">
              <p>Select a step block to view properties</p>
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