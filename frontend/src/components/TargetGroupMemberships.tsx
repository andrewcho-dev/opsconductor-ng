import React, { useState, useEffect } from 'react';
import {
  Plus,
  Minus,
  Users,
  Monitor,
  Eye,
  Check,
  X,
  Search
} from 'lucide-react';
// import { targetGroupApi, assetTargetApi } from '../services/api';

interface TargetGroup {
  id: number;
  name: string;
  description?: string;
  path: string;
  level: number;
  color?: string;
  target_count?: number;
  direct_target_count?: number;
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

const TargetGroupMemberships: React.FC = () => {
  const [groups, setGroups] = useState<TargetGroup[]>([]);
  const [selectedGroup, setSelectedGroup] = useState<TargetGroup | null>(null);
  const [groupTargets, setGroupTargets] = useState<Target[]>([]);
  const [allTargets, setAllTargets] = useState<Target[]>([]);
  const [availableTargets, setAvailableTargets] = useState<Target[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  
  // Form states
  const [addingTargets, setAddingTargets] = useState(false);
  const [selectedTargets, setSelectedTargets] = useState<number[]>([]);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    loadGroups();
    loadAllTargets();
  }, []);

  useEffect(() => {
    if (selectedGroup) {
      loadGroupTargets(selectedGroup.id);
    }
  }, [selectedGroup]);

  useEffect(() => {
    // Filter available targets (not in current group)
    const groupTargetIds = new Set(groupTargets.map(t => t.id));
    const filtered = allTargets.filter(target => 
      !groupTargetIds.has(target.id) &&
      (target.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
       target.hostname.toLowerCase().includes(searchTerm.toLowerCase()) ||
       (target.ip_address && target.ip_address.includes(searchTerm)))
    );
    setAvailableTargets(filtered);
  }, [allTargets, groupTargets, searchTerm]);

