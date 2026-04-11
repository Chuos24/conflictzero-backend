"""
Conflict Zero - Auth Router
Endpoints de autenticación y gestión de usuario
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime
import hashlib
import secrets

from app.core.database import get_db
from app.core.security import (
    get_current_company, 
    get_password_hash, 
    verify_password,
    generate_api_key,
    create_access_token
)
from app.models_v2 import Company, AuditLog

router = APIRouter(prefix="/auth", tags=["Autenticación"])


# ============================================================
# SCHEMAS
# ============================================================

class RegisterRequest(BaseModel):
    """Registro de nueva empresa"""
    ruc: str = Field(..., min_length=11, max_length=11, pattern=r'^\d{11}$')
    razon_social: str = Field(..., min_length=3, max_length=255)
    contact_email: EmailStr
    contact_name: str = Field(..., min_length=2, max_length=255)
    contact_phone: Optional[str] = Field(None, max_length=50)
    password: str = Field(..., min_length=8, max_length=100)
    invited_by_code: Optional[str] = None


class LoginRequest(BaseModel):
    """Login de empresa"""
    ruc: str = Field(..., min_length=11, max_length=11)
    password: str


class UpdateProfileRequest(BaseModel):
    """Actualizar perfil"""
    contact_name: Optional[str] = Field(None, min_length=2, max_length=255)
    contact_phone: Optional[str] = None
    razon_social: Optional[str] = Field(None, min_length=3, max_length=255)


class ChangePasswordRequest(BaseModel):
    """Cambiar contraseña"""
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=100)


class AuthResponse(BaseModel):
    """Respuesta de autenticación"""
    access_token: str
    token_type: str = "bearer"
    company: dict


class MeResponse(BaseModel):
    """Respuesta con datos del usuario actual"""
    ruc_hash: str
    razon_social: str
    plan_tier: str
    status: str
    is_founder: bool
    contact_email: str
    contact_name: Optional[str]
    max_monthly_queries: int
    used_queries_this_month: int
    api_key_prefix: Optional[str]


class ApiKeyResponse(BaseModel):
    """Respuesta con API key"""
    api_key: str
    prefix: str
    created_at: datetime
    message: str


# ============================================================
# ENDPOINTS
# ============================================================

@router.post("/register", response_model=AuthResponse, summary="Registrar nueva empresa")
async def register(
    request: RegisterRequest,
    db: Session = Depends(get_db)
):
    """
    Registra una nueva empresa en el sistema.
    """
    # Verificar si el RUC ya existe
    ruc_hash = hashlib.sha256(request.ruc.encode()).hexdigest()
    existing = db.query(Company).filter(
        Company.ruc_hash == ruc_hash,
        Company.deleted_at.is_(None)
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este RUC ya está registrado"
        )
    
    # Crear nueva empresa
    password_hash = get_password_hash(request.password)
    
    company = Company(
        ruc_hash=ruc_hash,
        ruc_encrypted=request.ruc.encode(),  # En producción: encriptar con AES
        razon_social=request.razon_social,
        contact_email=request.contact_email,
        contact_name=request.contact_name,
        contact_phone=request.contact_phone,
        password_hash=password_hash,
        invited_by_code=request.invited_by_code,
        plan_tier="bronze",
        status="active"
    )
    
    db.add(company)
    db.flush()  # Para obtener el ID
    
    # Generar API key inicial
    api_key, api_key_hash = generate_api_key()
    company.api_key = api_key_hash
    company.api_key_created_at = datetime.utcnow()
    
    # Log de auditoría
    audit = AuditLog(
        actor_type="user",
        actor_id=str(company.id),
        company_id=company.id,
        action="company_registered",
        resource_type="company",
        resource_id=str(company.id)
    )
    db.add(audit)
    db.commit()
    
    # Generar token
    access_token = create_access_token(data={"sub": str(company.id)})
    
    return AuthResponse(
        access_token=access_token,
        company={
            "id": str(company.id),
            "razon_social": company.razon_social,
            "plan_tier": company.plan_tier
        }
    )


@router.post("/login", response_model=AuthResponse, summary="Iniciar sesión")
async def login(
    request: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Inicia sesión con RUC y contraseña.
    """
    # Buscar empresa por RUC hash
    ruc_hash = hashlib.sha256(request.ruc.encode()).hexdigest()
    company = db.query(Company).filter(
        Company.ruc_hash == ruc_hash,
        Company.deleted_at.is_(None)
    ).first()
    
    if not company or not company.password_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="RUC o contraseña incorrectos"
        )
    
    # Verificar contraseña
    if not verify_password(request.password, company.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="RUC o contraseña incorrectos"
        )
    
    # Verificar estado
    if company.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Cuenta {company.status}. Contacte soporte."
        )
    
    # Actualizar último login
    company.last_login_at = datetime.utcnow()
    db.commit()
    
    # Generar token
    access_token = create_access_token(data={"sub": str(company.id)})
    
    return AuthResponse(
        access_token=access_token,
        company={
            "id": str(company.id),
            "razon_social": company.razon_social,
            "plan_tier": company.plan_tier,
            "is_founder": company.is_founder
        }
    )


