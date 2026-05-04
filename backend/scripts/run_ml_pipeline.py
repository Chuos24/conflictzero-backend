#!/usr/bin/env python3
"""
Conflict Zero - ML Pipeline v1.5
Pipeline completo: Generar dataset + Entrenar modelo + Evaluar
Fase 2

Uso:
    cd backend && python scripts/run_ml_pipeline.py
"""

import os
import sys
import json
import subprocess
import time
from datetime import datetime
from pathlib import Path

# Añadir parent al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


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
            timeout=300  # 5 min max por paso
        )
        
        elapsed = time.time() - start
        
        if result.returncode == 0:
            print(f"✅ Completado en {elapsed:.1f}s")
            if result.stdout:
                print(result.stdout[-500:])  # Last 500 chars
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


def generate_dataset() -> bool:
    """Genera dataset histórico sintético."""
    return run_step(
        "Generar Dataset ML",
        [sys.executable, "scripts/generate_ml_dataset.py"],
        cwd="/root/.openclaw/workspace/conflict-zero-fase1/backend"
    )


def train_model() -> bool:
    """Entrena modelo v1.5."""
    return run_step(
        "Entrenar Modelo ML v1.5",
        [
            sys.executable, 
            "scripts/train_ml_model.py",
            "--dataset", "ml_dataset.json",
            "--model-type", "gradient_boosting",
            "--output", "models"
        ],
        cwd="/root/.openclaw/workspace/conflict-zero-fase1/backend"
    )


def validate_model() -> bool:
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
        import numpy as np
        
        model = joblib.load(latest)
        
        # Test prediction
        test_features = np.array([[0.5, 0.3, 0.1, 0.2, 1.0, 0.5]])
        prediction = model.predict(test_features)
        probabilities = model.predict_proba(test_features)
        
        print(f"✅ Modelo cargado exitosamente")
        print(f"   Predicción test: {prediction[0]}")
        print(f"   Probabilidades: {probabilities[0]}")
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
        "pipeline": "ML v1.5 Training",
        "timestamp": datetime.now().isoformat(),
        "results": results,
        "status": "SUCCESS" if all(results.values()) else "PARTIAL" if any(results.values()) else "FAILED"
    }
    
    report_path = Path("/root/.openclaw/workspace/conflict-zero-fase1/backend/ml_pipeline_report.json")
    report_path.write_text(json.dumps(report, indent=2, default=str))
    
    return report["status"]


def main():
    print("=" * 60)
    print("Conflict Zero - ML Pipeline v1.5")
    print("=" * 60)
    print(f"Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    results = {}
    
    # Paso 1: Generar dataset
    results["dataset"] = generate_dataset()
    
    # Paso 2: Entrenar modelo
    results["training"] = train_model() if results["dataset"] else False
    
    # Paso 3: Validar modelo
    results["validation"] = validate_model() if results["training"] else False
    
    # Paso 4: Actualizar versión
    results["version_update"] = update_ml_version() if results["validation"] else False
    
    # Reporte final
    status = generate_report(results)
    
    print("\n" + "=" * 60)
    print("📊 RESUMEN DEL PIPELINE")
    print("=" * 60)
    for step, success in results.items():
        icon = "✅" if success else "❌"
        print(f"   {icon} {step}")
    print("=" * 60)
    print(f"Estado final: {status}")
    
    if status == "SUCCESS":
        print("\n🎉 Pipeline ML v1.5 completado exitosamente!")
        print("   El modelo está listo para producción.")
    elif status == "PARTIAL":
        print("\n⚠️ Pipeline completado parcialmente. Revisar logs.")
    else:
        print("\n❌ Pipeline falló. Revisar errores arriba.")
    
    return 0 if status != "FAILED" else 1


if __name__ == "__main__":
    sys.exit(main())
