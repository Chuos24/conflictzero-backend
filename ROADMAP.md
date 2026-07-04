# ConflictZero Backend — Roadmap Técnico

## Stack Tecnológico

- **Runtime:** Python 3.11 en AWS Lambda
- **API:** Amazon API Gateway (REST)
- **Base de datos:** DynamoDB (caché) + RDS PostgreSQL/Aurora (datos)
- **Autenticación:** Amazon Cognito
- **Storage:** Amazon S3
- **Colas / Jobs:** Amazon EventBridge
- **Caché:** Redis
- **Monitoreo:** Amazon CloudWatch
- **Email:** Amazon SES
- **IA:** Amazon Bedrock
- **Seguridad:** AWS KMS, WAF, CloudTrail
- **Pagos:** Culqi / PayU
- **IaC:** AWS SAM (template.yaml)

---

## Fases del Proyecto

### Fase 1 — Base ✅ Completada
- Arquitectura AWS, VPC, IAM, CI/CD
- Cognito auth, API Gateway, lambdas base
- DynamoDB caché, PostgreSQL schema

### Fase 2 — Motor de Homologación ✅ Completada
- Lambda homologacion activa
- 10 categorías de scoring con pesos por sector
- Integración SUNAT con caché Redis
- Sistema de tokens y billetera interna

### Fase 3 — Fuentes de Datos 🔴 En progreso

#### Semana 10: Scrapers de fuentes públicas
```
Fuentes: OSCE, RNP, TCE, SUNAFIL, OEFA
Arquitectura:
  - EventBridge scheduled rules → Lambda scraper por fuente
  - Raw data → S3 (conflictzero-scrapers-raw/)
  - Normalized data → PostgreSQL tabla fuentes_externas
  - Errores → CloudWatch Alarms + SNS
Lambdas a crear:
  - conflictzero-scraper-osce
  - conflictzero-scraper-rnp
  - conflictzero-scraper-tce
  - conflictzero-scraper-sunafil
  - conflictzero-scraper-oefa
```

#### Semana 11: Macro-agentes sectoriales
```
Agentes: CONSTRUCCIÓN, SERVICIOS, PRODUCTIVO, FINANCIERO, TECH, TRANSVERSALES
Arquitectura:
  - Activación automática según sector del usuario (header X-Sector)
  - Cada agente define sus fuentes relevantes y pesos específicos
  - Estructura extensible: agregar fuente sin refactorizar agente
Lambdas a crear:
  - conflictzero-agente-construccion
  - conflictzero-agente-servicios
  - conflictzero-agente-productivo
  - conflictzero-agente-financiero
  - conflictzero-agente-tech
  - conflictzero-agente-transversales
```

### Fase 4 — Monetización y Seguridad 🔴 Pendiente

#### Semana 12: Pagos
```
Pasarela: Culqi (Perú primario) + PayU (fallback Latam)
Flujo:
  1. Usuario inicia pago → Lambda conflictzero-pagos
  2. Webhook confirmación → activar membresía/tokens en PostgreSQL
  3. Si membresía vencida → bloquear endpoints de consulta
Tablas nuevas: pagos, membresías, facturas
```

#### Semana 13: Seguridad producción
```
- AWS KMS: cifrado de datos sensibles en RDS y S3
- AWS WAF: reglas en API Gateway (rate limiting, geo-blocking)
- AWS CloudTrail: auditoría completa de llamadas API
- Cumplimiento Ley 29733: anonimización, consentimiento, retención
```

### Fase 5 — Documentos e IA 🟡 Pendiente

#### Semana 14: Almacenamiento documental
```
- S3 buckets por ambiente con acceso privado
- Lambda conflictzero-documentos: upload, validación, extracción
- Amazon Textract: OCR de PDFs e imágenes
- Vinculación documento → score de categoría
```

#### Semana 15: Amazon Bedrock
```
- Resúmenes ejecutivos del proveedor en lenguaje natural
- Recomendaciones de IA basadas en score y fuentes verificadas
- Generación automática de observaciones por categoría
Modelo: Claude 3 Sonnet via Bedrock
```

### Fase 6 — Optimización y Trazabilidad 🔵 Pendiente

#### Semana 16-17: Monitoreo y trazabilidad
```
- EventBridge: revisión semanal automática de proveedores aprobados
- SES: alertas por cambios de score o nuevas sanciones
- Trazabilidad: log de visualizaciones, descargas, contactos
- Badge 'Transacción verificada por ConflictZero'
```

#### Semana 18: Blockchain y optimización
```
- Blockchain registry para scores, sellos y transacciones
- AWS Budgets para control de costos
- TTL Redis optimizado, backups y snapshots RDS
- Plan de recuperación ante fallos (RTO/RPO)
```

---

## Lambdas Pendientes de Uncommentar en template.yaml

Estas lambdas ya tienen código pero están comentadas en el SAM:
- `ConsultaRucFunction` → `lambdas/consulta-ruc/`
- `ConsultaSancionesFunction` → `lambdas/sanciones/`
- `ScoringFunction` → `lambdas/scoring/`
- `CertificadoFunction` → `lambdas/certificado/`

**Acción inmediata:** Descomentar en `template.yaml` y ejecutar `sam deploy`.
