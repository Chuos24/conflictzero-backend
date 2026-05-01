"""
Servicio de monitoreo continuo de proveedores.
Fase 2 - Conflict Zero
"""
import json
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models_monitoring import (
    SupplierSnapshot, SupplierChange, MonitoringAlert, 
    MonitoringRule, MonitoringSchedule
)
from app.models_v2 import Company
from app.services.data_collection import collect_company_data
from app.services.scoring_service import calculate_risk_score


class MonitoringService:
    """Servicio principal para monitoreo de proveedores."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_snapshot(self, company_id: int, ruc: str) -> SupplierSnapshot:
        """Crea un nuevo snapshot de un proveedor."""
        # Recolectar datos actuales
        raw_data = collect_company_data(ruc)
        
        # Calcular scores
        risk_score = calculate_risk_score(raw_data)
        compliance_score = self._calculate_compliance_score(raw_data)
        
        # Determinar status
        status = self._determine_status(raw_data, risk_score)
        
        snapshot = SupplierSnapshot(
            company_id=company_id,
            ruc=ruc,
            raw_data=raw_data,
            risk_score=risk_score,
            compliance_score=compliance_score,
            status=status,
            snapshot_date=datetime.utcnow()
        )
        
        self.db.add(snapshot)
        self.db.commit()
        self.db.refresh(snapshot)
        
        return snapshot
    
    def detect_changes(self, company_id: int, new_snapshot: SupplierSnapshot) -> List[SupplierChange]:
        """Detecta cambios comparando con el snapshot anterior."""
        # Obtener snapshot anterior
        previous_snapshot = (
            self.db.query(SupplierSnapshot)
            .filter(
                SupplierSnapshot.company_id == company_id,
                SupplierSnapshot.id != new_snapshot.id
            )
            .order_by(desc(SupplierSnapshot.snapshot_date))
            .first()
        )
        
        if not previous_snapshot:
            return []
        
        changes = []
        old_data = previous_snapshot.raw_data or {}
        new_data = new_snapshot.raw_data or {}
        
        # Detectar sanciones nuevas
        old_sanctions = set(old_data.get("sanctions", []))
        new_sanctions = set(new_data.get("sanctions", []))
        added_sanctions = new_sanctions - old_sanctions
        
        for sanction in added_sanctions:
            changes.append(SupplierChange(
                snapshot_id=new_snapshot.id,
                company_id=company_id,
                change_type="sanction_added",
                description=f"Nueva sanción detectada: {sanction}",
                previous_value="",
                new_value=sanction,
                severity="critical"
            ))
        
        # Detectar cambio de representante
        old_rep = old_data.get("representative", "")
        new_rep = new_data.get("representative", "")
        if old_rep and new_rep and old_rep != new_rep:
            changes.append(SupplierChange(
                snapshot_id=new_snapshot.id,
                company_id=company_id,
                change_type="representative_changed",
                description=f"Cambio de representante legal: {old_rep} → {new_rep}",
                previous_value=old_rep,
                new_value=new_rep,
                severity="warning"
            ))
        
        # Detectar cambio de dirección
        old_address = old_data.get("address", "")
        new_address = new_data.get("address", "")
        if old_address and new_address and old_address != new_address:
            changes.append(SupplierChange(
                snapshot_id=new_snapshot.id,
                company_id=company_id,
                change_type="address_changed",
                description="Cambio de dirección fiscal detectado",
                previous_value=old_address,
                new_value=new_address,
                severity="info"
            ))
        
        # Detectar cambio de score de riesgo
        if previous_snapshot.risk_score and new_snapshot.risk_score:
            score_diff = new_snapshot.risk_score - previous_snapshot.risk_score
            if score_diff > 10:  # Subió más de 10 puntos
                changes.append(SupplierChange(
                    snapshot_id=new_snapshot.id,
                    company_id=company_id,
                    change_type="score_dropped",
                    description=f"Riesgo aumentó de {previous_snapshot.risk_score:.1f} a {new_snapshot.risk_score:.1f}",
                    previous_value=str(previous_snapshot.risk_score),
                    new_value=str(new_snapshot.risk_score),
                    severity="warning" if score_diff > 20 else "info"
                ))
        
        # Detectar cambio de estado
        if previous_snapshot.status != new_snapshot.status:
            changes.append(SupplierChange(
                snapshot_id=new_snapshot.id,
                company_id=company_id,
                change_type="status_changed",
                description=f"Estado cambió de {previous_snapshot.status} a {new_snapshot.status}",
                previous_value=previous_snapshot.status,
                new_value=new_snapshot.status,
                severity="critical" if new_snapshot.status == "sanctioned" else "warning"
            ))
        
        # Guardar cambios
        for change in changes:
            self.db.add(change)
        
        self.db.commit()
        return changes
    
    def generate_alerts(self, changes: List[SupplierChange]) -> List[MonitoringAlert]:
        """Genera alertas basadas en cambios detectados y reglas del usuario."""
        alerts = []
        
        for change in changes:
            # Obtener reglas activas para esta empresa
            rules = (
                self.db.query(MonitoringRule)
                .filter(
                    MonitoringRule.company_id == change.company_id,
                    MonitoringRule.is_active == True
                )
                .all()
            )
            
            # Si no hay reglas específicas, crear alerta por defecto para el owner
            if not rules:
                # Obtener owner de la empresa
                company = self.db.query(Company).filter(Company.id == change.company_id).first()
                if company and company.owner_id:
                    alert = MonitoringAlert(
                        change_id=change.id,
                        company_id=change.company_id,
                        user_id=company.owner_id,
                        title=f"Cambio detectado: {change.change_type}",
                        message=change.description,
                        channel="dashboard"
                    )
                    self.db.add(alert)
                    alerts.append(alert)
            else:
                for rule in rules:
                    if self._should_alert_for_rule(rule, change):
                        alert = MonitoringAlert(
                            change_id=change.id,
                            company_id=change.company_id,
                            user_id=rule.user_id,
                            title=f"Cambio detectado: {change.change_type}",
                            message=change.description,
                            channel="email" if rule.notify_email else "dashboard"
                        )
                        self.db.add(alert)
                        alerts.append(alert)
        
        self.db.commit()
        return alerts
    
    def run_daily_check(self, schedule_id: Optional[int] = None) -> Dict[str, Any]:
        """Ejecuta el monitoreo diario de todos los proveedores activos."""
        # Crear o actualizar schedule
        if schedule_id:
            schedule = self.db.query(MonitoringSchedule).filter(MonitoringSchedule.id == schedule_id).first()
        else:
            schedule = MonitoringSchedule(
                status="running",
                schedule_type="daily",
                started_at=datetime.utcnow()
            )
            self.db.add(schedule)
            self.db.commit()
            self.db.refresh(schedule)
        
        try:
            # Obtener todas las empresas activas
            companies = self.db.query(Company).filter(Company.is_active == True).all()
            
            schedule.total_suppliers = len(companies)
            self.db.commit()
            
            total_changes = 0
            total_alerts = 0
            
            for company in companies:
                try:
                    # Crear snapshot
                    snapshot = self.create_snapshot(company.id, company.ruc)
                    
                    # Detectar cambios
                    changes = self.detect_changes(company.id, snapshot)
                    
                    if changes:
                        # Generar alertas
                        alerts = self.generate_alerts(changes)
                        total_changes += len(changes)
                        total_alerts += len(alerts)
                    
                    schedule.checked_suppliers += 1
                    self.db.commit()
                    
                except Exception as e:
                    # Log error pero continuar con el siguiente
                    print(f"Error procesando {company.ruc}: {str(e)}")
                    continue
            
            # Actualizar schedule completado
            schedule.status = "completed"
            schedule.changes_detected = total_changes
            schedule.alerts_generated = total_alerts
            schedule.completed_at = datetime.utcnow()
            self.db.commit()
            
            return {
                "status": "success",
                "schedule_id": schedule.id,
                "total_suppliers": schedule.total_suppliers,
                "checked_suppliers": schedule.checked_suppliers,
                "changes_detected": total_changes,
                "alerts_generated": total_alerts
            }
            
        except Exception as e:
            schedule.status = "failed"
            schedule.error_message = str(e)
            schedule.completed_at = datetime.utcnow()
            self.db.commit()
            
            return {
                "status": "error",
                "schedule_id": schedule.id,
                "error": str(e)
            }
    
    def get_supplier_history(self, company_id: int, days: int = 30) -> List[Dict[str, Any]]:
        """Obtiene historial de snapshots de un proveedor."""
        since = datetime.utcnow() - timedelta(days=days)
        
        snapshots = (
            self.db.query(SupplierSnapshot)
            .filter(
                SupplierSnapshot.company_id == company_id,
                SupplierSnapshot.snapshot_date >= since
            )
            .order_by(SupplierSnapshot.snapshot_date)
            .all()
        )
        
        return [
            {
                "id": s.id,
                "date": s.snapshot_date.isoformat(),
                "risk_score": s.risk_score,
                "compliance_score": s.compliance_score,
                "status": s.status,
                "raw_data": s.raw_data
            }
            for s in snapshots
        ]
    
    def get_pending_alerts(self, user_id: int) -> List[MonitoringAlert]:
        """Obtiene alertas pendientes para un usuario."""
        return (
            self.db.query(MonitoringAlert)
            .filter(
                MonitoringAlert.user_id == user_id,
                MonitoringAlert.status.in_(["pending", "sent"])
            )
            .order_by(desc(MonitoringAlert.created_at))
            .all()
        )
    
    def mark_alert_read(self, alert_id: int) -> bool:
        """Marca una alerta como leída."""
        alert = self.db.query(MonitoringAlert).filter(MonitoringAlert.id == alert_id).first()
        if not alert:
            return False
        
        alert.status = "read"
        alert.read_at = datetime.utcnow()
        self.db.commit()
        return True
    
    def dismiss_alert(self, alert_id: int) -> bool:
        """Descarta una alerta."""
        alert = self.db.query(MonitoringAlert).filter(MonitoringAlert.id == alert_id).first()
        if not alert:
            return False
        
        alert.status = "dismissed"
        alert.dismissed_at = datetime.utcnow()
        self.db.commit()
        return True
    
    # Métodos privados
    
    def _calculate_compliance_score(self, raw_data: Dict[str, Any]) -> Optional[float]:
        """Calcula score de compliance basado en datos recolectados."""
        checks = raw_data.get("compliance_checks", [])
        if not checks:
            return None
        
        passed = sum(1 for c in checks if c.get("status") == "passed")
        return (passed / len(checks)) * 100
    
    def _determine_status(self, raw_data: Dict[str, Any], risk_score: Optional[float]) -> str:
        """Determina el estado general del proveedor."""
        sanctions = raw_data.get("sanctions", [])
        if sanctions:
            return "sanctioned"
        
        if risk_score is not None:
            if risk_score > 70:
                return "critical"
            elif risk_score > 40:
                return "warning"
        
        return "active"
    
    def _should_alert_for_rule(self, rule: MonitoringRule, change: SupplierChange) -> bool:
        """Determina si una regla debe generar alerta para un cambio."""
        conditions = rule.conditions or {}
        
        # Regla tipo 'all' alerta de todo
        if rule.rule_type == "all":
            return True
        
        # Regla específica por tipo de cambio
        if rule.rule_type == change.change_type:
            return True
        
        # Regla por threshold de score
        if rule.rule_type == "score_threshold":
            threshold = conditions.get("score_threshold", 50)
            if change.change_type == "score_dropped":
                try:
                    new_score = float(change.new_value or 0)
                    return new_score > threshold
                except (ValueError, TypeError):
                    return False
        
        return False


def calculate_severity(change_type: str, value: float) -> str:
    """Calcula la severidad de un cambio basado en su tipo y magnitud."""
    if change_type == "sanction_new":
        return "critical"
    if change_type == "risk_score_drop":
        if value >= 25.0:
            return "high"
        elif value >= 15.0:
            return "medium"
        elif value >= 5.0:
            return "low"
        return "info"
    if change_type == "address_change":
        return "medium"
    if change_type == "representative_changed":
        return "warning"
    if change_type == "status_changed":
        return "critical"
    return "info"


def detect_changes(old_data: dict, new_data: dict) -> List[Dict[str, Any]]:
    """Detecta cambios entre dos snapshots de datos (versión pura sin DB)."""
    changes = []

    # Detectar caída de score de riesgo
    old_score = old_data.get("risk_score")
    new_score = new_data.get("risk_score")
    if old_score is not None and new_score is not None:
        diff = old_score - new_score
        if diff > 0:
            changes.append({
                "change_type": "risk_score_drop",
                "severity": calculate_severity("risk_score_drop", diff),
                "old_value": str(old_score),
                "new_value": str(new_score)
            })

    # Detectar nueva sanción
    old_sanctions = old_data.get("sanctions_count", 0)
    new_sanctions = new_data.get("sanctions_count", 0)
    if new_sanctions > old_sanctions:
        changes.append({
            "change_type": "sanction_new",
            "severity": calculate_severity("sanction_new", float(new_sanctions - old_sanctions)),
            "old_value": str(old_sanctions),
            "new_value": str(new_sanctions)
        })

    # Detectar cambio de dirección
    old_address = old_data.get("address", "")
    new_address = new_data.get("address", "")
    if old_address and new_address and old_address != new_address:
        changes.append({
            "change_type": "address_change",
            "severity": calculate_severity("address_change", 1.0),
            "old_value": old_address,
            "new_value": new_address
        })

    return changes
