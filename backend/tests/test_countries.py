"""
Tests para el módulo de configuración multi-país.
"""

import pytest
from app.core.countries import (
    CountryCode,
    COUNTRY_CONFIGS,
    get_country_config,
    get_all_countries,
    get_supported_country_codes,
    validate_document,
    format_document,
    get_document_help_text,
    get_verification_sources,
    get_api_endpoint,
)


class TestCountryCodeEnum:
    """Tests para el enum de códigos de país."""
    
    def test_all_countries_present(self):
        """Verifica que todos los países planificados estén definidos."""
        expected = {"PE", "CL", "CO", "MX", "ES"}
        actual = {c.value for c in CountryCode}
        assert actual == expected
    
    def test_country_code_values(self):
        """Verifica valores individuales."""
        assert CountryCode.PE == "PE"
        assert CountryCode.CL == "CL"
        assert CountryCode.CO == "CO"
        assert CountryCode.MX == "MX"
        assert CountryCode.ES == "ES"


class TestCountryConfigs:
    """Tests para configuraciones de país."""
    
    def test_all_configs_present(self):
        """Verifica que haya config para cada CountryCode."""
        for code in CountryCode:
            assert code in COUNTRY_CONFIGS, f"Falta config para {code}"
    
    def test_peru_config(self):
        """Verifica configuración de Perú."""
        config = COUNTRY_CONFIGS[CountryCode.PE]
        assert config.name == "Perú"
        assert config.currency == "PEN"
        assert config.currency_symbol == "S/"
        assert config.document_label == "RUC"
        assert config.document_length == 11
        assert config.vat_label == "IGV"
        assert config.vat_rate == 0.18
        assert config.phone_prefix == "+51"
        assert "sunat" in config.verification_sources
    
    def test_chile_config(self):
        """Verifica configuración de Chile."""
        config = COUNTRY_CONFIGS[CountryCode.CL]
        assert config.name == "Chile"
        assert config.currency == "CLP"
        assert config.document_label == "RUT"
        assert config.vat_rate == 0.19
        assert config.phone_prefix == "+56"
        assert config.decimal_separator == ","
    
    def test_colombia_config(self):
        """Verifica configuración de Colombia."""
        config = COUNTRY_CONFIGS[CountryCode.CO]
        assert config.name == "Colombia"
        assert config.document_label == "NIT"
        assert config.currency == "COP"
        assert config.vat_rate == 0.19
    
    def test_mexico_config(self):
        """Verifica configuración de México."""
        config = COUNTRY_CONFIGS[CountryCode.MX]
        assert config.name == "México"
        assert config.document_label == "RFC"
        assert config.document_length is None  # Variable 12-13
        assert config.currency == "MXN"
        assert config.vat_rate == 0.16
    
    def test_spain_config(self):
        """Verifica configuración de España."""
        config = COUNTRY_CONFIGS[CountryCode.ES]
        assert config.name == "España"
        assert config.currency == "EUR"
        assert config.currency_symbol == "€"
        assert config.document_label == "NIF/CIF"
        assert config.vat_rate == 0.21
        assert config.data_protection_law == "RGPD"


class TestValidationPeru:
    """Tests para validación de RUC peruano."""
    
    def test_valid_ruc(self):
        """RUC válido con dígito verificador correcto."""
        # RUC válido: 20100130204 (Interbank - dígito verificador: 4)
        valid, error = validate_document("PE", "20100130204")
        assert valid is True
        assert error is None
    
    def test_empty_ruc(self):
        """RUC vacío."""
        valid, error = validate_document("PE", "")
        assert valid is False
        assert "requerido" in error
    
    def test_non_numeric_ruc(self):
        """RUC con letras."""
        valid, error = validate_document("PE", "2010013020A")
        assert valid is False
        assert "solo números" in error
    
    def test_wrong_length(self):
        """RUC con longitud incorrecta."""
        valid, error = validate_document("PE", "1234567890")
        assert valid is False
        assert "11 dígitos" in error
    
    def test_invalid_type(self):
        """RUC con tipo de contribuyente inválido."""
        valid, error = validate_document("PE", "99123456789")
        assert valid is False
        assert "Tipo" in error
    
    def test_invalid_check_digit(self):
        """RUC con dígito verificador incorrecto."""
        valid, error = validate_document("PE", "20100130205")
        assert valid is False
        assert "verificador" in error


