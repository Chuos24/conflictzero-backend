# Conflict Zero - Fase 1

Sistema de verificación de riesgo de proveedores y contrapartes contractuales para empresas peruanas.

## Estructura del Proyecto

```
conflict-zero-fase1/
├── backend/           # FastAPI Backend (Python 3.11)
├── dashboard/         # React 18 + Vite Frontend
├── landing/           # HTML Landing Page
├── docs/              # Documentación
└── docker-compose.yml # Infraestructura local
```

## Tech Stack

### Backend
- **Python 3.11** + FastAPI
- **SQLAlchemy 2.0** + PostgreSQL 15
- **Redis 7** para cache
- **JWT** para autenticación
- **Pydantic v2** para validación

### Frontend
- **React 18** + Vite 5
- **React Router DOM v6**
- **Recharts** para gráficos
- **Axios** para API calls

## Inicio Rápido

### Requisitos
- Docker + Docker Compose
- Node.js 18+ (para desarrollo local)
- Python 3.11+ (para desarrollo local)

### Levantar todo el stack

```bash
cd conflict-zero-fase1
docker-compose up -d
```

Servicios disponibles:
- **Backend API**: http://localhost:8000
- **Dashboard**: http://localhost:5173
- **Landing**: http://localhost:3000 (si está configurada)
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379
- **API Docs**: http://localhost:8000/docs

### Comandos útiles

```bash
# Ver logs
docker-compose logs -f backend

# Reconstruir después de cambios
docker-compose up -d --build

# Ejecutar tests
docker-compose exec backend pytest

# Acceder a la base de datos
docker-compose exec db psql -U postgres -d conflict_zero

# Acceder a Redis
docker-compose exec redis redis-cli
```

## Variables de Entorno

### Backend (.env)
```
DATABASE_URL=postgresql://user:pass@host:5432/db
REDIS_URL=redis://host:6379/0
SECRET_KEY=your-secret-key
ENCRYPTION_KEY=your-32-char-encryption-key
SENDGRID_API_KEY=optional
ENVIRONMENT=production
```

### Dashboard (.env)
```
VITE_API_URL=https://api.conflictzero.com
```

## Características Principales

### Fase 1 - MVP
- ✅ Verificación de RUC (SUNAT/OSCE/TCE)
- ✅ Score de riesgo 0-100
- ✅ Certificados digitales con QR
- ✅ Sistema de autenticación JWT
- ✅ Comparación de hasta 10 RUCs
- ✅ Invitaciones y red de proveedores
- ✅ Dashboard con métricas
- ✅ Dark mode

### Roadmap Fase 2
- Monitoreo continuo de proveedores
- Alertas automáticas
- API pública
- Integración con ERPs

## Licencia

Copyright © 2026 Conflict Zero. Todos los derechos reservados.
