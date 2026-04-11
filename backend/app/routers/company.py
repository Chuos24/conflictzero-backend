"""
Conflict Zero - Company Router
Endpoints para gestión de perfil de empresa y API keys
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field, EmailStr
import hashlib
import secrets
import uuid

from app.core.database import get_db
from app.core.security import get_current_company, generate_api_key
from app.models_v2 import Company, ApiKey, AuditLog

router = APIRouter(prefix="/company", tags=["Empresa"])


# ============================================================
# SCHEMAS
# ============================================================

class CompanyProfileResponse(BaseModel):
    """Respuesta del perfil de empresa"""
    id: str
    ruc_hash: str
    public_slug: str
    razon_social: str
    direccion: Optional[str]
    distrito: Optional[str]
    provincia: Optional[str]
    departamento: Optional[str]
    plan_tier: str
    status: str
    is_founder: bool
    founder_expires_at: Optional[datetime]
    max_monthly_queries: int
    used_queries_this_month: int
    queries_reset_at: datetime
    contact_email: str
    contact_name: Optional[str]
    contact_phone: Optional[str]
    created_at: datetime
    last_login_at: Optional[datetime]


class UpdateCompanyProfileRequest(BaseModel):
    """Request para actualizar perfil de empresa"""
    razon_social: Optional[str] = Field(None, min_length=3, max_length=255)
    direccion: Optional[str] = Field(None, max_length=500)
    distrito: Optional[str] = Field(None, max_length=100)
    provincia: Optional[str] = Field(None, max_length=100)
    departamento: Optional[str] = Field(None, max_length=100)
    contact_name: Optional[str] = Field(None, min_length=2, max_length=255)
    contact_phone: Optional[str] = Field(None, max_length=50)


class ApiKeyCreateRequest(BaseModel):
    """Request para crear API key"""
    name: str = Field(default="API Key", min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    expires_days: Optional[int] = Field(None, ge=1, le=365, description="Días hasta expiración (opcional)")


class ApiKeyResponse(BaseModel):
    """Respuesta con API key (solo se muestra al crear)"""
    id: str
    key: str  # La key completa, solo se muestra una vez
    name: str
    key_prefix: str
    description: Optional[str]
    created_at: datetime
    expires_at: Optional[datetime]
    message: str = "Guarda esta clave, no se mostrará de nuevo."


class ApiKeyInfoResponse(BaseModel):
    """Info de API key sin el secret"""
    id: str
    name: str
    key_prefix: str
    description: Optional[str]
    usage_count: int
    last_used_at: Optional[datetime]
    is_active: bool
    created_at: datetime
    expires_at: Optional[datetime]
    revoked_at: Optional[datetime]


class ApiKeyListResponse(BaseModel):
    """Respuesta de lista de API keys"""
    items: List[ApiKeyInfoResponse]
    total: int


class UpdateApiKeyRequest(BaseModel):
    """Request para actualizar API key"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)


class CompanyStatsResponse(BaseModel):
    """Estadísticas de la empresa"""
    total_verifications: int
    total_api_keys: int
    active_api_keys: int
    plan_tier: str
    queries_remaining: int
    queries_used_percent: float


# ============================================================
# ENDPOINTS - PROFILE
# ============================================================

@router.get("/profile", response_model=CompanyProfileResponse, summary="Obtener perfil de empresa")
async def get_company_profile(
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db)
):
    """
    Obtiene el perfil completo de la empresa autenticada.
    
    - Requiere autenticación
    - No incluye datos sensibles como API keys
    """
    return CompanyProfileResponse(
        id=str(current_company.id),
        ruc_hash=current_company.ruc_hash[:16] + "..." if current_company.ruc_hash else "",
        public_slug=current_company.public_slug,
        razon_social=current_company.razon_social,
        direccion=current_company.direccion,
        distrito=current_company.distrito,
        provincia=current_company.provincia,
        departamento=current_company.departamento,
        plan_tier=current_company.plan_tier,
        status=current_company.status,
        is_founder=current_company.is_founder,
        founder_expires_at=current_company.founder_expires_at,
        max_monthly_queries=current_company.max_monthly_queries,
        used_queries_this_month=current_company.used_queries_this_month,
        queries_reset_at=current_company.queries_reset_at or datetime.utcnow(),
        contact_email=current_company.contact_email,
        contact_name=current_company.contact_name,
        contact_phone=current_company.contact_phone,
        created_at=current_company.created_at,
        last_login_at=current_company.last_login_at
    )


