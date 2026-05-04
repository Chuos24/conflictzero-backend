"""
Conflict Zero - SAP ERP OAuth/SOAP Integration
Conector real con autenticación OAuth 2.0 y SOAP API para SAP S/4HANA
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
import requests
import xml.etree.ElementTree as ET
from urllib.parse import urljoin
import hashlib
import hmac
import base64


class SAPOAuth2Client:
    """
    Cliente OAuth 2.0 para SAP S/4HANA.
    Soporta Authorization Code flow y Client Credentials.
    """
    
    def __init__(
        self,
        base_url: str,
        client_id: str,
        client_secret: str,
        auth_url: Optional[str] = None,
        token_url: Optional[str] = None
    ):
        self.base_url = base_url.rstrip("/")
        self.client_id = client_id
        self.client_secret = client_secret
        self.auth_url = auth_url or f"{self.base_url}/sap/bc/sec/oauth2/token"
        self.token_url = token_url or f"{self.base_url}/sap/bc/sec/oauth2/token"
        self._access_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None
    
    def _is_token_valid(self) -> bool:
        """Verifica si el token actual es válido"""
        if not self._access_token or not self._token_expires_at:
            return False
        return datetime.utcnow() < self._token_expires_at - timedelta(minutes=5)
    
    def authenticate_client_credentials(self) -> bool:
        """
        Autenticación OAuth 2.0 Client Credentials.
        Usado para integraciones server-to-server.
        """
        try:
            response = requests.post(
                self.token_url,
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "scope": "ZEPM_VENDOR_READ ZEPM_VENDOR_WRITE"
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=30,
                verify=True
            )
            response.raise_for_status()
            
            token_data = response.json()
            self._access_token = token_data["access_token"]
            expires_in = token_data.get("expires_in", 3600)
            self._token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
            
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"SAP OAuth error: {e}")
            return False
    
    def get_auth_headers(self) -> Dict[str, str]:
        """Retorna headers de autenticación para requests SAP"""
        if not self._is_token_valid():
            self.authenticate_client_credentials()
        
        return {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json",
            "x-csrf-token": self._get_csrf_token() if self._access_token else ""
        }
    
    def _get_csrf_token(self) -> str:
        """Obtiene CSRF token para requests de escritura"""
        try:
            response = requests.get(
                f"{self.base_url}/sap/bc/sec/csrf",
                headers={"Authorization": f"Bearer {self._access_token}"},
                timeout=10
            )
            return response.headers.get("x-csrf-token", "")
        except:
            return ""


class SAPSOAPClient:
    """
    Cliente SOAP para SAP S/4HANA.
    Para operaciones complejas de proveedores que requieren BAPI/RFC.
    """
    
    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.soap_headers = {
            "Content-Type": "text/xml; charset=utf-8",
            "Authorization": self._get_basic_auth()
        }
    
    def _get_basic_auth(self) -> str:
        """Genera header de autenticación básica"""
        credentials = base64.b64encode(
            f"{self.username}:{self.password}".encode()
        ).decode()
        return f"Basic {credentials}"
    
    def _build_soap_envelope(self, body: str) -> str:
        """Construye envelope SOAP"""
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope/"
               xmlns:urn="urn:sap-com:document:sap:soap:functions:mc-style">
    <soap:Header/>
    <soap:Body>
        {body}
    </soap:Body>
</soap:Envelope>"""
    
    def get_vendor_details(self, vendor_code: str) -> Dict:
        """
        Obtiene detalles de proveedor via BAPI_VENDOR_GETDETAIL
        """
        soap_body = f"""
        <urn:BAPI_VENDOR_GETDETAIL>
            <VENDORNO>{vendor_code}</VENDORNO>
        </urn:BAPI_VENDOR_GETDETAIL>
        """
        
        try:
            response = requests.post(
                f"{self.base_url}/sap/bc/srt/rfc/sap/bapi_vendor_getdetail/100/bapi_vendor_getdetail/binding",
                headers=self.soap_headers,
                data=self._build_soap_envelope(soap_body),
                timeout=30
            )
            response.raise_for_status()
            
            # Parsear respuesta XML
            root = ET.fromstring(response.content)
            
            # Extraer datos del proveedor
            vendor_data = {}
            for elem in root.iter():
                if elem.tag.endswith("NAME"):
                    vendor_data["name"] = elem.text
                elif elem.tag.endswith("CITY"):
                    vendor_data["city"] = elem.text
                elif elem.tag.endswith("COUNTRY"):
                    vendor_data["country"] = elem.text
            
            return {
                "success": True,
                "vendor_code": vendor_code,
                "data": vendor_data
            }
            
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "vendor_code": vendor_code,
                "error": str(e)
            }
    
    def update_vendor_risk_fields(
        self,
        vendor_code: str,
        risk_score: float,
        risk_level: str
    ) -> Dict:
        """
        Actualiza campos custom de riesgo en SAP via BAPI_VENDOR_CHANGE
        """
        soap_body = f"""
        <urn:BAPI_VENDOR_CHANGE>
            <VENDORNO>{vendor_code}</VENDORNO>
            <VENDOR_DATA>
                <RISK_SCORE>{risk_score}</RISK_SCORE>
                <RISK_LEVEL>{risk_level}</RISK_LEVEL>
                <LAST_VERIFIED>{datetime.utcnow().isoformat()}</LAST_VERIFIED>
            </VENDOR_DATA>
        </urn:BAPI_VENDOR_CHANGE>
        """
        
        try:
            response = requests.post(
                f"{self.base_url}/sap/bc/srt/rfc/sap/bapi_vendor_change/100/bapi_vendor_change/binding",
                headers={**self.soap_headers, "x-csrf-token": "fetch"},
                data=self._build_soap_envelope(soap_body),
                timeout=30
            )
            
            return {
                "success": response.status_code == 200,
                "vendor_code": vendor_code,
                "status_code": response.status_code
            }
            
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "vendor_code": vendor_code,
                "error": str(e)
            }


