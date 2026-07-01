import { Suspense, lazy } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';

import { AuthProvider } from './context/AuthContext';
import { ThemeProvider } from './context/ThemeContext';
import { ToastProvider } from './context/ToastContext';
import { queryClient } from './lib/queryClient';
import Layout from './components/Layout';
import ProtectedRoute from './components/ProtectedRoute';
import LoadingSpinner from './components/LoadingSpinner';

// Lazy-loaded pages for code splitting
const Login = lazy(() => import('./pages/Login'));
const Register = lazy(() => import('./pages/Register'));
const Dashboard = lazy(() => import('./pages/Dashboard'));
const Verifications = lazy(() => import('./pages/Verifications'));
const Compare = lazy(() => import('./pages/Compare'));
const Invites = lazy(() => import('./pages/Invites'));
const Compliance = lazy(() => import('./pages/Compliance'));
const Network = lazy(() => import('./pages/Network'));
const Profile = lazy(() => import('./pages/Profile'));
const Settings = lazy(() => import('./pages/Settings'));
const Monitoring = lazy(() => import('./pages/Monitoring'));
const Privacy = lazy(() => import('./pages/Privacy'));
const AuditReports = lazy(() => import('./pages/AuditReports'));
const WhiteLabel = lazy(() => import('./pages/WhiteLabel'));
const Countries = lazy(() => import('./pages/Countries'));

function PageLoader(): JSX.Element {
  return (
    <div
      style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh' }}
    >
      <LoadingSpinner size="large" />
    </div>
  );
}

function App(): JSX.Element {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <ToastProvider>
          <AuthProvider>
            <BrowserRouter>
              <Suspense fallback={<PageLoader />}>
                <Routes>
                  {/* Public Routes */}
                  <Route path="/login" element={<Login />} />
                  <Route path="/register" element={<Register />} />

                  {/* Protected Routes */}
                  <Route element={<ProtectedRoute />}>
                    <Route element={<Layout />}>
                      <Route path="/" element={<Navigate to="/dashboard" replace />} />
                      <Route path="/dashboard" element={<Dashboard />} />
                      <Route path="/verifications" element={<Verifications />} />
                      <Route path="/compare" element={<Compare />} />
                      <Route path="/invites" element={<Invites />} />
                      <Route path="/compliance" element={<Compliance />} />
                      <Route path="/network" element={<Network />} />
                      <Route path="/monitoring" element={<Monitoring />} />
                      <Route path="/privacy" element={<Privacy />} />
                      <Route path="/audit" element={<AuditReports />} />
                      <Route path="/white-label" element={<WhiteLabel />} />
                      <Route path="/countries" element={<Countries />} />
                      <Route path="/profile" element={<Profile />} />
                      <Route path="/settings" element={<Settings />} />
                    </Route>
                  </Route>

                  {/* Catch all */}
                  <Route path="*" element={<Navigate to="/" replace />} />
                </Routes>
              </Suspense>
            </BrowserRouter>
          </AuthProvider>
        </ToastProvider>
      </ThemeProvider>
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  );
}

export default App;
