"""
Conflict Zero - Invite Router
Sistema de invitaciones para efecto red
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime, timedelta
import secrets
import string

from app.core.database import get_db
from app.core.security import get_current_company, get_current_founder
from app.models_v2 import Company, Invite, PublicProfile
from app.schemas import InviteCreate, InviteCreateBulk, InviteResponse
from app.services.email_service import get_email_service

router = APIRouter(prefix="/invites", tags=["Invites"])


def generate_invite_code() -> str:
    """Genera código de invitación único: CZ-XXXX-XXXX"""
    code = "CZ-" + "".join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(4)) + "-" + "".join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(4))
    return code


def calculate_depth_level(db: Session, inviter_id: str, parent_invite_id: Optional[str] = None) -> int:
    """
    Calcula el nivel de profundidad en el efecto red.
    
    - Si es invitación directa del Founder (sin parent): depth_level = 1
    - Si es invitación de un subcontratista: depth_level = parent.depth_level + 1
    """
    if parent_invite_id:
        # Buscar la invitación padre
        parent_invite = db.query(Invite).filter(
            Invite.id == parent_invite_id,
            Invite.deleted_at.is_(None)
        ).first()
        
        if parent_invite and parent_invite.depth_level:
            return parent_invite.depth_level + 1
    
    # Verificar si el inviter es un Founder o fue invitado
    inviter = db.query(Company).filter(
        Company.id == inviter_id,
        Company.deleted_at.is_(None)
    ).first()
    
    if inviter:
        # Si el inviter tiene invite_depth > 0, es parte de la red
        if inviter.invite_depth and inviter.invite_depth > 0:
            return inviter.invite_depth + 1
        
        # Si es Founder (is_founder=True), la invitación es nivel 1
        if inviter.is_founder:
            return 1
    
    # Default: nivel 1
    return 1


@router.post("/", response_model=dict, status_code=201)
async def create_invite(
    invite_data: InviteCreate,
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db)
):
    """
    Crea una nueva invitación para un subcontratista.
    """
    # Verificar que la empresa puede invitar (plan gold o founder)
    if current_company.plan_tier not in ["gold", "founder"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo planes Gold y Founder pueden enviar invitaciones"
        )
    
    # Verificar si ya existe invitación para este email
    existing = db.query(Invite).filter(
        Invite.invitee_email == invite_data.invitee_email,
        Invite.inviter_id == current_company.id,
        Invite.deleted_at.is_(None),
        Invite.status.in_(["sent", "opened", "clicked"])
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe una invitación activa para este email"
        )
    
    # Generar hash del RUC si se proporciona
    import hashlib
    ruc_hash = None
    if invite_data.invitee_ruc:
        ruc_hash = hashlib.sha256(invite_data.invitee_ruc.encode()).hexdigest()
    
    # Calcular depth_level basado en parent_invite si existe
    depth_level = calculate_depth_level(
        db=db,
        inviter_id=current_company.id,
        parent_invite_id=invite_data.parent_invite_id if hasattr(invite_data, 'parent_invite_id') else None
    )
    
    # Crear invitación
    invite = Invite(
        invite_code=generate_invite_code(),
        inviter_id=current_company.id,
        inviter_company_name=current_company.razon_social,
        invitee_email=invite_data.invitee_email,
        invitee_company_name=invite_data.invitee_company_name,
        invitee_ruc_hash=ruc_hash,
        expected_plan=invite_data.expected_plan.value if hasattr(invite_data.expected_plan, 'value') else invite_data.expected_plan,
        monthly_value=invite_data.monthly_value,
        depth_level=depth_level,
        status="sent",
        expires_at=datetime.utcnow() + timedelta(days=30)
    )
    
    db.add(invite)
    db.commit()
    db.refresh(invite)
    
    # Enviar email de invitación
    email_service = get_email_service()
    registration_link = f"https://czperu.com/register?invite={invite.invite_code}"
    
    try:
        email_service.send_invite_to_subcontractor(
            to_email=invite_data.invitee_email,
            inviter_company=current_company.razon_social,
            invite_code=invite.invite_code,
            registration_link=registration_link
        )
    except Exception as e:
        print(f"[Invite] Email error (non-blocking): {e}")
    
    return {
        "message": "Invitación enviada exitosamente",
        "invite_code": invite.invite_code,
        "invitee_email": invite.invitee_email,
        "depth_level": depth_level,
        "expires_at": invite.expires_at.isoformat()
    }


@router.post("/bulk", response_model=dict)
async def create_invites_bulk(
    bulk_data: InviteCreateBulk,
    current_company: Company = Depends(get_current_founder),  # Solo founders pueden bulk
    db: Session = Depends(get_db)
):
    """
    Crea múltiples invitaciones (upload CSV).
    Solo disponible para Founders.
    """
    created = []
    failed = []
    
    # Calcular depth_level base para el Founder
    depth_level = calculate_depth_level(db=db, inviter_id=current_company.id)
    
    for invite_data in bulk_data.invites:
        try:
            # Verificar si ya existe
            existing = db.query(Invite).filter(
                Invite.invitee_email == invite_data.invitee_email,
                Invite.inviter_id == current_company.id,
                Invite.deleted_at.is_(None)
            ).first()
            
            if existing:
                failed.append({
                    "email": invite_data.invitee_email,
                    "reason": "Ya existe invitación"
                })
                continue
            
            # Crear invitación
            import hashlib
            ruc_hash = None
            if invite_data.invitee_ruc:
                ruc_hash = hashlib.sha256(invite_data.invitee_ruc.encode()).hexdigest()
            
            invite = Invite(
                invite_code=generate_invite_code(),
                inviter_id=current_company.id,
                inviter_company_name=current_company.razon_social,
                invitee_email=invite_data.invitee_email,
                invitee_company_name=invite_data.invitee_company_name,
                invitee_ruc_hash=ruc_hash,
                expected_plan=invite_data.expected_plan.value if hasattr(invite_data.expected_plan, 'value') else invite_data.expected_plan,
                monthly_value=invite_data.monthly_value,
                depth_level=depth_level,  # Mismo nivel para todas las bulk invites
                status="sent",
                expires_at=datetime.utcnow() + timedelta(days=30)
            )
            
            db.add(invite)
            created.append(invite)
            
        except Exception as e:
            failed.append({
                "email": invite_data.invitee_email,
                "reason": str(e)
            })
    
    db.commit()
    
    # Enviar emails
    email_service = get_email_service()
    for invite in created:
        try:
            registration_link = f"https://czperu.com/register?invite={invite.invite_code}"
            email_service.send_invite_to_subcontractor(
                to_email=invite.invitee_email,
                inviter_company=current_company.razon_social,
                invite_code=invite.invite_code,
                registration_link=registration_link
            )
        except Exception as e:
            print(f"[Invite] Email error for {invite.invitee_email}: {e}")
    
    return {
        "created": len(created),
        "failed": len(failed),
        "failed_details": failed,
        "depth_level": depth_level,
        "invite_codes": [i.invite_code for i in created]
    }


@router.get("/", response_model=dict)
async def list_invites(
    status: Optional[str] = None,
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db)
):
    """
    Lista todas las invitaciones enviadas por la empresa.
    """
    query = db.query(Invite).filter(
        Invite.inviter_id == current_company.id,
        Invite.deleted_at.is_(None)
    )
    
    if status:
        query = query.filter(Invite.status == status)
    
    invites = query.order_by(Invite.created_at.desc()).all()
    
    return {
        "total": len(invites),
        "invites": [
            {
                "id": str(inv.id),
                "invite_code": inv.invite_code,
                "invitee_email": inv.invitee_email,
                "invitee_company_name": inv.invitee_company_name,
                "status": inv.status,
                "expected_plan": inv.expected_plan,
                "monthly_value": float(inv.monthly_value) if inv.monthly_value else None,
                "depth_level": inv.depth_level,
                "sent_at": inv.sent_at.isoformat() if inv.sent_at else None,
                "opened_at": inv.opened_at.isoformat() if inv.opened_at else None,
                "registered_at": inv.registered_at.isoformat() if inv.registered_at else None,
                "converted_to_paid_at": inv.converted_to_paid_at.isoformat() if inv.converted_to_paid_at else None,
                "expires_at": inv.expires_at.isoformat() if inv.expires_at else None,
                "enforcement_emails_sent": inv.enforcement_emails_sent
            }
            for inv in invites
        ]
    }


@router.get("/stats", response_model=dict)
async def get_invite_stats(
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db)
):
    """
    Estadísticas de invitaciones (para dashboard).
    """
    stats = db.query(
        func.count(Invite.id).label('total'),
        func.count(func.case([(Invite.status == 'paid', 1)])).label('paid'),
        func.count(func.case([(Invite.status == 'registered', 1)])).label('registered'),
        func.count(func.case([(Invite.status.in_(['sent', 'opened', 'clicked']), 1)])).label('pending'),
        func.sum(func.case([(Invite.status == 'paid', Invite.monthly_value)], else_=0)).label('monthly_value')
    ).filter(
        Invite.inviter_id == current_company.id,
        Invite.deleted_at.is_(None)
    ).first()
    
    total = stats.total or 0
    paid = stats.paid or 0
    
    conversion_rate = round((paid / total * 100), 1) if total > 0 else 0
    
    # Calcular depth stats
    depth_stats = db.query(
        Invite.depth_level,
        func.count(Invite.id).label('count')
    ).filter(
        Invite.inviter_id == current_company.id,
        Invite.deleted_at.is_(None)
    ).group_by(Invite.depth_level).all()
    
    return {
        "total_invites": total,
        "paid": paid,
        "registered_not_paid": stats.registered or 0,
        "pending": stats.pending or 0,
        "conversion_rate": conversion_rate,
        "monthly_network_value": float(stats.monthly_value or 0),
        "goal_percent": min(100, round((paid / max(total * 0.5, 1)) * 100, 0)),  # Meta: 50%
        "depth_distribution": {
            f"level_{d.depth_level}": d.count 
            for d in depth_stats
        }
    }


@router.post("/validate", response_model=dict)
async def validate_invite_code(
    invite_code: str,
    db: Session = Depends(get_db)
):
    """
    Valida un código de invitación (para registro).
    """
    invite = db.query(Invite).filter(
        Invite.invite_code == invite_code,
        Invite.deleted_at.is_(None)
    ).first()
    
    if not invite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Código de invitación no válido"
        )
    
    if invite.status in ['expired', 'cancelled']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Esta invitación ha expirado o sido cancelada"
        )
    
    if invite.expires_at and invite.expires_at < datetime.utcnow():
        invite.status = 'expired'
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Esta invitación ha expirado"
        )
    
    # Marcar como abierta si no lo está
    if invite.status == 'sent':
        invite.status = 'opened'
        invite.opened_at = datetime.utcnow()
        db.commit()
    
    return {
        "valid": True,
        "invite_code": invite.invite_code,
        "inviter_company": invite.inviter_company_name,
        "invitee_email": invite.invitee_email,
        "expected_plan": invite.expected_plan,
        "depth_level": invite.depth_level
    }
