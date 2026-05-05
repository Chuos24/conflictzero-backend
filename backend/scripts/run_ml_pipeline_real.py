#!/usr/bin/env python3
"""
Conflict Zero - ML Pipeline v1.5 con Datos Reales de PostgreSQL
Pipeline completo: Extraer datos reales + Generar dataset + Entrenar modelo + Evaluar
Fase 2 - Producción

Uso:
    cd backend && python scripts/run_ml_pipeline_real.py

Requiere PostgreSQL activo con datos históricos.
"""

import os
import sys
import json
import subprocess
import time
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.core.config import settings
from app.models import VerificationRequest, Company
from app.models_monitoring import SupplierSnapshot, SupplierChange


def run_step(name: str, command: list, cwd: str = None) -> bool:
    """Ejecuta un paso del pipeline y reporta resultado."""
    print(f"\n{'='*60}")
    print(f"🔹 PASO: {name}")
    print(f"{'='*60}")
    
    start = time.time()
    try:
        result = subprocess.run(
            command,
            cwd=cwd or os.path.join(os.path.dirname(__file__), '..'),
            capture_output=True,
            text=True,
            timeout=300
        )
        
        elapsed = time.time() - start
        
        if result.returncode == 0:
            print(f"✅ Completado en {elapsed:.1f}s")
            if result.stdout:
                print(result.stdout[-500:])
            return True
        else:
            print(f"❌ Falló en {elapsed:.1f}s")
            print(f"STDERR: {result.stderr[-1000:]}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"❌ Timeout (5min)")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def extract_real_dataset() -> bool:
    """Extrae datos reales de PostgreSQL para entrenamiento ML."""
    print(f"\n{'='*60}")
    print(f"🔹 PASO: Extraer Dataset Real de PostgreSQL")
    print(f"{'='*60}")
    
    try:
        # Conexión a PostgreSQL
        engine = create_engine(settings.DATABASE_URL)
        Session = sessionmaker(bind=engine)
        db = Session()
        
        # Obtener verificaciones históricas
        verifications = db.query(VerificationRequest).filter(
            VerificationRequest.created_at >= datetime.utcnow() - timedelta(days=180)
        ).all()
        
        if len(verifications) < 10:
            print(f"⚠️ Solo {len(verifications)} verificaciones encontradas. Usando dataset sintético.")
            return False
        
        print(f"✅ {len(verifications)} verificaciones históricas encontradas")
        
        # Extraer features
        data = []
        for v in verifications:
            ruc = v.target_ruc
            
            # Obtener snapshots del proveedor
            snapshots = db.query(SupplierSnapshot).filter(
                SupplierSnapshot.ruc == ruc
            ).order_by(SupplierSnapshot.snapshot_date.asc()).all()
            
            # Features
            risk_score = v.risk_score or 50
            debt_ratio = 0.0
            sanctions = 0
            volatility = 0.0
            
            if snapshots:
                scores = [s.risk_score for s in snapshots if s.risk_score is not None]
                if scores:
                    volatility = float(np.std(scores)) if len(scores) > 1 else 0.0
                    
                    # Obtener deuda del último snapshot
                    raw = snapshots[-1].raw_data or {}
                    debt = raw.get("deuda_tributaria", raw.get("deuda", 0))
                    debt_ratio = float(debt) / 100000 if debt else 0.0
            
            # Contar sanciones
            sanction_count = db.query(SupplierChange).filter(
                SupplierChange.change_type == "sanction_added",
                SupplierChange.company_id == ruc
            ).count()
            sanctions = min(sanction_count, 10)
            
            # Determinar clase de riesgo
            if risk_score >= 70:
                risk_class = 0  # bajo
            elif risk_score >= 50:
                risk_class = 1  # moderado
            elif risk_score >= 30:
                risk_class = 2  # alto
            else:
                risk_class = 3  # crítico
            
            data.append({
                "risk_score": risk_score,
                "debt_ratio": debt_ratio,
                "sanctions": sanctions,
                "volatility": volatility,
                "verified": 1,
                "consultation_freq": len(snapshots),
                "risk_class": risk_class
            })
        
        # Guardar dataset
        df = pd.DataFrame(data)
        dataset_path = Path("/root/.openclaw/workspace/conflict-zero-fase1/backend/ml_dataset_real.json")
        dataset_path.write_text(df.to_json(orient="records", indent=2))
        
        print(f"✅ Dataset real guardado: {len(data)} registros")
        print(f"   Distribución de clases:")
        for cls, count in df["risk_class"].value_counts().sort_index().items():
            labels = {0: "bajo", 1: "moderado", 2: "alto", 3: "crítico"}
            print(f"     {labels[cls]}: {count}")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Error extrayendo datos reales: {e}")
        return False


def train_model_real() -> bool:
    """Entrena modelo con datos reales."""
    dataset_path = Path("/root/.openclaw/workspace/conflict-zero-fase1/backend/ml_dataset_real.json")
    
    if not dataset_path.exists():
        print("❌ No se encontró dataset real. Generando dataset sintético...")
        return run_step(
            "Entrenar Modelo (Sintético)",
            [
                sys.executable,
                "scripts/train_ml_model.py",
                "--dataset", "ml_dataset.json",
                "--model-type", "gradient_boosting",
                "--output", "models"
            ],
            cwd="/root/.openclaw/workspace/conflict-zero-fase1/backend"
        )
    
    return run_step(
        "Entrenar Modelo (Datos Reales)",
        [
            sys.executable,
            "scripts/train_ml_model.py",
            "--dataset", str(dataset_path),
            "--model-type", "gradient_boosting",
            "--output", "models",
            "--name", "real_v1.5"
        ],
        cwd="/root/.openclaw/workspace/conflict-zero-fase1/backend"
    )


def validate_model_real() -> bool:
    """Valida que el modelo se pueda cargar y hacer predicciones."""
    print(f"\n{'='*60}")
    print(f"🔹 PASO: Validación del Modelo")
    print(f"{'='*60}")
    
    models_dir = Path("/root/.openclaw/workspace/conflict-zero-fase1/backend/models")
    latest = models_dir / "latest.joblib"
    
    if not latest.exists():
        print("❌ No se encontró modelo latest.joblib")
        return False
    
    try:
        import joblib
        
        model = joblib.load(latest)
        
        # Test prediction con datos típicos peruanos
        test_features = np.array([
            [0.65, 0.3, 0.1, 0.2, 1.0, 0.5],   # Empresa estable
            [0.25, 0.8, 0.4, 0.5, 0.0, 0.1],   # Empresa riesgosa
            [0.50, 0.5, 0.2, 0.3, 1.0, 0.3]    # Empresa moderada
        ])
        
        predictions = model.predict(test_features)
        probabilities = model.predict_proba(test_features)
        
        labels = ["bajo", "moderado", "alto", "crítico"]
        
        print(f"✅ Modelo cargado exitosamente")
        for i, (pred, prob) in enumerate(zip(predictions, probabilities)):
            print(f"   Test {i+1}: {labels[pred]} (confianza: {max(prob):.1%})")
        
        return True
        
    except Exception as e:
        print(f"❌ Error validando modelo: {e}")
        return False


def update_ml_version() -> bool:
    """Actualiza la versión ML en el código del backend."""
    print(f"\n{'='*60}")
    print(f"🔹 PASO: Actualizar Versión ML en Código")
    print(f"{'='*60}")
    
    ml_scoring_path = Path("/root/.openclaw/workspace/conflict-zero-fase1/backend/app/routers/ml_scoring.py")
    
    if not ml_scoring_path.exists():
        print("❌ No se encontró ml_scoring.py")
        return False
    
    try:
        content = ml_scoring_path.read_text()
        
        # Actualizar versión
        if 'ML_SCORING_VERSION = "1.4"' in content:
            new_content = content.replace(
                'ML_SCORING_VERSION = "1.4"',
                'ML_SCORING_VERSION = "1.5"'
            )
            ml_scoring_path.write_text(new_content)
            print("✅ Versión actualizada: 1.4 → 1.5")
            return True
        elif 'ML_SCORING_VERSION = "1.5"' in content:
            print("✅ Versión ya está en 1.5")
            return True
        else:
            print("⚠️ No se encontró versión para actualizar")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def generate_report(results: dict) -> str:
    """Genera reporte de ejecución del pipeline."""
    report = {
        "pipeline": "ML v1.5 Real Data Training",
        "timestamp": datetime.now().isoformat(),
        "results": results,
        "status": "SUCCESS" if all(results.values()) else "PARTIAL" if any(results.values()) else "FAILED"
    }
    
    report_path = Path("/root/.openclaw/workspace/conflict-zero-fase1/backend/ml_pipeline_real_report.json")
    report_path.write_text(json.dumps(report, indent=2, default=str))
    
    return report["status"]


def main():
    print("=" * 60)
    print("Conflict Zero - ML Pipeline v1.5 (Datos Reales)")
    print("=" * 60)
    print(f"Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Database: {settings.DATABASE_URL[:50]}...")
    print("=" * 60)
    
    results = {}
    
    # Paso 1: Extraer datos reales
    results["extract_real"] = extract_real_dataset()
    
    # Paso 2: Entrenar modelo
    results["training"] = train_model_real()
    
    # Paso 3: Validar modelo
    results["validation"] = validate_model_real() if results["training"] else False
    
    # Paso 4: Actualizar versión
    results["version_update"] = update_ml_version() if results["validation"] else False
    
    # Reporte final
    status = generate_report(results)
    
    print("\n" + "=" * 60)
    print("📊 RESUMEN DEL PIPELINE (DATOS REALES)")
    print("=" * 60)
    for step, success in results.items():
        icon = "✅" if success else "❌"
        print(f"   {icon} {step}")
    print("=" * 60)
    print(f"Estado final: {status}")
    
    if status == "SUCCESS":
        print("\n🎉 Pipeline ML v1.5 con datos reales completado!")
        print("   El modelo está listo para producción.")
    elif status == "PARTIAL":
        print("\n⚠️ Pipeline completado parcialmente.")
        print("   Posiblemente faltan datos históricos suficientes.")
    else:
        print("\n❌ Pipeline falló. Revisar errores arriba.")
    
    return 0 if status != "FAILED" else 1


if __name__ == "__main__":
    sys.exit(main())
