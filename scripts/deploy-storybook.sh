#!/usr/bin/env bash
# Script para hacer build y deploy local de Storybook
# Uso: ./scripts/deploy-storybook.sh [target]
# Targets: local (default), gh-pages, netlify

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DASHBOARD_DIR="$PROJECT_ROOT/dashboard"
TARGET="${1:-local}"

echo "📚 Conflict Zero - Storybook Deploy"
echo "===================================="
echo "Target: $TARGET"
echo ""

# Verificar que estamos en el directorio correcto
if [ ! -f "$DASHBOARD_DIR/package.json" ]; then
    echo "❌ Error: No se encontró dashboard/package.json"
    echo "Ejecuta este script desde la raíz del proyecto"
    exit 1
fi

cd "$DASHBOARD_DIR"

# Verificar Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Error: Node.js no está instalado"
    exit 1
fi

NODE_VERSION=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 18 ]; then
    echo "❌ Error: Se requiere Node.js 18+. Versión actual: $(node --version)"
    exit 1
fi

echo "✅ Node.js $(node --version)"

# Instalar dependencias si es necesario
if [ ! -d "node_modules" ] || [ ! -d "node_modules/@storybook" ]; then
    echo "📦 Instalando dependencias..."
    npm ci
fi

# Build de Storybook
echo ""
echo "🔨 Building Storybook..."
npm run build-storybook

if [ ! -d "storybook-static" ]; then
    echo "❌ Error: El build de Storybook falló"
    exit 1
fi

echo "✅ Storybook build exitoso"
echo "   Output: $DASHBOARD_DIR/storybook-static"
echo "   Size: $(du -sh storybook-static | cut -f1)"

# Deploy según target
case "$TARGET" in
    local)
        echo ""
        echo "🚀 Iniciando servidor local..."
        echo "   URL: http://localhost:6006"
        echo ""
        npx serve storybook-static -l 6006
        ;;
    
    gh-pages)
        echo ""
        echo "🚀 Deployando a GitHub Pages..."
        
        if ! command -v gh &> /dev/null; then
            echo "❌ Error: GitHub CLI (gh) no está instalado"
            echo "   Instálalo desde: https://cli.github.com/"
            exit 1
        fi
        
        # Verificar autenticación
        if ! gh auth status &> /dev/null; then
            echo "❌ Error: No estás autenticado con GitHub CLI"
            echo "   Ejecuta: gh auth login"
            exit 1
        fi
        
        # Crear carpeta temporal para gh-pages
        TEMP_DIR=$(mktemp -d)
        cp -r storybook-static/* "$TEMP_DIR/"
        
        # Deploy con gh pages
        cd "$TEMP_DIR"
        git init
        git add .
        git commit -m "Deploy Storybook $(date '+%Y-%m-%d %H:%M:%S')"
        
        REPO_URL=$(gh repo view --json url -q '.url' 2>/dev/null || echo "")
        if [ -z "$REPO_URL" ]; then
            echo "❌ Error: No se pudo obtener la URL del repositorio"
            rm -rf "$TEMP_DIR"
            exit 1
        fi
        
        git push "$REPO_URL.git" HEAD:gh-pages --force
        rm -rf "$TEMP_DIR"
        
        echo "✅ Storybook deployado a GitHub Pages"
        echo "   URL: $REPO_URL/tree/gh-pages"
        ;;
    
    netlify)
        echo ""
        echo "🚀 Deployando a Netlify..."
        
        if ! command -v netlify &> /dev/null; then
            echo "❌ Error: Netlify CLI no está instalado"
            echo "   Instálalo con: npm install -g netlify-cli"
            exit 1
        fi
        
        if [ -z "$NETLIFY_SITE_ID" ]; then
            echo "❌ Error: Variable NETLIFY_SITE_ID no está configurada"
            echo "   Configúrala en tu .env o exporta: export NETLIFY_SITE_ID=xxx"
            exit 1
        fi
        
        netlify deploy --dir=storybook-static --prod --site="$NETLIFY_SITE_ID"
        echo "✅ Storybook deployado a Netlify"
        ;;
    
    *)
        echo "❌ Target no reconocido: $TARGET"
        echo ""
        echo "Uso: ./scripts/deploy-storybook.sh [target]"
        echo ""
        echo "Targets disponibles:"
        echo "  local     - Inicia servidor local (default)"
        echo "  gh-pages  - Deploya a GitHub Pages"
        echo "  netlify   - Deploya a Netlify"
        exit 1
        ;;
esac
