"""
Conflict Zero - Scoring Service
Cálculo de score de riesgo basado en SUNAT, OSCE, TCE
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class SunatData:
    debt_amount: float = 0
    tax_status: str = ""
    contributor_status: str = ""
    is_active: bool = True


@dataclass
class SanctionData:
    entity: str  # OSCE, TCE
    description: str
    severity: str  # low, medium, high
    is_active: bool = True


@dataclass
class ScoreResult:
    score: int  # 0-100
    risk_level: RiskLevel
    breakdown: Dict[str, float]
    recommendations: List[str]


class ScoringService:
    """
    Servicio de cálculo de score de riesgo.
    
    Fórmula:
    - Base: 100 puntos
    - SUNAT deuda: -5 a -30 puntos
    - OSCE sanciones: -10 a -25 cada una
    - TCE sanciones: -15 a -30 cada una
    - Estado contribuyente: -20 si no es activo
    """
    
    def __init__(self):
        self.weights = {
            "sunat_debt": 0.30,
            "sunat_status": 0.20,
            "osce_sanctions": 0.25,
            "tce_sanctions": 0.25
        }
    
    def calculate_score(
        self,
        sunat_data: SunatData,
        osce_sanctions: List[SanctionData],
        tce_sanctions: List[SanctionData]
    ) -> ScoreResult:
        """
        Calcula el score de riesgo completo.
        """
        score = 100.0
        breakdown = {}
        recommendations = []
        
        # 1. Deuda SUNAT (max -30 puntos)
        sunat_debt_penalty = self._calculate_sunat_debt_penalty(sunat_data.debt_amount)
        score -= sunat_debt_penalty
        breakdown["sunat_debt"] = -sunat_debt_penalty
        
        if sunat_data.debt_amount > 100000:
            recommendations.append("Alta deuda tributaria detectada - verificar plan de pagos")
        
        # 2. Estado del contribuyente (max -20 puntos)
        status_penalty = 0
        if sunat_data.contributor_status.lower() not in ["activo", ""]:
            status_penalty = 20
            score -= status_penalty
            recommendations.append("Contribuyente no está activo en SUNAT")
        breakdown["sunat_status"] = -status_penalty
        
        # 3. Sanciones OSCE (max -25 cada una, hasta -50)
        osce_penalty = 0
        active_osce = [s for s in osce_sanctions if s.is_active]
        for sanction in active_osce[:2]:  # Máximo 2 sanciones consideradas
            penalty = self._calculate_sanction_penalty(sanction, "osce")
            osce_penalty += penalty
        osce_penalty = min(osce_penalty, 50)  # Cap a 50 puntos
        score -= osce_penalty
        breakdown["osce_sanctions"] = -osce_penalty
        
        if active_osce:
            recommendations.append(f"{len(active_osce)} sanción(es) activa(s) en OSCE")
        
        # 4. Sanciones TCE (max -30 cada una, hasta -60)
        tce_penalty = 0
        active_tce = [s for s in tce_sanctions if s.is_active]
        for sanction in active_tce[:2]:  # Máximo 2 sanciones consideradas
            penalty = self._calculate_sanction_penalty(sanction, "tce")
            tce_penalty += penalty
        tce_penalty = min(tce_penalty, 60)  # Cap a 60 puntos
        score -= tce_penalty
        breakdown["tce_sanctions"] = -tce_penalty
        
        if active_tce:
            recommendations.append(f"{len(active_tce)} sanción(es) activa(s) en TCE")
        
        # Asegurar rango 0-100
        score = max(0, min(100, score))
        
        # Determinar nivel de riesgo
        risk_level = self._get_risk_level(score, active_osce, active_tce)
        
        # Recomendaciones adicionales basadas en score
        if score >= 90:
            recommendations.append("Empresa con excelente cumplimiento - riesgo mínimo")
        elif score >= 70:
            recommendations.append("Cumplimiento aceptable - monitoreo estándar recomendado")
        elif score >= 50:
            recommendations.append("Riesgo moderado - verificar documentación adicional")
        else:
            recommendations.append("ALTO RIESGO - Se recomienda debida diligencia extendida")
        
        return ScoreResult(
            score=int(score),
            risk_level=risk_level,
            breakdown=breakdown,
            recommendations=recommendations
        )
    
    def _calculate_sunat_debt_penalty(self, debt_amount: float) -> float:
        """
        Calcula penalización por deuda SUNAT.
        """
        if debt_amount == 0:
            return 0
        elif debt_amount < 10000:
            return 5
        elif debt_amount < 50000:
            return 10
        elif debt_amount < 100000:
            return 20
        else:
            return 30
    
    def _calculate_sanction_penalty(self, sanction: SanctionData, entity: str) -> float:
        """
        Calcula penalización por sanción.
        """
        base_penalty = {
            "osce": {"low": 10, "medium": 15, "high": 25},
            "tce": {"low": 15, "medium": 20, "high": 30}
        }
        
        return base_penalty.get(entity, {}).get(sanction.severity.lower(), 10)
    
    def _get_risk_level(
        self,
        score: float,
        osce_sanctions: List[SanctionData],
        tce_sanctions: List[SanctionData]
    ) -> RiskLevel:
        """
        Determina el nivel de riesgo basado en score y sanciones.
        """
        # CRITICAL: Score < 50 O tiene sanciones TCE activas
        if score < 50 or tce_sanctions:
            return RiskLevel.CRITICAL
        
        # HIGH: Score < 70 O tiene sanciones OSCE activas
        if score < 70 or osce_sanctions:
            return RiskLevel.HIGH
        
        # MEDIUM: Score < 85
        if score < 85:
            return RiskLevel.MEDIUM
        
        # LOW: Score >= 85
        return RiskLevel.LOW
    
    def get_tier_from_score(self, score: int) -> str:
        """
        Determina el tier del sello basado en score.
        """
        if score >= 90:
            return "gold"
        elif score >= 75:
            return "silver"
        elif score >= 60:
            return "bronze"
        else:
            return "expired"


# Singleton
scoring_service = ScoringService()

def get_scoring_service() -> ScoringService:
    return scoring_service
