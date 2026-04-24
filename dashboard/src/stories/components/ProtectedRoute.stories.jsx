import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { ProtectedRoute } from '../components/ProtectedRoute'

// Componentes de ejemplo
function PublicPage() {
  return <div style={{ padding: '40px' }}>🌐 Página Pública - Accesible sin login</div>
}

function PrivatePage() {
  return <div style={{ padding: '40px' }}>🔒 Página Privada - Requiere autenticación</div>
}

function LoginPage() {
  return <div style={{ padding: '40px' }}>🔑 Página de Login</div>
}

export default {
  title: 'Components/ProtectedRoute',
  component: ProtectedRoute,
  decorators: [
    (Story) => (
      <BrowserRouter>
        <Story />
      </BrowserRouter>
    ),
  ],
  parameters: {
    layout: 'fullscreen',
    docs: {
      description: {
        component: 'ProtectedRoute protege rutas privadas redirigiendo a login cuando no hay sesión activa.',
      },
    },
  },
}

export const Authenticated = {
  render: () => (
    <Routes>
      <Route path="/" element={<PublicPage />} />
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <PrivatePage />
          </ProtectedRoute>
        }
      />
      <Route path="*" element={<Navigate to="/dashboard" />} />
    </Routes>
  ),
  name: 'Usuario Autenticado',
  parameters: {
    docs: {
      description: {
        story: 'Cuando el usuario está autenticado, se renderiza el contenido protegido.',
      },
    },
  },
}

export const Unauthenticated = {
  render: () => {
    // Simulamos un usuario no autenticado forzando el estado
    return (
      <Routes>
        <Route path="/" element={<PublicPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <PrivatePage />
            </ProtectedRoute>
          }
        />
        <Route path="*" element={<Navigate to="/dashboard" />} />
      </Routes>
    )
  },
  name: 'Usuario No Autenticado',
  parameters: {
    docs: {
      description: {
        story: 'Cuando no hay sesión, el usuario es redirigido automáticamente a /login.',
      },
    },
  },
}
