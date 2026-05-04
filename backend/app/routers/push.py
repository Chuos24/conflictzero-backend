"""
Conflict Zero - Push Notifications Router
Registro y gestión de tokens Expo para push notifications
Fase 2
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
import logging

from app.core.database import get_db
from app.core.auth import get_current_company
from app.models import Company
from app.services.push_notifications import push_service

router = APIRouter(prefix="/push", tags=["push-notifications"])
logger = logging.getLogger(__name__)


class PushTokenRegister(BaseModel):
    push_token: str
    platform: str  # 'ios' | 'android'
    device_id: Optional[str] = None


class PushPreferences(BaseModel):
    enabled: bool
    alert_types: Optional[List[str]] = None
    quiet_hours_start: Optional[int] = None  # 0-23
    quiet_hours_end: Optional[int] = None    # 0-23


class PushTokenList(BaseModel):
    tokens: List[str]


@router.post("/register-token")
async def register_push_token(
    data: PushTokenRegister,
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_company)
):
    """Registra un push token Expo para la empresa actual."""
    
    if not current_company.push_tokens:
        current_company.push_tokens = []
    
    # Evitar duplicados
    if data.push_token not in current_company.push_tokens:
        current_company.push_tokens.append(data.push_token)
        db.commit()
        
        logger.info(f"Push token registrado para {current_company.ruc}")
        
        # Enviar notificación de confirmación
        try:
            await push_service.send_push(
                push_tokens=[data.push_token],
                title="🔔 Notificaciones activadas",
                body="Recibirás alertas cuando detectemos cambios en tus proveedores.",
                data={"type": "token_registered", "screen": "Settings"}
            )
        except Exception as e:
            logger.warning(f"No se pudo enviar confirmación de push: {e}")
    
    return {
        "status": "success",
        "message": "Token registrado",
        "token_count": len(current_company.push_tokens)
    }


@router.delete("/unregister-token")
async def unregister_push_token(
    push_token: str,
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_company)
):
    """Elimina un push token."""
    
    if current_company.push_tokens and push_token in current_company.push_tokens:
        current_company.push_tokens.remove(push_token)
        db.commit()
        
        logger.info(f"Push token eliminado para {current_company.ruc}")
    
    return {
        "status": "success",
        "message": "Token eliminado",
        "token_count": len(current_company.push_tokens or [])
    }


@router.get("/tokens")
async def list_push_tokens(
    current_company: Company = Depends(get_current_company)
):
    """Lista los tokens registrados (útil para debug)."""
    return {
        "tokens": current_company.push_tokens or [],
        "count": len(current_company.push_tokens or []),
        "enabled": current_company.push_enabled
    }


@router.patch("/preferences")
async def update_preferences(
    prefs: PushPreferences,
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_company)
):
    """Actualiza preferencias de notificaciones."""
    
    current_company.push_enabled = prefs.enabled
    db.commit()
    
    return {
        "status": "success",
        "enabled": prefs.enabled
    }


@router.post("/test")
async def test_push_notification(
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_company)
):
    """Envía una notificación de prueba."""
    
    if not current_company.push_tokens:
        raise HTTPException(
            status_code=400,
            detail="No hay tokens registrados. Registra un token primero."
        )
    
    result = await push_service.send_push(
        push_tokens=current_company.push_tokens,
        title="🧪 Notificación de prueba",
        body=f"Esta es una prueba desde Conflict Zero ({current_company.razon_social[:20]})",
        data={"type": "test", "screen": "Settings"},
        priority="high"
    )
    
    return {
        "status": "sent",
        "result": result
    }
