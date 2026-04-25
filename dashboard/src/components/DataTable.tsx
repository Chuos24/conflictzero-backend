import React from 'react'
import { useDataTable } from '../hooks/usePagination'
import { useLocalStorage } from '../hooks/useLocalStorage'
import LoadingSpinner from './LoadingSpinner'
import './DataTable.css'

export interface DataTableColumn<T = Record<string, unknown>> {
  key: keyof T | string
  title: string
  sortable?: boolean
  searchable?: boolean
  width?: string
  render?: (value: unknown, row: T) => React.ReactNode
}

export interface DataTableProps<T = Record<string, unknown>> {
  data?: T[]
  columns?: DataTableColumn<T>[]
  searchPlaceholder?: string
  itemsPerPage?: number
  selectable?: boolean
  onRowClick?: ((row: T) => void) | null
  loading?: boolean
  emptyMessage?: string
}

/**
 * Reusable DataTable Component
 * 
 * Features:
 * - Search/filter
 * - Sort by column
 * - Pagination
 * - Row selection (optional)
 * - Empty state
 * - Loading state
 */
function DataTable<T extends { id?: string | number } = Record<string, unknown>>({
  data = [],
  columns = [],
  searchPlaceholder = 'Buscar...',
  itemsPerPage = 10,
  selectable = false,
  onRowClick = null,
  loading = false,
  emptyMessage = 'No hay datos disponibles'
}: DataTableProps<T>): JSX.Element {
  const searchFields = columns.filter(col => col.searchable).map(col => col.key as string)
  const defaultSort = columns.find(col => col.defaultSort)?.key as string | null
  
  const {
    searchTerm,
    setSearchTerm,
    clearSearch,
    sortedItems,
    sortField,
    sortDirection,
    toggleSort,
    getSortIcon,
    currentPage,
    totalPages,
    currentItems,
    goToPage,
    nextPage,
    prevPage,
    hasNextPage,
    hasPrevPage,
    totalItems,
    displayItems,
    resultCount
  } = useDataTable(data as Record<string, unknown>[], searchFields, defaultSort, itemsPerPage)
  
  const [selectedRows, setSelectedRows] = useLocalStorage<(string | number)[]>('datatable-selection', [])
  
  const handleSelectAll = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.checked) {
      setSelectedRows(displayItems.map(row => (row as T).id).filter(Boolean))
    } else {
      setSelectedRows([])
    }
  }
  
  const handleSelectRow = (id: string | number) => {
    setSelectedRows(prev => 
      prev.includes(id) 
        ? prev.filter(rowId => rowId !== id)
        : [...prev, id]
    )
  }
  
  const isAllSelected = displayItems.length > 0 && displayItems.every(row => selectedRows.includes((row as T).id))
  
  if (loading) {
    return (
      <div className="datatable__loading">
        <LoadingSpinner />
        <p>Cargando datos...</p>
      </div>
    )
  }
  
  return (
    <div className="datatable">
      {/* Search */}
      <div className="datatable__toolbar">
        <div className="datatable__search">
          <input
            type="text"
            placeholder={searchPlaceholder}
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="datatable__search-input"
          />
          {searchTerm && (
            <button 
              className="datatable__search-clear"
              onClick={clearSearch}
              aria-label="Limpiar búsqueda"
            >
              ×
            </button>
          )}
        </div>
        <div className="datatable__info">
          {resultCount} de {totalItems} resultados
        </div>
      </div>
      
      {/* Table */}
      <div className="datatable__wrapper">
        <table className="datatable__table">
          <thead>
            <tr>
              {selectable && (
                <th className="datatable__th datatable__th--select">
                  <input 
                    type="checkbox" 
                    checked={isAllSelected}
                    onChange={handleSelectAll}
                  />
                </th>
              )}
              {columns.map(col => (
                <th 
                  key={col.key as string}
                  className={`datatable__th ${col.sortable ? 'datatable__th--sortable' : ''}`}
                  onClick={() => col.sortable && toggleSort(col.key as string)}
                  style={{ width: col.width }}
                >
                  {col.title}
                  {col.sortable && (
                    <span className="datatable__sort-icon">
                      {getSortIcon(col.key as string)}
                    </span>
                  )}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {displayItems.length === 0 ? (
              <tr>
                <td 
                  colSpan={columns.length + (selectable ? 1 : 0)}
                  className="datatable__empty"
                >
                  {emptyMessage}
                </td>
              </tr>
            ) : (
              displayItems.map((row, index) => (
                <tr 
                  key={(row as T).id || index}
                  className={`datatable__row ${onRowClick ? 'datatable__row--clickable' : ''}`}
                  onClick={() => onRowClick && onRowClick(row as T)}
                >
                  {selectable && (
                    <td className="datatable__td datatable__td--select">
                      <input 
                        type="checkbox"
                        checked={selectedRows.includes((row as T).id)}
                        onChange={() => handleSelectRow((row as T).id)}
                        onClick={(e) => e.stopPropagation()}
                      />
                    </td>
                  )}
                  {columns.map(col => (
                    <td key={col.key as string} className="datatable__td">
                      {col.render 
                        ? col.render((row as Record<string, unknown>)[col.key as string], row as T)
                        : String((row as Record<string, unknown>)[col.key as string] ?? '—')
                      }
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
      
      {/* Pagination */}
      {totalPages > 1 && (
        <div className="datatable__pagination">
          <button
            className="datatable__page-btn"
            onClick={prevPage}
            disabled={!hasPrevPage}
          >
            ← Anterior
          </button>
          
          <div className="datatable__pages">
            {Array.from({ length: totalPages }, (_, i) => i + 1).map(page => (
              <button
                key={page}
                className={`datatable__page-num ${page === currentPage ? 'datatable__page-num--active' : ''}`}
                onClick={() => goToPage(page)}
              >
                {page}
              </button>
            ))}
          </div>
          
          <button
            className="datatable__page-btn"
            onClick={nextPage}
            disabled={!hasNextPage}
          >
            Siguiente →
          </button>
        </div>
      )}
    </div>
  )
}

export default DataTable
