-- ============================================================
-- CONFLICT ZERO - SCHEMA v2.0 (Refactorizado con UUID + Seguridad)
-- Cambios: UUID PK, RUC encriptado, soft delete, contractual obligation
-- ============================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto"; -- Para encriptación

-- ============================================================
-- 1. COMPANIES (UUID PK, RUC encriptado)
-- ============================================================
CREATE TABLE companies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- RUC encriptado (AES-256 via pgcrypto)
    ruc_encrypted BYTEA NOT NULL,
    ruc_hash VARCHAR(64) UNIQUE NOT NULL, -- SHA-256 para búsquedas sin desencriptar
    
    -- Slug público para URLs (16 chars aleatorios)
    public_slug VARCHAR(16) UNIQUE NOT NULL,
    
    razon_social VARCHAR(255) NOT NULL,
    direccion VARCHAR(500),
    distrito VARCHAR(100),
    provincia VARCHAR(100),
    departamento VARCHAR(100),
    
    -- Plan y estado
    plan_tier VARCHAR(20) NOT NULL DEFAULT 'bronze' 
        CHECK (plan_tier IN ('bronze', 'silver', 'gold', 'founder')),
    status VARCHAR(20) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('active', 'cancelled', 'suspended', 'pending')),
    is_founder BOOLEAN DEFAULT FALSE,
    founder_expires_at TIMESTAMP,
    
    -- Obligación contractual (manual, solo admin puede activar)
    contractual_obligation BOOLEAN DEFAULT FALSE,
    contractual_signed_at TIMESTAMP,
    contractual_document_url VARCHAR(500),
    
    -- Límites y uso
    max_monthly_queries INTEGER DEFAULT 1000,
    used_queries_this_month INTEGER DEFAULT 0,
    queries_reset_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- API
    api_key VARCHAR(255) UNIQUE,
    api_key_created_at TIMESTAMP,
    
    -- Contacto
    contact_email VARCHAR(255) NOT NULL,
    contact_name VARCHAR(255),
    contact_phone VARCHAR(50),
    
    -- Tracking de invitaciones
    invited_by_code VARCHAR(50),
    invite_depth INTEGER DEFAULT 0,
    
    -- Soft delete + retención legal (5 años)
    deleted_at TIMESTAMP,
    is_archived BOOLEAN DEFAULT FALSE,
    retained_until DATE, -- 5 años desde created_at
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP
);

CREATE INDEX idx_companies_slug ON companies(public_slug);
CREATE INDEX idx_companies_ruc_hash ON companies(ruc_hash);
CREATE INDEX idx_companies_plan ON companies(plan_tier);
CREATE INDEX idx_companies_status ON companies(status) WHERE deleted_at IS NULL;
CREATE INDEX idx_companies_api_key ON companies(api_key);
CREATE INDEX idx_companies_founder ON companies(is_founder) WHERE is_founder = TRUE;

-- ============================================================
-- 2. FOUNDER APPLICATIONS
-- ============================================================
CREATE TABLE founder_applications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- RUC encriptado
    ruc_encrypted BYTEA NOT NULL,
    ruc_hash VARCHAR(64) NOT NULL,
    
    company_name VARCHAR(255) NOT NULL,
    
    contact_name VARCHAR(255) NOT NULL,
    contact_email VARCHAR(255) NOT NULL,
    contact_phone VARCHAR(50),
    
    annual_volume VARCHAR(20) NOT NULL 
        CHECK (annual_volume IN ('10-50M', '50-200M', '200M+')),
    subcontractor_count VARCHAR(20) NOT NULL
        CHECK (subcontractor_count IN ('5-20', '20-50', '50+')),
    
    status VARCHAR(20) DEFAULT 'pending'
        CHECK (status IN ('pending', 'under_review', 'approved', 'rejected', 'waitlisted')),
    
    -- Notas internas
    notes TEXT,
    reviewed_by VARCHAR(255),
    reviewed_at TIMESTAMP,
    
    -- Tracking
    ip_address VARCHAR(45),
    user_agent TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_founder_apps_status ON founder_applications(status);
