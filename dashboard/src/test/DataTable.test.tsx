// @ts-nocheck
import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import DataTable from '../components/DataTable'

// Mock hooks
vi.mock('../hooks/usePagination', () => ({
  useDataTable: vi.fn()
}))

vi.mock('../hooks/useLocalStorage', () => ({
  useLocalStorage: vi.fn()
}))

import { useDataTable } from '../hooks/usePagination'
import { useLocalStorage } from '../hooks/useLocalStorage'

describe('DataTable', () => {
  const mockData = [
    { id: 1, name: 'Empresa A', ruc: '201001001', score: 85 },
    { id: 2, name: 'Empresa B', ruc: '202002002', score: 45 },
    { id: 3, name: 'Empresa C', ruc: '203003003', score: 92 }
  ]

  const mockColumns = [
    { key: 'name', title: 'Nombre', sortable: true, searchable: true },
    { key: 'ruc', title: 'RUC', sortable: true },
    { key: 'score', title: 'Score', sortable: true, render: (val) => `${val}/100` }
  ]

  const defaultPagination = {
    searchTerm: '',
    setSearchTerm: vi.fn(),
    clearSearch: vi.fn(),
    sortedItems: mockData,
    sortField: null,
    sortDirection: 'asc',
    toggleSort: vi.fn(),
    getSortIcon: vi.fn(() => '↕'),
    currentPage: 1,
    totalPages: 1,
    currentItems: mockData,
    goToPage: vi.fn(),
    nextPage: vi.fn(),
    prevPage: vi.fn(),
    hasNextPage: false,
    hasPrevPage: false,
    totalItems: 3,
    displayItems: mockData,
    resultCount: 3
  }

  beforeEach(() => {
    vi.clearAllMocks()
    useDataTable.mockReturnValue(defaultPagination)
    useLocalStorage.mockReturnValue([[], vi.fn()])
  })

  it('renders table with correct headers', () => {
    render(<DataTable data={mockData} columns={mockColumns} />)
    
    expect(screen.getByText('Nombre')).toBeInTheDocument()
    expect(screen.getByText('RUC')).toBeInTheDocument()
    expect(screen.getByText('Score')).toBeInTheDocument()
  })

  it('renders table rows with data', () => {
    render(<DataTable data={mockData} columns={mockColumns} />)
    
    expect(screen.getByText('Empresa A')).toBeInTheDocument()
    expect(screen.getByText('Empresa B')).toBeInTheDocument()
    expect(screen.getByText('Empresa C')).toBeInTheDocument()
  })

  it('applies custom render function for columns', () => {
    render(<DataTable data={mockData} columns={mockColumns} />)
    
    expect(screen.getByText('85/100')).toBeInTheDocument()
    expect(screen.getByText('45/100')).toBeInTheDocument()
    expect(screen.getByText('92/100')).toBeInTheDocument()
  })

  it('shows loading state', () => {
    render(<DataTable data={mockData} columns={mockColumns} loading={true} />)
    
    expect(screen.getByText('Cargando datos...')).toBeInTheDocument()
  })

  it('shows empty message when no data', () => {
    useDataTable.mockReturnValue({
      ...defaultPagination,
      displayItems: [],
      sortedItems: [],
      resultCount: 0,
      totalItems: 0
    })
    
    render(<DataTable data={[]} columns={mockColumns} emptyMessage="Sin resultados" />)
    
    expect(screen.getByText('Sin resultados')).toBeInTheDocument()
  })

  it('renders search input with placeholder', () => {
    render(<DataTable data={mockData} columns={mockColumns} searchPlaceholder="Buscar empresas..." />)
    
    expect(screen.getByPlaceholderText('Buscar empresas...')).toBeInTheDocument()
  })

  it('calls setSearchTerm on search input change', () => {
    const setSearchTerm = vi.fn()
    useDataTable.mockReturnValue({
      ...defaultPagination,
      setSearchTerm
    })
    
    render(<DataTable data={mockData} columns={mockColumns} />)
    
    const input = screen.getByPlaceholderText('Buscar...')
    fireEvent.change(input, { target: { value: 'Empresa A' } })
    
    expect(setSearchTerm).toHaveBeenCalledWith('Empresa A')
  })

  it('shows clear search button when searchTerm exists', () => {
    useDataTable.mockReturnValue({
      ...defaultPagination,
      searchTerm: 'test'
    })
    
    render(<DataTable data={mockData} columns={mockColumns} />)
    
    expect(screen.getByLabelText('Limpiar búsqueda')).toBeInTheDocument()
  })

  it('calls clearSearch when clear button clicked', () => {
    const clearSearch = vi.fn()
    useDataTable.mockReturnValue({
      ...defaultPagination,
      searchTerm: 'test',
      clearSearch
    })
    
    render(<DataTable data={mockData} columns={mockColumns} />)
    
    fireEvent.click(screen.getByLabelText('Limpiar búsqueda'))
    expect(clearSearch).toHaveBeenCalled()
  })

  it('shows result count info', () => {
    render(<DataTable data={mockData} columns={mockColumns} />)
    
    expect(screen.getByText('3 de 3 resultados')).toBeInTheDocument()
  })

  it('renders pagination when multiple pages', () => {
    useDataTable.mockReturnValue({
      ...defaultPagination,
      totalPages: 3,
      hasNextPage: true,
      hasPrevPage: false
    })
    
    render(<DataTable data={mockData} columns={mockColumns} />)
    
    expect(screen.getByText('← Anterior')).toBeInTheDocument()
    expect(screen.getByText('Siguiente →')).toBeInTheDocument()
    expect(screen.getByText('1')).toBeInTheDocument()
    expect(screen.getByText('2')).toBeInTheDocument()
    expect(screen.getByText('3')).toBeInTheDocument()
  })

  it('calls goToPage when page number clicked', () => {
    const goToPage = vi.fn()
    useDataTable.mockReturnValue({
      ...defaultPagination,
      totalPages: 3,
      hasNextPage: true,
      goToPage
    })
    
    render(<DataTable data={mockData} columns={mockColumns} />)
    
    fireEvent.click(screen.getByText('2'))
    expect(goToPage).toHaveBeenCalledWith(2)
  })

  it('calls prevPage and nextPage when buttons clicked', () => {
    const prevPage = vi.fn()
    const nextPage = vi.fn()
    useDataTable.mockReturnValue({
      ...defaultPagination,
      totalPages: 3,
      hasNextPage: true,
      hasPrevPage: true,
      prevPage,
      nextPage
    })
    
    render(<DataTable data={mockData} columns={mockColumns} />)
    
    fireEvent.click(screen.getByText('← Anterior'))
    expect(prevPage).toHaveBeenCalled()
    
    fireEvent.click(screen.getByText('Siguiente →'))
    expect(nextPage).toHaveBeenCalled()
  })

  it('disables pagination buttons at boundaries', () => {
    useDataTable.mockReturnValue({
      ...defaultPagination,
      totalPages: 2,
      hasNextPage: false,
      hasPrevPage: false
    })
    
    render(<DataTable data={mockData} columns={mockColumns} />)
    
    expect(screen.getByText('← Anterior')).toBeDisabled()
    expect(screen.getByText('Siguiente →')).toBeDisabled()
  })

  it('renders selectable rows with checkboxes', () => {
    render(<DataTable data={mockData} columns={mockColumns} selectable={true} />)
    
    const checkboxes = screen.getAllByRole('checkbox')
    // Header checkbox + 3 row checkboxes
    expect(checkboxes).toHaveLength(4)
  })

  it('calls onRowClick when row is clicked', () => {
    const onRowClick = vi.fn()
    render(<DataTable data={mockData} columns={mockColumns} onRowClick={onRowClick} />)
    
    const row = screen.getByText('Empresa A').closest('tr')
    fireEvent.click(row)
    
    expect(onRowClick).toHaveBeenCalledWith(mockData[0])
  })

  it('renders sortable column indicators', () => {
    render(<DataTable data={mockData} columns={mockColumns} />)
    
    const sortableHeaders = screen.getAllByText('↕')
    // name, ruc, score are all sortable
    expect(sortableHeaders).toHaveLength(3)
  })

  it('calls toggleSort when sortable header clicked', () => {
    const toggleSort = vi.fn()
    useDataTable.mockReturnValue({
      ...defaultPagination,
      toggleSort
    })
    
    render(<DataTable data={mockData} columns={mockColumns} />)
    
    fireEvent.click(screen.getByText('Nombre'))
    expect(toggleSort).toHaveBeenCalledWith('name')
  })
})
