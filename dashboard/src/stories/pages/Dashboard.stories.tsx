// @ts-nocheck
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { AuthProvider } from '../src/context/AuthContext'
import { ToastProvider } from '../src/context/ToastContext'
import { ThemeProvider } from '../src/context/ThemeContext'
import Dashboard from '../src/pages/Dashboard'

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false } }
})

function DashboardWrapper() {
  return (
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={['/dashboard']}>
        <AuthProvider>
          <ThemeProvider>
            <ToastProvider>
              <Routes>
                <Route path="/dashboard" element={<Dashboard />} />
              </Routes>
            </ToastProvider>
          </ThemeProvider>
        </AuthProvider>
      </MemoryRouter>
    </QueryClientProvider>
  )
}

/**
 * Dashboard Page - Pagina principal de analytics
 *
 * Referencia: Stripe Dashboard layout
 * https://dashboard.stripe.com/
 */
export default {
  title: 'Pages/Dashboard',
  component: DashboardWrapper,
  parameters: {
    layout: 'fullscreen',
    docs: {
      description: {
        component: 'Pagina principal del dashboard con metricas, graficos y acciones rapidas.',
      },
    },
  },
}

export const Default = {
  render: () => <DashboardWrapper />,
}
