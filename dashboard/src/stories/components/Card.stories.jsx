import Card from '../src/components/Card'
import Badge from '../src/components/Badge'

/**
 * Card - Componente de tarjeta reutilizable
 * 
 * Referencia: Material Design Cards
 * https://material.io/components/cards
 */
export default {
  title: 'Components/Card',
  component: Card,
  tags: ['autodocs'],
  argTypes: {
    title: {
      control: 'text',
      description: 'Título de la tarjeta',
    },
    icon: {
      control: 'text',
      description: 'Icono (emoji o string)',
    },
    hoverable: {
      control: 'boolean',
      description: 'Efecto hover',
    },
    onClick: {
      action: 'clicked',
      description: 'Handler de click',
    },
  },
}

export const Default = {
  args: {
    title: 'Título de tarjeta',
    children: <p>Contenido de la tarjeta con información relevante.</p>,
  },
}

export const WithIcon = {
  args: {
    title: 'Estadísticas',
    icon: '📊',
    children: <p>Total de verificaciones: 1,234</p>,
  },
}

export const WithAction = {
  args: {
    title: 'Verificaciones',
    icon: '✓',
    action: <button className="btn-sm">Ver todas</button>,
    children: <p>12 verificaciones este mes</p>,
  },
}

export const Hoverable = {
  args: {
    title: 'Clickable',
    hoverable: true,
    children: <p>Esta tarjeta tiene efecto hover.</p>,
  },
}

export const Clickable = {
  args: {
    title: 'Ver detalle',
    hoverable: true,
    onClick: () => alert('Card clicked!'),
    children: <p>Haz click en esta tarjeta.</p>,
  },
}

export const ComplexContent = {
  args: {
    title: 'Estado del proveedor',
    icon: '🏢',
    action: <Badge variant="success">Activo</Badge>,
    children: (
      <div>
        <p><strong>RUC:</strong> 20123456789</p>
        <p><strong>Razón social:</strong> Constructora ABC S.A.C.</p>
        <p><strong>Última verificación:</strong> Hoy</p>
      </div>
    ),
  },
}
