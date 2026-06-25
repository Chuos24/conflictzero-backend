"""
Conflict Zero - Configuración Multi-País
Módulo de validación y configuración por país para Fase 3 Enterprise.
"""

import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from enum import Enum


class CountryCode(str, Enum):
    """Códigos ISO 3166-1 alpha-2 soportados."""
    PE = "PE"
    CL = "CL"
    CO = "CO"
    MX = "MX"
    ES = "ES"


@dataclass
class CountryConfig:
    """Configuración completa de un país."""
    code: CountryCode
    name: str
    currency: str
    currency_symbol: str
    document_label: str
    document_length: Optional[int]
    document_regex: str
    document_example: str
    document_validator: callable
    verification_sources: List[str]
    api_endpoints: Dict[str, str]
    legal_framework: str
    data_protection_law: str
    timezone: str
    language: str
    date_format: str
    decimal_separator: str
    thousands_separator: str
    vat_label: str
    vat_rate: float
    phone_prefix: str
    phone_regex: str


def _validate_ruc_pe(ruc: str) -> Tuple[bool, Optional[str]]:
    """
    Valida RUC peruano (11 dígitos) con algoritmo de verificación.
    Retorna (válido, mensaje_error).
    """
    if not ruc:
        return False, "RUC es requerido"
    
    if not ruc.isdigit():
        return False, "RUC debe contener solo números"
    
    if len(ruc) != 11:
        return False, f"RUC debe tener 11 dígitos (tiene {len(ruc)})"
    
    # Validar tipo de contribuyente por primeros dígitos
    tipo = ruc[0:2]
    tipos_validos = ["10", "15", "17", "20"]  # Persona natural, sociedad, etc.
    if tipo not in tipos_validos:
        return False, f"Tipo de contribuyente no válido: {tipo}"
    
    # Algoritmo de validación módulo 11
    factores = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2]
    suma = sum(int(ruc[i]) * factores[i] for i in range(10))
    resto = suma % 11
    digito_verificador = 11 - resto
    if digito_verificador == 10:
        digito_verificador = 0
    elif digito_verificador == 11:
        digito_verificador = 1
    
    if int(ruc[10]) != digito_verificador:
        return False, "Dígito verificador inválido"
    
    return True, None


def _validate_rut_cl(rut: str) -> Tuple[bool, Optional[str]]:
    """
    Valida RUT chileno ( formato: 12345678-9 o 12345678-K ).
    """
    if not rut:
        return False, "RUT es requerido"
    
    # Normalizar: quitar puntos y espacios
    rut = rut.replace(".", "").replace(" ", "").upper()
    
    if not re.match(r"^\d{7,8}-[\dK]$", rut):
        return False, "Formato RUT inválido. Debe ser: 12345678-9 o 12345678-K"
    
    numero, dv = rut.split("-")
    
    # Algoritmo módulo 11
    suma = 0
    multiplicador = 2
    for d in reversed(numero):
        suma += int(d) * multiplicador
        multiplicador = multiplicador + 1 if multiplicador < 7 else 2
    
    resto = suma % 11
    dv_calculado = 11 - resto
    
    if dv_calculado == 11:
        dv_calculado = "0"
    elif dv_calculado == 10:
        dv_calculado = "K"
    else:
        dv_calculado = str(dv_calculado)
    
    if dv != dv_calculado:
        return False, "Dígito verificador inválido"
    
    return True, None


def _validate_nit_co(nit: str) -> Tuple[bool, Optional[str]]:
    """
    Valida NIT colombiano (9 dígitos, puede incluir guión).
    """
    if not nit:
        return False, "NIT es requerido"
    
    nit = nit.replace("-", "").replace(" ", "")
    
    if not nit.isdigit():
        return False, "NIT debe contener solo números"
    
    if len(nit) < 9 or len(nit) > 10:
        return False, f"NIT debe tener 9-10 dígitos (tiene {len(nit)})"
    
    # Algoritmo de validación Dian
    primos = [3, 7, 13, 17, 19, 23, 29, 37, 41]
    numero = nit[:-1] if len(nit) == 10 else nit
    dv = int(nit[-1]) if len(nit) == 10 else 0
    
    suma = sum(int(numero[i]) * primos[i] for i in range(len(numero)))
    residuo = suma % 11
    
    if residuo > 1:
        dv_calculado = 11 - residuo
    else:
        dv_calculado = residuo
    
    if dv != dv_calculado:
        return False, "Dígito de verificación inválido"
    
    return True, None


