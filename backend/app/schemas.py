"""
Conflict Zero - Pydantic Schemas
Validación y serialización de datos
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, EmailStr, constr
from enum import Enum

# ============================================================
# ENUMS
# ============================================================

class PlanTier(str, Enum):
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    FOUNDER = "founder"

class CompanyStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"

class ApplicationStatus(str, Enum):
    PENDING = "pending"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    WAITLISTED = "waitlisted"

class SelloStatus(str, Enum):
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    EXPIRED = "expired"

class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class InviteStatus(str, Enum):
    SENT = "sent"
    OPENED = "opened"
    CLICKED = "clicked"
    REGISTERED = "registered"
    PAID = "paid"
    EXPIRED = "expired"
    CANCELLED = "cancelled"

# ============================================================
# FOUNDER APPLICATION SCHEMAS
# ============================================================

class FounderApplicationCreate(BaseModel):
    """Schema para crear aplicación al Programa Fundador"""
    company_ruc: constr(pattern=r'^[0-9]{11}$') = Field(..., description="RUC de 11 dígitos")
    company_name: str = Field(..., min_length=3, max_length=255)
    contact_name: str = Field(..., min_length=3, max_length=255)
    contact_email: EmailStr
    contact_phone: Optional[str] = Field(None, max_length=50)
    annual_volume: str = Field(..., pattern=r'^(10-50M|50-200M|200M\+)$')
    subcontractor_count: str = Field(..., pattern=r'^(5-20|20-50|50\+)$')
    
    class Config:
        json_schema_extra = {
            "example": {
                "company_ruc": "20100123091",
                "company_name": "Constructora ABC S.A.C.",
                "contact_name": "Juan Pérez",
                "contact_email": "juan.perez@constructora.com",
                "contact_phone": "+51 999 999 999",
                "annual_volume": "50-200M",
                "subcontractor_count": "20-50"
            }
        }

class FounderApplicationResponse(BaseModel):
    """Schema de respuesta para aplicaciones"""
    id: str
    company_ruc: str
    company_name: str
    contact_name: str
    contact_email: str
    annual_volume: str
    subcontractor_count: str
    status: ApplicationStatus
    created_at: datetime
    
    class Config:
        from_attributes = True

class FounderApplicationReview(BaseModel):
    """Schema para revisar una aplicación (admin)"""
    status: ApplicationStatus
    notes: Optional[str] = None

# ============================================================
# COMPANY SCHEMAS
# ============================================================

class CompanyCreate(BaseModel):
    """Crear nueva empresa"""
    ruc: constr(pattern=r'^[0-9]{11}$')
    razon_social: str = Field(..., min_length=3, max_length=255)
    contact_email: EmailStr
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    plan_tier: PlanTier = PlanTier.BRONZE

class CompanyUpdate(BaseModel):
    """Actualizar empresa"""
    razon_social: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    plan_tier: Optional[PlanTier] = None
    status: Optional[CompanyStatus] = None

class CompanyResponse(BaseModel):
    """Respuesta con datos de empresa"""
    ruc: str
    razon_social: str
    plan_tier: PlanTier
    status: CompanyStatus
    is_founder: bool
    max_monthly_queries: int
    used_queries_this_month: int
    contact_email: str
    contact_name: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

class CompanyPublic(BaseModel):
    """Datos públicos de empresa (para perfiles)"""
    ruc: str
    razon_social: str
    plan_tier: PlanTier

# ============================================================
# PUBLIC PROFILE SCHEMAS
# ============================================================

class PublicProfileCreate(BaseModel):
    """Crear perfil público"""
    ruc: str
    display_name: str
    slug: str

class PublicProfileUpdate(BaseModel):
    """Actualizar perfil público"""
    display_name: Optional[str] = None
    sello_status: Optional[SelloStatus] = None
    sello_expires_at: Optional[datetime] = None
    current_score: Optional[int] = Field(None, ge=0, le=100)
    risk_level: Optional[RiskLevel] = None
    current_certificate_url: Optional[str] = None
    is_publicly_visible: Optional[bool] = None

class PublicProfileResponse(BaseModel):
    """Respuesta completa de perfil público"""
    ruc: str
    display_name: str
    slug: str
    sello_status: SelloStatus
    sello_expires_at: Optional[datetime]
    current_score: Optional[int]
    risk_level: Optional[RiskLevel]
    total_verifications: int
    last_verified_at: Optional[datetime]
    current_certificate_url: Optional[str]
    company: CompanyPublic
    
    class Config:
        from_attributes = True

class PublicProfileMinimal(BaseModel):
    """Versión mínima para mostrar públicamente (sin auth)"""
    ruc: str
    display_name: str
    sello_status: SelloStatus
    sello_expires_at: Optional[datetime]
    current_score: Optional[int]
    risk_level: Optional[RiskLevel]
    total_verifications: int
    last_verified_at: Optional[datetime]

# ============================================================
# INVITE SCHEMAS
# ============================================================

class InviteCreate(BaseModel):
    """Crear invitación"""
    invitee_email: EmailStr
    invitee_company_name: Optional[str] = None
    invitee_ruc: Optional[constr(pattern=r'^[0-9]{11}$')] = None
    expected_plan: PlanTier = PlanTier.BRONZE
    monthly_value: Optional[float] = None

class InviteCreateBulk(BaseModel):
    """Crear múltiples invitaciones (CSV upload)"""
    invites: List[InviteCreate]

class InviteResponse(BaseModel):
    """Respuesta de invitación"""
    invite_code: str
    inviter_ruc: str
    inviter_company_name: str
    invitee_email: str
    invitee_company_name: Optional[str]
    status: InviteStatus
    depth_level: int
    expected_plan: PlanTier
    monthly_value: Optional[float]
    sent_at: datetime
    expires_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class InviteAccept(BaseModel):
    """Aceptar invitación (registro)"""
    invite_code: str
    company_ruc: constr(pattern=r'^[0-9]{11}$')
    razon_social: str
    contact_email: EmailStr
    contact_name: str
    contact_phone: Optional[str] = None

class NetworkSummary(BaseModel):
    """Resumen de efecto red"""
    ruc: str
    razon_social: str
    plan_tier: PlanTier
    total_invites_sent: int
    invites_converted: int
    monthly_network_value: float
    active_subcontractors: int

# ============================================================
# VERIFICATION SCHEMAS
# ============================================================

class VerificationRequest(BaseModel):
    """Solicitud de verificación"""
    target_ruc: constr(pattern=r'^[0-9]{11}$')

class SunatData(BaseModel):
    """Datos de SUNAT"""
    debt_amount: float = 0
    tax_status: Optional[str] = None
    contributor_status: Optional[str] = None
    address: Optional[str] = None
    department: Optional[str] = None
    province: Optional[str] = None
    district: Optional[str] = None

class SanctionData(BaseModel):
    """Datos de sanción"""
    sanction_id: str
    description: str
    date: Optional[datetime] = None
    status: str
    severity: str
    entity: str

class ScoreBreakdown(BaseModel):
    """Desglose del score"""
    sunat_contribution: float
    osce_contribution: float
    tce_contribution: float
    ml_contribution: float

class VerificationResponse(BaseModel):
    """Respuesta de verificación completa"""
    id: str
    target_ruc: str
    target_company_name: Optional[str]
    score: int
    risk_level: RiskLevel
    sunat_data: SunatData
    osce_sanctions: List[SanctionData]
    tce_sanctions: List[SanctionData]
    score_breakdown: ScoreBreakdown
    certificate_url: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

# ============================================================
# API KEY SCHEMAS
# ============================================================

class ApiKeyCreate(BaseModel):
    """Crear API key"""
    name: str = Field(default="API Key")
    description: Optional[str] = None
    scopes: List[str] = Field(default=["read:verifications", "read:profile"])
    expires_at: Optional[datetime] = None

class ApiKeyResponse(BaseModel):
    """Respuesta con API key (solo se muestra una vez)"""
    id: str
    key: str  # La key completa, solo se muestra al crear
    name: str
    key_prefix: str
    scopes: List[str]
    created_at: datetime
    expires_at: Optional[datetime]

class ApiKeyInfo(BaseModel):
    """Info de API key (sin el secret)"""
    id: str
    name: str
    key_prefix: str
    scopes: List[str]
    usage_count: int
    last_used_at: Optional[datetime]
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

# ============================================================
# WEBHOOK SCHEMAS
# ============================================================

class WebhookCreate(BaseModel):
    """Crear webhook"""
    url: str = Field(..., pattern=r'^https?://')
    events: List[str] = Field(default=["verification.completed"])

class WebhookResponse(BaseModel):
    """Respuesta de webhook"""
    id: str
    url: str
    events: List[str]
    is_active: bool
    success_count: int
    failure_count: int
    last_triggered_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True

# ============================================================
# ERP API SCHEMAS (Para integraciones B2B)
# ============================================================

class ERPVerificationRequest(BaseModel):
    """Request desde ERP (bulk)"""
    rucs: List[constr(pattern=r'^[0-9]{11}$')] = Field(..., max_length=500)
    include_details: bool = True

class ERPVerificationResponse(BaseModel):
    """Respuesta para ERP"""
    ruc: str
    company_name: Optional[str]
    score: int
    risk_level: RiskLevel
    sello_status: Optional[SelloStatus]
    has_sunat_debt: bool
    osce_sanctions_count: int
    tce_sanctions_count: int
    is_verified: bool
    verified_at: Optional[datetime]

class ERPBulkResponse(BaseModel):
    """Respuesta bulk para ERP"""
    results: List[ERPVerificationResponse]
    total_processed: int
    total_risk_high: int
    total_risk_critical: int

# ============================================================
# DASHBOARD SCHEMAS
# ============================================================

class DashboardStats(BaseModel):
    """Stats para dashboard"""
    total_verifications_this_month: int
    remaining_queries: int
    total_queries_limit: int
    network_size: int  # Subcontratistas en red
    invites_sent: int
    invites_converted: int
    monthly_network_value: float

class RecentVerification(BaseModel):
    """Verificación reciente para dashboard"""
    id: str
    target_ruc: str
    target_company_name: Optional[str]
    score: int
    risk_level: RiskLevel
    created_at: datetime

class DashboardResponse(BaseModel):
    """Dashboard completo"""
    company: CompanyResponse
    stats: DashboardStats
    recent_verifications: List[RecentVerification]
    network_summary: Optional[NetworkSummary] = None

# ============================================================
# ERROR SCHEMAS
# ============================================================

class ErrorResponse(BaseModel):
    """Respuesta de error estándar"""
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None

class ValidationErrorResponse(BaseModel):
    """Respuesta de error de validación"""
    error: str
    details: List[Dict[str, Any]]
