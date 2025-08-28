import React, { useState, useEffect, useCallback } from 'react';
import { Target, JobStep } from '../types';
import { targetApi } from '../services/api';

interface VisualJobBuilderProps {
  onJobCreate: (jobData: any) => void;
  onCancel: () => void;
}

interface StepTemplate {
  id: string;
  name: string;
  type: string;
  description: string;
  icon: string;
  defaultConfig: Partial<JobStep>;
  category: 'windows' | 'linux' | 'network' | 'file' | 'control';
}

const stepTemplates: StepTemplate[] = [
  // Windows Templates
  {
    id: 'winrm-powershell',
    name: 'PowerShell Command',
    type: 'winrm.exec',
    description: 'Execute PowerShell commands on Windows targets',
    icon: '🔧',
    category: 'windows',
    defaultConfig: {
      type: 'winrm.exec',
      name: 'PowerShell Command',
      config: {
        command: 'Get-Service',
        shell: 'powershell',
        timeout: 300
      }
    }
  },
  {
    id: 'winrm-service-restart',
    name: 'Restart Service',
    type: 'winrm.exec',
    description: 'Restart a Windows service',
    icon: '🔄',
    category: 'windows',
    defaultConfig: {
      type: 'winrm.exec',
      name: 'Restart Service',
      config: {
        command: 'Restart-Service -Name "{{service_name}}" -Force',
        shell: 'powershell',
        timeout: 120
      }
    }
  },
  {
    id: 'winrm-file-copy',
    name: 'Copy File',
    type: 'winrm.copy',
    description: 'Copy files to Windows targets',
    icon: '📁',
    category: 'file',
    defaultConfig: {
      type: 'winrm.copy',
      name: 'Copy File',
      config: {
        source: 'C:\\source\\file.txt',
        destination: 'C:\\destination\\file.txt'
      }
    }
  },
  // Linux Templates
  {
    id: 'ssh-bash-command',
    name: 'Bash Command',
    type: 'ssh.exec',
    description: 'Execute bash commands on Linux targets',
    icon: '💻',
    category: 'linux',
    defaultConfig: {
      type: 'ssh.exec',
      name: 'Bash Command',
      config: {
        command: 'ls -la',
        shell: 'bash',
        timeout: 300
      }
    }
  },
  {
    id: 'ssh-service-restart',
    name: 'Restart Linux Service',
    type: 'ssh.exec',
    description: 'Restart a Linux service using systemctl',
    icon: '🔄',
    category: 'linux',
    defaultConfig: {
      type: 'ssh.exec',
      name: 'Restart Linux Service',
      config: {
        command: 'sudo systemctl restart {{service_name}}',
        shell: 'bash',
        timeout: 120
      }
    }
  },
  {
    id: 'sftp-upload',
    name: 'Upload File',
    type: 'sftp.upload',
    description: 'Upload files to Linux targets via SFTP',
    icon: '⬆️',
    category: 'file',
    defaultConfig: {
      type: 'sftp.upload',
      name: 'Upload File',
      config: {
        local_path: '/local/file.txt',
        remote_path: '/remote/file.txt',
        preserve_permissions: true
      }
    }
  },
  // Network Templates
  {
    id: 'http-get',
    name: 'HTTP GET Request',
    type: 'http.get',
    description: 'Make HTTP GET requests to APIs',
    icon: '🌐',
    category: 'network',
    defaultConfig: {
      type: 'http.get',
      name: 'HTTP GET Request',
      config: {
        url: 'https://api.example.com/status',
        timeout: 30,
        verify_ssl: true
      }
    }
  },
  {
    id: 'webhook',
    name: 'Send Webhook',
    type: 'webhook.post',
    description: 'Send webhook notifications',
    icon: '📡',
    category: 'network',
    defaultConfig: {
      type: 'webhook.post',
      name: 'Send Webhook',
      config: {
        url: 'https://hooks.example.com/webhook',
        payload: { message: 'Job completed' },
        headers: { 'Content-Type': 'application/json' }
      }
    }
  },
  // Control Templates
  {
    id: 'wait',
    name: 'Wait/Delay',
    type: 'control.wait',
    description: 'Add a delay between steps',
    icon: '⏱️',
    category: 'control',
    defaultConfig: {
      type: 'control.wait',
      name: 'Wait',
      config: {
        duration: 30,
        unit: 'seconds'
      }
    }
  }
];