def _validate_rfc_mx(rfc: str) -> Tuple[bool, Optional[str]]:
    """
    Valida RFC mexicano (12-13 caracteres).
    Persona moral: 12 chars (3 letras + 6 fecha + 3 homoclave)
    Persona física: 13 chars (4 letras + 6 fecha + 3 homoclave)
    """
    if not rfc:
        return False, "RFC es requerido"
    
    rfc = rfc.upper().replace(" ", "")
    
    if len(rfc) not in [12, 13]:
        return False, f"RFC debe tener 12 o 13 caracteres (tiene {len(rfc)})"
    
    # Patrón básico: letras + fecha + homoclave
    if len(rfc) == 12:  # Persona moral
        if not re.match(r"^[A-Z]{3}\d{6}[A-Z0-9]{3}$", rfc):
            return False, "Formato RFC inválido para persona moral"
    else:  # Persona física
        if not re.match(r"^[A-Z]{4}\d{6}[A-Z0-9]{3}$", rfc):
            return False, "Formato RFC inválido para persona física"
    
    # Validar fecha
    fecha_str = rfc[3:9] if len(rfc) == 12 else rfc[4:10]
    try:
        year = int(fecha_str[0:2])
        month = int(fecha_str[2:4])
        day = int(fecha_str[4:6])
        
        # Año razonable (entre 1900 y 2099)
        year_full = 1900 + year if year >= 50 else 2000 + year
        from datetime import date
        date(year_full, month, day)
    except (ValueError, IndexError):
        return False, "Fecha en RFC inválida"
    
    return True, None


def _validate_nif_es(nif: str) -> Tuple[bool, Optional[str]]:
    """
    Valida NIF/CIF español (9 caracteres).
    """
    if not nif:
        return False, "NIF/CIF es requerido"
    
    nif = nif.upper().replace(" ", "").replace("-", "")
    
    if len(nif) != 9:
        return False, f"NIF/CIF debe tener 9 caracteres (tiene {len(nif)})"
    
    # Tipos de entidad
    tipo = nif[0]
    tipos_empresa = "ABCDEFGHJNPQRSUVW"  # CIF para empresas
    tipos_persona = "KLMXYZ"  # NIE para extranjeros
    tipos_dni = "1234567890"  # DNI para españoles
    
    if tipo in tipos_dni:
        # DNI: 8 números + letra
        if not re.match(r"^\d{8}[A-Z]$", nif):
            return False, "Formato DNI inválido"
        
        letras = "TRWAGMYFPDXBNJZSQVHLCKE"
        numero = int(nif[0:8])
        letra_calculada = letras[numero % 23]
        if nif[8] != letra_calculada:
            return False, "Letra de DNI inválida"
    
    elif tipo in tipos_persona:
        # NIE
        if not re.match(r"^[KLMXYZ]\d{7}[A-Z]$", nif):
            return False, "Formato NIE inválido"
    
    elif tipo in tipos_empresa:
        # CIF
        if not re.match(r"^[A-Z]\d{7}[A-Z0-9]$", nif):
            return False, "Formato CIF inválido"
    
    else:
        return False, f"Tipo de documento no reconocido: {tipo}"
    
    return True, None


# ============================================================
# CONFIGURACIÓN DE PAÍSES
# ============================================================

