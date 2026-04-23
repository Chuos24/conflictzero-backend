import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import Card from '../components/Card'

describe('Card', () => {
  it('renders with title', () => {
    render(<Card title="Test Card">Content</Card>)
    expect(screen.getByText('Test Card')).toBeInTheDocument()
    expect(screen.getByText('Content')).toBeInTheDocument()
  })

  it('renders without title', () => {
    render(<Card>No Title</Card>)
    expect(screen.getByText('No Title')).toBeInTheDocument()
    expect(screen.queryByRole('heading')).not.toBeInTheDocument()
  })

  it('renders with icon', () => {
    const Icon = () => <span data-testid="icon">🔥</span>
    render(<Card title="With Icon" icon={<Icon />}>Content</Card>)
    expect(screen.getByTestId('icon')).toBeInTheDocument()
  })

  it('renders with action', () => {
    render(
      <Card title="With Action" action={<button>Action</button>}>
        Content
      </Card>
    )
    expect(screen.getByText('Action')).toBeInTheDocument()
  })

  it('handles click when clickable', () => {
    const onClick = vi.fn()
    render(
      <Card title="Clickable" clickable onClick={onClick}>
        Click me
      </Card>
    )
    fireEvent.click(screen.getByText('Click me').closest('.cz-card'))
    expect(onClick).toHaveBeenCalled()
  })

  it('applies custom className', () => {
    render(<Card className="custom-card">Custom</Card>)
    expect(screen.getByText('Custom').closest('.cz-card')).toHaveClass('custom-card')
  })

  it('applies hover effect when clickable', () => {
    const onClick = vi.fn()
    render(
      <Card clickable onClick={onClick}>
        Hoverable
      </Card>
    )
    expect(screen.getByText('Hoverable').closest('.cz-card')).toHaveClass('cz-card--clickable')
  })
})
