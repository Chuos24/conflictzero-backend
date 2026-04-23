import React from 'react'
import { useDataTable } from '../hooks/usePagination'
import { useLocalStorage } from '../hooks/useLocalStorage'
import LoadingSpinner from './LoadingSpinner'
import './DataTable.css'

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
 * 
 * @param {Array} data - Array of objects to display
 * @param {Array} columns - Column definitions
 * @param {string} searchPlaceholder - Placeholder for search input
 * @param {number} itemsPerPage - Items per page
 * @param {boolean} selectable - Enable row selection
 * @param {Function} onRowClick - Callback when row is clicked
 * @param {boolean} loading - Loading state
 * @param {string} emptyMessage - Message when no data
 */
function DataTable({
  data = [],
  columns = [],
  searchPlaceholder = 'Buscar...',
  itemsPerPage = 10,
  selectable = false,
  onRowClick = null,
  loading = false,
  emptyMessage = 'No hay datos disponibles'
}) {
  const searchFields = columns.filter(col => col.searchable).map(col => col.key)
  const defaultSort = columns.find(col => col.defaultSort)?.key || null
  
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
  } = useDataTable(data, searchFields, defaultSort, itemsPerPage)
  
  const [selectedRows, setSelectedRows] = useLocalStorage('datatable-selection', [])
  
  const handleSelectAll = (e) => {
    if (e.target.checked) {
      setSelectedRows(displayItems.map(row => row.id))
    } else {
      setSelectedRows([])
    }
  }
  
  const handleSelectRow = (id) => {
    setSelectedRows(prev => 
      prev.includes(id) 
        ? prev.filter(rowId => rowId !== id)
        : [...prev, id]
    )
  }
  
  const isAllSelected = displayItems.length > 0 && displayItems.every(row => selectedRows.includes(row.id))
  
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
                  key={col.key}
                  className={`datatable__th ${col.sortable ? 'datatable__th--sortable' : ''}`}
                  onClick={() => col.sortable && toggleSort(col.key)}
                  style={{ width: col.width }}
                >
                  {col.title}
                  {col.sortable && (
                    <span className="datatable__sort-icon">
                      {getSortIcon(col.key)}
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
                  key={row.id || index}
                  className={`datatable__row ${onRowClick ? 'datatable__row--clickable' : ''}`}
                  onClick={() => onRowClick && onRowClick(row)}
                >
                  {selectable && (
                    <td className="datatable__td datatable__td--select">
                      <input 
                        type="checkbox"
                        checked={selectedRows.includes(row.id)}
                        onChange={() => handleSelectRow(row.id)}
                        onClick={(e) => e.stopPropagation()}
                      />
                    </td>
                  )}
                  {columns.map(col => (
                    <td key={col.key} className="datatable__td">
                      {col.render 
                        ? col.render(row[col.key], row)
                        : row[col.key] || '—'
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