@router.patch("/profile", response_model=CompanyProfileResponse, summary="Actualizar perfil de empresa")
async def update_company_profile(
    request: UpdateCompanyProfileRequest,
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db)
):
    """
    Actualiza los datos del perfil de la empresa.
    
    - Requiere autenticación
    - Solo actualiza los campos proporcionados
    - Registra cambios en auditoría
    """
    old_values = {}
    new_values = {}
    
    # Actualizar campos si se proporcionan
    if request.razon_social is not None:
        old_values["razon_social"] = current_company.razon_social
        current_company.razon_social = request.razon_social
        new_values["razon_social"] = request.razon_social
    
    if request.direccion is not None:
        old_values["direccion"] = current_company.direccion
        current_company.direccion = request.direccion
        new_values["direccion"] = request.direccion
    
    if request.distrito is not None:
        old_values["distrito"] = current_company.distrito
        current_company.distrito = request.distrito
        new_values["distrito"] = request.distrito
    
    if request.provincia is not None:
        old_values["provincia"] = current_company.provincia
        current_company.provincia = request.provincia
        new_values["provincia"] = request.provincia
    
    if request.departamento is not None:
        old_values["departamento"] = current_company.departamento
        current_company.departamento = request.departamento
        new_values["departamento"] = request.departamento
    
    if request.contact_name is not None:
        old_values["contact_name"] = current_company.contact_name
        current_company.contact_name = request.contact_name
        new_values["contact_name"] = request.contact_name
    
    if request.contact_phone is not None:
        old_values["contact_phone"] = current_company.contact_phone
        current_company.contact_phone = request.contact_phone
        new_values["contact_phone"] = request.contact_phone
    
    # Guardar cambios
    if new_values:
        current_company.updated_at = datetime.utcnow()
        
        # Log de auditoría
        audit = AuditLog(
            id=uuid.uuid4(),
            actor_type="user",
            actor_id=str(current_company.id),
            company_id=current_company.id,
            action="company_profile_updated",
            resource_type="company",
            resource_id=str(current_company.id),
            old_values=old_values,
            new_values=new_values,
            created_at=datetime.utcnow()
        )
        db.add(audit)
        db.commit()
    
    return CompanyProfileResponse(
        id=str(current_company.id),
        ruc_hash=current_company.ruc_hash[:16] + "..." if current_company.ruc_hash else "",
        public_slug=current_company.public_slug,
        razon_social=current_company.razon_social,
        direccion=current_company.direccion,
        distrito=current_company.distrito,
        provincia=current_company.provincia,
        departamento=current_company.departamento,
        plan_tier=current_company.plan_tier,
        status=current_company.status,
        is_founder=current_company.is_founder,
        founder_expires_at=current_company.founder_expires_at,
        max_monthly_queries=current_company.max_monthly_queries,
        used_queries_this_month=current_company.used_queries_this_month,
        queries_reset_at=current_company.queries_reset_at or datetime.utcnow(),
        contact_email=current_company.contact_email,
        contact_name=current_company.contact_name,
        contact_phone=current_company.contact_phone,
        created_at=current_company.created_at,
        last_login_at=current_company.last_login_at
    )


