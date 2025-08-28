import React, { useState, useEffect } from 'react';
import { Target } from '../types';
import { targetApi } from '../services/api';

interface TargetGroup {
  id: number;
  name: string;
  description: string;
  targets: number[];
  tags: string[];
  created_at: string;
}

interface TargetGroupCreate {
  name: string;
  description: string;
  targets: number[];
  tags: string[];
}

const TargetGroups: React.FC = () => {
  const [targetGroups, setTargetGroups] = useState<TargetGroup[]>([]);
  const [targets, setTargets] = useState<Target[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingGroup, setEditingGroup] = useState<TargetGroup | null>(null);
  const [formData, setFormData] = useState<TargetGroupCreate>({
    name: '',
    description: '',
    targets: [],
    tags: []
  });
  const [newTag, setNewTag] = useState('');

  useEffect(() => {
    fetchTargetGroups();
    fetchTargets();
  }, []);

  const fetchTargetGroups = async () => {
    try {
      // For now, we'll simulate target groups since the API doesn't exist yet
      // In a real implementation, this would call targetGroupApi.list()
      const mockGroups: TargetGroup[] = [
        {
          id: 1,
          name: 'Production Servers',
          description: 'All production Windows and Linux servers',
          targets: [1, 2, 3],
          tags: ['production', 'critical'],
          created_at: new Date().toISOString()
        },
        {
          id: 2,
          name: 'Development Environment',
          description: 'Development and testing servers',
          targets: [4, 5],
          tags: ['development', 'testing'],
          created_at: new Date().toISOString()
        }
      ];
      setTargetGroups(mockGroups);
    } catch (error) {
      console.error('Failed to fetch target groups:', error);
      setTargetGroups([]);
    } finally {
      setLoading(false);
    }
  };

  const fetchTargets = async () => {
    try {
      const response = await targetApi.list();
      setTargets(response.targets || []);
    } catch (error) {
      console.error('Failed to fetch targets:', error);
      setTargets([]);
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      // For now, we'll simulate creation
      // In a real implementation, this would call targetGroupApi.create(formData)
      const newGroup: TargetGroup = {
        id: Date.now(),
        ...formData,
        created_at: new Date().toISOString()
      };
      setTargetGroups([...targetGroups, newGroup]);
      setShowCreateModal(false);
      resetForm();
    } catch (error) {
      console.error('Failed to create target group:', error);
      alert('Failed to create target group. Please try again.');
    }
  };

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingGroup) return;

    try {
      // For now, we'll simulate update
      // In a real implementation, this would call targetGroupApi.update(editingGroup.id, formData)
      const updatedGroups = targetGroups.map(group =>
        group.id === editingGroup.id
          ? { ...group, ...formData }
          : group
      );
      setTargetGroups(updatedGroups);
      setEditingGroup(null);
      resetForm();
    } catch (error) {
      console.error('Failed to update target group:', error);
      alert('Failed to update target group. Please try again.');
    }
  };

  const handleDelete = async (groupId: number) => {
    if (!window.confirm('Are you sure you want to delete this target group?')) return;

    try {
      // For now, we'll simulate deletion
      // In a real implementation, this would call targetGroupApi.delete(groupId)
      setTargetGroups(targetGroups.filter(group => group.id !== groupId));
    } catch (error) {
      console.error('Failed to delete target group:', error);
      alert('Failed to delete target group. Please try again.');
    }
  };

  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
      targets: [],
      tags: []
    });
    setNewTag('');
  };

  const startEdit = (group: TargetGroup) => {
    setEditingGroup(group);
    setFormData({
      name: group.name,
      description: group.description,
      targets: group.targets,
      tags: group.tags
    });
  };

  const addTag = () => {
    if (newTag.trim() && !formData.tags.includes(newTag.trim())) {
      setFormData({
        ...formData,
        tags: [...formData.tags, newTag.trim()]
      });
      setNewTag('');
    }
  };

  const removeTag = (tagToRemove: string) => {
    setFormData({
      ...formData,
      tags: formData.tags.filter(tag => tag !== tagToRemove)
    });
  };

  const toggleTarget = (targetId: number) => {
    const isSelected = formData.targets.includes(targetId);
    if (isSelected) {
      setFormData({
        ...formData,
        targets: formData.targets.filter(id => id !== targetId)
      });
    } else {
      setFormData({
        ...formData,
        targets: [...formData.targets, targetId]
      });
    }
  };

  const getTargetNames = (targetIds: number[]) => {
    return targetIds
      .map(id => targets.find(t => t.id === id)?.name)
      .filter(Boolean)
      .join(', ');
  };

  const bulkOperations = [
    { id: 'restart-services', name: 'Restart Services', icon: '🔄' },
    { id: 'update-credentials', name: 'Update Credentials', icon: '🔑' },
    { id: 'health-check', name: 'Health Check', icon: '🏥' },
    { id: 'backup', name: 'Backup Configuration', icon: '💾' },
    { id: 'patch-update', name: 'Apply Updates', icon: '🔧' }
  ];

  if (loading) return <div>Loading target groups...</div>;

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h1>Target Groups</h1>
        <button 
          className="btn btn-primary"
          onClick={() => setShowCreateModal(true)}
        >
          Create Target Group
        </button>
      </div>

      <div className="card">
        <table className="table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Description</th>
              <th>Targets</th>
              <th>Tags</th>
              <th>Created</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {targetGroups.map(group => (
              <tr key={group.id}>
                <td>
                  <strong>{group.name}</strong>
                </td>
                <td>{group.description}</td>
                <td>
                  <span style={{ fontSize: '12px', color: '#666' }}>
                    {group.targets.length} targets: {getTargetNames(group.targets)}
                  </span>
                </td>
                <td>
                  <div style={{ display: 'flex', gap: '5px', flexWrap: 'wrap' }}>
                    {group.tags.map(tag => (
                      <span 
                        key={tag}
                        style={{
                          backgroundColor: '#e9ecef',
                          padding: '2px 8px',
                          borderRadius: '12px',
                          fontSize: '11px'
                        }}
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                </td>
                <td>{new Date(group.created_at).toLocaleDateString()}</td>
                <td>
                  <div style={{ display: 'flex', gap: '5px', flexWrap: 'wrap' }}>
                    <button 
                      className="btn btn-primary"
                      onClick={() => startEdit(group)}
                      style={{ fontSize: '12px' }}
                    >
                      Edit
                    </button>
                    <div className="dropdown" style={{ position: 'relative', display: 'inline-block' }}>
                      <button 
                        className="btn btn-secondary dropdown-toggle"
                        style={{ fontSize: '12px' }}
                        onClick={(e) => {
                          const dropdown = e.currentTarget.nextElementSibling as HTMLElement;
                          dropdown.style.display = dropdown.style.display === 'block' ? 'none' : 'block';
                        }}
                      >
                        Bulk Actions
                      </button>
                      <div 
                        className="dropdown-menu"
                        style={{
                          position: 'absolute',
                          top: '100%',
                          left: 0,
                          backgroundColor: 'white',
                          border: '1px solid #ddd',
                          borderRadius: '4px',
                          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
                          zIndex: 1000,
                          minWidth: '150px',
                          display: 'none'
                        }}
                      >
                        {bulkOperations.map(op => (
                          <button
                            key={op.id}
                            className="dropdown-item"
                            style={{
                              display: 'block',
                              width: '100%',
                              padding: '8px 12px',
                              border: 'none',
                              backgroundColor: 'transparent',
                              textAlign: 'left',
                              fontSize: '12px'
                            }}
                            onClick={() => {
                              alert(`Bulk operation "${op.name}" would be executed on ${group.targets.length} targets`);
                            }}
                          >
                            {op.icon} {op.name}
                          </button>
                        ))}
                      </div>
                    </div>
                    <button 
                      className="btn btn-danger"
                      onClick={() => handleDelete(group.id)}
                      style={{ fontSize: '12px' }}
                    >
                      Delete
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Create/Edit Modal */}
      {(showCreateModal || editingGroup) && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.5)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000
        }}>
          <div className="card" style={{ width: '600px', margin: '20px', maxHeight: '80vh', overflow: 'auto' }}>
            <h3>{editingGroup ? 'Edit Target Group' : 'Create Target Group'}</h3>
            <form onSubmit={editingGroup ? handleUpdate : handleCreate}>
              <div className="form-group">
                <label>Name:</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  required
                />
              </div>

              <div className="form-group">
                <label>Description:</label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  rows={3}
                />
              </div>

              <div className="form-group">
                <label>Select Targets:</label>
                <div style={{ 
                  maxHeight: '200px', 
                  overflowY: 'auto', 
                  border: '1px solid #ddd', 
                  borderRadius: '4px', 
                  padding: '10px' 
                }}>
                  {targets.map(target => (
                    <label key={target.id} style={{ display: 'block', marginBottom: '8px' }}>
                      <input
                        type="checkbox"
                        checked={formData.targets.includes(target.id)}
                        onChange={() => toggleTarget(target.id)}
                        style={{ marginRight: '8px' }}
                      />
                      <strong>{target.name}</strong> ({target.hostname}) - {target.protocol.toUpperCase()}
                      {target.os_type && (
                        <span style={{ 
                          marginLeft: '8px', 
                          fontSize: '11px', 
                          backgroundColor: '#e9ecef', 
                          padding: '2px 6px', 
                          borderRadius: '8px' 
                        }}>
                          {target.os_type}
                        </span>
                      )}
                    </label>
                  ))}
                </div>
                <div style={{ marginTop: '8px', fontSize: '12px', color: '#666' }}>
                  Selected: {formData.targets.length} targets
                </div>
              </div>

              <div className="form-group">
                <label>Tags:</label>
                <div style={{ display: 'flex', gap: '5px', marginBottom: '10px' }}>
                  <input
                    type="text"
                    value={newTag}
                    onChange={(e) => setNewTag(e.target.value)}
                    placeholder="Add tag"
                    onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addTag())}
                    style={{ flex: 1 }}
                  />
                  <button 
                    type="button" 
                    onClick={addTag}
                    className="btn btn-secondary"
                    style={{ fontSize: '12px' }}
                  >
                    Add
                  </button>
                </div>
                <div style={{ display: 'flex', gap: '5px', flexWrap: 'wrap' }}>
                  {formData.tags.map(tag => (
                    <span 
                      key={tag}
                      style={{
                        backgroundColor: '#007bff',
                        color: 'white',
                        padding: '4px 8px',
                        borderRadius: '12px',
                        fontSize: '12px',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '5px'
                      }}
                    >
                      {tag}
                      <button
                        type="button"
                        onClick={() => removeTag(tag)}
                        style={{
                          background: 'none',
                          border: 'none',
                          color: 'white',
                          cursor: 'pointer',
                          fontSize: '14px'
                        }}
                      >
                        ×
                      </button>
                    </span>
                  ))}
                </div>
              </div>

              <div style={{ display: 'flex', gap: '10px', marginTop: '20px' }}>
                <button type="submit" className="btn btn-primary">
                  {editingGroup ? 'Update Group' : 'Create Group'}
                </button>
                <button 
                  type="button" 
                  className="btn btn-secondary"
                  onClick={() => {
                    setShowCreateModal(false);
                    setEditingGroup(null);
                    resetForm();
                  }}
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default TargetGroups;