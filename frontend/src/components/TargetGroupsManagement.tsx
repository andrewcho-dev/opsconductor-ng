import React, { useState, useEffect } from 'react';
import {
  Plus,
  Edit3,
  Trash2,
  Folder,
  FolderOpen,
  Users,
  ChevronDown,
  ChevronRight,
  Palette,
  Check,
  X,
  ArrowLeft,
  Monitor
} from 'lucide-react';
import { targetGroupApi, assetTargetApi } from '../services/api';

interface TargetGroup {
  id: number;
  name: string;
  description?: string;
  parent_group_id?: number;
  path: string;
  level: number;
  icon?: string;
  created_at: string;
  updated_at?: string;
  target_count?: number;
  direct_target_count?: number;
  children?: TargetGroup[];
}

interface TargetGroupCreate {
  name: string;
  description?: string;
  parent_group_id?: number;
  icon?: string;
}

interface Target {
  id: number;
  name: string;
  hostname: string;
  ip_address?: string;
  os_type?: string;
  description?: string;
  services: any[];
}

const TargetGroupsManagement: React.FC = () => {
  const [groups, setGroups] = useState<TargetGroup[]>([]);
  const [treeData, setTreeData] = useState<TargetGroup[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  
  // Form states
  const [addingNew, setAddingNew] = useState(false);
  const [editingGroup, setEditingGroup] = useState<TargetGroup | null>(null);
  const [selectedGroup, setSelectedGroup] = useState<TargetGroup | null>(null);
  const [newGroup, setNewGroup] = useState<TargetGroupCreate>({
    name: '',
    description: '',
    parent_group_id: undefined,
    icon: 'folder'
  });
  const [editGroup, setEditGroup] = useState<TargetGroupCreate>({
    name: '',
    description: '',
    parent_group_id: undefined,
    icon: 'folder'
  });
  
  // Tree view state
  const [expandedNodes, setExpandedNodes] = useState<Set<number>>(new Set());

  // New states for 3-column functionality
  const [groupTargets, setGroupTargets] = useState<Target[]>([]);
  const [allTargets, setAllTargets] = useState<Target[]>([]);
  const [availableTargets, setAvailableTargets] = useState<Target[]>([]);
  const [availableGroups, setAvailableGroups] = useState<TargetGroup[]>([]);
  const [selectedTargets, setSelectedTargets] = useState<number[]>([]);
  const [addingMembers, setAddingMembers] = useState(false);

  useEffect(() => {
    loadGroups();
    loadTreeData();
    loadAllTargets();
  }, []);

  useEffect(() => {
    if (selectedGroup) {
      loadGroupTargets(selectedGroup.id);
    } else {
      setGroupTargets([]);
    }
  }, [selectedGroup]);

  useEffect(() => {
    // Update available targets and groups when data changes
    updateAvailableItems();
  }, [allTargets, groups, groupTargets, selectedGroup]);

  const loadGroups = async () => {
    try {
      const data = await targetGroupApi.list(true);
      setGroups(data.groups);
      console.log('Groups refreshed with counts:', data.groups.map((g: any) => ({ name: g.name, count: g.target_count })));
    } catch (err) {
      console.error('Failed to load groups:', err);
    }
  };

  const loadTreeData = async () => {
    try {
      setLoading(true);
      const data = await targetGroupApi.getTree();
      setTreeData(data.tree);
      
      // Auto-expand root nodes
      const rootIds = data.tree.map((group: TargetGroup) => group.id);
      setExpandedNodes(new Set(rootIds));
    } catch (err) {
      console.error('Failed to load tree data:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadAllTargets = async () => {
    try {
      const data = await assetTargetApi.list();
      setAllTargets(data.targets || []);
    } catch (err) {
      console.error('Failed to load targets:', err);
    }
  };

  const loadGroupTargets = async (groupId: number) => {
    try {
      const data = await targetGroupApi.getTargets(groupId);
      setGroupTargets(data.targets || []);
    } catch (err) {
      console.error('Failed to load group targets:', err);
      setGroupTargets([]);
    }
  };

  const updateAvailableItems = () => {
    if (!selectedGroup) {
      setAvailableTargets([]);
      setAvailableGroups([]);
      return;
    }

    // Filter available targets (not in current group)
    const groupTargetIds = new Set(groupTargets.map(t => t.id));
    const filteredTargets = allTargets.filter(target => !groupTargetIds.has(target.id));
    setAvailableTargets(filteredTargets);

    // Filter available groups (not the selected group and not its children)
    const getChildGroupIds = (group: TargetGroup): number[] => {
      const ids = [group.id];
      if (group.children) {
        group.children.forEach(child => {
          ids.push(...getChildGroupIds(child));
        });
      }
      return ids;
    };

    const excludedGroupIds = new Set(getChildGroupIds(selectedGroup));
    const filteredGroups = groups.filter(group => 
      !excludedGroupIds.has(group.id) && group.id !== selectedGroup.id
    );
    setAvailableGroups(filteredGroups);
  };

  const startAddingNew = () => {
    setNewGroup({
      name: '',
      description: '',
      parent_group_id: selectedGroup?.id,
      icon: 'folder'
    });
    setAddingNew(true);
    
    // If creating a subgroup, ensure the parent is expanded so user can see the form
    if (selectedGroup?.id) {
      const newExpanded = new Set(expandedNodes);
      newExpanded.add(selectedGroup.id);
      setExpandedNodes(newExpanded);
    }
  };

  const cancelAddingNew = () => {
    setAddingNew(false);
    setNewGroup({
      name: '',
      description: '',
      parent_group_id: undefined,
      icon: 'folder'
    });
  };

  const startEditing = (group: TargetGroup) => {
    setEditGroup({
      name: group.name,
      description: group.description || '',
      parent_group_id: group.parent_group_id,
      icon: group.icon || 'folder'
    });
    setEditingGroup(group);
  };

  const cancelEditing = () => {
    setEditingGroup(null);
    setEditGroup({
      name: '',
      description: '',
      parent_group_id: undefined,
      icon: 'folder'
    });
  };

  const handleCreate = async () => {
    if (!newGroup.name.trim()) {
      alert('Group name is required');
      return;
    }

    try {
      setSaving(true);
      const createdGroup = await targetGroupApi.create(newGroup);
      await loadGroups();
      await loadTreeData();
      
      // If creating a subgroup, expand the parent
      if (newGroup.parent_group_id) {
        const newExpanded = new Set(expandedNodes);
        newExpanded.add(newGroup.parent_group_id);
        setExpandedNodes(newExpanded);
      }
      
      // Select the newly created group to highlight it
      if (createdGroup && createdGroup.id) {
        // Find the created group in the updated data
        setTimeout(() => {
          // Small delay to ensure tree data is loaded
          const findGroupById = (groups: TargetGroup[], id: number): TargetGroup | null => {
            for (const group of groups) {
              if (group.id === id) return group;
              if (group.children) {
                const found = findGroupById(group.children, id);
                if (found) return found;
              }
            }
            return null;
          };
          
          const foundGroup = findGroupById(treeData, createdGroup.id);
          if (foundGroup) {
            setSelectedGroup(foundGroup);
          }
        }, 100);
      }
      
      cancelAddingNew();
    } catch (error) {
      console.error('Failed to create group:', error);
      alert('Failed to create group');
    } finally {
      setSaving(false);
    }
  };

  const handleUpdate = async () => {
    if (!editingGroup || !editGroup.name.trim()) {
      alert('Group name is required');
      return;
    }

    try {
      setSaving(true);
      await targetGroupApi.update(editingGroup.id, editGroup);
      await loadGroups();
      await loadTreeData();
      cancelEditing();
      if (selectedGroup?.id === editingGroup.id) {
        setSelectedGroup(null);
      }
    } catch (error) {
      console.error('Failed to update group:', error);
      alert('Failed to update group');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (groupId: number) => {
    if (window.confirm('Delete this group? This action cannot be undone.')) {
      try {
        await targetGroupApi.delete(groupId);
        await loadGroups();
        await loadTreeData();
        if (selectedGroup?.id === groupId) {
          setSelectedGroup(null);
        }
      } catch (error) {
        console.error('Failed to delete group:', error);
        alert('Failed to delete group');
      }
    }
  };

  const toggleNode = (nodeId: number) => {
    const newExpanded = new Set(expandedNodes);
    if (newExpanded.has(nodeId)) {
      newExpanded.delete(nodeId);
    } else {
      newExpanded.add(nodeId);
    }
    setExpandedNodes(newExpanded);
  };

  // Member management functions
  const handleTargetSelect = (targetId: number) => {
    setSelectedTargets(prev => 
      prev.includes(targetId) 
        ? prev.filter(id => id !== targetId)
        : [...prev, targetId]
    );
  };



  const handleAddMembers = async () => {
    if (!selectedGroup || selectedTargets.length === 0) {
      return;
    }

    try {
      setSaving(true);
      
      // Add selected targets
      await targetGroupApi.addTargets(selectedGroup.id, selectedTargets);
      
      // Reload data
      await loadGroups();
      await loadTreeData(); // Refresh tree with updated counts
      await loadGroupTargets(selectedGroup.id);
      
      // Clear selections
      setSelectedTargets([]);
      setAddingMembers(false);
    } catch (error) {
      console.error('Failed to add targets:', error);
      alert('Failed to add targets to group');
    } finally {
      setSaving(false);
    }
  };

  const handleRemoveTarget = async (targetId: number) => {
    if (!selectedGroup) return;
    
    try {
      await targetGroupApi.removeTarget(selectedGroup.id, targetId);
      await loadGroupTargets(selectedGroup.id);
      await loadGroups(); // Refresh counts
      await loadTreeData(); // Refresh tree with updated counts
    } catch (error) {
      console.error('Failed to remove target:', error);
      alert('Failed to remove target from group');
    }
  };

  const startAddingMembers = () => {
    setAddingMembers(true);
    setSelectedTargets([]);
    // setSelectedGroups([]);
  };

  const cancelAddingMembers = () => {
    setAddingMembers(false);
    setSelectedTargets([]);
  };

  // Drag and drop handlers
  const handleDragStart = (e: React.DragEvent, type: 'target' | 'group', id: number) => {
    e.dataTransfer.setData('text/plain', JSON.stringify({ type, id }));
    e.dataTransfer.effectAllowed = 'move';
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    
    // Add visual feedback
    const dropZone = e.currentTarget as HTMLElement;
    dropZone.classList.add('drag-over');
  };

  const handleDragLeave = (e: React.DragEvent) => {
    // Remove visual feedback when leaving drop zone
    const dropZone = e.currentTarget as HTMLElement;
    dropZone.classList.remove('drag-over');
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    
    // Remove visual feedback
    const dropZone = e.currentTarget as HTMLElement;
    dropZone.classList.remove('drag-over');
    
    if (!selectedGroup) return;
    
    try {
      const data = JSON.parse(e.dataTransfer.getData('text/plain'));
      const { type, id } = data;
      
      if (type === 'target') {
        await targetGroupApi.addTargets(selectedGroup.id, [id]);
        await loadGroupTargets(selectedGroup.id);
        await loadGroups(); // Refresh counts
        await loadTreeData(); // Refresh tree with updated counts
      }
    } catch (error) {
      console.error('Failed to add item via drag and drop:', error);
      alert('Failed to add item to group');
    }
  };

  const handleDropRemove = async (e: React.DragEvent) => {
    e.preventDefault();
    
    // Remove visual feedback
    const dropZone = e.currentTarget as HTMLElement;
    dropZone.classList.remove('drag-over');
    
    if (!selectedGroup) return;
    
    try {
      const data = JSON.parse(e.dataTransfer.getData('text/plain'));
      const { type, id } = data;
      
      if (type === 'target') {
        await targetGroupApi.removeTarget(selectedGroup.id, parseInt(id));
        await loadGroupTargets(selectedGroup.id);
        await loadGroups(); // Refresh counts
        await loadTreeData(); // Refresh tree with updated counts
      }
    } catch (error) {
      console.error('Failed to remove target via drag and drop:', error);
      alert('Failed to remove target from group');
    }
  };

  const renderTreeNode = (group: TargetGroup, depth = 0) => {
    const isExpanded = expandedNodes.has(group.id);
    const hasChildren = group.children && group.children.length > 0;
    const isSelected = selectedGroup?.id === group.id;
    const isEditing = editingGroup?.id === group.id;

    return (
      <React.Fragment key={group.id}>
        <tr 
          className={`tree-row ${isSelected ? 'selected' : ''} ${isEditing ? 'editing' : ''}`}
          onClick={() => !isEditing && setSelectedGroup(group)}
        >
          <td style={{ paddingLeft: `${depth * 20 + 8}px` }}>
            <div className="tree-node">
              {hasChildren ? (
                <button
                  className="tree-toggle"
                  onClick={(e) => {
                    e.stopPropagation();
                    toggleNode(group.id);
                  }}
                >
                  {isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                </button>
              ) : (
                <span className="tree-spacer"></span>
              )}
              {isExpanded ? <FolderOpen size={16} /> : <Folder size={16} />}
              <span className="group-name">{group.name}</span>
            </div>
          </td>
          <td>{group.target_count || 0}</td>
          <td>
            <div className="action-buttons">
              {isEditing ? (
                <>
                  <button
                    className="btn-icon btn-success"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleUpdate();
                    }}
                    disabled={saving}
                    title="Save changes"
                  >
                    <Check size={14} />
                  </button>
                  <button
                    className="btn-icon btn-secondary"
                    onClick={(e) => {
                      e.stopPropagation();
                      cancelEditing();
                    }}
                    title="Cancel"
                  >
                    <X size={14} />
                  </button>
                </>
              ) : (
                <>
                  <button
                    className="btn-icon btn-primary"
                    onClick={(e) => {
                      e.stopPropagation();
                      startEditing(group);
                    }}
                    title="Edit group"
                  >
                    <Edit3 size={14} />
                  </button>
                  <button
                    className="btn-icon btn-danger"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDelete(group.id);
                    }}
                    title="Delete group"
                  >
                    <Trash2 size={14} />
                  </button>
                </>
              )}
            </div>
          </td>
        </tr>
        
        {/* Render new group form inline if this group is selected and we're adding */}
        {addingNew && isSelected && (
          <tr className="tree-row editing new-group-form">
            <td style={{ paddingLeft: `${(depth + 1) * 20 + 8}px` }}>
              <div className="tree-node">
                <span className="tree-spacer"></span>
                <Folder size={16} />
                <input
                  type="text"
                  className="form-input"
                  placeholder={`New subgroup in "${group.name}"`}
                  value={newGroup.name}
                  onChange={(e) => setNewGroup({...newGroup, name: e.target.value})}
                  autoFocus
                />
              </div>
            </td>
            <td>0</td>
            <td>
              <div className="action-buttons">
                <button
                  className="btn-icon btn-success"
                  onClick={handleCreate}
                  disabled={saving}
                  title={`Create subgroup in "${group.name}"`}
                >
                  <Check size={14} />
                </button>
                <button
                  className="btn-icon btn-secondary"
                  onClick={cancelAddingNew}
                  title="Cancel"
                >
                  <X size={14} />
                </button>
              </div>
            </td>
          </tr>
        )}
        
        {isExpanded && hasChildren && group.children?.map(child => 
          renderTreeNode(child, depth + 1)
        )}
      </React.Fragment>
    );
  };

  if (loading) {
    return (
      <div className="loading-overlay">
        <div className="loading-spinner"></div>
      </div>
    );
  }

  return (
    <>
      <style>
        {`
          /* Dashboard-style layout - EXACT MATCH */
          .dashboard-grid {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 12px;
            align-items: stretch;
            height: 100%;
          }
          .dashboard-section {
            background: white;
            border: 1px solid var(--neutral-200);
            border-radius: 6px;
            overflow: hidden;
            display: flex;
            flex-direction: column;
            height: 100%;
          }
          .section-header {
            background: var(--neutral-50);
            padding: 8px 12px;
            font-weight: 600;
            font-size: 13px;
            color: var(--neutral-700);
            border-bottom: 1px solid var(--neutral-200);
            display: flex;
            justify-content: space-between;
            align-items: center;
          }
          .compact-content {
            padding: 0;
            flex: 1;
            display: flex;
            flex-direction: column;
            overflow: auto;
          }
          .table-container {
            flex: 1;
            overflow: auto;
          }
          
          /* Groups table styles */
          .groups-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 12px;
          }
          .groups-table th {
            background: var(--neutral-50);
            padding: 6px 8px;
            text-align: left;
            font-weight: 600;
            color: var(--neutral-700);
            border-bottom: 1px solid var(--neutral-200);
            font-size: 11px;
          }
          .groups-table td {
            padding: 6px 8px;
            border-bottom: 1px solid var(--neutral-100);
            vertical-align: middle;
            font-size: 12px;
          }
          .tree-row:hover {
            background: var(--neutral-50);
          }
          .tree-row.selected {
            background: var(--primary-blue-light);
            border-left: 3px solid var(--primary-blue);
          }
          .tree-row.editing {
            background: var(--warning-yellow-light);
            border-left: 3px solid var(--warning-yellow);
          }
          .tree-row.new-group-form {
            background: var(--success-green-light);
            border-left: 3px solid var(--success-green);
          }
          .parent-indicator {
            font-size: 11px;
            color: var(--neutral-600);
            margin-left: 8px;
            font-style: italic;
            background: var(--neutral-100);
            padding: 2px 6px;
            border-radius: 3px;
          }
          .tree-row {
            cursor: pointer;
          }
          
          /* Targets table styles */
          .targets-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 12px;
          }
          .targets-table th {
            background: var(--neutral-50);
            padding: 6px 8px;
            text-align: left;
            font-weight: 600;
            color: var(--neutral-700);
            border-bottom: 1px solid var(--neutral-200);
            font-size: 11px;
          }
          .targets-table td {
            padding: 6px 8px;
            border-bottom: 1px solid var(--neutral-100);
            vertical-align: middle;
            font-size: 12px;
          }
          .targets-table tr:hover {
            background: var(--neutral-50);
          }
          .targets-table tr.selectable {
            cursor: pointer;
          }
          .targets-table tr.selected {
            background: var(--primary-blue-light);
          }
          
          /* Checkbox styles */
          .checkbox {
            width: 14px;
            height: 14px;
            margin-right: 8px;
          }
          
          /* Drag and drop styles */
          .draggable {
            cursor: grab;
            position: relative;
          }
          .draggable:hover td:first-child::after {
            content: '⋮⋮';
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 12px;
            color: var(--neutral-400);
            line-height: 1;
            letter-spacing: -2px;
            height: 100%;
          }
          .draggable:active {
            cursor: grabbing;
            opacity: 0.7;
          }
          .drop-zone {
            position: relative;
            min-height: 200px;
          }
          .drop-zone.drag-over {
            background: var(--primary-blue-light);
            border: 2px dashed var(--primary-blue);
            border-radius: 4px;
          }
          .drop-zone::after {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            pointer-events: none;
            border-radius: 4px;
            transition: all 0.2s ease;
          }
          .drop-zone.drag-over::after {
            background: rgba(59, 130, 246, 0.1);
            border: 2px dashed var(--primary-blue);
          }
          
          /* Tree node styles */
          .tree-node {
            display: flex;
            align-items: center;
            gap: 6px;
          }
          .tree-toggle {
            background: none;
            border: none;
            padding: 2px;
            cursor: pointer;
            display: flex;
            align-items: center;
            color: var(--neutral-600);
          }
          .tree-toggle:hover {
            color: var(--neutral-800);
          }
          .tree-spacer {
            width: 18px;
          }
          .group-name {
            font-weight: 500;
          }

          
          /* Action buttons */
          .action-buttons {
            display: flex;
            gap: 4px;
          }
          .btn-icon {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            padding: 4px;
            border: none;
            border-radius: 3px;
            background: transparent;
            cursor: pointer;
            transition: all 0.2s;
            font-size: 12px;
          }
          .btn-primary {
            color: var(--primary-blue);
          }
          .btn-primary:hover {
            background: var(--primary-blue-light);
          }
          .btn-success {
            color: var(--success-green);
          }
          .btn-success:hover:not(:disabled) {
            color: var(--success-green-dark);
          }
          .btn-danger {
            color: var(--danger-red);
          }
          .btn-danger:hover {
            background: var(--danger-red-light);
          }
          .btn-secondary {
            color: var(--neutral-600);
          }
          .btn-secondary:hover {
            background: var(--neutral-100);
          }
          
          /* Group details panel */
          .group-details {
            padding: 8px;
            font-size: 12px;
          }
          .group-details h3 {
            margin: 0 0 8px 0;
            font-size: 14px;
            color: var(--neutral-800);
          }
          .group-details .detail-row {
            display: flex;
            justify-content: space-between;
            margin-bottom: 4px;
            padding: 2px 0;
          }
          .group-details .detail-label {
            font-weight: 500;
            color: var(--neutral-600);
          }
          .group-details .detail-value {
            color: var(--neutral-800);
          }
          
          /* Form styles */
          .form-group {
            margin-bottom: 8px;
          }
          .form-label {
            display: block;
            margin-bottom: 4px;
            font-weight: 500;
            font-size: 11px;
            color: var(--neutral-700);
          }
          .form-input {
            width: 100%;
            padding: 6px 8px;
            border: 1px solid var(--neutral-300);
            border-radius: 3px;
            font-size: 12px;
            background: white;
          }
          .form-input:focus {
            outline: none;
            border-color: var(--primary-blue);
            box-shadow: 0 0 0 2px var(--blue-100);
          }
          .form-select {
            width: 100%;
            padding: 6px 8px;
            border: 1px solid var(--neutral-300);
            border-radius: 3px;
            font-size: 12px;
            background: white;
          }
          
          /* Empty state */
          .empty-state {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 40px 20px;
            text-align: center;
            color: var(--neutral-600);
          }
          .empty-state h3 {
            margin: 0 0 8px 0;
            font-size: 16px;
            color: var(--neutral-700);
          }
          .empty-state p {
            margin: 0 0 16px 0;
            font-size: 14px;
          }
          
          /* Loading styles */
          .loading-overlay {
            display: flex;
            align-items: center;
            justify-content: center;
            height: 200px;
          }
          .loading-spinner {
            width: 24px;
            height: 24px;
            border: 2px solid var(--neutral-200);
            border-top: 2px solid var(--primary-blue);
            border-radius: 50%;
            animation: spin 1s linear infinite;
          }
          @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
        `}
      </style>

      {/* 3-column dashboard grid */}
      <div className="dashboard-grid">
        {/* Column 1: Groups Tree */}
        <div className="dashboard-section">
          <div className="section-header">
            Target Groups ({groups.length})
            <button 
              className="btn-icon btn-success"
              onClick={startAddingNew}
              title={selectedGroup ? `Add subgroup to "${selectedGroup.name}"` : "Add new group"}
              disabled={addingNew || !!editingGroup}
            >
              <Plus size={16} />
            </button>
          </div>
          <div className="compact-content">
            {groups.length === 0 && !addingNew ? (
              <div className="empty-state">
                <h3>No target groups found</h3>
                <p>Get started by creating your first target group.</p>
                <button 
                  className="btn-icon btn-success"
                  onClick={startAddingNew}
                  title="Create first group"
                >
                  <Plus size={16} />
                </button>
              </div>
            ) : (
              <div className="table-container">
                <table className="groups-table">
                  <thead>
                    <tr>
                      <th>Name</th>
                      <th>Targets</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {/* Root-level new group form (when no parent is selected) */}
                    {addingNew && !selectedGroup && (
                      <tr className="tree-row editing new-group-form">
                        <td>
                          <div className="tree-node" style={{ paddingLeft: '8px' }}>
                            <span className="tree-spacer"></span>
                            <Folder size={16} />
                            <input
                              type="text"
                              className="form-input"
                              placeholder="Root group name"
                              value={newGroup.name}
                              onChange={(e) => setNewGroup({...newGroup, name: e.target.value})}
                              autoFocus
                            />
                          </div>
                        </td>
                        <td>0</td>
                        <td>
                          <div className="action-buttons">
                            <button
                              className="btn-icon btn-success"
                              onClick={handleCreate}
                              disabled={saving}
                              title="Create root group"
                            >
                              <Check size={14} />
                            </button>
                            <button
                              className="btn-icon btn-secondary"
                              onClick={cancelAddingNew}
                              title="Cancel"
                            >
                              <X size={14} />
                            </button>
                          </div>
                        </td>
                      </tr>
                    )}
                    
                    {treeData.map(group => renderTreeNode(group))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>

        {/* Column 2: Group Members */}
        <div className="dashboard-section">
          <div className="section-header">
            {selectedGroup ? `${selectedGroup.name} Members` : 'Group Members'}
            {selectedGroup && !addingMembers && (
              <button 
                className="btn-icon btn-success"
                onClick={startAddingMembers}
                title="Add members to group"
              >
                <Plus size={16} />
              </button>
            )}
            {addingMembers && (
              <div className="action-buttons">
                <button
                  className="btn-icon btn-success"
                  onClick={handleAddMembers}
                  disabled={saving || selectedTargets.length === 0}
                  title="Add selected items"
                >
                  <ArrowLeft size={14} />
                </button>
                <button
                  className="btn-icon btn-secondary"
                  onClick={cancelAddingMembers}
                  title="Cancel"
                >
                  <X size={14} />
                </button>
              </div>
            )}
          </div>
          <div className="compact-content">
            {!selectedGroup ? (
              <div className="empty-state">
                <Users size={32} />
                <h3>Select a Group</h3>
                <p>Choose a target group to view and manage its members.</p>
              </div>
            ) : loading ? (
              <div className="loading-overlay">
                <div className="loading-spinner"></div>
              </div>
            ) : groupTargets.length === 0 ? (
              <div 
                className="empty-state drop-zone"
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
              >
                <Monitor size={32} />
                <h3>No Targets</h3>
                <p>This group has no targets assigned yet.</p>
                <p style={{ fontSize: '11px', color: 'var(--neutral-500)', marginTop: '8px' }}>
                  💡 Drag items from the right column or click the button below
                </p>
                <button 
                  className="btn-icon btn-success"
                  onClick={startAddingMembers}
                  title="Add first target"
                >
                  <Plus size={16} />
                </button>
              </div>
            ) : (
              <div 
                className="table-container drop-zone"
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
              >
                <table className="targets-table">
                  <thead>
                    <tr>
                      <th style={{ width: '20px' }}></th>
                      <th>Name</th>
                      <th>Hostname</th>
                      <th>IP Address</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {groupTargets.map((target) => (
                      <tr 
                        key={target.id}
                        className="draggable"
                        draggable
                        onDragStart={(e) => handleDragStart(e, 'target', target.id)}
                      >
                        <td></td>
                        <td>{target.name}</td>
                        <td>{target.hostname}</td>
                        <td>{target.ip_address || '-'}</td>
                        <td>
                          <button
                            className="btn-icon btn-danger"
                            onClick={() => handleRemoveTarget(target.id)}
                            title="Remove from group"
                          >
                            <X size={14} />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>

        {/* Column 3: Available Targets */}
        <div 
          className="dashboard-section drop-zone"
          onDragOver={(e) => { e.preventDefault(); e.currentTarget.classList.add('drag-over'); }}
          onDragLeave={(e) => e.currentTarget.classList.remove('drag-over')}
          onDrop={(e) => handleDropRemove(e)}
        >
          <div className="section-header">
            Available Targets
          </div>
          <div className="compact-content">
            {!selectedGroup ? (
              <div className="empty-state">
                <Monitor size={32} />
                <h3>Select a Group</h3>
                <p>Choose a target group to see available items to add.</p>
              </div>
            ) : (
              <div className="table-container">

                <table className="targets-table">
                  <thead>
                    <tr>
                      <th style={{ width: '20px' }}></th>
                      <th>Name</th>
                      <th>Hostname</th>
                      <th>IP Address</th>
                    </tr>
                  </thead>
                  <tbody>
                    {availableTargets.map((target) => (
                      <tr 
                        key={target.id}
                        className="draggable"
                        draggable
                        onDragStart={(e) => handleDragStart(e, 'target', target.id)}
                      >
                        <td></td>
                        <td>{target.name}</td>
                        <td>{target.hostname}</td>
                        <td>{target.ip_address || '-'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>



                {availableTargets.length === 0 && (
                  <div className="empty-state">
                    <Monitor size={32} />
                    <h3>No Available Targets</h3>
                    <p>All targets are already assigned to this group.</p>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  );
};

export default TargetGroupsManagement;