# ConflictZero Backend v3.0 — AWS Serverless

Arquitectura 100% serverless en AWS. Sin servidores, sin Render, sin Vercel.

## Stack

| Capa | Servicio AWS |
|------|--------------|
| API | API Gateway (REST) |
| Lógica | AWS Lambda (Python 3.12) |
| Cache | DynamoDB (TTL automático) |
| Certificados | S3 (presigned URLs) |
| Secrets | SSM Parameter Store |
| Infra como código | AWS SAM (`template.yaml`) |

## Endpoints

| Método | Ruta | Lambda | Descripción |
|--------|------|--------|-------------|
| GET | `/health` | health | Status de la API |
| GET | `/consulta-ruc/{ruc}` | consulta-ruc | Datos SUNAT |
| GET | `/sanciones/{ruc}` | sanciones | OSCE + TCE |
| GET | `/consulta-completa/{ruc}` | scoring | Score de riesgo completo |
| GET | `/generar-certificado/{ruc}` | certificado | Genera y sube certificado a S3 |

## Estructura

```
conflictzero-backend/
├── template.yaml              # SAM - infraestructura como código
├── lambdas/
│   ├── health/                # Health check
│   ├── consulta-ruc/          # SUNAT
│   ├── sanciones/             # OSCE + TCE
│   ├── scoring/               # Score de riesgo
│   └── certificado/           # Generación + S3
└── layers/
    └── shared/python/utils/   # CORS, cache DynamoDB, validación RUC
```

## Deploy

```bash
# Instalar AWS SAM CLI
brew install aws-sam-cli

# Configurar credenciales AWS
aws configure

# Antes del primer deploy: guardar el token en SSM
aws ssm put-parameter \
  --name /conflictzero/buscaruc_token \
  --value "TU_TOKEN" \
  --type SecureString

# Build y deploy
sam build
sam deploy --guided

# Deploys siguientes
sam build && sam deploy
```

## Variables de entorno en Lambda

Configurar en AWS Console > Lambda > Configuration > Environment Variables:

- `S3_BUCKET`: `conflictzero-certificados-prod`
- `DYNAMODB_TABLE`: `conflictzero-consultas`
- `API_BASE_URL`: URL de API Gateway tras el primer deploy
- `ALLOWED_ORIGIN`: `https://czperu.com`

## IAM Role

`arn:aws:iam::981207387949:role/conflictzero-lambda-role`

El role necesita permisos para: `s3:PutObject`, `s3:GetObject`, `dynamodb:GetItem`, `dynamodb:PutItem`, `ssm:GetParameter`.
