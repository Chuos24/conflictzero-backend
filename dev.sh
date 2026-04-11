#!/bin/bash
# Conflict Zero - Comandos de desarrollo

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

case "$1" in
    "start")
        echo -e "${GREEN}🚀 Iniciando todos los servicios...${NC}"
        docker-compose up -d
        echo -e "${GREEN}✅ Servicios iniciados${NC}"
        echo "   API:     http://localhost:8000"
        echo "   Landing: http://localhost:5500"
        ;;
    "stop")
        echo -e "${YELLOW}🛑 Deteniendo servicios...${NC}"
        docker-compose down
        ;;
    "restart")
        echo -e "${YELLOW}🔄 Reiniciando backend...${NC}"
        docker-compose restart backend
        ;;
    "logs")
        echo -e "${BLUE}📋 Logs del backend:${NC}"
        docker-compose logs -f backend
        ;;
    "shell")
        echo -e "${BLUE}🐚 Accediendo al shell del backend...${NC}"
        docker-compose exec backend bash
        ;;
    "db")
        echo -e "${BLUE}🐘 Accediendo a PostgreSQL...${NC}"
        docker-compose exec db psql -U cz_user -d conflict_zero
        ;;
    "test")
        echo -e "${BLUE}🧪 Ejecutando tests...${NC}"
        docker-compose exec backend pytest -v
        ;;
    "seed")
        echo -e "${YELLOW}🌱 Ejecutando seed de datos...${NC}"
        docker-compose exec backend python -m scripts.seed_db
        ;;
    "dashboard")
        echo -e "${GREEN}⚛️  Iniciando dashboard de desarrollo...${NC}"
        cd dashboard && npm run dev
        ;;
    "build-dashboard")
        echo -e "${YELLOW}🔨 Build del dashboard...${NC}"
        cd dashboard && npm run build
        ;;
    "clean")
        echo -e "${RED}🧹 Limpiando contenedores y volúmenes...${NC}"
        docker-compose down -v
        docker system prune -f
        ;;
    "status")
        echo -e "${BLUE}📊 Estado de los servicios:${NC}"
        docker-compose ps
        echo ""
        echo -e "${BLUE}🌐 Health Check:${NC}"
        curl -s http://localhost:8000/health | jq . || curl -s http://localhost:8000/health
        ;;
    *)
        echo -e "${BLUE}Conflict Zero - Comandos de desarrollo${NC}"
        echo ""
        echo "Uso: ./dev.sh [comando]"
        echo ""
        echo "Comandos:"
        echo "  start           Iniciar todos los servicios"
        echo "  stop            Detener todos los servicios"
        echo "  restart         Reiniciar backend"
        echo "  logs            Ver logs del backend"
        echo "  shell           Shell en el contenedor backend"
        echo "  db              Acceder a PostgreSQL"
        echo "  test            Ejecutar tests"
        echo "  seed            Ejecutar seed de datos"
        echo "  dashboard       Iniciar dashboard en modo dev"
        echo "  build-dashboard Build del dashboard"
        echo "  clean           Limpiar todo (⚠️  borra datos)"
        echo "  status          Ver estado de servicios"
        echo ""
        ;;
esac
