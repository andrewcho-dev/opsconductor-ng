import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import Navbar from './components/Navbar';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import AIChatPage from './pages/AIChat';
import Assets from './pages/Assets';
import SystemSettings from './pages/SystemSettings';
import LegacySettings from './pages/LegacySettings';
import InfrastructureMonitoring from './pages/InfrastructureMonitoring';
import NotificationsPage from './pages/NotificationsPage';
import TemplatesPage from './pages/TemplatesPage';
import AuditLogsPage from './pages/AuditLogsPage';
import NetworkAnalysisPage from './pages/NetworkAnalysisPage';
import SchedulesPage from './pages/SchedulesPage';
import AIMonitoringPage from './pages/AIMonitoringPage';

// Protected Route Component
interface ProtectedRouteProps {
  children: React.ReactNode;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth();
  
  if (isLoading) {
    return <div style={{ padding: '20px', textAlign: 'center' }}>Loading...</div>;
  }
  
  return isAuthenticated ? <>{children}</> : <Navigate to="/login" />;
};

const App: React.FC = () => {
  return (
    <AuthProvider>
      <Router>
        <div className="app-container">
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route
              path="/*"
              element={
                <ProtectedRoute>
                  <Navbar />
                  <Routes>
                    <Route path="/" element={<AIChatPage />} />
                    <Route path="/dashboard" element={<Dashboard />} />
                    
                    {/* Schedules Route */}
                    <Route path="/schedules" element={<SchedulesPage />} />

                    {/* Assets Routes */}
                    <Route path="/assets" element={<Assets />} />
                    <Route path="/assets/:action" element={<Assets />} />
                    <Route path="/assets/:action/:id" element={<Assets />} />

                    {/* Infrastructure Routes */}
                    <Route path="/infrastructure" element={<InfrastructureMonitoring />} />
                    <Route path="/network-analysis" element={<NetworkAnalysisPage />} />
                    <Route path="/ai-monitoring" element={<AIMonitoringPage />} />

                    {/* Communication Routes */}
                    <Route path="/notifications" element={<NotificationsPage />} />
                    <Route path="/templates" element={<TemplatesPage />} />
                    <Route path="/audit-logs" element={<AuditLogsPage />} />

                    <Route path="/settings" element={<Navigate to="/settings/smtp" />} />
                    <Route path="/settings/:section" element={<SystemSettings />} />
                    <Route path="/legacy-settings" element={<LegacySettings />} />
                    <Route path="*" element={<Navigate to="/" />} />
                  </Routes>
                </ProtectedRoute>
              }
            />
          </Routes>
        </div>
      </Router>
    </AuthProvider>
  );
};

export default App;