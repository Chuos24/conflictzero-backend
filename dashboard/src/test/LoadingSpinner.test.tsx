import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import LoadingSpinner from '../components/LoadingSpinner'

describe('LoadingSpinner', () => {
  it('renders with default size and text', () => {
    render(<LoadingSpinner />)
    expect(screen.getByText('Cargando...')).toBeInTheDocument()
    const spinner = document.querySelector('.loading-spinner')
    expect(spinner).toHaveClass('spinner-medium')
  })

  it('renders with small size', () => {
    render(<LoadingSpinner size="small" />)
    const spinner = document.querySelector('.loading-spinner')
    expect(spinner).toHaveClass('spinner-small')
  })

  it('renders with large size', () => {
    render(<LoadingSpinner size="large" />)
    const spinner = document.querySelector('.loading-spinner')
    expect(spinner).toHaveClass('spinner-large')
  })

  it('renders custom text', () => {
    render(<LoadingSpinner text="Procesando..." />)
    expect(screen.getByText('Procesando...')).toBeInTheDocument()
  })

  it('does not render text when empty string', () => {
    render(<LoadingSpinner text="" />)
    expect(screen.queryByText('Cargando...')).not.toBeInTheDocument()
  })
})
