"""
Conflict Zero - Admin Router
Endpoints para administración del sistema
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from uuid import UUID

from app.core.database import get_db
from app.core.security import get_current_admin
from app.schemas import UserResponse

router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
    responses={401: {"description": "Unauthorized"}, 403: {"description": "Forbidden"}}
)


@router.get("/pending-users", response_model=List[UserResponse])
async def get_pending_users(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_admin)
):
    """
    Obtener lista de usuarios pendientes de aprobación.
    Requiere autenticación de administrador.
    """
    from app.models_v2 import Company
    
    # Get companies with pending status
    pending = db.query(Company).filter(
        Company.status == "pending"
    ).order_by(Company.created_at.desc()).all()
    
    return [
        UserResponse(
            id=company.id,
            email=company.contact_email,
            ruc=company.ruc_hash[:11] if company.ruc_hash else None,  # Usar hash como identificador
            company_name=company.razon_social,
            status=company.status,
            created_at=company.created_at,
            founder_program=company.is_founder
        )
        for company in pending
    ]


@router.get("/all-users", response_model=List[UserResponse])
async def get_all_users(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_admin)
):
    """
    Obtener todos los usuarios registrados.
    Requiere autenticación de administrador.
    """
    from app.models_v2 import Company
    
    users = db.query(Company).order_by(Company.created_at.desc()).all()
    
    return [
        UserResponse(
            id=company.id,
            email=company.contact_email,
            ruc=company.ruc_hash[:11] if company.ruc_hash else None,
            company_name=company.razon_social,
            status=company.status,
            created_at=company.created_at,
            founder_program=company.is_founder
        )
        for company in users
    ]


@router.post("/approve-user/{user_id}")
async def approve_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_admin)
):
    """
    Aprobar un usuario pendiente.
    Requiere autenticación de administrador.
    """
    from app.models_v2 import Company
    from app.services.email_service import send_approval_email
    
    try:
        company_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de usuario inválido"
        )
    
    company = db.query(Company).filter(Company.id == company_uuid).first()
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    company.status = "active"
    company.updated_at = datetime.utcnow()
    db.commit()
    
    # Send approval email
    try:
        await send_approval_email(company.contact_email, company.razon_social)
    except Exception as e:
        print(f"⚠️  Error sending approval email: {e}")
    
    return {
        "success": True,
        "message": f"Usuario {company.contact_email} aprobado exitosamente",
        "user_id": user_id
    }


@router.post("/reject-user/{user_id}")
async def reject_user(
    user_id: str,
    reason: str = "No cumple con los requisitos",
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_admin)
):
    """
    Rechazar un usuario pendiente.
    Requiere autenticación de administrador.
    """
    from app.models_v2 import Company
    from app.services.email_service import send_rejection_email
    
    try:
        company_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de usuario inválido"
        )
    
    company = db.query(Company).filter(Company.id == company_uuid).first()
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    user_email = company.contact_email
    user_name = company.razon_social
    
    # Delete the rejected user
    db.delete(company)
    db.commit()
    
    # Send rejection email
    try:
        await send_rejection_email(user_email, user_name, reason)
    except Exception as e:
        print(f"⚠️  Error sending rejection email: {e}")
    
    return {
        "success": True,
        "message": f"Usuario {user_email} rechazado",
        "user_id": user_id,
        "reason": reason
    }


@router.get("/stats")
async def get_admin_stats(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_admin)
):
    """
    Obtener estadísticas para el panel de admin.
    Requiere autenticación de administrador.
    """
    from app.models_v2 import Company, VerificationRequest, FounderApplication
    from sqlalchemy import func
    
    # User stats
    total_users = db.query(Company).count()
    pending_users = db.query(Company).filter(Company.status == "pending").count()
    active_users = db.query(Company).filter(Company.status == "active").count()
    founder_users = db.query(Company).filter(Company.is_founder == True).count()
    
    # Verification stats
    total_verifications = db.query(VerificationRequest).count()
    
    # Founder applications
    total_applications = db.query(FounderApplication).count()
    pending_applications = db.query(FounderApplication).filter(
        FounderApplication.status == "pending"
    ).count()
    
    # Recent registrations (last 7 days)
    from datetime import timedelta
    week_ago = datetime.utcnow() - timedelta(days=7)
    recent_users = db.query(Company).filter(Company.created_at >= week_ago).count()
    
    return {
        "users": {
            "total": total_users,
            "pending": pending_users,
            "active": active_users,
            "founder_program": founder_users,
            "recent_7_days": recent_users
        },
        "verifications": {
            "total": total_verifications
        },
        "founder_applications": {
            "total": total_applications,
            "pending": pending_applications
        },
        "timestamp": datetime.utcnow().isoformat()
    }
