# ConflictZero Backend v2.0.0

API de consulta de riesgo de proveedores para el mercado peruano.

## Fuentes de datos

| Fuente | Endpoint base | Descripción |
|--------|--------------|-------------|
| SUNAT | `/sunat/ruc/:ruc` | Estado tributario |
| OSCE | `/osce/inhabilitados` | Inhabilitados en contrataciones del Estado |
| TCE | `/tce/inhabilitados` | Tribunal de Contrataciones |
| RNP | `/rnp/inhabilitados` | Registro Nacional de Proveedores |
| SUNAFIL | `/sunafil/sanciones` | Sanciones laborales |

## Consulta completa

```
GET /consulta-completa/:ruc
```

Devuelve score de riesgo (0-100), nivel (`BAJO / MEDIO / ALTO / CRÍTICO`) y todas las sanciones activas.

## Setup local

```bash
cp .env.example .env
# Editar .env con tus API keys
npm install
npm run dev
```

## Variables de entorno

Ver `.env.example` para la lista completa.

## Deploy (Render)

- Build Command: `npm install`
- Start Command: `npm start`
- Node version: 18+
