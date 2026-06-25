"""
White-label Router
Endpoints para gestión de configuraciones white-label / personalización de marca.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.services.white_label import WhiteLabelService, BrandingConfig, ThemeColor, MARKET_CONFIGS
from app.core.security import get_current_company


router = APIRouter(prefix="/white-label", tags=["White-label"])


class WhiteLabelCreateRequest(BaseModel):
    tenant_id: str
    config: dict


class WhiteLabelUpdateRequest(BaseModel):
    config: dict


class WhiteLabelResponse(BaseModel):
    tenant_id: str
    config: dict
    css_variables: str
    manifest: dict


class WhiteLabelListResponse(BaseModel):
    tenants: list
    default_config: dict
    market_configs: list


# ===== PUBLIC ENDPOINTS =====

@router.get("/config", response_model=dict)
async def get_public_config(tenant_id: Optional[str] = None):
    """
    Obtiene la configuración white-label pública de un tenant.
    No requiere autenticación - usado por el frontend para cargar tema.
    """
    config = WhiteLabelService.get_tenant_config(tenant_id)
    return {
        "app_name": config.app_name,
        "app_short_name": config.app_short_name,
        "company_name": config.company_name,
        "support_url": config.support_url,
        "privacy_url": config.privacy_url,
        "terms_url": config.terms_url,
        "support_email": config.support_email,
        "support_phone": config.support_phone,
        "logo_url": config.logo_url,
        "logo_dark_url": config.logo_dark_url,
        "favicon_url": config.favicon_url,
        "theme": config.theme.model_dump(),
        "font_family": config.font_family,
        "font_heading": config.font_heading,
        "features": config.features,
        "custom_texts": config.custom_texts,
        "meta_title": config.meta_title,
        "meta_description": config.meta_description,
        "default_language": config.default_language,
        "supported_languages": config.supported_languages,
    }


@router.get("/config/{tenant_id}/css")
async def get_tenant_css(tenant_id: str):
    """Genera variables CSS para el tema del tenant"""
    config = WhiteLabelService.get_tenant_config(tenant_id)
    css = WhiteLabelService.generate_css_variables(config)
    return {"css": css, "tenant_id": tenant_id}


@router.get("/config/{tenant_id}/manifest.json")
async def get_tenant_manifest(tenant_id: str):
    """Genera manifest.json para PWA personalizado"""
    config = WhiteLabelService.get_tenant_config(tenant_id)
    manifest = WhiteLabelService.generate_manifest_json(config)
    return manifest


# ===== ADMIN ENDPOINTS (requieren autenticación) =====

@router.get("/admin/tenants", response_model=WhiteLabelListResponse)
async def list_tenants(current_company=Depends(get_current_company)):
    """Lista todos los tenants white-label registrados (solo admin)"""
    # Verificar rol admin
    if getattr(current_company, 'role', None) != 'admin' and getattr(current_company, 'is_admin', False) is not True:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requiere rol de administrador"
        )
    
    tenants = [
        {"tenant_id": tid, "app_name": cfg.app_name}
        for tid, cfg in WhiteLabelService._tenants.items()
    ]
    
    return WhiteLabelListResponse(
        tenants=tenants,
        default_config=WhiteLabelService.DEFAULT_CONFIG.model_dump(),
        market_configs=list(MARKET_CONFIGS.keys())
    )


@router.post("/admin/tenants", response_model=WhiteLabelResponse, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    request: WhiteLabelCreateRequest,
    current_company=Depends(get_current_company)
):
    """Registra un nuevo tenant white-label"""
    # Verificar rol admin
    if getattr(current_company, 'role', None) != 'admin' and getattr(current_company, 'is_admin', False) is not True:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requiere rol de administrador"
        )
    
    # Validar que no exista
    if request.tenant_id in WhiteLabelService._tenants:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Tenant '{request.tenant_id}' ya existe"
        )
    
    # Crear configuración
    try:
        config = BrandingConfig(**request.config)
        WhiteLabelService.register_tenant(request.tenant_id, config)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    return WhiteLabelResponse(
        tenant_id=request.tenant_id,
        config=config.model_dump(),
        css_variables=WhiteLabelService.generate_css_variables(config),
        manifest=WhiteLabelService.generate_manifest_json(config)
    )


@router.get("/admin/tenants/{tenant_id}", response_model=WhiteLabelResponse)
async def get_tenant_detail(
    tenant_id: str,
    current_company=Depends(get_current_company)
):
    """Obtiene detalle completo de un tenant"""
    if getattr(current_company, 'role', None) != 'admin' and getattr(current_company, 'is_admin', False) is not True:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requiere rol de administrador"
        )
    
    config = WhiteLabelService.get_tenant_config(tenant_id)
    
    return WhiteLabelResponse(
        tenant_id=tenant_id,
        config=config.model_dump(),
        css_variables=WhiteLabelService.generate_css_variables(config),
        manifest=WhiteLabelService.generate_manifest_json(config)
    )


@router.put("/admin/tenants/{tenant_id}", response_model=WhiteLabelResponse)
async def update_tenant(
    tenant_id: str,
    request: WhiteLabelUpdateRequest,
    current_company=Depends(get_current_company)
):
    """Actualiza configuración de un tenant"""
    if getattr(current_company, 'role', None) != 'admin' and getattr(current_company, 'is_admin', False) is not True:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requiere rol de administrador"
        )
    
    if tenant_id not in WhiteLabelService._tenants:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant '{tenant_id}' no encontrado"
        )
    
    try:
        config = BrandingConfig(**request.config)
        WhiteLabelService._tenants[tenant_id] = config
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    return WhiteLabelResponse(
        tenant_id=tenant_id,
        config=config.model_dump(),
        css_variables=WhiteLabelService.generate_css_variables(config),
        manifest=WhiteLabelService.generate_manifest_json(config)
    )


@router.delete("/admin/tenants/{tenant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tenant(
    tenant_id: str,
    current_company=Depends(get_current_company)
):
    """Elimina un tenant white-label"""
    if getattr(current_company, 'role', None) != 'admin' and getattr(current_company, 'is_admin', False) is not True:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requiere rol de administrador"
        )
    
    if tenant_id not in WhiteLabelService._tenants:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant '{tenant_id}' no encontrado"
        )
    
    del WhiteLabelService._tenants[tenant_id]
    return None


@router.get("/admin/markets/{market_id}", response_model=dict)
async def get_market_config(
    market_id: str,
    current_company=Depends(get_current_company)
):
    """Obtiene configuración predefinida para un mercado"""
    if getattr(current_company, 'role', None) != 'admin' and getattr(current_company, 'is_admin', False) is not True:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requiere rol de administrador"
        )
    
    if market_id not in MARKET_CONFIGS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mercado '{market_id}' no encontrado. Disponibles: {list(MARKET_CONFIGS.keys())}"
        )
    
    config = MARKET_CONFIGS[market_id]
    return {
        "market_id": market_id,
        "config": config.model_dump(),
        "css_variables": WhiteLabelService.generate_css_variables(config),
        "manifest": WhiteLabelService.generate_manifest_json(config)
    }


@router.post("/admin/markets/{market_id}/clone/{tenant_id}", response_model=WhiteLabelResponse)
async def clone_market_config(
    market_id: str,
    tenant_id: str,
    current_company=Depends(get_current_company)
):
    """Clona configuración de un mercado como nuevo tenant"""
    if getattr(current_company, 'role', None) != 'admin' and getattr(current_company, 'is_admin', False) is not True:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requiere rol de administrador"
        )
    
    if market_id not in MARKET_CONFIGS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mercado '{market_id}' no encontrado"
        )
    
    if tenant_id in WhiteLabelService._tenants:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Tenant '{tenant_id}' ya existe"
        )
    
    config = MARKET_CONFIGS[market_id]
    WhiteLabelService.register_tenant(tenant_id, config)
    
    return WhiteLabelResponse(
        tenant_id=tenant_id,
        config=config.model_dump(),
        css_variables=WhiteLabelService.generate_css_variables(config),
        manifest=WhiteLabelService.generate_manifest_json(config)
    )
