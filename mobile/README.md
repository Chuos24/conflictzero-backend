# Conflict Zero - Mobile App

Aplicación móvil oficial de Conflict Zero para iOS y Android.

## Tecnologías

- **React Native** con Expo SDK 50
- **TypeScript** 100%
- **Zustand** para estado global
- **React Navigation** (Stack + Bottom Tabs)
- **Expo Secure Store** para almacenamiento seguro
- **Expo Barcode Scanner** para escaneo QR de RUCs
- **Expo Notifications** para push notifications

## Estructura

```
mobile/
├── App.tsx                 # Entry point con navegación
├── package.json            # Dependencias Expo
├── tsconfig.json           # Configuración TypeScript
├── assets/                 # Iconos y splash screens
└── src/
    ├── components/          # Componentes reutilizables
    │   └── index.tsx        # Text, Input, Button
    ├── context/             # Context providers
    │   ├── AuthContext.tsx   # Auth state + SecureStore
    │   └── ThemeContext.tsx  # Dark/light mode
    └── screens/             # Pantallas principales
        ├── LoginScreen.tsx
        ├── VerifyScreen.tsx    # Buscar por RUC
        ├── ScanScreen.tsx      # Escanear QR
        ├── NetworkScreen.tsx   # Mi Red
        ├── AlertsScreen.tsx    # Alertas
        ├── ProfileScreen.tsx   # Perfil
        └── CompanyDetailScreen.tsx
```

## Características

- 🔍 **Verificación RUC** - Buscar empresas por RUC de 11 dígitos
- 📷 **Escaneo QR** - Escanea códigos QR con RUCs integrados
- 👥 **Mi Red** - Lista de proveedores monitoreados
- 🔔 **Alertas** - Notificaciones de cambios en proveedores
- 📊 **Detalle Empresa** - Scores, sanciones, deuda SUNAT
- 🔐 **Auth seguro** - JWT en SecureStore
- 🌙 **Dark mode** - Soporte nativo tema oscuro

## Instalación

```bash
cd mobile
npm install
npx expo start
```

## Build

```bash
# iOS
expo build:ios

# Android
expo build:android

# O con EAS
eas build --platform ios
```

## Roadmap Mobile

- [ ] Push notifications reales
- [ ] Modo offline con cache
- [ ] Biométrico (Face ID / fingerprint)
- [ ] Widgets iOS/Android
- [ ] Wearables support

---

*Conflict Zero © 2026*
