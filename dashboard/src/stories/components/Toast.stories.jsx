import Toast from '../src/components/Toast'

/**
 * Toast - Notificación flotante
 * 
 * Referencia: Atlassian Design System banner/flag
 * https://atlassian.design/components/banner/
 */
export default {
  title: 'Components/Toast',
  component: Toast,
  tags: ['autodocs'],
  argTypes: {
    type: {
      control: 'select',
      options: ['success', 'error', 'warning', 'info'],
      description: 'Tipo de toast',
    },
    message: {
      control: 'text',
      description: 'Mensaje a mostrar',
    },
    onClose: {
      action: 'closed',
      description: 'Callback al cerrar',
    },
  },
}

export const Success = {
  args: {
    type: 'success',
    message: 'Verificación completada exitosamente',
    onClose: () => {},
  },
}

export const Error = {
  args: {
    type: 'error',
    message: 'Error al conectar con el servidor',
    onClose: () => {},
  },
}

export const Warning = {
  args: {
    type: 'warning',
    message: 'Su plan está por expirar en 3 días',
    onClose: () => {},
  },
}

export const Info = {
  args: {
    type: 'info',
    message: 'Nueva versión disponible',
    onClose: () => {},
  },
}

export const AllTypes = {
  render: () => (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
      <Toast type="success" message="Operación exitosa" onClose={() => {}} />
      <Toast type="error" message="Ha ocurrido un error" onClose={() => {}} />
      <Toast type="warning" message="Advertencia importante" onClose={() => {}} />
      <Toast type="info" message="Información relevante" onClose={() => {}} />
    </div>
  ),
}