CREATE INDEX idx_founder_apps_ruc_hash ON founder_applications(ruc_hash);
CREATE INDEX idx_founder_apps_created ON founder_applications(created_at);

-- ============================================================
-- 3. PUBLIC PROFILES (Lock-in con estados visuales granulares)
-- ============================================================
CREATE TABLE public_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    
    -- Slug público único
    slug VARCHAR(16) UNIQUE NOT NULL,
    
    display_name VARCHAR(255) NOT NULL,
    
    -- Estado del sello (para lógica)
    sello_status VARCHAR(20) NOT NULL DEFAULT 'expired'
        CHECK (sello_status IN ('bronze', 'silver', 'gold', 'expired')),
    sello_expires_at TIMESTAMP,
    
    -- Estado visual (para UI/psicología del lock-in)
    visual_state VARCHAR(30) NOT NULL DEFAULT 'expired_shame'
        CHECK (visual_state IN (
            'active_gold',      -- Verde brillante + check
            'active_silver',    -- Azul metálico
            'active_bronze',    -- Naranja
            'expired_grace',    -- Amarillo "Vence en 3 días"
            'expired_shame',    -- Rojo "Sello Vencido - Riesgo Legal"
            'suspended'         -- Gris "En verificación"
        )),
    
    -- Score y riesgo
    current_score INTEGER CHECK (current_score BETWEEN 0 AND 100),
    risk_level VARCHAR(20) CHECK (risk_level IN ('low', 'medium', 'high', 'critical')),
    
    -- Contadores públicos
    total_verifications INTEGER DEFAULT 0,
    last_verified_at TIMESTAMP,
    
    -- Visibilidad
    is_publicly_visible BOOLEAN DEFAULT TRUE,
    
    -- Certificado actual
    current_certificate_url VARCHAR(500),
    certificate_hash VARCHAR(64),
    
    -- Soft delete
    deleted_at TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_public_profiles_slug ON public_profiles(slug);
CREATE INDEX idx_public_profiles_company ON public_profiles(company_id);
CREATE INDEX idx_public_profiles_status ON public_profiles(sello_status);
CREATE INDEX idx_public_profiles_visible ON public_profiles(is_publicly_visible) 
    WHERE is_publicly_visible = TRUE AND deleted_at IS NULL;

-- ============================================================
-- 4. INVITES (Efecto Red con obligación contractual)
-- ============================================================
CREATE TABLE invites (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    invite_code VARCHAR(20) UNIQUE NOT NULL,
    
    -- Quién invita
    inviter_id UUID NOT NULL REFERENCES companies(id),
    inviter_company_name VARCHAR(255) NOT NULL,
    
    -- A quién se invita
    invitee_id UUID REFERENCES companies(id), -- Se llena cuando se registra
    invitee_email VARCHAR(255) NOT NULL,
    invitee_company_name VARCHAR(255),
    invitee_ruc_hash VARCHAR(64), -- Hash para buscar sin desencriptar
    
    -- Jerarquía (árbol genealógico)
    depth_level INTEGER DEFAULT 1,
    parent_invite_id UUID REFERENCES invites(id),
    
    -- Estado
    status VARCHAR(20) DEFAULT 'sent'
        CHECK (status IN ('sent', 'opened', 'clicked', 'registered', 'paid', 'expired', 'cancelled')),
    
    -- Tracking de cumplimiento contractual
    enforcement_emails_sent INTEGER DEFAULT 0,
    last_enforcement_email_at TIMESTAMP,
    conversion_deadline DATE, -- Fecha límite para pagar o queda bloqueado
    
    -- Tracking de conversión
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    opened_at TIMESTAMP,
    clicked_at TIMESTAMP,
    registered_at TIMESTAMP,
    converted_to_paid_at TIMESTAMP,
    
    -- Valor económico
    expected_plan VARCHAR(20) DEFAULT 'bronze',
    monthly_value DECIMAL(10,2),
    
    -- Email tracking
    email_subject VARCHAR(500),
    email_template_used VARCHAR(50),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP DEFAULT (CURRENT_TIMESTAMP + INTERVAL '30 days'),
    
    deleted_at TIMESTAMP
);

