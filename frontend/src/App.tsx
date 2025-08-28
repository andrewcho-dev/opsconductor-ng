import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import Navbar from './components/Navbar';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Users from './pages/Users';
import Credentials from './pages/Credentials';
import Targets from './pages/Targets';
import TargetGroups from './components/TargetGroups';
import Jobs from './pages/Jobs';
import Schedules from './pages/Schedules';
import AdvancedScheduler from './components/AdvancedScheduler';
import JobRuns from './pages/JobRuns';
import JobRunDetail from './pages/JobRunDetail';
import Notifications from './pages/Notifications';
import EnhancedSettings from './pages/EnhancedSettings';

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
        <div className="App">
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route
              path="/*"
              element={
                <ProtectedRoute>
                  <Navbar />
                  <div className="container">
                    <Routes>
                      <Route path="/" element={<Dashboard />} />
                      <Route path="/user-management" element={<Users />} />
                      <Route path="/credential-management" element={<Credentials />} />
                      <Route path="/targets-management" element={<Targets />} />
                      <Route path="/target-groups" element={<TargetGroups />} />
                      <Route path="/job-management" element={<Jobs />} />
                      <Route path="/schedule-management" element={<Schedules />} />
                      <Route path="/advanced-scheduler" element={<AdvancedScheduler />} />
                      <Route path="/job-runs" element={<JobRuns />} />
                      <Route path="/job-runs/:id" element={<JobRunDetail />} />
                      <Route path="/notifications" element={<Notifications />} />
                      <Route path="/settings" element={<EnhancedSettings />} />
                      <Route path="*" element={<Navigate to="/" />} />
                    </Routes>
                  </div>
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