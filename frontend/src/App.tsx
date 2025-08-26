import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { isAuthenticated } from './services/api';
import { AuthProvider } from './contexts/AuthContext';
import Navbar from './components/Navbar';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Users from './pages/Users';
import Credentials from './pages/Credentials';
import Targets from './pages/Targets';
import Jobs from './pages/Jobs';
import Schedules from './pages/Schedules';
import JobRuns from './pages/JobRuns';
import JobRunDetail from './pages/JobRunDetail';
import Notifications from './components/Notifications';
import Settings from './pages/Settings';

// Protected Route Component
interface ProtectedRouteProps {
  children: React.ReactNode;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  return isAuthenticated() ? <>{children}</> : <Navigate to="/login" />;
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
                      <Route path="/users" element={<Users />} />
                      <Route path="/credentials" element={<Credentials />} />
                      <Route path="/targets" element={<Targets />} />
                      <Route path="/jobs" element={<Jobs />} />
                      <Route path="/schedule-management" element={<Schedules />} />
                      <Route path="/runs" element={<JobRuns />} />
                      <Route path="/runs/:id" element={<JobRunDetail />} />
                      <Route path="/notifications" element={<Notifications />} />
                      <Route path="/settings" element={<Settings />} />
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