  const loadGroups = async () => {
    try {
      // const data = await targetGroupApi.list(true);
      // setGroups(data.groups);
      setGroups([]);
    } catch (err) {
      console.error('Failed to load groups:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadAllTargets = async () => {
    try {
      // const data = await assetTargetApi.list();
      // setAllTargets(data.targets || []);
      setAllTargets([]);
    } catch (err) {
      console.error('Failed to load targets:', err);
    }
  };

  const loadGroupTargets = async (groupId: number) => {
    try {
      setLoading(true);
      // const data = await targetGroupApi.getTargets(groupId);
      // setGroupTargets(data.targets || []);
      setGroupTargets([]);
    } catch (err) {
      console.error('Failed to load group targets:', err);
      setGroupTargets([]);
    } finally {
      setLoading(false);
    }
  };

  const startAddingTargets = () => {
    setSelectedTargets([]);
    setSearchTerm('');
    setAddingTargets(true);
  };

  const cancelAddingTargets = () => {
    setAddingTargets(false);
    setSelectedTargets([]);
    setSearchTerm('');
  };

  const handleAddTargets = async () => {
    if (!selectedGroup || selectedTargets.length === 0) return;

    try {
      setSaving(true);
      // await targetGroupApi.addTargets(selectedGroup.id, selectedTargets);
      await loadGroupTargets(selectedGroup.id);
      await loadGroups(); // Refresh counts
      cancelAddingTargets();
    } catch (error) {
      console.error('Failed to add targets:', error);
      alert('Failed to add targets to group');
    } finally {
      setSaving(false);
    }
  };

  const handleRemoveTarget = async (targetId: number) => {
    if (!selectedGroup) return;
    
    if (window.confirm('Remove this target from the group?')) {
      try {
        // await targetGroupApi.removeTarget(selectedGroup.id, targetId);
        await loadGroupTargets(selectedGroup.id);
        await loadGroups(); // Refresh counts
      } catch (error) {
        console.error('Failed to remove target:', error);
        alert('Failed to remove target from group');
      }
    }
  };

  const toggleTargetSelection = (targetId: number) => {
    setSelectedTargets(prev => 
      prev.includes(targetId) 
        ? prev.filter(id => id !== targetId)
        : [...prev, targetId]
    );
  };

  if (loading && groups.length === 0) {
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
          .groups-table tr:hover {
            background: var(--neutral-50);
          }
          .groups-table tr.selected {
            background: var(--primary-blue-light);
            border-left: 3px solid var(--primary-blue);
          }
          .groups-table tr {
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
            border: 1px solid transparent;
            border-radius: 3px;
            background: transparent;
            cursor: pointer;
            transition: all 0.2s;
            font-size: 12px;
          }
          .btn-primary {
            color: var(--primary-blue);
            border-color: var(--primary-blue-light);
          }
          .btn-primary:hover {
            background: var(--primary-blue-light);
          }
          .btn-success {
            background: var(--success-green);
            color: white;
            border-color: var(--success-green);
          }
          .btn-success:hover {
            background: var(--success-green-dark);
          }
          .btn-danger {
            color: var(--danger-red);
            border-color: var(--danger-red-light);
          }
          .btn-danger:hover {
            background: var(--danger-red-light);
          }
          .btn-secondary {
            color: var(--neutral-600);
            border-color: var(--neutral-300);
          }
          .btn-secondary:hover {
            background: var(--neutral-100);
          }
          
          /* Color indicator */
          .color-indicator {
            width: 12px;
            height: 12px;
            border-radius: 2px;
            border: 1px solid var(--neutral-300);
            display: inline-block;
            margin-right: 6px;
          }
          
          /* Search input */
          .search-container {
            padding: 8px;
            border-bottom: 1px solid var(--neutral-200);
          }
          .search-input {
            width: 100%;
            padding: 6px 8px 6px 32px;
            border: 1px solid var(--neutral-300);
            border-radius: 3px;
            font-size: 12px;
            background: white;
            position: relative;
          }
          .search-input:focus {
            outline: none;
            border-color: var(--primary-blue);
            box-shadow: 0 0 0 2px var(--blue-100);
          }
          .search-icon {
            position: absolute;
            left: 8px;
            top: 50%;
            transform: translateY(-50%);
            color: var(--neutral-500);
            pointer-events: none;
          }
          
          /* Checkbox */
          .checkbox {
            width: 14px;
            height: 14px;
            margin-right: 8px;
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
        {/* Column 1: Groups List */}
        <div className="dashboard-section">
          <div className="section-header">
            Target Groups ({groups.length})
          </div>
          <div className="compact-content">
            {groups.length === 0 ? (
              <div className="empty-state">
                <Users size={32} />
                <h3>No Groups</h3>
                <p>Create target groups first in the Groups Management tab.</p>
              </div>
            ) : (
              <div className="table-container">
                <table className="groups-table">
                  <thead>
                    <tr>
                      <th>Name</th>
                      <th>Targets</th>
                    </tr>
                  </thead>
                  <tbody>
                    {groups.map((group) => (
                      <tr 
                        key={group.id} 
                        className={selectedGroup?.id === group.id ? 'selected' : ''}
                        onClick={() => setSelectedGroup(group)}
                      >
                        <td>
                          <div style={{ display: 'flex', alignItems: 'center' }}>
                            {group.color && (
                              <span 
                                className="color-indicator" 
                                style={{ backgroundColor: group.color }}
                              ></span>
                            )}
                            {group.name}
                          </div>
                        </td>
                        <td>{group.target_count || 0}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>

        {/* Column 2: Group Targets */}
        <div className="dashboard-section">
          <div className="section-header">
            {selectedGroup ? `${selectedGroup.name} Targets` : 'Group Targets'}
            {selectedGroup && (
              <button 
                className="btn-icon btn-success"
                onClick={startAddingTargets}
                title="Add targets to group"
                disabled={addingTargets}
              >
                <Plus size={16} />
              </button>
            )}
          </div>
          <div className="compact-content">
            {!selectedGroup ? (
              <div className="empty-state">
                <Monitor size={32} />
                <h3>Select a Group</h3>
                <p>Choose a target group to view and manage its targets.</p>
              </div>
            ) : loading ? (
              <div className="loading-overlay">
                <div className="loading-spinner"></div>
              </div>
            ) : groupTargets.length === 0 ? (
              <div className="empty-state">
                <Monitor size={32} />
                <h3>No Targets</h3>
                <p>This group has no targets assigned yet.</p>
                <button 
                  className="btn-icon btn-success"
                  onClick={startAddingTargets}
                  title="Add first target"
                >
                  <Plus size={16} />
                </button>
              </div>
            ) : (
              <div className="table-container">
                <table className="targets-table">
                  <thead>
                    <tr>
                      <th>Name</th>
                      <th>Hostname</th>
                      <th>IP Address</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {groupTargets.map((target) => (
                      <tr key={target.id}>
                        <td>{target.name}</td>
                        <td>{target.hostname}</td>
                        <td>{target.ip_address || '-'}</td>
                        <td>
                          <button
                            className="btn-icon btn-danger"
                            onClick={() => handleRemoveTarget(target.id)}
                            title="Remove from group"
                          >
                            <Minus size={14} />
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

        {/* Column 3: Available Targets (when adding) */}
        <div className="dashboard-section">
          <div className="section-header">
            {addingTargets ? 'Add Targets' : 'Available Targets'}
            {addingTargets && (
              <div className="action-buttons">
                <button
                  className="btn-icon btn-success"
                  onClick={handleAddTargets}
                  disabled={saving || selectedTargets.length === 0}
                  title="Add selected targets"
                >
                  <Check size={14} />
                </button>
                <button
                  className="btn-icon btn-secondary"
                  onClick={cancelAddingTargets}
                  title="Cancel"
                >
                  <X size={14} />
                </button>
              </div>
            )}
          </div>
          <div className="compact-content">
            {!addingTargets ? (
              <div className="empty-state">
                <Eye size={32} />
                <h3>Add Targets</h3>
                <p>Click the + button to add targets to the selected group.</p>
              </div>
            ) : (
              <>
                <div className="search-container" style={{ position: 'relative' }}>
                  <Search className="search-icon" size={16} />
                  <input
                    type="text"
                    className="search-input"
                    placeholder="Search targets..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                  />
                </div>
                <div className="table-container">
                  {availableTargets.length === 0 ? (
                    <div className="empty-state">
                      <Monitor size={32} />
                      <h3>No Available Targets</h3>
                      <p>All targets are already in this group or no targets match your search.</p>
                    </div>
                  ) : (
                    <table className="targets-table">
                      <thead>
                        <tr>
                          <th>Select</th>
                          <th>Name</th>
                          <th>Hostname</th>
                          <th>IP</th>
                        </tr>
                      </thead>
                      <tbody>
                        {availableTargets.map((target) => (
                          <tr 
                            key={target.id}
                            className={`selectable ${selectedTargets.includes(target.id) ? 'selected' : ''}`}
                            onClick={() => toggleTargetSelection(target.id)}
                          >
                            <td>
                              <input
                                type="checkbox"
                                className="checkbox"
                                checked={selectedTargets.includes(target.id)}
                                onChange={() => toggleTargetSelection(target.id)}
                              />
                            </td>
                            <td>{target.name}</td>
                            <td>{target.hostname}</td>
                            <td>{target.ip_address || '-'}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  )}
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </>
  );
};

export default TargetGroupMemberships;