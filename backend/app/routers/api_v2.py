"""
Conflict Zero - API v2 Routes (General)
Endpoints misceláneos de la API v2
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from app.core.database import get_db
from app.models_v2 import Company, PublicProfile, VerificationRequest

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
