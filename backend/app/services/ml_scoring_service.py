"""
Conflict Zero - ML Scoring Service
Fase 2 - Machine Learning para scoring predictivo de riesgo
"""

import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func
import json
import hashlib

from app.core.database import get_db
from app.models_monitoring import SupplierSnapshot, SupplierChange
from app.models import VerificationRequest, Company


class MLScoringService:
    """
    Servicio de Machine Learning para scoring predictivo de riesgo.
    
    Utiliza features históricas para predecir riesgo futuro:
    - Historial de verificaciones
    - Cambios detectados
    - Patrones de comportamiento
    - Benchmarking sectorial
    """
    
    # Pesos para el modelo base (v1)
    FEATURE_WEIGHTS = {
        "verification_frequency": 0.15,
        "score_volatility": 0.20,
        "sanction_history": 0.25,
        "debt_trend": 0.20,
        "compliance_consistency": 0.20
    }
    
    # Thresholds de riesgo
    RISK_THRESHOLDS = {
        "low": 70,
        "moderate": 50,
        "high": 30,
        "critical": 0
    }
    
    def __init__(self, db: Session):
        self.db = db
    
    def calculate_ml_score(
        self,
        ruc: str,
        company_id: Optional[str] = None,
        lookback_days: int = 90
    ) -> Dict:
        """
        Calcula el ML score para un proveedor basado en historial.
        
        Args:
            ruc: RUC del proveedor
            company_id: ID de la empresa que monitorea (opcional)
            lookback_days: Días de historial a considerar
            
        Returns:
            Dict con score, features usadas y explicación
        """
        since = datetime.utcnow() - timedelta(days=lookback_days)
        
        # Features
        features = {
            "verification_frequency": self._get_verification_frequency(ruc, since),
            "score_volatility": self._get_score_volatility(ruc, since),
            "sanction_history": self._get_sanction_history(ruc, since),
            "debt_trend": self._get_debt_trend(ruc, since),
            "compliance_consistency": self._get_compliance_consistency(ruc, since)
        }
        
        # Calcular score ponderado
        weighted_score = sum(
            features[key] * weight
            for key, weight in self.FEATURE_WEIGHTS.items()
        )
        
        # Normalizar a 0-100
        ml_score = max(0, min(100, weighted_score))
        
        # Determinar nivel
        risk_level = self._get_risk_level(ml_score)
        
        # Generar explicación
        explanation = self._generate_explanation(features, risk_level)
        
        return {
            "ruc": ruc,
            "ml_score": round(ml_score, 2),
            "risk_level": risk_level,
            "features": features,
            "explanation": explanation,
            "lookback_days": lookback_days,
            "calculated_at": datetime.utcnow().isoformat(),
            "model_version": "1.0.0"
        }
    
    def _get_verification_frequency(self, ruc: str, since: datetime) -> float:
        """
        Feature: Frecuencia de verificaciones en el período.
        Más verificaciones = más transparencia = mejor score.
        """
        count = self.db.query(func.count(VerificationRequest.id)).filter(
            VerificationRequest.target_ruc == ruc,
            VerificationRequest.created_at >= since
        ).scalar()
        
        # Normalizar: 0-10+ verificaciones → 0-100
        return min(100, count * 10)
    
    def _get_score_volatility(self, ruc: str, since: datetime) -> float:
        """
        Feature: Volatilidad del score histórico.
        Menos volatilidad = más estable = mejor score.
        """
        snapshots = self.db.query(SupplierSnapshot).filter(
            SupplierSnapshot.ruc == ruc,
            SupplierSnapshot.snapshot_date >= since
        ).order_by(SupplierSnapshot.snapshot_date.asc()).all()
        
        if len(snapshots) < 2:
            return 50  # Neutral si no hay historial
        
        scores = [s.risk_score for s in snapshots if s.risk_score is not None]
        if len(scores) < 2:
            return 50
        
        # Calcular desviación estándar
        std = np.std(scores)
        
        # Menor volatilidad = mejor (invertir: 100 - std_normalizado)
        # std típica 0-30 → invertir a 100-0
        volatility_score = max(0, 100 - (std * 3))
        
        return round(volatility_score, 2)
    
    def _get_sanction_history(self, ruc: str, since: datetime) -> float:
        """
        Feature: Historial de sanciones.
        Menos sanciones = mejor score.
        """
        sanctions = self.db.query(func.count(SupplierChange.id)).filter(
            SupplierChange.change_type == "sanction_added",
            SupplierChange.company_id == ruc,
            SupplierChange.created_at >= since
        ).scalar()
        
        # 0 sanciones = 100, cada sanción resta 25
        return max(0, 100 - (sanctions * 25))
    
    def _get_debt_trend(self, ruc: str, since: datetime) -> float:
        """
        Feature: Tendencia de deuda.
        Deuda decreciente = mejor score.
        """
        # Obtener snapshots ordenados
        snapshots = self.db.query(SupplierSnapshot).filter(
            SupplierSnapshot.ruc == ruc,
            SupplierSnapshot.snapshot_date >= since
        ).order_by(SupplierSnapshot.snapshot_date.asc()).all()
        
        if len(snapshots) < 2:
            return 50  # Neutral
        
        # Extraer deuda de raw_data
        debts = []
        for s in snapshots:
            raw = s.raw_data or {}
            debt = raw.get("deuda_tributaria", raw.get("deuda", 0))
            if debt:
                debts.append(float(debt))
        
        if len(debts) < 2:
            return 50
        
        # Calcular tendencia (pendiente)
        first_debt = debts[0]
        last_debt = debts[-1]
        
        if first_debt == 0:
            return 100 if last_debt == 0 else 50
        
        # Ratio de cambio: < 1 = deuda decreciente (bueno)
        ratio = last_debt / first_debt
        
        # Invertir: ratio 0.5 → score 75, ratio 2.0 → score 25
        debt_score = max(0, min(100, 100 - ((ratio - 1) * 50)))
        
        return round(debt_score, 2)
    
    def _get_compliance_consistency(self, ruc: str, since: datetime) -> float:
        """
        Feature: Consistencia de compliance.
        Compliance consistente = mejor score.
        """
        # Contar cambios de compliance
        compliance_changes = self.db.query(func.count(SupplierChange.id)).filter(
            SupplierChange.change_type.in_([
                "compliance_expired", "compliance_renewed", "representative_changed"
            ]),
            SupplierChange.company_id == ruc,
            SupplierChange.created_at >= since
        ).scalar()
        
        # 0 cambios = 100, cada cambio resta 15
        return max(0, 100 - (compliance_changes * 15))
    
    def _get_risk_level(self, score: float) -> str:
        """Determina el nivel de riesgo basado en el score."""
        if score >= self.RISK_THRESHOLDS["low"]:
            return "low"
        elif score >= self.RISK_THRESHOLDS["moderate"]:
            return "moderate"
        elif score >= self.RISK_THRESHOLDS["high"]:
            return "high"
        else:
            return "critical"
    
    def _generate_explanation(
        self,
        features: Dict[str, float],
        risk_level: str
    ) -> List[str]:
        """Genera explicación legible del score."""
        explanations = []
        
        # Verificación frequency
        if features["verification_frequency"] >= 80:
            explanations.append("Alta frecuencia de verificaciones indica transparencia.")
        elif features["verification_frequency"] <= 30:
            explanations.append("Baja frecuencia de verificaciones - posible falta de transparencia.")
        
        # Volatilidad
        if features["score_volatility"] >= 80:
            explanations.append("Score histórico muy estable.")
        elif features["score_volatility"] <= 40:
            explanations.append("Alta volatilidad en score histórico - inestabilidad detectada.")
        
        # Sanciones
        if features["sanction_history"] >= 90:
            explanations.append("Sin sanciones recientes.")
        elif features["sanction_history"] <= 50:
            explanations.append("Sanciones detectadas recientemente.")
        
        # Deuda
        if features["debt_trend"] >= 80:
            explanations.append("Tendencia de deuda favorable (decreciente).")
        elif features["debt_trend"] <= 40:
            explanations.append("Deuda en aumento - riesgo financiero creciente.")
        
        # Compliance
        if features["compliance_consistency"] >= 80:
            explanations.append("Compliance consistente y estable.")
        elif features["compliance_consistency"] <= 50:
            explanations.append("Múltiples cambios de compliance detectados.")
        
        # Overall
        if risk_level == "low":
            explanations.append("✅ Proveedor de bajo riesgo recomendado.")
        elif risk_level == "critical":
            explanations.append("⚠️ ALTO RIESGO: Se recomienda evaluación adicional antes de contratar.")
        
        return explanations
    
    def get_benchmark(
        self,
        ruc: str,
        sector: Optional[str] = None
    ) -> Dict:
        """
        Benchmarking del proveedor contra su sector.
        """
        # Obtener score del proveedor
        provider_score = self.calculate_ml_score(ruc)
        
        # Si no hay sector, retornar solo score individual
        if not sector:
            return {
                "ruc": ruc,
                "individual_score": provider_score["ml_score"],
                "sector": None,
                "sector_average": None,
                "sector_median": None,
                "percentile": None,
                "comparison": "No hay datos de sector para comparar"
            }
        
        # TODO: Implementar comparación sectorial con datos agregados
        # Por ahora retornar placeholder
        return {
            "ruc": ruc,
            "individual_score": provider_score["ml_score"],
            "sector": sector,
            "sector_average": None,
            "sector_median": None,
            "percentile": None,
            "comparison": "Benchmarking sectorial requiere dataset de entrenamiento"
        }
    
    def detect_anomalies(
        self,
        ruc: str,
        since: datetime = None
    ) -> List[Dict]:
        """
        Detecta anomalías en el comportamiento del proveedor.
        """
        if since is None:
            since = datetime.utcnow() - timedelta(days=30)
        
        anomalies = []
        
        # 1. Cambio abrupto de score
        snapshots = self.db.query(SupplierSnapshot).filter(
            SupplierSnapshot.ruc == ruc,
            SupplierSnapshot.snapshot_date >= since
        ).order_by(SupplierSnapshot.snapshot_date.asc()).all()
        
        if len(snapshots) >= 2:
            scores = [s.risk_score for s in snapshots if s.risk_score is not None]
            if len(scores) >= 2:
                # Detectar cambios > 20 puntos
                for i in range(1, len(scores)):
                    diff = abs(scores[i] - scores[i-1])
                    if diff > 20:
                        anomalies.append({
                            "type": "score_drop",
                            "severity": "high" if diff > 30 else "medium",
                            "description": f"Cambio abrupto de score: {scores[i-1]:.0f} → {scores[i]:.0f} ({diff:+.0f} puntos)",
                            "detected_at": snapshots[i].snapshot_date.isoformat()
                        })
        
        # 2. Múltiples sanciones en corto tiempo
        recent_sanctions = self.db.query(SupplierChange).filter(
            SupplierChange.change_type == "sanction_added",
            SupplierChange.company_id == ruc,
            SupplierChange.created_at >= since
        ).count()
        
        if recent_sanctions >= 2:
            anomalies.append({
                "type": "multiple_sanctions",
                "severity": "critical",
                "description": f"{recent_sanctions} sanciones detectadas en los últimos 30 días",
                "count": recent_sanctions
            })
        
        # 3. Deuda en aumento acelerado
        if snapshots:
            raw_first = snapshots[0].raw_data or {}
            raw_last = snapshots[-1].raw_data or {}
            
            debt_first = raw_first.get("deuda_tributaria", 0)
            debt_last = raw_last.get("deuda_tributaria", 0)
            
            if debt_first and debt_last:
                debt_ratio = float(debt_last) / float(debt_first)
                if debt_ratio > 1.5:
                    anomalies.append({
                        "type": "debt_spike",
                        "severity": "high",
                        "description": f"Deuda aumentó {debt_ratio:.1f}x en el período",
                        "previous": debt_first,
                        "current": debt_last
                    })
        
        return anomalies


# Instancia singleton para uso rápido
_ml_service = None

def get_ml_service(db: Session = Depends(get_db)) -> MLScoringService:
    """Dependencia para obtener MLScoringService."""
    return MLScoringService(db)
