"""
Conflict Zero - SQLAlchemy Models v2.0
UUID PK, RUC encriptado, soft delete, contractual obligation
"""

import uuid
import hashlib
import os
from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy import Column, String, Boolean, DateTime, Integer, Float, Text, ForeignKey, CheckConstraint, UniqueConstraint, event, LargeBinary
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, declarative_base, validates
from sqlalchemy.sql import func

Base = declarative_base()

# Usar tipos genéricos compatibles con PostgreSQL y SQLite
JSONB_TYPE = Text  # Para SQLite; en PostgreSQL se puede usar JSONB
BYTEA_TYPE = LargeBinary  # Funciona en ambos

# ============================================================
# UTILS PARA ENCRIPTACIÓN
# ============================================================

def hash_ruc(ruc: str) -> str:
    """Genera hash SHA-256 del RUC para búsquedas sin desencriptar"""
    return hashlib.sha256(ruc.encode()).hexdigest()

def generate_public_slug() -> str:
    """Genera slug único de 16 caracteres para URLs públicas"""
    import secrets
    import string
    return ''.join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(16))

# ============================================================
# 1. COMPANIES (UUID PK, RUC encriptado)
# ============================================================

class Company(Base):
    __tablename__ = "companies"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # RUC encriptado (AES-256 via pgcrypto en DB, o application layer)
    ruc_encrypted = Column(BYTEA_TYPE, nullable=False)
    ruc_hash = Column(String(64), unique=True, nullable=False, index=True)
    
    # Slug público para URLs
    public_slug = Column(String(16), unique=True, nullable=False, index=True, default=generate_public_slug)
    
    razon_social = Column(String(255), nullable=False)
    direccion = Column(String(500))
    distrito = Column(String(100))
    provincia = Column(String(100))
    departamento = Column(String(100))
    
    # Plan y estado
    plan_tier = Column(String(20), nullable=False, default="bronze")
    plan_type = Column(String(20), nullable=False, default="bronze")
    status = Column(String(20), nullable=False, default="pending")
    is_founder = Column(Boolean, default=False)
    founder_expires_at = Column(DateTime)
    
    # Suscripción y pagos
    subscription_status = Column(String(20), default="inactive")
    plan_activated_at = Column(DateTime)
    next_billing_date = Column(DateTime)
    
    # Obligación contractual (manual, solo admin)
    contractual_obligation = Column(Boolean, default=False)
    contractual_signed_at = Column(DateTime)
    contractual_document_url = Column(String(500))
    
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
    
    # Soft delete + retención legal
    deleted_at = Column(DateTime)
    is_archived = Column(Boolean, default=False)
    retained_until = Column(DateTime)  # 5 años desde created_at
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = Column(DateTime)
    
    # Relaciones
    sent_invites = relationship("Invite", foreign_keys="Invite.inviter_id", back_populates="inviter")
    verifications = relationship("VerificationRequest", back_populates="company")
    api_keys = relationship("ApiKey", back_populates="company")
    public_profile = relationship("PublicProfile", back_populates="company", uselist=False)
    hierarchies_as_parent = relationship("CompanyHierarchy", foreign_keys="CompanyHierarchy.parent_id", back_populates="parent")
    hierarchies_as_child = relationship("CompanyHierarchy", foreign_keys="CompanyHierarchy.child_id", back_populates="child")
    digital_signatures = relationship("DigitalSignature", back_populates="company")
    
    __table_args__ = (
        CheckConstraint("plan_tier IN ('bronze', 'silver', 'gold', 'founder')", name="valid_plan_tier"),
        CheckConstraint("plan_type IN ('essential', 'professional', 'enterprise', 'bronze', 'silver', 'gold', 'founder')", name="valid_plan_type"),
        CheckConstraint("status IN ('active', 'cancelled', 'suspended', 'pending')", name="valid_status"),
        CheckConstraint("subscription_status IN ('active', 'inactive', 'canceled', 'past_due')", name="valid_subscription_status"),
    )
    
    @validates('plan_tier')
    def validate_plan_tier(self, key, value):
        assert value in ['bronze', 'silver', 'gold', 'founder']
        return value
    
    @validates('plan_type')
    def validate_plan_type(self, key, value):
        assert value in ['essential', 'professional', 'enterprise', 'bronze', 'silver', 'gold', 'founder']
        return value
    
    def soft_delete(self):
        """Soft delete con retención de 5 años"""
        self.deleted_at = datetime.utcnow()
        self.retained_until = datetime.utcnow() + timedelta(days=365*5)
        self.status = 'cancelled'
    
    def is_active_record(self):
        """Verifica si el registro está activo (no eliminado)"""
        return self.deleted_at is None
    
    def get_founder_compliance_status(self):
        """Calcula estado de cumplimiento contractual"""
        if not self.contractual_obligation:
            return 'sin_obligacion'
        
        invites = [i for i in self.sent_invites if i.deleted_at is None]
        if not invites:
            return 'sin_invitados'
        
        paid = len([i for i in invites if i.status == 'paid'])
        total = len(invites)
        
        if paid >= total * 0.5:
            return 'cumpliendo'
        elif self.founder_expires_at and self.founder_expires_at - datetime.utcnow() <= timedelta(days=7):
            return 'riesgo_inminente'
        else:
            return 'en_riesgo'


