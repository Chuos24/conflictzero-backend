import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';

import ProtectedRoute from '../components/ProtectedRoute';
import * as AuthContextModule from '../context/AuthContext';

describe('ProtectedRoute', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('renders outlet when authenticated', () => {
    vi.spyOn(AuthContextModule, 'useAuth').mockReturnValue({
      user: { id: 1, ruc: '20123456789' },
      isAuthenticated: true,
      loading: false,
      logout: vi.fn(),
      login: vi.fn(),
      setUser: vi.fn(),
    } as any);

    render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <Routes>
          <Route element={<ProtectedRoute />}>
            <Route
              path="/dashboard"
              element={<div data-testid="protected">Protected Content</div>}
            />
          </Route>
        </Routes>
      </MemoryRouter>
    );

    expect(document.querySelector('[data-testid="protected"]')).toBeInTheDocument();
  });

  it('redirects to login when not authenticated', () => {
    vi.spyOn(AuthContextModule, 'useAuth').mockReturnValue({
      user: null,
      isAuthenticated: false,
      loading: false,
      logout: vi.fn(),
      login: vi.fn(),
      setUser: vi.fn(),
    } as any);

    render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <Routes>
          <Route element={<ProtectedRoute />}>
            <Route
              path="/dashboard"
              element={<div data-testid="protected">Protected Content</div>}
            />
          </Route>
          <Route path="/login" element={<div data-testid="login">Login Page</div>} />
        </Routes>
      </MemoryRouter>
    );

    expect(document.querySelector('[data-testid="login"]')).toBeInTheDocument();
  });

  it('shows loading spinner when auth is loading', () => {
    vi.spyOn(AuthContextModule, 'useAuth').mockReturnValue({
      user: null,
      isAuthenticated: false,
      loading: true,
      logout: vi.fn(),
      login: vi.fn(),
      setUser: vi.fn(),
    } as any);

    render(
      <MemoryRouter>
        <ProtectedRoute />
      </MemoryRouter>
    );

    expect(document.querySelector('.spinner')).toBeInTheDocument();
  });
});
