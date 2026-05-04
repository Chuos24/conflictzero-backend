"""
Conflict Zero - Dynamics 365 OAuth 2.0 Integration
Implementación real de OAuth 2.0 para Microsoft Dynamics 365
"""

from typing import Dict, Optional, List
from datetime import datetime, timedelta
import requests
import urllib.parse


class DynamicsOAuth2Client:
    """
    Cliente OAuth 2.0 para Microsoft Dynamics 365.
    Soporta Authorization Code flow y Client Credentials.
    """
    
    def __init__(
        self,
        tenant_id: str,
        client_id: str,
        client_secret: str,
        resource: str = "https://yourorg.crm.dynamics.com",
        authority_url: Optional[str] = None
    ):
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.resource = resource
        self.authority_url = authority_url or f"https://login.microsoftonline.com/{tenant_id}"
        
        self.token_url = f"{self.authority_url}/oauth2/v2.0/token"
        self.authorize_url = f"{self.authority_url}/oauth2/v2.0/authorize"
        
        self._access_token: Optional[str] = None
        self._refresh_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None
    
    def get_authorization_url(
        self,
        redirect_uri: str,
        state: Optional[str] = None,
        scope: Optional[List[str]] = None
    ) -> str:
        """
        Genera URL de autorización para Authorization Code flow.
        """
        default_scope = scope or ["https://yourorg.crm.dynamics.com/.default"]
        scopes = " ".join(default_scope)
        
        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "redirect_uri": redirect_uri,
            "scope": scopes,
            "response_mode": "query"
        }
        
        if state:
            params["state"] = state
        
        query_string = urllib.parse.urlencode(params)
        return f"{self.authorize_url}?{query_string}"
    
    def exchange_code_for_token(
        self,
        authorization_code: str,
        redirect_uri: str
    ) -> Dict:
        """
        Intercambia código de autorización por tokens.
        """
        data = {
            "grant_type": "authorization_code",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": authorization_code,
            "redirect_uri": redirect_uri
        }
        
        return self._request_token(data)
    
    def authenticate_client_credentials(self) -> bool:
        """
        Autenticación Client Credentials (server-to-server).
        """
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": f"{self.resource}/.default"
        }
        
        result = self._request_token(data)
        return result.get("success", False)
    
    def refresh_access_token(self) -> bool:
        """
        Refresca el access token usando refresh token.
        """
        if not self._refresh_token:
            return False
        
        data = {
            "grant_type": "refresh_token",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": self._refresh_token,
            "scope": f"{self.resource}/.default"
        }
        
        result = self._request_token(data)
        return result.get("success", False)
    
    def _request_token(self, data: Dict) -> Dict:
        """Realiza petición de token a Microsoft Identity Platform"""
        try:
            response = requests.post(
                self.token_url,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=30
            )
            response.raise_for_status()
            
            token_data = response.json()
            
            self._access_token = token_data["access_token"]
            if "refresh_token" in token_data:
                self._refresh_token = token_data["refresh_token"]
            
            expires_in = token_data.get("expires_in", 3600)
            self._token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
            
            return {
                "success": True,
                "token_type": token_data.get("token_type", "Bearer"),
                "expires_in": expires_in,
                "scope": token_data.get("scope", "")
            }
            
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": str(e),
                "status_code": getattr(e.response, "status_code", None) if hasattr(e, "response") else None
            }
    
    def _is_token_valid(self) -> bool:
        """Verifica si el token actual es válido"""
        if not self._access_token or not self._token_expires_at:
            return False
        return datetime.utcnow() < self._token_expires_at - timedelta(minutes=5)
    
    def get_auth_headers(self) -> Dict[str, str]:
        """Retorna headers de autenticación"""
        if not self._is_token_valid():
            if self._refresh_token:
                self.refresh_access_token()
            else:
                self.authenticate_client_credentials()
        
        return {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json",
            "OData-MaxVersion": "4.0",
            "OData-Version": "4.0",
            "Accept": "application/json"
        }


