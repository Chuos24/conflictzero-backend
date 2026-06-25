#!/usr/bin/env python3
"""
Cron job para limpieza de datos expirados según políticas de retención.
Ejecutar diariamente via cron: 0 2 * * * python scripts/cron_data_cleanup.py
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.gdpr import GDPRComplianceService


def run_cleanup():
    """Ejecuta limpieza de datos expirados."""
    print(f"🧹 Iniciando limpieza de datos expirados - {datetime.now(timezone.utc).isoformat()}")
    
    # Create DB session
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        start_time = datetime.now(timezone.utc)
        
        # Run cleanup
        results = GDPRComplianceService.cleanup_expired_data(db, dry_run=False)
        deleted_count = sum(results.values())
        
        duration = datetime.now(timezone.utc) - start_time
        
        if deleted_count > 0:
            print(f"✅ Limpieza completada: {deleted_count} registros eliminados")
            for category, count in results.items():
                if count > 0:
                    print(f"   - {category}: {count}")
        else:
            print("✅ Limpieza completada: no hay registros expirados")
            
        # Log cleanup run
        print(f"⏱️  Duración: {duration.total_seconds():.2f}s")
        
    except Exception as e:
        print(f"❌ Error durante limpieza: {e}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    run_cleanup()
