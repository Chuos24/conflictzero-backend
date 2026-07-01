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
GET  /health                               → Estado del sistema y agentes activos
GET  /agentes                              → Lista de agentes y sus fuentes
GET  /consulta/{ruc}?sector=XXX            → Homologación completa del proveedor
GET  /generar-certificado/{ruc}?sector=XXX → Certificado HTML en S3
```

## Variables de entorno

```
S3_BUCKET      = conflictzero-documentos-prod
BUSCARUC_TOKEN = <token cuando disponible>
```

## Estructura del repo

```
lambdas/
  homologacion/   ← Motor principal activo: 6 agentes + scoring + certificados
  consulta-ruc/   ← Fase 3: lambda dedicada SUNAT
  sanciones/      ← Fase 3: lambda dedicada OSCE/TCE/SUNAFIL
  scoring/        ← Fase 3: motor de scoring aislado
  certificado/    ← Fase 3: generador de certificados
  health/         ← Fase 3: health check dedicado
layers/           ← Layers compartidos (Fase 3)
```

## Deploy rápido (AWS CloudShell)

```bash
curl -s https://raw.githubusercontent.com/Chuos24/conflictzero-backend/main/lambdas/homologacion/lambda_function.py \
  | python3 -c "
import sys, zipfile, io
content = sys.stdin.buffer.read()
buf = io.BytesIO()
with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as z:
    z.writestr('lambda_function.py', content)
with open('/tmp/lambda.zip', 'wb') as f:
    f.write(buf.getvalue())
print('ZIP OK:', len(buf.getvalue()), 'bytes')
" && aws lambda update-function-code \
  --function-name conflictzero-homologacion \
  --zip-file fileb:///tmp/lambda.zip \
  --query 'LastModified'
```

## Scoring

El score de 0–100 pondera categorías según el agente sectorial:
- **≥ 70** → APROBADO ✅
- **40–69** → OBSERVADO ⚠️
- **< 40** → RECHAZADO ❌

## Estado de integración de fuentes

| Fuente | Estado |
|---|---|
| SUNAT (vía BuscarRUC) | 🔄 Pendiente token BUSCARUC_TOKEN |
| OSCE/TCE inhabilitados | ✅ Activo (scraping) |
| SUNAFIL | 🔄 Pendiente (datos abiertos CSV) |
| OEFA | 🔄 Pendiente (datos abiertos) |
| Burós de crédito | 🔄 Pendiente (partnership) |
| SBS / SMV | 🔄 Pendiente (datos abiertos) |
| Poder Judicial | 🔄 Pendiente (scraping) |

## Roadmap

| Fase | Descripción | Estado |
|---|---|---|
| Fase 1 | Limpieza repo + bucket correcto | ✅ Completa |
| Fase 2 | DynamoDB cache + API Gateway verificado | 🔄 En curso |
| Fase 3 | Separar lambdas individuales | ⏳ Pendiente |
| Fase 4 | Integrar fuentes reales (tokens) | ⏳ Pendiente |
