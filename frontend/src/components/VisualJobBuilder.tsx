import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Job, JobStep } from '../types';
import { stepLibraryService, StepDefinition } from '../services/stepLibraryService';
import StepConfigModal from './StepConfigModal';

interface VisualJobBuilderProps {
  onJobCreate: (jobData: any) => void;
  onCancel: () => void;
  editingJob?: Job | null;
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

const VisualJobBuilder: React.FC<VisualJobBuilderProps> = ({ onJobCreate, onCancel, editingJob }) => {
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

  const handleSave = () => {
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
  };

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
    <div style={{ display: 'flex', height: '100vh', backgroundColor: '#f5f5f5' }}>
      {/* Left Panel - Step Library */}
      <div style={{ 
        width: '300px', 
        backgroundColor: 'white', 
        borderRight: '1px solid #ddd',
        display: 'flex',
        flexDirection: 'column'
      }}>
        {/* Header */}
        <div style={{ 
          padding: '16px', 
          borderBottom: '1px solid #ddd',
          backgroundColor: '#f8f9fa'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
            <h3 style={{ margin: 0, fontSize: '16px' }}>📚 Step Library</h3>
            <div style={{ fontSize: '12px', color: '#666' }}>
              Manage libraries in Settings
            </div>
          </div>
          
          {/* Search */}
          <input
            type="text"
            placeholder="Search steps..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            style={{
              width: '100%',
              padding: '8px',
              border: '1px solid #ddd',
              borderRadius: '4px',
              fontSize: '14px',
              marginBottom: '8px'
            }}
          />
          
          {/* Filters */}
          <div style={{ display: 'flex', gap: '8px' }}>
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              style={{ flex: 1, padding: '4px', fontSize: '12px' }}
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
              style={{ flex: 1, padding: '4px', fontSize: '12px' }}
            >
              {libraries.map(lib => (
                <option key={lib} value={lib}>
                  {lib === 'all' ? 'All Libraries' : lib}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Step Templates */}
        <div style={{ flex: 1, overflow: 'auto', padding: '8px' }}>
          {loadingSteps ? (
            <div style={{ textAlign: 'center', padding: '20px', color: '#666' }}>
              <div>Loading step libraries...</div>
            </div>
          ) : stepLoadError ? (
            <div style={{ 
              backgroundColor: '#fff3cd', 
              color: '#856404', 
              padding: '8px', 
              borderRadius: '4px', 
              fontSize: '12px',
              marginBottom: '8px'
            }}>
              ⚠️ {stepLoadError}
            </div>
          ) : null}
          
          {filteredTemplates.map(template => (
            <div
              key={template.id}
              draggable
              onDragStart={(e) => handleTemplateDragStart(template, e)}
              style={{
                padding: '8px',
                margin: '4px 0',
                backgroundColor: template.color || '#007bff',
                color: 'white',
                borderRadius: '4px',
                cursor: 'grab',
                fontSize: '12px',
                userSelect: 'none'
              }}
              title={template.description}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span>{template.icon}</span>
                <div>
                  <div style={{ fontWeight: 'bold' }}>{template.name}</div>
                  <div style={{ fontSize: '10px', opacity: 0.8 }}>
                    {template.library} • {template.category}
                  </div>
                </div>
              </div>
            </div>
          ))}
          
          {filteredTemplates.length === 0 && !loadingSteps && (
            <div style={{ textAlign: 'center', padding: '20px', color: '#666' }}>
              No steps found matching your criteria
            </div>
          )}
        </div>
      </div>

      {/* Main Canvas Area */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        {/* Top Toolbar */}
        <div style={{ 
          padding: '12px 16px', 
          backgroundColor: 'white', 
          borderBottom: '1px solid #ddd',
          display: 'flex',
          alignItems: 'center',
          gap: '12px'
        }}>
          <input
            type="text"
            placeholder="Job Name"
            value={jobName}
            onChange={(e) => setJobName(e.target.value)}
            style={{
              padding: '8px 12px',
              border: '1px solid #ddd',
              borderRadius: '4px',
              fontSize: '14px',
              width: '200px'
            }}
          />
          
          <div style={{ flex: 1 }} />
          
          <button
            onClick={() => loadStepDefinitions()}
            style={{
              padding: '8px 12px',
              backgroundColor: '#6c757d',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer'
            }}
            disabled={loadingSteps}
          >
            🔄 Refresh Steps
          </button>
          
          <button
            onClick={onCancel}
            style={{
              padding: '8px 12px',
              backgroundColor: '#6c757d',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer'
            }}
          >
            Cancel
          </button>
          
          <button
            onClick={handleSave}
            style={{
              padding: '8px 12px',
              backgroundColor: '#28a745',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer'
            }}
          >
            Save Job
          </button>
        </div>

        {/* Canvas */}
        <div
          ref={canvasRef}
          style={{
            flex: 1,
            position: 'relative',
            overflow: 'auto',
            backgroundColor: '#fafafa',
            backgroundImage: 'radial-gradient(circle, #ddd 1px, transparent 1px)',
            backgroundSize: '20px 20px'
          }}
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
                  <span>{template?.icon || '📄'}</span>
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
                    ×
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