"""
Conflict Zero - Founder Compliance Endpoint
/founder/compliance - El "miedo" que mantiene al Founder enganchado
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from typing import List
from datetime import datetime, timedelta

from app.models import Company, Invite, CompanyHierarchy
from app.core.database import get_db
from app.core.security import get_current_company

router = APIRouter(prefix="/api/v2/founder", tags=["Founder Compliance"])


@router.get(
    "/compliance",
    summary="Estado de cumplimiento contractual (El Miedo)",
    description="""
    Retorna el estado de cumplimiento del Founder respecto a su obligación 
    contractual de exigir el Sello a su cadena de subcontratistas.
    
    Estados posibles:
    - sin_obligacion: Aún no firma contrato
    - sin_invitados: Debe subir lista de subcontratistas
    - cumpliendo: 50%+ de conversión (excelente)
    - en_riesgo: <50% conversión, pero tiempo disponible
    - riesgo_inminente: <7 días para mantener beneficio
    """
)
async def get_founder_compliance(
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db)
):
    """
    Endpoint crítico para el lock-in del Founder.
    Muestra: "Si no cumples, pierdes tu beneficio en X días"
    """
    # Verificar que es Founder
    if not current_company.is_founder:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo Fundadores pueden acceder a este endpoint"
        )
    
    # Calcular métricas de invitaciones
    invites_stats = db.query(
        func.count(Invite.id).label('total_invitados'),
        func.count(case([(Invite.status == 'paid', 1)])).label('registrados'),
        func.count(case([(Invite.status == 'registered', 1)])).label('registrados_no_pagados'),
        func.count(case([(Invite.status.in_(['sent', 'opened', 'clicked']), 1)])).label('pendientes'),
        func.sum(case([(Invite.status == 'paid', Invite.monthly_value)], else_=0)).label('valor_mensual')
    ).filter(
        Invite.inviter_id == current_company.id,
        Invite.deleted_at.is_(None)
    ).first()
    
    total_invitados = invites_stats.total_invitados or 0
    registrados = invites_stats.registrados or 0
    registrados_no_pagados = invites_stats.registrados_no_pagados or 0
    pendientes = invites_stats.pendientes or 0
    valor_mensual = float(invites_stats.valor_mensual or 0)
    
    # Calcular tasa de conversión
    tasa_conversion = round((registrados / total_invitados * 100), 1) if total_invitados > 0 else 0
    
    # Determinar estado de cumplimiento
    dias_restantes = None
    if current_company.founder_expires_at:
        dias_restantes = (current_company.founder_expires_at - datetime.utcnow()).days
    
    if not current_company.contractual_obligation:
        estado_cumplimiento = "sin_obligacion"
        mensaje_alerta = "Pendiente de firma de contrato de obligación contractual"
        nivel_urgencia = "info"
    elif total_invitados == 0:
        estado_cumplimiento = "sin_invitados"
        mensaje_alerta = "Debe subir lista de subcontratistas para cumplir con el programa"
        nivel_urgencia = "warning"
    elif registrados >= total_invitados * 0.5:
        estado_cumplimiento = "cumpliendo"
        mensaje_alerta = "¡Excelente! Estás cumpliendo con tu obligación contractual"
        nivel_urgencia = "success"
    elif dias_restantes is not None and dias_restantes <= 7:
        estado_cumplimiento = "riesgo_inminente"
        mensaje_alerta = f"CRÍTICO: Te faltan {dias_restantes} días para mantener tu beneficio Founder"
        nivel_urgencia = "critical"
    else:
        estado_cumplimiento = "en_riesgo"
        faltantes = int(total_invitados * 0.5) - registrados
        mensaje_alerta = f"Necesitas {faltantes} conversiones más para cumplir. {pendientes} pendientes de respuesta."
        nivel_urgencia = "warning"
    
    # Calcular proyección
    proyeccion_30_dias = valor_mensual * 1.2 if tasa_conversion > 30 else valor_mensual
    
    return {
        "company": {
            "id": str(current_company.id),
            "razon_social": current_company.razon_social,
            "public_slug": current_company.public_slug,
            "is_founder": current_company.is_founder,
            "founder_expires_at": current_company.founder_expires_at.isoformat() if current_company.founder_expires_at else None,
            "contractual_obligation": current_company.contractual_obligation,
            "contractual_signed_at": current_company.contractual_signed_at.isoformat() if current_company.contractual_signed_at else None
        },
        "metricas": {
            "subcontratistas_obligados": total_invitados,
            "registrados": registrados,
            "registrados_no_pagados": registrados_no_pagados,
            "pendientes": pendientes,
            "tasa_conversion_porcentaje": tasa_conversion,
            "valor_mensual_generado": valor_mensual,
            "proyeccion_30_dias": proyeccion_30_dias
        },
        "cumplimiento": {
            "estado": estado_cumplimiento,
            "mensaje": mensaje_alerta,
            "nivel_urgencia": nivel_urgencia,
            "dias_restantes_founder": dias_restantes,
            "meta_conversion": 50,  # 50% es la meta
            "faltantes_para_meta": max(0, int(total_invitados * 0.5) - registrados)
        },
        "acciones_requeridas": _get_acciones_requeridas(
            estado_cumplimiento, 
            pendientes, 
            current_company.contractual_obligation
        ),
        "ultima_actualizacion": datetime.utcnow().isoformat()
    }


def _get_acciones_requeridas(estado: str, pendientes: int, tiene_obligacion: bool) -> List[dict]:
    """Genera lista de acciones basada en el estado"""
    acciones = []
    
    if not tiene_obligacion:
        acciones.append({
            "tipo": "urgente",
            "accion": "firmar_contrato",
            "titulo": "Firmar contrato de obligación contractual",
            "descripcion": "Contacta a tu account manager para firmar el compromiso",
            "cta": "Contactar ahora",
            "url": "/contacto"
        })
    
    if estado == "sin_invitados":
        acciones.append({
            "tipo": "urgente",
            "accion": "subir_csv",
            "titulo": "Subir lista de subcontratistas",
            "descripcion": "Sube un CSV con los RUCs de tus subcontratistas para enviar invitaciones",
            "cta": "Subir CSV",
            "url": "/invites/upload"
        })
    
    if pendientes > 0 and estado in ["en_riesgo", "riesgo_inminente"]:
        acciones.append({
            "tipo": "recordatorio",
            "accion": "enviar_recordatorios",
            "titulo": f"Enviar recordatorios a {pendientes} subcontratistas pendientes",
            "descripcion": "Envía emails de 'Tu cliente te exige verificación'",
            "cta": "Enviar recordatorios",
            "url": "/invites/enforce"
        })
    
    if estado == "cumpliendo":
        acciones.append({
            "tipo": "optimizacion",
            "accion": "mejorar_red",
            "titulo": "Expandir red de subcontratistas",
            "descripcion": "Estás cumpliendo bien. ¿Tienes más subcontratistas para invitar?",
            "cta": "Agregar más",
            "url": "/invites/new"
        })
    
    return acciones


@router.get(
    "/compliance/detalle-invites",
    summary="Detalle de cada invitación (para gestión)",
    description="Lista detallada de cada subcontratista invitado con su estado"
)
async def get_founder_invites_detail(
    status: str = None,
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db)
):
    """Lista detallada de invitaciones para gestión del Founder"""
    
    if not current_company.is_founder:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo Fundadores pueden acceder"
        )
    
    query = db.query(Invite).filter(
        Invite.inviter_id == current_company.id,
        Invite.deleted_at.is_(None)
    )
    
    if status:
        query = query.filter(Invite.status == status)
    
    invites = query.order_by(Invite.created_at.desc()).all()
    
    return {
        "total": len(invites),
        "invites": [
            {
                "id": str(inv.id),
                "invite_code": inv.invite_code,
                "invitee_email": inv.invitee_email,
                "invitee_company_name": inv.invitee_company_name,
                "status": inv.status,
                "expected_plan": inv.expected_plan,
                "monthly_value": float(inv.monthly_value) if inv.monthly_value else None,
                "sent_at": inv.sent_at.isoformat() if inv.sent_at else None,
                "opened_at": inv.opened_at.isoformat() if inv.opened_at else None,
                "registered_at": inv.registered_at.isoformat() if inv.registered_at else None,
                "converted_to_paid_at": inv.converted_to_paid_at.isoformat() if inv.converted_to_paid_at else None,
                "enforcement_emails_sent": inv.enforcement_emails_sent,
                "conversion_deadline": inv.conversion_deadline.isoformat() if inv.conversion_deadline else None,
                "dias_desde_envio": (datetime.utcnow() - inv.sent_at).days if inv.sent_at else None
            }
            for inv in invites
        ]
    }


@router.post(
    "/compliance/enviar-recordatorios",
    summary="Enviar emails de presión a pendientes",
    description="Envía recordatorios 'Tu cliente te exige' a subcontratistas pendientes"
)
async def send_enforcement_emails(
    invite_codes: List[str],
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db)
):
    """
    Envía emails de presión a subcontratistas que no han respondido.
    Incrementa el contador enforcement_emails_sent.
    """
    if not current_company.is_founder:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo Fundadores pueden acceder"
        )
    
    if not current_company.contractual_obligation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Debes firmar el contrato de obligación contractual primero"
        )
    
    enviados = 0
    for code in invite_codes:
        invite = db.query(Invite).filter(
            Invite.invite_code == code,
            Invite.inviter_id == current_company.id,
            Invite.status.in_(['sent', 'opened', 'clicked'])
        ).first()
        
        if invite:
            # TODO: Enviar email real aquí
            invite.send_enforcement_email()
            enviados += 1
    
    db.commit()
    
    return {
        "enviados": enviados,
        "mensaje": f"Se enviaron {enviados} recordatorios de cumplimiento",
        "nota": "Los subcontratistas recibirán email de 'Tu cliente te exige verificación'"
    }


@router.get(
    "/compliance/resumen-ejecutivo",
    summary="Resumen para dashboard ejecutivo",
    description="Resumen de una línea para mostrar en dashboard principal"
)
async def get_compliance_summary(
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db)
):
    """Resumen ultra-conciso para el dashboard"""
    
    if not current_company.is_founder:
        return {"visible": False}
    
    stats = db.query(
        func.count(Invite.id).label('total'),
        func.count(case([(Invite.status == 'paid', 1)])).label('pagados')
    ).filter(
        Invite.inviter_id == current_company.id,
        Invite.deleted_at.is_(None)
    ).first()
    
    total = stats.total or 0
    pagados = stats.pagados or 0
    
    dias = None
    if current_company.founder_expires_at:
        dias = (current_company.founder_expires_at - datetime.utcnow()).days
    
    # Mensaje de una línea
    if not current_company.contractual_obligation:
        mensaje = "⏳ Firma pendiente: Contacta a tu account manager"
        color = "yellow"
    elif total == 0:
        mensaje = "📤 Acción requerida: Sube tu lista de subcontratistas"
        color = "orange"
    elif pagados >= total * 0.5:
        mensaje = f"✅ Cumpliendo: {pagados}/{total} verificados"
        color = "green"
    elif dias and dias <= 7:
        mensaje = f"🚨 {dias} días para mantener tu beneficio Founder"
        color = "red"
    else:
        faltan = int(total * 0.5) - pagados
        mensaje = f"⚠️ Necesitas {faltan} conversiones más ({pagados}/{total})"
        color = "orange"
    
    return {
        "visible": True,
        "mensaje": mensaje,
        "color": color,
        "dias_restantes": dias,
        "progreso_porcentaje": round((pagados / total * 100), 0) if total > 0 else 0
    }
