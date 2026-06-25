"""
Tests para módulos GDPR y Audit (Fase 3)
"""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

# Tests para GDPR Compliance Service
def test_gdpr_mask_email():
    """Test de enmascaramiento de email"""
    from app.core.gdpr import mask_email
    assert mask_email("juan@example.com") == "j***@example.com"
    assert mask_email("ab@test.com") == "a***@test.com"
    assert mask_email("x@y.z") == "*@y.z"
    assert mask_email("invalid") == "***"


def test_gdpr_mask_ruc():
    """Test de enmascaramiento de RUC"""
    from app.core.gdpr import mask_ruc
    assert mask_ruc("20512345678") == "20*****78"
    assert mask_ruc("1234") == "12*****34"
    assert mask_ruc("12") == "***"


def test_gdpr_hash_data_subject_id():
    """Test de generación de ID anonimizado"""
    from app.core.gdpr import hash_data_subject_id
    result = hash_data_subject_id("test-company-id")
    assert len(result) == 16
    assert isinstance(result, str)
    # Debe ser determinístico
    assert hash_data_subject_id("test-company-id") == result


def test_gdpr_get_data_retention_schedule():
    """Test de política de retención de datos"""
    from app.core.gdpr import GDPRComplianceService
    schedule = GDPRComplianceService.get_data_retention_schedule()
    assert "verification_requests" in schedule
    assert "audit_logs" in schedule
    assert "payment_records" in schedule
    assert schedule["payment_records"] == 365 * 5  # 5 años


def test_gdpr_get_privacy_notice():
    """Test de generación de avisos de privacidad"""
    from app.core.gdpr import GDPRPolicy
    es_notice = GDPRPolicy.get_privacy_notice("ES")
    assert "RGPD" in es_notice
    
    pe_notice = GDPRPolicy.get_privacy_notice("PE")
    assert "Ley 29733" in pe_notice
    
    # Default debe ser PE
    default_notice = GDPRPolicy.get_privacy_notice("XX")
    assert "Ley 29733" in default_notice


def test_gdpr_legal_bases():
    """Test de bases legales GDPR"""
    from app.core.gdpr import GDPRPolicy
    assert "consent" in GDPRPolicy.LEGAL_BASES
    assert "contract" in GDPRPolicy.LEGAL_BASES
    assert "legal_obligation" in GDPRPolicy.LEGAL_BASES


def test_gdpr_special_categories():
    """Test de categorías especiales de datos"""
    from app.core.gdpr import GDPRPolicy
    assert "genetic_data" in GDPRPolicy.SPECIAL_CATEGORIES
    assert "biometric_data" in GDPRPolicy.SPECIAL_CATEGORIES
    assert "health_data" in GDPRPolicy.SPECIAL_CATEGORIES


# Tests para Audit Service
def test_audit_report_id_generation():
    """Test de generación de ID de reporte"""
    from app.services.audit_service import AuditReport, AuditReportType
    report = AuditReport(
        report_type=AuditReportType.COMPLIANCE,
        company_id="test-company",
        start_date=datetime.now(timezone.utc),
        end_date=datetime.now(timezone.utc)
    )
    assert report.report_id.startswith("AUD-")
    assert len(report.report_id) > 4


def test_audit_report_add_section():
    """Test de adición de secciones al reporte"""
    from app.services.audit_service import AuditReport, AuditReportType
    report = AuditReport(
        report_type=AuditReportType.COMPLIANCE,
        company_id="test-company",
        start_date=datetime.now(timezone.utc),
        end_date=datetime.now(timezone.utc)
    )
    report.add_section("Test Section", {"key": "value"})
    assert "sections" in report.data
    assert len(report.data["sections"]) == 1
    assert report.data["sections"][0]["title"] == "Test Section"


