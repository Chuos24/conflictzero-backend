"""
Tests para el módulo de pagos (payments.py)
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi import HTTPException
from datetime import datetime

from app.routers.payments import (
    CulqiService,
    _get_plan_limit,
    PLAN_PRICES_CENTS,
    PLAN_NAMES,
)


# ============================================================
# TESTS DE SERVICIO CULQI
# ============================================================

class TestCulqiService:
    """Tests para el servicio de Culqi"""

    def test_is_configured_with_valid_key(self):
        """Culqi está configurado cuando la secret key empieza con sk_"""
        with patch('app.routers.payments.CULQI_SECRET_KEY', 'sk_test_123456'):
            assert CulqiService.is_configured() is True

    def test_is_configured_without_key(self):
        """Culqi no está configurado cuando no hay secret key"""
        with patch('app.routers.payments.CULQI_SECRET_KEY', ''):
            assert CulqiService.is_configured() is False

    def test_is_configured_with_invalid_key(self):
        """Culqi no está configurado cuando la key no empieza con sk_"""
        with patch('app.routers.payments.CULQI_SECRET_KEY', 'pk_test_123456'):
            assert CulqiService.is_configured() is False

    @pytest.mark.asyncio
    async def test_create_charge_not_configured(self):
        """Error 503 cuando Culqi no está configurado"""
        with patch('app.routers.payments.CULQI_SECRET_KEY', ''):
            with pytest.raises(HTTPException) as exc_info:
                await CulqiService.create_charge({})
            assert exc_info.value.status_code == 503

    @pytest.mark.asyncio
    async def test_create_charge_success(self):
        """Crear charge exitoso"""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "id": "chr_test_123",
            "status": "captured",
            "amount": 40000
        }

        with patch('httpx.AsyncClient') as mock_client:
            mock_ctx = MagicMock()
            mock_ctx.__aenter__ = AsyncMock(return_value=mock_ctx)
            mock_ctx.__aexit__ = AsyncMock(return_value=None)
            mock_ctx.post = AsyncMock(return_value=mock_response)
            mock_client.return_value = mock_ctx

            with patch('app.routers.payments.CULQI_SECRET_KEY', 'sk_test_123'):
                result = await CulqiService.create_charge({
                    "amount": 40000,
                    "currency_code": "PEN",
                    "email": "test@example.com"
                })
                assert result["id"] == "chr_test_123"
                assert result["status"] == "captured"

    @pytest.mark.asyncio
    async def test_create_charge_error(self):
        """Error en charge de Culqi"""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            "merchant_message": "Tarjeta declinada",
            "user_message": "Pago rechazado",
            "code": "card_declined"
        }

        with patch('httpx.AsyncClient') as mock_client:
            mock_ctx = MagicMock()
            mock_ctx.__aenter__ = AsyncMock(return_value=mock_ctx)
            mock_ctx.__aexit__ = AsyncMock(return_value=None)
            mock_ctx.post = AsyncMock(return_value=mock_response)
            mock_client.return_value = mock_ctx

            with patch('app.routers.payments.CULQI_SECRET_KEY', 'sk_test_123'):
                with pytest.raises(HTTPException) as exc_info:
                    await CulqiService.create_charge({})
                assert exc_info.value.status_code == 400


# ============================================================
# TESTS DE HELPERS
# ============================================================

class TestHelpers:
    """Tests para funciones helper"""

    def test_get_plan_limit_essential(self):
        """Plan essential tiene 1000 consultas"""
        assert _get_plan_limit("essential") == 1000

    def test_get_plan_limit_professional(self):
        """Plan professional tiene 5000 consultas"""
        assert _get_plan_limit("professional") == 5000

    def test_get_plan_limit_enterprise(self):
        """Plan enterprise tiene 100000 consultas"""
        assert _get_plan_limit("enterprise") == 100000

    def test_get_plan_limit_founder(self):
        """Plan founder tiene consultas ilimitadas"""
        assert _get_plan_limit("founder") == 999999999

    def test_get_plan_limit_default(self):
        """Plan desconocido default a 1000"""
        assert _get_plan_limit("unknown") == 1000


# ============================================================
# TESTS DE CONFIGURACIÓN
# ============================================================

class TestPaymentConfig:
    """Tests para configuración de pagos"""

    def test_plan_prices(self):
        """Los precios de los planes son correctos"""
        assert PLAN_PRICES_CENTS["essential"] == 40000      # S/ 400.00
        assert PLAN_PRICES_CENTS["professional"] == 80000   # S/ 800.00
        assert PLAN_PRICES_CENTS["enterprise"] == 250000    # S/ 2,500.00

    def test_plan_names(self):
        """Los nombres de los planes son correctos"""
        assert PLAN_NAMES["essential"] == "Essential"
        assert PLAN_NAMES["professional"] == "Professional"
        assert PLAN_NAMES["enterprise"] == "Enterprise"
