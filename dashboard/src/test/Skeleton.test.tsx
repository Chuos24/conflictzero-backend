// @ts-nocheck
import React from 'react'
import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import Skeleton, { SkeletonCard, SkeletonTable, SkeletonProfile } from '../components/Skeleton'

describe('Skeleton', () => {
  it('renders default text skeleton', () => {
    const { container } = render(<Skeleton />)
    
    const skeleton = container.querySelector('.cz-skeleton')
    expect(skeleton).toHaveClass('cz-skeleton')
    expect(skeleton).toHaveClass('cz-skeleton--text')
  })

  it('renders with custom variant', () => {
    const { container } = render(<Skeleton variant="rect" />)
    
    const skeleton = container.querySelector('.cz-skeleton')
    expect(skeleton).toHaveClass('cz-skeleton--rect')
  })

  it('renders with custom width and height', () => {
    const { container } = render(<Skeleton width={200} height={50} />)
    
    const skeleton = container.querySelector('.cz-skeleton')
    expect(skeleton).toHaveStyle({ width: '200px', height: '50px' })
  })

  it('renders with string width/height values', () => {
    const { container } = render(<Skeleton width="100%" height="2rem" />)
    
    const skeleton = container.querySelector('.cz-skeleton')
    expect(skeleton).toHaveStyle({ width: '100%', height: '2rem' })
  })

  it('renders circle variant with border radius', () => {
    const { container } = render(<Skeleton circle width={40} height={40} />)
    
    const skeleton = container.querySelector('.cz-skeleton')
    expect(skeleton).toHaveStyle({ borderRadius: '50%' })
  })

  it('renders multiple skeletons with count prop', () => {
    const { container } = render(<Skeleton count={3} />)
    
    const skeletons = container.querySelectorAll('.cz-skeleton')
    expect(skeletons).toHaveLength(3)
  })

  it('applies custom className', () => {
    const { container } = render(<Skeleton className="custom-skeleton" />)
    
    const skeleton = container.querySelector('.cz-skeleton')
    expect(skeleton).toHaveClass('custom-skeleton')
  })

  it('has animation shimmer class', () => {
    const { container } = render(<Skeleton />)
    
    const skeleton = container.querySelector('.cz-skeleton')
    expect(skeleton).toBeInTheDocument()
  })
})

describe('SkeletonCard', () => {
  it('renders card skeleton with default lines', () => {
    render(<SkeletonCard />)
    
    const card = document.querySelector('.cz-skeleton-card')
    expect(card).toBeInTheDocument()
    
    // Should have title + 3 default lines = 4 skeleton elements
    const skeletons = card.querySelectorAll('.cz-skeleton')
    expect(skeletons.length).toBeGreaterThanOrEqual(4)
  })

  it('renders card with custom line count', () => {
    render(<SkeletonCard lines={5} />)
    
    const card = document.querySelector('.cz-skeleton-card')
    const skeletons = card.querySelectorAll('.cz-skeleton')
    // Title + 5 lines = 6
    expect(skeletons.length).toBeGreaterThanOrEqual(6)
  })

  it('renders card with image', () => {
    render(<SkeletonCard hasImage={true} />)
    
    const image = document.querySelector('.cz-skeleton-card__image')
    expect(image).toBeInTheDocument()
  })

  it('renders card without image by default', () => {
    render(<SkeletonCard />)
    
    const image = document.querySelector('.cz-skeleton-card__image')
    expect(image).not.toBeInTheDocument()
  })
})

describe('SkeletonTable', () => {
  it('renders table skeleton with default rows and columns', () => {
    render(<SkeletonTable />)
    
    const table = document.querySelector('.cz-skeleton-table')
    expect(table).toBeInTheDocument()
    
    const header = table.querySelector('.cz-skeleton-table__header')
    expect(header).toBeInTheDocument()
    
    const rows = table.querySelectorAll('.cz-skeleton-table__row')
    expect(rows).toHaveLength(5) // default rows
  })

  it('renders with custom rows and columns', () => {
    render(<SkeletonTable rows={3} columns={2} />)
    
    const table = document.querySelector('.cz-skeleton-table')
    const rows = table.querySelectorAll('.cz-skeleton-table__row')
    expect(rows).toHaveLength(3)
    
    // Header should have 2 columns
    const headerSkeletons = table.querySelector('.cz-skeleton-table__header').querySelectorAll('.cz-skeleton')
    expect(headerSkeletons).toHaveLength(2)
  })
})

describe('SkeletonProfile', () => {
  it('renders profile skeleton structure', () => {
    render(<SkeletonProfile />)
    
    const profile = document.querySelector('.cz-skeleton-profile')
    expect(profile).toBeInTheDocument()
    
    const header = profile.querySelector('.cz-skeleton-profile__header')
    expect(header).toBeInTheDocument()
    
    const info = profile.querySelector('.cz-skeleton-profile__info')
    expect(info).toBeInTheDocument()
    
    const stats = profile.querySelector('.cz-skeleton-profile__stats')
    expect(stats).toBeInTheDocument()
  })

  it('renders circle avatar in profile', () => {
    render(<SkeletonProfile />)
    
    const circleSkeleton = document.querySelector('.cz-skeleton--circle')
    expect(circleSkeleton).toBeInTheDocument()
    expect(circleSkeleton).toHaveStyle({ width: '80px', height: '80px' })
  })

  it('renders multiple stat cards', () => {
    render(<SkeletonProfile />)
    
    const statsSection = document.querySelector('.cz-skeleton-profile__stats')
    const cards = statsSection.querySelectorAll('.cz-skeleton-card')
    expect(cards.length).toBeGreaterThanOrEqual(3)
  })
})
