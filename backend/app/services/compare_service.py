"""
Conflict Zero - Compare Service
Servicio para comparar múltiples empresas simultáneamente
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.services.data_collection import collect_multiple_rucs


class CompareResult:
    """Resultado de comparación entre empresas"""
    
    def __init__(self, companies_data: List[Dict], comparison: Dict[str, Any]):
        self.companies = companies_data
        self.comparison = comparison
        self.generated_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "companies": self.companies,
            "comparison": self.comparison,
            "generated_at": self.generated_at.isoformat()
        }


def validate_ruc_list(rucs: List[str]) -> tuple[List[str], List[Dict]]:
    """
    Valida lista de RUCs.
    
    Returns:
        (rucs_validos, errores)
    """
    valid_rucs = []
    errors = []
    
    for i, ruc in enumerate(rucs):
        # Limpiar
        ruc_clean = ruc.strip()
        
        # Validar longitud
        if len(ruc_clean) != 11:
            errors.append({
                "index": i,
                "ruc": ruc,
                "error": "RUC debe tener 11 dígitos"
            })
            continue
        
        # Validar que sean solo números
        if not ruc_clean.isdigit():
            errors.append({
                "index": i,
                "ruc": ruc,
                "error": "RUC debe contener solo números"
            })
            continue
        
        # Validar dígito verificador (simplificado)
        # En producción, usar validación completa de RUC peruano
        valid_rucs.append(ruc_clean)
    
    return valid_rucs, errors


def compare_companies(rucs: List[str], db: Session) -> Dict[str, Any]:
    """
    Compara múltiples empresas por sus RUCs.
    
    Args:
        rucs: Lista de RUCs (2-10)
        db: Sesión de base de datos
    
    Returns:
        Dict con comparación completa
    """
    # Validar cantidad
    if len(rucs) < 2:
        raise ValueError("Se requieren al menos 2 RUCs para comparar")
    
    if len(rucs) > 10:
        raise ValueError("Máximo 10 RUCs por comparación")
    
    # Validar RUCs
    valid_rucs, errors = validate_ruc_list(rucs)
    
    if not valid_rucs:
        return {
            "success": False,
            "error": "No se encontraron RUCs válidos",
            "validation_errors": errors
        }
    
    # Colectar datos
    data = collect_multiple_rucs(valid_rucs, db)
    
    return {
        "success": True,
        "rucs_processed": len(valid_rucs),
        "rucs_requested": len(rucs),
        "validation_errors": errors if errors else None,
        "data": data,
        "generated_at": datetime.utcnow().isoformat()
    }


def get_user_compare_limits(company) -> Dict[str, Any]:
    """
    Obtiene límites de comparación según el plan del usuario.
    """
    limits = {
        "bronze": {
            "max_per_comparison": 3,
            "comparisons_per_day": 5,
            "features": ["basic_comparison"]
        },
        "silver": {
            "max_per_comparison": 5,
            "comparisons_per_day": 20,
            "features": ["basic_comparison", "risk_analysis", "history"]
        },
        "gold": {
            "max_per_comparison": 10,
            "comparisons_per_day": 100,
            "features": ["basic_comparison", "risk_analysis", "history", "export_pdf", "api_access"]
        },
        "founder": {
            "max_per_comparison": 10,
            "comparisons_per_day": 999999,  # Ilimitado
            "features": ["basic_comparison", "risk_analysis", "history", "export_pdf", "api_access", "priority_support"]
        }
    }
    
    plan = company.plan_tier if company else "bronze"
    return limits.get(plan, limits["bronze"])


def generate_compare_report(data: Dict[str, Any], format: str = "json") -> Dict[str, Any]:
    """
    Genera reporte de comparación en formato solicitado.
    
    Args:
        data: Datos de comparación
        format: "json", "csv", "pdf"
    """
    if format == "json":
        return data
    
    elif format == "csv":
        # Generar CSV simple
        companies = data.get("data", {}).get("results", [])
        lines = ["RUC,Razon Social,Score,Risk Level,Deuda,Total Sanciones"]
        
        for company in companies:
            summary = company.get("summary", {})
            sunat = company.get("sunat", {})
            
            # Usar valores del cálculo de comparación
            ruc = summary.get("ruc", "")
            razon_social = summary.get("razon_social", "").replace(",", " ")
            
            lines.append(f"{ruc},{razon_social},-,-,{sunat.get('deuda', 0)},{summary.get('total_sanctions', 0)}")
        
        return {
            "format": "csv",
            "content": "\n".join(lines)
        }
    
    elif format == "pdf":
        # Placeholder - requiere implementación de generación PDF
        return {
            "format": "pdf",
            "message": "PDF generation not implemented in this version",
            "companies_count": len(data.get("data", {}).get("results", []))
        }
    
    else:
        raise ValueError(f"Formato no soportado: {format}")
