import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import Modal from '../components/Modal'

describe('Modal', () => {
  it('renders when open', () => {
    render(
      <Modal isOpen={true} onClose={() => {}} title="Test Modal">
        Modal content
      </Modal>
    )
    expect(screen.getByText('Test Modal')).toBeInTheDocument()
    expect(screen.getByText('Modal content')).toBeInTheDocument()
  })

  it('does not render when closed', () => {
    render(
      <Modal isOpen={false} onClose={() => {}} title="Closed Modal">
        Hidden content
      </Modal>
    )
    expect(screen.queryByText('Closed Modal')).not.toBeInTheDocument()
  })

  it('calls onClose when clicking overlay', () => {
    const onClose = vi.fn()
    render(
      <Modal isOpen={true} onClose={onClose} title="Close Test">
        Content
      </Modal>
    )
    fireEvent.click(screen.getByRole('dialog').closest('.cz-modal__overlay'))
    expect(onClose).toHaveBeenCalled()
  })

  it('does not close when clicking inside content', () => {
    const onClose = vi.fn()
    render(
      <Modal isOpen={true} onClose={onClose} title="No Close">
        <button>Inside</button>
      </Modal>
    )
    fireEvent.click(screen.getByText('Inside'))
    expect(onClose).not.toHaveBeenCalled()
  })

  it('renders with footer', () => {
    render(
      <Modal isOpen={true} onClose={() => {}} title="With Footer" footer={<button>Save</button>}>
        Content
      </Modal>
    )
    expect(screen.getByText('Save')).toBeInTheDocument()
  })

  it('applies size classes', () => {
    const { rerender } = render(
      <Modal isOpen={true} onClose={() => {}} title="Small" size="small">
        Content
      </Modal>
    )
    expect(screen.getByRole('dialog').closest('.cz-modal__content')).toHaveClass('cz-modal__content--small')

    rerender(
      <Modal isOpen={true} onClose={() => {}} title="Large" size="large">
        Content
      </Modal>
    )
    expect(screen.getByRole('dialog').closest('.cz-modal__content')).toHaveClass('cz-modal__content--large')
  })

  it('renders without close button when showCloseButton is false', () => {
    render(
      <Modal isOpen={true} onClose={() => {}} title="No Close Button" showCloseButton={false}>
        Content
      </Modal>
    )
    expect(screen.queryByLabelText('Close modal')).not.toBeInTheDocument()
  })
})
