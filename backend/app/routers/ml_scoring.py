"""
Conflict Zero - ML Scoring Router
Endpoint para exponer el ML Score de riesgo predictivo.
Fase 2
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_company
from app.services.ml_scoring_service import MLScoringService
from app.models_v2 import Company

router = APIRouter(prefix="/ml", tags=["ML Scoring"])


def get_ml_service(db: Session = Depends(get_db)) -> MLScoringService:
    """Dependencia para obtener MLScoringService."""
    return MLScoringService(db)


@router.get("/score/{ruc}", summary="Obtener ML Score de un proveedor")
async def get_ml_score(
    ruc: str,
    lookback_days: int = Query(default=90, ge=30, le=365, description="Días de historial a considerar"),
    current_company: Company = Depends(get_current_company),
    service: MLScoringService = Depends(get_ml_service)
):
    """
    Calcula y retorna el ML Score de riesgo para un proveedor.
    
    - Requiere autenticación
    - Usa features históricas para predecir riesgo futuro
    - Retorna score, nivel de riesgo, features y explicación
    """
    # Validar RUC (11 dígitos numéricos)
    if not ruc or len(ruc) != 11 or not ruc.isdigit():
        raise HTTPException(
            status_code=400,
            detail="RUC inválido. Debe tener 11 dígitos numéricos."
        )
    
    try:
        result = service.calculate_ml_score(
            ruc=ruc,
            company_id=str(current_company.id),
            lookback_days=lookback_days
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error calculando ML score: {str(e)}"
        )


@router.get("/score/{ruc}/anomalies", summary="Detectar anomalías en proveedor")
async def get_ml_anomalies(
    ruc: str,
    days: int = Query(default=30, ge=7, le=90, description="Días de historial para anomalías"),
    current_company: Company = Depends(get_current_company),
    service: MLScoringService = Depends(get_ml_service)
):
    """
    Detecta anomalías en el comportamiento de un proveedor.
    
    - Cambios abruptos de score
    - Múltiples sanciones en corto tiempo
    - Deuda en aumento acelerado
    """
    if not ruc or len(ruc) != 11 or not ruc.isdigit():
        raise HTTPException(
            status_code=400,
            detail="RUC inválido. Debe tener 11 dígitos numéricos."
        )
    
    try:
        from datetime import timedelta
        since = datetime.utcnow() - timedelta(days=days)
        anomalies = service.detect_anomalies(ruc=ruc, since=since)
        return {
            "ruc": ruc,
            "anomalies": anomalies,
            "anomaly_count": len(anomalies),
            "has_anomalies": len(anomalies) > 0,
            "days_analyzed": days,
            "analyzed_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error detectando anomalías: {str(e)}"
        )


@router.get("/score/{ruc}/benchmark", summary="Benchmarking sectorial")
async def get_ml_benchmark(
    ruc: str,
    sector: Optional[str] = Query(None, description="Sector económico para comparar"),
    current_company: Company = Depends(get_current_company),
    service: MLScoringService = Depends(get_ml_service)
):
    """
    Benchmarking del proveedor contra su sector.
    """
    if not ruc or len(ruc) != 11 or not ruc.isdigit():
        raise HTTPException(
            status_code=400,
            detail="RUC inválido. Debe tener 11 dígitos numéricos."
        )
    
    try:
        benchmark = service.get_benchmark(ruc=ruc, sector=sector)
        return benchmark
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generando benchmark: {str(e)}"
        )


@router.post("/score/batch", summary="ML Score batch para múltiples RUCs")
async def get_ml_score_batch(
    rucs: List[str],
    lookback_days: int = Query(default=90, ge=30, le=365),
    current_company: Company = Depends(get_current_company),
    service: MLScoringService = Depends(get_ml_service)
):
    """
    Calcula ML Score para múltiples RUCs en batch.
    
    - Máximo 50 RUCs por petición
    - Útil para evaluación de red de proveedores
    """
    if len(rucs) > 50:
        raise HTTPException(
            status_code=400,
            detail="Máximo 50 RUCs por petición batch"
        )
    
    results = []
    errors = []
    
    for ruc in rucs:
        if not ruc or len(ruc) != 11 or not ruc.isdigit():
            errors.append({"ruc": ruc, "error": "RUC inválido"})
            continue
        
        try:
            score = service.calculate_ml_score(
                ruc=ruc,
                company_id=str(current_company.id),
                lookback_days=lookback_days
            )
            results.append(score)
        except Exception as e:
            errors.append({"ruc": ruc, "error": str(e)})
    
    return {
        "results": results,
        "errors": errors,
        "total_requested": len(rucs),
        "successful": len(results),
        "failed": len(errors),
        "lookback_days": lookback_days
    }


@router.get("/model-info", summary="Información del modelo ML")
async def get_model_info():
    """
    Retorna información sobre el modelo de ML actual.
    
    - Versión del modelo
    - Features utilizadas
    - Pesos de features
    - Thresholds de riesgo
    """
    return {
        "model_version": "v1.0",
        "model_type": "heuristic_weighted",
        "features": list(MLScoringService.FEATURE_WEIGHTS.keys()),
        "feature_weights": MLScoringService.FEATURE_WEIGHTS,
        "risk_thresholds": {
            "low": 40,
            "medium": 60,
            "high": 75,
            "critical": 85
        },
        "description": "Modelo base de scoring predictivo basado en features históricas"
    }


@router.get("/health", summary="Health check del servicio ML")
async def get_ml_health(
    db: Session = Depends(get_db)
):
    """
    Verifica que el servicio de ML esté operativo.
    """
    try:
        # Verificar que podemos instanciar el servicio
        service = MLScoringService(db)
        # Verificar que hay datos suficientes
        from app.models_monitoring import SupplierSnapshot
        from sqlalchemy import func
        count = db.query(func.count(SupplierSnapshot.id)).scalar() or 0
        
        return {
            "status": "healthy",
            "model_version": "v1.0",
            "snapshots_count": count,
            "ready": count >= 10  # Mínimo 10 snapshots para confianza
        }
    except Exception as e:
        # En entornos sin datos (testing), retornar degraded en vez de error
        return {
            "status": "degraded",
            "model_version": "v1.0",
            "snapshots_count": 0,
            "ready": False,
            "note": "Sin conexión a base de datos o datos insuficientes"
        }


@router.get("/features", summary="Features del modelo ML")
async def get_ml_features():
    """
    Lista las features utilizadas por el modelo de ML con descripciones.
    """
    return {
        "features": [
            {
                "name": "verification_frequency",
                "weight": MLScoringService.FEATURE_WEIGHTS["verification_frequency"],
                "description": "Frecuencia de verificación del proveedor (más frecuente = más confiable)",
                "type": "frequency",
                "range": "0-100"
            },
            {
                "name": "score_volatility",
                "weight": MLScoringService.FEATURE_WEIGHTS["score_volatility"],
                "description": "Volatilidad del score histórico (menos volátil = más estable)",
                "type": "volatility",
                "range": "0-100"
            },
            {
                "name": "sanction_history",
                "weight": MLScoringService.FEATURE_WEIGHTS["sanction_history"],
                "description": "Historial de sanciones OSCE/TCE (más sanciones = más riesgo)",
                "type": "count",
                "range": "0-100"
            },
            {
                "name": "debt_trend",
                "weight": MLScoringService.FEATURE_WEIGHTS["debt_trend"],
                "description": "Tendencia de deuda SUNAT (deuda creciente = más riesgo)",
                "type": "trend",
                "range": "0-100"
            },
            {
                "name": "compliance_consistency",
                "weight": MLScoringService.FEATURE_WEIGHTS["compliance_consistency"],
                "description": "Consistencia de compliance (cambios frecuentes = menos confiable)",
                "type": "consistency",
                "range": "0-100"
            }
        ],
        "total_features": len(MLScoringService.FEATURE_WEIGHTS),
        "model_version": "v1.0"
    }
