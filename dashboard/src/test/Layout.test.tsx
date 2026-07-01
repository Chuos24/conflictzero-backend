import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

import { ThemeProvider } from '../context/ThemeContext';
import { AuthProvider } from '../context/AuthContext';
import Layout from '../components/Layout';

// Mock Outlet
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    Outlet: () => <div data-testid="outlet">Outlet Content</div>,
    useNavigate: () => vi.fn(),
  };
});

// Mock api para AuthProvider
vi.mock('../services/api', () => ({
  default: {
    defaults: { headers: { common: {} } },
    get: vi
      .fn()
      .mockResolvedValue({ data: { id: 1, company_name: 'Test Corp', plan_tier: 'founder' } }),
    post: vi.fn(),
  },
}));

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <AuthProvider>
          <MemoryRouter>{children}</MemoryRouter>
        </AuthProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
};

describe('Layout', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  it('renders layout with navigation', () => {
    render(<Layout />, { wrapper: createWrapper() });

    expect(screen.getByText('Conflict Zero')).toBeInTheDocument();
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Verificaciones')).toBeInTheDocument();
    expect(screen.getByTestId('outlet')).toBeInTheDocument();
  });

  it('renders user info when authenticated', () => {
    localStorage.setItem('cz_token', 'test-token');

    render(<Layout />, { wrapper: createWrapper() });

    // Wait for auth to load
    expect(screen.getByText('Cerrar sesión')).toBeInTheDocument();
  });

  it('shows navigation items', () => {
    render(<Layout />, { wrapper: createWrapper() });

    expect(screen.getByText('Comparar')).toBeInTheDocument();
    expect(screen.getByText('Mi Red')).toBeInTheDocument();
    expect(screen.getByText('Monitoreo')).toBeInTheDocument();
    expect(screen.getByText('Configuración')).toBeInTheDocument();
  });
});