COUNTRY_CONFIGS: Dict[CountryCode, CountryConfig] = {
    CountryCode.PE: CountryConfig(
        code=CountryCode.PE,
        name="Perú",
        currency="PEN",
        currency_symbol="S/",
        document_label="RUC",
        document_length=11,
        document_regex=r"^\d{11}$",
        document_example="20100130204",
        document_validator=_validate_ruc_pe,
        verification_sources=["sunat", "osce", "tce", "indecopi"],
        api_endpoints={
            "sunat": "https://api.sunat.gob.pe/v1",
            "osce": "https://api.osce.gob.pe/v1",
            "tce": "https://api.tce.gob.pe/v1",
            "indecopi": "https://api.indecopi.gob.pe/v1"
        },
        legal_framework="Ley N° 29733 - Protección de Datos Personales",
        data_protection_law="Ley N° 29733",
        timezone="America/Lima",
        language="es",
        date_format="DD/MM/YYYY",
        decimal_separator=".",
        thousands_separator=",",
        vat_label="IGV",
        vat_rate=0.18,
        phone_prefix="+51",
        phone_regex=r"^\+51\s?\d{9}$"
    ),
    
    CountryCode.CL: CountryConfig(
        code=CountryCode.CL,
        name="Chile",
        currency="CLP",
        currency_symbol="$",
        document_label="RUT",
        document_length=9,
        document_regex=r"^\d{7,8}-[\dK]$",
        document_example="76.123.456-K",
        document_validator=_validate_rut_cl,
        verification_sources=["sii", "chilecompra", "tdlc"],
        api_endpoints={
            "sii": "https://api.sii.cl/v1",
            "chilecompra": "https://api.mercadopublico.cl/v1",
            "tdlc": "https://api.tdlc.cl/v1"
        },
        legal_framework="Ley N° 19.628 - Protección de la Vida Privada",
        data_protection_law="Ley N° 19.628",
        timezone="America/Santiago",
        language="es",
        date_format="DD/MM/YYYY",
        decimal_separator=",",
        thousands_separator=".",
        vat_label="IVA",
        vat_rate=0.19,
        phone_prefix="+56",
        phone_regex=r"^\+56\s?\d{9}$"
    ),
    
    CountryCode.CO: CountryConfig(
        code=CountryCode.CO,
        name="Colombia",
        currency="COP",
        currency_symbol="$",
        document_label="NIT",
        document_length=9,
        document_regex=r"^\d{9,10}$",
        document_example="900.123.456-7",
        document_validator=_validate_nit_co,
        verification_sources=["dian", "secop", "sic"],
        api_endpoints={
            "dian": "https://api.dian.gov.co/v1",
            "secop": "https://api.contratacion.gov.co/v1",
            "sic": "https://api.sic.gov.co/v1"
        },
        legal_framework="Ley 1581 de 2012 - Protección de Datos",
        data_protection_law="Ley 1581 de 2012",
        timezone="America/Bogota",
        language="es",
        date_format="DD/MM/YYYY",
        decimal_separator=",",
        thousands_separator=".",
        vat_label="IVA",
        vat_rate=0.19,
        phone_prefix="+57",
        phone_regex=r"^\+57\s?\d{10}$"
    ),
    
    CountryCode.MX: CountryConfig(
        code=CountryCode.MX,
        name="México",
        currency="MXN",
        currency_symbol="$",
        document_label="RFC",
        document_length=None,  # Variable: 12 o 13
        document_regex=r"^[A-Z]{3,4}\d{6}[A-Z0-9]{3}$",
        document_example="ABCD010101ABC",
        document_validator=_validate_rfc_mx,
        verification_sources=["sat", "compranet", "cofece"],
        api_endpoints={
            "sat": "https://api.sat.gob.mx/v1",
            "compranet": "https://api.compranet.gob.mx/v1",
            "cofece": "https://api.cofece.gob.mx/v1"
        },
        legal_framework="Ley Federal de Protección de Datos Personales",
        data_protection_law="LFPDPPP",
        timezone="America/Mexico_City",
        language="es",
        date_format="DD/MM/YYYY",
        decimal_separator=".",
        thousands_separator=",",
        vat_label="IVA",
        vat_rate=0.16,
        phone_prefix="+52",
        phone_regex=r"^\+52\s?\d{10}$"
    ),
    
    CountryCode.ES: CountryConfig(
        code=CountryCode.ES,
        name="España",
        currency="EUR",
        currency_symbol="€",
        document_label="NIF/CIF",
        document_length=9,
        document_regex=r"^[A-Z0-9]{9}$",
        document_example="B12345678",
        document_validator=_validate_nif_es,
        verification_sources=["aeat", "boe", "cnmc"],
        api_endpoints={
            "aeat": "https://api.aeat.es/v1",
            "boe": "https://api.boe.es/v1",
            "cnmc": "https://api.cnmc.es/v1"
        },
        legal_framework="RGPD + LOPDGDD",
        data_protection_law="RGPD",
        timezone="Europe/Madrid",
        language="es",
        date_format="DD/MM/YYYY",
        decimal_separator=",",
        thousands_separator=".",
        vat_label="IVA",
        vat_rate=0.21,
        phone_prefix="+34",
        phone_regex=r"^\+34\s?\d{9}$"
    )
}


