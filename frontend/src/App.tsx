import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import Navbar from './components/Navbar';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Users from './pages/Users';


import Targets from './pages/Targets';


import Jobs from './pages/Jobs';
import JobMonitoring from './pages/JobMonitoring';

import JobRuns from './pages/JobRuns';



import SystemSettings from './pages/SystemSettings';
import LegacySettings from './pages/LegacySettings';
import RoleManagement from './pages/RoleManagement';

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
                    <Route path="/" element={<Dashboard />} />
                    <Route path="/user-management" element={<Users />} />
                    <Route path="/user-management/:action" element={<Users />} />
                    <Route path="/user-management/:action/:id" element={<Users />} />

                    <Route path="/targets-management" element={<Targets />} />
                    <Route path="/targets-management/:action" element={<Targets />} />
                    <Route path="/targets-management/:action/:id" element={<Targets />} />


                    <Route path="/job-management" element={<Jobs />} />
                    <Route path="/job-management/:action" element={<Jobs />} />
                    <Route path="/job-management/:action/:id" element={<Jobs />} />

                    <Route path="/job-monitoring" element={<JobMonitoring />} />

                    <Route path="/job-runs" element={<Navigate to="/history/job-runs" />} />
                    <Route path="/history/job-runs" element={<JobRuns />} />



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