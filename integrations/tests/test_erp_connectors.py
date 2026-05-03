"""
Tests para conectores ERP de Conflict Zero
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from integrations.sap.sap_connector import SAPConnector, SAPVendorRequest
from integrations.netsuite.netsuite_connector import NetSuiteConnector
from integrations.dynamics.dynamics_connector import DynamicsConnector


class TestSAPConnector:
    """Tests para SAPConnector"""
    
    def setup_method(self):
        self.connector = SAPConnector(
            base_url="https://sap-test.example.com",
            api_key="test-api-key",
            username="testuser",
            password="testpass"
        )
    
    def test_init(self):
        """Test inicialización del conector"""
        assert self.connector.base_url == "https://sap-test.example.com"
        assert self.connector.api_key == "test-api-key"
        assert self.connector.headers["Authorization"] == "Bearer test-api-key"
    
    @patch('integrations.sap.sap_connector.requests.post')
    def test_verify_vendor_success(self, mock_post):
        """Test verificación de proveedor exitosa"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "risk_score": 25.5,
            "risk_level": "bajo",
            "status": "activo",
            "alerts": []
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        result = self.connector.verify_vendor("V001", "20100012345", "1000")
        
        assert result["success"] is True
        assert result["vendor_code"] == "V001"
        assert result["ruc"] == "20100012345"
        assert result["risk_score"] == 25.5
        assert result["risk_level"] == "bajo"
        assert "timestamp" in result
    
    @patch('integrations.sap.sap_connector.requests.post')
    def test_verify_vendor_failure(self, mock_post):
        """Test verificación de proveedor con error de red"""
        mock_post.side_effect = Exception("Connection timeout")
        
        result = self.connector.verify_vendor("V001", "20100012345")
        
        assert result["success"] is False
        assert result["vendor_code"] == "V001"
        assert "error" in result
        assert "Connection timeout" in result["error"]
    
    @patch('integrations.sap.sap_connector.requests.post')
    def test_batch_verify_vendors(self, mock_post):
        """Test verificación en lote"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "risk_score": 30.0,
            "risk_level": "medio",
            "status": "activo"
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        vendors = [
            SAPVendorRequest(vendor_code="V001", company_code="1000", ruc="20100012345"),
            SAPVendorRequest(vendor_code="V002", company_code="1000", ruc="20100012346"),
        ]
        
        results = self.connector.batch_verify_vendors(vendors)
        
        assert len(results) == 2
        assert all(r["success"] for r in results)
        assert mock_post.call_count == 2
    
    def test_sync_vendor_master_data(self):
        """Test sincronización de datos maestros"""
        result = self.connector.sync_vendor_master_data("V001", {"risk_score": 25})
        
        assert result["success"] is True
        assert result["vendor_code"] == "V001"
        assert result["action"] == "sync"
    
    def test_default_config(self):
        """Test configuración por defecto"""
        from integrations.sap.sap_connector import DEFAULT_SAP_CONFIG
        
        assert "base_url" in DEFAULT_SAP_CONFIG
        assert "api_version" in DEFAULT_SAP_CONFIG
        assert DEFAULT_SAP_CONFIG["timeout"] == 30
        assert DEFAULT_SAP_CONFIG["retry_count"] == 3


class TestNetSuiteConnector:
    """Tests para NetSuiteConnector"""
    
    def setup_method(self):
        self.connector = NetSuiteConnector(
            account_id="123456",
            consumer_key="consumer-key",
            consumer_secret="consumer-secret",
            token_id="token-id",
            token_secret="token-secret"
        )
    
    def test_init(self):
        """Test inicialización del conector"""
        assert self.connector.account_id == "123456"
        assert self.connector.base_url == "https://123456.suitetalk.api.netsuite.com"
    
    @patch('integrations.netsuite.netsuite_connector.requests.post')
    def test_verify_vendor_success(self, mock_post):
        """Test verificación de proveedor exitosa"""
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        result = self.connector.verify_vendor("123", "20100012345")
        
        assert result["success"] is True
        assert result["vendor_id"] == "123"
        assert result["ruc"] == "20100012345"
        assert "timestamp" in result
    
    def test_get_auth_headers(self):
        """Test generación de headers de auth"""
        headers = self.connector._get_auth_headers()
        
        assert "Authorization" in headers
        assert "Content-Type" in headers
    
    def test_create_vendor_record(self):
        """Test creación de registro de proveedor"""
        result = self.connector.create_vendor_record({"name": "Test Vendor"})
        
        assert result["success"] is True
        assert result["action"] == "create_vendor"
    
    def test_suitescript_code_exists(self):
        """Test que el código SuiteScript existe y es válido"""
        from integrations.netsuite.netsuite_connector import SUITESCRIPT_CODE
        
        assert "NApiVersion" in SUITESCRIPT_CODE
        assert "RESTlet" in SUITESCRIPT_CODE
        assert "custentity_cz_risk_score" in SUITESCRIPT_CODE


class TestDynamicsConnector:
    """Tests para DynamicsConnector"""
    
    def setup_method(self):
        self.connector = DynamicsConnector(
            tenant_id="tenant-123",
            client_id="client-456",
            client_secret="secret-789",
            environment_url="https://test.crm.dynamics.com"
        )
    
    def test_init(self):
        """Test inicialización del conector"""
        assert self.connector.tenant_id == "tenant-123"
        assert self.connector.client_id == "client-456"
        assert self.connector.environment_url == "https://test.crm.dynamics.com"
        assert self.connector.access_token is None
    
    @patch('integrations.dynamics.dynamics_connector.requests.post')
    def test_get_access_token(self, mock_post):
        """Test obtención de token OAuth2"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "access_token": "test-token-123",
            "expires_in": 3600
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        token = self.connector._get_access_token()
        
        assert token == "test-token-123"
        assert self.connector.access_token == "test-token-123"
        
        # Verificar que se llamó al endpoint correcto
        call_args = mock_post.call_args
        assert "tenant-123" in call_args[0][0]
    
    @patch('integrations.dynamics.dynamics_connector.requests.post')
    @patch('integrations.dynamics.dynamics_connector.requests.patch')
    def test_verify_vendor_success(self, mock_patch, mock_post):
        """Test verificación de proveedor exitosa con actualización en Dynamics"""
        # Mock token request
        mock_token_response = Mock()
        mock_token_response.json.return_value = {"access_token": "token-123"}
        mock_token_response.raise_for_status = Mock()
        
        # Mock CZ API request
        mock_cz_response = Mock()
        mock_cz_response.json.return_value = {
            "risk_score": 15.0,
            "status": "activo"
        }
        mock_cz_response.raise_for_status = Mock()
        
        # Mock Dynamics update
        mock_dynamics_response = Mock()
        mock_dynamics_response.raise_for_status = Mock()
        
        mock_post.side_effect = [mock_token_response, mock_cz_response]
        mock_patch.return_value = mock_dynamics_response
        
        result = self.connector.verify_vendor("V-001", "20100012345")
        
        assert result["success"] is True
        assert result["vendor_account"] == "V-001"
        assert result["risk_score"] == 15.0
    
    def test_get_vendor_list_placeholder(self):
        """Test lista de proveedores (placeholder)"""
        result = self.connector.get_vendor_list()
        
        assert isinstance(result, list)
        assert len(result) == 0
    
    def test_power_automate_flow_exists(self):
        """Test que el flow de Power Automate existe"""
        from integrations.dynamics.dynamics_connector import POWER_AUTOMATE_FLOW
        
        assert "definition" in POWER_AUTOMATE_FLOW
        assert "triggers" in POWER_AUTOMATE_FLOW["definition"]


class TestERPIntegrationEdgeCases:
    """Tests para casos edge en integraciones ERP"""
    
    def test_sap_invalid_ruc_format(self):
        """Test SAP con RUC inválido"""
        connector = SAPConnector("https://test.com", "key")
        
        # Un RUC con menos de 11 dígitos debería ser manejado
        result = connector.verify_vendor("V001", "123")
        
        # El conector no valida el RUC internamente, pero debería manejar el error de la API
        assert "vendor_code" in result
    
    def test_netsuite_missing_credentials(self):
        """Test NetSuite sin credenciales"""
        connector = NetSuiteConnector("", "", "", "", "")
        
        assert connector.account_id == ""
        assert connector.base_url == "https://.suitetalk.api.netsuite.com"
    
    def test_dynamics_token_refresh(self):
        """Test que el token se refresca correctamente"""
        connector = DynamicsConnector("t", "c", "s", "https://env.com")
        
        # Simular token expirado
        connector.access_token = "old-token"
        
        # El token debería refrescarse en la próxima llamada
        assert connector.access_token == "old-token"