# ============================================================
# 2. FOUNDER APPLICATIONS
# ============================================================

class FounderApplication(Base):
    __tablename__ = "founder_applications"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # RUC encriptado (nullable hasta que se implemente encriptación real en el endpoint)
    ruc_encrypted = Column(BYTEA_TYPE, nullable=True)
    ruc_hash = Column(String(64), nullable=False, index=True)
    
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
    
    # Soft delete
    deleted_at = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        CheckConstraint("annual_volume IN ('10-50M', '50-200M', '200M+')", name="valid_volume"),
        CheckConstraint("subcontractor_count IN ('5-20', '20-50', '50+')", name="valid_subcontractor_count"),
        CheckConstraint("status IN ('pending', 'under_review', 'approved', 'rejected', 'waitlisted')", name="valid_app_status"),
    )
    
    def get_priority_score(self):
        """Calcula score de prioridad para el review"""
        volume_score = {'200M+': 100, '50-200M': 75, '10-50M': 50}.get(self.annual_volume, 50)
        subs_score = {'50+': 100, '20-50': 75, '5-20': 50}.get(self.subcontractor_count, 50)
        return volume_score + subs_score
    
    def get_potencial_efecto_red(self):
        """Clasifica potencial de efecto red"""
        if self.subcontractor_count == '50+':
            return 'alto_potencial_red'
        elif self.subcontractor_count == '20-50':
            return 'medio_potencial'
        else:
            return 'bajo_potencial'


# ============================================================
# 3. PUBLIC PROFILES (Lock-in de vergüenza)
# ============================================================

