"""
Conflict Zero - SDK Python Oficial
====================================
SDK para integrar la API de Conflict Zero en aplicaciones Python.

Uso:
    from conflictzero import ConflictZeroClient

    client = ConflictZeroClient(api_key="tu_api_key")
    company = client.verify_ruc("20100012345")
"""

import requests
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum


class ConflictZeroError(Exception):
    """Error base del SDK."""
    pass


class AuthenticationError(ConflictZeroError):
    """Error de autenticación (401)."""
    pass


class RateLimitError(ConflictZeroError):
    """Error de rate limit (429)."""
    pass


class NotFoundError(ConflictZeroError):
    """Recurso no encontrado (404)."""
    pass


class ValidationError(ConflictZeroError):
    """Error de validación (422)."""
    pass


@dataclass
class APIResponse:
    """Respuesta estándar de la API."""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    status_code: int = 200


class ConflictZeroClient:
    """
    Cliente oficial de Conflict Zero para Python.

    Args:
        api_key: Tu API key de Conflict Zero
        base_url: URL base de la API (default: https://api.conflictzero.com)
        timeout: Timeout en segundos (default: 30)
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.conflictzero.com",
        timeout: int = 30
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "ConflictZero-SDK-Python/1.0.0"
        })

    def _handle_response(self, response: requests.Response) -> APIResponse:
        """Maneja la respuesta HTTP y lanza excepciones según el status code."""
        if response.status_code == 401:
            raise AuthenticationError("API key inválida o expirada")
        elif response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 60))
            raise RateLimitError(f"Rate limit excedido. Reintenta en {retry_after}s")
        elif response.status_code == 404:
            raise NotFoundError("Recurso no encontrado")
        elif response.status_code == 422:
            raise ValidationError(f"Error de validación: {response.text}")
        elif response.status_code >= 500:
            raise ConflictZeroError(f"Error del servidor: {response.status_code}")

        response.raise_for_status()
        return APIResponse(
            success=True,
            data=response.json() if response.text else None,
            status_code=response.status_code
        )

    def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> APIResponse:
        """Realiza una petición HTTP."""
        url = f"{self.base_url}{endpoint}"
        response = self.session.request(
            method=method,
            url=url,
            timeout=self.timeout,
            **kwargs
        )
        return self._handle_response(response)

    # ============================================================
    # VERIFICACIÓN
    # ============================================================

    def verify_ruc(self, ruc: str) -> APIResponse:
        """
        Verifica un RUC peruano.

        Args:
            ruc: RUC de 11 dígitos

        Returns:
            APIResponse con datos de la empresa
        """
        return self._request("GET", f"/api/v2/verify/{ruc}")

    def verify_bulk(self, rucs: List[str]) -> APIResponse:
        """
        Verifica múltiples RUCs en una sola petición.

        Args:
            rucs: Lista de RUCs de 11 dígitos

        Returns:
            APIResponse con resultados de verificación
        """
        return self._request("POST", "/api/v2/verify/bulk", json={"rucs": rucs})

    def get_company_details(self, ruc: str) -> APIResponse:
        """Obtiene detalles completos de una empresa."""
        return self._request("GET", f"/api/v2/company/{ruc}")

    # ============================================================
    # COMPARACIÓN
    # ============================================================

    def compare_companies(self, rucs: List[str]) -> APIResponse:
        """
        Compara hasta 10 empresas.

        Args:
            rucs: Lista de RUCs (máx 10)

        Returns:
            APIResponse con análisis comparativo
        """
        return self._request("POST", "/api/v2/compare", json={"rucs": rucs})

    # ============================================================
    # SCORING
    # ============================================================

    def get_risk_score(self, ruc: str) -> APIResponse:
        """Obtiene el score de riesgo de un proveedor."""
        return self._request("GET", f"/api/v2/score/{ruc}")

    def get_compliance_certificate(self, ruc: str) -> APIResponse:
        """Obtiene el certificado de compliance."""
        return self._request("GET", f"/api/v2/certificate/{ruc}")

    # ============================================================
    # RED DE PROVEEDORES
    # ============================================================

    def get_network(self) -> APIResponse:
        """Obtiene la red de proveedores del usuario."""
        return self._request("GET", "/api/v2/network")

    def add_to_network(self, ruc: str, name: str, tags: Optional[List[str]] = None) -> APIResponse:
        """Agrega un proveedor a la red."""
        payload = {"ruc": ruc, "name": name}
        if tags:
            payload["tags"] = tags
        return self._request("POST", "/api/v2/network", json=payload)

    def remove_from_network(self, company_id: int) -> APIResponse:
        """Elimina un proveedor de la red."""
        return self._request("DELETE", f"/api/v2/network/{company_id}")

    # ============================================================
    # MONITOREO
    # ============================================================

    def get_monitoring_alerts(self, status: Optional[str] = None) -> APIResponse:
        """Obtiene alertas de monitoreo."""
        params = {}
        if status:
            params["status"] = status
        return self._request("GET", "/api/v2/monitoring/alerts", params=params)

    def get_monitoring_changes(self, severity: Optional[str] = None) -> APIResponse:
        """Obtiene cambios detectados."""
        params = {}
        if severity:
            params["severity"] = severity
        return self._request("GET", "/api/v2/monitoring/changes", params=params)

    def create_snapshot(self, company_id: int) -> APIResponse:
        """Crea un snapshot manual de un proveedor."""
        return self._request("POST", f"/api/v2/monitoring/snapshots/{company_id}")

    def run_monitoring(self) -> APIResponse:
        """Ejecuta monitoreo manual."""
        return self._request("POST", "/api/v2/monitoring/run")

    def get_monitoring_stats(self) -> APIResponse:
        """Obtiene estadísticas de monitoreo."""
        return self._request("GET", "/api/v2/monitoring/stats")

    # ============================================================
    # WEBHOOKS
    # ============================================================

    def register_webhook(self, url: str, events: List[str], secret: Optional[str] = None) -> APIResponse:
        """
        Registra un webhook para recibir eventos.

        Args:
            url: URL del webhook
            events: Lista de eventos (e.g., ["supplier.change", "alert.new"])
            secret: Secreto para firmar payloads
        """
        payload = {"url": url, "events": events}
        if secret:
            payload["secret"] = secret
        return self._request("POST", "/api/v2/webhooks", json=payload)

    def list_webhooks(self) -> APIResponse:
        """Lista webhooks registrados."""
        return self._request("GET", "/api/v2/webhooks")

    def delete_webhook(self, webhook_id: int) -> APIResponse:
        """Elimina un webhook."""
        return self._request("DELETE", f"/api/v2/webhooks/{webhook_id}")

    # ============================================================
    # ADMIN
    # ============================================================

    def get_dashboard_stats(self) -> APIResponse:
        """Obtiene estadísticas del dashboard (solo admin)."""
        return self._request("GET", "/api/v2/admin/dashboard")

    def get_recent_users(self, limit: int = 50) -> APIResponse:
        """Obtiene usuarios recientes (solo admin)."""
        return self._request("GET", "/api/v2/admin/users", params={"limit": limit})

    # ============================================================
    # UTILIDADES
    # ============================================================

    def health_check(self) -> APIResponse:
        """Verifica el estado de la API."""
        return self._request("GET", "/api/v2/health")

    def get_rate_limit_status(self) -> APIResponse:
        """Obtiene el estado del rate limit."""
        response = self._request("GET", "/api/v2/rate-limit")
        headers = getattr(response, 'headers', {})
        return APIResponse(
            success=True,
            data={
                "limit": headers.get("X-RateLimit-Limit"),
                "remaining": headers.get("X-RateLimit-Remaining"),
                "reset": headers.get("X-RateLimit-Reset")
            }
        )

    def close(self):
        """Cierra la sesión HTTP."""
        self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False
