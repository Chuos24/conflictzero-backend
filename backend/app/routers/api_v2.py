"""
Conflict Zero - API Routers
Endpoints para el monopolio B2B
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
import uuid
import secrets
import string
from datetime import datetime, timedelta

from app.models import (
    Company, FounderApplication, PublicProfile, Invite, 
    VerificationRequest, ApiKey, AuditLog
)
from app.schemas import (
    FounderApplicationCreate, FounderApplicationResponse,
    CompanyCreate, CompanyResponse, CompanyUpdate,
    PublicProfileCreate, PublicProfileResponse, PublicProfileMinimal,
    InviteCreate, InviteResponse, InviteCreateBulk, InviteAccept,
    VerificationRequest as VerificationRequestSchema, VerificationResponse,
    ApiKeyCreate, ApiKeyResponse, ApiKeyInfo,
    ERPVerificationRequest, ERPBulkResponse,
    DashboardResponse, DashboardStats, RecentVerification,
    NetworkSummary
)
from app.core.database import get_db
from app.core.security import get_current_company, verify_api_key

router = APIRouter(prefix="/api/v2", tags=["Conflict Zero API v2"])
security = HTTPBearer()

# ============================================================
# FOUNDER APPLICATIONS (Programa Fundador)
# ============================================================

@router.post(
    "/founder-applications",
    response_model=FounderApplicationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Aplicar al Programa Fundador",
    description="Endpoint público para que constructoras apliquen al programa exclusivo"
)
async def create_founder_application(
    application: FounderApplicationCreate,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Crea una nueva aplicación al Programa Fundador.
    
    - Solo 10 cupos disponibles
    - Requiere volumen mínimo de S/ 50M anuales
    - 3 meses de acceso Enterprise gratuito
    """
    # Verificar si ya existe aplicación para este RUC
    existing = db.query(FounderApplication).filter(
        FounderApplication.company_ruc == application.company_ruc
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe una aplicación para este RUC"
        )
    
    # Verificar si ya es cliente
    existing_company = db.query(Company).filter(
        Company.ruc == application.company_ruc
    ).first()
    
    if existing_company and existing_company.plan_tier != "bronze":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Esta empresa ya es cliente activo"
        )
    
    # Verificar cupos disponibles
    approved_count = db.query(FounderApplication).filter(
        FounderApplication.status == "approved"
    ).count()
    
    if approved_count >= 10:
        # Agregar a waitlist
        app_status = "waitlisted"
    else:
        app_status = "pending"
    
    # Crear aplicación
    db_application = FounderApplication(
        company_ruc=application.company_ruc,
        company_name=application.company_name,
        contact_name=application.contact_name,
        contact_email=application.contact_email,
        contact_phone=application.contact_phone,
        annual_volume=application.annual_volume,
        subcontractor_count=application.subcontractor_count,
        status=app_status,
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent")
    )
    
    db.add(db_application)
    db.commit()
    db.refresh(db_application)
    
    # Log de auditoría
    audit_log = AuditLog(
        actor_type="system",
        action="founder_application.created",
        resource_type="founder_application",
        resource_id=str(db_application.id),
        new_values={
            "company_ruc": application.company_ruc,
            "company_name": application.company_name,
            "annual_volume": application.annual_volume
        },
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent")
    )
    db.add(audit_log)
    db.commit()
    
    # TODO: Enviar email de confirmación (background task)
    # background_tasks.add_task(send_founder_confirmation_email, db_application)
    
    return db_application


@router.get(
    "/founder-applications/{application_id}",
    response_model=FounderApplicationResponse,
    summary="Obtener estado de aplicación"
)
async def get_founder_application(
    application_id: str,
    db: Session = Depends(get_db)
):
    """Consulta el estado de una aplicación existente"""
    application = db.query(FounderApplication).filter(
        FounderApplication.id == application_id
    ).first()
    
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aplicación no encontrada"
        )
    
    return application


# ============================================================
# PUBLIC PROFILES (Lock-in de vergüenza)
# ============================================================

