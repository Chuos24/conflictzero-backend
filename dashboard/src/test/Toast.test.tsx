import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent, act } from '@testing-library/react'
import Toast from '../components/Toast'

describe('Toast', () => {
  it('renders success toast', () => {
    render(<Toast message="Guardado" type="success" onClose={() => {}} />)
    expect(screen.getByText('Guardado')).toBeInTheDocument()
    expect(screen.getByText('✓')).toBeInTheDocument()
  })

  it('renders error toast', () => {
    render(<Toast message="Error" type="error" onClose={() => {}} />)
    expect(screen.getByText('Error')).toBeInTheDocument()
    expect(screen.getByText('✕')).toBeInTheDocument()
  })

  it('renders warning toast', () => {
    render(<Toast message="Advertencia" type="warning" onClose={() => {}} />)
    expect(screen.getByText('Advertencia')).toBeInTheDocument()
    expect(screen.getByText('⚠')).toBeInTheDocument()
  })

  it('renders info toast', () => {
    render(<Toast message="Info" type="info" onClose={() => {}} />)
    expect(screen.getByText('Info')).toBeInTheDocument()
    expect(screen.getByText('ℹ')).toBeInTheDocument()
  })

  it('calls onClose when clicking close button', async () => {
    const onClose = vi.fn()
    render(<Toast message="Test" type="success" onClose={onClose} />)
    const closeBtn = screen.getByText('×')
    fireEvent.click(closeBtn)
    await act(async () => {
      await new Promise(r => setTimeout(r, 350))
    })
    expect(onClose).toHaveBeenCalled()
  })
})
