import { describe, it, expect } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { usePagination, useSearch, useSort, useDataTable } from '../hooks/usePagination'

describe('usePagination', () => {
  const items = Array.from({ length: 25 }, (_, i) => ({ id: i, name: `Item ${i}` }))

  it('should initialize with correct defaults', () => {
    const { result } = renderHook(() => usePagination(items, 10))

    expect(result.current.currentPage).toBe(1)
    expect(result.current.totalPages).toBe(3)
    expect(result.current.totalItems).toBe(25)
    expect(result.current.currentItems).toHaveLength(10)
    expect(result.current.hasNextPage).toBe(true)
    expect(result.current.hasPrevPage).toBe(false)
  })

  it('should go to next page', () => {
    const { result } = renderHook(() => usePagination(items, 10))

    act(() => {
      result.current.nextPage()
    })

    expect(result.current.currentPage).toBe(2)
    expect(result.current.hasPrevPage).toBe(true)
    expect(result.current.currentItems[0].id).toBe(10)
  })

  it('should go to previous page', () => {
    const { result } = renderHook(() => usePagination(items, 10))

    // Navigate to page 3 (last page)
    act(() => {
      result.current.goToPage(3)
    })
    expect(result.current.currentPage).toBe(3)
    expect(result.current.hasNextPage).toBe(false)

    // Try to go beyond last page — should stay on page 3
    act(() => {
      result.current.nextPage()
    })
    expect(result.current.currentPage).toBe(3)
  })

  it('should not exceed last page', () => {
    const { result } = renderHook(() => usePagination(items, 10))

    act(() => {
      result.current.goToPage(10)
    })

    // goToPage silently ignores out-of-range pages, stays on current page
    expect(result.current.currentPage).toBe(1)
    expect(result.current.hasNextPage).toBe(true)
  })

  it('should not go below page 1', () => {
    const { result } = renderHook(() => usePagination(items, 10))

    act(() => {
      result.current.prevPage()
    })

    expect(result.current.currentPage).toBe(1)
  })

  it('should reset pagination', () => {
    const { result } = renderHook(() => usePagination(items, 10))

    act(() => {
      result.current.nextPage()
    })

    expect(result.current.currentPage).toBe(2)

    act(() => {
      result.current.resetPagination()
    })

    expect(result.current.currentPage).toBe(1)
  })

  it('should handle empty items', () => {
    const { result } = renderHook(() => usePagination([], 10))

    expect(result.current.totalPages).toBe(0)
    expect(result.current.currentItems).toHaveLength(0)
  })
})

describe('useSearch', () => {
  const items = [
    { id: 1, name: 'Alice', role: 'admin' },
    { id: 2, name: 'Bob', role: 'user' },
    { id: 3, name: 'Charlie', role: 'admin' },
  ]

  it('should filter items by search term', () => {
    const { result } = renderHook(() => useSearch(items, ['name']))

    act(() => {
      result.current.setSearchTerm('ali')
    })

    expect(result.current.filteredItems).toHaveLength(1)
    expect(result.current.filteredItems[0].name).toBe('Alice')
    expect(result.current.hasResults).toBe(true)
  })

  it('should return all items when search is empty', () => {
    const { result } = renderHook(() => useSearch(items, ['name']))

    expect(result.current.filteredItems).toHaveLength(3)
  })

  it('should clear search', () => {
    const { result } = renderHook(() => useSearch(items, ['name']))

    act(() => {
      result.current.setSearchTerm('ali')
    })

    act(() => {
      result.current.clearSearch()
    })

    expect(result.current.searchTerm).toBe('')
    expect(result.current.filteredItems).toHaveLength(3)
  })

  it('should handle no results', () => {
    const { result } = renderHook(() => useSearch(items, ['name']))

    act(() => {
      result.current.setSearchTerm('xyz')
    })

    expect(result.current.filteredItems).toHaveLength(0)
    expect(result.current.hasResults).toBe(false)
    expect(result.current.resultCount).toBe(0)
  })
})

describe('useSort', () => {
  const items = [
    { id: 1, name: 'Charlie', score: 30 },
    { id: 2, name: 'Alice', score: 50 },
    { id: 3, name: 'Bob', score: 40 },
  ]

  it('should sort by string field ascending', () => {
    const { result } = renderHook(() => useSort(items, 'name'))

    expect(result.current.sortField).toBe('name')
    expect(result.current.sortDirection).toBe('asc')
    expect(result.current.sortedItems[0].name).toBe('Alice')
    expect(result.current.sortedItems[2].name).toBe('Charlie')
  })

  it('should toggle sort direction', () => {
    const { result } = renderHook(() => useSort(items, 'name'))

    act(() => {
      result.current.toggleSort('name')
    })

    expect(result.current.sortDirection).toBe('desc')
    expect(result.current.sortedItems[0].name).toBe('Charlie')
  })

  it('should change sort field and reset direction', () => {
    const { result } = renderHook(() => useSort(items, 'name', 'desc'))

    act(() => {
      result.current.toggleSort('score')
    })

    expect(result.current.sortField).toBe('score')
    expect(result.current.sortDirection).toBe('asc')
  })

  it('should return correct sort icon', () => {
    const { result } = renderHook(() => useSort(items, 'name'))

    expect(result.current.getSortIcon('name')).toBe('↑')
    expect(result.current.getSortIcon('score')).toBe('⇅')

    act(() => {
      result.current.toggleSort('name')
    })

    expect(result.current.getSortIcon('name')).toBe('↓')
  })

  it('should sort numbers correctly', () => {
    const { result } = renderHook(() => useSort(items, 'score'))

    expect(result.current.sortedItems[0].score).toBe(30)
    expect(result.current.sortedItems[2].score).toBe(50)
  })
})

describe('useDataTable', () => {
  const items = [
    { id: 1, name: 'Charlie', role: 'admin' },
    { id: 2, name: 'Alice', role: 'user' },
    { id: 3, name: 'Bob', role: 'admin' },
    { id: 4, name: 'David', role: 'user' },
    { id: 5, name: 'Eve', role: 'admin' },
  ]

  it('should combine search, sort and pagination', () => {
    const { result } = renderHook(() =>
      useDataTable(items, ['name', 'role'], 'name', 2)
    )

    expect(result.current.displayItems).toHaveLength(2)
    expect(result.current.displayItems[0].name).toBe('Alice')

    act(() => {
      result.current.setSearchTerm('admin')
    })

    expect(result.current.displayItems).toHaveLength(2)
    expect(result.current.resultCount).toBe(3)
  })
})
