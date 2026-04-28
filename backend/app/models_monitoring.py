"""
Modelos para el sistema de monitoreo continuo de proveedores.
Fase 2 - Conflict Zero
"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, DateTime, Text, Boolean, 
    ForeignKey, JSON, Float, Index
)
from sqlalchemy.orm import relationship
from app.core.database import Base


class SupplierSnapshot(Base):
    """Snapshot periódico del estado de un proveedor."""
    __tablename__ = "supplier_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    ruc = Column(String(11), nullable=False, index=True)
    
    # Datos capturados
    raw_data = Column(JSON, default=dict, nullable=False)
    
    # Scores calculados
    risk_score = Column(Float, nullable=True)
    compliance_score = Column(Float, nullable=True)
    
    # Estado general
    status = Column(String(20), default="active")  # active, warning, critical, sanctioned
    
    # Metadatos
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    snapshot_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relaciones
    company = relationship("Company", back_populates="snapshots")
    changes = relationship("SupplierChange", back_populates="snapshot", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_snapshot_company_date", "company_id", "snapshot_date"),
    )


class SupplierChange(Base):
    """Registro de cambios detectados entre snapshots."""
    __tablename__ = "supplier_changes"

    id = Column(Integer, primary_key=True, index=True)
    snapshot_id = Column(Integer, ForeignKey("supplier_snapshots.id", ondelete="CASCADE"), nullable=False)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    
    # Tipo de cambio
    change_type = Column(String(50), nullable=False, index=True)
    # Ejemplos: "sanction_added", "representative_changed", "address_changed",
    #           "score_dropped", "compliance_expired", "new_verification"
    
    # Descripción legible
    description = Column(Text, nullable=False)
    
    # Datos antes/después
    previous_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    
    # Severidad
    severity = Column(String(20), default="info")  # info, warning, critical
    
    # Estado de alerta
    alert_sent = Column(Boolean, default=False)
    alert_sent_at = Column(DateTime, nullable=True)
    
    # Metadatos
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relaciones
    snapshot = relationship("SupplierSnapshot", back_populates="changes")
    company = relationship("Company", back_populates="changes")
    alerts = relationship("MonitoringAlert", back_populates="change", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_change_company_type", "company_id", "change_type"),
        Index("idx_change_severity", "severity", "alert_sent"),
    )


class MonitoringAlert(Base):
    """Alertas generadas por cambios en proveedores."""
    __tablename__ = "monitoring_alerts"

    id = Column(Integer, primary_key=True, index=True)
    change_id = Column(Integer, ForeignKey("supplier_changes.id", ondelete="CASCADE"), nullable=False)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Configuración de la alerta
    channel = Column(String(20), default="email")  # email, dashboard, webhook, push
    
    # Estado
    status = Column(String(20), default="pending")  # pending, sent, read, dismissed
    
    # Contenido
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    
    # Tracking
    sent_at = Column(DateTime, nullable=True)
    read_at = Column(DateTime, nullable=True)
    dismissed_at = Column(DateTime, nullable=True)
    
    # Metadatos
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relaciones
    change = relationship("SupplierChange", back_populates="alerts")
    company = relationship("Company", back_populates="monitoring_alerts")
    user = relationship("User", back_populates="monitoring_alerts")
    
    __table_args__ = (
        Index("idx_alert_user_status", "user_id", "status"),
        Index("idx_alert_company", "company_id"),
    )


class MonitoringRule(Base):
    """Reglas personalizadas de monitoreo por usuario/empresa."""
    __tablename__ = "monitoring_rules"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=True)
    
    # Qué monitorear
    rule_type = Column(String(50), nullable=False)  # all, sanctions, representatives, score_threshold, compliance_expiry
    
    # Condiciones
    conditions = Column(JSON, default=dict, nullable=False)
    # Ejemplo: {"score_threshold": 30, "compliance_days_before": 30}
    
    # Canales de notificación
    notify_email = Column(Boolean, default=True)
    notify_dashboard = Column(Boolean, default=True)
    notify_webhook = Column(Boolean, default=False)
    webhook_url = Column(String(500), nullable=True)
    
    # Frecuencia
    frequency = Column(String(20), default="daily")  # realtime, daily, weekly
    
    # Estado
    is_active = Column(Boolean, default=True)
    
    # Metadatos
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    user = relationship("User", back_populates="monitoring_rules")
    company = relationship("Company", back_populates="monitoring_rules")


class MonitoringSchedule(Base):
    """Programación de ejecuciones del monitoreo."""
    __tablename__ = "monitoring_schedules"

    id = Column(Integer, primary_key=True, index=True)
    
    # Estado de la ejecución
    status = Column(String(20), default="scheduled")  # scheduled, running, completed, failed
    
    # Tipo de ejecución
    schedule_type = Column(String(20), default="daily")  # daily, manual, onboarding
    
    # Métricas
    total_suppliers = Column(Integer, default=0)
    checked_suppliers = Column(Integer, default=0)
    changes_detected = Column(Integer, default=0)
    alerts_generated = Column(Integer, default=0)
    
    # Errores
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        Index("idx_schedule_status", "status", "created_at"),
    )