class Dynamics365Client:
    """
    Cliente para Dynamics 365 Web API.
    Operaciones CRUD sobre entidades de proveedores.
    """
    
    def __init__(self, oauth: DynamicsOAuth2Client, base_url: str):
        self.oauth = oauth
        self.base_url = base_url.rstrip("/")
        self.api_url = f"{self.base_url}/api/data/v9.2"
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Dict:
        """Realiza petición autenticada a Dynamics 365"""
        url = f"{self.api_url}/{endpoint}"
        headers = self.oauth.get_auth_headers()
        
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
                "data": response.json() if response.text else None,
                "headers": dict(response.headers)
            }
            
        except requests.exceptions.HTTPError as e:
            return {
                "success": False,
                "status_code": response.status_code,
                "error": response.text if hasattr(response, "text") else str(e)
            }
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_vendor(self, vendor_id: str) -> Dict:
        """Obtiene proveedor por ID"""
        return self._make_request("GET", f"accounts({vendor_id})")
    
    def search_vendors_by_ruc(self, ruc: str) -> Dict:
        """Busca proveedor por RUC (campo custom)"""
        filter_query = f"cz_ruc eq '{ruc}'"
        return self._make_request("GET", "accounts", params={
            "$filter": filter_query,
            "$select": "accountid,name,cz_risk_score,cz_risk_level,cz_status"
        })
    
    def update_vendor_risk(
        self,
        vendor_id: str,
        risk_score: float,
        risk_level: str
    ) -> Dict:
        """Actualiza campos de riesgo del proveedor"""
        return self._make_request("PATCH", f"accounts({vendor_id})", data={
            "cz_risk_score": risk_score,
            "cz_risk_level": risk_level,
            "cz_last_verified": datetime.utcnow().isoformat()
        })
    
    def create_vendor(self, vendor_data: Dict) -> Dict:
        """Crea nuevo proveedor"""
        return self._make_request("POST", "accounts", data=vendor_data)
    
    def list_vendors(self, top: int = 50) -> Dict:
        """Lista proveedores"""
        return self._make_request("GET", "accounts", params={
            "$top": str(top),
            "$select": "accountid,name,cz_risk_score,cz_risk_level,cz_status"
        })


class DynamicsBidirectionalSync:
    """
    Sincronización bidireccional Dynamics 365 ↔ Conflict Zero
    """
    
    def __init__(
        self,
        dynamics: Dynamics365Client,
        conflict_zero_api_key: str,
        conflict_zero_base_url: str = "https://api.conflictzero.com"
    ):
        self.dynamics = dynamics
        self.cz_api_key = conflict_zero_api_key
        self.cz_base_url = conflict_zero_base_url
    
    def sync_vendor_to_cz(self, vendor_id: str, ruc: str) -> Dict:
        """Sync Dynamics → Conflict Zero"""
        # 1. Obtener vendor de Dynamics
        dyn_data = self.dynamics.get_vendor(vendor_id)
        if not dyn_data["success"]:
            return {"success": False, "stage": "dynamics_fetch", "error": dyn_data.get("error")}
        
        # 2. Verificar en Conflict Zero
        try:
            cz_response = requests.post(
                f"{self.cz_base_url}/api/v2/verify",
                headers={"Authorization": f"Bearer {self.cz_api_key}"},
                json={"ruc": ruc, "source": "dynamics_sync"},
                timeout=30
            )
            cz_data = cz_response.json()
            
            # 3. Actualizar Dynamics con riesgo
            if "risk_score" in cz_data:
                update = self.dynamics.update_vendor_risk(
                    vendor_id,
                    cz_data["risk_score"],
                    cz_data.get("risk_level", "unknown")
                )
                
                return {
                    "success": True,
                    "direction": "dyn_to_cz",
                    "vendor_id": vendor_id,
                    "risk_score": cz_data["risk_score"],
                    "dynamics_updated": update["success"]
                }
            
            return {"success": False, "stage": "cz_verify", "error": "No risk data"}
            
        except requests.exceptions.RequestException as e:
            return {"success": False, "stage": "cz_api", "error": str(e)}
    
    def sync_vendor_from_cz(self, vendor_id: str, ruc: str) -> Dict:
        """Sync Conflict Zero → Dynamics"""
        try:
            cz_response = requests.post(
                f"{self.cz_base_url}/api/v2/verify",
                headers={"Authorization": f"Bearer {self.cz_api_key}"},
                json={"ruc": ruc},
                timeout=30
            )
            cz_data = cz_response.json()
            
            if "risk_score" in cz_data:
                update = self.dynamics.update_vendor_risk(
                    vendor_id,
                    cz_data["risk_score"],
                    cz_data.get("risk_level", "unknown")
                )
                return {
                    "success": update["success"],
                    "direction": "cz_to_dyn",
                    "vendor_id": vendor_id,
                    "risk_score": cz_data["risk_score"]
                }
            
            return {"success": False, "error": "No risk score from CZ"}
            
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": str(e)}


def create_dynamics_client(
    tenant_id: str,
    client_id: str,
    client_secret: str,
    resource_url: str
) -> Dynamics365Client:
    """Factory para crear cliente Dynamics 365"""
    oauth = DynamicsOAuth2Client(tenant_id, client_id, client_secret, resource_url)
    oauth.authenticate_client_credentials()
    return Dynamics365Client(oauth, resource_url)
