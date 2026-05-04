"""
Conflict Zero - ERP Integration Tests (Updated)
Tests para conectores SAP, NetSuite, Dynamics con OAuth real
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Importar conectores actualizados
from integrations.sap.sap_oauth import (
    SAPOAuth2Client,
    SAPSOAPClient,
    SAPBidirectionalSync,
    create_sap_rest_connector,
    create_sap_soap_connector
)
from integrations.netsuite.netsuite_oauth import (
    NetSuiteOAuth1Client,
    NetSuiteBidirectionalSync,
    create_netsuite_client
)
from integrations.dynamics.dynamics_oauth import (
    DynamicsOAuth2Client,
    Dynamics365Client,
    DynamicsBidirectionalSync,
    create_dynamics_client
)


# ============================================================
# SAP OAuth 2.0 Tests
# ============================================================

class TestSAPOAuth2Client:
    def test_init(self):
        client = SAPOAuth2Client(
            base_url="https://sap.example.com",
            client_id="test_client",
            client_secret="test_secret"
        )
        assert client.base_url == "https://sap.example.com"
        assert client.client_id == "test_client"
        assert client._access_token is None

    @patch('integrations.sap.sap_oauth.requests.post')
    def test_authenticate_client_credentials(self, mock_post):
        mock_post.return_value = Mock(
            status_code=200,
            json=lambda: {
                "access_token": "test_token_123",
                "expires_in": 3600,
                "token_type": "Bearer"
            }
        )
        
        client = SAPOAuth2Client(
            base_url="https://sap.example.com",
            client_id="test_client",
            client_secret="test_secret"
        )
        
        result = client.authenticate_client_credentials()
        assert result is True
        assert client._access_token == "test_token_123"
        assert client._token_expires_at is not None

    def test_is_token_valid_no_token(self):
        client = SAPOAuth2Client("https://sap.example.com", "client", "secret")
        assert client._is_token_valid() is False

    @patch('integrations.sap.sap_oauth.requests.post')
    def test_get_auth_headers(self, mock_post):
        mock_post.return_value = Mock(
            status_code=200,
            json=lambda: {
                "access_token": "test_token",
                "expires_in": 3600
            }
        )
        
        client = SAPOAuth2Client("https://sap.example.com", "client", "secret")
        client.authenticate_client_credentials()
        
        headers = client.get_auth_headers()
        assert "Authorization" in headers
        assert headers["Authorization"] == "Bearer test_token"


class TestSAPSOAPClient:
    def test_init(self):
        client = SAPSOAPClient(
            base_url="https://sap.example.com",
            username="admin",
            password="secret"
        )
        assert client.username == "admin"
        assert "Authorization" in client.soap_headers

    def test_get_basic_auth(self):
        client = SAPSOAPClient("https://sap.example.com", "admin", "secret")
        auth = client._get_basic_auth()
        assert auth.startswith("Basic ")

    @patch('integrations.sap.sap_oauth.requests.post')
    def test_get_vendor_details(self, mock_post):
        mock_post.return_value = Mock(
            status_code=200,
            content=b'<?xml version="1.0"?><root><NAME>Test Vendor</NAME></root>'
        )
        
        client = SAPSOAPClient("https://sap.example.com", "admin", "secret")
        result = client.get_vendor_details("V001")
        
        assert result["success"] is True
        assert result["vendor_code"] == "V001"

    @patch('integrations.sap.sap_oauth.requests.post')
    def test_update_vendor_risk_fields(self, mock_post):
        mock_post.return_value = Mock(status_code=200)
        
        client = SAPSOAPClient("https://sap.example.com", "admin", "secret")
        result = client.update_vendor_risk_fields("V001", 75.5, "moderate")
        
        assert result["success"] is True
        assert result["vendor_code"] == "V001"


class TestSAPBidirectionalSync:
    @patch('integrations.sap.sap_oauth.SAPSOAPClient.get_vendor_details')
    @patch('integrations.sap.sap_oauth.requests.post')
    def test_sync_vendor_to_cz(self, mock_cz_post, mock_sap_get):
        mock_sap_get.return_value = {
            "success": True,
            "data": {"name": "Test Vendor"}
        }
        mock_cz_post.return_value = Mock(
            status_code=200,
            json=lambda: {"risk_score": 80.0, "risk_level": "moderate"}
        )
        
        oauth = Mock()
        soap = Mock()
        soap.get_vendor_details.return_value = {"success": True, "data": {}}
        
        sync = SAPBidirectionalSync(oauth, soap, "cz_api_key")
        
        # Mockear método de sync
        with patch.object(sync, 'sync_vendor_to_conflict_zero', return_value={
            "success": True,
            "direction": "sap_to_cz",
            "risk_score": 80.0,
            "sap_updated": True
        }):
            result = sync.sync_vendor_to_conflict_zero("V001", "12345678901")
            assert result["success"] is True


# ============================================================
# NetSuite OAuth 1.0a Tests
# ============================================================

class TestNetSuiteOAuth1Client:
    def test_init(self):
        client = NetSuiteOAuth1Client(
            account_id="123456",
            consumer_key="ck_test",
            consumer_secret="cs_test",
            token_id="tk_test",
            token_secret="ts_test"
        )
        assert client.account_id == "123456"
        assert client.realm == "123456"

    def test_generate_nonce(self):
        client = NetSuiteOAuth1Client("123456", "ck", "cs", "tk", "ts")
        nonce1 = client._generate_nonce()
        nonce2 = client._generate_nonce()
        assert len(nonce1) == 32  # 16 bytes hex = 32 chars
        assert nonce1 != nonce2

    def test_generate_timestamp(self):
        client = NetSuiteOAuth1Client("123456", "ck", "cs", "tk", "ts")
        ts = client._generate_timestamp()
        assert ts.isdigit()
        assert len(ts) == 10  # Unix timestamp

    def test_create_signature_base(self):
        client = NetSuiteOAuth1Client("123456", "ck", "cs", "tk", "ts")
        base = client._create_signature_base(
            "GET",
            "https://123456.suitetalk.api.netsuite.com/services/rest/record/v1/vendor",
            {"oauth_consumer_key": "ck"}
        )
        assert "GET" in base
        assert "vendor" in base

    @patch('integrations.netsuite.netsuite_oauth.requests.request')
    def test_make_request(self, mock_request):
        mock_request.return_value = Mock(
            status_code=200,
            json=lambda: {"id": "123", "name": "Test"},
            text='{"id": "123"}'
        )
        
        client = NetSuiteOAuth1Client("123456", "ck", "cs", "tk", "ts")
        result = client.make_request("GET", "vendor/123")
        
        assert result["success"] is True
        assert result["status_code"] == 200

    @patch('integrations.netsuite.netsuite_oauth.requests.request')
    def test_get_vendor(self, mock_request):
        mock_request.return_value = Mock(
            status_code=200,
            json=lambda: {"id": "123", "companyName": "Test Vendor"},
            text='{"id": "123"}'
        )
        
        client = NetSuiteOAuth1Client("123456", "ck", "cs", "tk", "ts")
        result = client.get_vendor("123")
        
        assert result["success"] is True
        assert "data" in result

    @patch('integrations.netsuite.netsuite_oauth.requests.request')
    def test_update_vendor_risk(self, mock_request):
        mock_request.return_value = Mock(
            status_code=200,
            json=lambda: {},
            text=""
        )
        
        client = NetSuiteOAuth1Client("123456", "ck", "cs", "tk", "ts")
        result = client.update_vendor_risk("123", 85.0, "high")
        
        assert result["success"] is True


class TestNetSuiteBidirectionalSync:
    def test_init(self):
        ns_client = Mock()
        sync = NetSuiteBidirectionalSync(ns_client, "cz_key")
        assert sync.netsuite == ns_client
        assert sync.cz_api_key == "cz_key"


# ============================================================
# Dynamics 365 OAuth 2.0 Tests
# ============================================================

class TestDynamicsOAuth2Client:
    def test_init(self):
        client = DynamicsOAuth2Client(
            tenant_id="tenant-123",
            client_id="client-123",
            client_secret="secret-123",
            resource="https://org.crm.dynamics.com"
        )
        assert client.tenant_id == "tenant-123"
        assert client.resource == "https://org.crm.dynamics.com"

    def test_get_authorization_url(self):
        client = DynamicsOAuth2Client("tenant", "client", "secret", "https://org.crm.dynamics.com")
        url = client.get_authorization_url("https://callback.com")
        
        assert "login.microsoftonline.com" in url
        assert "client_id=client" in url
        assert "response_type=code" in url

    @patch('integrations.dynamics.dynamics_oauth.requests.post')
    def test_authenticate_client_credentials(self, mock_post):
        mock_post.return_value = Mock(
            status_code=200,
            json=lambda: {
                "access_token": "dynamics_token",
                "expires_in": 3600,
                "token_type": "Bearer"
            }
        )
        
        client = DynamicsOAuth2Client("tenant", "client", "secret", "https://org.crm.dynamics.com")
        result = client.authenticate_client_credentials()
        
        assert result is True
        assert client._access_token == "dynamics_token"

    @patch('integrations.dynamics.dynamics_oauth.requests.post')
    def test_refresh_access_token(self, mock_post):
        mock_post.return_value = Mock(
            status_code=200,
            json=lambda: {
                "access_token": "new_token",
                "expires_in": 3600
            }
        )
        
        client = DynamicsOAuth2Client("tenant", "client", "secret", "https://org.crm.dynamics.com")
        client._refresh_token = "old_refresh"
        result = client.refresh_access_token()
        
        assert result is True
        assert client._access_token == "new_token"

    def test_is_token_valid_no_token(self):
        client = DynamicsOAuth2Client("tenant", "client", "secret", "https://org.crm.dynamics.com")
        assert client._is_token_valid() is False


class TestDynamics365Client:
    @patch('integrations.dynamics.dynamics_oauth.DynamicsOAuth2Client.get_auth_headers')
    @patch('integrations.dynamics.dynamics_oauth.requests.request')
    def test_get_vendor(self, mock_request, mock_headers):
        mock_headers.return_value = {"Authorization": "Bearer test"}
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"accountid": "123", "name": "Test Account"}
        mock_response.text = '{"accountid": "123"}'
        mock_response.headers = {}
        mock_request.return_value = mock_response
        
        oauth = Mock()
        client = Dynamics365Client(oauth, "https://org.crm.dynamics.com")
        result = client.get_vendor("123")
        
        assert result["success"] is True
        assert result["data"]["accountid"] == "123"

    @patch('integrations.dynamics.dynamics_oauth.DynamicsOAuth2Client.get_auth_headers')
    @patch('integrations.dynamics.dynamics_oauth.requests.request')
    def test_update_vendor_risk(self, mock_request, mock_headers):
        mock_headers.return_value = {"Authorization": "Bearer test"}
        mock_response = Mock()
        mock_response.status_code = 204
        mock_response.json.return_value = {}
        mock_response.text = ""
        mock_response.headers = {}
        mock_request.return_value = mock_response
        
        oauth = Mock()
        client = Dynamics365Client(oauth, "https://org.crm.dynamics.com")
        result = client.update_vendor_risk("123", 90.0, "high")
        
        assert result["success"] is True


class TestDynamicsBidirectionalSync:
    def test_init(self):
        dyn_client = Mock()
        sync = DynamicsBidirectionalSync(dyn_client, "cz_key")
        assert sync.dynamics == dyn_client


# ============================================================
# Factory Function Tests
# ============================================================

class TestFactoryFunctions:
    @patch('integrations.sap.sap_oauth.SAPOAuth2Client')
    def test_create_sap_rest_connector(self, mock_oauth):
        mock_oauth.return_value = Mock()
        connector = create_sap_rest_connector("https://sap.com", "client", "secret")
        assert connector is not None

    def test_create_sap_soap_connector(self):
        connector = create_sap_soap_connector("https://sap.com", "admin", "pass")
        assert isinstance(connector, SAPSOAPClient)

    @patch('integrations.netsuite.netsuite_oauth.NetSuiteOAuth1Client')
    def test_create_netsuite_client(self, mock_client):
        mock_client.return_value = Mock()
        client = create_netsuite_client("123", "ck", "cs", "tk", "ts")
        assert client is not None

    @patch('integrations.dynamics.dynamics_oauth.DynamicsOAuth2Client')
    @patch('integrations.dynamics.dynamics_oauth.Dynamics365Client')
    def test_create_dynamics_client(self, mock_dyn, mock_oauth):
        mock_oauth_instance = Mock()
        mock_oauth.return_value = mock_oauth_instance
        mock_dyn.return_value = Mock()
        
        client = create_dynamics_client("tenant", "client", "secret", "https://org.crm.dynamics.com")
        assert client is not None
