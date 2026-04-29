# Conflict Zero SDK - JavaScript/TypeScript

SDK oficial de Conflict Zero para integrar la API de verificación y monitoreo de proveedores en aplicaciones JavaScript y TypeScript.

## Instalación

```bash
npm install conflictzero
# o
yarn add conflictzero
```

## Uso Rápido

```javascript
import { ConflictZeroClient } from 'conflictzero';

// Inicializar cliente
const client = new ConflictZeroClient({ apiKey: 'tu_api_key' });

// Verificar un RUC
const result = await client.verifyRUC('20100012345');
console.log(result.data);

// Comparar múltiples empresas
const comparison = await client.compareCompanies(['20100012345', '20100067890']);
console.log(comparison.data);

// Obtener alertas de monitoreo
const alerts = await client.getMonitoringAlerts('unread');
console.log(alerts.data);
```

## Autenticación

Obtén tu API key desde el [dashboard de Conflict Zero](https://app.conflictzero.com/settings/api).

## Métodos Disponibles

### Verificación
- `verifyRUC(ruc)` - Verifica un RUC peruano
- `verifyBulk(rucs)` - Verifica múltiples RUCs
- `getCompanyDetails(ruc)` - Obtiene detalles completos

### Comparación
- `compareCompanies(rucs)` - Compara hasta 10 empresas

### Scoring
- `getRiskScore(ruc)` - Score de riesgo 0-100
- `getComplianceCertificate(ruc)` - Certificado digital

### Red de Proveedores
- `getNetwork()` - Lista proveedores en tu red
- `addToNetwork(ruc, name, tags)` - Agrega proveedor
- `removeFromNetwork(companyId)` - Elimina proveedor

### Monitoreo Continuo
- `getMonitoringAlerts(status)` - Alertas detectadas
- `getMonitoringChanges(severity)` - Cambios detectados
- `createSnapshot(companyId)` - Crea snapshot manual
- `runMonitoring()` - Ejecuta monitoreo manual
- `getMonitoringStats()` - Estadísticas de monitoreo

### Webhooks
- `registerWebhook(url, events, secret)` - Registra webhook
- `listWebhooks()` - Lista webhooks registrados
- `deleteWebhook(webhookId)` - Elimina webhook

## Manejo de Errores

```javascript
import { ConflictZeroClient, AuthenticationError, RateLimitError } from 'conflictzero';

try {
  await client.verifyRUC('20100012345');
} catch (error) {
  if (error instanceof AuthenticationError) {
    console.log('API key inválida');
  } else if (error instanceof RateLimitError) {
    console.log('Rate limit excedido');
  } else {
    console.log('Error:', error.message);
  }
}
```

## TypeScript

El SDK incluye tipos integrados. No requiere `@types/conflictzero`.

```typescript
import { ConflictZeroClient } from 'conflictzero';

const client = new ConflictZeroClient({ apiKey: process.env.CZ_API_KEY! });
const result = await client.verifyRUC('20100012345');
// result.data está tipado automáticamente
```

## Licencia

MIT License
