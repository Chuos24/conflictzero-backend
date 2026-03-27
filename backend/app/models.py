"""
Conflict Zero - SQLAlchemy Models
Base de datos para monopolio B2B de verificación
"""

import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, String, Boolean, DateTime, Integer, Float, Text, ForeignKey, CheckConstraint, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

class Company(Base):
    """Empresas clientes (constructoras y subcontratistas)"""
    __tablename__ = "companies"
    
    ruc = Column(String(11), primary_key=True)
    razon_social = Column(String(255), nullable=False)
    direccion = Column(String(500))
    distrito = Column(String(100))
    provincia = Column(String(100))
    departamento = Column(String(100))
    
    # Plan y estado
    plan_tier = Column(String(20), nullable=False, default="bronze")
    status = Column(String(20), nullable=False, default="pending")
    is_founder = Column(Boolean, default=False)
    founder_expires_at = Column(DateTime)
    
    # Límites y uso
    max_monthly_queries = Column(Integer, default=1000)
    used_queries_this_month = Column(Integer, default=0)
    queries_reset_at = Column(DateTime, default=datetime.utcnow)
    
    # API
    api_key = Column(String(255), unique=True)
    api_key_created_at = Column(DateTime)
    
    # Contacto
    contact_email = Column(String(255), nullable=False)
    contact_name = Column(String(255))
    contact_phone = Column(String(50))
    
    # Tracking de invitaciones
    invited_by_code = Column(String(50))
    invite_depth = Column(Integer, default=0)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = Column(DateTime)
    
    # Relaciones
    sent_invites = relationship("Invite", foreign_keys="Invite.inviter_ruc", back_populates="inviter")
    verifications = relationship("VerificationRequest", back_populates="company")
    api_keys = relationship("ApiKey", back_populates="company")
    public_profile = relationship("PublicProfile", back_populates="company", uselist=False)
    
    __table_args__ = (
        CheckConstraint("plan_tier IN ('bronze', 'silver', 'gold', 'founder')", name="valid_plan_tier"),
        CheckConstraint("status IN ('active', 'cancelled', 'suspended', 'pending')", name="valid_status"),
    )


class FounderApplication(Base):
    """Aplicaciones al Programa Fundador"""
    __tablename__ = "founder_applications"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    company_ruc = Column(String(11), nullable=False)
    company_name = Column(String(255), nullable=False)
    
    contact_name = Column(String(255), nullable=False)
    contact_email = Column(String(255), nullable=False)
    contact_phone = Column(String(50))
    
    annual_volume = Column(String(20), nullable=False)
    subcontractor_count = Column(String(20), nullable=False)
    
    status = Column(String(20), default="pending")
    notes = Column(Text)
    reviewed_by = Column(String(255))
    reviewed_at = Column(DateTime)
    
    ip_address = Column(String(45))
    user_agent = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        CheckConstraint("annual_volume IN ('10-50M', '50-200M', '200M+')", name="valid_volume"),
        CheckConstraint("subcontractor_count IN ('5-20', '20-50', '50+')", name="valid_subcontractor_count"),
        CheckConstraint("status IN ('pending', 'under_review', 'approved', 'rejected', 'waitlisted')", name="valid_app_status"),
    )


class PublicProfile(Base):
    """Perfiles públicos - Lock-in de vergüenza"""
    __tablename__ = "public_profiles"
    
    ruc = Column(String(11), ForeignKey("companies.ruc", ondelete="CASCADE"), primary_key=True)
    
    display_name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False)
    
    sello_status = Column(String(20), default="expired")
    sello_expires_at = Column(DateTime)
    
    current_score = Column(Integer)
    risk_level = Column(String(20))
    
    total_verifications = Column(Integer, default=0)
    last_verified_at = Column(DateTime)
    
    is_publicly_visible = Column(Boolean, default=True)
    
    current_certificate_url = Column(String(500))
    certificate_hash = Column(String(64))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    company = relationship("Company", back_populates="public_profile")
    
    __table_args__ = (
        CheckConstraint("sello_status IN ('bronze', 'silver', 'gold', 'expired')", name="valid_sello_status"),
        CheckConstraint("risk_level IN ('low', 'medium', 'high', 'critical')", name="valid_risk_level"),
        CheckConstraint("current_score BETWEEN 0 AND 100", name="valid_score"),
    )


class Invite(Base):
    """Sistema de invitaciones - Efecto Red"""
    __tablename__ = "invites"
    
    invite_code = Column(String(20), primary_key=True)
    
    inviter_ruc = Column(String(11), ForeignKey("companies.ruc"), nullable=False)
    inviter_company_name = Column(String(255), nullable=False)
    
    invitee_ruc = Column(String(11))
    invitee_email = Column(String(255), nullable=False)
    invitee_company_name = Column(String(255))
    
    depth_level = Column(Integer, default=1)
    parent_invite_code = Column(String(20), ForeignKey("invites.invite_code"))
    
    status = Column(String(20), default="sent")
    
    sent_at = Column(DateTime, default=datetime.utcnow)
    opened_at = Column(DateTime)
    clicked_at = Column(DateTime)
    registered_at = Column(DateTime)
    converted_to_paid_at = Column(DateTime)
    
    expected_plan = Column(String(20), default="bronze")
    monthly_value = Column(Float)
    
    email_subject = Column(String(500))
    email_template_used = Column(String(50))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    
    # Relaciones
    inviter = relationship("Company", foreign_keys=[inviter_ruc], back_populates="sent_invites")
    parent_invite = relationship("Invite", remote_side=[invite_code], back_populates="child_invites")
    child_invites = relationship("Invite", back_populates="parent_invite")
    
    __table_args__ = (
        CheckConstraint("status IN ('sent', 'opened', 'clicked', 'registered', 'paid', 'expired', 'cancelled')", name="valid_invite_status"),
    )


