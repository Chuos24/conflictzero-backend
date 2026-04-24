/**
 * Conflict Zero - Global TypeScript Types
 * Basado en los schemas del backend (FastAPI/Pydantic)
 */

// ============================================================
// ENUMS
// ============================================================

export type PlanTier = 'bronze' | 'silver' | 'gold' | 'founder';
export type CompanyStatus = 'pending' | 'active' | 'suspended' | 'cancelled';
export type ApplicationStatus = 'pending' | 'under_review' | 'approved' | 'rejected' | 'waitlisted';
export type SelloStatus = 'bronze' | 'silver' | 'gold' | 'expired';
export type RiskLevel = 'low' | 'medium' | 'high' | 'critical';
export type InviteStatus = 'sent' | 'opened' | 'clicked' | 'registered' | 'paid' | 'expired' | 'cancelled';
export type AlertSeverity = 'info' | 'warning' | 'critical';
export type AlertStatus = 'unread' | 'read' | 'resolved';

// ============================================================
// USER / AUTH
// ============================================================

export interface User {
  id: number;
  email: string;
  ruc?: string;
  company_name?: string;
  status: string;
  created_at?: string;
  founder_program: boolean;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface RegisterData {
  ruc: string;
  razon_social: string;
  contact_email: string;
  contact_phone?: string;
  password: string;
}

// ============================================================
// COMPANY
// ============================================================

export interface Company {
  ruc: string;
  razon_social: string;
  plan_tier: PlanTier;
  status: CompanyStatus;
  is_founder: boolean;
  max_monthly_queries: number;
  used_queries_this_month: number;
  contact_email: string;
  contact_name?: string;
  contact_phone?: string;
  created_at: string;
}

export interface CompanyUpdate {
  razon_social?: string;
  contact_email?: string;
  contact_name?: string;
  contact_phone?: string;
  plan_tier?: PlanTier;
  status?: CompanyStatus;
}

export interface CompanyPublic {
  ruc: string;
  razon_social: string;
  plan_tier: PlanTier;
}

// ============================================================
// FOUNDER APPLICATIONS
// ============================================================

export interface FounderApplication {
  id: string;
  company_ruc: string;
  company_name: string;
  contact_name: string;
  contact_email: string;
  annual_volume: string;
  subcontractor_count: string;
  status: ApplicationStatus;
  created_at: string;
}

export interface FounderApplicationCreate {
  company_ruc: string;
  company_name: string;
  contact_name: string;
  contact_email: string;
  contact_phone?: string;
  annual_volume: string;
  subcontractor_count: string;
}

// ============================================================
// PUBLIC PROFILE
// ============================================================

export interface PublicProfile {
  ruc: string;
  display_name: string;
  slug: string;
  sello_status: SelloStatus;
  sello_expires_at?: string;
  current_score?: number;
  risk_level?: RiskLevel;
  total_verifications: number;
  last_verified_at?: string;
  current_certificate_url?: string;
  company: CompanyPublic;
}

// ============================================================
// VERIFICATIONS
// ============================================================

export interface VerificationRequest {
  id: string;
  ruc: string;
  status: string;
  result?: VerificationResult;
  created_at: string;
  completed_at?: string;
}

export interface VerificationResult {
  ruc: string;
  razon_social: string;
  score: number;
  risk_level: RiskLevel;
  sanctions_count: number;
  sanctions_details?: Sanction[];
  representatives?: Representative[];
  legal_address?: string;
  employee_count?: string;
  sunat_status?: string;
  osce_status?: string;
  tce_status?: string;
  observations?: string[];
}

export interface Sanction {
  entity: string;
  resolution: string;
  date: string;
  reason: string;
  duration: string;
  status: string;
}

export interface Representative {
  name: string;
  document: string;
  position: string;
  date_from: string;
}

// ============================================================
// COMPARISON
// ============================================================

export interface Comparison {
  id: string;
  rucs: string[];
  results: VerificationResult[];
  created_at: string;
}

// ============================================================
// INVITES
// ============================================================

export interface Invite {
  id: string;
  email: string;
  company_name: string;
  message?: string;
  status: InviteStatus;
  created_at: string;
  expires_at: string;
}

export interface InviteCreate {
  email: string;
  company_name: string;
  message?: string;
}

export interface InviteStats {
  total_sent: number;
  total_opened: number;
  total_registered: number;
  total_paid: number;
  conversion_rate: number;
}

// ============================================================
// COMPLIANCE
// ============================================================

export interface ComplianceStatus {
  overall_status: string;
  score: number;
  obligations: ComplianceObligation[];
}

export interface ComplianceObligation {
  id: string;
  name: string;
  description: string;
  status: string;
  due_date?: string;
  completed_at?: string;
  is_required: boolean;
}

// ============================================================
// NETWORK (MI RED)
// ============================================================

export interface NetworkSupplier {
  id: string;
  ruc: string;
  razon_social: string;
  risk_level: RiskLevel;
  current_score?: number;
  status: 'active' | 'inactive' | 'watch';
  added_at: string;
  last_checked_at?: string;
  notes?: string;
  tags?: string[];
}

export interface NetworkAlert {
  id: string;
  supplier_id: string;
  supplier_name: string;
  type: 'score_change' | 'new_sanction' | 'status_change' | 'representative_change';
  severity: AlertSeverity;
  message: string;
  details?: Record<string, unknown>;
  status: AlertStatus;
  created_at: string;
}

export interface NetworkStats {
  total_suppliers: number;
  active_count: number;
  watch_count: number;
  inactive_count: number;
  avg_score: number;
  high_risk_count: number;
  unread_alerts: number;
}

// ============================================================
// API KEYS
// ============================================================

export interface ApiKey {
  id: string;
  name: string;
  prefix: string;
  created_at: string;
  last_used_at?: string;
  is_active: boolean;
}

// ============================================================
// WEBHOOKS
// ============================================================

export interface Webhook {
  id: string;
  url: string;
  events: string[];
  is_active: boolean;
  created_at: string;
  secret?: string;
}

// ============================================================
// DASHBOARD / ANALYTICS
// ============================================================

export interface DashboardStats {
  total_verifications: number;
  verifications_this_month: number;
  remaining_queries: number;
  average_score: number;
  risk_distribution: {
    low: number;
    medium: number;
    high: number;
    critical: number;
  };
  recent_verifications: VerificationRequest[];
  monthly_trend: Array<{
    month: string;
    verifications: number;
    avg_score: number;
  }>;
}

// ============================================================
// PAYMENTS
// ============================================================

export interface PaymentOrder {
  id: string;
  amount: number;
  currency: string;
  description: string;
  status: 'pending' | 'completed' | 'failed' | 'refunded';
  created_at: string;
}

export interface CulqiToken {
  id: string;
  type: string;
  email: string;
  card_number?: string;
  card_brand?: string;
}

// ============================================================
// UI / COMPONENT TYPES
// ============================================================

export interface ToastMessage {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  message: string;
  duration?: number;
}

export interface ThemeContextType {
  theme: 'light' | 'dark';
  toggleTheme: () => void;
}

export interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<{ success: boolean; error?: string }>;
  logout: () => void;
  isAuthenticated: boolean;
}

export interface PaginationParams {
  page: number;
  page_size: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

// ============================================================
// UTILITY TYPES
// ============================================================

export type Nullable<T> = T | null;
export type Optional<T> = T | undefined;

export interface StorageValue {
  value: unknown;
  expiry?: number;
}
