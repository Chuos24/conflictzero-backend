#!/usr/bin/env python3
"""
Conflict Zero - ML Dataset Generator
Genera datos sintéticos históricos para entrenamiento del modelo ML v1.5+
Fase 2

Uso:
    cd backend && python scripts/generate_ml_dataset.py
"""

import random
import string
import hashlib
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
import json
import sys
import os

# Add parent to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.core.database import Base, get_db
from app.core.config import settings
from app.models import Company, VerificationRequest
from app.models_monitoring import SupplierSnapshot, SupplierChange, MonitoringRule


def generate_ruc():
    """Genera un RUC peruano válido (formato)."""
    # RUC empieza con 10 (persona natural con empresa) o 20 (empresa)
    prefix = random.choice(['10', '20'])
    body = ''.join(random.choices(string.digits, k=8))
    # Checksum simple (no real, solo para formato)
    check = random.randint(0, 9)
    return f"{prefix}{body}{check}"


def encrypt_ruc_simple(ruc: str) -> bytes:
    """Encriptación simple para datos sintéticos (no usar en producción)."""
    # XOR básico con clave fija para testing
    key = b'conflictzero2026'
    ruc_bytes = ruc.encode('utf-8')
    encrypted = bytearray()
    for i, b in enumerate(ruc_bytes):
        encrypted.append(b ^ key[i % len(key)])
    return bytes(encrypted)


def generate_company_name():
    """Genera nombre de empresa ficticio peruana."""
    prefixes = ['Comercial', 'Servicios', 'Tecnologías', 'Constructora', 'Grupo',
                'Importaciones', 'Exportaciones', 'Logística', 'Consultora', 'Industrias']
    names = ['Andina', 'Nacional', 'Peruana', 'Lima', 'Cuzco', 'Arequipa', 'Trujillo',
             'Pacífico', 'Sol', 'Inca', 'Sur', 'Norte', 'Centro', 'Oeste', 'Este']
    suffixes = ['S.A.C.', 'S.R.L.', 'E.I.R.L.', 'S.A.', 'S.A.A.', 'Corp.', 'Group']
    return f"{random.choice(prefixes)} {random.choice(names)} {random.choice(suffixes)}"


def generate_debt_trend(start_debt, days, trend='stable'):
    """Genera serie de deuda con tendencia."""
    debts = []
    current = start_debt
    for i in range(days):
        if trend == 'increasing':
            current *= 1.02  # 2% diario
        elif trend == 'decreasing':
            current *= 0.98
        elif trend == 'volatile':
            current *= random.uniform(0.9, 1.1)
        else:
            current *= random.uniform(0.99, 1.01)
        current = max(0, current)
        debts.append(round(current, 2))
    return debts


def generate_supplier_profile(risk_profile='low'):
    """Genera un perfil de proveedor con características de riesgo."""
    if risk_profile == 'low':
        return {
            'score_base': random.randint(70, 95),
            'sanctions': 0,
            'debt_trend': 'decreasing',
            'volatility': 'low',
            'compliance_changes': 0
        }
    elif risk_profile == 'medium':
        return {
            'score_base': random.randint(50, 75),
            'sanctions': random.randint(0, 2),
            'debt_trend': random.choice(['stable', 'slight_increase']),
            'volatility': 'medium',
            'compliance_changes': random.randint(0, 2)
        }
    elif risk_profile == 'high':
        return {
            'score_base': random.randint(20, 50),
            'sanctions': random.randint(2, 5),
            'debt_trend': 'increasing',
            'volatility': 'high',
            'compliance_changes': random.randint(2, 5)
        }
    else:  # critical
        return {
            'score_base': random.randint(0, 25),
            'sanctions': random.randint(5, 10),
            'debt_trend': 'increasing',
            'volatility': 'extreme',
            'compliance_changes': random.randint(5, 10)
        }


