// @ts-nocheck
import Modal from '../src/components/Modal'
import { useState } from 'react'

/**
 * Modal - Componente de modal reutilizable
 * 
 * Referencia: Atlassian Design System modal dialog
 * https://atlassian.design/components/modal-dialog/
 */
export default {
  title: 'Components/Modal',
  component: Modal,
  tags: ['autodocs'],
  argTypes: {
    isOpen: {
      control: 'boolean',
      description: 'Controla la visibilidad del modal',
    },
    title: {
      control: 'text',
      description: 'Título del modal',
    },
    size: {
      control: 'select',
      options: ['small', 'medium', 'large', 'fullscreen'],
      description: 'Tamaño del modal',
    },
    showCloseButton: {
      control: 'boolean',
      description: 'Mostrar botón de cerrar',
    },
    closeOnOverlay: {
      control: 'boolean',
      description: 'Cerrar al hacer click en overlay',
    },
    closeOnEscape: {
      control: 'boolean',
      description: 'Cerrar con tecla Escape',
    },
  },
}

const ModalWrapper = (args) => {
  const [isOpen, setIsOpen] = useState(false)
  return (
    <div>
      <button onClick={() => setIsOpen(true)}>Abrir modal</button>
      <Modal {...args} isOpen={isOpen} onClose={() => setIsOpen(false)}>
        {args.children}
      </Modal>
    </div>
  )
}

export const Default = {
  render: ModalWrapper,
  args: {
    title: 'Título del modal',
    size: 'medium',
    children: (
      <div>
        <p>Este es el contenido del modal. Puede incluir cualquier elemento React.</p>
        <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit.</p>
      </div>
    ),
    showCloseButton: true,
    closeOnOverlay: true,
    closeOnEscape: true,
  },
}

export const Small = {
  render: ModalWrapper,
  args: {
    title: 'Confirmación',
    size: 'small',
    children: <p>¿Estás seguro de que deseas continuar?</p>,
  },
}

export const Large = {
  render: ModalWrapper,
  args: {
    title: 'Detalle completo',
    size: 'large',
    children: (
      <div>
        <p>Contenido extenso para demostrar el tamaño large del modal.</p>
        <p>Este modal tiene más espacio disponible para mostrar información detallada.</p>
      </div>
    ),
  },
}

export const NoCloseButton = {
  render: ModalWrapper,
  args: {
    title: 'Procesando...',
    size: 'small',
    showCloseButton: false,
    closeOnOverlay: false,
    children: <p>Este modal no se puede cerrar manualmente.</p>,
  },
}
