"""
Conflict Zero - Payments Router
Integración con pasarelas de pago peruanas (Culqi / Izipay)

P0: Pasarela de pagos real — bloqueante para cobro automático.
Actualmente soporta Culqi v2 (más popular en Perú).
Para producción: configurar CULQI_PUBLIC_KEY y CULQI_SECRET_KEY en env vars.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any
import hashlib
import hmac
import uuid
import os
import httpx

from app.core.database import get_db
from app.core.security import get_current_company
from app.core.rate_limit import rate_limited_auth
from app.core.config import settings
from app.models_v2 import Company, AuditLog

router = APIRouter(prefix="/payments", tags=["Pagos"])

# ============================================================
# CONFIGURACIÓN
# ============================================================

CULQI_PUBLIC_KEY = os.getenv("CULQI_PUBLIC_KEY", "")
CULQI_SECRET_KEY = os.getenv("CULQI_SECRET_KEY", "")
CULQI_API_BASE = "https://api.culqi.com/v2"

# Planes y precios en céntimos (Perú: PEN)
PLAN_PRICES_CENTS = {
    "essential": 40000,      # S/ 400.00
    "professional": 80000,   # S/ 800.00
    "enterprise": 250000,    # S/ 2,500.00
}

PLAN_NAMES = {
    "essential": "Essential",
    "professional": "Professional",
    "enterprise": "Enterprise",
}


# ============================================================
# SCHEMAS
# ============================================================

class CreateChargeRequest(BaseModel):
    """Request para crear un cargo (charge) con Culqi"""
    amount: int = Field(..., description="Monto en céntimos (ej: 40000 = S/ 400.00)")
    currency_code: str = Field(default="PEN", description="Moneda: PEN")
    email: str = Field(..., description="Email del cliente")
    source_id: str = Field(..., description="Token de tarjeta generado por Culqi.js")
    plan_type: str = Field(..., description="essential | professional | enterprise")
    description: Optional[str] = Field(default=None, description="Descripción del cargo")


class CreateChargeResponse(BaseModel):
    """Respuesta de cargo exitoso"""
    success: bool
    charge_id: str
    amount: int
    currency: str
    email: str
    plan_type: str
    plan_name: str
    status: str
    created_at: str
    receipt_url: Optional[str] = None


class PaymentMethodCreate(BaseModel):
    """Request para guardar un método de pago (card)"""
    card_token: str = Field(..., description="Token de tarjeta de Culqi.js")
    card_brand: Optional[str] = Field(default=None, description="Visa, Mastercard, etc.")
    card_last_four: Optional[str] = Field(default=None, description="Últimos 4 dígitos")
    is_default: bool = Field(default=True)


class SubscriptionCreateRequest(BaseModel):
    """Request para crear una suscripción"""
    plan_type: str = Field(..., description="essential | professional | enterprise")
    card_token: str = Field(..., description="Token de tarjeta")


class SubscriptionResponse(BaseModel):
    """Respuesta de suscripción"""
    success: bool
    subscription_id: Optional[str] = None
    plan_type: str
    status: str
    next_billing_date: Optional[str] = None
    message: str


class WebhookPayload(BaseModel):
    """Payload genérico para webhooks de Culqi"""
    object: str
    type: str
    data: Dict[str, Any]
    id: Optional[str] = None
    creation_date: Optional[int] = None


# ============================================================
# SERVICIO CULQI
# ============================================================

class CulqiService:
    """Servicio de integración con Culqi API v2"""

    @staticmethod
    def is_configured() -> bool:
        """Verifica si Culqi está configurado"""
        return bool(CULQI_SECRET_KEY and CULQI_SECRET_KEY.startswith("sk_"))

    @staticmethod
    async def create_charge(payload: dict) -> dict:
        """Crea un cargo (charge) en Culqi"""
        if not CulqiService.is_configured():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Pasarela de pagos no configurada. Contactar a soporte."
            )

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{CULQI_API_BASE}/charges",
                json=payload,
                headers={
                    "Authorization": f"Bearer {CULQI_SECRET_KEY}",
                    "Content-Type": "application/json",
                },
                timeout=30.0
            )

            if response.status_code != 201:
                error_data = response.json() if response.text else {"message": "Error desconocido"}
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error": "culqi_error",
                        "message": error_data.get("merchant_message", error_data.get("user_message", "Error en el pago")),
                        "culqi_code": error_data.get("code", "unknown")
                    }
                )

            return response.json()

    @staticmethod
    async def create_subscription(plan_type: str, card_token: str, email: str) -> dict:
        """
        Crea una suscripción recurrente en Culqi.
        En Culqi v2, las suscripciones se manejan vía Charges recurrentes
        o usando Culqi Subscriptions (si está habilitado).
        """
        # Nota: Culqi Subscriptions requiere activación por parte del merchant.
        # Para MVP: simulamos con un charge inicial y marcamos la empresa como subscribed.
        amount = PLAN_PRICES_CENTS.get(plan_type, 40000)

        charge_payload = {
            "amount": amount,
            "currency_code": "PEN",
            "email": email,
            "source_id": card_token,
            "description": f"Suscripción {PLAN_NAMES.get(plan_type, plan_type)} - Conflict Zero"
        }

        return await CulqiService.create_charge(charge_payload)

    @staticmethod
    async def get_charge(charge_id: str) -> dict:
        """Obtiene detalles de un cargo"""
        if not CulqiService.is_configured():
            raise HTTPException(status_code=503, detail="Pasarela no configurada")

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{CULQI_API_BASE}/charges/{charge_id}",
                headers={"Authorization": f"Bearer {CULQI_SECRET_KEY}"},
                timeout=10.0
            )
            if response.status_code == 200:
                return response.json()
            raise HTTPException(status_code=404, detail="Cargo no encontrado")


# ============================================================
# ENDPOINTS
# ============================================================

@router.get("/config", summary="Configuración pública de pagos")
async def get_payment_config():
    """
    Retorna configuración pública para el frontend de pagos.
    Incluye la public key de Culqi y los planes disponibles.
    """
    return {
        "gateway": "culqi" if CulqiService.is_configured() else "manual",
        "public_key": CULQI_PUBLIC_KEY if CULQI_PUBLIC_KEY.startswith("pk_") else None,
        "currency": "PEN",
        "currency_symbol": "S/",
        "plans": [
            {
                "id": "essential",
                "name": "Essential",
                "price_cents": PLAN_PRICES_CENTS["essential"],
                "price_formatted": "S/ 400.00",
                "description": "1,000 consultas/mes, historial 90 días, comparación 2 RUCs, PDF certs"
            },
            {
                "id": "professional",
                "name": "Professional",
                "price_cents": PLAN_PRICES_CENTS["professional"],
                "price_formatted": "S/ 800.00",
                "description": "5,000 consultas/mes, historial ilimitado, comparación 5 RUCs, API access, bulk upload, priority support"
            },
            {
                "id": "enterprise",
                "name": "Enterprise",
                "price_cents": PLAN_PRICES_CENTS["enterprise"],
                "price_formatted": "S/ 2,500.00",
                "description": "100,000 consultas/mes, todo lo anterior + webhooks, dedicated manager"
            }
        ],
        "is_live": CulqiService.is_configured()
    }


@router.post("/charge", response_model=CreateChargeResponse, summary="Crear cargo (pago único)")
async def create_charge(
    request: CreateChargeRequest,
    current_company: Company = Depends(rate_limited_auth),
    db: Session = Depends(get_db)
):
    """
    Procesa un pago único con Culqi.
    
    Flujo:
    1. Frontend genera token de tarjeta con Culqi.js (PK)
    2. Frontend envía token + plan a este endpoint
    3. Backend crea charge en Culqi con SK
    4. Si éxito: activar plan en la empresa
    """
    # Validar plan
    if request.plan_type not in PLAN_PRICES_CENTS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Plan inválido. Opciones: {list(PLAN_PRICES_CENTS.keys())}"
        )

    # Validar monto coincide con el plan
    expected_amount = PLAN_PRICES_CENTS[request.plan_type]
    if request.amount != expected_amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Monto incorrecto. Esperado: {expected_amount} céntimos para plan {request.plan_type}"
        )

    # Crear cargo en Culqi
    charge_payload = {
        "amount": request.amount,
        "currency_code": request.currency_code,
        "email": request.email,
        "source_id": request.source_id,
        "description": request.description or f"Pago plan {PLAN_NAMES.get(request.plan_type)} - Conflict Zero"
    }

    try:
        culqi_response = await CulqiService.create_charge(charge_payload)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"error": "payment_gateway_error", "message": str(e)}
        )

    # Actualizar empresa: activar plan
    current_company.plan_tier = request.plan_type
    current_company.plan_type = request.plan_type
    current_company.plan_activated_at = datetime.utcnow()
    current_company.max_monthly_queries = _get_plan_limit(request.plan_type)
    current_company.used_queries_this_month = 0
    current_company.is_active = True

    # Log de auditoría
    audit = AuditLog(
        id=uuid.uuid4(),
        company_id=current_company.id,
        action="plan_purchased",
        entity_type="company",
        entity_id=str(current_company.id),
        details={
            "plan_type": request.plan_type,
            "charge_id": culqi_response.get("id"),
            "amount": request.amount,
            "gateway": "culqi",
            "email": request.email
        }
    )
    db.add(audit)
    db.commit()
    db.refresh(current_company)

    return CreateChargeResponse(
        success=True,
        charge_id=culqi_response.get("id", "unknown"),
        amount=request.amount,
        currency=request.currency_code,
        email=request.email,
        plan_type=request.plan_type,
        plan_name=PLAN_NAMES.get(request.plan_type, request.plan_type),
        status=culqi_response.get("status", "unknown"),
        created_at=datetime.utcnow().isoformat(),
        receipt_url=culqi_response.get("receipt_url")
    )


@router.post("/subscription", response_model=SubscriptionResponse, summary="Crear suscripción recurrente")
async def create_subscription(
    request: SubscriptionCreateRequest,
    current_company: Company = Depends(rate_limited_auth),
    db: Session = Depends(get_db)
):
    """
    Crea una suscripción recurrente mensual.
    
    Nota: En Culqi, las suscripciones requieren configuración adicional.
    Este endpoint crea el charge inicial y marca la empresa como suscripta.
    """
    if request.plan_type not in PLAN_PRICES_CENTS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Plan inválido: {request.plan_type}"
        )

    email = current_company.email or current_company.contact_email or "cliente@czperu.com"

    try:
        culqi_response = await CulqiService.create_subscription(
            request.plan_type,
            request.card_token,
            email
        )
    except HTTPException:
        raise
    except Exception as e:
        return SubscriptionResponse(
            success=False,
            plan_type=request.plan_type,
            status="failed",
            message=f"Error al procesar suscripción: {str(e)}"
        )

    # Activar suscripción
    current_company.plan_tier = request.plan_type
    current_company.plan_type = request.plan_type
    current_company.plan_activated_at = datetime.utcnow()
    current_company.max_monthly_queries = _get_plan_limit(request.plan_type)
    current_company.used_queries_this_month = 0
    current_company.is_active = True
    current_company.subscription_status = "active"

    db.commit()
    db.refresh(current_company)

    return SubscriptionResponse(
        success=True,
        subscription_id=culqi_response.get("id"),
        plan_type=request.plan_type,
        status="active",
        next_billing_date=(datetime.utcnow().replace(day=1) + __import__('datetime').timedelta(days=32)).replace(day=1).isoformat(),
        message=f"Suscripción {PLAN_NAMES.get(request.plan_type)} activada exitosamente"
    )


@router.get("/history", summary="Historial de pagos")
async def get_payment_history(
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db),
    limit: int = 20,
    offset: int = 0
):
    """
    Obtiene el historial de pagos de la empresa desde los logs de auditoría.
    """
    logs = db.query(AuditLog).filter(
        AuditLog.company_id == current_company.id,
        AuditLog.action.in_(["plan_purchased", "plan_upgraded", "payment_failed"]),
        AuditLog.deleted_at.is_(None)
    ).order_by(AuditLog.created_at.desc()).offset(offset).limit(limit).all()

    items = []
    for log in logs:
        details = log.details or {}
        items.append({
            "id": str(log.id),
            "action": log.action,
            "plan_type": details.get("plan_type"),
            "amount_cents": details.get("amount"),
            "gateway": details.get("gateway", "unknown"),
            "charge_id": details.get("charge_id"),
            "created_at": log.created_at.isoformat() if log.created_at else None,
            "details": details
        })

    return {
        "items": items,
        "total": len(items),
        "has_more": len(items) == limit
    }


@router.post("/webhook/culqi", summary="Webhook de Culqi")
async def culqi_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Recibe webhooks de Culqi para eventos de pago.
    
    Eventos soportados:
    - charge.succeeded
    - charge.failed
    - subscription.active
    - subscription.canceled
    
    Verifica firma HMAC-SHA256 con CULQI_WEBHOOK_SECRET para seguridad.
    """
    # Leer body raw para verificar firma
    payload_body = await request.body()
    
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="JSON inválido")

    event_type = payload.get("type", "")
    data = payload.get("data", {})

    # Verificar firma del webhook con secret de Culqi
    signature = request.headers.get("X-Culqi-Signature")
    if settings.CULQI_WEBHOOK_SECRET:
        if not _verify_culqi_signature(payload_body, signature or "", settings.CULQI_WEBHOOK_SECRET):
            raise HTTPException(status_code=401, detail="Firma de webhook inválida")
    else:
        # En desarrollo sin secret configurado, loguear warning
        import logging
        logging.getLogger(__name__).warning("CULQI_WEBHOOK_SECRET no configurado — webhook sin verificación de firma")

    if event_type == "charge.succeeded":
        # Pago exitoso — ya manejado en /charge
        pass

    elif event_type == "charge.failed":
        # Pago fallido — log y notificar
        email = data.get("email", "")
        charge_id = data.get("id", "")

        # Buscar empresa por email
        company = db.query(Company).filter(
            (Company.email == email) | (Company.contact_email == email),
            Company.deleted_at.is_(None)
        ).first()

        if company:
            audit = AuditLog(
                id=uuid.uuid4(),
                company_id=company.id,
                action="payment_failed",
                entity_type="payment",
                entity_id=charge_id,
                details={
                    "charge_id": charge_id,
                    "email": email,
                    "error": data.get("outcome", {}).get("user_message", "Pago fallido"),
                    "gateway": "culqi"
                }
            )
            db.add(audit)
            db.commit()

    elif event_type == "subscription.canceled":
        # Suscripción cancelada — degradar a free (no existe free, marcar como inactivo)
        email = data.get("email", "")
        company = db.query(Company).filter(
            (Company.email == email) | (Company.contact_email == email),
            Company.deleted_at.is_(None)
        ).first()

        if company:
            company.subscription_status = "canceled"
            db.commit()

    return {"received": True, "type": event_type}


# ============================================================
# HELPERS
# ============================================================

def _verify_culqi_signature(payload_body: bytes, signature: str, secret: str) -> bool:
    """
    Verifica la firma HMAC-SHA256 del webhook de Culqi.
    Culqi envia la firma en el header X-Culqi-Signature.
    """
    if not secret or not signature:
        return False
    expected = hmac.new(
        secret.encode('utf-8'),
        payload_body,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


def _get_plan_limit(plan_type: str) -> int:
    """Retorna el límite mensual de consultas según plan"""
    limits = {
        "essential": 1000,
        "professional": 5000,
        "enterprise": 100000,
        "founder": 999999999
    }
    return limits.get(plan_type, 1000)
