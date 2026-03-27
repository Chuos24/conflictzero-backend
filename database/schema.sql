-- ============================================================
-- CONFLICT ZERO - SCHEMA COMPLETO (Fase 1)
-- Base de datos para monopolio B2B de verificación de RUCs
-- ============================================================

-- Extensiones necesarias
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================
-- 1. COMPANIES (Empresas clientes)
-- ============================================================
CREATE TABLE companies (
    ruc VARCHAR(11) PRIMARY KEY,
    razon_social VARCHAR(255) NOT NULL,
    direccion VARCHAR(500),
    distrito VARCHAR(100),
    provincia VARCHAR(100),
    departamento VARCHAR(100),
    
    -- Plan y estado
    plan_tier VARCHAR(20) NOT NULL DEFAULT 'bronze' 
        CHECK (plan_tier IN ('bronze', 'silver', 'gold', 'founder')),
    status VARCHAR(20) NOT NULL DEFAULT 'active'
        CHECK (status IN ('active', 'cancelled', 'suspended', 'pending')),
    is_founder BOOLEAN DEFAULT FALSE,
    founder_expires_at TIMESTAMP,
    
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
    
    -- Tracking de invitaciones (efecto red)
    invited_by_code VARCHAR(50),
    invite_depth INTEGER DEFAULT 0, -- 0=directo, 1=invitado, 2=nieto, etc.
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP
);

CREATE INDEX idx_companies_plan ON companies(plan_tier);
CREATE INDEX idx_companies_status ON companies(status);
CREATE INDEX idx_companies_api_key ON companies(api_key);
CREATE INDEX idx_companies_invited_by ON companies(invited_by_code);

-- ============================================================
-- 2. FOUNDER APPLICATIONS (Aplicaciones al Programa Fundador)
-- ============================================================
CREATE TABLE founder_applications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Datos de la empresa
    company_ruc VARCHAR(11) NOT NULL,
    company_name VARCHAR(255) NOT NULL,
    
    -- Contacto
    contact_name VARCHAR(255) NOT NULL,
    contact_email VARCHAR(255) NOT NULL,
    contact_phone VARCHAR(50),
    
    -- Información de volumen
    annual_volume VARCHAR(20) NOT NULL 
        CHECK (annual_volume IN ('10-50M', '50-200M', '200M+')),
    subcontractor_count VARCHAR(20) NOT NULL
        CHECK (subcontractor_count IN ('5-20', '20-50', '50+')),
    
    -- Estado de la aplicación
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
CREATE INDEX idx_founder_apps_ruc ON founder_applications(company_ruc);
CREATE INDEX idx_founder_apps_created ON founder_applications(created_at);

