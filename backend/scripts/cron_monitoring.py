#!/usr/bin/env python3
"""
Script de cron para monitoreo diario de proveedores.
Fase 2 - Conflict Zero

Ejecución:
    python cron_monitoring.py

Configuración en cron:
    0 2 * * * cd /app/backend && python scripts/cron_monitoring.py >> /var/log/monitoring.log 2>&1
"""
import sys
import os
from datetime import datetime

# Añadir el directorio padre al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.core.database import SessionLocal
from app.services.monitoring_service import MonitoringService


def run_daily_monitoring():
    """Ejecuta el monitoreo diario de todos los proveedores."""
    print(f"[{datetime.utcnow().isoformat()}] Iniciando monitoreo diario...")
    
    db = SessionLocal()
    try:
        service = MonitoringService(db)
        result = service.run_daily_check()
        
        print(f"[{datetime.utcnow().isoformat()}] Monitoreo completado:")
        print(f"  - Status: {result['status']}")
        print(f"  - Schedule ID: {result.get('schedule_id')}")
        print(f"  - Total proveedores: {result.get('total_suppliers', 0)}")
        print(f"  - Chequeados: {result.get('checked_suppliers', 0)}")
        print(f"  - Cambios detectados: {result.get('changes_detected', 0)}")
        print(f"  - Alertas generadas: {result.get('alerts_generated', 0)}")
        
        if result['status'] == 'error':
            print(f"  - ERROR: {result.get('error')}")
            sys.exit(1)
            
    except Exception as e:
        print(f"[{datetime.utcnow().isoformat()}] ERROR en monitoreo: {str(e)}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    run_daily_monitoring()