class PublicProfile(Base):
    __tablename__ = "public_profiles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    
    slug = Column(String(16), unique=True, nullable=False, index=True)
    display_name = Column(String(255), nullable=False)
    
    # Estado del sello
    sello_status = Column(String(20), default="expired")
    sello_expires_at = Column(DateTime)
    
    # Estado visual para UI/psicología
    visual_state = Column(String(30), default="expired_shame")
    
    current_score = Column(Integer)
    risk_level = Column(String(20))
    
    total_verifications = Column(Integer, default=0)
    last_verified_at = Column(DateTime)
    
    is_publicly_visible = Column(Boolean, default=True)
    
    current_certificate_url = Column(String(500))
    certificate_hash = Column(String(64))
    
    deleted_at = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    company = relationship("Company", back_populates="public_profile")
    
    __table_args__ = (
        CheckConstraint("sello_status IN ('bronze', 'silver', 'gold', 'expired')", name="valid_sello_status"),
        CheckConstraint("risk_level IN ('low', 'medium', 'high', 'critical')", name="valid_risk_level"),
        CheckConstraint("current_score BETWEEN 0 AND 100", name="valid_score"),
        CheckConstraint("visual_state IN ('active_gold', 'active_silver', 'active_bronze', 'expired_grace', 'expired_shame', 'suspended')", name="valid_visual_state"),
    )
    
    def update_visual_state(self):
        """Actualiza estado visual basado en sello_status y expiración"""
        if self.sello_status == 'expired':
            self.visual_state = 'expired_shame'
        elif self.sello_status == 'bronze':
            self.visual_state = 'active_bronze'
        elif self.sello_status == 'silver':
            self.visual_state = 'active_silver'
        elif self.sello_status == 'gold':
            self.visual_state = 'active_gold'
        
        # Si está por expirar (3 días), mostrar grace period
        if self.sello_expires_at and self.sello_status != 'expired':
            days_until = (self.sello_expires_at - datetime.utcnow()).days
            if days_until <= 3 and days_until > 0:
                self.visual_state = 'expired_grace'


# ============================================================
# 4. INVITES (Efecto Red con obligación contractual)
# ============================================================

class Invite(Base):
    __tablename__ = "invites"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invite_code = Column(String(20), unique=True, nullable=False, index=True)
    
    inviter_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False, index=True)
    inviter_company_name = Column(String(255), nullable=False)
    
    invitee_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=True)
    invitee_email = Column(String(255), nullable=False, index=True)
    invitee_company_name = Column(String(255))
    invitee_ruc_hash = Column(String(64), index=True)
    
    depth_level = Column(Integer, default=1)
    parent_invite_id = Column(UUID(as_uuid=True), ForeignKey("invites.id"), nullable=True)
    
    status = Column(String(20), default="sent")
    
    # Tracking de cumplimiento contractual
    enforcement_emails_sent = Column(Integer, default=0)
    last_enforcement_email_at = Column(DateTime)
    conversion_deadline = Column(DateTime)
    
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
    expires_at = Column(DateTime, default=lambda: datetime.utcnow() + timedelta(days=30))
    
    deleted_at = Column(DateTime)
    
    # Relaciones
    inviter = relationship("Company", foreign_keys=[inviter_id], back_populates="sent_invites")
    invitee = relationship("Company", foreign_keys=[invitee_id])
    parent_invite = relationship("Invite", remote_side=[id], back_populates="child_invites")
    child_invites = relationship("Invite", back_populates="parent_invite")
    
    __table_args__ = (
        CheckConstraint("status IN ('sent', 'opened', 'clicked', 'registered', 'paid', 'expired', 'cancelled')", name="valid_invite_status"),
    )
    
    def check_expiration(self):
        """Verifica y actualiza estado si expiró"""
        if self.expires_at and self.expires_at < datetime.utcnow() and self.status in ['sent', 'opened', 'clicked']:
            self.status = 'expired'
            return True
        return False
    
    def send_enforcement_email(self):
        """Registra envío de email de presión"""
        self.enforcement_emails_sent += 1
        self.last_enforcement_email_at = datetime.utcnow()


# ============================================================
# 5. VERIFICATION REQUESTS
# ============================================================

