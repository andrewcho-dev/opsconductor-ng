import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import Navbar from './components/Navbar';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Users from './pages/Users';
import Roles from './pages/Roles';
import AIChatPage from './pages/AIChat';
import Assets from './pages/Assets';
import JobRuns from './pages/JobRuns';
import SystemSettings from './pages/SystemSettings';
import LegacySettings from './pages/LegacySettings';
import RoleManagement from './pages/RoleManagement';
import Workflows from './pages/Workflows';
import FlowRuns from './pages/FlowRuns';
import InfrastructureMonitoring from './pages/InfrastructureMonitoring';

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
                    
                    {/* Workflows Routes */}
                    <Route path="/workflows" element={<Workflows />} />
                    <Route path="/workflows/:action" element={<Workflows />} />
                    <Route path="/workflows/:action/:id" element={<Workflows />} />
                    <Route path="/workflows/runs" element={<FlowRuns />} />
                    <Route path="/workflows/runs/:id" element={<FlowRuns />} />

                    {/* Assets Routes */}
                    <Route path="/assets" element={<Assets />} />
                    <Route path="/assets/:action" element={<Assets />} />
                    <Route path="/assets/:action/:id" element={<Assets />} />

                    {/* Infrastructure Routes */}
                    <Route path="/infrastructure" element={<InfrastructureMonitoring />} />

                    {/* History Routes - Legacy Job Runs Only */}
                    <Route path="/job-runs" element={<Navigate to="/history/job-runs" />} />
                    <Route path="/history/job-runs" element={<JobRuns />} />

                    {/* User & Role Management Routes */}
                    <Route path="/users" element={<Users />} />
                    <Route path="/users/:action" element={<Users />} />
                    <Route path="/users/:action/:id" element={<Users />} />
                    <Route path="/roles" element={<Roles />} />
                    <Route path="/roles/:action" element={<Roles />} />
                    <Route path="/roles/:action/:id" element={<Roles />} />



                    <Route path="/settings" element={<Navigate to="/settings/smtp" />} />
                    <Route path="/settings/roles" element={<RoleManagement />} />
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