// @ts-nocheck
import Badge from '../src/components/Badge'

/**
 * Badge - Componente de etiqueta reutilizable
 * 
 * Referencia: Atlassian Design System badges
 * https://atlassian.design/components/badge/
 */
export default {
  title: 'Components/Badge',
  component: Badge,
  tags: ['autodocs'],
  argTypes: {
    variant: {
      control: 'select',
      options: ['default', 'success', 'warning', 'error', 'info'],
      description: 'Estilo visual del badge',
    },
    size: {
      control: 'select',
      options: ['small', 'medium', 'large'],
      description: 'Tamaño del badge',
    },
    pulse: {
      control: 'boolean',
      description: 'Activa animación de pulso',
    },
    children: {
      control: 'text',
      description: 'Contenido del badge',
    },
    className: {
      control: 'text',
      description: 'Clases CSS adicionales',
    },
  },
}

export const Default = {
  args: {
    children: 'Badge',
    variant: 'default',
    size: 'medium',
  },
}

export const Success = {
  args: {
    children: 'Verificado',
    variant: 'success',
    size: 'medium',
  },
}

export const Warning = {
  args: {
    children: 'Pendiente',
    variant: 'warning',
    size: 'medium',
  },
}

export const Error = {
  args: {
    children: 'Rechazado',
    variant: 'error',
    size: 'medium',
  },
}

export const Info = {
  args: {
    children: 'Info',
    variant: 'info',
    size: 'medium',
  },
}

export const Small = {
  args: {
    children: 'Small',
    variant: 'default',
    size: 'small',
  },
}

export const Large = {
  args: {
    children: 'Large',
    variant: 'default',
    size: 'large',
  },
}

export const WithPulse = {
  args: {
    children: 'En vivo',
    variant: 'success',
    size: 'medium',
    pulse: true,
  },
}

export const AllVariants = {
  render: () => (
    <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', alignItems: 'center' }}>
      <Badge variant="default">Default</Badge>
      <Badge variant="success">Success</Badge>
      <Badge variant="warning">Warning</Badge>
      <Badge variant="error">Error</Badge>
      <Badge variant="info">Info</Badge>
    </div>
  ),
}

export const AllSizes = {
  render: () => (
    <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', alignItems: 'center' }}>
      <Badge size="small">Small</Badge>
      <Badge size="medium">Medium</Badge>
      <Badge size="large">Large</Badge>
    </div>
  ),
}