CREATE INDEX idx_invites_inviter ON invites(inviter_id);
CREATE INDEX idx_invites_status ON invites(status);
CREATE INDEX idx_invites_email ON invites(invitee_email);
CREATE INDEX idx_invites_parent ON invites(parent_invite_id);
CREATE INDEX idx_invites_code ON invites(invite_code);

-- ============================================================
-- 5. VERIFICATION REQUESTS (Core con soft delete)
-- ============================================================
CREATE TABLE verification_requests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Quién consulta
    consultant_id UUID NOT NULL REFERENCES companies(id),
    
    -- A quién se consulta (RUC hash para búsquedas)
    target_ruc_hash VARCHAR(64) NOT NULL,
    target_ruc_encrypted BYTEA, -- Opcional: guardar si el usuario lo marca como "frecuente"
    target_company_name VARCHAR(255),
    
    -- Resultado
    score INTEGER NOT NULL CHECK (score BETWEEN 0 AND 100),
    risk_level VARCHAR(20) NOT NULL CHECK (risk_level IN ('low', 'medium', 'high', 'critical')),
    
    -- Datos SUNAT
    sunat_debt DECIMAL(15,2) DEFAULT 0,
    sunat_tax_status VARCHAR(50),
    sunat_contributor_status VARCHAR(50),
    
    -- Sanciones
    osce_sanctions_count INTEGER DEFAULT 0,
    osce_sanctions_details JSONB DEFAULT '[]'::jsonb,
    tce_sanctions_count INTEGER DEFAULT 0,
    tce_sanctions_details JSONB DEFAULT '[]'::jsonb,
    
    -- ML Score
    ml_anomaly_score DECIMAL(5,4) DEFAULT 0,
    ml_risk_factors JSONB DEFAULT '[]'::jsonb,
    
    -- Certificado generado
    certificate_url VARCHAR(500),
    certificate_hash VARCHAR(64),
    digital_signature_id VARCHAR(100),
    digital_signature_timestamp TIMESTAMP,
    
    -- Datos raw completos
    raw_data JSONB,
    
    -- Caché
    is_cached BOOLEAN DEFAULT FALSE,
    cache_expires_at TIMESTAMP,
    
    -- Soft delete + retención legal (5 años)
    deleted_at TIMESTAMP,
    retained_until DATE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    public_certificate_id UUID
);

CREATE INDEX idx_verifications_consultant ON verification_requests(consultant_id);
CREATE INDEX idx_verifications_target_hash ON verification_requests(target_ruc_hash);
CREATE INDEX idx_verifications_created ON verification_requests(created_at);
CREATE INDEX idx_verifications_score ON verification_requests(score);

-- ============================================================
-- 6. COMPANY HIERARCHIES (Red de subcontratistas)
-- ============================================================
CREATE TABLE company_hierarchies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    parent_id UUID NOT NULL REFERENCES companies(id),
    child_id UUID NOT NULL REFERENCES companies(id),
    
    relationship_type VARCHAR(50) DEFAULT 'subcontractor'
        CHECK (relationship_type IN ('subcontractor', 'supplier', 'client', 'partner')),
    created_via VARCHAR(50) DEFAULT 'manual'
        CHECK (created_via IN ('manual', 'invite', 'csv_import', 'api')),
    invite_id UUID REFERENCES invites(id),
    
    is_active BOOLEAN DEFAULT TRUE,
    verified_at TIMESTAMP,
    
    notes TEXT,
    
    -- Soft delete
    deleted_at TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(parent_id, child_id)
);

CREATE INDEX idx_hierarchies_parent ON company_hierarchies(parent_id);
CREATE INDEX idx_hierarchies_child ON company_hierarchies(child_id);
CREATE INDEX idx_hierarchies_active ON company_hierarchies(is_active) 
    WHERE is_active = TRUE AND deleted_at IS NULL;

