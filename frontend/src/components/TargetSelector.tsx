import React, { useState, useEffect } from 'react';
import { Target } from '../types';
import { targetApi } from '../services/api';

interface TargetSelectorProps {
  selectedTargets: number[];
  onTargetsChange: (targets: number[]) => void;
  multiSelect?: boolean;
  showDetails?: boolean;
  filterByPlatform?: string;
  filterByStatus?: string;
}

interface TargetGroup {
  id: string;
  name: string;
  description: string;
  targets: Target[];
}

const TargetSelector: React.FC<TargetSelectorProps> = ({
  selectedTargets,
  onTargetsChange,
  multiSelect = true,
  showDetails = false,
  filterByPlatform,
  filterByStatus
}) => {
  const [targets, setTargets] = useState<Target[]>([]);
  const [targetGroups, setTargetGroups] = useState<TargetGroup[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [viewMode, setViewMode] = useState<'list' | 'grid' | 'groups'>('list');
  const [showOffline, setShowOffline] = useState(true);
  const [platformFilter, setPlatformFilter] = useState<string>('all');


  useEffect(() => {
    fetchTargets();
    fetchTargetGroups();
  }, []);

  const fetchTargets = async () => {
    try {
      const response = await targetApi.list();
      setTargets(response.targets || []);
    } catch (error) {
      console.error('Failed to fetch targets:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchTargetGroups = async () => {
    try {
      // Mock target groups for now
      const mockGroups: TargetGroup[] = [
        {
          id: 'web-servers',
          name: 'Web Servers',
          description: 'Production web servers',
          targets: []
        },
        {
          id: 'database-servers',
          name: 'Database Servers',
          description: 'Database cluster nodes',
          targets: []
        },
        {
          id: 'development',
          name: 'Development Environment',
          description: 'Development and testing servers',
          targets: []
        }
      ];
      setTargetGroups(mockGroups);
    } catch (error) {
      console.error('Failed to fetch target groups:', error);
    }
  };

  const handleTargetToggle = (targetId: number) => {
    if (multiSelect) {
      if (selectedTargets.includes(targetId)) {
        onTargetsChange(selectedTargets.filter(id => id !== targetId));
      } else {
        onTargetsChange([...selectedTargets, targetId]);
      }
    } else {
      onTargetsChange([targetId]);
    }
  };

  const handleSelectAll = () => {
    const filteredTargetIds = getFilteredTargets().map(t => t.id);
    onTargetsChange(filteredTargetIds);
  };

  const handleSelectNone = () => {
    onTargetsChange([]);
  };

  const getFilteredTargets = () => {
    return targets.filter(target => {
      // Search filter
      const matchesSearch = searchTerm === '' || 
        target.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        target.hostname.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (target.ip_address && target.ip_address.toLowerCase().includes(searchTerm.toLowerCase()));

      // Platform filter
      const matchesPlatform = platformFilter === 'all' || 
        (target.os_type && target.os_type.toLowerCase() === platformFilter.toLowerCase());

      // Status filter (using a default status since Target interface doesn't have status)
      const matchesStatus = showOffline || true; // Assume all targets are available

      // Props filters
      const matchesPropsPlatform = !filterByPlatform || 
        (target.os_type && target.os_type.toLowerCase() === filterByPlatform.toLowerCase());

      const matchesPropsStatus = !filterByStatus || true; // Assume all targets match status

      return matchesSearch && matchesPlatform && 
             matchesStatus && matchesPropsPlatform && matchesPropsStatus;
    });
  };

  const getTargetStatusIcon = (status: string) => {
    switch (status) {
      case 'online': return '🟢';
      case 'offline': return '🔴';
      case 'warning': return '🟡';
      default: return '⚪';
    }
  };

  const getTargetPlatformIcon = (platform: string) => {
    switch (platform?.toLowerCase()) {
      case 'windows': return '🪟';
      case 'linux': return '🐧';
      case 'macos': return '🍎';
      case 'docker': return '🐳';
      default: return '💻';
    }
  };

  const renderTargetCard = (target: Target) => (
    <div
      key={target.id}
      style={{
        border: `2px solid ${selectedTargets.includes(target.id) ? '#007bff' : '#ddd'}`,
        borderRadius: '8px',
        padding: '12px',
        margin: '8px',
        backgroundColor: selectedTargets.includes(target.id) ? '#f0f8ff' : 'white',
        cursor: 'pointer',
        transition: 'all 0.2s ease',
        minWidth: viewMode === 'grid' ? '200px' : 'auto',
        flex: viewMode === 'grid' ? '0 0 200px' : 'none'
      }}
      onClick={() => handleTargetToggle(target.id)}
    >
      <div style={{ display: 'flex', alignItems: 'center', marginBottom: '8px' }}>
        <input
          type={multiSelect ? 'checkbox' : 'radio'}
          checked={selectedTargets.includes(target.id)}
          onChange={() => handleTargetToggle(target.id)}
          style={{ marginRight: '8px' }}
          onClick={(e) => e.stopPropagation()}
        />
        <span style={{ fontSize: '16px', marginRight: '8px' }}>
          {getTargetPlatformIcon(target.os_type || 'unknown')}
        </span>
        <span style={{ fontSize: '14px', marginRight: '8px' }}>
          🟢
        </span>
        <strong style={{ fontSize: '14px' }}>{target.name}</strong>
      </div>
      
      <div style={{ fontSize: '12px', color: '#666', marginBottom: '4px' }}>
        <strong>Host:</strong> {target.hostname}:{target.port}
      </div>
      
      {target.os_type && (
        <div style={{ fontSize: '12px', color: '#666', marginBottom: '4px' }}>
          <strong>OS Type:</strong> {target.os_type}
        </div>
      )}
      
      {target.ip_address && (
        <div style={{ fontSize: '12px', color: '#666', marginBottom: '4px' }}>
          <strong>IP Address:</strong> {target.ip_address}
        </div>
      )}
      

      
      {showDetails && target.tags && target.tags.length > 0 && (
        <div style={{ marginTop: '8px' }}>
          {target.tags.map(tag => (
            <span
              key={tag}
              style={{
                display: 'inline-block',
                backgroundColor: '#e9ecef',
                color: '#495057',
                padding: '2px 6px',
                borderRadius: '12px',
                fontSize: '10px',
                marginRight: '4px',
                marginBottom: '2px'
              }}
            >
              {tag}
            </span>
          ))}
        </div>
      )}
    </div>
  );

  const renderTargetGroups = () => (
    <div>
      {targetGroups.map(group => (
        <div key={group.id} style={{ marginBottom: '20px' }}>
          <div style={{ 
            backgroundColor: '#f8f9fa', 
            padding: '10px', 
            borderRadius: '6px',
            marginBottom: '10px',
            border: '1px solid #dee2e6'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <h6 style={{ margin: '0 0 4px 0', fontSize: '14px' }}>{group.name}</h6>
                <p style={{ margin: 0, fontSize: '12px', color: '#666' }}>{group.description}</p>
              </div>
              <div>
                <button
                  onClick={() => {
                    const groupTargets = getFilteredTargets().filter(t => 
                      group.targets.some(gt => gt.id === t.id)
                    );
                    const groupTargetIds = groupTargets.map(t => t.id);
                    onTargetsChange(Array.from(new Set([...selectedTargets, ...groupTargetIds])));
                  }}
                  style={{
                    padding: '4px 8px',
                    fontSize: '10px',
                    backgroundColor: '#007bff',
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    marginRight: '4px'
                  }}
                >
                  Select All
                </button>
              </div>
            </div>
          </div>
          
          <div style={{ 
            display: 'flex', 
            flexWrap: 'wrap',
            gap: '8px',
            paddingLeft: '10px'
          }}>
            {getFilteredTargets()
              .filter(target => group.targets.some(gt => gt.id === target.id))
              .map(renderTargetCard)}
          </div>
        </div>
      ))}
      
      {/* Ungrouped targets */}
      <div>
        <div style={{ 
          backgroundColor: '#f8f9fa', 
          padding: '10px', 
          borderRadius: '6px',
          marginBottom: '10px',
          border: '1px solid #dee2e6'
        }}>
          <h6 style={{ margin: 0, fontSize: '14px' }}>Other Targets</h6>
        </div>
        
        <div style={{ 
          display: 'flex', 
          flexWrap: 'wrap',
          gap: '8px',
          paddingLeft: '10px'
        }}>
          {getFilteredTargets()
            .filter(target => !targetGroups.some(group => 
              group.targets.some(gt => gt.id === target.id)
            ))
            .map(renderTargetCard)}
        </div>
      </div>
    </div>
  );

  if (loading) {
    return <div style={{ padding: '20px', textAlign: 'center' }}>Loading targets...</div>;
  }

  const filteredTargets = getFilteredTargets();
  const platforms = Array.from(new Set(targets.map(t => t.os_type).filter(Boolean)));

  return (
    <div style={{ border: '1px solid #ddd', borderRadius: '6px', backgroundColor: 'white' }}>
      {/* Header */}
      <div style={{ 
        padding: '12px', 
        borderBottom: '1px solid #ddd',
        backgroundColor: '#f8f9fa'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
          <h6 style={{ margin: 0, fontSize: '14px' }}>
            Select Targets ({selectedTargets.length} of {filteredTargets.length} selected)
          </h6>
          
          <div style={{ display: 'flex', gap: '4px' }}>
            <button
              onClick={() => setViewMode('list')}
              style={{
                padding: '4px 8px',
                fontSize: '10px',
                backgroundColor: viewMode === 'list' ? '#007bff' : '#6c757d',
                color: 'white',
                border: 'none',
                borderRadius: '3px',
                cursor: 'pointer'
              }}
            >
              List
            </button>
            <button
              onClick={() => setViewMode('grid')}
              style={{
                padding: '4px 8px',
                fontSize: '10px',
                backgroundColor: viewMode === 'grid' ? '#007bff' : '#6c757d',
                color: 'white',
                border: 'none',
                borderRadius: '3px',
                cursor: 'pointer'
              }}
            >
              Grid
            </button>
            <button
              onClick={() => setViewMode('groups')}
              style={{
                padding: '4px 8px',
                fontSize: '10px',
                backgroundColor: viewMode === 'groups' ? '#007bff' : '#6c757d',
                color: 'white',
                border: 'none',
                borderRadius: '3px',
                cursor: 'pointer'
              }}
            >
              Groups
            </button>
          </div>
        </div>
        
        {/* Search and Filters */}
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center', flexWrap: 'wrap' }}>
          <input
            type="text"
            placeholder="Search targets..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            style={{
              flex: 1,
              minWidth: '150px',
              padding: '4px 8px',
              fontSize: '12px',
              border: '1px solid #ddd',
              borderRadius: '4px'
            }}
          />
          
          <select
            value={platformFilter}
            onChange={(e) => setPlatformFilter(e.target.value)}
            style={{
              padding: '4px 8px',
              fontSize: '12px',
              border: '1px solid #ddd',
              borderRadius: '4px'
            }}
          >
            <option value="all">All Platforms</option>
            {platforms.map(platform => (
              <option key={platform} value={platform}>{platform}</option>
            ))}
          </select>
          

          
          <label style={{ display: 'flex', alignItems: 'center', fontSize: '12px' }}>
            <input
              type="checkbox"
              checked={showOffline}
              onChange={(e) => setShowOffline(e.target.checked)}
              style={{ marginRight: '4px' }}
            />
            Show Offline
          </label>
        </div>
        
        {/* Bulk Actions */}
        {multiSelect && (
          <div style={{ display: 'flex', gap: '8px', marginTop: '8px' }}>
            <button
              onClick={handleSelectAll}
              style={{
                padding: '4px 12px',
                fontSize: '11px',
                backgroundColor: '#28a745',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer'
              }}
            >
              Select All ({filteredTargets.length})
            </button>
            <button
              onClick={handleSelectNone}
              style={{
                padding: '4px 12px',
                fontSize: '11px',
                backgroundColor: '#dc3545',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer'
              }}
            >
              Select None
            </button>
          </div>
        )}
      </div>
      
      {/* Target List */}
      <div style={{ 
        maxHeight: '400px', 
        overflowY: 'auto',
        padding: viewMode === 'list' ? '0' : '8px'
      }}>
        {filteredTargets.length === 0 ? (
          <div style={{ padding: '20px', textAlign: 'center', color: '#666' }}>
            No targets found matching your criteria
          </div>
        ) : viewMode === 'groups' ? (
          renderTargetGroups()
        ) : (
          <div style={{ 
            display: viewMode === 'grid' ? 'flex' : 'block',
            flexWrap: 'wrap',
            gap: viewMode === 'grid' ? '8px' : '0'
          }}>
            {filteredTargets.map(renderTargetCard)}
          </div>
        )}
      </div>
      
      {/* Footer */}
      {selectedTargets.length > 0 && (
        <div style={{ 
          padding: '8px 12px', 
          borderTop: '1px solid #ddd',
          backgroundColor: '#f8f9fa',
          fontSize: '12px',
          color: '#666'
        }}>
          Selected: {selectedTargets.map(id => {
            const target = targets.find(t => t.id === id);
            return target ? target.name : `ID:${id}`;
          }).join(', ')}
        </div>
      )}
    </div>
  );
};

export default TargetSelector;