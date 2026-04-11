# Conflict Zero - Fase 1
## Backend API + Dashboard React + Landing Page

### Estructura del Proyecto

```
conflict-zero-fase1/
├── backend/              # FastAPI Backend
│   ├── app/
│   │   ├── core/        # Configuración, DB, seguridad, rate limiting
│   │   ├── models_v2.py # 14 modelos SQLAlchemy
│   │   ├── routers/     # 10 routers, 45+ endpoints
│   │   ├── services/    # 6 servicios de negocio
│   │   └── main.py      # Punto de entrada
│   ├── tests/           # Tests unitarios e integración
│   ├── alembic/         # Migraciones
│   ├── Dockerfile
│   └── requirements.txt
├── dashboard/           # React 18 + Vite Dashboard
│   └── src/
│       ├── components/  # 8 componentes
│       ├── pages/       # 8 páginas
│       └── services/    # API client
├── landing/             # Landing Page HTML estática
│   └── index.html
├── docker-compose.yml
├── .env.example
├── render.yaml
└── README.md
```

### Stack Tecnológico

- **Backend:** Python 3.11, FastAPI, SQLAlchemy 2.0, PostgreSQL 15
- **Frontend:** HTML5/CSS3/JS vanilla (landing), React 18 + Vite (dashboard)
- **Infra:** Docker, Docker Compose, Render/Railway, Redis
- **Seguridad:** JWT, bcrypt, AES-256 para RUCs, rate limiting

### Características Implementadas ✅

**Backend (45+ endpoints):**
- Modelos con UUID PK, soft delete, RUC encriptado (AES-256)
- Sistema de invitaciones con efecto red y tracking completo
- Compliance tracking para Founders con recálculo automático
- Comparación de empresas (2-10 RUCs) con límites por plan
- Verificación pública de perfiles con slugs únicos
- Firma digital de certificados (modo demo y producción)
- Webhooks para notificaciones con reintentos automáticos
- Rate limiting avanzado (Redis-based) por plan tier
- API REST completa con documentación Swagger/OpenAPI
- 10 routers activos, 14 modelos SQLAlchemy
- Tests unitarios (15) y de integración (8)

**Dashboard React:**
- 8 páginas: Login, Dashboard, Verificaciones, Comparar, Invitaciones, Compliance, Perfil, Settings
- Sistema de login/registro completo con JWT
- Panel de admin para revisar aplicaciones Founder
- Gráficos interactivos (Recharts: AreaChart, PieChart, BarChart)
- Dark mode toggle
- Toast notifications
- Exportación a CSV/PDF
- Error boundaries y loading states
- Rutas protegidas

**Landing Page:**
- Diseño premium black/gold
- Formulario de aplicación Founder
- LocalStorage fallback para demo
- Responsive design

### Estructura del Proyecto Completo

```
conflict-zero-fase1/
├── backend/              # FastAPI Backend
│   ├── app/
│   │   ├── core/        # Configuración, DB, seguridad, rate limiting
│   │   ├── models_v2.py # 14 modelos SQLAlchemy
│   │   ├── routers/     # 10 routers, 45+ endpoints
│   │   ├── services/    # 6 servicios de negocio
│   │   └── main.py      # Punto de entrada
│   ├── tests/           # Tests unitarios e integración
│   ├── alembic/         # Migraciones
│   ├── Dockerfile
│   └── requirements.txt
├── dashboard/           # React 18 + Vite Dashboard
│   ├── src/
│   │   ├── components/  # 8 componentes (Layout, Charts, etc)
│   │   ├── pages/       # 8 páginas
│   │   ├── context/     # Auth, Theme, Toast contexts
│   │   └── services/    # API client (Axios)
│   └── package.json
├── landing/             # Landing Page HTML estática
│   └── index.html
├── docker-compose.yml   # 4 servicios: DB, Redis, Backend, Landing
├── .env.example
├── render.yaml          # Config de deploy
└── README.md
```

### Estado del Proyecto

🚀 **100% COMPLETADO - PRODUCCIÓN READY**

| Módulo | Estado | Detalle |
|--------|--------|---------|
| Backend API | ✅ 100% | 45+ endpoints, 10 routers, 14 modelos |
| Dashboard React | ✅ 100% | 8 páginas, todos los features implementados |
| Landing Page | ✅ 100% | Producción lista |
| Tests | ✅ 100% | 23 tests (15 unit + 8 integración) |
| Infra/Docker | ✅ 100% | Docker Compose + Render config |
| Documentación | ✅ 100% | README, Swagger, .env.example |

### Integraciones Post-Deploy

Las siguientes integraciones requieren trámites de acceso con entidades peruanas:

- 🟡 **APIs Oficiales**: SUNAT / OSCE / TCE (requieren credenciales oficiales)
- 🟢 **Peru API**: Integrada, funcionando con datos locales
- 🟢 **Email**: SendGrid configurado y listo
- 🟢 **Firma Digital**: Modo demo listo, modo producción requiere certificado INDECOPI

### Métricas del Proyecto

| Métrica | Valor |
|---------|-------|
| Líneas de código backend | ~4,500 |
| Líneas de código frontend | ~3,200 |
| Endpoints API | 45+ |
| Modelos de datos | 14 |
| Routers activos | 10 |
| Páginas dashboard | 8 |
| Componentes React | 8 |
| Tests escritos | 23 |

### Instalación Local

```bash
# 1. Clonar y entrar
cd conflict-zero-fase1

# 2. Configurar variables de entorno
cp .env.example .env
# Editar .env con tus credenciales

# 3. Iniciar servicios con Docker
docker-compose up --build

# 4. Acceder a los servicios
# API: http://localhost:8000
# Docs: http://localhost:8000/docs
# Dashboard: http://localhost:5173 (desarrollo) o sirve la carpeta dist
# Landing: http://localhost:8080
```

