import React from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClientProvider } from '@tanstack/react-query'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'
import { AuthProvider } from './context/AuthContext'
import { ThemeProvider } from './context/ThemeContext'
import { ToastProvider } from './context/ToastContext'
import { queryClient } from './lib/queryClient'
import Layout from './components/Layout'
import ProtectedRoute from './components/ProtectedRoute'

// Pages
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Verifications from './pages/Verifications'
import Compare from './pages/Compare'
import Invites from './pages/Invites'
import Compliance from './pages/Compliance'
import Network from './pages/Network'
import Profile from './pages/Profile'
import Settings from './pages/Settings'

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <ToastProvider>
          <AuthProvider>
            <BrowserRouter>
              <Routes>
                {/* Public Routes */}
                <Route path="/login" element={<Login />} />

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
                    <Route path="/profile" element={<Profile />} />
                    <Route path="/settings" element={<Settings />} />
                  </Route>
                </Route>

                {/* Catch all */}
                <Route path="*" element={<Navigate to="/" replace />} />
              </Routes>
            </BrowserRouter>
          </AuthProvider>
        </ToastProvider>
      </ThemeProvider>
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  )
}

export default App
