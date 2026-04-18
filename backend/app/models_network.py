"""
Conflict Zero - Modelos adicionales para Mi Red (Supplier Watchlist)
Alertas y snapshots para monitoreo continuo de proveedores
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy import Column, String, Boolean, DateTime, Integer, Float, Text, ForeignKey, CheckConstraint, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB, BYTEA
from sqlalchemy.orm import relationship

from app.models_v2 import Base, hash_ruc


# ============================================================
# 13. SUPPLIER ALERTS (Alertas de cambios en proveedores)
# ============================================================

class SupplierAlert(Base):
    """
    Alertas generadas cuando se detectan cambios en proveedores monitoreados.
    """
    __tablename__ = "supplier_alerts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Empresa que recibe la alerta (el monitoreador)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # RUC del proveedor que cambió (hash para búsqueda)
    supplier_ruc_hash = Column(String(64), nullable=False, index=True)
    supplier_company_name = Column(String(255), nullable=False)
    
    # Tipo de alerta
    alert_type = Column(String(50), nullable=False)  # score_change, new_sanction, debt_increase, status_change, etc.
    
    # Detalles del cambio
    previous_score = Column(Integer)
    new_score = Column(Integer)
    previous_risk_level = Column(String(20))
    new_risk_level = Column(String(20))
    
    # Datos adicionales del cambio (JSON)
    change_details = Column(JSONB, default=dict)
    
    # Estado de la alerta
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime)
    
    # Severidad
    severity = Column(String(20), default="medium")  # low, medium, high, critical
    
    # Notificación
    email_sent = Column(Boolean, default=False)
    email_sent_at = Column(DateTime)
    webhook_sent = Column(Boolean, default=False)
    webhook_sent_at = Column(DateTime)
    
    # Soft delete
    deleted_at = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    company = relationship("Company")
    
    __table_args__ = (
        CheckConstraint("alert_type IN ('score_change', 'new_sanction', 'debt_increase', 'status_change', 'verification_expired', 'risk_level_change')", name="valid_alert_type"),
        CheckConstraint("severity IN ('low', 'medium', 'high', 'critical')", name="valid_severity"),
        Index('idx_supplier_alerts_company_unread', 'company_id', 'is_read'),  # Para queries rápidos de "alertas no leídas"
    )
    
    def mark_as_read(self):
        """Marca la alerta como leída"""
        self.is_read = True
        self.read_at = datetime.utcnow()
    
    def get_score_delta(self) -> Optional[int]:
        """Retorna el cambio en score (positivo = mejoró, negativo = empeoró)"""
        if self.previous_score is not None and self.new_score is not None:
            return self.new_score - self.previous_score
        return None


# ============================================================
# 14. COMPANY SNAPSHOTS (Snapshots para detectar cambios)
# ============================================================

class CompanySnapshot(Base):
    """
    Snapshot del estado de una empresa en un momento específico.
    Usado para detectar cambios entre verificaciones.
    """
    __tablename__ = "company_snapshots"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # RUC del proveedor (hash)
    ruc_hash = Column(String(64), nullable=False, index=True)
    company_name = Column(String(255))
    
    # Snapshot de datos
    score = Column(Integer)
    risk_level = Column(String(20))
    
    # Datos SUNAT
    sunat_debt = Column(Float, default=0)
    sunat_tax_status = Column(String(50))
    sunat_contributor_status = Column(String(50))
    
    # Datos OSCE/TCE
    osce_sanctions_count = Column(Integer, default=0)
    osce_sanctions_details = Column(JSONB, default=list)
    tce_sanctions_count = Column(Integer, default=0)
    tce_sanctions_details = Column(JSONB, default=list)
    
    # Datos completos en JSON
    full_data = Column(JSONB)
    
    # Metadatos
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)  # Cuándo deja de ser válido para comparación
    
    # Quién monitorea (opcional - si es parte de una red específica)
    monitoring_company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="SET NULL"))
    
    __table_args__ = (
        Index('idx_snapshots_ruc_created', 'ruc_hash', 'created_at'),  # Para obtener el snapshot más reciente de un RUC
    )

    def is_expired(self):
        """Verifica si el snapshot ha expirado."""
        if self.expires_at is None:
            return False
        return self.expires_at < datetime.utcnow()


# ============================================================
# 15. SUPPLIER NETWORK (Relación Company -> Proveedores monitoreados)
# ============================================================

class SupplierNetwork(Base):
    """
    Registra qué proveedores monitorea cada empresa.
    """
    __tablename__ = "supplier_networks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Empresa que monitorea
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # RUC del proveedor monitoreado
    supplier_ruc_hash = Column(String(64), nullable=False, index=True)
    supplier_ruc_encrypted = Column(BYTEA)
    supplier_company_name = Column(String(255))
    
    # Estado del monitoreo
    is_active = Column(Boolean, default=True)
    
    # Última verificación
    last_verified_at = Column(DateTime)
    last_snapshot_id = Column(UUID(as_uuid=True), ForeignKey("company_snapshots.id", ondelete="SET NULL"))
    
    # Configuración de alertas
    alert_on_score_change = Column(Boolean, default=True)
    alert_on_new_sanction = Column(Boolean, default=True)
    alert_on_debt_increase = Column(Boolean, default=True)
    alert_threshold = Column(Integer, default=10)  # Mínimo cambio en score para alertar
    
    # Notas
    notes = Column(Text)
    tags = Column(JSONB, default=list)  # Tags personalizados
    
    # Metadatos
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime)
    
    # Relaciones
    company = relationship("Company")
    last_snapshot = relationship("CompanySnapshot")
    
    __table_args__ = (
        UniqueConstraint('company_id', 'supplier_ruc_hash', name='unique_supplier_in_network'),
    )
    
    def soft_delete(self):
        """Soft delete del proveedor de la red"""
        self.deleted_at = datetime.utcnow()
        self.is_active = False
