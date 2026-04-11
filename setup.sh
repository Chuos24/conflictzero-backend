#!/bin/bash
# Conflict Zero - Setup Script
# Automatiza la instalación local del proyecto

set -e

echo "🚀 Conflict Zero - Setup Local"
echo "================================"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check dependencies
check_dependency() {
    if ! command -v $1 &> /dev/null; then
        echo -e "${RED}❌ $1 no está instalado${NC}"
        return 1
    else
        echo -e "${GREEN}✅ $1 instalado${NC}"
        return 0
    fi
}

echo ""
echo "📋 Verificando dependencias..."
check_dependency docker || { echo "Instalar Docker: https://docs.docker.com/get-docker/"; exit 1; }
check_dependency docker-compose || { echo "Instalar Docker Compose"; exit 1; }

# Check if .env exists
if [ ! -f .env ]; then
    echo ""
    echo -e "${YELLOW}⚠️  Archivo .env no encontrado${NC}"
    echo "📝 Creando .env desde template..."
    cp .env.example .env
    echo -e "${YELLOW}⚠️  Edita .env con tus credenciales antes de continuar${NC}"
fi

# Create necessary directories
echo ""
echo "📁 Creando directorios..."
mkdir -p backend/certs
mkdir -p logs

# Build and start
echo ""
echo "🔨 Construyendo contenedores..."
docker-compose build

echo ""
echo "🚀 Iniciando servicios..."
docker-compose up -d db redis

echo ""
echo "⏳ Esperando que PostgreSQL esté listo..."
sleep 5

# Run migrations (if we had alembic)
# echo "🔄 Ejecutando migraciones..."
# docker-compose exec backend alembic upgrade head

echo ""
echo "🚀 Iniciando backend..."
docker-compose up -d backend landing

echo ""
echo -e "${GREEN}✅ Setup completado!${NC}"
echo ""
echo "📍 Servicios disponibles:"
echo "   • API:        http://localhost:8000"
echo "   • Docs:       http://localhost:8000/docs"
echo "   • Landing:    http://localhost:5500"
echo "   • PostgreSQL: localhost:5432"
echo "   • Redis:      localhost:6379"
echo ""
echo "📋 Comandos útiles:"
echo "   docker-compose logs -f backend    # Ver logs del backend"
echo "   docker-compose exec backend bash  # Shell en el contenedor"
echo "   docker-compose down               # Detener todo"
echo ""
echo -e "${YELLOW}⚠️  Nota: Para el dashboard React, ejecuta:${NC}"
echo "   cd dashboard && npm install && npm run dev"
echo ""