@router.get(
    "/public/verify/{slug}",
    response_model=PublicProfileMinimal,
    summary="Verificar Sello públicamente",
    description="Endpoint público sin autenticación para verificar el estado de un Sello"
)
async def verify_public_profile(
    slug: str,
    db: Session = Depends(get_db)
):
    """
    Verifica el estado público de un Sello CZ.
    
    URL pública: czperu.com/verificar/{slug}
    Muestra: VIGENTE (Bronze/Silver/Gold) o VENCIDO
    """
    profile = db.query(PublicProfile).filter(
        PublicProfile.slug == slug,
        PublicProfile.is_publicly_visible == True
    ).first()
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Perfil no encontrado"
        )
    
    # Verificar si el sello expiró
    if profile.sello_expires_at and profile.sello_expires_at < datetime.utcnow():
        profile.sello_status = "expired"
        db.commit()
    
    return profile


@router.get(
    "/public/verify-by-ruc/{ruc}",
    response_model=PublicProfileMinimal,
    summary="Verificar Sello por RUC"
)
async def verify_public_profile_by_ruc(
    ruc: str,
    db: Session = Depends(get_db)
):
    """Busca perfil público por RUC (redirección a slug)"""
    profile = db.query(PublicProfile).filter(
        PublicProfile.ruc == ruc,
        PublicProfile.is_publicly_visible == True
    ).first()
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Empresa no verificada o no tiene Sello CZ"
        )
    
    return profile


# ============================================================
# COMPANIES (Admin)
# ============================================================

@router.post(
    "/companies",
    response_model=CompanyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear empresa (Admin)"
)
async def create_company(
    company: CompanyCreate,
    db: Session = Depends(get_db)
):
    """Crea una nueva empresa en el sistema (uso interno/admin)"""
    
    # Verificar si ya existe
    existing = db.query(Company).filter(Company.ruc == company.ruc).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empresa ya existe"
        )
    
    db_company = Company(
        ruc=company.ruc,
        razon_social=company.razon_social,
        contact_email=company.contact_email,
        contact_name=company.contact_name,
        contact_phone=company.contact_phone,
        plan_tier=company.plan_tier.value,
        status="active"
    )
    
    db.add(db_company)
    db.commit()
    db.refresh(db_company)
    
    return db_company


@router.get(
    "/companies/me",
    response_model=CompanyResponse,
    summary="Obtener mi empresa"
)
async def get_my_company(
    current_company: Company = Depends(get_current_company)
):
    """Obtiene los datos de la empresa autenticada"""
    return current_company


@router.patch(
    "/companies/me",
    response_model=CompanyResponse,
    summary="Actualizar mi empresa"
)
async def update_my_company(
    update: CompanyUpdate,
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db)
):
    """Actualiza datos de la empresa"""
    
    if update.razon_social:
        current_company.razon_social = update.razon_social
    if update.contact_email:
        current_company.contact_email = update.contact_email
    if update.contact_name:
        current_company.contact_name = update.contact_name
    if update.contact_phone:
        current_company.contact_phone = update.contact_phone
    
    db.commit()
    db.refresh(current_company)
    
    return current_company


# ============================================================
# INVITES (Efecto Red)
# ============================================================

def generate_invite_code() -> str:
    """Genera código de invitación único"""
    return ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))


@router.post(
    "/invites",
    response_model=InviteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear invitación"
)
async def create_invite(
    invite: InviteCreate,
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db)
):
    """
    Crea una invitación para un subcontratista.
    Solo disponible para planes Gold y Founder.
    """
    # Verificar plan
    if current_company.plan_tier not in ["gold", "founder"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo planes Gold y Founder pueden invitar subcontratistas"
        )
    
    # Generar código único
    code = generate_invite_code()
    while db.query(Invite).filter(Invite.invite_code == code).first():
        code = generate_invite_code()
    
    db_invite = Invite(
        invite_code=code,
        inviter_ruc=current_company.ruc,
        inviter_company_name=current_company.razon_social,
        invitee_email=invite.invitee_email,
        invitee_company_name=invite.invitee_company_name,
        invitee_ruc=invite.invitee_ruc,
        expected_plan=invite.expected_plan.value,
        monthly_value=invite.monthly_value,
        expires_at=datetime.utcnow() + timedelta(days=30)
    )
    
    db.add(db_invite)
    db.commit()
    db.refresh(db_invite)
    
    # TODO: Enviar email de invitación
    
    return db_invite


