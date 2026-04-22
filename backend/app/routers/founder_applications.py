"""
Conflict Zero - Founder Applications Router
Recibe aplicaciones desde la landing page founders.czperu.com
"""

from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime, timedelta
import hashlib
import os

from app.core.database import get_db
from app.models_v2 import FounderApplication, Company

router = APIRouter(prefix="/founder-applications", tags=["Founder Applications"])


class FounderApplicationCreate(BaseModel):
    """Schema para crear aplicación de Founder"""
    ruc: str = Field(..., min_length=11, max_length=11, pattern=r"^\d{11}$")
    company_name: str = Field(..., min_length=3, max_length=255)
    contact_name: str = Field(..., min_length=2, max_length=255)
    contact_email: str = Field(..., max_length=255)
    contact_phone: Optional[str] = Field(None, max_length=50)
    annual_volume: str = Field(..., pattern=r"^(10-50M|50-200M|200M+)$")
    subcontractor_count: str = Field(..., pattern=r"^(5-20|20-50|50+)$")
    
    @field_validator('ruc')
    @classmethod
    def validate_ruc(cls, v):
        if not v.isdigit() or len(v) != 11:
            raise ValueError('RUC debe tener 11 dígitos numéricos')
        return v


class FounderApplicationResponse(BaseModel):
    """Schema de respuesta"""
    id: str
    ruc_hash: str
    company_name: str
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True


@router.post(
    "/",
    response_model=FounderApplicationResponse,
    status_code=201,
    summary="Crear aplicación de Founder",
    description="Recibe aplicación desde la landing page y la guarda en PostgreSQL"
)
async def create_founder_application(
    application: FounderApplicationCreate,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Endpoint para la landing page founders.czperu.com
    Guarda la aplicación en founder_applications
    """
    # Generar hash del RUC (búsqueda sin desencriptar)
    ruc_hash = hashlib.sha256(application.ruc.encode()).hexdigest()
    
    # Verificar si ya existe aplicación con este RUC
    existing = db.query(FounderApplication).filter(
        FounderApplication.ruc_hash == ruc_hash,
        FounderApplication.deleted_at.is_(None)
    ).first()
    
    if existing:
        # Si ya existe y está pendiente, actualizar
        if existing.status == 'pending':
            existing.company_name = application.company_name
            existing.contact_name = application.contact_name
            existing.contact_email = application.contact_email
            existing.contact_phone = application.contact_phone
            existing.annual_volume = application.annual_volume
            existing.subcontractor_count = application.subcontractor_count
            existing.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(existing)
            return existing
        else:
            # Si ya fue procesada, rechazar
            raise HTTPException(
                status_code=400,
                detail="Este RUC ya tiene una aplicación en proceso"
            )
    
    # Crear nueva aplicación
    # NOTA: En producción real, el RUC debería encriptarse con pgcrypto o Fernet
    # Por ahora, guardamos solo el hash para búsquedas
    new_app = FounderApplication(
        ruc_hash=ruc_hash,
        # ruc_encrypted se deja NULL por ahora (necesitaría implementar encriptación real)
        company_name=application.company_name,
        contact_name=application.contact_name,
        contact_email=application.contact_email,
        contact_phone=application.contact_phone,
        annual_volume=application.annual_volume,
        subcontractor_count=application.subcontractor_count,
        status="pending",
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )
    
    db.add(new_app)
    db.commit()
    db.refresh(new_app)
    
    # Notificación async (desactivada en modo demo)
    # background_tasks.add_task(notify_new_application, new_app.id)
    
    print(f"✅ Nueva aplicación Founder recibida: {application.company_name} ({application.ruc})")
    
    return FounderApplicationResponse(
        id=str(new_app.id),
        ruc_hash=new_app.ruc_hash,
        company_name=new_app.company_name,
        status=new_app.status,
        created_at=new_app.created_at
    )


@router.get(
    "/",
    summary="Listar aplicaciones (Admin)",
    description="Obtener todas las aplicaciones de Founders (para panel admin)"
)
async def list_founder_applications(
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Lista aplicaciones para el equipo de review"""
    query = db.query(FounderApplication).filter(
        FounderApplication.deleted_at.is_(None)
    )
    
    if status:
        query = query.filter(FounderApplication.status == status)
    
    total = query.count()
    applications = query.order_by(
        FounderApplication.created_at.desc()
    ).offset(offset).limit(limit).all()
    
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "applications": [
            {
                "id": str(app.id),
                "company_name": app.company_name,
                "contact_name": app.contact_name,
                "contact_email": app.contact_email,
                "annual_volume": app.annual_volume,
                "subcontractor_count": app.subcontractor_count,
                "status": app.status,
                "priority_score": app.get_priority_score(),
                "potencial_red": app.get_potencial_efecto_red(),
                "created_at": app.created_at.isoformat() if app.created_at else None
            }
            for app in applications
        ]
    }