const VisualJobBuilder: React.FC<VisualJobBuilderProps> = ({ onJobCreate, onCancel }) => {
  const [targets, setTargets] = useState<Target[]>([]);
  const [jobName, setJobName] = useState('');
  const [jobDescription, setJobDescription] = useState('');
  const [selectedTargets, setSelectedTargets] = useState<number[]>([]);
  const [jobSteps, setJobSteps] = useState<JobStep[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [draggedTemplate, setDraggedTemplate] = useState<StepTemplate | null>(null);
  const [editingStep, setEditingStep] = useState<number | null>(null);

  useEffect(() => {
    fetchTargets();
  }, []);

  const fetchTargets = async () => {
    try {
      const response = await targetApi.list();
      setTargets(response.targets || []);
    } catch (error) {
      console.error('Failed to fetch targets:', error);
    }
  };

  const handleDragStart = (template: StepTemplate) => {
    setDraggedTemplate(template);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const handleDrop = (e: React.DragEvent, index?: number) => {
    e.preventDefault();
    if (!draggedTemplate) return;

    const newStep: JobStep = {
      ...draggedTemplate.defaultConfig,
      id: `step_${Date.now()}`,
      name: `${draggedTemplate.name} ${jobSteps.length + 1}`
    } as JobStep;

    if (index !== undefined) {
      // Insert at specific position
      const newSteps = [...jobSteps];
      newSteps.splice(index, 0, newStep);
      setJobSteps(newSteps);
    } else {
      // Add to end
      setJobSteps([...jobSteps, newStep]);
    }

    setDraggedTemplate(null);
  };

  const removeStep = (index: number) => {
    setJobSteps(jobSteps.filter((_, i) => i !== index));
  };

  const moveStep = (fromIndex: number, toIndex: number) => {
    const newSteps = [...jobSteps];
    const [movedStep] = newSteps.splice(fromIndex, 1);
    newSteps.splice(toIndex, 0, movedStep);
    setJobSteps(newSteps);
  };

  const updateStep = (index: number, updatedStep: Partial<JobStep>) => {
    const newSteps = [...jobSteps];
    newSteps[index] = { ...newSteps[index], ...updatedStep };
    setJobSteps(newSteps);
  };

  const handleSubmit = () => {
    if (!jobName.trim()) {
      alert('Please enter a job name');
      return;
    }

    if (selectedTargets.length === 0) {
      alert('Please select at least one target');
      return;
    }

    if (jobSteps.length === 0) {
      alert('Please add at least one step');
      return;
    }

    const jobData = {
      name: jobName,
      version: 1,
      definition: {
        name: jobName,
        version: 1,
        description: jobDescription,
        parameters: {},
        steps: jobSteps,
        targets: selectedTargets
      },
      is_active: true
    };

    onJobCreate(jobData);
  };

  const filteredTemplates = selectedCategory === 'all' 
    ? stepTemplates 
    : stepTemplates.filter(t => t.category === selectedCategory);

  const categoryColors = {
    windows: '#0078d4',
    linux: '#ff6b35',
    network: '#00bcf2',
    file: '#107c10',
    control: '#8764b8'
  };

  return (
    <div className="visual-job-builder" style={{ display: 'flex', height: '80vh', gap: '20px' }}>
      {/* Left Panel - Templates */}
      <div style={{ width: '300px', borderRight: '1px solid #ddd', paddingRight: '20px' }}>
        <h3>Step Templates</h3>
        
        {/* Category Filter */}
        <div style={{ marginBottom: '15px' }}>
          <select 
            value={selectedCategory} 
            onChange={(e) => setSelectedCategory(e.target.value)}
            style={{ width: '100%', padding: '8px' }}
          >
            <option value="all">All Categories</option>
            <option value="windows">Windows</option>
            <option value="linux">Linux</option>
            <option value="network">Network</option>
            <option value="file">File Operations</option>
            <option value="control">Control Flow</option>
          </select>
        </div>

        {/* Template List */}
        <div style={{ maxHeight: '500px', overflowY: 'auto' }}>
          {filteredTemplates.map(template => (
            <div
              key={template.id}
              draggable
              onDragStart={() => handleDragStart(template)}
              style={{
                padding: '12px',
                margin: '8px 0',
                border: '1px solid #ddd',
                borderRadius: '6px',
                cursor: 'grab',
                backgroundColor: '#f8f9fa',
                borderLeft: `4px solid ${categoryColors[template.category]}`
              }}
              onMouseDown={(e) => e.currentTarget.style.cursor = 'grabbing'}
              onMouseUp={(e) => e.currentTarget.style.cursor = 'grab'}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontSize: '18px' }}>{template.icon}</span>
                <div>
                  <div style={{ fontWeight: 'bold', fontSize: '14px' }}>{template.name}</div>
                  <div style={{ fontSize: '12px', color: '#666' }}>{template.description}</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Center Panel - Job Builder */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        {/* Job Configuration */}
        <div style={{ marginBottom: '20px', padding: '20px', border: '1px solid #ddd', borderRadius: '6px' }}>
          <h3>Job Configuration</h3>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px', marginBottom: '15px' }}>
            <div>
              <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>Job Name *</label>
              <input
                type="text"
                value={jobName}
                onChange={(e) => setJobName(e.target.value)}
                placeholder="Enter job name"
                style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
              />
            </div>
            <div>
              <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>Description</label>
              <input
                type="text"
                value={jobDescription}
                onChange={(e) => setJobDescription(e.target.value)}
                placeholder="Optional description"
                style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
              />
            </div>
          </div>

          {/* Target Selection */}
          <div>
            <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>Target Servers *</label>
            <div style={{ maxHeight: '100px', overflowY: 'auto', border: '1px solid #ddd', borderRadius: '4px', padding: '8px' }}>
              {targets.map(target => (
                <label key={target.id} style={{ display: 'block', marginBottom: '5px' }}>
                  <input
                    type="checkbox"
                    checked={selectedTargets.includes(target.id)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setSelectedTargets([...selectedTargets, target.id]);
                      } else {
                        setSelectedTargets(selectedTargets.filter(id => id !== target.id));
                      }
                    }}
                    style={{ marginRight: '8px' }}
                  />
                  {target.name} ({target.hostname}) - {target.protocol.toUpperCase()}
                </label>
              ))}
            </div>
          </div>
        </div>

        {/* Job Steps */}
        <div style={{ flex: 1 }}>
          <h3>Job Steps</h3>
          <div
            onDragOver={handleDragOver}
            onDrop={(e) => handleDrop(e)}
            style={{
              minHeight: '300px',
              border: '2px dashed #ddd',
              borderRadius: '6px',
              padding: '20px',
              backgroundColor: jobSteps.length === 0 ? '#f8f9fa' : 'white'
            }}
          >
            {jobSteps.length === 0 ? (
              <div style={{ textAlign: 'center', color: '#666', marginTop: '50px' }}>
                <div style={{ fontSize: '48px', marginBottom: '10px' }}>📋</div>
                <div>Drag and drop step templates here to build your job</div>
              </div>
            ) : (
              jobSteps.map((step, index) => (
                <div
                  key={step.id || index}
                  style={{
                    padding: '15px',
                    margin: '10px 0',
                    border: '1px solid #ddd',
                    borderRadius: '6px',
                    backgroundColor: 'white',
                    position: 'relative'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                      <strong>Step {index + 1}: {step.name}</strong>
                      <div style={{ fontSize: '12px', color: '#666' }}>Type: {step.type}</div>
                    </div>
                    <div style={{ display: 'flex', gap: '5px' }}>
                      <button
                        onClick={() => setEditingStep(editingStep === index ? null : index)}
                        style={{ padding: '5px 10px', fontSize: '12px' }}
                      >
                        {editingStep === index ? 'Close' : 'Edit'}
                      </button>
                      <button
                        onClick={() => removeStep(index)}
                        style={{ padding: '5px 10px', fontSize: '12px', backgroundColor: '#dc3545', color: 'white', border: 'none', borderRadius: '3px' }}
                      >
                        Remove
                      </button>
                    </div>
                  </div>

                  {editingStep === index && (
                    <div style={{ marginTop: '15px', padding: '15px', backgroundColor: '#f8f9fa', borderRadius: '4px' }}>
                      <div style={{ marginBottom: '10px' }}>
                        <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>Step Name</label>
                        <input
                          type="text"
                          value={step.name}
                          onChange={(e) => updateStep(index, { name: e.target.value })}
                          style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
                        />
                      </div>
                      <div>
                        <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>Configuration (JSON)</label>
                        <textarea
                          value={JSON.stringify(step.config, null, 2)}
                          onChange={(e) => {
                            try {
                              const config = JSON.parse(e.target.value);
                              updateStep(index, { config });
                            } catch (err) {
                              // Invalid JSON, don't update
                            }
                          }}
                          rows={6}
                          style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px', fontFamily: 'monospace' }}
                        />
                      </div>
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </div>

        {/* Action Buttons */}
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '20px' }}>
          <button
            onClick={onCancel}
            style={{ padding: '10px 20px', backgroundColor: '#6c757d', color: 'white', border: 'none', borderRadius: '4px' }}
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            style={{ padding: '10px 20px', backgroundColor: '#007bff', color: 'white', border: 'none', borderRadius: '4px' }}
          >
            Create Job
          </button>
        </div>
      </div>
    </div>
  );
};

export default VisualJobBuilder;