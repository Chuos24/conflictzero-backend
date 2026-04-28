// @ts-nocheck
import LoadingSpinner from '../src/components/LoadingSpinner'

/**
 * LoadingSpinner - Indicador de carga
 */
export default {
  title: 'Components/LoadingSpinner',
  component: LoadingSpinner,
  tags: ['autodocs'],
  argTypes: {
    size: {
      control: 'select',
      options: ['small', 'medium', 'large'],
      description: 'Tamaño del spinner',
    },
    text: {
      control: 'text',
      description: 'Texto a mostrar debajo del spinner',
    },
  },
}

export const Default = {
  args: {
    size: 'medium',
    text: 'Cargando...',
  },
}

export const Small = {
  args: {
    size: 'small',
    text: 'Cargando...',
  },
}

export const Large = {
  args: {
    size: 'large',
    text: 'Procesando solicitud...',
  },
}

export const NoText = {
  args: {
    size: 'medium',
    text: '',
  },
}
