// @ts-nocheck
import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import Card from '../components/Card'

describe('Card', () => {
  it('renders with title', () => {
    render(
      <Card title="Test Title">
        Content
      </Card>
    )
    expect(screen.getByText('Test Title')).toBeInTheDocument()
    expect(screen.getByText('Content')).toBeInTheDocument()
  })

  it('renders without title', () => {
    render(<Card>Just Content</Card>)
    expect(screen.getByText('Just Content')).toBeInTheDocument()
  })

  it('renders with icon', () => {
    render(
      <Card title="With Icon" icon={<span data-testid="icon">★</span>}>
        Content
      </Card>
    )
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
    const { container } = render(
      <Card onClick={onClick}>
        Click me
      </Card>
    )
    const card = container.querySelector('.card--clickable')
    expect(card).toBeInTheDocument()
    fireEvent.click(card)
    expect(onClick).toHaveBeenCalled()
  })

  it('applies custom className', () => {
    const { container } = render(<Card className="custom-card">Custom</Card>)
    const card = container.querySelector('.card')
    expect(card).toHaveClass('custom-card')
  })

  it('applies hover effect when hoverable', () => {
    const { container } = render(
      <Card hoverable>
        Hoverable
      </Card>
    )
    const card = container.querySelector('.card')
    expect(card).toHaveClass('card--hoverable')
  })
})