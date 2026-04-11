# Conflict Zero - Backend API

Backend de la plataforma Conflict Zero - Sistema de verificación de riesgo para constructoras peruanas.

## 🚀 Tecnologías

- **FastAPI** - Framework web moderno y rápido
- **SQLAlchemy 2.0** - ORM para PostgreSQL
- **Pydantic** - Validación de datos y settings
- **JWT** - Autenticación con tokens
- **Alembic** - Migraciones de base de datos
- **pytest** - Testing
- **Docker** - Containerización

## 📁 Estructura

```
backend/
├── app/
│   ├── core/           # Configuración, seguridad, database
│   ├── models.py       # Modelos SQLAlchemy v1
│   ├── models_v2.py    # Modelos SQLAlchemy v2 (UUID, RUC encriptado)
│   ├── schemas.py      # Pydantic schemas
│   ├── main.py         # Aplicación FastAPI principal
│   └── routers/        # Endpoints API
│       ├── auth.py
│       ├── company.py
│       ├── compare.py
│       ├── verifications.py
│       ├── invites.py
│       ├── founder_applications.py
│       └── founder_compliance.py
│   └── services/       # Lógica de negocio
│       ├── data_collection.py
│       ├── scoring_service.py
│       ├── digital_signature_v2.py
│       ├── compare_service.py
│       └── email_service.py
├── tests/              # Tests unitarios e integración
├── scripts/            # Scripts de utilidad
├── Dockerfile
├── requirements.txt
└── pytest.ini
```

## 🛠️ Setup Local

### 1. Clonar y entrar al directorio

```bash
cd conflict-zero-fase1/backend
```

### 2. Crear entorno virtual

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# o
venv\Scripts\activate     # Windows
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

```bash
cp .env.example .env
# Editar .env con tus configuraciones
```

**Variables requeridas:**

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/conflict_zero

# Seguridad
SECRET_KEY=your-secret-key-here
ENCRYPTION_KEY=your-32-byte-encryption-key

# APIs externas (opcional para demo)
SUNAT_API_KEY=
OSCE_API_KEY=
TCE_API_KEY=
FACTALIZA_API_KEY=

# Email (opcional)
SENDGRID_API_KEY=

# Modo
ENV=development
CERT_MODE=demo  # demo o production
```

### 5. Inicializar base de datos

```bash
# Crear tablas
python -c "from app.core.database import init_db; init_db()"

# O con Alembic
alembic upgrade head
```

### 6. Ejecutar servidor

```bash
# Desarrollo con hot reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Producción
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 🐳 Docker

### Desarrollo local con Docker Compose

```bash
cd conflict-zero-fase1
docker-compose up -d
```

Esto levanta:
- Backend API en http://localhost:8000
- PostgreSQL en localhost:5432
- Dashboard en http://localhost:3000

### Construir imagen manualmente

```bash
docker build -t conflict-zero-backend ./backend
```

## 🧪 Testing

```bash
# Ejecutar todos los tests
cd backend
pytest

# Con cobertura
pytest --cov=app --cov-report=html

# Tests específicos
pytest tests/test_auth.py -v
```

## 📚 API Documentation

Una vez ejecutando el servidor:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## 🔐 Seguridad

### Encriptación de RUC

Los RUCs se almacenan encriptados con AES-256. El hash SHA-256 se usa para búsquedas sin revelar el RUC.

### Rate Limiting

- **Por IP**: 100 requests/minuto
- **Por plan mensual**: Según tier (bronze: 1000, silver: 5000, gold: 100000, founder: ilimitado)

### Autenticación

- JWT tokens con expiración de 24h
- Refresh tokens de 7 días
- API keys por empresa con rate limiting individual

## 🔄 Endpoints Principales

### Autenticación (`/api/v1/auth`)
- `POST /register` - Registrar empresa
- `POST /login` - Iniciar sesión
- `GET /me` - Perfil actual

### Verificaciones (`/api/v1/verify`)
- `POST /` - Verificar RUC
- `GET /history` - Historial
- `GET /{id}/certificate` - Descargar certificado

### Empresa (`/api/v1/company`)
- `GET /profile` - Perfil
- `PATCH /profile` - Actualizar perfil
- `GET /stats` - Estadísticas
- `GET/POST /api-keys` - Gestión de API keys

### Comparación (`/api/v1/compare`)
- `POST /` - Comparar múltiples RUCs (2-10)

### Fundadores (`/api/v2`)
- `POST /founder-applications` - Aplicar como founder
- `GET /founder/compliance` - Estado de compliance
- `POST /invites` - Crear invitaciones

## 📝 Variables de Plan

| Plan | Max Queries/mes | Comparaciones/día | Max por comparación |
|------|----------------|-------------------|---------------------|
| bronze | 1,000 | 5 | 3 |
| silver | 5,000 | 20 | 5 |
| gold | 100,000 | 100 | 10 |
| founder | Ilimitado | Ilimitado | 10 |

## 🚀 Deploy

### Render.com

1. Conectar repositorio a Render
2. Configurar Blueprint desde `render.yaml`
3. Agregar variables de entorno en dashboard de Render

### Variables de entorno en producción

```env
ENV=production
CERT_MODE=production
DATABASE_URL=${{ secrets.DATABASE_URL }}
SECRET_KEY=${{ secrets.SECRET_KEY }}
ENCRYPTION_KEY=${{ secrets.ENCRYPTION_KEY }}
```

## 📄 Licencia

Propietario - Conflict Zero Perú
