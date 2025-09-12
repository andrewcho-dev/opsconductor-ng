import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import Navbar from './components/Navbar';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Users from './pages/Users';

import Targets from './pages/Targets';
import TargetGroups from './pages/TargetGroups';

import Discovery from './pages/Discovery';
import Jobs from './pages/Jobs';


import JobRuns from './pages/JobRuns';

import NotificationHistoryPage from './pages/NotificationHistory';
import CeleryWorkersIframe from './pages/CeleryWorkersIframe';
import SystemSettings from './pages/SystemSettings';
import LegacySettings from './pages/LegacySettings';

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

                    <Route path="/target-groups" element={<TargetGroups />} />
                    <Route path="/target-groups/:action" element={<TargetGroups />} />

                    <Route path="/discovery" element={<Discovery />} />
                    <Route path="/job-management" element={<Jobs />} />
                    <Route path="/job-management/:action" element={<Jobs />} />
                    <Route path="/job-management/:action/:id" element={<Jobs />} />


                    <Route path="/job-runs" element={<Navigate to="/history/job-runs" />} />
                    <Route path="/history/job-runs" element={<JobRuns />} />
                    <Route path="/history/notifications" element={<NotificationHistoryPage />} />
                    <Route path="/history/celery-workers-iframe" element={<CeleryWorkersIframe />} />
                    <Route path="/notifications" element={<Navigate to="/settings/notification-preferences" />} />
                    <Route path="/settings" element={<Navigate to="/settings/step-library" />} />
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