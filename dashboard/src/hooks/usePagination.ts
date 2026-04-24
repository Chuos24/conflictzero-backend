import { useState, useCallback } from 'react'

export interface UsePaginationReturn<T> {
  currentPage: number
  totalPages: number
  currentItems: T[]
  goToPage: (page: number) => void
  nextPage: () => void
  prevPage: () => void
  resetPagination: () => void
  hasNextPage: boolean
  hasPrevPage: boolean
  totalItems: number
}

export function usePagination<T>(items: T[] = [], itemsPerPage = 10): UsePaginationReturn<T> {
  const [currentPage, setCurrentPage] = useState(1)
  
  const totalPages = Math.ceil(items.length / itemsPerPage)
  const startIndex = (currentPage - 1) * itemsPerPage
  const endIndex = startIndex + itemsPerPage
  const currentItems = items.slice(startIndex, endIndex)
  
  const goToPage = useCallback((page: number) => {
    if (page >= 1 && page <= totalPages) {
      setCurrentPage(page)
    }
  }, [totalPages])
  
  const nextPage = useCallback(() => {
    if (currentPage < totalPages) {
      setCurrentPage(page => page + 1)
    }
  }, [currentPage, totalPages])
  
  const prevPage = useCallback(() => {
    if (currentPage > 1) {
      setCurrentPage(page => page - 1)
    }
  }, [currentPage])
  
  const resetPagination = useCallback(() => {
    setCurrentPage(1)
  }, [])
  
  return {
    currentPage,
    totalPages,
    currentItems,
    goToPage,
    nextPage,
    prevPage,
    resetPagination,
    hasNextPage: currentPage < totalPages,
    hasPrevPage: currentPage > 1,
    totalItems: items.length
  }
}

export interface UseSearchReturn<T> {
  searchTerm: string
  setSearchTerm: (term: string) => void
  filteredItems: T[]
  clearSearch: () => void
  hasResults: boolean
  resultCount: number
}

export function useSearch<T extends Record<string, unknown>>(items: T[] = [], fields: (keyof T)[] = []): UseSearchReturn<T> {
  const [searchTerm, setSearchTerm] = useState('')
  
  const filteredItems = searchTerm
    ? items.filter(item => 
        fields.some(field => {
          const value = item[field]
          if (value === null || value === undefined) return false
          return String(value).toLowerCase().includes(searchTerm.toLowerCase())
        })
      )
    : items
  
  const clearSearch = useCallback(() => {
    setSearchTerm('')
  }, [])
  
  return {
    searchTerm,
    setSearchTerm,
    filteredItems,
    clearSearch,
    hasResults: filteredItems.length > 0,
    resultCount: filteredItems.length
  }
}

export interface UseSortReturn<T> {
  sortField: keyof T | null
  sortDirection: 'asc' | 'desc'
  sortedItems: T[]
  toggleSort: (field: keyof T) => void
  getSortIcon: (field: keyof T) => string
}

export function useSort<T extends Record<string, unknown>>(items: T[] = [], defaultField: keyof T | null = null, defaultDirection: 'asc' | 'desc' = 'asc'): UseSortReturn<T> {
  const [sortField, setSortField] = useState<keyof T | null>(defaultField)
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>(defaultDirection)
  
  const sortedItems = sortField
    ? [...items].sort((a, b) => {
        const aValue = a[sortField]
        const bValue = b[sortField]
        
        if (aValue === null || aValue === undefined) return 1
        if (bValue === null || bValue === undefined) return -1
        
        if (typeof aValue === 'string' && typeof bValue === 'string') {
          return sortDirection === 'asc'
            ? aValue.localeCompare(bValue)
            : bValue.localeCompare(aValue)
        }
        
        const aNum = Number(aValue)
        const bNum = Number(bValue)
        return sortDirection === 'asc'
          ? aNum - bNum
          : bNum - aNum
      })
    : items
  
  const toggleSort = useCallback((field: keyof T) => {
    if (sortField === field) {
      setSortDirection(dir => dir === 'asc' ? 'desc' : 'asc')
    } else {
      setSortField(field)
      setSortDirection('asc')
    }
  }, [sortField])
  
  const getSortIcon = useCallback((field: keyof T): string => {
    if (sortField !== field) return '⇅'
    return sortDirection === 'asc' ? '↑' : '↓'
  }, [sortField, sortDirection])
  
  return {
    sortField,
    sortDirection,
    sortedItems,
    toggleSort,
    getSortIcon
  }
}

export interface UseDataTableReturn<T> extends UseSearchReturn<T>, UseSortReturn<T>, UsePaginationReturn<T> {
  displayItems: T[]
}

export function useDataTable<T extends Record<string, unknown>>(
  items: T[] = [],
  searchFields: (keyof T)[] = [],
  sortField: keyof T | null = null,
  itemsPerPage = 10
): UseDataTableReturn<T> {
  const search = useSearch(items, searchFields)
  const sort = useSort(search.filteredItems, sortField)
  const pagination = usePagination(sort.sortedItems, itemsPerPage)
  
  return {
    ...search,
    ...sort,
    ...pagination,
    displayItems: pagination.currentItems
  }
}
