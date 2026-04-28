// @ts-nocheck
import DataTable from '../src/components/DataTable'

/**
 * DataTable - Componente de tabla con búsqueda, ordenamiento y paginación
 * 
 * Referencia: Material Design Data tables
 * https://material.io/components/data-tables
 */
export default {
  title: 'Components/DataTable',
  component: DataTable,
  tags: ['autodocs'],
  argTypes: {
    data: {
      control: 'object',
      description: 'Array de objetos a mostrar',
    },
    columns: {
      control: 'object',
      description: 'Definición de columnas',
    },
    loading: {
      control: 'boolean',
      description: 'Estado de carga',
    },
    selectable: {
      control: 'boolean',
      description: 'Permitir selección de filas',
    },
    itemsPerPage: {
      control: 'number',
      description: 'Items por página',
    },
  },
}

const sampleData = [
  { id: 1, ruc: '20123456789', name: 'Constructora ABC S.A.C.', status: 'Activo', risk: 'Bajo' },
  { id: 2, ruc: '20987654321', name: 'Ingeniería XYZ E.I.R.L.', status: 'Activo', risk: 'Medio' },
  { id: 3, ruc: '20555555555', name: 'Grupo Delta S.A.', status: 'Inactivo', risk: 'Alto' },
  { id: 4, ruc: '20333333333', name: 'Obras Perú S.A.C.', status: 'Activo', risk: 'Bajo' },
  { id: 5, ruc: '20777777777', name: 'Construcciones Sur E.I.R.L.', status: 'Pendiente', risk: 'Medio' },
]

const columns = [
  { key: 'ruc', title: 'RUC', sortable: true, searchable: true },
  { key: 'name', title: 'Razón Social', sortable: true, searchable: true },
  { key: 'status', title: 'Estado', sortable: true, searchable: true },
  { key: 'risk', title: 'Riesgo', sortable: true, searchable: true },
]

export const Default = {
  args: {
    data: sampleData,
    columns,
    itemsPerPage: 3,
    selectable: false,
    loading: false,
    emptyMessage: 'No hay datos disponibles',
  },
}

export const Selectable = {
  args: {
    data: sampleData,
    columns,
    itemsPerPage: 3,
    selectable: true,
    loading: false,
  },
}

export const Loading = {
  args: {
    data: [],
    columns,
    loading: true,
  },
}

export const Empty = {
  args: {
    data: [],
    columns,
    loading: false,
    emptyMessage: 'No se encontraron proveedores en la red',
  },
}

export const WithCustomRender = {
  args: {
    data: sampleData,
    columns: [
      { key: 'ruc', title: 'RUC', sortable: true, searchable: true },
      { key: 'name', title: 'Razón Social', sortable: true, searchable: true },
      { 
        key: 'status', 
        title: 'Estado', 
        sortable: true,
        render: (value) => (
          <span className={`status-badge ${value.toLowerCase()}`}>{value}</span>
        )
      },
      { 
        key: 'risk', 
        title: 'Riesgo', 
        sortable: true,
        render: (value) => (
          <span style={{ 
            color: value === 'Bajo' ? '#22c55e' : value === 'Medio' ? '#f59e0b' : '#ef4444',
            fontWeight: 600 
          }}>
            {value}
          </span>
        )
      },
    ],
    itemsPerPage: 3,
  },
}
