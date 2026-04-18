#!/usr/bin/env python3
"""
Conflict Zero - Cron Job: Re-verificación diaria de proveedores (Mi Red)
Ejecutar: python -m scripts.cron_daily_network_check
O: cd /app && python scripts/cron_daily_network_check.py

Este script:
1. Obtiene todos los proveedores activos en redes
2. Re-verifica cada proveedor contra SUNAT/OSCE/TCE
3. Compara con el snapshot anterior
4. Genera alertas si hay cambios
5. Envía notificaciones por email
"""

import os
import sys
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import uuid

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError

# Import models
from app.models_v2 import Company, hash_ruc
from app.models_network import SupplierNetwork, SupplierAlert, CompanySnapshot
from app.core.security import decrypt_ruc

# Database connection
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://user:pass@localhost/conflict_zero')
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class NetworkReverificationService:
    """Servicio de re-verificación diaria de proveedores."""
    
    def __init__(self, db: Session):
        self.db = db
        self.alerts_created = 0
        self.suppliers_checked = 0
        self.errors = []
    
    async def run_daily_check(self):
        """Ejecuta el proceso completo de re-verificación."""
        logger.info("🚀 Iniciando re-verificación diaria de proveedores")
        start_time = datetime.utcnow()
        
        try:
            # Obtener proveedores activos que necesitan verificación
            suppliers = self._get_suppliers_to_check()
            logger.info(f"📊 {len(suppliers)} proveedores pendientes de verificación")
            
            for supplier in suppliers:
                try:
                    await self._check_supplier(supplier)
                    self.suppliers_checked += 1
                except Exception as e:
                    logger.error(f"❌ Error verificando proveedor {supplier.id}: {e}")
                    self.errors.append({
                        'supplier_id': str(supplier.id),
                        'error': str(e)
                    })
            
            # Commit de todas las transacciones
            self.db.commit()
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            logger.info(f"✅ Re-verificación completada en {duration:.2f}s")
            logger.info(f"   - Proveedores verificados: {self.suppliers_checked}")
            logger.info(f"   - Alertas creadas: {self.alerts_created}")
            logger.info(f"   - Errores: {len(self.errors)}")
            
            return {
                'success': True,
                'suppliers_checked': self.suppliers_checked,
                'alerts_created': self.alerts_created,
                'errors': len(self.errors),
                'duration_seconds': duration
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Error fatal en re-verificación: {e}")
            return {
                'success': False,
                'error': str(e),
                'suppliers_checked': self.suppliers_checked,
                'alerts_created': self.alerts_created
            }
    
    def _get_suppliers_to_check(self) -> List[SupplierNetwork]:
        """
        Obtiene proveedores que necesitan verificación.
        Criterios:
        - Activo y no eliminado
        - Nunca verificado O última verificación > 24 horas
        """
        twenty_four_hours_ago = datetime.utcnow() - timedelta(hours=24)
        
        return self.db.query(SupplierNetwork).filter(
            SupplierNetwork.is_active == True,
            SupplierNetwork.deleted_at.is_(None),
            # Nunca verificado o verificado hace > 24h
            (
                (SupplierNetwork.last_verified_at.is_(None)) |
                (SupplierNetwork.last_verified_at < twenty_four_hours_ago)
            )
        ).all()
    
    async def _check_supplier(self, supplier: SupplierNetwork):
        """Verifica un proveedor y genera alertas si hay cambios."""
        # Obtener RUC del proveedor (necesitamos desencriptar)
        try:
            ruc = decrypt_ruc(supplier.supplier_ruc_encrypted)
        except Exception as e:
            logger.warning(f"⚠️ No se pudo desencriptar RUC para {supplier.id}: {e}")
            ruc = None
        
        if not ruc:
            logger.warning(f"⚠️ RUC no disponible para proveedor {supplier.id}")
            return
        
        # Realizar verificación (mock por ahora, en prod integrar con services)
        current_data = await self._fetch_supplier_data(ruc)
        
        if not current_data:
            logger.warning(f"⚠️ No se pudo obtener datos para RUC {ruc}")
            return
        
        # Crear nuevo snapshot
        new_snapshot = CompanySnapshot(
            ruc_hash=hash_ruc(ruc),
            company_name=current_data.get('company_name'),
            score=current_data.get('score'),
            risk_level=current_data.get('risk_level'),
            sunat_debt=current_data.get('sunat_debt', 0),
            sunat_tax_status=current_data.get('sunat_tax_status'),
            sunat_contributor_status=current_data.get('sunat_contributor_status'),
            osce_sanctions_count=current_data.get('osce_sanctions_count', 0),
            osce_sanctions_details=current_data.get('osce_sanctions_details', []),
            tce_sanctions_count=current_data.get('tce_sanctions_count', 0),
            tce_sanctions_details=current_data.get('tce_sanctions_details', []),
            full_data=current_data,
            monitoring_company_id=supplier.company_id,
            expires_at=datetime.utcnow() + timedelta(hours=24)
        )
        
        self.db.add(new_snapshot)
        self.db.flush()  # Para obtener el ID
        
        # Actualizar referencia al snapshot en el supplier
        supplier.last_snapshot_id = new_snapshot.id
        supplier.last_verified_at = datetime.utcnow()
        
        # Comparar con snapshot anterior si existe
        if supplier.last_snapshot_id:
            old_snapshot = self.db.query(CompanySnapshot).filter(
                CompanySnapshot.id == supplier.last_snapshot_id
            ).first()
            
            if old_snapshot:
                await self._detect_changes_and_create_alerts(
                    supplier, old_snapshot, new_snapshot
                )
    
    async def _fetch_supplier_data(self, ruc: str) -> Optional[Dict]:
        """
        Obtiene datos actualizados del proveedor.
        En producción, esto llamaría a los servicios de verificación.
        """
        # TODO: Integrar con app.services.data_collection
        # Por ahora, simulamos datos
        
        # En producción, descomentar:
        # from app.services.data_collection import DataCollectionService
        # service = DataCollectionService()
        # return await service.collect_all_data(ruc)
        
        # Mock data para desarrollo
        return {
            'ruc': ruc,
            'company_name': f'Empresa {ruc}',
            'score': 85,  # Simulado
            'risk_level': 'low',
            'sunat_debt': 0,
            'sunat_tax_status': 'ACTIVO',
            'sunat_contributor_status': 'HABIDO',
            'osce_sanctions_count': 0,
            'osce_sanctions_details': [],
            'tce_sanctions_count': 0,
            'tce_sanctions_details': [],
            'checked_at': datetime.utcnow().isoformat()
        }
    
    async def _detect_changes_and_create_alerts(
        self,
        supplier: SupplierNetwork,
        old: CompanySnapshot,
        new: CompanySnapshot
    ):
        """Detecta cambios entre snapshots y crea alertas."""
        alerts_to_create = []
        
        # Cambio en score
        if old.score != new.score and supplier.alert_on_score_change:
            score_delta = new.score - old.score
            
            # Solo alertar si el cambio supera el umbral
            if abs(score_delta) >= supplier.alert_threshold:
                severity = 'high' if score_delta < -20 else 'medium' if score_delta < -10 else 'low'
                
                alert = SupplierAlert(
                    company_id=supplier.company_id,
                    supplier_ruc_hash=supplier.supplier_ruc_hash,
                    supplier_company_name=supplier.supplier_company_name,
                    alert_type='score_change',
                    severity=severity,
                    previous_score=old.score,
                    new_score=new.score,
                    previous_risk_level=old.risk_level,
                    new_risk_level=new.risk_level,
                    change_details={
                        'score_delta': score_delta,
                        'previous_score': old.score,
                        'new_score': new.score,
                        'threshold': supplier.alert_threshold
                    }
                )
                alerts_to_create.append(alert)
        
        # Cambio en nivel de riesgo
        if old.risk_level != new.risk_level:
            severity_map = {
                ('low', 'medium'): 'medium',
                ('low', 'high'): 'high',
                ('low', 'critical'): 'critical',
                ('medium', 'high'): 'high',
                ('medium', 'critical'): 'critical',
                ('high', 'critical'): 'critical',
            }
            severity = severity_map.get((old.risk_level, new.risk_level), 'low')
            
            alert = SupplierAlert(
                company_id=supplier.company_id,
                supplier_ruc_hash=supplier.supplier_ruc_hash,
                supplier_company_name=supplier.supplier_company_name,
                alert_type='risk_level_change',
                severity=severity,
                previous_score=old.score,
                new_score=new.score,
                previous_risk_level=old.risk_level,
                new_risk_level=new.risk_level,
                change_details={
                    'previous_level': old.risk_level,
                    'new_level': new.risk_level
                }
            )
            alerts_to_create.append(alert)
        
        # Nueva sanción OSCE
        if new.osce_sanctions_count > old.osce_sanctions_count and supplier.alert_on_new_sanction:
            new_sanctions = new.osce_sanctions_count - old.osce_sanctions_count
            
            alert = SupplierAlert(
                company_id=supplier.company_id,
                supplier_ruc_hash=supplier.supplier_ruc_hash,
                supplier_company_name=supplier.supplier_company_name,
                alert_type='new_sanction',
                severity='critical',
                previous_score=old.score,
                new_score=new.score,
                previous_risk_level=old.risk_level,
                new_risk_level=new.risk_level,
                change_details={
                    'sanction_type': 'OSCE',
                    'new_sanctions_count': new_sanctions,
                    'total_sanctions': new.osce_sanctions_count,
                    'details': new.osce_sanctions_details
                }
            )
            alerts_to_create.append(alert)
        
        # Nueva sanción TCE
        if new.tce_sanctions_count > old.tce_sanctions_count and supplier.alert_on_new_sanction:
            new_sanctions = new.tce_sanctions_count - old.tce_sanctions_count
            
            alert = SupplierAlert(
                company_id=supplier.company_id,
                supplier_ruc_hash=supplier.supplier_ruc_hash,
                supplier_company_name=supplier.supplier_company_name,
                alert_type='new_sanction',
                severity='critical',
                previous_score=old.score,
                new_score=new.score,
                previous_risk_level=old.risk_level,
                new_risk_level=new.risk_level,
                change_details={
                    'sanction_type': 'TCE',
                    'new_sanctions_count': new_sanctions,
                    'total_sanctions': new.tce_sanctions_count,
                    'details': new.tce_sanctions_details
                }
            )
            alerts_to_create.append(alert)
        
        # Aumento de deuda SUNAT
        if new.sunat_debt > old.sunat_debt and supplier.alert_on_debt_increase:
            debt_increase = new.sunat_debt - old.sunat_debt
            
            # Alertar si aumentó más de 10% o más de S/ 10,000
            if debt_increase > 10000 or (old.sunat_debt > 0 and debt_increase / old.sunat_debt > 0.1):
                alert = SupplierAlert(
                    company_id=supplier.company_id,
                    supplier_ruc_hash=supplier.supplier_ruc_hash,
                    supplier_company_name=supplier.supplier_company_name,
                    alert_type='debt_increase',
                    severity='high' if debt_increase > 50000 else 'medium',
                    previous_score=old.score,
                    new_score=new.score,
                    previous_risk_level=old.risk_level,
                    new_risk_level=new.risk_level,
                    change_details={
                        'previous_debt': old.sunat_debt,
                        'new_debt': new.sunat_debt,
                        'increase': debt_increase
                    }
                )
                alerts_to_create.append(alert)
        
        # Guardar alertas
        for alert in alerts_to_create:
            self.db.add(alert)
            self.alerts_created += 1
            logger.info(f"🔔 Alerta creada: {alert.alert_type} para {alert.supplier_company_name}")
        
        # Enviar notificaciones (en producción)
        if alerts_to_create:
            await self._send_notifications(supplier, alerts_to_create)
    
    async def _send_notifications(self, supplier: SupplierNetwork, alerts: List[SupplierAlert]):
        """Envía notificaciones por email cuando se crean alertas."""
        # TODO: Integrar con email_service
        # from app.services.email_service import send_alert_email
        
        company = self.db.query(Company).filter(Company.id == supplier.company_id).first()
        if not company:
            return
        
        # En producción, enviar email aquí
        logger.info(f"📧 Notificación pendiente para {company.contact_email} ({len(alerts)} alertas)")


async def main():
    """Punto de entrada principal."""
    db = SessionLocal()
    
    try:
        service = NetworkReverificationService(db)
        result = await service.run_daily_check()
        
        # Print resultado en formato JSON para logs
        import json
        print(json.dumps(result, indent=2, default=str))
        
        if not result['success']:
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"❌ Error ejecutando cron job: {e}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())
