# ConflictZero Backend

Plataforma SaaS B2B de homologación, verificación y descubrimiento de proveedores para el mercado peruano.

## Arquitectura

AWS Lambda + API Gateway (Python 3.11). Sin dependencias externas — solo stdlib y boto3.

## Agentes sectoriales

| Agente | Sectores | Fuentes principales |
|---|---|---|
| `construccion` | Obras, infraestructura, ingeniería | SUNAT, OSCE, RNP, TCE, CIP |
| `servicios` | Limpieza, seguridad, logística | SUNAT, SUNAFIL, MTPE, INDECOPI |
| `productivo` | Alimentos, minería, energía | PRODUCE, SENASA, OEFA, OSINERGMIN |
| `financiero` | Fintech, seguros, factoring | SBS, SMV, UIF, burós de crédito |
| `tech` | SaaS, ciberseguridad, TI | INDECOPI, ISO 27001, protección de datos |
| `transversales` | Compliance general | Poder Judicial, listas restrictivas |

## Endpoints

```
GET  /health                          → Estado del sistema y agentes activos
GET  /agentes                         → Lista de agentes y sus fuentes
GET  /consulta/{ruc}?sector=XXX       → Homologación completa del proveedor
GET  /generar-certificado/{ruc}?sector=XXX → Certificado HTML en S3
```

## Variables de entorno

```
S3_BUCKET     = conflictzero-certificados-prod
BACKEND_URL   = https://conflictzero-backend1.onrender.com
```

## Estructura del repo

```
lambdas/
  homologacion/     ← Motor principal: 6 agentes + scoring + certificados
  consulta-ruc/     ← Lambda específica consulta SUNAT
  sanciones/        ← Lambda específica sanciones OSCE/TCE/SUNAFIL
  scoring/          ← Motor de scoring aislado
  certificado/      ← Generador de certificados
  health/           ← Health check
layers/             ← Layers compartidos (futuro)
```

## Deploy rápido (AWS CloudShell)

```bash
# 1. Clonar y empaquetar
git clone https://github.com/Chuos24/conflictzero-backend.git
cd conflictzero-backend/lambdas/homologacion
zip -r ../../deploy.zip lambda_function.py

# 2. Actualizar Lambda existente
cd ../..
aws lambda update-function-code \
  --function-name conflictzero-homologacion \
  --zip-file fileb://deploy.zip

# 3. Verificar
aws lambda invoke \
  --function-name conflictzero-homologacion \
  --payload '{"path":"/health","httpMethod":"GET"}' \
  response.json && cat response.json
```

## Scoring

El score de 0–100 pondera categorías según el agente sectorial:
- **≥ 70** → APROBADO ✅
- **40–69** → OBSERVADO ⚠️
- **< 40** → RECHAZADO ❌

## Estado de integración de fuentes

| Fuente | Estado |
|---|---|
| SUNAT (vía Render) | ✅ Activo |
| OSCE/TCE inhabilitados | ✅ Activo (scraping) |
| SUNAFIL | 🔄 Pendiente (datos abiertos CSV) |
| OEFA | 🔄 Pendiente (datos abiertos) |
| Burós de crédito | 🔄 Pendiente (partnership) |
| SBS / SMV | 🔄 Pendiente (datos abiertos) |
| Poder Judicial | 🔄 Pendiente (scraping) |