class VerificationRequest(Base):
    __tablename__ = "verification_requests"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    consultant_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False, index=True)
    
    target_ruc_hash = Column(String(64), nullable=False, index=True)
    target_ruc_encrypted = Column(BYTEA_TYPE)
    target_company_name = Column(String(255))
    
    score = Column(Integer, nullable=False)
    risk_level = Column(String(20), nullable=False)
    
    sunat_debt = Column(Float, default=0)
    sunat_tax_status = Column(String(50))
    sunat_contributor_status = Column(String(50))
    
    osce_sanctions_count = Column(Integer, default=0)
    osce_sanctions_details = Column(JSONB_TYPE, default=list)
    tce_sanctions_count = Column(Integer, default=0)
    tce_sanctions_details = Column(JSONB_TYPE, default=list)
    
    ml_anomaly_score = Column(Float, default=0)
    ml_risk_factors = Column(JSONB_TYPE, default=list)
    
    certificate_url = Column(String(500))
    certificate_hash = Column(String(64))
    digital_signature_id = Column(String(100))
    digital_signature_timestamp = Column(DateTime)
    
    raw_data = Column(JSONB_TYPE)
    
    is_cached = Column(Boolean, default=False)
    cache_expires_at = Column(DateTime)
    
    deleted_at = Column(DateTime)
    retained_until = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    public_certificate_id = Column(UUID(as_uuid=True))
    
    # Relaciones
    company = relationship("Company", back_populates="verifications")
    digital_signature = relationship("DigitalSignature", back_populates="verification", uselist=False)
    
    __table_args__ = (
        CheckConstraint("score BETWEEN 0 AND 100", name="valid_verification_score"),
        CheckConstraint("risk_level IN ('low', 'medium', 'high', 'critical')", name="valid_verification_risk"),
    )
    
    def soft_delete(self):
        """Soft delete con retención legal"""
        self.deleted_at = datetime.utcnow()
        self.retained_until = datetime.utcnow() + timedelta(days=365*5)


# ============================================================
# 6. COMPANY HIERARCHIES
# ============================================================

class CompanyHierarchy(Base):
    __tablename__ = "company_hierarchies"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    parent_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False, index=True)
    child_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False, index=True)
    
    relationship_type = Column(String(50), default="subcontractor")
    created_via = Column(String(50), default="manual")
    invite_id = Column(UUID(as_uuid=True), ForeignKey("invites.id"))
    
    is_active = Column(Boolean, default=True)
    verified_at = Column(DateTime)
    
    notes = Column(Text)
    
    deleted_at = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    parent = relationship("Company", foreign_keys=[parent_id], back_populates="hierarchies_as_parent")
    child = relationship("Company", foreign_keys=[child_id], back_populates="hierarchies_as_child")
    invite = relationship("Invite")
    
    __table_args__ = (
        CheckConstraint("relationship_type IN ('subcontractor', 'supplier', 'client', 'partner')", name="valid_relationship"),
        CheckConstraint("created_via IN ('manual', 'invite', 'csv_import', 'api')", name="valid_created_via"),
        UniqueConstraint('parent_id', 'child_id', name='unique_hierarchy'),
    )


# ============================================================
# 7. API KEYS
# ============================================================

class ApiKey(Base):
    __tablename__ = "api_keys"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    
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
    
    scopes = Column(JSONB_TYPE, default=list)
    
    deleted_at = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(255))
    
    company = relationship("Company", back_populates="api_keys")


# ============================================================
# 8. WEBHOOKS
# ============================================================

class Webhook(Base):
    __tablename__ = "webhooks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    
    url = Column(String(500), nullable=False)
    secret = Column(String(255), nullable=False)
    
    events = Column(JSONB_TYPE, nullable=False)
    
    is_active = Column(Boolean, default=True)
    
    success_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)
    last_triggered_at = Column(DateTime)
    last_error = Column(Text)
    
    deleted_at = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ============================================================
# ============================================================
# 8b. WEBHOOK DELIVERIES
# ============================================================

class WebhookDelivery(Base):
    __tablename__ = "webhook_deliveries"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    webhook_id = Column(UUID(as_uuid=True), ForeignKey("webhooks.id", ondelete="CASCADE"), nullable=False, index=True)
    
    event_type = Column(String(50), nullable=False)
    payload = Column(JSONB_TYPE, nullable=False)
    
    status = Column(String(20), default="pending")
    http_status = Column(Integer)
    response_body = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    
    __table_args__ = (
        CheckConstraint("status IN ('pending', 'delivered', 'failed')", name="valid_delivery_status"),
    )


