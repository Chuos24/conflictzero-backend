"""
Conflict Zero - API v2 Routes (General)
Endpoints misceláneos de la API v2
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import Optional, List
from datetime import datetime, timedelta

from app.core.database import get_db
from app.core.security import get_current_company
from app.models_v2 import Company, PublicProfile, VerificationRequest, Invite, AuditLog

router = APIRouter(tags=["API v2"])


@router.get("/companies/verify/{ruc}", summary="Verificar RUC públicamente")
async def verify_ruc_public(
    ruc: str,
    db: Session = Depends(get_db)
):
    """Verificación pública de un RUC (para la página de verificación)"""
    import hashlib
    ruc_hash = hashlib.sha256(ruc.encode()).hexdigest()
    
    # Buscar en companies
    company = db.query(Company).filter(
        Company.ruc_hash == ruc_hash,
        Company.deleted_at.is_(None)
    ).first()
    
    if not company:
        return {
            "found": False,
            "message": "RUC no encontrado en nuestro registro"
        }
    
    # Obtener perfil público
    profile = db.query(PublicProfile).filter(
        PublicProfile.company_id == company.id
    ).first()
    
    # Obtener última verificación
    last_verification = db.query(VerificationRequest).filter(
        VerificationRequest.target_ruc_hash == ruc_hash
    ).order_by(VerificationRequest.created_at.desc()).first()
    
    return {
        "found": True,
        "company": {
            "public_slug": company.public_slug,
            "razon_social": company.razon_social,
            "plan_tier": company.plan_tier,
            "status": company.status
        },
        "profile": {
            "sello_status": profile.sello_status if profile else None,
            "sello_expires_at": profile.sello_expires_at.isoformat() if profile and profile.sello_expires_at else None,
            "visual_state": profile.visual_state if profile else None,
            "current_score": profile.current_score if profile else None,
            "risk_level": profile.risk_level if profile else None,
            "total_verifications": profile.total_verifications if profile else 0
        } if profile else None,
        "last_verification": {
            "score": last_verification.score,
            "risk_level": last_verification.risk_level,
            "sunat_debt": last_verification.sunat_debt,
            "osce_sanctions_count": last_verification.osce_sanctions_count,
            "tce_sanctions_count": last_verification.tce_sanctions_count,
            "created_at": last_verification.created_at.isoformat()
        } if last_verification else None
    }


@router.get("/public-profile/{slug}", summary="Perfil público por slug")
async def get_public_profile(
    slug: str,
    db: Session = Depends(get_db)
):
    """Obtener perfil público de una empresa por su slug"""
    profile = db.query(PublicProfile).filter(
        PublicProfile.slug == slug,
        PublicProfile.is_publicly_visible == True
    ).first()
    
    if not profile:
        raise HTTPException(status_code=404, detail="Perfil no encontrado")
    
    company = db.query(Company).filter(Company.id == profile.company_id).first()
    
    return {
        "slug": profile.slug,
        "display_name": profile.display_name,
        "sello_status": profile.sello_status,
        "sello_expires_at": profile.sello_expires_at.isoformat() if profile.sello_expires_at else None,
        "visual_state": profile.visual_state,
        "current_score": profile.current_score,
        "risk_level": profile.risk_level,
        "total_verifications": profile.total_verifications,
        "last_verified_at": profile.last_verified_at.isoformat() if profile.last_verified_at else None,
        "company": {
            "razon_social": company.razon_social if company else None
        }
    }


# ============================================================
# DASHBOARD ENDPOINTS
# ============================================================

@router.get("/dashboard/stats", summary="Estadísticas del dashboard")
async def get_dashboard_stats(
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db)
):
    """
    Retorna estadísticas para el dashboard principal.
    """
    # Verificaciones del usuario
    verifications_count = db.query(func.count(VerificationRequest.id)).filter(
        VerificationRequest.consultant_id == current_company.id,
        VerificationRequest.deleted_at.is_(None)
    ).scalar()

    # Comparaciones (simulado - en producción sería una tabla separada)
    comparisons_count = db.query(func.count(VerificationRequest.id)).filter(
        VerificationRequest.consultant_id == current_company.id,
        VerificationRequest.is_cached == False,
        VerificationRequest.deleted_at.is_(None)
    ).scalar()

    # Invitaciones
    invites_stats = db.query(
        func.count(Invite.id).label('total'),
        func.count(func.case([(Invite.status == 'paid', 1)])).label('paid')
    ).filter(
        Invite.inviter_id == current_company.id,
        Invite.deleted_at.is_(None)
    ).first()

    # Última verificación
    last_verification = db.query(VerificationRequest).filter(
        VerificationRequest.consultant_id == current_company.id,
        VerificationRequest.deleted_at.is_(None)
    ).order_by(desc(VerificationRequest.created_at)).first()

    # Score promedio
    avg_score = db.query(func.avg(VerificationRequest.score)).filter(
        VerificationRequest.consultant_id == current_company.id,
        VerificationRequest.deleted_at.is_(None)
    ).scalar()

    return {
        "verifications_count": verifications_count or 0,
        "comparisons_count": comparisons_count or 0,
        "invites_sent": invites_stats.total or 0,
        "invites_accepted": invites_stats.paid or 0,
        "last_verification": {
            "id": str(last_verification.id) if last_verification else None,
            "score": last_verification.score if last_verification else None,
            "risk_level": last_verification.risk_level if last_verification else None,
            "target_company_name": last_verification.target_company_name if last_verification else None,
            "created_at": last_verification.created_at.isoformat() if last_verification else None
        },
        "average_score": round(float(avg_score), 1) if avg_score else None,
        "plan": {
            "tier": current_company.plan_tier,
            "is_founder": current_company.is_founder,
            "queries_used": current_company.used_queries_this_month,
            "queries_limit": current_company.max_monthly_queries
        }
    }


@router.get("/dashboard/activity", summary="Actividad reciente del dashboard")
async def get_dashboard_activity(
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db),
    limit: int = 10
):
    """
    Retorna actividad reciente para el dashboard.
    Combina verificaciones, invitaciones y auditoría.
    """
    activities = []

    # Verificaciones recientes
    verifications = db.query(VerificationRequest).filter(
        VerificationRequest.consultant_id == current_company.id,
        VerificationRequest.deleted_at.is_(None)
    ).order_by(desc(VerificationRequest.created_at)).limit(limit).all()

    for v in verifications:
        activities.append({
            "id": str(v.id),
            "type": "verification",
            "title": f"Verificación: {v.target_company_name or 'Empresa desconocida'}",
            "description": f"Score: {v.score}/100 - Riesgo: {v.risk_level}",
            "timestamp": v.created_at.isoformat() if v.created_at else None,
            "meta": {
                "score": v.score,
                "risk_level": v.risk_level,
                "ruc": v.target_ruc_hash[:16] + "..." if v.target_ruc_hash else None
            }
        })

    # Invitaciones recientes
    invites = db.query(Invite).filter(
        Invite.inviter_id == current_company.id,
        Invite.deleted_at.is_(None)
    ).order_by(desc(Invite.created_at)).limit(limit).all()

    for inv in invites:
        activities.append({
            "id": str(inv.id),
            "type": "invite",
            "title": f"Invitación enviada: {inv.invitee_company_name or inv.invitee_email}",
            "description": f"Estado: {inv.status}",
            "timestamp": inv.created_at.isoformat() if inv.created_at else None,
            "meta": {
                "status": inv.status,
                "email": inv.invitee_email
            }
        })

    # Ordenar por timestamp y limitar
    activities.sort(key=lambda x: x["timestamp"] or "", reverse=True)
    activities = activities[:limit]

    return {
        "activities": activities,
        "total_count": len(activities)
    }


@router.get("/dashboard/notifications", summary="Notificaciones del usuario")
async def get_dashboard_notifications(
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db),
    unread_only: bool = False
):
    """
    Retorna notificaciones para el usuario.
    """
    # Simulación de notificaciones - en producción vendrían de una tabla
    notifications = []

    # Notificación de expiración del plan Founder
    if current_company.is_founder and current_company.founder_expires_at:
        dias_restantes = (current_company.founder_expires_at - datetime.utcnow()).days
        if dias_restantes <= 7:
            notifications.append({
                "id": "founder_expiry",
                "type": "warning",
                "title": "Tu beneficio Founder expira pronto",
                "message": f"Te quedan {dias_restantes} días de acceso Founder gratuito.",
                "action_url": "/compliance",
                "action_text": "Ver compliance",
                "created_at": datetime.utcnow().isoformat(),
                "is_read": False
            })

    # Notificación de límite de consultas
    usage_percent = (current_company.used_queries_this_month / current_company.max_monthly_queries) * 100
    if usage_percent >= 80:
        notifications.append({
            "id": "query_limit",
            "type": "info" if usage_percent < 90 else "warning",
            "title": "Estás cerca de tu límite de consultas",
            "message": f"Has usado {usage_percent:.0f}% de tus consultas mensuales.",
            "action_url": "/settings",
            "action_text": "Actualizar plan",
            "created_at": datetime.utcnow().isoformat(),
            "is_read": False
        })

    return {
        "notifications": notifications,
        "unread_count": len([n for n in notifications if not n.get("is_read", True)])
    }