-- ============================================================
-- 7. API KEYS
-- ============================================================
CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    
    key_hash VARCHAR(255) UNIQUE NOT NULL,
    key_prefix VARCHAR(8) NOT NULL,
    
    name VARCHAR(100) DEFAULT 'API Key',
    description TEXT,
    
    rate_limit_per_minute INTEGER DEFAULT 60,
    rate_limit_per_hour INTEGER DEFAULT 1000,
    
    last_used_at TIMESTAMP,
    usage_count INTEGER DEFAULT 0,
    
    is_active BOOLEAN DEFAULT TRUE,
    expires_at TIMESTAMP,
    revoked_at TIMESTAMP,
    revoked_reason TEXT,
    
    scopes JSONB DEFAULT '["read:verifications", "read:profile"]'::jsonb,
    
    deleted_at TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255)
);

CREATE INDEX idx_api_keys_company ON api_keys(company_id);
CREATE INDEX idx_api_keys_hash ON api_keys(key_hash);
CREATE INDEX idx_api_keys_active ON api_keys(is_active) WHERE is_active = TRUE AND deleted_at IS NULL;

-- ============================================================
-- 8. WEBHOOKS
-- ============================================================
CREATE TABLE webhooks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    
    url VARCHAR(500) NOT NULL,
    secret VARCHAR(255) NOT NULL,
    
    events JSONB NOT NULL,
    
    is_active BOOLEAN DEFAULT TRUE,
    
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    last_triggered_at TIMESTAMP,
    last_error TEXT,
    
    deleted_at TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_webhooks_company ON webhooks(company_id);
CREATE INDEX idx_webhooks_active ON webhooks(is_active) WHERE is_active = TRUE AND deleted_at IS NULL;

-- ============================================================
-- 9. API CACHE (PostgreSQL como cache)
-- ============================================================
CREATE TABLE api_cache (
    query_hash VARCHAR(32) PRIMARY KEY, -- MD5 de "SUNAT_20100123091"
    query_type VARCHAR(50) NOT NULL, -- 'SUNAT', 'OSCE', 'TCE'
    query_identifier VARCHAR(100) NOT NULL, -- RUC o identificador
    
    response_json JSONB NOT NULL,
    status_code INTEGER DEFAULT 200,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL, -- TTL: normalmente 1 hora
    
    hit_count INTEGER DEFAULT 1,
    last_hit_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_api_cache_expires ON api_cache(expires_at);
CREATE INDEX idx_api_cache_query ON api_cache(query_type, query_identifier);

-- Función para limpiar caché expirado (correr cada hora)
CREATE OR REPLACE FUNCTION cleanup_expired_cache()
RETURNS void AS $$
BEGIN
    DELETE FROM api_cache WHERE expires_at < CURRENT_TIMESTAMP;
END;
$$ LANGUAGE plpgsql;

-- ============================================================
-- 10. AUDIT LOG
-- ============================================================
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    actor_type VARCHAR(20) NOT NULL
        CHECK (actor_type IN ('user', 'system', 'api_key', 'webhook')),
    actor_id VARCHAR(255),
    company_id UUID REFERENCES companies(id),
    
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50) NOT NULL,
    resource_id VARCHAR(255),
    
    old_values JSONB,
    new_values JSONB,
    metadata JSONB,
    
    ip_address VARCHAR(45),
    user_agent TEXT,
    request_id VARCHAR(100),
    
    retained_until DATE, -- 5 años
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_company ON audit_logs(company_id);
CREATE INDEX idx_audit_action ON audit_logs(action);
CREATE INDEX idx_audit_created ON audit_logs(created_at);
CREATE INDEX idx_audit_resource ON audit_logs(resource_type, resource_id);

-- ============================================================
-- 11. SYSTEM CONFIG
-- ============================================================
CREATE TABLE system_config (
    key VARCHAR(100) PRIMARY KEY,
    value JSONB NOT NULL,
    description TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(255)
);