# 9. API CACHE (PostgreSQL como cache)
# ============================================================

class ApiCache(Base):
    __tablename__ = "api_cache"
    
    query_hash = Column(String(32), primary_key=True)
    query_type = Column(String(50), nullable=False, index=True)
    query_identifier = Column(String(100), nullable=False, index=True)
    
    response_json = Column(JSONB_TYPE, nullable=False)
    status_code = Column(Integer, default=200)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False, index=True)
    
    hit_count = Column(Integer, default=1)
    last_hit_at = Column(DateTime, default=datetime.utcnow)
    
    def is_expired(self):
        return self.expires_at < datetime.utcnow()
    
    def hit(self):
        """Registra un hit en el caché"""
        self.hit_count += 1
        self.last_hit_at = datetime.utcnow()


# ============================================================
# 10. AUDIT LOG
# ============================================================

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    actor_type = Column(String(20), nullable=False)
    actor_id = Column(String(255))
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), index=True)
    
    action = Column(String(100), nullable=False)
    resource_type = Column(String(50), nullable=False)
    resource_id = Column(String(255))
    
    old_values = Column(JSONB_TYPE)
    new_values = Column(JSONB_TYPE)
    audit_metadata = Column(JSONB_TYPE)  # Renamed from 'metadata' to avoid SQLAlchemy reserved word
    
    ip_address = Column(String(45))
    user_agent = Column(Text)
    request_id = Column(String(100))
    
    retained_until = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        CheckConstraint("actor_type IN ('user', 'system', 'api_key', 'webhook')", name="valid_actor_type"),
    )


# ============================================================
# 11. DIGITAL SIGNATURES (INDECOPI)
# ============================================================

class DigitalSignature(Base):
    __tablename__ = "digital_signatures"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    verification_id = Column(UUID(as_uuid=True), ForeignKey("verification_requests.id"), nullable=False, index=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False, index=True)
    
    signature_data = Column(BYTEA_TYPE, nullable=False)
    certificate_id = Column(String(100), nullable=False)
    certificate_issuer = Column(String(255))
    
    signed_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    is_valid = Column(Boolean, default=True)
    revoked_at = Column(DateTime)
    revocation_reason = Column(Text)
    
    document_hash = Column(String(64), nullable=False)
    signature_hash = Column(String(64), nullable=False)
    
    signature_algorithm = Column(String(50), default="SHA256withRSA")
    key_size = Column(Integer, default=2048)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    verification = relationship("VerificationRequest", back_populates="digital_signature")
    company = relationship("Company", back_populates="digital_signatures")


# ============================================================
# 11b. COMPARISON REQUESTS
# ============================================================

class ComparisonRequest(Base):
    __tablename__ = "comparison_requests"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    
    rucs = Column(JSONB_TYPE, default=list)
    results = Column(JSONB_TYPE)
    
    status = Column(String(20), default="completed")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ============================================================
# 12. SYSTEM CONFIG
# ============================================================

class SystemConfig(Base):
    __tablename__ = "system_config"
    
    key = Column(String(100), primary_key=True)
    value = Column(JSONB_TYPE, nullable=False)
    description = Column(Text)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(String(255))


# ============================================================
# EVENTS (Triggers)
# ============================================================

@event.listens_for(Company, 'before_insert')
def set_retention_date(mapper, connection, target):
    """Setea fecha de retención al crear empresa"""
    if not target.retained_until:
        target.retained_until = datetime.utcnow() + timedelta(days=365*5)


@event.listens_for(VerificationRequest, 'before_insert')
def set_verification_retention(mapper, connection, target):
    """Setea fecha de retención al crear verificación"""
    if not target.retained_until:
        target.retained_until = datetime.utcnow() + timedelta(days=365*5)


@event.listens_for(Invite, 'before_update')
def check_invite_expiration(mapper, connection, target):
    """Verifica expiración de invitación antes de actualizar"""
    target.check_expiration()