@router.get(
    "/{application_id}",
    summary="Obtener aplicación por ID"
)
async def get_founder_application(
    application_id: str,
    db: Session = Depends(get_db)
):
    """Obtener detalle de una aplicación"""
    from uuid import UUID
    
    try:
        app_uuid = UUID(application_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID inválido")
    
    application = db.query(FounderApplication).filter(
        FounderApplication.id == app_uuid,
        FounderApplication.deleted_at.is_(None)
    ).first()
    
    if not application:
        raise HTTPException(status_code=404, detail="Aplicación no encontrada")
    
    return {
        "id": str(application.id),
        "ruc_hash": application.ruc_hash[:16] + "...",
        "company_name": application.company_name,
        "contact_name": application.contact_name,
        "contact_email": application.contact_email,
        "contact_phone": application.contact_phone,
        "annual_volume": application.annual_volume,
        "subcontractor_count": application.subcontractor_count,
        "status": application.status,
        "notes": application.notes,
        "reviewed_by": application.reviewed_by,
        "reviewed_at": application.reviewed_at.isoformat() if application.reviewed_at else None,
        "priority_score": application.get_priority_score(),
        "potencial_red": application.get_potencial_efecto_red(),
        "created_at": application.created_at.isoformat() if application.created_at else None,
        "updated_at": application.updated_at.isoformat() if application.updated_at else None
    }


@router.patch(
    "/{application_id}/review",
    summary="Revisar aplicación (Admin)"
)
async def review_application(
    application_id: str,
    status: str,  # approved, rejected, waitlisted
    notes: Optional[str] = None,
    reviewed_by: str = "admin",
    db: Session = Depends(get_db)
):
    """Admin revisa y actualiza estado de aplicación"""
    from uuid import UUID
    
    if status not in ['approved', 'rejected', 'waitlisted', 'under_review']:
        raise HTTPException(status_code=400, detail="Estado inválido")
    
    try:
        app_uuid = UUID(application_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID inválido")
    
    application = db.query(FounderApplication).filter(
        FounderApplication.id == app_uuid
    ).first()
    
    if not application:
        raise HTTPException(status_code=404, detail="Aplicación no encontrada")
    
    application.status = status
    application.notes = notes
    application.reviewed_by = reviewed_by
    application.reviewed_at = datetime.utcnow()
    
    db.commit()
    db.refresh(application)
    
    # Si es approved, crear Company como Founder
    created_company = None
    if status == 'approved':
        # Verificar si ya existe una Company con este RUC
        existing_company = db.query(Company).filter(
            Company.ruc_hash == application.ruc_hash,
            Company.deleted_at.is_(None)
        ).first()
        
        if existing_company:
            # Actualizar a Founder
            existing_company.is_founder = True
            existing_company.plan_tier = "founder"
            existing_company.founder_expires_at = datetime.utcnow() + timedelta(days=365)
            existing_company.contact_email = application.contact_email
            existing_company.contact_name = application.contact_name
            existing_company.contact_phone = application.contact_phone
            db.commit()
            db.refresh(existing_company)
            created_company = existing_company
        else:
            # Crear nueva Company como Founder
            # Calcular expiración (12 meses desde ahora)
            founder_expires = datetime.utcnow() + timedelta(days=365)
            
            new_company = Company(
                ruc_encrypted=b"encrypted_placeholder",  # En producción: encriptar RUC real
                ruc_hash=application.ruc_hash,
                razon_social=application.company_name,
                contact_email=application.contact_email,
                contact_name=application.contact_name,
                contact_phone=application.contact_phone,
                plan_tier="founder",
                status="active",
                is_founder=True,
                founder_expires_at=founder_expires,
                max_monthly_queries=10000,  # Founder: 10k queries
                contractual_obligation=True,  # Founder tiene obligación contractual
                contractual_signed_at=datetime.utcnow(),
                retained_until=datetime.utcnow() + timedelta(days=365*5)  # 5 años retención legal
            )
            
            db.add(new_company)
            db.commit()
            db.refresh(new_company)
            created_company = new_company
            
            print(f"✅ Nueva Company Founder creada: {new_company.razon_social} (ID: {new_company.id})")
    
    result = {
        "message": f"Aplicación {status}",
        "application_id": application_id
    }
    
    if created_company:
        result["company"] = {
            "id": str(created_company.id),
            "razon_social": created_company.razon_social,
            "is_founder": created_company.is_founder,
            "founder_expires_at": created_company.founder_expires_at.isoformat() if created_company.founder_expires_at else None
        }
    
    return result


@router.get(
    "/stats/summary",
    summary="Estadísticas de aplicaciones"
)
async def get_application_stats(
    db: Session = Depends(get_db)
):
    """Stats para dashboard admin"""
    # SQLite-compatible query: count with filter conditions
    total = db.query(FounderApplication).filter(
        FounderApplication.deleted_at.is_(None)
    ).count()
    
    pending = db.query(FounderApplication).filter(
        FounderApplication.deleted_at.is_(None),
        FounderApplication.status == 'pending'
    ).count()
    
    under_review = db.query(FounderApplication).filter(
        FounderApplication.deleted_at.is_(None),
        FounderApplication.status == 'under_review'
    ).count()
    
    approved = db.query(FounderApplication).filter(
        FounderApplication.deleted_at.is_(None),
        FounderApplication.status == 'approved'
    ).count()
    
    rejected = db.query(FounderApplication).filter(
        FounderApplication.deleted_at.is_(None),
        FounderApplication.status == 'rejected'
    ).count()
    
    return {
        "total": total,
        "pending": pending,
        "under_review": under_review,
        "approved": approved,
        "rejected": rejected,
        "conversion_rate": round(approved / total * 100, 1) if total > 0 else 0
    }
