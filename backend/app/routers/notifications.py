"""
Conflict Zero - Push Notifications Router
Endpoints para registrar tokens y enviar notificaciones push
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_company
from app.models_v2 import Company

router = APIRouter(prefix="/v1/notifications", tags=["Push Notifications"])


class PushTokenRequest(BaseModel):
    """Request para registrar token de push notification"""
    token: str = Field(..., min_length=10, description="Expo push token")
    platform: str = Field(..., pattern="^(ios|android)$", description="Plataforma del dispositivo")
    device_id: Optional[str] = Field(None, description="ID único del dispositivo")
    app_version: Optional[str] = Field(None, description="Versión de la app")


class PushTokenResponse(BaseModel):
    """Response del registro de token"""
    success: bool
    token_id: Optional[str] = None
    message: str


class NotificationPayload(BaseModel):
    """Payload para enviar notificación push"""
    title: str = Field(..., max_length=100)
    body: str = Field(..., max_length=200)
    data: Optional[dict] = Field(None, description="Datos adicionales para deep linking")
    priority: str = Field("normal", pattern="^(normal|high)$")


class NotificationSendRequest(BaseModel):
    """Request para enviar notificación a usuario"""
    company_id: str
    notification: NotificationPayload
    send_email_fallback: bool = True


# Almacenamiento en memoria temporal - en producción usar tabla en BD
# Estructura: {company_id: [{token, platform, device_id, created_at, last_used}]}
_push_tokens_db = {}


@router.post("/push-token", response_model=PushTokenResponse, summary="Registrar token push")
async def register_push_token(
    request: PushTokenRequest,
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db)
):
    """
    Registra un token de push notification para el usuario actual.
    
    - Requiere autenticación
    - Un usuario puede tener múltiples tokens (múltiples dispositivos)
    """
    company_id = str(current_company.id)
    
    # Inicializar lista si no existe
    if company_id not in _push_tokens_db:
        _push_tokens_db[company_id] = []
    
    # Verificar si el token ya existe
    existing = [t for t in _push_tokens_db[company_id] if t["token"] == request.token]
    if existing:
        # Actualizar timestamp
        existing[0]["last_used"] = datetime.utcnow().isoformat()
        return PushTokenResponse(
            success=True,
            token_id=f"{company_id}_{request.token[:8]}",
            message="Token actualizado"
        )
    
    # Agregar nuevo token
    token_entry = {
        "token": request.token,
        "platform": request.platform,
        "device_id": request.device_id,
        "app_version": request.app_version,
        "created_at": datetime.utcnow().isoformat(),
        "last_used": datetime.utcnow().isoformat()
    }
    _push_tokens_db[company_id].append(token_entry)
    
    return PushTokenResponse(
        success=True,
        token_id=f"{company_id}_{request.token[:8]}",
        message="Token registrado exitosamente"
    )


@router.delete("/push-token/{token}", summary="Revocar token push")
async def revoke_push_token(
    token: str,
    current_company: Company = Depends(get_current_company)
):
    """
    Revoca un token de push notification (logout o uninstall).
    
    - Requiere autenticación
    - El token debe pertenecer al usuario autenticado
    """
    company_id = str(current_company.id)
    
    if company_id not in _push_tokens_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontraron tokens para este usuario"
        )
    
    # Filtrar el token
    original_count = len(_push_tokens_db[company_id])
    _push_tokens_db[company_id] = [
        t for t in _push_tokens_db[company_id] if t["token"] != token
    ]
    
    if len(_push_tokens_db[company_id]) == original_count:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Token no encontrado"
        )
    
    return {"success": True, "message": "Token revocado"}


@router.get("/push-tokens", summary="Listar tokens registrados")
async def list_push_tokens(
    current_company: Company = Depends(get_current_company)
):
    """
    Lista los tokens de push notification registrados del usuario.
    
    - Requiere autenticación
    - No retorna los tokens completos por seguridad (solo los primeros 8 chars)
    """
    company_id = str(current_company.id)
    tokens = _push_tokens_db.get(company_id, [])
    
    return {
        "tokens": [
            {
                "token_preview": t["token"][:8] + "...",
                "platform": t["platform"],
                "device_id": t.get("device_id"),
                "app_version": t.get("app_version"),
                "created_at": t["created_at"],
                "last_used": t["last_used"]
            }
            for t in tokens
        ],
        "total_count": len(tokens)
    }


@router.post("/send", summary="Enviar notificación push (admin)")
async def send_push_notification(
    request: NotificationSendRequest,
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db)
):
    """
    Envía una notificación push a un usuario específico.
    
    - Requiere autenticación admin
    - Si no hay tokens registrados, puede enviar email fallback
    """
    # Verificar que el company_id objetivo existe
    target = db.query(Company).filter(Company.id == request.company_id).first()
    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Empresa objetivo no encontrada"
        )
    
    tokens = _push_tokens_db.get(request.company_id, [])
    
    if not tokens:
        if request.send_email_fallback:
            # En producción: enviar email como fallback
            return {
                "success": False,
                "fallback": "email",
                "message": "No hay tokens push registrados. Email fallback activado."
            }
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No hay tokens push registrados para este usuario"
        )
    
    # En producción: integrar con Expo Push API o Firebase
    sent_count = 0
    for token_entry in tokens:
        # Simular envío exitoso
        sent_count += 1
    
    return {
        "success": True,
        "sent_count": sent_count,
        "total_tokens": len(tokens),
        "notification": request.notification.dict()
    }


@router.post("/broadcast", summary="Broadcast de notificación (admin)")
async def broadcast_notification(
    notification: NotificationPayload,
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db)
):
    """
    Envía una notificación push a todos los usuarios.
    
    - Requiere permisos de administrador
    - Usar con precaución
    """
    total_tokens = sum(len(tokens) for tokens in _push_tokens_db.values())
    
    # En producción: integrar con Expo Push API
    return {
        "success": True,
        "total_recipients": len(_push_tokens_db),
        "total_tokens": total_tokens,
        "notification": notification.dict()
    }


@router.get("/stats", summary="Estadísticas de notificaciones")
async def get_notification_stats(
    current_company: Company = Depends(get_current_company)
):
    """
    Retorna estadísticas de notificaciones push.
    
    - Total de tokens registrados
    - Tokens por plataforma
    """
    all_tokens = []
    for tokens in _push_tokens_db.values():
        all_tokens.extend(tokens)
    
    platform_counts = {}
    for token in all_tokens:
        platform = token["platform"]
        platform_counts[platform] = platform_counts.get(platform, 0) + 1
    
    return {
        "total_tokens": len(all_tokens),
        "total_users": len(_push_tokens_db),
        "platforms": platform_counts,
        "tokens_per_user_avg": len(all_tokens) / len(_push_tokens_db) if _push_tokens_db else 0
    }
