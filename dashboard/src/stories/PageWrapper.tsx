// @ts-nocheck
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { AuthProvider } from '../src/context/AuthContext'
import { ToastProvider } from '../src/context/ToastContext'
import { ThemeProvider } from '../src/context/ThemeContext'

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false } }
})

export function PageWrapper({ children, initialEntry = '/' }: { children: React.ReactNode; initialEntry?: string }) {
  return (
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[initialEntry]}>
        <AuthProvider>
          <ThemeProvider>
            <ToastProvider>
              <Routes>
                <Route path={initialEntry} element={children} />
              </Routes>
            </ToastProvider>
          </ThemeProvider>
        </AuthProvider>
      </MemoryRouter>
    </QueryClientProvider>
  )
}
