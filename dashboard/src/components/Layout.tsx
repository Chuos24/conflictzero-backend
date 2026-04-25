import React from 'react'
import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import ThemeToggle from './ThemeToggle'
import './Layout.css'

export interface NavItem {
  path: string
  label: string
  icon: string
}

function Layout(): JSX.Element {
  const { user, logout } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const navItems: NavItem[] = [
    { path: '/dashboard', label: 'Dashboard', icon: '📊' },
    { path: '/verifications', label: 'Verificaciones', icon: '✓' },
    { path: '/compare', label: 'Comparar', icon: '⚖️' },
    { path: '/network', label: 'Mi Red', icon: '🌐' },
    { path: '/invites', label: 'Invitaciones', icon: '📧' },
    { path: '/compliance', label: 'Compliance', icon: '🛡️' },
    { path: '/profile', label: 'Perfil', icon: '👤' },
    { path: '/settings', label: 'Configuración', icon: '⚙️' },
  ]

  return (
    <div className="layout">
      <aside className="sidebar">
        <div className="sidebar-header">
          <h1 className="logo">
            <span className="logo-cz">CZ</span>
            <span className="logo-text">Conflict Zero</span>
          </h1>
          <div className="user-badge">
            {user?.plan_tier === 'founder' && <span className="badge founder">FOUNDER</span>}
          </div>
        </div>

        <nav className="sidebar-nav">
          {navItems.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              className={`nav-item ${location.pathname === item.path ? 'active' : ''}`}
            >
              <span className="nav-icon">{item.icon}</span>
              <span className="nav-label">{item.label}</span>
            </Link>
          ))}
        </nav>

        <div className="sidebar-footer">
          <div className="user-info">
            <span className="user-name">{user?.company_name || 'Usuario'}</span>
            <span className="user-ruc">RUC: {user?.ruc_display || '---'}</span>
          </div>
          <div className="sidebar-actions">
            <ThemeToggle />
            <button onClick={handleLogout} className="logout-btn">
              <span>🚪</span> Cerrar sesión
            </button>
          </div>
        </div>
      </aside>

      <main className="main-content">
        <Outlet />
      </main>
    </div>
  )
}

export default Layout
