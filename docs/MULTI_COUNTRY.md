# Conflict Zero - Configuración Multi-País

## Países Soportados (Fase 3)

### Implementados (Fase 1-2)
- **PE** - Perú (país base)
  - Validación: RUC (11 dígitos)
  - Fuentes: SUNAT, OSCE, TCE, INDECOPI
  - Moneda: PEN

### Planificados (Fase 3)
- **CL** - Chile
  - Validación: RUT (8-9 dígitos + dígito verificador)
  - Fuentes: SII, ChileCompra, TDLC
  - Moneda: CLP

- **CO** - Colombia
  - Validación: NIT (9 dígitos)
  - Fuentes: DIAN, SECOP, SIC
  - Moneda: COP

- **MX** - México
  - Validación: RFC (12-13 caracteres)
  - Fuentes: SAT, CompraNet, COFECE
  - Moneda: MXN

- **ES** - España
  - Validación: NIF/CIF (9 caracteres)
  - Fuentes: AEAT, BOE, CNMC
  - Moneda: EUR

## Estructura de Configuración

```python
# app/core/countries.py
COUNTRY_CONFIGS = {
    "PE": {
        "name": "Perú",
        "currency": "PEN",
        "document_label": "RUC",
        "document_length": 11,
        "document_regex": r"^\d{11}$",
        "verification_sources": ["sunat", "osce", "tce"],
        "api_endpoints": {
            "sunat": "https://api.sunat.gob.pe/v1",
            "osce": "https://api.osce.gob.pe/v1",
            "tce": "https://api.tce.gob.pe/v1"
        }
    },
    "CL": {
        "name": "Chile",
        "currency": "CLP",
        "document_label": "RUT",
        "document_length": 9,
        "document_regex": r"^\d{7,8}-[\dkK]$",
        "verification_sources": ["sii", "chilecompra"],
        "api_endpoints": {
            "sii": "https://api.sii.cl/v1",
            "chilecompra": "https://api.mercadopublico.cl/v1"
        }
    }
}
```

## Migración de Base de Datos

Para soportar multi-país, se requiere:

1. **Tabla `countries`** - Catálogo de países soportados
2. **Campo `country_code`** en tabla `companies`
3. **Campo `country_code`** en tabla `verification_requests`
4. **Índices** por país para consultas optimizadas

## Consideraciones Legales

- **Perú**: Ley de Protección de Datos Personales (Ley N° 29733)
- **Chile**: Ley N° 19.628 sobre Protección de la Vida Privada
- **Colombia**: Ley 1581 de 2012 (Protección de Datos)
- **México**: Ley Federal de Protección de Datos Personales en Posesión de los Particulares
- **España**: RGPD (Reglamento General de Protección de Datos) + LOPDGDD

## Roadmap Implementación

1. **Q3 2026**: Chile (CL) - Mercado más maduro en compliance
2. **Q4 2026**: Colombia (CO) - Alto crecimiento en contratación pública
3. **Q1 2027**: México (MX) - Mercado más grande
4. **Q2 2027**: España (ES) - Puerta a Europa

---
*Documento creado: 2026-06-22*
*Fase: 3 - Enterprise*
