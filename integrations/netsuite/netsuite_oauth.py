"""
Conflict Zero - NetSuite OAuth 1.0a Integration
Implementación real de OAuth 1.0a para SuiteTalk REST API
"""

from typing import Dict, Optional
from datetime import datetime
import requests
import urllib.parse
import hmac
import hashlib
import base64
import secrets
import time


class NetSuiteOAuth1Client:
    """
    Cliente OAuth 1.0a para NetSuite SuiteTalk REST API.
    Implementa TBA (Token-Based Authentication).
    """
    
    def __init__(
        self,
        account_id: str,
        consumer_key: str,
        consumer_secret: str,
        token_id: str,
        token_secret: str,
        sandbox: bool = False
    ):
        self.account_id = account_id
        self.realm = account_id.replace("_", "-").upper()
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.token_id = token_id
        self.token_secret = token_secret
        
        # Base URL
        env = "sandbox" if sandbox else ""
        self.base_url = f"https://{account_id}.suitetalk.api.netsuite.com/services/rest/record/v1"
    
    def _generate_nonce(self) -> str:
        """Genera nonce aleatorio para OAuth 1.0a"""
        return secrets.token_hex(16)
    
    def _generate_timestamp(self) -> str:
        """Genera timestamp para OAuth 1.0a"""
        return str(int(time.time()))
    
    def _create_signature_base(
        self,
        method: str,
        url: str,
        params: Dict[str, str]
    ) -> str:
        """
        Crea la base para la firma OAuth 1.0a.
        Siguiendo RFC 5849 Section 3.4.1.
        """
        # 1. Obtener method y URL
        base_url = url.split("?")[0]
        
        # 2. Crear parameter string
        sorted_params = sorted(params.items())
        param_parts = []
        for key, value in sorted_params:
            encoded_key = urllib.parse.quote(key, safe="")
            encoded_value = urllib.parse.quote(str(value), safe="")
            param_parts.append(f"{encoded_key}={encoded_value}")
        param_string = "&".join(param_parts)
        
        # 3. Crear signature base string
        encoded_base_url = urllib.parse.quote(base_url, safe="")
        encoded_param_string = urllib.parse.quote(param_string, safe="")
        
        return f"{method.upper()}&{encoded_base_url}&{encoded_param_string}"
    
    def _sign_request(
        self,
        signature_base: str
    ) -> str:
        """
        Firma la petición con HMAC-SHA256.
        Usa consumer_secret&token_secret como signing key.
        """
        signing_key = f"{urllib.parse.quote(self.consumer_secret, safe='')}&{urllib.parse.quote(self.token_secret, safe='')}"
        
        signature = hmac.new(
            signing_key.encode("utf-8"),
            signature_base.encode("utf-8"),
            hashlib.sha256
        ).digest()
        
        return base64.b64encode(signature).decode()
    
    def get_auth_header(
        self,
        method: str,
        url: str,
        extra_params: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Genera el header Authorization completo para OAuth 1.0a.
        """
        nonce = self._generate_nonce()
        timestamp = self._generate_timestamp()
        
        # Parámetros OAuth
        oauth_params = {
            "oauth_consumer_key": self.consumer_key,
            "oauth_token": self.token_id,
            "oauth_signature_method": "HMAC-SHA256",
            "oauth_timestamp": timestamp,
            "oauth_nonce": nonce,
            "oauth_version": "1.0",
            "realm": self.realm
        }
        
        # Agregar parámetros extra (query params del request)
        if extra_params:
            oauth_params.update(extra_params)
        
        # Crear signature
        signature_base = self._create_signature_base(method, url, oauth_params)
        signature = self._sign_request(signature_base)
        oauth_params["oauth_signature"] = signature
        
        # Construir header
        auth_parts = []
        for key, value in sorted(oauth_params.items()):
            if key == "realm":
                auth_parts.insert(0, f'Realm="{value}"')
            else:
                auth_parts.append(f'{key}="{urllib.parse.quote(str(value), safe="")}"')
        
        return "OAuth " + ", ".join(auth_parts)
    
    def make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict[str, str]] = None
    ) -> Dict:
        """
        Realiza petición autenticada a NetSuite.
        """
        url = f"{self.base_url}/{endpoint}"
        
        # Query params para la firma
        query_params = params or {}
        
        auth_header = self.get_auth_header(method, url, query_params)
        
        headers = {
            "Authorization": auth_header,
            "Content-Type": "application/json",
            "Prefer": "transient"
        }
        
        try:
            response = requests.request(
                method=method.upper(),
                url=url,
                headers=headers,
                json=data,
                params=params,
                timeout=30
            )
            response.raise_for_status()
            
            return {
                "success": True,
                "status_code": response.status_code,
                "data": response.json() if response.text else None
            }
            
        except requests.exceptions.HTTPError as e:
            error_data = {}
            try:
                error_data = response.json()
            except:
                error_data = {"detail": response.text}
            
            return {
                "success": False,
                "status_code": response.status_code,
                "error": error_data,
                "message": str(e)
            }
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_vendor(self, vendor_id: str) -> Dict:
        """Obtiene un proveedor por ID"""
        return self.make_request("GET", f"vendor/{vendor_id}")
    
    def update_vendor_risk(self, vendor_id: str, risk_score: float, risk_level: str) -> Dict:
        """Actualiza campos custom de riesgo en el proveedor"""
        return self.make_request("PATCH", f"vendor/{vendor_id}", data={
            "custentity_cz_risk_score": risk_score,
            "custentity_cz_risk_level": risk_level,
            "custentity_cz_last_verified": datetime.utcnow().isoformat()
        })
    
    def search_vendors(self, ruc: Optional[str] = None, limit: int = 100) -> Dict:
        """Busca proveedores con filtros opcionales"""
        params = {"limit": str(limit)}
        if ruc:
            params["q"] = f"custentity_cz_ruc:{ruc}"
        return self.make_request("GET", "vendor", params=params)


class NetSuiteBidirectionalSync:
    """
    Sincronización bidireccional NetSuite ↔ Conflict Zero
    """
    
    def __init__(
        self,
        netsuite: NetSuiteOAuth1Client,
        conflict_zero_api_key: str,
        conflict_zero_base_url: str = "https://api.conflictzero.com"
    ):
        self.netsuite = netsuite
        self.cz_api_key = conflict_zero_api_key
        self.cz_base_url = conflict_zero_base_url
    
    def sync_vendor_to_cz(self, vendor_id: str, ruc: str) -> Dict:
        """Sync NetSuite → Conflict Zero"""
        # 1. Obtener vendor de NetSuite
        ns_data = self.netsuite.get_vendor(vendor_id)
        if not ns_data["success"]:
            return {"success": False, "stage": "netsuite_fetch", "error": ns_data.get("error")}
        
        # 2. Verificar en Conflict Zero
        try:
            cz_response = requests.post(
                f"{self.cz_base_url}/api/v2/verify",
                headers={"Authorization": f"Bearer {self.cz_api_key}"},
                json={"ruc": ruc, "source": "netsuite_sync"},
                timeout=30
            )
            cz_data = cz_response.json()
            
            # 3. Actualizar NetSuite con riesgo
            if "risk_score" in cz_data:
                update = self.netsuite.update_vendor_risk(
                    vendor_id,
                    cz_data["risk_score"],
                    cz_data.get("risk_level", "unknown")
                )
                
                return {
                    "success": True,
                    "direction": "ns_to_cz",
                    "vendor_id": vendor_id,
                    "risk_score": cz_data["risk_score"],
                    "netsuite_updated": update["success"]
                }
            
            return {"success": False, "stage": "cz_verify", "error": "No risk data"}
            
        except requests.exceptions.RequestException as e:
            return {"success": False, "stage": "cz_api", "error": str(e)}
    
    def sync_vendor_from_cz(self, vendor_id: str, ruc: str) -> Dict:
        """Sync Conflict Zero → NetSuite (enriquecimiento)"""
        # 1. Verificar en CZ
        try:
            cz_response = requests.post(
                f"{self.cz_base_url}/api/v2/verify",
                headers={"Authorization": f"Bearer {self.cz_api_key}"},
                json={"ruc": ruc},
                timeout=30
            )
            cz_data = cz_response.json()
            
            # 2. Actualizar NetSuite
            if "risk_score" in cz_data:
                update = self.netsuite.update_vendor_risk(
                    vendor_id,
                    cz_data["risk_score"],
                    cz_data.get("risk_level", "unknown")
                )
                return {
                    "success": update["success"],
                    "direction": "cz_to_ns",
                    "vendor_id": vendor_id,
                    "risk_score": cz_data["risk_score"]
                }
            
            return {"success": False, "error": "No risk score from CZ"}
            
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": str(e)}


def create_netsuite_client(
    account_id: str,
    consumer_key: str,
    consumer_secret: str,
    token_id: str,
    token_secret: str,
    sandbox: bool = False
) -> NetSuiteOAuth1Client:
    """Factory para crear cliente NetSuite OAuth 1.0a"""
    return NetSuiteOAuth1Client(
        account_id, consumer_key, consumer_secret,
        token_id, token_secret, sandbox
    )