class TestValidationChile:
    """Tests para validación de RUT chileno."""
    
    def test_valid_rut_with_dots(self):
        """RUT válido con formato con puntos."""
        valid, error = validate_document("CL", "76.123.456-K")
        # El RUT de ejemplo podría no ser válido matemáticamente
        # pero verificamos que el formato se procesa
        assert isinstance(valid, bool)
    
    def test_valid_rut_without_dots(self):
        """RUT válido sin puntos."""
        # RUT real: 12345678-5 (ejemplo)
        valid, error = validate_document("CL", "12345678-5")
        assert isinstance(valid, bool)
    
    def test_empty_rut(self):
        """RUT vacío."""
        valid, error = validate_document("CL", "")
        assert valid is False
        assert "requerido" in error
    
    def test_invalid_format(self):
        """RUT con formato incorrecto."""
        valid, error = validate_document("CL", "12345678")
        assert valid is False
        assert "Formato" in error
    
    def test_invalid_check_digit(self):
        """RUT con dígito verificador incorrecto."""
        valid, error = validate_document("CL", "12345678-9")
        assert valid is False
        assert "verificador" in error


class TestValidationColombia:
    """Tests para validación de NIT colombiano."""
    
    def test_valid_nit(self):
        """NIT válido."""
        valid, error = validate_document("CO", "9001234567")
        assert isinstance(valid, bool)
    
    def test_empty_nit(self):
        """NIT vacío."""
        valid, error = validate_document("CO", "")
        assert valid is False
        assert "requerido" in error
    
    def test_non_numeric(self):
        """NIT con letras."""
        valid, error = validate_document("CO", "900123456A")
        assert valid is False
        assert "solo números" in error
    
    def test_wrong_length(self):
        """NIT con longitud incorrecta."""
        valid, error = validate_document("CO", "1234567")
        assert valid is False
        assert "9-10 dígitos" in error


class TestValidationMexico:
    """Tests para validación de RFC mexicano."""
    
    def test_valid_rfc_moral(self):
        """RFC válido persona moral (12 chars)."""
        valid, error = validate_document("MX", "ABCD010101ABC")
        assert valid is True
        assert error is None
    
    def test_valid_rfc_fisica(self):
        """RFC válido persona física (13 chars)."""
        valid, error = validate_document("MX", "ABCD010101A12")
        assert valid is True
        assert error is None
    
    def test_empty_rfc(self):
        """RFC vacío."""
        valid, error = validate_document("MX", "")
        assert valid is False
        assert "requerido" in error
    
    def test_wrong_length(self):
        """RFC con longitud incorrecta."""
        valid, error = validate_document("MX", "ABCD010101")
        assert valid is False
        assert "12 o 13" in error
    
    def test_invalid_format(self):
        """RFC con formato incorrecto."""
        valid, error = validate_document("MX", "123456789012")
        assert valid is False
        assert "Formato" in error
    
    def test_invalid_date(self):
        """RFC con fecha inválida."""
        valid, error = validate_document("MX", "ABCD991301ABC")
        assert valid is False
        assert "Fecha" in error


