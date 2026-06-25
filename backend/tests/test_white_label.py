"""
Tests para el servicio y router de White-label
"""

import pytest
from fastapi.testclient import TestClient

from app.services.white_label import (
    WhiteLabelService, 
    BrandingConfig, 
    ThemeColor, 
    MARKET_CONFIGS
)
from app.main import app


client = TestClient(app)


class TestWhiteLabelService:
    """Tests unitarios para WhiteLabelService"""
    
    def setup_method(self):
        """Limpiar tenants antes de cada test"""
        WhiteLabelService._tenants.clear()
    
    def teardown_method(self):
        """Limpiar tenants después de cada test"""
        WhiteLabelService._tenants.clear()
    
    def test_default_config(self):
        """La configuración por defecto debe tener valores válidos"""
        config = WhiteLabelService.DEFAULT_CONFIG
        assert config.app_name == "Conflict Zero"
        assert config.default_language == "es"
        assert "founder_program" in config.features
        assert config.features["white_label"] is False
    
    def test_get_tenant_config_default(self):
        """Sin tenant_id debe retornar config por defecto"""
        config = WhiteLabelService.get_tenant_config(None)
        assert config.app_name == "Conflict Zero"
    
    def test_get_tenant_config_nonexistent(self):
        """Tenant inexistente debe retornar config por defecto"""
        config = WhiteLabelService.get_tenant_config("no-existe")
        assert config.app_name == "Conflict Zero"
    
    def test_register_tenant(self):
        """Debe poder registrar un nuevo tenant"""
        config = BrandingConfig(app_name="Test Corp")
        WhiteLabelService.register_tenant("test-corp", config)
        
        retrieved = WhiteLabelService.get_tenant_config("test-corp")
        assert retrieved.app_name == "Test Corp"
    
    def test_register_tenant_prevent_nested(self):
        """No debe permitir white-label anidado"""
        config = BrandingConfig()
        config.features["white_label"] = True
        
        with pytest.raises(ValueError, match="White-label anidado no permitido"):
            WhiteLabelService.register_tenant("nested", config)
    
    def test_generate_css_variables(self):
        """Debe generar CSS variables válidas"""
        config = BrandingConfig(
            theme=ThemeColor(primary="#ff0000", background="#000000")
        )
        css = WhiteLabelService.generate_css_variables(config)
        
        assert "--cz-primary: #ff0000" in css
        assert "--cz-background: #000000" in css
        assert "--cz-font-family: Inter" in css
    
    def test_generate_manifest_json(self):
        """Debe generar manifest.json válido"""
        config = BrandingConfig(
            app_name="Test App",
            app_short_name="TA",
            favicon_url="/custom-icon.png"
        )
        manifest = WhiteLabelService.generate_manifest_json(config)
        
        assert manifest["name"] == "Test App"
        assert manifest["short_name"] == "TA"
        assert manifest["theme_color"] == "#2563eb"
        assert any(icon["src"] == "/custom-icon.png" for icon in manifest["icons"])
    
    def test_generate_email_template(self):
        """Debe generar plantilla de email personalizada"""
        config = BrandingConfig(app_name="Test Corp")
        template = WhiteLabelService.generate_email_template(config, "welcome")
        
        assert "Test Corp" in template
        assert "Bienvenido a Test Corp" in template
    
    def test_generate_email_template_default(self):
        """Plantilla inexistente debe retornar welcome por defecto"""
        config = BrandingConfig()
        template = WhiteLabelService.generate_email_template(config, "no-existe")
        
        assert "Bienvenido" in template
    
    def test_market_configs_exist(self):
        """Debe tener configuraciones para mercados planificados"""
        expected_markets = ["peru", "chile", "colombia", "mexico", "spain"]
        for market in expected_markets:
            assert market in MARKET_CONFIGS
    
    def test_market_config_peru(self):
        """Config de Perú debe tener RUC"""
        config = MARKET_CONFIGS["peru"]
        assert "RUC" in config.custom_texts["verification_title"]
    
    def test_market_config_chile(self):
        """Config de Chile debe tener RUT"""
        config = MARKET_CONFIGS["chile"]
        assert "RUT" in config.custom_texts["verification_title"]
    
    def test_market_config_colombia(self):
        """Config de Colombia debe tener NIT"""
        config = MARKET_CONFIGS["colombia"]
        assert "NIT" in config.custom_texts["verification_title"]
    
    def test_market_config_mexico(self):
        """Config de México debe tener RFC"""
        config = MARKET_CONFIGS["mexico"]
        assert "RFC" in config.custom_texts["verification_title"]
    
    def test_market_config_spain(self):
        """Config de España debe tener NIF/CIF"""
        config = MARKET_CONFIGS["spain"]
        assert "NIF" in config.custom_texts["verification_title"]


