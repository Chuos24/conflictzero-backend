import Skeleton, { SkeletonCard, SkeletonTable, SkeletonProfile } from '../src/components/Skeleton'

/**
 * Skeleton - Componentes de placeholder para estados de carga
 * 
 * Referencia: Material Design Skeleton Screens
 * https://material.io/design/communication/launch-screen.html#skeleton-screen
 */
export default {
  title: 'Components/Skeleton',
  component: Skeleton,
  tags: ['autodocs'],
  argTypes: {
    variant: {
      control: 'select',
      options: ['text', 'rect', 'circle'],
      description: 'Variante de skeleton',
    },
    width: {
      control: 'text',
      description: 'Ancho (px, %, etc)',
    },
    height: {
      control: 'text',
      description: 'Alto (px, %, etc)',
    },
    count: {
      control: 'number',
      description: 'Cantidad de elementos',
    },
    circle: {
      control: 'boolean',
      description: 'Forma circular',
    },
  },
}

export const Text = {
  args: {
    variant: 'text',
    width: '200px',
  },
}

export const Rectangle = {
  args: {
    variant: 'rect',
    width: '200px',
    height: '120px',
  },
}

export const Circle = {
  args: {
    variant: 'circle',
    width: '60px',
    height: '60px',
  },
}

export const Multiple = {
  args: {
    variant: 'text',
    count: 3,
    width: '80%',
  },
}

export const Card = {
  render: () => (
    <div style={{ maxWidth: '300px' }}>
      <SkeletonCard lines={3} hasImage={true} />
    </div>
  ),
}

export const Table = {
  render: () => (
    <SkeletonTable rows={5} columns={4} />
  ),
}

export const Profile = {
  render: () => (
    <SkeletonProfile />
  ),
}
