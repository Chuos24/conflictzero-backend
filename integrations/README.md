# Integraciones ERP - Conflict Zero

Conectores oficiales para integrar Conflict Zero con sistemas ERP empresariales.

## Conectores Disponibles

| ERP | Tecnología | Estado | Archivo |
|-----|-----------|--------|---------|
| **SAP S/4HANA** | REST API | ✅ Beta | [`sap/sap_connector.py`](./sap/sap_connector.py) |
| **Oracle NetSuite** | SuiteScript / RESTlet | ✅ Beta | [`netsuite/netsuite_connector.py`](./netsuite/netsuite_connector.py) |
| **Microsoft Dynamics 365** | Power Automate / OData | ✅ Beta | [`dynamics/dynamics_connector.py`](./dynamics/dynamics_connector.py) |

## Automatización No-Code

| Plataforma | Tipo | Archivo |
|-----------|------|---------|
| **Zapier** | App Integration | [`zapier/manifest.json`](./zapier/manifest.json) |
| **Make (Integromat)** | App Integration | [`make/manifest.json`](./make/manifest.json) |

---

## SAP S/4HANA

### Instalación

```bash
pip install requests pydantic
```

### Uso

```python
from integrations.sap.sap_connector import SAPConnector

connector = SAPConnector(
    base_url="https://sap-server.company.com:44300",
    api_key="tu-api-key",
    username="usuario",
    password="password"
)

# Verificar un proveedor
result = connector.verify_vendor(
    vendor_code="V001",
    ruc="20100012345",
    company_code="1000"
)

print(f"Riesgo: {result['risk_level']} ({result['risk_score']})")
```

### Verificación en Lote

```python
from integrations.sap.sap_connector import SAPConnector, SAPVendorRequest

connector = SAPConnector(...)

vendors = [
    SAPVendorRequest(vendor_code="V001", company_code="1000", ruc="20100012345"),
    SAPVendorRequest(vendor_code="V002", company_code="1000", ruc="20100012346"),
]

results = connector.batch_verify_vendors(vendors)
```

### Configuración por Defecto

```python
from integrations.sap.sap_connector import DEFAULT_SAP_CONFIG

# Personalizar
config = {
    **DEFAULT_SAP_CONFIG,
    "base_url": "https://mi-sap.company.com",
    "timeout": 60
}
```

---

## Oracle NetSuite

### Autenticación

NetSuite utiliza OAuth 1.0a. Necesitarás:
- Account ID
- Consumer Key / Consumer Secret
- Token ID / Token Secret

### Uso

```python
from integrations.netsuite.netsuite_connector import NetSuiteConnector

connector = NetSuiteConnector(
    account_id="123456",
    consumer_key="consumer-key",
    consumer_secret="consumer-secret",
    token_id="token-id",
    token_secret="token-secret"
)

result = connector.verify_vendor(vendor_id="123", ruc="20100012345")
```

### SuiteScript (Instalación en NetSuite)

El archivo [`netsuite/netsuite_connector.py`](./netsuite/netsuite_connector.py) incluye el SuiteScript completo para instalar como RESTlet en NetSuite:

1. Copia la variable `SUITESCRIPT_CODE`
2. Crea un nuevo Script en NetSuite: *Customization > Scripting > Scripts > New*
3. Pega el código y deploya como RESTlet
4. Configura los campos custom:
   - `custentity_cz_risk_score` (Float)
   - `custentity_cz_status` (Text)

---

## Microsoft Dynamics 365

### Autenticación

Dynamics usa OAuth 2.0 con Client Credentials:
- Tenant ID
- Client ID / Client Secret
- Environment URL

### Uso

```python
from integrations.dynamics.dynamics_connector import DynamicsConnector

connector = DynamicsConnector(
    tenant_id="tenant-id",
    client_id="client-id",
    client_secret="client-secret",
    environment_url="https://env.crm.dynamics.com"
)

result = connector.verify_vendor(
    vendor_account="V-001",
    ruc="20100012345"
)

# Actualiza automáticamente el vendor en Dynamics con:
# - cz_riskscore
# - cz_status
# - cz_lastverified
```

### Power Automate Flow

El archivo incluye un flow JSON listo para importar en Power Automate. Ver variable `POWER_AUTOMATE_FLOW`.

---

## Tests

```bash
# Ejecutar todos los tests de integraciones
pytest integrations/tests/test_erp_connectors.py -v

# Con coverage
pytest integrations/tests/test_erp_connectors.py --cov=integrations --cov-report=html
```

---

## Roadmap

- [x] Conectores base (Python)
- [x] Tests unitarios
- [x] SuiteScript para NetSuite
- [x] Power Automate Flow para Dynamics
- [ ] Implementación OAuth real con retries
- [ ] Webhooks bidireccionales
- [ ] Sync de datos maestros completo

---

## Soporte

¿Necesitas un conector para otro ERP? 
- Abre un issue en GitHub
- Contacta: integraciones@conflictzero.com