# ============================================================
# FUNCIONES PÚBLICAS
# ============================================================

def get_country_config(country_code: str) -> Optional[CountryConfig]:
    """Obtiene configuración de país por código."""
    try:
        code = CountryCode(country_code.upper())
        return COUNTRY_CONFIGS.get(code)
    except ValueError:
        return None


def get_all_countries() -> List[CountryConfig]:
    """Retorna lista de todos los países configurados."""
    return list(COUNTRY_CONFIGS.values())


def get_supported_country_codes() -> List[str]:
    """Retorna lista de códigos de país soportados."""
    return [c.value for c in CountryCode]


def validate_document(country_code: str, document: str) -> Tuple[bool, Optional[str]]:
    """
    Valida un documento de identificación según el país.
    
    Args:
        country_code: Código ISO del país (PE, CL, CO, MX, ES)
        document: Número de documento a validar
    
    Returns:
        Tuple[bool, Optional[str]]: (válido, mensaje_error)
    """
    config = get_country_config(country_code)
    if not config:
        return False, f"País no soportado: {country_code}"
    
    return config.document_validator(document)


def format_document(country_code: str, document: str) -> str:
    """
    Formatea un documento según las convenciones del país.
    """
    config = get_country_config(country_code)
    if not config:
        return document
    
    document = document.strip().upper()
    
    if country_code.upper() == "PE":
        # RUC: 20100130204 → sin formato especial
        return document
    elif country_code.upper() == "CL":
        # RUT: 12345678K → 12.345.678-K
        doc = document.replace(".", "").replace("-", "")
        if len(doc) >= 8:
            dv = doc[-1]
            num = doc[:-1]
            return f"{num[:-3]}.{num[-3:]}-{dv}" if len(num) > 3 else f"{num}-{dv}"
    elif country_code.upper() == "CO":
        # NIT: 9001234567 → 900.123.456-7
        doc = document.replace(".", "").replace("-", "")
        if len(doc) >= 9:
            dv = doc[-1]
            base = doc[:-1]
            return f"{base[:3]}.{base[3:6]}.{base[6:]}-{dv}" if len(base) >= 7 else document
    elif country_code.upper() == "MX":
        # RFC: ABCD010101ABC → ya está formateado
        return document
    elif country_code.upper() == "ES":
        # NIF: B12345678 → B-12345678 (opcional)
        return document
    
    return document


def get_document_help_text(country_code: str) -> str:
    """Retorna texto de ayuda para el documento de un país."""
    config = get_country_config(country_code)
    if not config:
        return "Documento de identificación"
    
    return f"{config.document_label} ({config.document_example})"


def get_verification_sources(country_code: str) -> List[str]:
    """Retorna fuentes de verificación disponibles para un país."""
    config = get_country_config(country_code)
    if not config:
        return []
    return config.verification_sources


def get_api_endpoint(country_code: str, source: str) -> Optional[str]:
    """Retorna endpoint de API para una fuente de verificación en un país."""
    config = get_country_config(country_code)
    if not config:
        return None
    return config.api_endpoints.get(source)
