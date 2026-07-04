# Contribuir a ConflictZero Backend

## Flujo de trabajo

1. Crea tu rama desde `main`:
   ```bash
   git checkout -b feature/nombre-descriptivo
   ```
2. Haz tus cambios y commitea:
   ```bash
   git commit -m "feat: descripción corta del cambio"
   ```
3. Abre un Pull Request hacia `main`
4. El deploy a producción se hace **automáticamente** al mergear a `main` via GitHub Actions

## Convención de branches

| Prefijo | Uso |
|---|---|
| `feature/` | Nueva funcionalidad |
| `fix/` | Corrección de bug |
| `chore/` | Mantenimiento, deps, infra |
| `docs/` | Solo documentación |

## Convención de commits

Usar prefijos semánticos:
- `feat:` nueva funcionalidad
- `fix:` corrección de bug
- `chore:` tarea de mantenimiento
- `docs:` documentación
- `ci:` cambios en CI/CD

## Correr localmente

### Requisitos
- Python 3.11
- AWS SAM CLI
- AWS CLI configurado con credenciales de dev
- Docker (para `sam build --use-container`)

### Pasos

```bash
# Instalar dependencias del layer compartido
pip install -r layers/shared/requirements.txt -t layers/shared/python/

# Build
sam build

# Levantar API local
sam local start-api --env-vars env.json
```

### Variables de entorno locales

Crea un archivo `env.json` en la raíz (no commitear):

```json
{
  "Globals": {
    "BUSCARUC_TOKEN": "tu-token-aqui",
    "DYNAMODB_TABLE": "conflictzero-consultas",
    "S3_BUCKET": "conflictzero-documentos-dev",
    "ALLOWED_ORIGIN": "http://localhost:3000"
  }
}
```

## Secrets de GitHub Actions requeridos

Configurar en `Settings > Secrets and variables > Actions`:

| Secret | Descripción |
|---|---|
| `AWS_ACCESS_KEY_ID` | IAM key con permisos de deploy |
| `AWS_SECRET_ACCESS_KEY` | IAM secret |
| `SAM_DEPLOY_BUCKET` | Bucket S3 para artefactos SAM |
| `BUSCARUC_TOKEN` | Token de la API BuscarRUC |

## Estructura del proyecto

```
conflictzero-backend/
├── template.yaml          # SAM template principal
├── lambdas/
│   ├── health/            # GET /health
│   ├── homologacion/      # Motor principal de homologación
│   ├── consulta-ruc/      # GET /ruc/{ruc} — datos SUNAT
│   ├── sanciones/         # GET /sanciones/{ruc} — OSCE/TCE
│   ├── scoring/           # POST /scoring — cálculo de score
│   └── certificado/       # GET /certificado/{ruc} — PDF
├── layers/
│   └── shared/python/utils/  # Utilidades compartidas
├── ROADMAP.md
├── STATUS.md
└── CONTRIBUTING.md
```
