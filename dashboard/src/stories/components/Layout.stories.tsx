// @ts-nocheck
import { BrowserRouter } from 'react-router-dom'
import { Layout } from '../components/Layout'
import { ThemeProvider } from '../context/ThemeContext'
import { AuthProvider } from '../context/AuthContext'
import { ToastProvider } from '../context/ToastContext'

// Mock de AuthProvider con usuario logueado
function MockAuthProvider({ children }) {
  return (
    <AuthProvider>
      {children}
    </AuthProvider>
  )
}

export default {
  title: 'Components/Layout',
  component: Layout,
  decorators: [
    (Story) => (
      <BrowserRouter>
        <MockAuthProvider>
          <ThemeProvider>
            <ToastProvider>
              <Story />
            </ToastProvider>
          </ThemeProvider>
        </MockAuthProvider>
      </BrowserRouter>
    ),
  ],
  parameters: {
    layout: 'fullscreen',
    docs: {
      description: {
        component: 'Layout principal de la aplicación con sidebar, header y área de contenido. Incluye navegación y controles de usuario.',
      },
    },
  },
}

export const Default = {
  render: () => (
    <Layout>
      <div style={{ padding: '20px' }}>
        <h1>Contenido de Ejemplo</h1>
        <p>Este es el área principal donde se renderizan las páginas.</p>
      </div>
    </Layout>
  ),
  name: 'Layout Completo',
}

export const WithLongContent = {
  render: () => (
    <Layout>
      <div style={{ padding: '20px' }}>
        <h1>Página con Scroll</h1>
        {Array.from({ length: 20 }).map((_, i) => (
          <p key={i}>
            Lorem ipsum dolor sit amet, consectetur adipiscing elit. 
            Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
          </p>
        ))}
      </div>
    </Layout>
  ),
  name: 'Con Contenido Largo',
}

export const MobileViewport = {
  ...Default,
  name: 'Vista Mobile',
  parameters: {
    viewport: {
      defaultViewport: 'mobile1',
    },
  },
}
