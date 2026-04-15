"""
Webhooks Router - Notificaciones en tiempo real
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import hmac
import hashlib
import json

from app.core.database import get_db
from app.core.security import get_current_company
from app.models_v2 import Company, Webhook, WebhookDelivery
from app.services.email_service import send_email

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


@router.post("/register")
async def register_webhook(
    url: str,
    events: List[str],
    secret: Optional[str] = None,
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db)
):
    """Registrar un nuevo webhook para la empresa"""
    webhook = Webhook(
        company_id=current_company.id,
        url=url,
        events=events,
        secret=secret,
        is_active=True
    )
    db.add(webhook)
    db.commit()
    db.refresh(webhook)
    
    return {
        "id": webhook.id,
        "url": webhook.url,
        "events": webhook.events,
        "is_active": webhook.is_active,
        "created_at": webhook.created_at
    }


@router.get("/list")
async def list_webhooks(
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db)
):
    """Listar webhooks registrados"""
    webhooks = db.query(Webhook).filter(
        Webhook.company_id == current_company.id,
        Webhook.is_active == True
    ).all()
    
    return [
        {
            "id": w.id,
            "url": w.url,
            "events": w.events,
            "is_active": w.is_active,
            "created_at": w.created_at,
            "last_triggered": w.last_triggered
        }
        for w in webhooks
    ]


@router.delete("/{webhook_id}")
async def delete_webhook(
    webhook_id: str,
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db)
):
    """Eliminar un webhook"""
    webhook = db.query(Webhook).filter(
        Webhook.id == webhook_id,
        Webhook.company_id == current_company.id
    ).first()
    
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook no encontrado")
    
    webhook.is_active = False
    db.commit()
    
    return {"message": "Webhook eliminado"}


@router.post("/{webhook_id}/test")
async def test_webhook(
    webhook_id: str,
    background_tasks: BackgroundTasks,
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db)
):
    """Enviar evento de prueba al webhook"""
    webhook = db.query(Webhook).filter(
        Webhook.id == webhook_id,
        Webhook.company_id == current_company.id
    ).first()
    
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook no encontrado")
    
    payload = {
        "event": "test",
        "timestamp": datetime.utcnow().isoformat(),
        "data": {
            "message": "Este es un evento de prueba",
            "company": current_company.razon_social
        }
    }
    
    background_tasks.add_task(deliver_webhook, webhook, payload, db)
    
    return {"message": "Evento de prueba enviado"}


async def deliver_webhook(webhook: Webhook, payload: dict, db: Session):
    """Entregar webhook de forma asíncrona"""
    import httpx
    
    # Firmar payload si hay secreto
    headers = {
        "Content-Type": "application/json",
        "X-Webhook-ID": str(webhook.id),
        "X-Event-Type": payload.get("event", "unknown")
    }
    
    if webhook.secret:
        signature = hmac.new(
            webhook.secret.encode(),
            json.dumps(payload).encode(),
            hashlib.sha256
        ).hexdigest()
        headers["X-Webhook-Signature"] = f"sha256={signature}"
    
    # Registrar intento de entrega
    delivery = WebhookDelivery(
        webhook_id=webhook.id,
        payload=payload,
        status="pending"
    )
    db.add(delivery)
    db.commit()
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                webhook.url,
                json=payload,
                headers=headers
            )
        
        delivery.status = "delivered" if response.status_code < 400 else "failed"
        delivery.http_status = response.status_code
        delivery.response_body = response.text[:1000]  # Limitar tamaño
        webhook.last_triggered = datetime.utcnow()
        
    except Exception as e:
        delivery.status = "failed"
        delivery.response_body = str(e)[:1000]
    
    db.commit()
    
    # Notificar al usuario si falla
    if delivery.status == "failed":
        notify_webhook_failure(webhook, delivery, db)


def notify_webhook_failure(webhook: Webhook, delivery: WebhookDelivery, db: Session):
    """Notificar al usuario cuando un webhook falla"""
    # Contar fallos recientes
    recent_failures = db.query(WebhookDelivery).filter(
        WebhookDelivery.webhook_id == webhook.id,
        WebhookDelivery.status == "failed",
        WebhookDelivery.created_at >= datetime.utcnow() - timedelta(hours=24)
    ).count()
    
    # Solo notificar cada 5 fallos para no spamear
    if recent_failures % 5 == 0:
        company = db.query(Company).filter(Company.id == webhook.company_id).first()
        if company:
            send_email(
                to=company.email,
                subject="⚠️ Alerta: Tu webhook está fallando",
                template="webhook_failure",
                data={
                    "company_name": company.company_name,
                    "webhook_url": webhook.url,
                    "failure_count": recent_failures,
                    "last_error": delivery.response_body[:200]
                }
            )


@router.get("/{webhook_id}/deliveries")
async def get_webhook_deliveries(
    webhook_id: str,
    limit: int = 20,
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db)
):
    """Obtener historial de entregas de un webhook"""
    webhook = db.query(Webhook).filter(
        Webhook.id == webhook_id,
        Webhook.company_id == current_company.id
    ).first()
    
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook no encontrado")
    
    deliveries = db.query(WebhookDelivery).filter(
        WebhookDelivery.webhook_id == webhook_id
    ).order_by(
        WebhookDelivery.created_at.desc()
    ).limit(limit).all()
    
    return [
        {
            "id": d.id,
            "status": d.status,
            "http_status": d.http_status,
            "created_at": d.created_at,
            "event": d.payload.get("event", "unknown")
        }
        for d in deliveries
    ]
