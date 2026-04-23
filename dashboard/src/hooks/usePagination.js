import { useState, useCallback } from 'react'

/**
 * Custom hook for pagination
 * @param {Array} items - Array of items to paginate
 * @param {number} itemsPerPage - Number of items per page
 * @returns {Object} - Pagination state and helpers
 */
export function usePagination(items = [], itemsPerPage = 10) {
  const [currentPage, setCurrentPage] = useState(1)
  
  const totalPages = Math.ceil(items.length / itemsPerPage)
  const startIndex = (currentPage - 1) * itemsPerPage
  const endIndex = startIndex + itemsPerPage
  const currentItems = items.slice(startIndex, endIndex)
  
  const goToPage = useCallback((page) => {
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

/**
 * Custom hook for search/filter
 * @param {Array} items - Array of items to search
 * @param {Array} fields - Fields to search in
 * @returns {Object} - Search state and helpers
 */
export function useSearch(items = [], fields = []) {
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

/**
 * Custom hook for sorting
 * @param {Array} items - Array of items to sort
 * @param {string} defaultField - Default sort field
 * @param {string} defaultDirection - Default sort direction (asc/desc)
 * @returns {Object} - Sort state and helpers
 */
export function useSort(items = [], defaultField = null, defaultDirection = 'asc') {
  const [sortField, setSortField] = useState(defaultField)
  const [sortDirection, setSortDirection] = useState(defaultDirection)
  
  const sortedItems = sortField
    ? [...items].sort((a, b) => {
        const aValue = a[sortField]
        const bValue = b[sortField]
        
        if (aValue === null || aValue === undefined) return 1
        if (bValue === null || bValue === undefined) return -1
        
        if (typeof aValue === 'string') {
          return sortDirection === 'asc'
            ? aValue.localeCompare(bValue)
            : bValue.localeCompare(aValue)
        }
        
        return sortDirection === 'asc'
          ? aValue - bValue
          : bValue - aValue
      })
    : items
  
  const toggleSort = useCallback((field) => {
    if (sortField === field) {
      setSortDirection(dir => dir === 'asc' ? 'desc' : 'asc')
    } else {
      setSortField(field)
      setSortDirection('asc')
    }
  }, [sortField])
  
  const getSortIcon = useCallback((field) => {
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

/**
 * Custom hook for combining search, sort, and pagination
 * @param {Array} items - Array of items
 * @param {Array} searchFields - Fields to search in
 * @param {string} sortField - Default sort field
 * @param {number} itemsPerPage - Items per page
 * @returns {Object} - Combined state and helpers
 */
export function useDataTable(items = [], searchFields = [], sortField = null, itemsPerPage = 10) {
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