class SAPBidirectionalSync:
    """
    Sincronización bidireccional entre SAP y Conflict Zero.
    """
    
    def __init__(
        self,
        sap_oauth: SAPOAuth2Client,
        sap_soap: SAPSOAPClient,
        conflict_zero_api_key: str,
        conflict_zero_base_url: str = "https://api.conflictzero.com"
    ):
        self.sap_oauth = sap_oauth
        self.sap_soap = sap_soap
        self.cz_api_key = conflict_zero_api_key
        self.cz_base_url = conflict_zero_base_url
    
    def sync_vendor_to_conflict_zero(
        self,
        vendor_code: str,
        ruc: str
    ) -> Dict:
        """
        Sync: SAP → Conflict Zero
        Verifica proveedor en Conflict Zero y actualiza SAP con resultado.
        """
        # 1. Obtener datos del proveedor de SAP
        sap_data = self.sap_soap.get_vendor_details(vendor_code)
        if not sap_data["success"]:
            return {"success": False, "stage": "sap_fetch", "error": sap_data.get("error")}
        
        # 2. Verificar en Conflict Zero
        try:
            cz_response = requests.post(
                f"{self.cz_base_url}/api/v2/verify",
                headers={"Authorization": f"Bearer {self.cz_api_key}"},
                json={"ruc": ruc, "source": "sap_sync"},
                timeout=30
            )
            cz_data = cz_response.json()
            
            # 3. Actualizar SAP con datos de riesgo
            if "risk_score" in cz_data:
                update_result = self.sap_soap.update_vendor_risk_fields(
                    vendor_code=vendor_code,
                    risk_score=cz_data["risk_score"],
                    risk_level=cz_data.get("risk_level", "unknown")
                )
                
                return {
                    "success": True,
                    "direction": "sap_to_cz",
                    "vendor_code": vendor_code,
                    "risk_score": cz_data["risk_score"],
                    "sap_updated": update_result["success"]
                }
            
            return {"success": False, "stage": "cz_verify", "error": "No risk data"}
            
        except requests.exceptions.RequestException as e:
            return {"success": False, "stage": "cz_api", "error": str(e)}
    
    def sync_vendor_from_conflict_zero(
        self,
        ruc: str,
        vendor_code: str
    ) -> Dict:
        """
        Sync: Conflict Zero → SAP
        Actualiza Conflict Zero con datos maestros desde SAP.
        """
        # 1. Obtener datos maestros de SAP
        sap_data = self.sap_soap.get_vendor_details(vendor_code)
        if not sap_data["success"]:
            return {"success": False, "stage": "sap_fetch", "error": sap_data.get("error")}
        
        # 2. Enviar a Conflict Zero para enriquecimiento
        try:
            cz_response = requests.post(
                f"{self.cz_base_url}/api/v2/suppliers/enrich",
                headers={"Authorization": f"Bearer {self.cz_api_key}"},
                json={
                    "ruc": ruc,
                    "sap_data": sap_data.get("data", {}),
                    "source": "sap_master_data"
                },
                timeout=30
            )
            
            return {
                "success": cz_response.status_code == 200,
                "direction": "cz_to_sap",
                "vendor_code": vendor_code,
                "status_code": cz_response.status_code
            }
            
        except requests.exceptions.RequestException as e:
            return {"success": False, "stage": "cz_api", "error": str(e)}


# Factory functions para crear conectores

def create_sap_rest_connector(
    base_url: str,
    client_id: str,
    client_secret: str
) -> SAPOAuth2Client:
    """Crea conector REST OAuth 2.0 para SAP"""
    return SAPOAuth2Client(base_url, client_id, client_secret)


def create_sap_soap_connector(
    base_url: str,
    username: str,
    password: str
) -> SAPSOAPClient:
    """Crea conector SOAP para SAP"""
    return SAPSOAPClient(base_url, username, password)


def create_bidirectional_sync(
    sap_base_url: str,
    sap_client_id: str,
    sap_client_secret: str,
    sap_username: str,
    sap_password: str,
    cz_api_key: str
) -> SAPBidirectionalSync:
    """Crea sync bidireccional completo"""
    oauth = SAPOAuth2Client(sap_base_url, sap_client_id, sap_client_secret)
    soap = SAPSOAPClient(sap_base_url, sap_username, sap_password)
    return SAPBidirectionalSync(oauth, soap, cz_api_key)
