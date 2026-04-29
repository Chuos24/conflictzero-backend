import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";
import Monitoring from "../pages/Monitoring";

// Mock de los hooks de monitoreo
vi.mock("../hooks/useQueries", async () => {
  const actual = await vi.importActual("../hooks/useQueries");
  return {
    ...actual,
    useMonitoringStats: vi.fn(),
    useMonitoringAlerts: vi.fn(),
    useMonitoringChanges: vi.fn(),
    useMonitoringRules: vi.fn(),
    useMarkMonitoringAlertRead: vi.fn(),
    useDismissMonitoringAlert: vi.fn(),
  };
});

import {
  useMonitoringStats,
  useMonitoringAlerts,
  useMonitoringChanges,
  useMonitoringRules,
  useMarkMonitoringAlertRead,
  useDismissMonitoringAlert,
} from "../hooks/useQueries";

const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

const renderWithProviders = (ui) => {
  const queryClient = createTestQueryClient();
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>{ui}</MemoryRouter>
    </QueryClientProvider>
  );
};

describe("Monitoring Page", () => {
  const mockMarkRead = vi.fn();
  const mockDismiss = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();

    useMonitoringStats.mockReturnValue({
      data: {
        total_snapshots: 150,
        total_changes: 23,
        total_alerts: 8,
        alerts_unread: 3,
        last_run: "2026-04-28T14:30:00Z",
      },
      isLoading: false,
    });

    useMonitoringAlerts.mockReturnValue({
      data: [
        {
          id: 1,
          title: "Alerta: Score cayó",
          message: "El proveedor X cayó 20 puntos",
          severity: "high",
          status: "unread",
          created_at: "2026-04-28T10:00:00Z",
        },
        {
          id: 2,
          title: "Nueva sanción",
          message: "Sanción detectada en OSCE",
          severity: "critical",
          status: "read",
          created_at: "2026-04-27T08:00:00Z",
        },
      ],
      isLoading: false,
    });

    useMonitoringChanges.mockReturnValue({
      data: [
        {
          id: 1,
          change_type: "risk_score_drop",
          severity: "high",
          description: "Caída de 20 puntos",
          old_value: "80",
          new_value: "60",
          detected_at: "2026-04-28T10:00:00Z",
        },
      ],
      isLoading: false,
    });

    useMonitoringRules.mockReturnValue({
      data: [
        {
          id: 1,
          rule_type: "risk_score_drop",
          threshold: 10,
          is_active: true,
        },
      ],
      isLoading: false,
    });

    useMarkMonitoringAlertRead.mockReturnValue({
      mutate: mockMarkRead,
      isPending: false,
    });

    useDismissMonitoringAlert.mockReturnValue({
      mutate: mockDismiss,
      isPending: false,
    });
  });

  it("renderiza el título de la página", () => {
    renderWithProviders(<Monitoring />);
    expect(screen.getByText(/Monitoreo de Proveedores/i)).toBeInTheDocument();
  });

  it("muestra las stats cards correctamente", () => {
    renderWithProviders(<Monitoring />);
    expect(screen.getByText("150")).toBeInTheDocument(); // snapshots
    expect(screen.getByText("23")).toBeInTheDocument(); // changes
    expect(screen.getByText("8")).toBeInTheDocument(); // alerts
    expect(screen.getByText("3")).toBeInTheDocument(); // unread
  });

  it("renderiza la tabla de alertas", () => {
    renderWithProviders(<Monitoring />);
    expect(screen.getByText("Alerta: Score cayó")).toBeInTheDocument();
    expect(screen.getByText("Nueva sanción")).toBeInTheDocument();
  });

  it("renderiza la tabla de cambios", () => {
    renderWithProviders(<Monitoring />);
    fireEvent.click(screen.getByText(/Cambios/i));
    expect(screen.getByText("Caída de 20 puntos")).toBeInTheDocument();
  });

  it("renderiza las reglas de monitoreo", () => {
    renderWithProviders(<Monitoring />);
    fireEvent.click(screen.getByText(/Reglas/i));
    expect(screen.getByText("risk_score_drop")).toBeInTheDocument();
  });

  it("permite marcar alerta como leída", async () => {
    renderWithProviders(<Monitoring />);
    const markButtons = screen.getAllByRole("button", { name: /Marcar leída/i });
    fireEvent.click(markButtons[0]);
    await waitFor(() => expect(mockMarkRead).toHaveBeenCalledWith(1));
  });

  it("permite descartar alerta", async () => {
    renderWithProviders(<Monitoring />);
    const dismissButtons = screen.getAllByRole("button", { name: /Descartar/i });
    fireEvent.click(dismissButtons[0]);
    await waitFor(() => expect(mockDismiss).toHaveBeenCalledWith(1));
  });

  it("muestra estado de carga en stats", () => {
    useMonitoringStats.mockReturnValue({ data: null, isLoading: true });
    renderWithProviders(<Monitoring />);
    expect(screen.getByText(/Cargando estadísticas/i)).toBeInTheDocument();
  });

  it("muestra mensaje cuando no hay alertas", () => {
    useMonitoringAlerts.mockReturnValue({ data: [], isLoading: false });
    renderWithProviders(<Monitoring />);
    expect(screen.getByText(/No hay alertas/i)).toBeInTheDocument();
  });
});
