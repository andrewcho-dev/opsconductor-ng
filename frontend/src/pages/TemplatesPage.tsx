import React, { useState, useEffect } from 'react';
import { 
  FileText, Plus, Search, Filter, Eye, Edit, Trash2, 
  Mail, MessageSquare, Send, Code, Play
} from 'lucide-react';
import { templateApi } from '../services/api';
import { Template, TemplateCreate } from '../types';

const TemplatesPage: React.FC = () => {
  const [templates, setTemplates] = useState<Template[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [typeFilter, setTypeFilter] = useState<string>('all');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showPreviewModal, setShowPreviewModal] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState<Template | null>(null);

  // Pagination
  const [currentPage, setCurrentPage] = useState(1);
  const [totalItems, setTotalItems] = useState(0);
  const itemsPerPage = 20;

  useEffect(() => {
    loadTemplates();
  }, [currentPage, typeFilter]);

  const loadTemplates = async () => {
    try {
      setLoading(true);
      const filters: any = {};
      if (typeFilter !== 'all') filters.template_type = typeFilter;
      
      const response = await templateApi.list(
        (currentPage - 1) * itemsPerPage,
        itemsPerPage,
        filters
      );
      setTemplates(response.templates);
      setTotalItems(response.total);
    } catch (err: any) {
      setError(err.message || 'Failed to load templates');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!window.confirm('Are you sure you want to delete this template?')) return;
    
    try {
      await templateApi.delete(id);
      loadTemplates();
    } catch (err: any) {
      setError(err.message || 'Failed to delete template');
    }
  };

  const getTemplateIcon = (type: string) => {
    switch (type) {
      case 'email': return <Mail className="text-primary" size={16} />;
      case 'slack': return <MessageSquare className="text-success" size={16} />;
      case 'teams': return <MessageSquare className="text-info" size={16} />;
      case 'discord': return <MessageSquare className="text-secondary" size={16} />;
      case 'webhook': return <Send className="text-warning" size={16} />;
      default: return <FileText className="text-muted" size={16} />;
    }
  };

  const filteredTemplates = templates.filter(template =>
    template.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const totalPages = Math.ceil(totalItems / itemsPerPage);

  if (loading) {
    return (
      <div className="container-fluid">
        <div className="d-flex justify-content-center align-items-center" style={{ height: '400px' }}>
          <div className="spinner-border text-primary" role="status">
            <span className="visually-hidden">Loading...</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="container-fluid">
      <div className="row">
        <div className="col-12">
          <div className="d-flex justify-content-between align-items-center mb-4">
            <div>
              <h1 className="h3 mb-0">
                <FileText className="me-2" size={24} />
                Message Templates
              </h1>
              <p className="text-muted mb-0">Manage notification and communication templates</p>
            </div>
            <button
              className="btn btn-primary"
              onClick={() => setShowCreateModal(true)}
            >
              <Plus size={16} className="me-1" />
              Create Template
            </button>
          </div>

          {error && (
            <div className="alert alert-danger alert-dismissible fade show" role="alert">
              {error}
              <button
                type="button"
                className="btn-close"
                onClick={() => setError(null)}
              ></button>
            </div>
          )}

          {/* Filters */}
          <div className="card mb-4">
            <div className="card-body">
              <div className="row g-3">
                <div className="col-md-6">
                  <div className="input-group">
                    <span className="input-group-text">
                      <Search size={16} />
                    </span>
                    <input
                      type="text"
                      className="form-control"
                      placeholder="Search templates..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                    />
                  </div>
                </div>
                <div className="col-md-4">
                  <select
                    className="form-select"
                    value={typeFilter}
                    onChange={(e) => setTypeFilter(e.target.value)}
                  >
                    <option value="all">All Types</option>
                    <option value="email">Email</option>
                    <option value="slack">Slack</option>
                    <option value="teams">Microsoft Teams</option>
                    <option value="discord">Discord</option>
                    <option value="webhook">Webhook</option>
                    <option value="sms">SMS</option>
                  </select>
                </div>
                <div className="col-md-2">
                  <button
                    className="btn btn-outline-secondary w-100"
                    onClick={() => {
                      setSearchTerm('');
                      setTypeFilter('all');
                    }}
                  >
                    <Filter size={16} className="me-1" />
                    Clear
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* Templates Grid */}
          <div className="row">
            {filteredTemplates.length === 0 ? (
              <div className="col-12">
                <div className="card">
                  <div className="card-body text-center py-5">
                    <FileText size={48} className="text-muted mb-3" />
                    <h5 className="text-muted">No templates found</h5>
                    <p className="text-muted">Create your first template to get started.</p>
                  </div>
                </div>
              </div>
            ) : (
              filteredTemplates.map((template) => (
                <div key={template.id} className="col-md-6 col-lg-4 mb-4">
                  <div className="card h-100">
                    <div className="card-body">
                      <div className="d-flex justify-content-between align-items-start mb-3">
                        <div className="d-flex align-items-center">
                          {getTemplateIcon(template.template_type)}
                          <span className="ms-2 text-capitalize fw-medium">
                            {template.template_type}
                          </span>
                        </div>
                        <div className="d-flex align-items-center">
                          {template.is_active ? (
                            <span className="badge bg-success">Active</span>
                          ) : (
                            <span className="badge bg-secondary">Inactive</span>
                          )}
                        </div>
                      </div>
                      
                      <h6 className="card-title">{template.name}</h6>
                      
                      <div className="mb-3">
                        <small className="text-muted">
                          Variables: {template.metadata && Object.keys(template.metadata).length > 0 ? Object.keys(template.metadata).join(', ') : 'None'}
                        </small>
                      </div>
                      
                      <div className="d-flex justify-content-between align-items-center">
                        <small className="text-muted">
                          Created: {new Date(template.created_at).toLocaleDateString()}
                        </small>
                        <div className="btn-group btn-group-sm">
                          <button
                            className="btn btn-outline-primary"
                            onClick={() => {
                              setSelectedTemplate(template);
                              setShowPreviewModal(true);
                            }}
                            title="Preview"
                          >
                            <Eye size={14} />
                          </button>
                          <button
                            className="btn btn-outline-secondary"
                            onClick={() => {
                              setSelectedTemplate(template);
                              setShowEditModal(true);
                            }}
                            title="Edit"
                          >
                            <Edit size={14} />
                          </button>
                          <button
                            className="btn btn-outline-danger"
                            onClick={() => handleDelete(template.id)}
                            title="Delete"
                          >
                            <Trash2 size={14} />
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <nav className="mt-4">
              <ul className="pagination justify-content-center">
                <li className={`page-item ${currentPage === 1 ? 'disabled' : ''}`}>
                  <button
                    className="page-link"
                    onClick={() => setCurrentPage(currentPage - 1)}
                    disabled={currentPage === 1}
                  >
                    Previous
                  </button>
                </li>
                {Array.from({ length: totalPages }, (_, i) => i + 1).map((page) => (
                  <li key={page} className={`page-item ${currentPage === page ? 'active' : ''}`}>
                    <button
                      className="page-link"
                      onClick={() => setCurrentPage(page)}
                    >
                      {page}
                    </button>
                  </li>
                ))}
                <li className={`page-item ${currentPage === totalPages ? 'disabled' : ''}`}>
                  <button
                    className="page-link"
                    onClick={() => setCurrentPage(currentPage + 1)}
                    disabled={currentPage === totalPages}
                  >
                    Next
                  </button>
                </li>
              </ul>
            </nav>
          )}
        </div>
      </div>

      {/* Create Template Modal */}
      {showCreateModal && (
        <TemplateModal
          onClose={() => setShowCreateModal(false)}
          onSuccess={() => {
            setShowCreateModal(false);
            loadTemplates();
          }}
        />
      )}

      {/* Edit Template Modal */}
      {showEditModal && selectedTemplate && (
        <TemplateModal
          template={selectedTemplate}
          onClose={() => {
            setShowEditModal(false);
            setSelectedTemplate(null);
          }}
          onSuccess={() => {
            setShowEditModal(false);
            setSelectedTemplate(null);
            loadTemplates();
          }}
        />
      )}

      {/* Preview Template Modal */}
      {showPreviewModal && selectedTemplate && (
        <TemplatePreviewModal
          template={selectedTemplate}
          onClose={() => {
            setShowPreviewModal(false);
            setSelectedTemplate(null);
          }}
        />
      )}
    </div>
  );
};

// Template Modal Component (Create/Edit)
const TemplateModal: React.FC<{
  template?: Template;
  onClose: () => void;
  onSuccess: () => void;
}> = ({ template, onClose, onSuccess }) => {
  const isEdit = !!template;
  const [formData, setFormData] = useState<TemplateCreate>({
    name: template?.name || '',
    template_type: template?.template_type || 'email',
    subject_template: template?.subject_template || '',
    body_template: template?.body_template || '',
    metadata: template?.metadata || {},
    is_active: template?.is_active ?? true
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [newVariable, setNewVariable] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      if (isEdit && template) {
        await templateApi.update(template.id, formData);
      } else {
        await templateApi.create(formData);
      }
      onSuccess();
    } catch (err: any) {
      setError(err.message || `Failed to ${isEdit ? 'update' : 'create'} template`);
    } finally {
      setLoading(false);
    }
  };

  const addVariable = () => {
    if (newVariable.trim() && !Object.keys(formData.metadata || {}).includes(newVariable.trim())) {
      setFormData({
        ...formData,
        metadata: { ...(formData.metadata || {}), [newVariable.trim()]: '' }
      });
      setNewVariable('');
    }
  };

  const removeVariable = (variable: string) => {
    const newMetadata = { ...(formData.metadata || {}) };
    delete newMetadata[variable];
    setFormData({
      ...formData,
      metadata: newMetadata
    });
  };

  return (
    <div className="modal show d-block" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
      <div className="modal-dialog modal-xl">
        <div className="modal-content">
          <div className="modal-header">
            <h5 className="modal-title">
              {isEdit ? 'Edit Template' : 'Create Template'}
            </h5>
            <button type="button" className="btn-close" onClick={onClose}></button>
          </div>
          <form onSubmit={handleSubmit}>
            <div className="modal-body">
              {error && (
                <div className="alert alert-danger">{error}</div>
              )}
              
              <div className="row g-3">
                <div className="col-md-8">
                  <label className="form-label">Name *</label>
                  <input
                    type="text"
                    className="form-control"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    required
                  />
                </div>
                
                <div className="col-md-4">
                  <label className="form-label">Type *</label>
                  <select
                    className="form-select"
                    value={formData.template_type}
                    onChange={(e) => setFormData({ ...formData, template_type: e.target.value as any })}
                  >
                    <option value="email">Email</option>
                    <option value="slack">Slack</option>
                    <option value="teams">Microsoft Teams</option>
                    <option value="discord">Discord</option>
                    <option value="webhook">Webhook</option>
                    <option value="sms">SMS</option>
                  </select>
                </div>
                
                
                {(formData.template_type === 'email' || formData.template_type === 'teams') && (
                  <div className="col-12">
                    <label className="form-label">Subject Template</label>
                    <input
                      type="text"
                      className="form-control"
                      value={formData.subject_template}
                      onChange={(e) => setFormData({ ...formData, subject_template: e.target.value })}
                      placeholder="Use {{variable}} for dynamic content"
                    />
                  </div>
                )}
                
                <div className="col-12">
                  <label className="form-label">Body Template *</label>
                  <textarea
                    className="form-control"
                    rows={8}
                    value={formData.body_template}
                    onChange={(e) => setFormData({ ...formData, body_template: e.target.value })}
                    placeholder="Use {{variable}} for dynamic content"
                    required
                  />
                </div>
                
                <div className="col-12">
                  <label className="form-label">Variables</label>
                  <div className="input-group mb-2">
                    <input
                      type="text"
                      className="form-control"
                      value={newVariable}
                      onChange={(e) => setNewVariable(e.target.value)}
                      placeholder="Enter variable name"
                      onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addVariable())}
                    />
                    <button
                      type="button"
                      className="btn btn-outline-secondary"
                      onClick={addVariable}
                    >
                      Add
                    </button>
                  </div>
                  <div className="d-flex flex-wrap gap-2">
                    {Object.keys(formData.metadata || {}).map((variable: string) => (
                      <span key={variable} className="badge bg-secondary d-flex align-items-center">
                        {variable}
                        <button
                          type="button"
                          className="btn-close btn-close-white ms-2"
                          style={{ fontSize: '0.7em' }}
                          onClick={() => removeVariable(variable)}
                        ></button>
                      </span>
                    ))}
                  </div>
                </div>
                
                <div className="col-12">
                  <div className="form-check">
                    <input
                      className="form-check-input"
                      type="checkbox"
                      checked={formData.is_active}
                      onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                    />
                    <label className="form-check-label">
                      Active
                    </label>
                  </div>
                </div>
              </div>
            </div>
            <div className="modal-footer">
              <button type="button" className="btn btn-secondary" onClick={onClose}>
                Cancel
              </button>
              <button type="submit" className="btn btn-primary" disabled={loading}>
                {loading ? (
                  <>
                    <span className="spinner-border spinner-border-sm me-2"></span>
                    {isEdit ? 'Updating...' : 'Creating...'}
                  </>
                ) : (
                  isEdit ? 'Update Template' : 'Create Template'
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

// Template Preview Modal Component
const TemplatePreviewModal: React.FC<{
  template: Template;
  onClose: () => void;
}> = ({ template, onClose }) => {
  const [previewData, setPreviewData] = useState<{ subject?: string; body: string } | null>(null);
  const [variables, setVariables] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Initialize variables with sample data
    const sampleVars: Record<string, string> = {};
    if (template.metadata) {
      Object.keys(template.metadata).forEach(variable => {
        sampleVars[variable] = `[${variable}]`;
      });
    }
    setVariables(sampleVars);
  }, [template]);

  const generatePreview = async () => {
    setLoading(true);
    try {
      const response = await templateApi.preview({
        template_type: template.template_type,
        subject_template: template.subject_template,
        body_template: template.body_template,
        variables
      });
      setPreviewData(response);
    } catch (err: any) {
      console.error('Failed to generate preview:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    generatePreview();
  }, [variables]);

  return (
    <div className="modal show d-block" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
      <div className="modal-dialog modal-xl">
        <div className="modal-content">
          <div className="modal-header">
            <h5 className="modal-title">Template Preview: {template.name}</h5>
            <button type="button" className="btn-close" onClick={onClose}></button>
          </div>
          <div className="modal-body">
            <div className="row">
              <div className="col-md-4">
                <h6>Variables</h6>
                {template.metadata && Object.keys(template.metadata).length > 0 ? (
                  <div className="mb-3">
                    {Object.keys(template.metadata).map((variable: string) => (
                      <div key={variable} className="mb-2">
                        <label className="form-label small">{variable}</label>
                        <input
                          type="text"
                          className="form-control form-control-sm"
                          value={variables[variable] || ''}
                          onChange={(e) => setVariables({
                            ...variables,
                            [variable]: e.target.value
                          })}
                        />
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-muted">No variables defined</p>
                )}
              </div>
              <div className="col-md-8">
                <h6>Preview</h6>
                {loading ? (
                  <div className="text-center py-3">
                    <div className="spinner-border spinner-border-sm"></div>
                  </div>
                ) : previewData ? (
                  <div>
                    {previewData.subject && (
                      <div className="mb-3">
                        <label className="form-label small fw-bold">Subject:</label>
                        <div className="border rounded p-2 bg-light">
                          {previewData.subject}
                        </div>
                      </div>
                    )}
                    <div>
                      <label className="form-label small fw-bold">Body:</label>
                      <div className="border rounded p-3 bg-light" style={{ minHeight: '200px', whiteSpace: 'pre-wrap' }}>
                        {previewData.body}
                      </div>
                    </div>
                  </div>
                ) : (
                  <p className="text-muted">Unable to generate preview</p>
                )}
              </div>
            </div>
          </div>
          <div className="modal-footer">
            <button type="button" className="btn btn-secondary" onClick={onClose}>
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TemplatesPage;