@router.post(
    "/invites/bulk",
    response_model=List[InviteResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Crear invitaciones masivas (CSV)"
)
async def create_invites_bulk(
    bulk: InviteCreateBulk,
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db)
):
    """Crea múltiples invitaciones desde CSV"""
    
    if current_company.plan_tier not in ["gold", "founder"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo planes Gold y Founder pueden invitar subcontratistas"
        )
    
    created_invites = []
    
    for invite_data in bulk.invites:
        code = generate_invite_code()
        while db.query(Invite).filter(Invite.invite_code == code).first():
            code = generate_invite_code()
        
        db_invite = Invite(
            invite_code=code,
            inviter_ruc=current_company.ruc,
            inviter_company_name=current_company.razon_social,
            invitee_email=invite_data.invitee_email,
            invitee_company_name=invite_data.invitee_company_name,
            invitee_ruc=invite_data.invitee_ruc,
            expected_plan=invite_data.expected_plan.value,
            monthly_value=invite_data.monthly_value,
            expires_at=datetime.utcnow() + timedelta(days=30)
        )
        
        db.add(db_invite)
        created_invites.append(db_invite)
    
    db.commit()
    
    for invite in created_invites:
        db.refresh(invite)
    
    return created_invites


@router.get(
    "/invites",
    response_model=List[InviteResponse],
    summary="Listar mis invitaciones"
)
async def list_my_invites(
    status: Optional[str] = None,
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db)
):
    """Lista todas las invitaciones enviadas por la empresa"""
    query = db.query(Invite).filter(Invite.inviter_ruc == current_company.ruc)
    
    if status:
        query = query.filter(Invite.status == status)
    
    invites = query.order_by(Invite.created_at.desc()).all()
    return invites


@router.get(
    "/invites/{invite_code}",
    response_model=InviteResponse,
    summary="Obtener detalle de invitación"
)
async def get_invite(
    invite_code: str,
    db: Session = Depends(get_db)
):
    """Obtiene detalles de una invitación (para aceptar)"""
    invite = db.query(Invite).filter(Invite.invite_code == invite_code).first()
    
    if not invite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitación no encontrada"
        )
    
    # Verificar expiración
    if invite.expires_at and invite.expires_at < datetime.utcnow():
        invite.status = "expired"
        db.commit()
    
    return invite


# ============================================================
# NETWORK (Efecto Red - Dashboard)
# ============================================================

@router.get(
    "/network/summary",
    response_model=NetworkSummary,
    summary="Resumen de red (Efecto Red)"
)
async def get_network_summary(
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db)
):
    """
    Obtiene el resumen del efecto red:
    - Cuántos invites enviados
    - Cuántos convertidos
    - Valor mensual generado
    """
    
    total_invites = db.query(Invite).filter(
        Invite.inviter_ruc == current_company.ruc
    ).count()
    
    converted_invites = db.query(Invite).filter(
        Invite.inviter_ruc == current_company.ruc,
        Invite.status == "paid"
    ).count()
    
    monthly_value = db.query(func.sum(Invite.monthly_value)).filter(
        Invite.inviter_ruc == current_company.ruc,
        Invite.status == "paid"
    ).scalar() or 0
    
    from app.models import CompanyHierarchy
    active_subcontractors = db.query(CompanyHierarchy).filter(
        CompanyHierarchy.parent_ruc == current_company.ruc,
        CompanyHierarchy.is_active == True
    ).count()
    
    return NetworkSummary(
        ruc=current_company.ruc,
        razon_social=current_company.razon_social,
        plan_tier=current_company.plan_tier,
        total_invites_sent=total_invites,
        invites_converted=converted_invites,
        monthly_network_value=monthly_value,
        active_subcontractors=active_subcontractors
    )


