"""
Router API para monitoreo continuo de proveedores.
Fase 2 - Conflict Zero
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.services.monitoring_service import MonitoringService
from app.models_monitoring import (
    SupplierSnapshot, SupplierChange, MonitoringAlert, 
    MonitoringRule, MonitoringSchedule
)
from app.models_v2 import User

router = APIRouter(prefix="/api/v2/monitoring", tags=["monitoring"])


def get_monitoring_service(db: Session = Depends(get_db)) -> MonitoringService:
    return MonitoringService(db)


# ───────────────────────────────────────────────
# Snapshots
# ───────────────────────────────────────────────

@router.post("/snapshots/{company_id}", response_model=dict)
def create_snapshot(
    company_id: int,
    background_tasks: BackgroundTasks,
    service: MonitoringService = Depends(get_monitoring_service),
    current_user: User = Depends(get_current_user)
):
    """Crea un snapshot manual de un proveedor."""
    from app.models_v2 import Company
    db = service.db
    
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    
    snapshot = service.create_snapshot(company.id, company.ruc)
    
    # Detectar cambios en background
    background_tasks.add_task(service.detect_changes, company.id, snapshot)
    
    return {
        "id": snapshot.id,
        "company_id": snapshot.company_id,
        "ruc": snapshot.ruc,
        "status": snapshot.status,
        "risk_score": snapshot.risk_score,
        "compliance_score": snapshot.compliance_score,
        "snapshot_date": snapshot.snapshot_date.isoformat()
    }


@router.get("/snapshots/{company_id}/history", response_model=List[dict])
def get_snapshot_history(
    company_id: int,
    days: int = Query(default=30, ge=1, le=365),
    service: MonitoringService = Depends(get_monitoring_service),
    current_user: User = Depends(get_current_user)
):
    """Obtiene historial de snapshots de un proveedor."""
    return service.get_supplier_history(company_id, days)


# ───────────────────────────────────────────────
# Cambios
# ───────────────────────────────────────────────

@router.get("/changes", response_model=List[dict])
def list_changes(
    company_id: Optional[int] = Query(None),
    severity: Optional[str] = Query(None, regex="^(info|warning|critical)$"),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lista cambios detectados en proveedores."""
    query = db.query(SupplierChange)
    
    if company_id:
        query = query.filter(SupplierChange.company_id == company_id)
    if severity:
        query = query.filter(SupplierChange.severity == severity)
    
    changes = query.order_by(SupplierChange.created_at.desc()).limit(limit).all()
    
    return [
        {
            "id": c.id,
            "company_id": c.company_id,
            "change_type": c.change_type,
            "description": c.description,
            "severity": c.severity,
            "previous_value": c.previous_value,
            "new_value": c.new_value,
            "alert_sent": c.alert_sent,
            "created_at": c.created_at.isoformat()
        }
        for c in changes
    ]