@router.get("/stats", response_model=CompanyStatsResponse, summary="Obtener estadísticas de empresa")
async def get_company_stats(
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db)
):
    """
    Obtiene estadísticas de uso de la empresa.
    
    - Requiere autenticación
    """
    from app.models_v2 import VerificationRequest
    
    # Contar verificaciones
    total_verifications = db.query(VerificationRequest).filter(
        VerificationRequest.consultant_id == current_company.id,
        VerificationRequest.deleted_at.is_(None)
    ).count()
    
    # Contar API keys
    total_api_keys = db.query(ApiKey).filter(
        ApiKey.company_id == current_company.id,
        ApiKey.deleted_at.is_(None)
    ).count()
    
    active_api_keys = db.query(ApiKey).filter(
        ApiKey.company_id == current_company.id,
        ApiKey.is_active == True,
        ApiKey.deleted_at.is_(None)
    ).count()
    
    # Calcular porcentaje de uso
    queries_used_percent = (
        (current_company.used_queries_this_month / current_company.max_monthly_queries * 100)
        if current_company.max_monthly_queries > 0 else 0
    )
    
    return CompanyStatsResponse(
        total_verifications=total_verifications,
        total_api_keys=total_api_keys,
        active_api_keys=active_api_keys,
        plan_tier=current_company.plan_tier,
        queries_remaining=current_company.max_monthly_queries - current_company.used_queries_this_month,
        queries_used_percent=round(queries_used_percent, 1)
    )


# ============================================================
# ENDPOINTS - API KEYS
# ============================================================

@router.get("/api-keys", response_model=ApiKeyListResponse, summary="Listar API keys")
async def list_api_keys(
    include_revoked: bool = Query(False, description="Incluir keys revocadas"),
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db)
):
    """
    Lista todas las API keys de la empresa.
    
    - Requiere autenticación
    - Por defecto no incluye keys revocadas
    """
    query = db.query(ApiKey).filter(
        ApiKey.company_id == current_company.id,
        ApiKey.deleted_at.is_(None)
    )
    
    if not include_revoked:
        query = query.filter(ApiKey.is_active == True)
    
    api_keys = query.order_by(desc(ApiKey.created_at)).all()
    
    items = [
        ApiKeyInfoResponse(
            id=str(key.id),
            name=key.name,
            key_prefix=key.key_prefix,
            description=key.description,
            usage_count=key.usage_count or 0,
            last_used_at=key.last_used_at,
            is_active=key.is_active,
            created_at=key.created_at,
            expires_at=key.expires_at,
            revoked_at=key.revoked_at
        )
        for key in api_keys
    ]
    
    return ApiKeyListResponse(
        items=items,
        total=len(items)
    )


@router.post("/api-keys", response_model=ApiKeyResponse, summary="Crear API key")
async def create_api_key(
    request: ApiKeyCreateRequest,
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db)
):
    """
    Crea una nueva API key para la empresa.
    
    - Requiere autenticación
    - La key solo se muestra una vez al crear
    - Se puede especificar expiración opcional
    """
    # Generar nueva key
    api_key, key_hash = generate_api_key()
    
    # Calcular expiración si se especifica
    expires_at = None
    if request.expires_days:
        expires_at = datetime.utcnow() + timedelta(days=request.expires_days)
    
    # Crear registro
    new_key = ApiKey(
        id=uuid.uuid4(),
        company_id=current_company.id,
        key_hash=key_hash,
        key_prefix=api_key[:8],
        name=request.name,
        description=request.description,
        is_active=True,
        usage_count=0,
        created_at=datetime.utcnow(),
        expires_at=expires_at,
        created_by=str(current_company.id)
    )
    
    # Log de auditoría
    audit = AuditLog(
        id=uuid.uuid4(),
        actor_type="user",
        actor_id=str(current_company.id),
        company_id=current_company.id,
        action="api_key_created",
        resource_type="api_key",
        resource_id=str(new_key.id),
        new_values={
            "name": request.name,
            "prefix": api_key[:8],
            "expires_at": expires_at.isoformat() if expires_at else None
        },
        created_at=datetime.utcnow()
    )
    
    db.add(new_key)
    db.add(audit)
    db.commit()
    db.refresh(new_key)
    
    return ApiKeyResponse(
        id=str(new_key.id),
        key=api_key,
        name=new_key.name,
        key_prefix=new_key.key_prefix,
        description=new_key.description,
        created_at=new_key.created_at,
        expires_at=new_key.expires_at
    )