INSERT INTO system_config (key, value, description) VALUES
('founder_program', '{"max_slots": 10, "duration_months": 3, "open": true, "applications_received": 0}'::jsonb, 'Configuración del Programa Fundador'),
('plans', '{"bronze": {"price": 400, "queries": 1000}, "silver": {"price": 800, "queries": 5000}, "gold": {"price": 2500, "queries": null}}'::jsonb, 'Configuración de planes'),
('features', '{"public_profiles": true, "api_erp": true, "invites": true, "webhooks": false, "digital_signature": false}'::jsonb, 'Feature flags'),
('retention_years', '{"verification_requests": 5, "audit_logs": 5, "general": 5}'::jsonb, 'Años de retención legal');

-- ============================================================
-- 12. DIGITAL SIGNATURES (Para certificados INDECOPI)
-- ============================================================
CREATE TABLE digital_signatures (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Referencia al certificado firmado
    verification_id UUID NOT NULL REFERENCES verification_requests(id),
    company_id UUID NOT NULL REFERENCES companies(id),
    
    -- Datos de la firma
    signature_data BYTEA NOT NULL, -- El sello digital en sí
    certificate_id VARCHAR(100) NOT NULL, -- ID del certificado utilizado
    certificate_issuer VARCHAR(255), -- Entidad emisora (ej: INDECOPI, Llama.pe)
    
    -- Validación
    signed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP, -- Cuándo expira la validez de la firma
    is_valid BOOLEAN DEFAULT TRUE,
    revoked_at TIMESTAMP,
    revocation_reason TEXT,
    
    -- Hash para verificación de integridad
    document_hash VARCHAR(64) NOT NULL, -- SHA-256 del PDF original
    signature_hash VARCHAR(64) NOT NULL, -- SHA-256 de la firma
    
    -- Metadata
    signature_algorithm VARCHAR(50) DEFAULT 'SHA256withRSA',
    key_size INTEGER DEFAULT 2048,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_signatures_verification ON digital_signatures(verification_id);
CREATE INDEX idx_signatures_company ON digital_signatures(company_id);
CREATE INDEX idx_signatures_valid ON digital_signatures(is_valid) WHERE is_valid = TRUE;

-- ============================================================
-- TRIGGERS PARA UPDATED_AT
-- ============================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_companies_updated_at BEFORE UPDATE ON companies
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_founder_apps_updated_at BEFORE UPDATE ON founder_applications
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_public_profiles_updated_at BEFORE UPDATE ON public_profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_hierarchies_updated_at BEFORE UPDATE ON company_hierarchies
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_webhooks_updated_at BEFORE UPDATE ON webhooks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================
-- VIEWS PARA REPORTES
-- ============================================================

-- View: Resumen de efecto red por constructora
CREATE VIEW network_effect_summary AS
SELECT 
    c.id,
    c.public_slug,
    c.razon_social,
    c.plan_tier,
    c.contractual_obligation,
    COUNT(i.invite_code) as total_invites_sent,
    COUNT(CASE WHEN i.status = 'paid' THEN 1 END) as invites_converted,
    COUNT(CASE WHEN i.status IN ('sent', 'opened', 'clicked') THEN 1 END) as invites_pending,
    COALESCE(SUM(i.monthly_value), 0) as monthly_network_value,
    COUNT(DISTINCT ch.child_id) as active_subcontractors,
    -- Compliance calculation
    CASE 
        WHEN c.contractual_obligation = FALSE THEN 'no_obligation'
        WHEN COUNT(CASE WHEN i.status = 'paid' THEN 1 END) >= (COUNT(i.invite_code) * 0.5) THEN 'compliant'
        ELSE 'at_risk'
    END as compliance_status
FROM companies c
LEFT JOIN invites i ON c.id = i.inviter_id AND i.deleted_at IS NULL
LEFT JOIN company_hierarchies ch ON c.id = ch.parent_id AND ch.is_active = TRUE AND ch.deleted_at IS NULL
WHERE c.deleted_at IS NULL
  AND c.plan_tier IN ('gold', 'founder')
GROUP BY c.id, c.public_slug, c.razon_social, c.plan_tier, c.contractual_obligation;

-- View: Founder compliance (para endpoint /founder/compliance)
CREATE VIEW founder_compliance_status AS
SELECT 
    c.id as company_id,
    c.public_slug,
    c.razon_social,
    c.contractual_obligation,
    c.contractual_signed_at,
    c.founder_expires_at,
    
    -- Métricas de invitaciones
    COUNT(i.invite_code) as subcontratistas_obligados,
    COUNT(CASE WHEN i.status = 'paid' THEN 1 END) as registrados,
    COUNT(CASE WHEN i.status = 'registered' THEN 1 END) as registrados_no_pagados,
    COUNT(CASE WHEN i.status IN ('sent', 'opened', 'clicked') THEN 1 END) as pendientes,
    
    -- Cálculo de conversión
    CASE 
        WHEN COUNT(i.invite_code) = 0 THEN 0
        ELSE ROUND((COUNT(CASE WHEN i.status = 'paid' THEN 1 END)::NUMERIC / COUNT(i.invite_code)) * 100, 1)
    END as tasa_conversion,
    
    -- Valor mensual generado
    COALESCE(SUM(CASE WHEN i.status = 'paid' THEN i.monthly_value ELSE 0 END), 0) as valor_mensual_generado,
    
    -- Alerta de cumplimiento
    CASE 
        WHEN c.contractual_obligation = FALSE THEN 'sin_obligacion'
        WHEN COUNT(i.invite_code) = 0 THEN 'sin_invitados'
        WHEN COUNT(CASE WHEN i.status = 'paid' THEN 1 END) >= (COUNT(i.invite_code) * 0.3) THEN 'cumpliendo'
        WHEN c.founder_expires_at - CURRENT_DATE <= 7 THEN 'riesgo_inminente'
        ELSE 'en_riesgo'
    END as estado_cumplimiento,
    
    -- Mensaje para el frontend
    CASE 
        WHEN c.contractual_obligation = FALSE THEN 'Pendiente de firma de contrato'
        WHEN COUNT(i.invite_code) = 0 THEN 'Debe subir lista de subcontratistas'
        WHEN COUNT(CASE WHEN i.status = 'paid' THEN 1 END) >= (COUNT(i.invite_code) * 0.5) THEN 'Cumplimiento excelente'
        WHEN c.founder_expires_at - CURRENT_DATE <= 7 THEN 
            'Riesgo: ' || (c.founder_expires_at - CURRENT_DATE) || ' días para mantener beneficio'
        ELSE 'Necesita más conversiones para mantener Founder'
    END as mensaje_alerta,
    
    -- Días restantes
    c.founder_expires_at - CURRENT_DATE as dias_restantes

FROM companies c
LEFT JOIN invites i ON c.id = i.inviter_id AND i.deleted_at IS NULL
WHERE c.deleted_at IS NULL
  AND c.is_founder = TRUE
GROUP BY c.id, c.public_slug, c.razon_social, c.contractual_obligation, c.contractual_signed_at, c.founder_expires_at;

-- View: Aplicaciones pendientes con scoring
CREATE VIEW founder_applications_scored AS
SELECT 
    fa.*,
    CASE 
        WHEN fa.annual_volume = '200M+' THEN 100
        WHEN fa.annual_volume = '50-200M' THEN 75
        ELSE 50
    END + 
    CASE 
        WHEN fa.subcontractor_count = '50+' THEN 100
        WHEN fa.subcontractor_count = '20-50' THEN 75
        ELSE 50
    END as priority_score,
    CASE 
        WHEN fa.subcontractor_count = '50+' THEN 'alto_potencial_red'
        WHEN fa.subcontractor_count = '20-50' THEN 'medio_potencial'
        ELSE 'bajo_potencial'
    END as potencial_efecto_red
FROM founder_applications fa
WHERE fa.status = 'pending'
ORDER BY priority_score DESC, created_at ASC;
