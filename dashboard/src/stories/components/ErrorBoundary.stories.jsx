import { ErrorBoundary } from '../components/ErrorBoundary'

// Componente que lanza error para demostración
function BuggyComponent({ shouldThrow = false }) {
  if (shouldThrow) {
    throw new Error('Este es un error de demostración para Storybook')
  }
  return <div>Componente funcionando correctamente</div>
}

export default {
  title: 'Components/ErrorBoundary',
  component: ErrorBoundary,
  parameters: {
    layout: 'padded',
    docs: {
      description: {
        component: 'ErrorBoundary captura errores de React y muestra UI alternativa en lugar de crashear la app.',
      },
    },
  },
}

export const Working = {
  render: () => (
    <ErrorBoundary>
      <BuggyComponent shouldThrow={false} />
    </ErrorBoundary>
  ),
  name: 'Funcionando Normalmente',
}

export const WithError = {
  render: () => (
    <ErrorBoundary>
      <BuggyComponent shouldThrow={true} />
    </ErrorBoundary>
  ),
  name: 'Capturando Error',
}

export const CustomFallback = {
  render: () => (
    <ErrorBoundary
      fallback={
        <div style={{ padding: '20px', background: '#fee2e2', borderRadius: '8px' }}>
          <h3>⚠️ Error Personalizado</h3>
          <p>Algo salió mal, pero estamos trabajando en ello.</p>
        </div>
      }
    >
      <BuggyComponent shouldThrow={true} />
    </ErrorBoundary>
  ),
  name: 'Fallback Personalizado',
}
