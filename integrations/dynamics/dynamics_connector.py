"""
Conflict Zero - Microsoft Dynamics 365 Integration
Power Automate + Custom Connector
"""

from typing import Dict, List, Optional
from datetime import datetime
import requests


class DynamicsConnector:
    """
    Conector para Microsoft Dynamics 365 Finance & Operations.
    Utiliza Power Automate o APIs directas.
    """
    
    def __init__(
        self,
        tenant_id: str,
        client_id: str,
        client_secret: str,
        environment_url: str
    ):
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.environment_url = environment_url.rstrip("/")
        self.access_token = None
    
    def _get_access_token(self) -> str:
        """Obtiene token OAuth2 de Microsoft."""
        url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
        
        payload = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": f"{self.environment_url}/.default"
        }
        
        response = requests.post(url, data=payload, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        self.access_token = data["access_token"]
        return self.access_token
    
    def verify_vendor(
        self,
        vendor_account: str,
        ruc: str
    ) -> Dict:
        """
        Verifica un proveedor en Dynamics contra Conflict Zero.
        """
        try:
            token = self._get_access_token()
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            # Llamar API Conflict Zero
            response = requests.post(
                "https://api.conflictzero.com/api/v2/verify",
                headers={"Authorization": f"Bearer {token}"},
                json={"ruc": ruc},
                timeout=30
            )
            response.raise_for_status()
            
            cz_data = response.json()
            
            # Actualizar vendor en Dynamics
            update_response = requests.patch(
                f"{self.environment_url}/api/data/v9.2/vendors({vendor_account})",
                headers=headers,
                json={
                    "cz_riskscore": cz_data.get("risk_score", 0),
                    "cz_status": cz_data.get("status", "unknown"),
                    "cz_lastverified": datetime.utcnow().isoformat()
                },
                timeout=30
            )
            
            return {
                "success": True,
                "vendor_account": vendor_account,
                "ruc": ruc,
                "risk_score": cz_data.get("risk_score", 0),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "vendor_account": vendor_account,
                "ruc": ruc,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def get_vendor_list(
        self,
        risk_threshold: Optional[float] = None
    ) -> List[Dict]:
        """
        Obtiene lista de proveedores filtrados por riesgo.
        """
        # Placeholder - en producción query Dynamics API
        return []


# Power Automate Flow JSON (para importar)
POWER_AUTOMATE_FLOW = {
    "definition": {
        "$schema": "https://schema.management.azure.com/...",
        "contentVersion": "1.0.0.0",
        "triggers": {
            "Recurrence": {
                "type": "Recurrence",
                "recurrence": {
                    "frequency": "Day",
                    "interval": 1
                }
            }
        },
        "actions": {
            "Verify_Vendors": {
                "type": "Http",
                "inputs": {
                    "method": "POST",
                    "uri": "https://api.conflictzero.com/api/v2/verify",
                    "headers": {
                        "Authorization": "Bearer @{variables('CZ_API_KEY')}"
                    },
                    "body": {
                        "ruc": "@{items('Apply_to_each')?['ruc']}"
                    }
                }
            }
        }
    },
    "parameters": {}
}