-- ============================================================
-- 3. PUBLIC PROFILES (Lock-in de vergüenza pública)
-- ============================================================
CREATE TABLE public_profiles (
    ruc VARCHAR(11) PRIMARY KEY REFERENCES companies(ruc) ON DELETE CASCADE,
    
    -- Información pública
    display_name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL, -- Para URL: czperu.com/verificar/{slug}
    
    -- Estado del sello
    sello_status VARCHAR(20) NOT NULL DEFAULT 'expired'
        CHECK (sello_status IN ('bronze', 'silver', 'gold', 'expired')),
    sello_expires_at TIMESTAMP,
    
    -- Score actual
    current_score INTEGER CHECK (current_score BETWEEN 0 AND 100),
    risk_level VARCHAR(20) CHECK (risk_level IN ('low', 'medium', 'high', 'critical')),
    
    -- Contadores públicos
    total_verifications INTEGER DEFAULT 0,
    last_verified_at TIMESTAMP,
    
    -- Visibilidad (si cancela, sigue visible pero como "expired")
    is_publicly_visible BOOLEAN DEFAULT TRUE,
    
    -- Certificado actual
    current_certificate_url VARCHAR(500),
    certificate_hash VARCHAR(64), -- SHA256 del PDF
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_public_profiles_slug ON public_profiles(slug);
CREATE INDEX idx_public_profiles_status ON public_profiles(sello_status);
CREATE INDEX idx_public_profiles_visible ON public_profiles(is_publicly_visible) WHERE is_publicly_visible = TRUE;

-- ============================================================
-- 4. INVITES (Sistema de invitaciones - Efecto Red)
-- ============================================================
CREATE TABLE invites (
    invite_code VARCHAR(20) PRIMARY KEY,
    
    -- Quién invita (constructora madre)
    inviter_ruc VARCHAR(11) NOT NULL REFERENCES companies(ruc),
    inviter_company_name VARCHAR(255) NOT NULL,
    
    -- A quién se invita
    invitee_ruc VARCHAR(11), -- Se llena cuando se registra
    invitee_email VARCHAR(255) NOT NULL,
    invitee_company_name VARCHAR(255), -- Nombre tentativo si se conoce
    
    -- Jerarquía (para árbol genealógico)
    depth_level INTEGER DEFAULT 1, -- 1=directo, 2=invitado del invitado, etc.
    parent_invite_code VARCHAR(20) REFERENCES invites(invite_code),
    
    -- Estado
    status VARCHAR(20) DEFAULT 'sent'
        CHECK (status IN ('sent', 'opened', 'clicked', 'registered', 'paid', 'expired', 'cancelled')),
    
    -- Tracking de conversión
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    opened_at TIMESTAMP,
    clicked_at TIMESTAMP,
    registered_at TIMESTAMP,
    converted_to_paid_at TIMESTAMP,
    
    -- Valor económico
    expected_plan VARCHAR(20) DEFAULT 'bronze',
    monthly_value DECIMAL(10,2), -- Cuánto pagaría mensual ($400/$800/$2500)
    
    -- Email tracking
    email_subject VARCHAR(500),
    email_template_used VARCHAR(50),
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP DEFAULT (CURRENT_TIMESTAMP + INTERVAL '30 days'),
    
    CONSTRAINT valid_invitee CHECK (
        (status IN ('sent', 'opened', 'clicked') AND invitee_ruc IS NULL) OR
        (status IN ('registered', 'paid') AND invitee_ruc IS NOT NULL)
    )
);

CREATE INDEX idx_invites_inviter ON invites(inviter_ruc);
CREATE INDEX idx_invites_status ON invites(status);
CREATE INDEX idx_invites_email ON invites(invitee_email);
CREATE INDEX idx_invites_parent ON invites(parent_invite_code);

-- ============================================================
-- 5. VERIFICATION REQUESTS (El core business)
-- ============================================================
CREATE TABLE verification_requests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Quién consulta
    consultant_ruc VARCHAR(11) NOT NULL REFERENCES companies(ruc),
    
    -- A quién se consulta
    target_ruc VARCHAR(11) NOT NULL,
    target_company_name VARCHAR(255),
    
    -- Resultado del score
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
    digital_signature_id VARCHAR(100), -- ID de firma INDECOPI
    
    -- Datos raw completos
    raw_data JSONB,
    
    -- Metadata
    is_cached BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Relación con certificado público
    public_certificate_id UUID
);

CREATE INDEX idx_verifications_consultant ON verification_requests(consultant_ruc);
CREATE INDEX idx_verifications_target ON verification_requests(target_ruc);
CREATE INDEX idx_verifications_created ON verification_requests(created_at);
CREATE INDEX idx_verifications_score ON verification_requests(score);

-- ============================================================
-- 6. COMPANY HIERARCHIES (Red de subcontratistas)
-- ============================================================
CREATE TABLE company_hierarchies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Relación padre-hijo
    parent_ruc VARCHAR(11) NOT NULL REFERENCES companies(ruc),
    child_ruc VARCHAR(11) NOT NULL REFERENCES companies(ruc),
    
    -- Tipo de relación
    relationship_type VARCHAR(50) DEFAULT 'subcontractor'
        CHECK (relationship_type IN ('subcontractor', 'supplier', 'client', 'partner')),
    
    -- Origen de la relación (cómo se creó)
    created_via VARCHAR(50) DEFAULT 'manual'
        CHECK (created_via IN ('manual', 'invite', 'csv_import', 'api')),
    invite_code VARCHAR(20) REFERENCES invites(invite_code),
    
    -- Estado
    is_active BOOLEAN DEFAULT TRUE,
    verified_at TIMESTAMP, -- Cuándo se verificó la relación
    
    -- Metadata
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(parent_ruc, child_ruc)
);

CREATE INDEX idx_hierarchies_parent ON company_hierarchies(parent_ruc);
CREATE INDEX idx_hierarchies_child ON company_hierarchies(child_ruc);
CREATE INDEX idx_hierarchies_active ON company_hierarchies(is_active) WHERE is_active = TRUE;

