import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import Badge from '../components/Badge'

describe('Badge', () => {
  it('renders with default variant', () => {
    render(<Badge>Default</Badge>)
    expect(screen.getByText('Default')).toBeInTheDocument()
  })

  it('renders with success variant', () => {
    render(<Badge variant="success">Success</Badge>)
    const badge = screen.getByText('Success')
    expect(badge).toHaveClass('badge--success')
  })

  it('renders with warning variant', () => {
    render(<Badge variant="warning">Warning</Badge>)
    const badge = screen.getByText('Warning')
    expect(badge).toHaveClass('badge--warning')
  })

  it('renders with error variant', () => {
    render(<Badge variant="error">Error</Badge>)
    const badge = screen.getByText('Error')
    expect(badge).toHaveClass('badge--error')
  })

  it('renders with info variant', () => {
    render(<Badge variant="info">Info</Badge>)
    const badge = screen.getByText('Info')
    expect(badge).toHaveClass('badge--info')
  })

  it('renders with pulse animation when pulsing', () => {
    render(<Badge pulse>Pulsing</Badge>)
    const badge = screen.getByText('Pulsing')
    expect(badge).toHaveClass('badge--pulse')
  })

  it('renders with different sizes', () => {
    const { rerender } = render(<Badge size="small">Small</Badge>)
    expect(screen.getByText('Small')).toHaveClass('badge--small')
    
    rerender(<Badge size="medium">Medium</Badge>)
    expect(screen.getByText('Medium')).toHaveClass('badge--medium')
    
    rerender(<Badge size="large">Large</Badge>)
    expect(screen.getByText('Large')).toHaveClass('badge--large')
  })

  it('applies custom className', () => {
    render(<Badge className="custom-class">Custom</Badge>)
    expect(screen.getByText('Custom')).toHaveClass('custom-class')
  })
})