# Conflict Zero Dashboard

Dashboard React para clientes del programa Conflict Zero.

## Stack Tecnológico

- **Framework:** React 18 + Vite 5
- **Routing:** React Router DOM v6
- **HTTP Client:** Axios
- **Charts:** Recharts
- **Icons:** Lucide React
- **Date Utils:** date-fns

## Estructura

```
dashboard/
├── src/
│   ├── components/     # Componentes reutilizables
│   │   ├── Layout.jsx       # Layout principal con sidebar
│   │   ├── Layout.css       # Estilos del layout
│   │   └── ProtectedRoute.jsx  # Guard de rutas protegidas
│   ├── pages/         # Páginas principales
│   │   ├── Login.jsx        # Login de usuarios
│   │   ├── Dashboard.jsx    # Dashboard principal
│   │   ├── Verifications.jsx # Historial de verificaciones
│   │   ├── Compare.jsx      # Comparador de empresas
│   │   ├── Invites.jsx      # Sistema de invitaciones
│   │   ├── Compliance.jsx   # Tracking de compliance
│   │   ├── Profile.jsx      # Perfil de empresa
│   │   └── Settings.jsx     # Configuración
│   ├── services/      # API calls
│   │   └── api.js           # Configuración de Axios + endpoints
│   ├── context/       # React context
│   │   └── AuthContext.jsx  # Gestión de autenticación
│   ├── styles/        # CSS global
│   │   └── global.css       # Estilos globales
│   ├── App.jsx        # App component con rutas
│   └── main.jsx       # Entry point
├── index.html         # HTML template
├── vite.config.js     # Configuración de Vite
├── package.json       # Dependencias
└── .env.example       # Variables de entorno template
```

## Instalación

```bash
cd dashboard

# Instalar dependencias
npm install

# Copiar variables de entorno
cp .env.example .env
# Editar .env con la URL del API

# Iniciar servidor de desarrollo
npm run dev
```

El dashboard estará disponible en `http://localhost:3000`

## Build para producción

```bash
npm run build
```

El contenido de `dist/` se sirve como estático.

## Variables de Entorno

| Variable | Descripción | Default |
|----------|-------------|---------|
| `VITE_API_URL` | URL base del API backend | `http://localhost:8000` |
| `VITE_APP_NAME` | Nombre de la aplicación | `Conflict Zero` |
| `VITE_ENABLE_ANALYTICS` | Habilitar analytics | `false` |

## Scripts Disponibles

```bash
npm run dev      # Servidor de desarrollo
npm run build    # Build para producción
npm run preview  # Preview del build
```

## Proxy en Desarrollo

El `vite.config.js` está configurado para proxyear peticiones `/api` al backend:

```javascript
proxy: {
  '/api': {
    target: 'http://localhost:8000',
    changeOrigin: true
  }
}
```

Esto permite usar rutas relativas en desarrollo:
```javascript
api.get('/api/v1/auth/me')  // Va a http://localhost:8000/api/v1/auth/me
```

## Autenticación

El sistema usa JWT tokens:
1. Login guarda el token en `localStorage` como `cz_token`
2. El contexto `AuthContext` maneja el estado global
3. Axios intercepta requests para agregar el header `Authorization`
4. En 401, redirige automáticamente a login

## API Services

Todos los endpoints están en `src/services/api.js`:

```javascript
// Auth
authAPI.login(email, password)
authAPI.register(data)
authAPI.me()

// Verifications
verificationAPI.verify(ruc)
verificationAPI.history()

// Compare
compareAPI.compare(['20100123091', '20100123092'])

// Invites
inviteAPI.list()
inviteAPI.create({ email, company_name })

// Compliance
complianceAPI.status()
complianceAPI.network()

// Company
companyAPI.profile()
companyAPI.update(data)
```

## Rutas

| Ruta | Descripción | Protegida |
|------|-------------|-----------|
| `/login` | Login de usuarios | No |
| `/dashboard` | Dashboard principal | Sí |
| `/verifications` | Historial de verificaciones | Sí |
| `/compare` | Comparador de empresas | Sí |
| `/invites` | Sistema de invitaciones | Sí |
| `/compliance` | Tracking de compliance | Sí |
| `/profile` | Perfil de empresa | Sí |
| `/settings` | Configuración | Sí |

## Estilos

- CSS modules para componentes individuales
- `global.css` para estilos base y variables
- Sistema de diseño black/gold de Conflict Zero

## TODO

- [ ] Implementar gráficos con Recharts en Dashboard
- [ ] Agregar loading states globales
- [ ] Implementar error boundaries
- [ ] Dark mode toggle
- [ ] Notificaciones toast
- [ ] Exportar reportes (PDF/CSV)