@router.get("/changes/{change_id}", response_model=dict)
def get_change(
    change_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtiene detalle de un cambio específico."""
    change = db.query(SupplierChange).filter(SupplierChange.id == change_id).first()
    if not change:
        raise HTTPException(status_code=404, detail="Cambio no encontrado")
    
    return {
        "id": change.id,
        "company_id": change.company_id,
        "change_type": change.change_type,
        "description": change.description,
        "severity": change.severity,
        "previous_value": change.previous_value,
        "new_value": change.new_value,
        "alert_sent": change.alert_sent,
        "created_at": change.created_at.isoformat()
    }


# ───────────────────────────────────────────────
# Alertas
# ───────────────────────────────────────────────

@router.get("/alerts", response_model=List[dict])
def list_alerts(
    status: Optional[str] = Query(None, regex="^(pending|sent|read|dismissed)$"),
    limit: int = Query(default=50, ge=1, le=200),
    service: MonitoringService = Depends(get_monitoring_service),
    current_user: User = Depends(get_current_user)
):
    """Lista alertas del usuario actual."""
    query = service.db.query(MonitoringAlert).filter(
        MonitoringAlert.user_id == current_user.id
    )
    
    if status:
        query = query.filter(MonitoringAlert.status == status)
    
    alerts = query.order_by(MonitoringAlert.created_at.desc()).limit(limit).all()
    
    return [
        {
            "id": a.id,
            "change_id": a.change_id,
            "company_id": a.company_id,
            "title": a.title,
            "message": a.message,
            "channel": a.channel,
            "status": a.status,
            "created_at": a.created_at.isoformat(),
            "sent_at": a.sent_at.isoformat() if a.sent_at else None,
            "read_at": a.read_at.isoformat() if a.read_at else None
        }
        for a in alerts
    ]


@router.post("/alerts/{alert_id}/read", response_model=dict)
def mark_alert_read(
    alert_id: int,
    service: MonitoringService = Depends(get_monitoring_service),
    current_user: User = Depends(get_current_user)
):
    """Marca una alerta como leída."""
    success = service.mark_alert_read(alert_id)
    if not success:
        raise HTTPException(status_code=404, detail="Alerta no encontrada")
    return {"message": "Alerta marcada como leída"}


@router.post("/alerts/{alert_id}/dismiss", response_model=dict)
def dismiss_alert(
    alert_id: int,
    service: MonitoringService = Depends(get_monitoring_service),
    current_user: User = Depends(get_current_user)
):
    """Descarta una alerta."""
    success = service.dismiss_alert(alert_id)
    if not success:
        raise HTTPException(status_code=404, detail="Alerta no encontrada")
    return {"message": "Alerta descartada"}


# ───────────────────────────────────────────────
# Reglas de Monitoreo
# ───────────────────────────────────────────────

@router.get("/rules", response_model=List[dict])
def list_rules(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lista reglas de monitoreo del usuario."""
    rules = db.query(MonitoringRule).filter(
        MonitoringRule.user_id == current_user.id
    ).all()
    
    return [
        {
            "id": r.id,
            "company_id": r.company_id,
            "rule_type": r.rule_type,
            "conditions": r.conditions,
            "notify_email": r.notify_email,
            "notify_dashboard": r.notify_dashboard,
            "notify_webhook": r.notify_webhook,
            "webhook_url": r.webhook_url,
            "frequency": r.frequency,
            "is_active": r.is_active,
            "created_at": r.created_at.isoformat()
        }
        for r in rules
    ]


@router.post("/rules", response_model=dict)
def create_rule(
    rule_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Crea una nueva regla de monitoreo."""
    rule = MonitoringRule(
        user_id=current_user.id,
        company_id=rule_data.get("company_id"),
        rule_type=rule_data.get("rule_type", "all"),
        conditions=rule_data.get("conditions", {}),
        notify_email=rule_data.get("notify_email", True),
        notify_dashboard=rule_data.get("notify_dashboard", True),
        notify_webhook=rule_data.get("notify_webhook", False),
        webhook_url=rule_data.get("webhook_url"),
        frequency=rule_data.get("frequency", "daily")
    )
    
    db.add(rule)
    db.commit()
    db.refresh(rule)
    
    return {
        "id": rule.id,
        "rule_type": rule.rule_type,
        "is_active": rule.is_active,
        "created_at": rule.created_at.isoformat()
    }


@router.patch("/rules/{rule_id}", response_model=dict)
def update_rule(
    rule_id: int,
    rule_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Actualiza una regla de monitoreo."""
    rule = db.query(MonitoringRule).filter(
        MonitoringRule.id == rule_id,
        MonitoringRule.user_id == current_user.id
    ).first()
    
    if not rule:
        raise HTTPException(status_code=404, detail="Regla no encontrada")
    
    for key, value in rule_data.items():
        if hasattr(rule, key):
            setattr(rule, key, value)
    
    db.commit()
    db.refresh(rule)
    
    return {"message": "Regla actualizada", "id": rule.id}


@router.delete("/rules/{rule_id}", response_model=dict)
def delete_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Elimina una regla de monitoreo."""
    rule = db.query(MonitoringRule).filter(
        MonitoringRule.id == rule_id,
        MonitoringRule.user_id == current_user.id
    ).first()
    
    if not rule:
        raise HTTPException(status_code=404, detail="Regla no encontrada")
    
    db.delete(rule)
    db.commit()
    
    return {"message": "Regla eliminada"}


# ───────────────────────────────────────────────
# Schedule / Ejecuciones
# ───────────────────────────────────────────────

@router.post("/run", response_model=dict)
def run_monitoring(
    background_tasks: BackgroundTasks,
    service: MonitoringService = Depends(get_monitoring_service),
    current_user: User = Depends(get_current_user)
):
    """Ejecuta manualmente el monitoreo de todos los proveedores."""
    # Solo admins pueden ejecutar manualmente
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Solo administradores pueden ejecutar monitoreo manual")
    
    schedule = MonitoringSchedule(status="running", schedule_type="manual")
    service.db.add(schedule)
    service.db.commit()
    service.db.refresh(schedule)
    
    # Ejecutar en background
    background_tasks.add_task(service.run_daily_check, schedule.id)
    
    return {
        "message": "Monitoreo iniciado en background",
        "schedule_id": schedule.id
    }


@router.get("/schedules", response_model=List[dict])
def list_schedules(
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lista ejecuciones de monitoreo."""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Solo administradores pueden ver schedules")
    
    schedules = db.query(MonitoringSchedule).order_by(
        MonitoringSchedule.created_at.desc()
    ).limit(limit).all()
    
    return [
        {
            "id": s.id,
            "status": s.status,
            "schedule_type": s.schedule_type,
            "total_suppliers": s.total_suppliers,
            "checked_suppliers": s.checked_suppliers,
            "changes_detected": s.changes_detected,
            "alerts_generated": s.alerts_generated,
            "started_at": s.started_at.isoformat() if s.started_at else None,
            "completed_at": s.completed_at.isoformat() if s.completed_at else None,
            "created_at": s.created_at.isoformat()
        }
        for s in schedules
    ]


# ───────────────────────────────────────────────
# Dashboard Stats
# ───────────────────────────────────────────────

@router.get("/stats", response_model=dict)
def get_monitoring_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Estadísticas de monitoreo para el dashboard."""
    from sqlalchemy import func
    
    # Conteos
    total_snapshots = db.query(func.count(SupplierSnapshot.id)).scalar() or 0
    total_changes = db.query(func.count(SupplierChange.id)).scalar() or 0
    pending_alerts = db.query(func.count(MonitoringAlert.id)).filter(
        MonitoringAlert.user_id == current_user.id,
        MonitoringAlert.status == "pending"
    ).scalar() or 0
    
    # Cambios recientes por severidad
    critical_changes = db.query(func.count(SupplierChange.id)).filter(
        SupplierChange.severity == "critical"
    ).scalar() or 0
    warning_changes = db.query(func.count(SupplierChange.id)).filter(
        SupplierChange.severity == "warning"
    ).scalar() or 0
    
    # Último schedule
    last_schedule = db.query(MonitoringSchedule).order_by(
        MonitoringSchedule.created_at.desc()
    ).first()
    
    return {
        "total_snapshots": total_snapshots,
        "total_changes_detected": total_changes,
        "pending_alerts": pending_alerts,
        "critical_changes": critical_changes,
        "warning_changes": warning_changes,
        "last_run": {
            "id": last_schedule.id if last_schedule else None,
            "status": last_schedule.status if last_schedule else None,
            "completed_at": last_schedule.completed_at.isoformat() if last_schedule and last_schedule.completed_at else None
        }
    }
