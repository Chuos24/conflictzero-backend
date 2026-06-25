"""
White-label Configuration Service
Servicio para personalización de marca en despliegues white-label.
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, HttpUrl
from enum import Enum
import json


class ThemeColor(BaseModel):
    """Configuración de colores del tema"""
    primary: str = "#2563eb"        # Color principal (botones, links)
    secondary: str = "#64748b"      # Color secundario
    success: str = "#22c55e"        # Éxito/verde
    warning: str = "#f59e0b"        # Advertencia/amarillo
    danger: str = "#ef4444"         # Peligro/rojo
    background: str = "#ffffff"     # Fondo
    surface: str = "#f8fafc"        # Superficie/cards
    text: str = "#0f172a"           # Texto principal
    textMuted: str = "#64748b"      # Texto secundario
    border: str = "#e2e8f0"         # Bordes


class BrandingConfig(BaseModel):
    """Configuración de marca white-label"""
    
    # Identidad
    app_name: str = "Conflict Zero"
    app_short_name: str = "CZ"
    company_name: str = "Conflict Zero S.A.C."
    
    # URLs
    support_url: Optional[str] = "https://conflictzero.com/support"
    privacy_url: Optional[str] = "https://conflictzero.com/privacy"
    terms_url: Optional[str] = "https://conflictzero.com/terms"
    
    # Contacto
    support_email: str = "soporte@conflictzero.com"
    support_phone: Optional[str] = None
    
    # Logo
    logo_url: Optional[str] = None
    logo_dark_url: Optional[str] = None  # Logo para modo oscuro
    favicon_url: Optional[str] = None
    
    # Colores
    theme: ThemeColor = ThemeColor()
    
    # Tipografía
    font_family: str = "Inter, system-ui, sans-serif"
    font_heading: Optional[str] = None
    
    # Features habilitadas
    features: Dict[str, bool] = {
        "founder_program": True,
        "api_access": True,
        "webhooks": True,
        "ml_scoring": True,
        "compliance_tracking": True,
        "white_label": False,  # Meta: no permitir white-label anidado
    }
    
    # Textos personalizados
    custom_texts: Dict[str, str] = {
        "login_title": "Bienvenido",
        "login_subtitle": "Ingresa tus credenciales para continuar",
        "dashboard_welcome": "Panel de Control",
        "verification_title": "Verificar RUC",
        "network_title": "Mi Red de Proveedores",
    }
    
    # SEO
    meta_title: str = "Conflict Zero - Verificación de Proveedores"
    meta_description: str = "Sistema de verificación de riesgo de proveedores"
    
    # Idioma por defecto
    default_language: str = "es"
    supported_languages: list = ["es", "en"]


class WhiteLabelService:
    """Servicio de gestión de configuraciones white-label"""
    
    # Configuración por defecto de Conflict Zero
    DEFAULT_CONFIG = BrandingConfig()
    
    # Registro de tenants white-label
    _tenants: Dict[str, BrandingConfig] = {}
    
    @classmethod
    def register_tenant(cls, tenant_id: str, config: BrandingConfig):
        """Registra un nuevo tenant white-label"""
        # Validar que no intente white-label anidado
        if config.features.get("white_label", False):
            raise ValueError("White-label anidado no permitido")
        
        cls._tenants[tenant_id] = config
    
    @classmethod
    def get_tenant_config(cls, tenant_id: Optional[str] = None) -> BrandingConfig:
        """Obtiene configuración de un tenant"""
        if tenant_id is None or tenant_id not in cls._tenants:
            return cls.DEFAULT_CONFIG
        return cls._tenants[tenant_id]
    
    @classmethod
    def generate_css_variables(cls, config: BrandingConfig) -> str:
        """Genera variables CSS para el tema"""
        theme = config.theme
        return f"""
        :root {{
            --cz-primary: {theme.primary};
            --cz-secondary: {theme.secondary};
            --cz-success: {theme.success};
            --cz-warning: {theme.warning};
            --cz-danger: {theme.danger};
            --cz-background: {theme.background};
            --cz-surface: {theme.surface};
            --cz-text: {theme.text};
            --cz-text-muted: {theme.textMuted};
            --cz-border: {theme.border};
            --cz-font-family: {config.font_family};
        }}
        """
    
    @classmethod
    def generate_manifest_json(cls, config: BrandingConfig) -> Dict[str, Any]:
        """Genera manifest.json para PWA personalizado"""
        return {
            "name": config.app_name,
            "short_name": config.app_short_name,
            "description": config.meta_description,
            "theme_color": config.theme.primary,
            "background_color": config.theme.background,
            "display": "standalone",
            "start_url": "/",
            "icons": [
                {
                    "src": config.favicon_url or "/icon-192.png",
                    "sizes": "192x192",
                    "type": "image/png"
                },
                {
                    "src": config.favicon_url or "/icon-512.png",
                    "sizes": "512x512",
                    "type": "image/png"
                }
            ]
        }
    
    @classmethod
    def generate_email_template(cls, config: BrandingConfig, template_name: str) -> str:
        """Genera plantilla de email personalizada"""
        # Templates básicos
        templates = {
            "welcome": f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: {config.font_family}; color: {config.theme.text}; }}
                    .header {{ background: {config.theme.primary}; color: white; padding: 20px; }}
                    .content {{ padding: 20px; }}
                    .footer {{ color: {config.theme.textMuted}; font-size: 12px; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>{config.app_name}</h1>
                </div>
                <div class="content">
                    <h2>Bienvenido a {config.app_name}</h2>
                    <p>Gracias por registrarte.</p>
                </div>
                <div class="footer">
                    <p>{config.company_name}</p>
                    <p><a href="{config.privacy_url}">Privacidad</a> | 
                       <a href="{config.terms_url}">Términos</a></p>
                </div>
            </body>
            </html>
            """,
            "verification_complete": f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: {config.font_family}; }}
                    .header {{ background: {config.theme.primary}; color: white; padding: 20px; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>{config.app_name}</h1>
                </div>
                <h2>Verificación Completada</h2>
                <p>Su solicitud de verificación ha sido procesada.</p>
            </body>
            </html>
            """
        }
        return templates.get(template_name, templates["welcome"])


# Configuraciones predefinidas para mercados
MARKET_CONFIGS = {
    "peru": BrandingConfig(
        app_name="Conflict Zero Perú",
        default_language="es",
        supported_languages=["es"],
        custom_texts={
            "verification_title": "Verificar RUC",
            "network_title": "Mi Red de Proveedores",
        }
    ),
    "chile": BrandingConfig(
        app_name="Conflict Zero Chile",
        default_language="es",
        supported_languages=["es"],
        custom_texts={
            "verification_title": "Verificar RUT",
            "network_title": "Mi Red de Proveedores",
        }
    ),
    "colombia": BrandingConfig(
        app_name="Conflict Zero Colombia",
        default_language="es",
        supported_languages=["es"],
        custom_texts={
            "verification_title": "Verificar NIT",
            "network_title": "Mi Red de Proveedores",
        }
    ),
    "mexico": BrandingConfig(
        app_name="Conflict Zero México",
        default_language="es",
        supported_languages=["es"],
        custom_texts={
            "verification_title": "Verificar RFC",
            "network_title": "Mi Red de Proveedores",
        }
    ),
    "spain": BrandingConfig(
        app_name="Conflict Zero España",
        default_language="es",
        supported_languages=["es", "en"],
        custom_texts={
            "verification_title": "Verificar NIF/CIF",
            "network_title": "Mi Red de Proveedores",
        }
    )
}