@router.patch("/api-keys/{key_id}", response_model=ApiKeyInfoResponse, summary="Actualizar API key")
async def update_api_key(
    key_id: str,
    request: UpdateApiKeyRequest,
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db)
):
    """
    Actualiza el nombre o descripción de una API key.
    
    - Requiere autenticación
    - No se puede modificar la key en sí
    """
    try:
        key_uuid = uuid.UUID(key_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de API key inválido"
        )
    
    api_key = db.query(ApiKey).filter(
        ApiKey.id == key_uuid,
        ApiKey.company_id == current_company.id,
        ApiKey.deleted_at.is_(None)
    ).first()
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key no encontrada"
        )
    
    old_values = {}
    new_values = {}
    
    if request.name is not None:
        old_values["name"] = api_key.name
        api_key.name = request.name
        new_values["name"] = request.name
    
    if request.description is not None:
        old_values["description"] = api_key.description
        api_key.description = request.description
        new_values["description"] = request.description
    
    if new_values:
        api_key.updated_at = datetime.utcnow()
        
        # Log de auditoría
        audit = AuditLog(
            id=uuid.uuid4(),
            actor_type="user",
            actor_id=str(current_company.id),
            company_id=current_company.id,
            action="api_key_updated",
            resource_type="api_key",
            resource_id=str(api_key.id),
            old_values=old_values,
            new_values=new_values,
            created_at=datetime.utcnow()
        )
        db.add(audit)
        db.commit()
    
    return ApiKeyInfoResponse(
        id=str(api_key.id),
        name=api_key.name,
        key_prefix=api_key.key_prefix,
        description=api_key.description,
        usage_count=api_key.usage_count or 0,
        last_used_at=api_key.last_used_at,
        is_active=api_key.is_active,
        created_at=api_key.created_at,
        expires_at=api_key.expires_at,
        revoked_at=api_key.revoked_at
    )


@router.delete("/api-keys/{key_id}", summary="Revocar API key")
async def revoke_api_key(
    key_id: str,
    reason: Optional[str] = None,
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db)
):
    """
    Revoca (elimina) una API key.
    
    - Requiere autenticación
    - La key dejará de funcionar inmediatamente
    - Se puede especificar una razón
    """
    try:
        key_uuid = uuid.UUID(key_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de API key inválido"
        )
    
    api_key = db.query(ApiKey).filter(
        ApiKey.id == key_uuid,
        ApiKey.company_id == current_company.id,
        ApiKey.deleted_at.is_(None)
    ).first()
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key no encontrada"
        )
    
    # Revocar key
    api_key.is_active = False
    api_key.revoked_at = datetime.utcnow()
    api_key.revoked_reason = reason or "Revocada por usuario"
    
    # Log de auditoría
    audit = AuditLog(
        id=uuid.uuid4(),
        actor_type="user",
        actor_id=str(current_company.id),
        company_id=current_company.id,
        action="api_key_revoked",
        resource_type="api_key",
        resource_id=str(api_key.id),
        old_values={"is_active": True},
        new_values={
            "is_active": False,
            "revoked_reason": api_key.revoked_reason
        },
        created_at=datetime.utcnow()
    )
    
    db.add(audit)
    db.commit()
    
    return {
        "success": True,
        "message": "API key revocada correctamente",
        "revoked_at": api_key.revoked_at.isoformat()
    }