@router.get("/me", response_model=MeResponse, summary="Obtener datos del usuario actual")
async def get_me(
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db)
):
    """
    Retorna los datos de la empresa autenticada.
    """
    # Obtener prefijo de API key si existe
    api_key_prefix = None
    if current_company.api_key:
        api_key_prefix = current_company.api_key[:8] + "..."
    
    return MeResponse(
        ruc_hash=current_company.ruc_hash[:16] + "...",
        razon_social=current_company.razon_social,
        plan_tier=current_company.plan_tier,
        status=current_company.status,
        is_founder=current_company.is_founder,
        contact_email=current_company.contact_email,
        contact_name=current_company.contact_name,
        max_monthly_queries=current_company.max_monthly_queries,
        used_queries_this_month=current_company.used_queries_this_month,
        api_key_prefix=api_key_prefix
    )


@router.patch("/profile", summary="Actualizar perfil")
async def update_profile(
    request: UpdateProfileRequest,
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db)
):
    """
    Actualiza los datos del perfil de la empresa.
    """
    old_values = {}
    new_values = {}
    
    if request.contact_name is not None:
        old_values["contact_name"] = current_company.contact_name
        current_company.contact_name = request.contact_name
        new_values["contact_name"] = request.contact_name
    
    if request.contact_phone is not None:
        old_values["contact_phone"] = current_company.contact_phone
        current_company.contact_phone = request.contact_phone
        new_values["contact_phone"] = request.contact_phone
    
    if request.razon_social is not None:
        old_values["razon_social"] = current_company.razon_social
        current_company.razon_social = request.razon_social
        new_values["razon_social"] = request.razon_social
    
    # Guardar cambios
    if new_values:
        current_company.updated_at = datetime.utcnow()
        
        # Log de auditoría
        audit = AuditLog(
            actor_type="user",
            actor_id=str(current_company.id),
            company_id=current_company.id,
            action="profile_updated",
            resource_type="company",
            resource_id=str(current_company.id),
            old_values=old_values,
            new_values=new_values
        )
        db.add(audit)
        db.commit()
    
    return {
        "success": True,
        "message": "Perfil actualizado",
        "updated_fields": list(new_values.keys())
    }


@router.post("/change-password", summary="Cambiar contraseña")
async def change_password(
    request: ChangePasswordRequest,
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db)
):
    """
    Cambia la contraseña de la cuenta.
    """
    # Verificar contraseña actual
    if not verify_password(request.current_password, current_company.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Contraseña actual incorrecta"
        )
    
    # Actualizar contraseña
    current_company.password_hash = get_password_hash(request.new_password)
    current_company.updated_at = datetime.utcnow()
    
    # Log de auditoría
    audit = AuditLog(
        actor_type="user",
        actor_id=str(current_company.id),
        company_id=current_company.id,
        action="password_changed",
        resource_type="company",
        resource_id=str(current_company.id)
    )
    db.add(audit)
    db.commit()
    
    return {
        "success": True,
        "message": "Contraseña actualizada correctamente"
    }


@router.post("/regenerate-api-key", response_model=ApiKeyResponse, summary="Regenerar API key")
async def regenerate_api_key(
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db)
):
    """
    Genera una nueva API key y revoca la anterior.
    
    ⚠️ La API key anterior dejará de funcionar inmediatamente.
    """
    # Generar nueva key
    new_api_key, new_api_key_hash = generate_api_key()
    
    # Guardar old para log
    old_key_prefix = None
    if current_company.api_key:
        old_key_prefix = current_company.api_key[:8]
    
    # Actualizar
    current_company.api_key = new_api_key_hash
    current_company.api_key_created_at = datetime.utcnow()
    
    # Log de auditoría
    audit = AuditLog(
        actor_type="user",
        actor_id=str(current_company.id),
        company_id=current_company.id,
        action="api_key_regenerated",
        resource_type="company",
        resource_id=str(current_company.id),
        old_values={"old_key_prefix": old_key_prefix},
        new_values={"new_key_prefix": new_api_key[:8]}
    )
    db.add(audit)
    db.commit()
    
    return ApiKeyResponse(
        api_key=new_api_key,
        prefix=new_api_key[:8],
        created_at=datetime.utcnow(),
        message="API key regenerada. Guarda esta clave, no se mostrará de nuevo."
    )
