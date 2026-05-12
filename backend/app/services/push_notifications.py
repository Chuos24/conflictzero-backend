import logging
from typing import Optional, List
from datetime import datetime, timezone
import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import Company

logger = logging.getLogger(__name__)


class PushNotificationService:
    """
    Servicio de Push Notifications para Conflict Zero.
    Usa Expo Push Notification Service para mobile.
    """
    
    EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"
    
    def __init__(self):
        self.enabled = bool(getattr(settings, 'EXPO_ACCESS_TOKEN', None))
    
    async def send_push(
        self,
        push_tokens: List[str],
        title: str,
        body: str,
        data: Optional[dict] = None,
        priority: str = "default"
    ) -> dict:
        """
        Envía push notification via Expo.
        
        Args:
            push_tokens: Lista de Expo push tokens
            title: Título de la notificación
            body: Cuerpo del mensaje
            data: Datos extras (deep link payload)
            priority: 'default' | 'normal' | 'high'
        """
        if not self.enabled:
            logger.warning("Push notifications deshabilitadas (sin EXPO_ACCESS_TOKEN)")
            return {"status": "disabled", "sent": 0}
        
        if not push_tokens:
            return {"status": "no_tokens", "sent": 0}
        
        messages = []
        for token in push_tokens:
            messages.append({
                "to": token,
                "title": title,
                "body": body,
                "data": data or {},
                "priority": priority,
                "sound": "default",
                "badge": 1
            })
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.EXPO_PUSH_URL,
                    json=messages,
                    headers={
                        "Accept": "application/json",
                        "Accept-Encoding": "gzip, deflate",
                        "Content-Type": "application/json"
                    },
                    timeout=30.0
                )
                
                result = response.json()
                
                if response.status_code == 200:
                    logger.info(f"Push enviado: {len(messages)} mensajes")
                    return {
                        "status": "success",
                        "sent": len(messages),
                        "details": result
                    }
                else:
                    logger.error(f"Error Expo push: {result}")
                    return {
                        "status": "error",
                        "sent": 0,
                        "error": result
                    }
                    
        except Exception as e:
            logger.error(f"Excepción enviando push: {e}")
            return {
                "status": "exception",
                "sent": 0,
                "error": str(e)
            }
    
    async def send_alert_notification(
        self,
        db: Session,
        company_id: int,
        alert_type: str,
        ruc: str,
        razon_social: str,
        severity: str,
        change_description: str
    ) -> dict:
        """
        Envía notificación de alerta de proveedor a dispositivos del usuario.
        """
        # Obtener push tokens de la empresa
        company = db.query(Company).filter(Company.id == company_id).first()
        
        if not company or not company.push_tokens:
            return {"status": "no_tokens", "reason": "company_without_tokens"}
        
        # Construir mensaje según severidad
        emoji_map = {
            "critical": "🔴",
            "high": "🟠",
            "medium": "🟡",
            "low": "🔵"
        }
        
        emoji = emoji_map.get(severity, "⚪")
        title = f"{emoji} Alerta: {razon_social[:30]}"
        body = f"{change_description[:100]}..."
        
        # Payload para deep link
        data = {
            "type": "supplier_alert",
            "alert_type": alert_type,
            "ruc": ruc,
            "company_id": company_id,
            "severity": severity,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "screen": "AlertDetail",
            "params": {"ruc": ruc, "alert_id": f"{company_id}_{ruc}_{datetime.now(timezone.utc).strftime('%Y%m%d')}"}
        }
        
        priority = "high" if severity in ["critical", "high"] else "default"
        
        return await self.send_push(
            push_tokens=company.push_tokens,
            title=title,
            body=body,
            data=data,
            priority=priority
        )
    
    async def send_welcome_notification(
        self,
        push_tokens: List[str],
        company_name: str
    ) -> dict:
        """Notificación de bienvenida."""
        return await self.send_push(
            push_tokens=push_tokens,
            title=f"🎉 Bienvenido a Conflict Zero",
            body=f"{company_name}, tu monitoreo de proveedores está activo.",
            data={"type": "welcome", "screen": "Dashboard"},
            priority="normal"
        )
    
    async def send_daily_summary(
        self,
        push_tokens: List[str],
        alerts_count: int,
        changes_count: int
    ) -> dict:
        """Resumen diario de alertas."""
        if alerts_count == 0:
            title = "✅ Sin alertas hoy"
            body = "Todos tus proveedores están estables."
        else:
            title = f"📊 {alerts_count} alertas detectadas"
            body = f"{changes_count} cambios en tus proveedores monitoreados."
        
        return await self.send_push(
            push_tokens=push_tokens,
            title=title,
            body=body,
            data={"type": "daily_summary", "screen": "Alerts"},
            priority="default"
        )


# Instancia singleton
push_service = PushNotificationService()
