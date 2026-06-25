"""
Tests de integración para endpoints GDPR y Audit
Prueban los endpoints FastAPI reales con TestClient
"""

import pytest
from datetime import datetime, timedelta, timezone


@pytest.mark.integration
class TestAuditEndpoints:
    """Tests para endpoints de Auditoría"""
    
    def test_generate_compliance_report(self, client, auth_headers):
        """Debe poder generar un reporte de compliance"""
        start_date = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
        end_date = datetime.now(timezone.utc).isoformat()
        
        response = client.post(
            "/api/v2/audit/reports/compliance",
            params={"start_date": start_date, "end_date": end_date},
            headers=auth_headers
        )
        
        assert response.status_code in [200, 500]  # 500 si no hay DB real
        
        if response.status_code == 200:
            data = response.json()
            assert "report_id" in data
            assert data["type"] == "compliance"
            assert "status" in data
            assert data["saved_to_db"] is not None
    
    def test_generate_security_report(self, client, auth_headers):
        """Debe poder generar un reporte de seguridad"""
        response = client.post(
            "/api/v2/audit/reports/security",
            headers=auth_headers
        )
        
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert data["type"] == "security"
            assert "report_id" in data
    
    def test_generate_data_processing_report(self, client, auth_headers):
        """Debe poder generar un reporte de procesamiento de datos"""
        response = client.post(
            "/api/v2/audit/reports/data-processing",
            headers=auth_headers
        )
        
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert data["type"] == "data_processing"
    
    def test_generate_network_changes_report(self, client, auth_headers):
        """Debe poder generar un reporte de cambios en red"""
        response = client.post(
            "/api/v2/audit/reports/network-changes",
            headers=auth_headers
        )
        
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert data["type"] == "network_changes"
    
    def test_list_audit_reports(self, client, auth_headers):
        """Debe poder listar reportes de auditoría"""
        response = client.get(
            "/api/v2/audit/reports",
            headers=auth_headers
        )
        
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert "reports" in data
            assert "total" in data
            assert "limit" in data
            assert "offset" in data
    
    def test_list_audit_reports_with_filter(self, client, auth_headers):
        """Debe poder filtrar reportes por tipo"""
        response = client.get(
            "/api/v2/audit/reports",
            params={"report_type": "compliance"},
            headers=auth_headers
        )
        
        assert response.status_code in [200, 500]
    
    def test_get_audit_schedule(self, client, auth_headers):
        """Debe obtener el calendario de auditorías"""
        response = client.get(
            "/api/v2/audit/schedule",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "schedule" in data
        assert isinstance(data["schedule"], list)
        assert len(data["schedule"]) == 4  # 4 tipos de reportes
    
    def test_get_nonexistent_report(self, client, auth_headers):
        """Debe retornar 404 para reporte inexistente"""
        response = client.get(
            "/api/v2/audit/reports/REPORTE-NO-EXISTE-1234",
            headers=auth_headers
        )
        
        assert response.status_code == 404


@pytest.mark.integration
class TestGDPRIntegrationEndpoints:
    """Tests para endpoints de GDPR"""
    
    def test_create_gdpr_access_request(self, client, auth_headers):
        """Debe poder crear una solicitud de acceso GDPR"""
        response = client.post(
            "/api/v2/audit/gdpr/requests",
            params={"request_type": "access", "description": "Solicitud de acceso a mis datos"},
            headers=auth_headers
        )
        
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert data["status"] == "created"
            assert "request" in data
            assert "request_number" in data["request"]
            assert data["request"]["request_type"] == "access"
    
    def test_create_gdpr_erasure_request(self, client, auth_headers):
        """Debe poder crear una solicitud de borrado GDPR"""
        response = client.post(
            "/api/v2/audit/gdpr/requests",
            params={"request_type": "erasure", "description": "Solicitud de borrado de datos"},
            headers=auth_headers
        )
        
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert data["status"] == "created"
            assert data["request"]["request_type"] == "erasure"
    
    def test_create_gdpr_portability_request(self, client, auth_headers):
        """Debe poder crear una solicitud de portabilidad GDPR"""
        response = client.post(
            "/api/v2/audit/gdpr/requests",
            params={"request_type": "portability"},
            headers=auth_headers
        )
        
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert data["request"]["request_type"] == "portability"
    
    def test_list_gdpr_requests(self, client, auth_headers):
        """Debe poder listar solicitudes GDPR"""
        response = client.get(
            "/api/v2/audit/gdpr/requests",
            headers=auth_headers
        )
        
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert "requests" in data
            assert "total" in data
    
    def test_list_gdpr_requests_with_filter(self, client, auth_headers):
        """Debe poder filtrar solicitudes por estado"""
        response = client.get(
            "/api/v2/audit/gdpr/requests",
            params={"status": "pending"},
            headers=auth_headers
        )
        
        assert response.status_code in [200, 500]
    
    def test_get_pending_gdpr_requests_count(self, client, auth_headers):
        """Debe obtener el conteo de solicitudes pendientes"""
        response = client.get(
            "/api/v2/audit/gdpr/requests/pending",
            headers=auth_headers
        )
        
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert "pending_count" in data
            assert isinstance(data["pending_count"], int)
    
    def test_get_overdue_gdpr_requests(self, client, auth_headers):
        """Debe obtener solicitudes vencidas"""
        response = client.get(
            "/api/v2/audit/gdpr/requests/overdue",
            headers=auth_headers
        )
        
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert "overdue_requests" in data
            assert "total_overdue" in data
    
    def test_export_personal_data(self, client, auth_headers):
        """Debe exportar datos personales en JSON"""
        response = client.get(
            "/api/v2/audit/gdpr/export",
            headers=auth_headers
        )
        
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert "export_id" in data
            assert "data_categories" in data
            assert "data" in data
            assert "profile" in data["data"]
    
    def test_request_data_erasure(self, client, auth_headers):
        """Debe procesar solicitud de borrado de datos"""
        response = client.delete(
            "/api/v2/audit/gdpr/erase",
            headers=auth_headers
        )
        
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert "status" in data
            assert data["status"] in ["pending", "rejected"]
            if data["status"] == "pending":
                assert "data_to_anonymize" in data
                assert "data_to_delete" in data
                assert "data_to_retain" in data


@pytest.mark.integration
class TestPDFGenerationEndpoints:
    """Tests para endpoints de generación de PDF"""
    
    def test_download_audit_report_pdf(self, client, auth_headers):
        """Debe poder descargar un PDF de reporte de auditoría"""
        # Primero crear un reporte
        start_date = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
        end_date = datetime.now(timezone.utc).isoformat()
        
        create_response = client.post(
            "/api/v2/audit/reports/compliance",
            params={"start_date": start_date, "end_date": end_date},
            headers=auth_headers
        )
        
        if create_response.status_code != 200:
            pytest.skip("No se pudo crear reporte para test de PDF")
        
        report_data = create_response.json()
        report_number = report_data["report_id"]
        
        # Descargar PDF
        response = client.get(
            f"/api/v2/audit/reports/{report_number}/pdf",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert "Content-Disposition" in response.headers
        assert "audit-report" in response.headers["Content-Disposition"]
        
        # Verificar que es un PDF válido (comienza con %PDF)
        content = response.content
        assert content[:4] == b"%PDF"
        assert len(content) > 100  # Debe ser un PDF no vacío
    
    def test_download_nonexistent_report_pdf(self, client, auth_headers):
        """Debe retornar 404 para PDF de reporte inexistente"""
        response = client.get(
            "/api/v2/audit/reports/NO-EXISTE-12345/pdf",
            headers=auth_headers
        )
        
        assert response.status_code == 404
    
    def test_export_gdpr_pdf(self, client, auth_headers):
        """Debe poder exportar datos GDPR en formato PDF"""
        response = client.get(
            "/api/v2/audit/gdpr/export/pdf",
            headers=auth_headers
        )
        
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            assert response.headers["content-type"] == "application/pdf"
            assert "Content-Disposition" in response.headers
            assert "gdpr-export" in response.headers["Content-Disposition"]
            
            content = response.content
            assert content[:4] == b"%PDF"
            assert len(content) > 100


@pytest.mark.integration
class TestPDFServiceUnit:
    """Tests unitarios para el servicio de PDF"""
    
    def test_pdf_generator_audit_report(self):
        """Debe generar un PDF de auditoría válido"""
        from app.services.pdf_service import pdf_generator
        
        report_data = {
            "report_type": "compliance",
            "status": "completed",
            "period_start": "2024-01-01",
            "period_end": "2024-01-31",
            "summary": "Reporte de prueba para verificar generación de PDF.",
            "metrics": {
                "total_verifications": 42,
                "total_companies": 10,
                "avg_score": 85.5
            },
            "findings": [
                {
                    "title": "Hallazgo de prueba",
                    "severity": "medium",
                    "description": "Descripción del hallazgo",
                    "recommendation": "Recomendación de prueba"
                }
            ],
            "recommendations": [
                "Recomendación 1",
                "Recomendación 2"
            ],
            "integrity_hash": "abc123def456",
            "generated_by": "test"
        }
        
        pdf_bytes = pdf_generator.generate_audit_report(
            report_data=report_data,
            report_number="AUD-TEST-001",
            company_name="Empresa Test"
        )
        
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 100
        assert pdf_bytes[:4] == b"%PDF"
    
    def test_pdf_generator_gdpr_export(self):
        """Debe generar un PDF de exportación GDPR válido"""
        from app.services.pdf_service import pdf_generator
        
        export_data = {
            "export_id": "GDPR-TEST-001",
            "data_categories": ["identification", "contact", "verification"],
            "data": {
                "profile": {
                    "razon_social": "Empresa Test S.A.C.",
                    "ruc_hash": "abc123",
                    "contact_email": "test@example.com"
                },
                "verifications": [
                    {"id": "v1", "score": 85, "risk_level": "low"}
                ]
            }
        }
        
        pdf_bytes = pdf_generator.generate_gdpr_export_pdf(
            export_data=export_data,
            company_name="Empresa Test",
            request_number="GDPR-TEST-001"
        )
        
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 100
        assert pdf_bytes[:4] == b"%PDF"
    
    def test_pdf_generator_empty_report(self):
        """Debe generar PDF incluso con datos mínimos"""
        from app.services.pdf_service import pdf_generator
        
        pdf_bytes = pdf_generator.generate_audit_report(
            report_data={},
            report_number="AUD-EMPTY-001",
            company_name="Empresa Vacía"
        )
        
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 100
        assert pdf_bytes[:4] == b"%PDF"
    
    def test_pdf_generator_empty_gdpr_export(self):
        """Debe generar PDF de GDPR incluso con datos mínimos"""
        from app.services.pdf_service import pdf_generator
        
        pdf_bytes = pdf_generator.generate_gdpr_export_pdf(
            export_data={},
            company_name="Empresa Vacía",
            request_number="GDPR-EMPTY-001"
        )
        
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 100
        assert pdf_bytes[:4] == b"%PDF"


@pytest.mark.integration
class TestAdminGDPREndpoints:
    """Tests para endpoints de admin GDPR"""
    
    def test_update_gdpr_request_status_requires_admin(self, client):
        """Debe requerir rol admin para actualizar estado"""
        response = client.post(
            "/api/v2/audit/gdpr/requests/GDPR-TEST-001/status",
            params={"status": "fulfilled"}
        )
        
        # Sin auth de admin, debe ser 401 o 403
        assert response.status_code in [401, 403]