class VerificationRequest(Base):
    """Consultas de verificación - Core business"""
    __tablename__ = "verification_requests"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    consultant_ruc = Column(String(11), ForeignKey("companies.ruc"), nullable=False)
    
    target_ruc = Column(String(11), nullable=False)
    target_company_name = Column(String(255))
    
    score = Column(Integer, nullable=False)
    risk_level = Column(String(20), nullable=False)
    
    sunat_debt = Column(Float, default=0)
    sunat_tax_status = Column(String(50))
    sunat_contributor_status = Column(String(50))
    
    osce_sanctions_count = Column(Integer, default=0)
    osce_sanctions_details = Column(JSONB, default=list)
    tce_sanctions_count = Column(Integer, default=0)
    tce_sanctions_details = Column(JSONB, default=list)
    
    ml_anomaly_score = Column(Float, default=0)
    ml_risk_factors = Column(JSONB, default=list)
    
    certificate_url = Column(String(500))
    certificate_hash = Column(String(64))
    digital_signature_id = Column(String(100))
    
    raw_data = Column(JSONB)
    
    is_cached = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    public_certificate_id = Column(UUID(as_uuid=True))
    
    # Relaciones
    company = relationship("Company", back_populates="verifications")
    
    __table_args__ = (
        CheckConstraint("score BETWEEN 0 AND 100", name="valid_verification_score"),
        CheckConstraint("risk_level IN ('low', 'medium', 'high', 'critical')", name="valid_verification_risk"),
    )


class CompanyHierarchy(Base):
    """Red de subcontratistas"""
    __tablename__ = "company_hierarchies"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    parent_ruc = Column(String(11), ForeignKey("companies.ruc"), nullable=False)
    child_ruc = Column(String(11), ForeignKey("companies.ruc"), nullable=False)
    
    relationship_type = Column(String(50), default="subcontractor")
    created_via = Column(String(50), default="manual")
    invite_code = Column(String(20), ForeignKey("invites.invite_code"))
    
    is_active = Column(Boolean, default=True)
    verified_at = Column(DateTime)
    
    notes = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        CheckConstraint("relationship_type IN ('subcontractor', 'supplier', 'client', 'partner')", name="valid_relationship"),
        CheckConstraint("created_via IN ('manual', 'invite', 'csv_import', 'api')", name="valid_created_via"),
        UniqueConstraint('parent_ruc', 'child_ruc', name='unique_hierarchy'),
    )


class ApiKey(Base):
    """API Keys para integraciones ERP"""
    __tablename__ = "api_keys"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_ruc = Column(String(11), ForeignKey("companies.ruc", ondelete="CASCADE"), nullable=False)
    
    key_hash = Column(String(255), unique=True, nullable=False)
    key_prefix = Column(String(8), nullable=False)
    
    name = Column(String(100), default="API Key")
    description = Column(Text)
    
    rate_limit_per_minute = Column(Integer, default=60)
    rate_limit_per_hour = Column(Integer, default=1000)
    
    last_used_at = Column(DateTime)
    usage_count = Column(Integer, default=0)
    
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime)
    revoked_at = Column(DateTime)
    revoked_reason = Column(Text)
    
    scopes = Column(JSONB, default=list)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(255))
    
    # Relaciones
    company = relationship("Company", back_populates="api_keys")


class Webhook(Base):
    """Webhooks para notificaciones en tiempo real"""
    __tablename__ = "webhooks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_ruc = Column(String(11), ForeignKey("companies.ruc", ondelete="CASCADE"), nullable=False)
    
    url = Column(String(500), nullable=False)
    secret = Column(String(255), nullable=False)
    
    events = Column(JSONB, nullable=False)
    
    is_active = Column(Boolean, default=True)
    
    success_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)
    last_triggered_at = Column(DateTime)
    last_error = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AuditLog(Base):
    """Logs de auditoría para compliance"""
    __tablename__ = "audit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    actor_type = Column(String(20), nullable=False)
    actor_id = Column(String(255))
    company_ruc = Column(String(11), ForeignKey("companies.ruc"))
    
    action = Column(String(100), nullable=False)
    resource_type = Column(String(50), nullable=False)
    resource_id = Column(String(255))
    
    old_values = Column(JSONB)
    new_values = Column(JSONB)
    metadata = Column(JSONB)
    
    ip_address = Column(String(45))
    user_agent = Column(Text)
    request_id = Column(String(100))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        CheckConstraint("actor_type IN ('user', 'system', 'api_key', 'webhook')", name="valid_actor_type"),
    )


class SystemConfig(Base):
    """Configuración del sistema"""
    __tablename__ = "system_config"
    
    key = Column(String(100), primary_key=True)
    value = Column(JSONB, nullable=False)
    description = Column(Text)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(String(255))
