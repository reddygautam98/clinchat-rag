import React, { Suspense } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { Box, CircularProgress } from '@mui/material';
import { useAuth } from './hooks/useAuth';

// Layout components
import DashboardLayout from './components/layout/DashboardLayout';
import LoginPage from './pages/auth/LoginPage';

// Lazy load pages for better performance
const Dashboard = React.lazy(() => import('./pages/dashboard/Dashboard'));
const DocumentAnalysis = React.lazy(() => import('./pages/documents/DocumentAnalysis'));
const PatientView = React.lazy(() => import('./pages/patient/PatientView'));
const AnalysisResults = React.lazy(() => import('./pages/analysis/AnalysisResults'));
const ComplianceReports = React.lazy(() => import('./pages/compliance/ComplianceReports'));
const UserManagement = React.lazy(() => import('./pages/admin/UserManagement'));
const Settings = React.lazy(() => import('./pages/settings/Settings'));

// Loading component
const LoadingSpinner = () => (
  <Box 
    display="flex" 
    justifyContent="center" 
    alignItems="center" 
    minHeight="60vh"
  >
    <CircularProgress size={60} />
  </Box>
);

// Protected route component
interface ProtectedRouteProps {
  children: React.ReactNode;
  requiredRoles?: string[];
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ 
  children, 
  requiredRoles = [] 
}) => {
  const { isAuthenticated, user, loading } = useAuth();
  
  if (loading) return <LoadingSpinner />;
  
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  
  if (requiredRoles.length > 0 && user) {
    const hasRequiredRole = requiredRoles.some(role => 
      user.roles?.includes(role)
    );
    
    if (!hasRequiredRole) {
      return <Navigate to="/dashboard" replace />;
    }
  }
  
  return <>{children}</>;
};

const App: React.FC = () => {
  return (
    <Routes>
      {/* Public routes */}
      <Route path="/login" element={<LoginPage />} />
      
      {/* Protected routes */}
      <Route 
        path="/" 
        element={
          <ProtectedRoute>
            <DashboardLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Navigate to="/dashboard" replace />} />
        
        <Route 
          path="dashboard" 
          element={
            <Suspense fallback={<LoadingSpinner />}>
              <Dashboard />
            </Suspense>
          } 
        />
        
        <Route 
          path="documents" 
          element={
            <Suspense fallback={<LoadingSpinner />}>
              <DocumentAnalysis />
            </Suspense>
          } 
        />
        
        <Route 
          path="patient/:patientId?" 
          element={
            <Suspense fallback={<LoadingSpinner />}>
              <PatientView />
            </Suspense>
          } 
        />
        
        <Route 
          path="analysis/:analysisId?" 
          element={
            <Suspense fallback={<LoadingSpinner />}>
              <AnalysisResults />
            </Suspense>
          } 
        />
        
        <Route 
          path="compliance" 
          element={
            <ProtectedRoute requiredRoles={['admin', 'compliance_officer']}>
              <Suspense fallback={<LoadingSpinner />}>
                <ComplianceReports />
              </Suspense>
            </ProtectedRoute>
          } 
        />
        
        <Route 
          path="admin/users" 
          element={
            <ProtectedRoute requiredRoles={['admin']}>
              <Suspense fallback={<LoadingSpinner />}>
                <UserManagement />
              </Suspense>
            </ProtectedRoute>
          } 
        />
        
        <Route 
          path="settings" 
          element={
            <Suspense fallback={<LoadingSpinner />}>
              <Settings />
            </Suspense>
          } 
        />
      </Route>
      
      {/* Catch all route */}
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
};

export default App;