class TestWhiteLabelPublicEndpoints:
    """Tests para endpoints públicos de white-label"""
    
    def setup_method(self):
        WhiteLabelService._tenants.clear()
        # Registrar tenant de prueba
        config = BrandingConfig(app_name="Test Tenant")
        WhiteLabelService.register_tenant("test-tenant", config)
    
    def teardown_method(self):
        WhiteLabelService._tenants.clear()
    
    def test_get_public_config_default(self):
        """Debe obtener config por defecto sin tenant_id"""
        response = client.get("/api/v2/white-label/config")
        assert response.status_code == 200
        data = response.json()
        assert data["app_name"] == "Conflict Zero"
        assert "theme" in data
    
    def test_get_public_config_with_tenant(self):
        """Debe obtener config de tenant específico"""
        response = client.get("/api/v2/white-label/config?tenant_id=test-tenant")
        assert response.status_code == 200
        data = response.json()
        assert data["app_name"] == "Test Tenant"
    
    def test_get_tenant_css(self):
        """Debe generar CSS para un tenant"""
        response = client.get("/api/v2/white-label/config/test-tenant/css")
        assert response.status_code == 200
        data = response.json()
        assert "css" in data
        assert "--cz-primary" in data["css"]
    
    def test_get_tenant_manifest(self):
        """Debe generar manifest.json para un tenant"""
        response = client.get("/api/v2/white-label/config/test-tenant/manifest.json")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Tenant"
        assert "icons" in data


class TestWhiteLabelAdminEndpoints:
    """Tests para endpoints administrativos de white-label"""
    
    def setup_method(self):
        WhiteLabelService._tenants.clear()
    
    def teardown_method(self):
        WhiteLabelService._tenants.clear()
    
    def test_list_tenants_unauthorized(self):
        """Listar tenants sin auth debe fallar"""
        response = client.get("/api/v2/white-label/admin/tenants")
        assert response.status_code in (401, 403)
    
    def test_create_tenant_unauthorized(self):
        """Crear tenant sin auth debe fallar"""
        response = client.post("/api/v2/white-label/admin/tenants", json={
            "tenant_id": "new-tenant",
            "config": {"app_name": "New"}
        })
        assert response.status_code in (401, 403)
    
    def test_get_market_config_unauthorized(self):
        """Obtener config de mercado sin auth debe fallar"""
        response = client.get("/api/v2/white-label/admin/markets/peru")
        assert response.status_code in (401, 403)
    
    def test_clone_market_unauthorized(self):
        """Clonar mercado sin auth debe fallar"""
        response = client.post("/api/v2/white-label/admin/markets/peru/clone/test")
        assert response.status_code in (401, 403)


class TestBrandingConfig:
    """Tests para el modelo BrandingConfig"""
    
    def test_default_values(self):
        """Valores por defecto deben ser válidos"""
        config = BrandingConfig()
        assert config.app_name == "Conflict Zero"
        assert config.theme.primary == "#2563eb"
        assert config.default_language == "es"
    
    def test_custom_values(self):
        """Debe aceptar valores personalizados"""
        config = BrandingConfig(
            app_name="Custom",
            theme=ThemeColor(primary="#ff0000"),
            features={"api_access": False}
        )
        assert config.app_name == "Custom"
        assert config.theme.primary == "#ff0000"
        assert config.features["api_access"] is False
    
    def test_theme_color_defaults(self):
        """ThemeColor debe tener valores por defecto"""
        theme = ThemeColor()
        assert theme.primary == "#2563eb"
        assert theme.success == "#22c55e"
        assert theme.danger == "#ef4444"
    
    def test_model_dump(self):
        """Debe poder serializarse a dict"""
        config = BrandingConfig(app_name="Test")
        data = config.model_dump()
        assert data["app_name"] == "Test"
        assert "theme" in data
        assert "features" in data
