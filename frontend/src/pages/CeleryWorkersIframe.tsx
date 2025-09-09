import React from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useLocation } from 'react-router-dom';
import { Activity, AlertCircle } from 'lucide-react';

const CeleryWorkersIframe: React.FC = () => {
  const { user } = useAuth();
  const location = useLocation();
  
  // Get task parameter from URL
  const searchParams = new URLSearchParams(location.search);
  const taskId = searchParams.get('task');

  // Check if user is admin
  if (user?.role !== 'admin') {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="bg-yellow-50 border border-yellow-200 text-yellow-700 px-4 py-3 rounded">
            <div className="flex items-center">
              <AlertCircle size={20} className="mr-2" />
              <div>
                <h3 className="font-medium">Access Restricted</h3>
                <p className="mt-1">Only administrators can access the Celery Workers dashboard.</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="dense-dashboard">
      {/* Header */}
      <div className="dashboard-header">
        <div className="header-left">
          <Activity size={20} style={{ color: '#2563eb' }} />
          <h1>Celery Workers</h1>
        </div>
      </div>

      {/* Full-width iframe section - matching CeleryHealthCard placement */}
      <div className="dashboard-grid" style={{ gridTemplateColumns: '1fr' }}>
        <div className="dashboard-section" style={{ height: 'calc(100vh - 110px)' }}>
          <div className="section-header">
            {taskId ? (
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span>Task: {taskId}</span>
                <span style={{ fontSize: '11px', color: 'var(--neutral-500)' }}>
                  (If task shows "Unknown", it may have expired from Celery)
                </span>
              </div>
            ) : "Worker Dashboard"}
          </div>
          <div className="compact-content" style={{ padding: 0 }}>
            <iframe
              ref={(iframe) => {
                if (iframe) {
                  iframe.onload = () => {
                    try {
                      const iframeDoc = iframe.contentDocument || iframe.contentWindow?.document;
                      if (iframeDoc) {
                        // Inject custom CSS to match OpsConductor visual standards
                        const style = iframeDoc.createElement('style');
                        style.textContent = `
                          /* OpsConductor Font Size Override */
                          body, html {
                            font-size: 13px !important;
                            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', sans-serif !important;
                          }
                          
                          /* Scale down various Flower UI elements */
                          .navbar, .nav {
                            font-size: 12px !important;
                          }
                          
                          .table, .table td, .table th {
                            font-size: 12px !important;
                          }
                          
                          .btn, .form-control, .form-select {
                            font-size: 12px !important;
                          }
                          
                          .card-header, .card-title {
                            font-size: 13px !important;
                          }
                          
                          .card-body {
                            font-size: 12px !important;
                          }
                          
                          /* Adjust spacing to match dense layout */
                          .container-fluid {
                            padding: 8px 12px !important;
                          }
                        `;
                        iframeDoc.head.appendChild(style);
                      }
                    } catch (e) {
                      console.log('Cannot inject CSS into iframe (cross-origin):', e);
                    }
                  };
                }
              }}
              src={taskId ? `/flower/task/${taskId}` : "/flower"}
              title="Celery Workers Dashboard"
              style={{ 
                width: '100%', 
                height: '100%', 
                border: 'none'
              }}
              allowFullScreen
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default CeleryWorkersIframe;