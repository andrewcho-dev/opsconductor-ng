import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import Navbar from './components/Navbar';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import AIChatPage from './pages/AIChat';
import Assets from './pages/Assets';
import Settings from './pages/Settings';
import SchedulesPage from './pages/SchedulesPage';

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

                    {/* Settings */}
                    <Route path="/settings" element={<Settings />} />
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