def generate_dataset(db: Session, companies_count=5, suppliers_per_company=10,
                     days_history=90, snapshot_frequency_days=7):
    """
    Genera dataset sintético completo para ML training.
    
    Args:
        companies_count: Número de empresas monitoreadoras
        suppliers_per_company: Proveedores por empresa
        days_history: Días de historial a generar
        snapshot_frequency_days: Frecuencia de snapshots (días)
    """
    print(f"🚀 Generando dataset ML...")
    print(f"   Empresas: {companies_count}")
    print(f"   Proveedores: {suppliers_per_company * companies_count}")
    print(f"   Días de historial: {days_history}")
    print(f"   Frecuencia snapshots: cada {snapshot_frequency_days} días")
    
    risk_profiles = ['low', 'low', 'low', 'medium', 'medium', 'high', 'critical']
    
    # Crear empresas
    companies = []
    for i in range(companies_count):
        ruc = generate_ruc()
        company = Company(
            ruc=ruc,
            razon_social=generate_company_name(),
            plan_tier=random.choice(['bronze', 'silver', 'gold', 'founder']),
            status='active',
            contact_email=f"admin{i}@example.com",
            contact_name=f"Admin {i}",
            contact_phone=f"+519{random.randint(10000000, 99999999)}",
            max_monthly_queries=random.choice([100, 500, 1000, 5000]),
            created_at=datetime.utcnow() - timedelta(days=random.randint(30, 365))
        )
        db.add(company)
        db.flush()
        companies.append(company)
    
    print(f"✅ {len(companies)} empresas creadas")
    
    # Crear proveedores con snapshots
    total_snapshots = 0
    total_changes = 0
    total_verifications = 0
    
    for company in companies:
        for s in range(suppliers_per_company):
            ruc = generate_ruc()
            profile = generate_supplier_profile(random.choice(risk_profiles))
            
            # Generar snapshots a lo largo del tiempo
            start_date = datetime.utcnow() - timedelta(days=days_history)
            snapshot_dates = []
            
            for day in range(0, days_history, snapshot_frequency_days):
                snapshot_dates.append(start_date + timedelta(days=day))
            
            # Generar deuda con tendencia
            start_debt = random.randint(0, 500000) if profile['debt_trend'] != 'decreasing' else random.randint(100000, 1000000)
            debt_series = generate_debt_trend(start_debt, len(snapshot_dates), profile['debt_trend'])
            
            prev_score = profile['score_base']
            
            for idx, snapshot_date in enumerate(snapshot_dates):
                # Score con volatilidad según perfil
                volatility_map = {
                    'low': 2, 'medium': 8, 'high': 15, 'extreme': 25
                }
                vol = volatility_map.get(profile['volatility'], 5)
                score = max(0, min(100, prev_score + random.randint(-vol, vol)))
                prev_score = score
                
                # Crear snapshot
                raw_data = {
                    'razon_social': generate_company_name(),
                    'deuda_tributaria': debt_series[idx],
                    'osce_sanciones': profile['sanctions'],
                    'tce_sanciones': random.randint(0, profile['sanctions']),
                    'score': score,
                    'verified': True
                }
                
                snapshot = SupplierSnapshot(
                    company_id=company.id,
                    ruc=ruc,
                    risk_score=score,
                    raw_data=raw_data,
                    snapshot_date=snapshot_date
                )
                db.add(snapshot)
                total_snapshots += 1
                
                # Generar cambios (algunos snapshots tendrán cambios asociados)
                if random.random() < 0.3:  # 30% de probabilidad de cambio
                    change_types = ['sanction_added', 'compliance_expired', 
                                    'compliance_renewed', 'representative_changed',
                                    'score_changed', 'debt_changed']
                    
                    change = SupplierChange(
                        company_id=company.id,
                        change_type=random.choice(change_types),
                        description=f"Cambio detectado en {snapshot_date.strftime('%Y-%m-%d')}",
                        severity=random.choice(['critical', 'high', 'medium', 'low']),
                        previous_value=str(random.randint(0, 100)),
                        new_value=str(score),
                        alert_sent=random.random() < 0.5,
                        snapshot_id=snapshot.id if hasattr(snapshot, 'id') else None,
                        created_at=snapshot_date
                    )
                    db.add(change)
                    total_changes += 1
            
            # Crear verificaciones
            for _ in range(random.randint(1, 10)):
                verification = VerificationRequest(
                    consultant_ruc=company.ruc,
                    target_ruc=ruc,
                    target_company_name=raw_data['razon_social'],
                    score=score,
                    risk_level='low' if score >= 70 else 'medium' if score >= 50 else 'high' if score >= 30 else 'critical',
                    sunat_debt=debt_series[idx],
                    osce_sanctions_count=profile['sanctions'],
                    tce_sanctions_count=random.randint(0, profile['sanctions']),
                    created_at=datetime.utcnow() - timedelta(days=random.randint(0, days_history))
                )
                db.add(verification)
                total_verifications += 1
    
    db.commit()
    
    print(f"\n📊 Dataset generado exitosamente:")
    print(f"   Snapshots: {total_snapshots}")
    print(f"   Cambios detectados: {total_changes}")
    print(f"   Verificaciones: {total_verifications}")
    print(f"   Total registros: {total_snapshots + total_changes + total_verifications}")
    
    return {
        'companies': len(companies),
        'snapshots': total_snapshots,
        'changes': total_changes,
        'verifications': total_verifications
    }


def export_dataset_to_json(db: Session, output_path='ml_dataset.json'):
    """Exporta el dataset a JSON para análisis externo."""
    snapshots = db.query(SupplierSnapshot).all()
    
    data = []
    for s in snapshots:
        data.append({
            'ruc': s.ruc,
            'company_id': s.company_id,
            'risk_score': s.risk_score,
            'snapshot_date': s.snapshot_date.isoformat(),
            'raw_data': s.raw_data
        })
    
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2, default=str)
    
    print(f"📁 Dataset exportado a {output_path} ({len(data)} registros)")


if __name__ == '__main__':
    print("=" * 60)
    print("Conflict Zero - ML Dataset Generator")
    print("=" * 60)
    
    # Usar SQLite local para generación rápida
    engine = create_engine('sqlite:///./ml_dataset.db')
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        dataset = generate_dataset(
            db=db,
            companies_count=3,
            suppliers_per_company=8,
            days_history=90,
            snapshot_frequency_days=7
        )
        
        export_dataset_to_json(db, 'ml_dataset.json')
        
        print("\n✅ Dataset listo para entrenamiento ML v1.5+")
        print("   Próximo paso: Entrenar modelo con los datos generados")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()
