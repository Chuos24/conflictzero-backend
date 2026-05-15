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
from datetime import datetime, timezone

# Añadir el directorio padre al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.core.database import SessionLocal
from app.services.monitoring_service import MonitoringService
from app.services.push_notifications import push_service
from app.models import Company


def run_daily_monitoring():
    """Ejecuta el monitoreo diario de todos los proveedores."""
    print(f"[{datetime.now(timezone.utc).isoformat()}] Iniciando monitoreo diario...")
    
    db = SessionLocal()
    try:
        service = MonitoringService(db)
        result = service.run_daily_check()
        
        print(f"[{datetime.now(timezone.utc).isoformat()}] Monitoreo completado:")
        print(f"  - Status: {result['status']}")
        print(f"  - Schedule ID: {result.get('schedule_id')}")
        print(f"  - Total proveedores: {result.get('total_suppliers', 0)}")
        print(f"  - Chequeados: {result.get('checked_suppliers', 0)}")
        print(f"  - Cambios detectados: {result.get('changes_detected', 0)}")
        print(f"  - Alertas generadas: {result.get('alerts_generated', 0)}")
        
        # Enviar push notifications para alertas críticas y altas
        if result.get('alerts_generated', 0) > 0:
            print(f"[{datetime.now(timezone.utc).isoformat()}] Enviando push notifications...")
            send_alert_push_notifications(db, result)
        
        if result['status'] == 'error':
            print(f"  - ERROR: {result.get('error')}")
            sys.exit(1)
            
    except Exception as e:
        print(f"[{datetime.now(timezone.utc).isoformat()}] ERROR en monitoreo: {str(e)}")
        sys.exit(1)
    finally:
        db.close()


async def send_alert_push_notifications(db, result):
    """Envía push notifications para alertas detectadas."""
    # Obtener empresas con alertas
    # Nota: Esto es un ejemplo, la implementación real dependería de cómo
    # se almacenan las alertas en la base de datos
    
    companies_with_alerts = db.query(Company).filter(
        Company.push_enabled == True,
        Company.push_tokens != []
    ).all()
    
    sent_count = 0
    for company in companies_with_alerts:
        if company.push_tokens:
            try:
                await push_service.send_daily_summary(
                    push_tokens=company.push_tokens,
                    alerts_count=result.get('changes_detected', 0),
                    changes_count=result.get('alerts_generated', 0)
                )
                sent_count += 1
            except Exception as e:
                print(f"  - Error enviando push a {company.ruc}: {e}")
    
    print(f"  - Push notifications enviadas: {sent_count}")


if __name__ == "__main__":
    run_daily_monitoring()