-- ============================================================
-- 7. API KEYS (Para integraciones ERP)
-- ============================================================
CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_ruc VARCHAR(11) NOT NULL REFERENCES companies(ruc) ON DELETE CASCADE,
    
    -- La key en sí (hasheada)
    key_hash VARCHAR(255) NOT NULL UNIQUE,
    key_prefix VARCHAR(8) NOT NULL, -- Primeros caracteres para identificación
    
    -- Información
    name VARCHAR(100) DEFAULT 'API Key',
    description TEXT,
    
    -- Límites
    rate_limit_per_minute INTEGER DEFAULT 60,
    rate_limit_per_hour INTEGER DEFAULT 1000,
    
    -- Uso
    last_used_at TIMESTAMP,
    usage_count INTEGER DEFAULT 0,
    
    -- Estado
    is_active BOOLEAN DEFAULT TRUE,
    expires_at TIMESTAMP,
    revoked_at TIMESTAMP,
    revoked_reason TEXT,
    
    -- Permisos (scopes)
    scopes JSONB DEFAULT '["read:verifications", "read:profile"]'::jsonb,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255)
);

CREATE INDEX idx_api_keys_company ON api_keys(company_ruc);
CREATE INDEX idx_api_keys_hash ON api_keys(key_hash);
CREATE INDEX idx_api_keys_active ON api_keys(is_active) WHERE is_active = TRUE;

-- ============================================================
-- 8. WEBHOOKS (Para notificaciones en tiempo real)
-- ============================================================
CREATE TABLE webhooks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_ruc VARCHAR(11) NOT NULL REFERENCES companies(ruc) ON DELETE CASCADE,
    
    -- Configuración
    url VARCHAR(500) NOT NULL,
    secret VARCHAR(255) NOT NULL, -- Para verificar firma HMAC
    
    -- Eventos suscritos
    events JSONB NOT NULL, -- ["verification.completed", "company.status_changed", "invite.converted"]
    
    -- Estado
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Métricas
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    last_triggered_at TIMESTAMP,
    last_error TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_webhooks_company ON webhooks(company_ruc);
CREATE INDEX idx_webhooks_active ON webhooks(is_active) WHERE is_active = TRUE;

-- ============================================================
-- 9. AUDIT LOG (Para compliance y debugging)
-- ============================================================
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Quién/Qué
    actor_type VARCHAR(20) NOT NULL -- 'user', 'system', 'api_key', 'webhook'
        CHECK (actor_type IN ('user', 'system', 'api_key', 'webhook')),
    actor_id VARCHAR(255),
    company_ruc VARCHAR(11) REFERENCES companies(ruc),
    
    -- Qué pasó
    action VARCHAR(100) NOT NULL, -- 'verification.created', 'invite.sent', 'company.updated'
    resource_type VARCHAR(50) NOT NULL,
    resource_id VARCHAR(255),
    
    -- Detalles
    old_values JSONB,
    new_values JSONB,
    metadata JSONB,
    
    -- Contexto
    ip_address VARCHAR(45),
    user_agent TEXT,
    request_id VARCHAR(100),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_company ON audit_logs(company_ruc);
CREATE INDEX idx_audit_action ON audit_logs(action);
CREATE INDEX idx_audit_created ON audit_logs(created_at);
CREATE INDEX idx_audit_resource ON audit_logs(resource_type, resource_id);

-- ============================================================
-- 10. SYSTEM CONFIG (Para feature flags y configuración)
-- ============================================================
CREATE TABLE system_config (
    key VARCHAR(100) PRIMARY KEY,
    value JSONB NOT NULL,
    description TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(255)
);

-- Valores iniciales
INSERT INTO system_config (key, value, description) VALUES
('founder_program', '{"max_slots": 10, "duration_months": 3, "open": true}'::jsonb, 'Configuración del Programa Fundador'),
('plans', '{"bronze": {"price": 400, "queries": 1000}, "silver": {"price": 800, "queries": 5000}, "gold": {"price": 2500, "queries": null}}'::jsonb, 'Configuración de planes'),
('features', '{"public_profiles": true, "api_erp": true, "invites": true, "webhooks": false}'::jsonb, 'Feature flags');

-- ============================================================
-- TRIGGERS PARA UPDATED_AT
-- ============================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

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
    c.ruc,
    c.razon_social,
    c.plan_tier,
    COUNT(i.invite_code) as total_invites_sent,
    COUNT(CASE WHEN i.status = 'paid' THEN 1 END) as invites_converted,
    COALESCE(SUM(i.monthly_value), 0) as monthly_network_value,
    COUNT(DISTINCT ch.child_ruc) as active_subcontractors
FROM companies c
LEFT JOIN invites i ON c.ruc = i.inviter_ruc
LEFT JOIN company_hierarchies ch ON c.ruc = ch.parent_ruc AND ch.is_active = TRUE
WHERE c.plan_tier IN ('gold', 'founder')
GROUP BY c.ruc, c.razon_social, c.plan_tier;

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
    END as priority_score
FROM founder_applications fa
WHERE fa.status = 'pending'
ORDER BY priority_score DESC, created_at ASC;