def test_audit_report_sign():
    """Test de firma de reporte"""
    from app.services.audit_service import AuditReport, AuditReportType
    report = AuditReport(
        report_type=AuditReportType.COMPLIANCE,
        company_id="test-company",
        start_date=datetime.now(timezone.utc),
        end_date=datetime.now(timezone.utc)
    )
    report.add_section("Test", {"data": "test"})
    report.sign_report("test-signer")
    
    assert report.signed is True
    assert report.status == "signed"
    assert report.hash is not None
    assert len(report.hash) == 64  # SHA-256


def test_audit_report_to_dict():
    """Test de exportación de reporte a diccionario"""
    from app.services.audit_service import AuditReport, AuditReportType
    report = AuditReport(
        report_type=AuditReportType.SECURITY,
        company_id="test-company",
        start_date=datetime.now(timezone.utc),
        end_date=datetime.now(timezone.utc)
    )
    data = report.to_dict()
    
    assert data["report_type"] == "security"
    assert data["company_id"] == "test-company"
    assert "period" in data
    assert "generated" in data
    assert data["status"] == "pending"


def test_audit_scheduler_frequencies():
    """Test de frecuencias del programador"""
    from app.services.audit_service import AuditScheduler
    assert AuditScheduler.SCHEDULES["compliance"] == "monthly"
    assert AuditScheduler.SCHEDULES["security"] == "weekly"
    assert AuditScheduler.SCHEDULES["data_processing"] == "quarterly"
    assert AuditScheduler.SCHEDULES["network_changes"] == "daily"


def test_audit_scheduler_get_next_date():
    """Test de cálculo de próxima fecha"""
    from app.services.audit_service import AuditScheduler
    now = datetime.now(timezone.utc)
    
    next_daily = AuditScheduler.get_next_report_date(now, "network_changes")
    assert next_daily == now + timedelta(days=1)
    
    next_weekly = AuditScheduler.get_next_report_date(now, "security")
    assert next_weekly == now + timedelta(weeks=1)
    
    next_monthly = AuditScheduler.get_next_report_date(now, "compliance")
    assert next_monthly == now + timedelta(days=30)


def test_audit_scheduler_should_generate():
    """Test de decisión de generación de reporte"""
    from app.services.audit_service import AuditScheduler
    now = datetime.now(timezone.utc)
    
    # Sin último reporte, debe generar
    assert AuditScheduler.should_generate_report("company1", "compliance", None) is True
    
    # Con fecha futura, no debe generar
    future = now + timedelta(days=10)
    assert AuditScheduler.should_generate_report("company1", "compliance", future) is False
    
    # Con fecha pasada (más de 30 días para mensual), debe generar
    past = now - timedelta(days=40)
    assert AuditScheduler.should_generate_report("company1", "compliance", past) is True


def test_audit_scheduler_get_schedule_calendar():
    """Test de calendario de auditorías"""
    from app.services.audit_service import AuditScheduler
    calendar = AuditScheduler.get_schedule_calendar()
    
    assert isinstance(calendar, list)
    assert len(calendar) == 4  # 4 tipos de reportes
    
    for item in calendar:
        assert "report_type" in item
        assert "frequency" in item
        assert "next_scheduled" in item
        assert "description" in item
        assert "is_active" in item
        assert item["is_active"] is True


# Tests con mock de DB
def test_audit_report_service_get_reports_by_company_no_db():
    """Test de fallback sin DB"""
    from app.services.audit_service import AuditReportService
    # Con db=None, debería retornar lista vacía
    result = AuditReportService.get_reports_by_company(None, "test-company")
    # Esto fallará si no se maneja el None, lo cual es intencional para detectar el bug
    # El servicio debería manejar db=None gracefully
    assert isinstance(result, list)


def test_gdpr_service_get_pending_count_no_db():
    """Test de fallback sin DB"""
    from app.core.gdpr import GDPRComplianceService
    result = GDPRComplianceService.get_pending_requests_count(None)
    assert result == 0


def test_gdpr_service_get_overdue_no_db():
    """Test de fallback sin DB"""
    from app.core.gdpr import GDPRComplianceService
    result = GDPRComplianceService.get_overdue_requests(None)
    assert result == []