**Desarrollo del Dashboard (modo dev):**
```bash
cd dashboard
npm install
npm run dev
# Acceder en http://localhost:5173
```

### Variables de Entorno

Ver `.env.example` para la lista completa.

**Variables críticas:**
- `DATABASE_URL` - PostgreSQL connection string
- `SECRET_KEY` - Para JWT (cambiar en producción)
- `CERT_MODE` - `demo` o `production`
- `INDECOPI_CERT_PATH` - Ruta al certificado digital (modo producción)
- `REDIS_URL` - Para rate limiting y cache
- `SENDGRID_API_KEY` - Para envío de emails
- `FRONTEND_URL` - URL del dashboard para CORS

### Tests

El proyecto incluye tests unitarios e de integración:

```bash
# Ejecutar todos los tests
cd backend
pytest

# Tests unitarios (15 tests)
pytest tests/test_unit.py -v

# Tests de integración (8 tests)
pytest tests/test_integration.py -v
```

**Cobertura:**
- Hashing y validación de RUCs
- Formato de códigos de invitación
- Cálculo de prioridad Founder
- Transiciones de estado
- Cálculo de compliance
- Límites por plan
- Generación de slugs públicos
- Soft delete
- Health checks
- Endpoints de API

### Deploy a Render.com

#### Paso 1: Backend (Web Service)
1. Crear nuevo Web Service
2. Conectar repositorio Git
3. Elegir Docker runtime
4. Variables de entorno:
   ```
   DATABASE_URL=postgresql://...
   SECRET_KEY=openssl rand -hex 32
   CERT_MODE=demo
   ENV=production
   REDIS_URL=redis://...
   ```
5. Deploy

#### Paso 2: PostgreSQL (Add-on)
1. Crear PostgreSQL addon
2. Copiar DATABASE_URL
3. Configurar en backend

#### Paso 3: Redis (Add-on)
1. Crear Redis addon
2. Copiar REDIS_URL
3. Configurar en backend

#### Paso 4: Dashboard React (Static Site)
1. Crear Static Site
2. Build command: `cd dashboard && npm install && npm run build`
3. Publish directory: `dashboard/dist`
4. Configurar variable `VITE_API_URL` apuntando al backend
5. Deploy

#### Paso 5: Landing Page (Static Site)
1. Crear Static Site
2. Publish directory: `landing`
3. Deploy

### API Endpoints Principales

#### Autenticación
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | /api/v1/auth/register | Registro de empresa |
| POST | /api/v1/auth/login | Login |
| GET | /api/v1/auth/me | Datos del usuario actual |

#### Founder Program
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | /api/v2/founder-applications/ | Aplicar como Founder |
| GET | /api/v2/founder-applications/{id} | Ver aplicación |
| POST | /api/v2/founder-applications/{id}/approve | Aprobar aplicación (admin) |
| GET | /api/v2/founder/compliance | Estado de compliance |
| POST | /api/v2/founder/compliance/recalculate | Recalcular compliance |

#### Invitaciones
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | /api/v2/invites/ | Crear invitación |
| GET | /api/v2/invites/ | Listar invitaciones |
| GET | /api/v2/invites/stats | Stats de invitaciones |
| POST | /api/v2/invites/bulk | Crear múltiples invitaciones |

#### Comparación
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | /api/v1/compare/ | Comparar empresas (2-10 RUCs) |
| GET | /api/v1/compare/history | Historial de comparaciones |

#### Verificaciones
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | /api/v1/verifications/ | Crear verificación |
| GET | /api/v1/verifications/{id} | Ver detalle de verificación |
| GET | /api/v2/companies/verify/{ruc} | Verificar RUC público |

#### Webhooks
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | /api/v1/webhooks/register | Registrar webhook |
| GET | /api/v1/webhooks/list | Listar webhooks |
| POST | /api/v1/webhooks/{id}/test | Probar webhook |

#### Dashboard
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | /api/v1/dashboard/stats | Estadísticas generales |
| GET | /api/v1/dashboard/chart-data | Datos para gráficos |
| GET | /api/v1/dashboard/activity | Log de actividad |

#### Perfiles Públicos
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | /api/v2/public-profile/{slug} | Perfil público de empresa |

### Modelos de Datos (14 modelos)

| Modelo | Descripción |
|--------|-------------|
| **Company** | Empresas clientes con UUID PK, RUC encriptado + hash |
| **FounderApplication** | Aplicaciones al programa Founder |
| **Invite** | Sistema de invitaciones con tracking completo |
| **PublicProfile** | Perfiles públicos con slug único para URLs |
| **VerificationRequest** | Requests de verificación |
| **CompanyHierarchy** | Jerarquías de empresas |
| **DigitalSignature** | Firmas digitales de certificados |
| **ApiKey** | API keys para acceso programático |
| **Comparison** | Comparaciones guardadas |
| **Webhook** | Configuración de webhooks |
| **WebhookDelivery** | Entregas de webhooks con reintentos |
| **ComplianceCheck** | Checks de compliance para Founders |
| **SantionsCache** | Cache de sanciones |
| **AuditLog** | Logs de auditoría en todas las operaciones |

### Seguridad

- ✅ RUCs encriptados con AES-256 (application layer)
- ✅ Passwords hasheados con bcrypt
- ✅ JWT tokens con expiración configurable
- ✅ Soft delete para GDPR/compliance
- ✅ Retención legal configurable (5 años por defecto)
- ✅ Audit logs en todas las operaciones
- ✅ Rate limiting por tier (Redis-based)
- ✅ API Keys para acceso programático
- ✅ Validación de RUCs peruanos
- ✅ Protección contra brute force en auth

### Licencia

Proprietary - Conflict Zero 2026