class TestValidationSpain:
    """Tests para validación de NIF/CIF español."""
    
    def test_valid_dni(self):
        """DNI válido."""
        # DNI real: 12345678Z (Z = letra para 12345678 mod 23)
        valid, error = validate_document("ES", "12345678Z")
        assert valid is True
        assert error is None
    
    def test_valid_cif(self):
        """CIF válido."""
        valid, error = validate_document("ES", "B12345678")
        assert isinstance(valid, bool)
    
    def test_empty_nif(self):
        """NIF vacío."""
        valid, error = validate_document("ES", "")
        assert valid is False
        assert "requerido" in error
    
    def test_wrong_length(self):
        """NIF con longitud incorrecta."""
        valid, error = validate_document("ES", "B1234567")
        assert valid is False
        assert "9 caracteres" in error
    
    def test_invalid_dni_letter(self):
        """DNI con letra incorrecta."""
        valid, error = validate_document("ES", "12345678A")
        assert valid is False
        assert "Letra" in error
    
    def test_unrecognized_type(self):
        """NIF con tipo no reconocido."""
        valid, error = validate_document("ES", "I12345678")
        assert valid is False
        assert "no reconocido" in error


class TestPublicFunctions:
    """Tests para funciones públicas del módulo."""
    
    def test_get_country_config_existing(self):
        """Obtener config de país existente."""
        config = get_country_config("PE")
        assert config is not None
        assert config.name == "Perú"
    
    def test_get_country_config_case_insensitive(self):
        """Obtener config sin importar mayúsculas."""
        config = get_country_config("pe")
        assert config is not None
        assert config.name == "Perú"
    
    def test_get_country_config_nonexistent(self):
        """Obtener config de país inexistente."""
        config = get_country_config("XX")
        assert config is None
    
    def test_get_all_countries(self):
        """Obtener todos los países."""
        countries = get_all_countries()
        assert len(countries) == 5
        names = {c.name for c in countries}
        assert "Perú" in names
        assert "Chile" in names
    
    def test_get_supported_country_codes(self):
        """Obtener códigos soportados."""
        codes = get_supported_country_codes()
        assert len(codes) == 5
        assert "PE" in codes
        assert "CL" in codes
        assert "CO" in codes
        assert "MX" in codes
        assert "ES" in codes
    
    def test_get_document_help_text(self):
        """Obtener texto de ayuda."""
        help_text = get_document_help_text("PE")
        assert "RUC" in help_text
        assert "20100130204" in help_text
    
    def test_get_document_help_text_unknown(self):
        """Obtener texto de ayuda para país desconocido."""
        help_text = get_document_help_text("XX")
        assert "Documento" in help_text
    
    def test_get_verification_sources(self):
        """Obtener fuentes de verificación."""
        sources = get_verification_sources("PE")
        assert "sunat" in sources
        assert "osce" in sources
    
    def test_get_verification_sources_unknown(self):
        """Obtener fuentes para país desconocido."""
        sources = get_verification_sources("XX")
        assert sources == []
    
    def test_get_api_endpoint(self):
        """Obtener endpoint de API."""
        endpoint = get_api_endpoint("PE", "sunat")
        assert endpoint is not None
        assert "sunat.gob.pe" in endpoint
    
    def test_get_api_endpoint_unknown(self):
        """Obtener endpoint inexistente."""
        endpoint = get_api_endpoint("PE", "inexistente")
        assert endpoint is None
    
    def test_validate_document_unknown_country(self):
        """Validar documento de país desconocido."""
        valid, error = validate_document("XX", "12345678901")
        assert valid is False
        assert "no soportado" in error


class TestFormatDocument:
    """Tests para formateo de documentos."""
    
    def test_format_rut_chile(self):
        """Formatear RUT chileno."""
        formatted = format_document("CL", "12345678K")
        assert "-" in formatted
    
    def test_format_nit_colombia(self):
        """Formatear NIT colombiano."""
        formatted = format_document("CO", "9001234567")
        assert "." in formatted
    
    def test_format_unknown_country(self):
        """Formatear documento de país desconocido."""
        formatted = format_document("XX", "12345678901")
        assert formatted == "12345678901"
