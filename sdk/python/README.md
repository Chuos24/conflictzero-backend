# Conflict Zero SDK - Python

SDK oficial de Conflict Zero para integrar la API de verificación y monitoreo de proveedores en aplicaciones Python.

## Instalación

```bash
pip install conflictzero
```

## Uso Rápido

```python
from conflictzero import ConflictZeroClient

# Inicializar cliente
client = ConflictZeroClient(api_key="tu_api_key")

# Verificar un RUC
result = client.verify_ruc("20100012345")
print(result.data)

# Comparar múltiples empresas
comparison = client.compare_companies(["20100012345", "20100067890"])
print(comparison.data)

# Obtener alertas de monitoreo
alerts = client.get_monitoring_alerts(status="unread")
print(alerts.data)
```

## Autenticación

Obtén tu API key desde el [dashboard de Conflict Zero](https://app.conflictzero.com/settings/api).

## Métodos Disponibles

### Verificación
- `verify_ruc(ruc)` - Verifica un RUC peruano
- `verify_bulk(rucs)` - Verifica múltiples RUCs
- `get_company_details(ruc)` - Obtiene detalles completos

### Comparación
- `compare_companies(rucs)` - Compara hasta 10 empresas

### Scoring
- `get_risk_score(ruc)` - Score de riesgo 0-100
- `get_compliance_certificate(ruc)` - Certificado digital

### Red de Proveedores
- `get_network()` - Lista proveedores en tu red
- `add_to_network(ruc, name, tags)` - Agrega proveedor
- `remove_from_network(company_id)` - Elimina proveedor

### Monitoreo Continuo
- `get_monitoring_alerts(status)` - Alertas detectadas
- `get_monitoring_changes(severity)` - Cambios detectados
- `create_snapshot(company_id)` - Crea snapshot manual
- `run_monitoring()` - Ejecuta monitoreo manual
- `get_monitoring_stats()` - Estadísticas de monitoreo

### Webhooks
- `register_webhook(url, events, secret)` - Registra webhook
- `list_webhooks()` - Lista webhooks registrados
- `delete_webhook(webhook_id)` - Elimina webhook

## Manejo de Errores

```python
from conflictzero import (
    ConflictZeroClient,
    AuthenticationError,
    RateLimitError,
    NotFoundError,
    ValidationError
)

try:
    client.verify_ruc("20100012345")
except AuthenticationError:
    print("API key inválida")
except RateLimitError as e:
    print(f"Rate limit: {e}")
except NotFoundError:
    print("RUC no encontrado")
except ValidationError as e:
    print(f"Error de validación: {e}")
```

## Context Manager

```python
with ConflictZeroClient(api_key="tu_api_key") as client:
    result = client.verify_ruc("20100012345")
    # La sesión se cierra automáticamente
```

## Licencia

MIT License
