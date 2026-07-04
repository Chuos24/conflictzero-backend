# ConflictZero Backend — Estado del Proyecto

> Última actualización: Julio 2026

## ✅ Completado

### Infraestructura AWS Base
- VPC, subredes públicas y privadas, security groups
- IAM con roles mínimos, MFA activado
- CI/CD pipeline configurado con ambientes dev, staging y producción
- API Gateway configurado con CORS para czperu.com
- SharedLayer compartido entre lambdas (cache DynamoDB, CORS, validación RUC)

### Base de Datos
- DynamoDB tabla `conflictzero-consultas` con TTL y PAY_PER_REQUEST
- Esquema PostgreSQL/Aurora con tablas: usuarios, empresas, roles, sectores, agentes, tokens, homologaciones, fuentes, scores y auditoría

### Autenticación
- Amazon Cognito con roles proveedor y contratista
- Flujo de registro, login, recuperación de contraseña

### Lambdas Deployadas
| Lambda | Estado | Descripción |
|--------|--------|-------------|
| `conflictzero-health` | ✅ Activa | Healthcheck del sistema |
| `conflictzero-homologacion` | ✅ Activa | Motor principal de homologación |
| `consulta-ruc` | ⚠️ Comentada en SAM | Integración SUNAT lista pero no deployada |
| `sanciones` | ⚠️ Comentada en SAM | Consulta OSCE/TCE lista pero no deployada |
| `scoring` | ⚠️ Comentada en SAM | Motor de scoring listo pero no deployado |
| `certificado` | ⚠️ Comentada en SAM | Generación de certificados lista pero no deployada |

### Motor de Homologación
- 10 categorías: identidad legal, tributario, laboral, regulatorio, financiero, legal, reputacional, ambiental, técnico y compliance
- Pesos de scoring por categoría y por sector
- Reglas: Aprobado, Aprobado con observaciones, En revisión, No recomendado
- Score general y por categoría con historial

### Integración SUNAT
- API comercial para consulta por RUC
- Caché Redis para evitar consultas repetidas
- Tabla de auditoría de cada consulta

### Sistema de Tokens
- Billetera interna con tabla de movimientos
- Registro de compra, consumo, devolución y ajuste
- Bloqueo automático si saldo insuficiente

---

## 🔴 Pendiente — Prioridad Alta

1. **Scrapers OSCE, RNP, TCE, SUNAFIL, OEFA** — Jobs con EventBridge, raw en S3, normalizados en PostgreSQL
2. **Macro-agentes sectoriales** — CONSTRUCCIÓN, SERVICIOS, PRODUCTIVO, FINANCIERO, TECH, TRANSVERSALES
3. **Integración de pagos Culqi/PayU** — Activación post-pago, bloqueo si membresía inactiva
4. **Seguridad de producción** — KMS, WAF, CloudTrail, Ley 29733

## 🟡 Pendiente — Prioridad Media

5. **Almacenamiento documental S3** — Buckets por ambiente, Textract para PDFs
6. **Monitoreo continuo** — EventBridge semanal, alertas SES
7. **Trazabilidad de contactos** — Visualizaciones, descargas, badge verificado
8. **Amazon Bedrock** — Resúmenes ejecutivos e IA vinculada a fuentes

## 🔵 Pendiente — Prioridad Baja

9. **Optimización de costos AWS** — Budgets, TTL Redis, backups, snapshots
10. **Blockchain registry** — Registro inmutable de scores y transacciones
