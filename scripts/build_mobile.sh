#!/bin/bash
#
# Conflict Zero - Mobile Build Script
# Fase 2 - Construye APK / iOS con EAS
#
# Uso:
#   ./scripts/build_mobile.sh [android|ios|all]
#

set -e

PLATFORM=${1:-android}
WORKSPACE="/root/.openclaw/workspace/conflict-zero-fase1"
MOBILE_DIR="$WORKSPACE/mobile"

echo "═══════════════════════════════════════════════════"
echo "Conflict Zero - Mobile Build"
echo "═══════════════════════════════════════════════════"
echo "Platform: $PLATFORM"
echo "Time: $(date)"
echo "═══════════════════════════════════════════════════"

# Verificar dependencias
check_deps() {
    echo "🔹 Verificando dependencias..."
    
    if ! command -v node &> /dev/null; then
        echo "❌ Node.js no encontrado. Instalar Node 18+."
        exit 1
    fi
    
    if ! command -v npx &> /dev/null; then
        echo "❌ npx no encontrado."
        exit 1
    fi
    
    echo "✅ Dependencias verificadas"
}

# Instalar dependencias
install_deps() {
    echo "🔹 Instalando dependencias..."
    cd "$MOBILE_DIR"
    
    if [ ! -d "node_modules" ]; then
        npm install
    fi
    
    # Verificar EAS CLI
    if ! npx eas --version &> /dev/null; then
        echo "📦 Instalando EAS CLI..."
        npm install -g eas-cli
    fi
    
    echo "✅ Dependencias instaladas"
}

# Build Android
build_android() {
    echo "🔹 Build Android (APK)..."
    cd "$MOBILE_DIR"
    
    # Configurar variables de entorno
    export EXPO_PUBLIC_API_URL=${EXPO_PUBLIC_API_URL:-"https://api.conflictzero.pe"}
    
    # Build con EAS
    npx eas build \
        --platform android \
        --profile preview \
        --non-interactive \
        --no-wait
    
    echo "✅ Build Android iniciado en EAS"
    echo "   Monitorear en: https://expo.dev/builds"
}

# Build iOS
build_ios() {
    echo "🔹 Build iOS (TestFlight)..."
    cd "$MOBILE_DIR"
    
    export EXPO_PUBLIC_API_URL=${EXPO_PUBLIC_API_URL:-"https://api.conflictzero.pe"}
    
    # Build con EAS
    npx eas build \
        --platform ios \
        --profile preview \
        --non-interactive \
        --no-wait
    
    echo "✅ Build iOS iniciado en EAS"
    echo "   Monitorear en: https://expo.dev/builds"
}

# Validar configuración
validate_config() {
    echo "🔹 Validando configuración..."
    
    # Verificar eas.json
    if [ ! -f "$MOBILE_DIR/eas.json" ]; then
        echo "❌ No se encontró eas.json"
        exit 1
    fi
    
    # Verificar App.tsx
    if [ ! -f "$MOBILE_DIR/App.tsx" ]; then
        echo "❌ No se encontró App.tsx"
        exit 1
    fi
    
    echo "✅ Configuración válida"
}

# Main
main() {
    check_deps
    validate_config
    install_deps
    
    case "$PLATFORM" in
        android)
            build_android
            ;;
        ios)
            build_ios
            ;;
        all)
            build_android
            build_ios
            ;;
        *)
            echo "Uso: $0 [android|ios|all]"
            exit 1
            ;;
    esac
    
    echo ""
    echo "═══════════════════════════════════════════════════"
    echo "✅ Build iniciado exitosamente"
    echo "═══════════════════════════════════════════════════"
    echo ""
    echo "Próximos pasos:"
    echo "1. Monitorear build en https://expo.dev/builds"
    echo "2. Descargar artefacto cuando termine"
    echo "3. Para iOS: Subir a TestFlight con Transporter"
    echo "4. Para Android: Subir APK a Play Console"
    echo ""
}

main
