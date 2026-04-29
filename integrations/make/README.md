# Conflict Zero - Make (Integromat) Integration

Integración oficial de Conflict Zero con [Make](https://www.make.com/) (anteriormente Integromat) para automatizar flujos de verificación y monitoreo de proveedores.

## Requisitos

- Cuenta en [Make](https://www.make.com/)
- API Key de Conflict Zero (obtenible desde tu dashboard en Configuración > API)

## Instalación

1. Ve a tu escenario en Make
2. Haz clic en "Add module" y busca "Conflict Zero"
3. Conecta tu cuenta ingresando tu API Key
4. Comienza a usar las acciones y triggers disponibles

## Acciones Disponibles

### 1. Verify RUC
Verifica una empresa peruana por su RUC.

**Input:**
- `ruc` (texto, requerido): Número de RUC de 11 dígitos

**Output:**
- `company_name`: Razón social
- `status`: Estado (active, inactive, suspended)
- `risk_score`: Puntuación de riesgo (0-100)
- `risk_level`: Nivel (bajo, medio, alto, crítico)
- `sanctions_count`: Cantidad de sanciones
- `sunat_debt`: Deuda con SUNAT

### 2. Compare Companies
Compara hasta 5 empresas lado a lado.

**Input:**
- `rucs` (array): Lista de RUCs a comparar

**Output:**
- `companies`: Array con detalles de cada empresa
- `best_option`: RUC con menor riesgo
- `risk_summary`: Resumen comparativo

### 3. Get Risk Score
Obtiene puntuación de riesgo detallada.

**Input:**
- `ruc` (texto, requerido)

**Output:**
- `total_score`: Puntuación global
- `risk_level`: Nivel de riesgo
- `factors`: Array de factores ponderados

### 4. Add to Network
Agrega un proveedor a tu red monitoreada.

**Input:**
- `ruc` (texto, requerido)
- `company_name` (texto, opcional)

**Output:**
- `id`: ID del registro
- `status`: Estado (added, already_exists)
- `added_at`: Fecha de registro

### 5. Get Monitoring Alerts
Obtiene alertas recientes de tu red.

**Input:**
- `status` (select, opcional): pending, sent, read, dismissed
- `limit` (número, opcional): Cantidad de resultados (default: 20)

**Output:**
- `alerts`: Array de alertas
- `total_count`: Total de alertas
- `unread_count`: No leídas

### 6. Create Webhook
Registra un webhook para alertas en tiempo real.

**Input:**
- `url` (texto, requerido): URL del webhook
- `events` (array): alert.created, change.detected, score.updated

**Output:**
- `webhook_id`: ID del webhook
- `secret`: Secreto para verificar firma HMAC
- `status`: Estado (active)

### 7. Get Compliance Certificate
Genera certificado de cumplimiento.

**Input:**
- `ruc` (texto, requerido)

**Output:**
- `certificate_url`: URL del certificado PDF
- `expires_at`: Fecha de expiración
- `verification_code`: Código de verificación

### 8. Search Company
Busca empresa por nombre o RUC.

**Input:**
- `query` (texto, requerido)

**Output:**
- `results`: Array de resultados
- `total`: Cantidad total

## Triggers

### New Alert
Se activa cuando se genera una nueva alerta.

**Output:**
- `alert_id`, `company_ruc`, `company_name`
- `alert_type`, `severity`, `message`, `created_at`

### Supplier Changed
Se activa cuando cambia el estado de un proveedor monitoreado.

**Output:**
- `change_id`, `company_ruc`, `change_type`
- `previous_value`, `new_value`, `severity`

### Score Updated
Se activa cuando cambia la puntuación de riesgo.

**Output:**
- `company_ruc`, `previous_score`, `new_score`
- `previous_level`, `new_level`

## Ejemplos de Escenarios

### Escenario 1: Alerta → Slack
1. Trigger: **New Alert** (severidad = critical)
2. Filtro: Solo alertas críticas
3. Acción: Enviar mensaje a Slack #alerts

### Escenario 2: Nuevo proveedor → Verificación automática
1. Trigger: Google Sheets (nueva fila)
2. Acción: **Verify RUC**
3. Condición: Si risk_level = "high"
4. Acción: Enviar email al procurement

### Escenario 3: Reporte semanal
1. Trigger: Schedule (todos los lunes 9am)
2. Acción: **Get Monitoring Alerts** (limit: 100, última semana)
3. Acción: Crear Google Sheets con resumen
4. Acción: Enviar email con link

## Seguridad

- Todas las llamadas usan HTTPS
- La API Key se almacena cifrada en Make
- Los webhooks incluyen firma HMAC en header `X-ConflictZero-Signature`

## Soporte

¿Problemas con la integración? Escríbenos a:
- Email: soporte@conflictzero.com
- Dashboard: https://app.conflictzero.com/support

---

*Conflict Zero © 2026 - Verificación Inteligente de Proveedores*