# ============================================================
# DASHBOARD
# ============================================================

@router.get(
    "/dashboard",
    response_model=DashboardResponse,
    summary="Dashboard completo"
)
async def get_dashboard(
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db)
):
    """Obtiene todos los datos del dashboard"""
    
    # Stats
    verifications_count = db.query(VerificationRequest).filter(
        VerificationRequest.consultant_ruc == current_company.ruc,
        VerificationRequest.created_at >= datetime.utcnow().replace(day=1)
    ).count()
    
    remaining = current_company.max_monthly_queries - current_company.used_queries_this_month
    
    from app.models import CompanyHierarchy
    network_size = db.query(CompanyHierarchy).filter(
        CompanyHierarchy.parent_ruc == current_company.ruc,
        CompanyHierarchy.is_active == True
    ).count()
    
    invites_stats = db.query(
        func.count(Invite.invite_code).label('total'),
        func.count(func.case([(Invite.status == 'paid', 1)])).label('converted')
    ).filter(Invite.inviter_ruc == current_company.ruc).first()
    
    monthly_value = db.query(func.sum(Invite.monthly_value)).filter(
        Invite.inviter_ruc == current_company.ruc,
        Invite.status == 'paid'
    ).scalar() or 0
    
    stats = DashboardStats(
        total_verifications_this_month=verifications_count,
        remaining_queries=remaining,
        total_queries_limit=current_company.max_monthly_queries,
        network_size=network_size,
        invites_sent=invites_stats.total or 0,
        invites_converted=invites_stats.converted or 0,
        monthly_network_value=monthly_value
    )
    
    # Recent verifications
    recent = db.query(VerificationRequest).filter(
        VerificationRequest.consultant_ruc == current_company.ruc
    ).order_by(VerificationRequest.created_at.desc()).limit(5).all()
    
    recent_list = [
        RecentVerification(
            id=str(v.id),
            target_ruc=v.target_ruc,
            target_company_name=v.target_company_name,
            score=v.score,
            risk_level=v.risk_level,
            created_at=v.created_at
        )
        for v in recent
    ]
    
    return DashboardResponse(
        company=current_company,
        stats=stats,
        recent_verifications=recent_list
    )


# ============================================================
# ERP API (Para integraciones B2B)
# ============================================================

@router.post(
    "/erp/verify-bulk",
    response_model=ERPBulkResponse,
    summary="Verificación masiva para ERP"
)
async def erp_verify_bulk(
    request: ERPVerificationRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    Endpoint diseñado para integración ERP (SAP, Oracle).
    Permite verificar hasta 500 RUCs en una sola llamada.
    
    Requiere API Key con scope 'read:verifications'
    """
    # Verificar API key
    company = verify_api_key(credentials.credentials, db)
    
    if not company or company.plan_tier not in ["gold", "founder"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Requiere plan Gold o Founder"
        )
    
    # Verificar rate limit
    # TODO: Implementar rate limiting real
    
    results = []
    high_risk = 0
    critical_risk = 0
    
    for ruc in request.rucs:
        # Buscar en caché o consultar
        # TODO: Implementar lógica de verificación real
        
        # Simular resultado
        result = {
            "ruc": ruc,
            "company_name": f"Empresa {ruc}",
            "score": 75,
            "risk_level": "medium",
            "sello_status": None,
            "has_sunat_debt": False,
            "osce_sanctions_count": 0,
            "tce_sanctions_count": 0,
            "is_verified": False,
            "verified_at": None
        }
        
        results.append(result)
        
        if result["risk_level"] == "high":
            high_risk += 1
        elif result["risk_level"] == "critical":
            critical_risk += 1
    
    return ERPBulkResponse(
        results=results,
        total_processed=len(results),
        total_risk_high=high_risk,
        total_risk_critical=critical_risk
    )
