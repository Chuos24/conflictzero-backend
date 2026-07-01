import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';

import {
  VerificationTrends,
  RiskDistribution,
  SanctionsByEntity,
  ComplianceHistory,
  StatsDashboard,
} from '../components/Charts';

// Mock recharts completely
vi.mock('recharts', () => ({
  LineChart: ({ children }: any) => <div data-testid="line-chart">{children}</div>,
  BarChart: ({ children }: any) => <div data-testid="bar-chart">{children}</div>,
  PieChart: ({ children }: any) => <div data-testid="pie-chart">{children}</div>,
  Line: () => <span>Line</span>,
  Bar: () => <span>Bar</span>,
  Pie: () => <span>Pie</span>,
  Cell: () => <span>Cell</span>,
  XAxis: () => <span>XAxis</span>,
  YAxis: () => <span>YAxis</span>,
  CartesianGrid: () => <span>CartesianGrid</span>,
  Tooltip: () => <span>Tooltip</span>,
  Legend: () => <span>Legend</span>,
  ResponsiveContainer: ({ children }: any) => (
    <div style={{ width: 400, height: 250 }} data-testid="responsive-container">
      {children}
    </div>
  ),
}));

describe('Charts Components', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('VerificationTrends renders with default data', () => {
    render(<VerificationTrends />);
    expect(screen.getByText('Tendencia de Verificaciones')).toBeInTheDocument();
  });

  it('VerificationTrends renders with provided data', () => {
    const data = [
      { date: 'Ene', verifications: 10, comparisons: 2 },
      { date: 'Feb', verifications: 15, comparisons: 3 },
    ];
    render(<VerificationTrends data={data} />);
    expect(screen.getByText('Tendencia de Verificaciones')).toBeInTheDocument();
  });

  it('RiskDistribution renders with default data', () => {
    render(<RiskDistribution />);
    expect(screen.getByText('Distribución de Riesgo')).toBeInTheDocument();
  });

  it('RiskDistribution renders with provided data', () => {
    const data = [
      { name: 'Bajo', value: 10, color: '#22c55e' },
      { name: 'Alto', value: 5, color: '#ef4444' },
    ];
    render(<RiskDistribution data={data} />);
    expect(screen.getByText('Distribución de Riesgo')).toBeInTheDocument();
  });

  it('SanctionsByEntity renders with default data', () => {
    render(<SanctionsByEntity />);
    expect(screen.getByText('Sanciones por Entidad')).toBeInTheDocument();
  });

  it('SanctionsByEntity renders with provided data', () => {
    const data = [
      { entity: 'SUNAT', sanciones: 2 },
      { entity: 'OSCE', sanciones: 5 },
    ];
    render(<SanctionsByEntity data={data} />);
    expect(screen.getByText('Sanciones por Entidad')).toBeInTheDocument();
  });

  it('ComplianceHistory renders with default data', () => {
    render(<ComplianceHistory />);
    expect(screen.getByText('Evolución del Compliance Score')).toBeInTheDocument();
  });

  it('ComplianceHistory renders with provided data', () => {
    const data = [
      { month: 'Ene', score: 72 },
      { month: 'Feb', score: 78 },
    ];
    render(<ComplianceHistory data={data} />);
    expect(screen.getByText('Evolución del Compliance Score')).toBeInTheDocument();
  });

  it('StatsDashboard renders all charts', () => {
    render(<StatsDashboard />);
    expect(screen.getByText('Tendencia de Verificaciones')).toBeInTheDocument();
    expect(screen.getByText('Distribución de Riesgo')).toBeInTheDocument();
    expect(screen.getByText('Sanciones por Entidad')).toBeInTheDocument();
    expect(screen.getByText('Evolución del Compliance Score')).toBeInTheDocument();
  });
});
