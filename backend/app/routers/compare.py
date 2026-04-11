"""
Conflict Zero - Compare Router
Endpoints para comparación de múltiples empresas
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator

from app.core.database import get_db
from app.core.security import get_current_company
from app.core.rate_limit import rate_limited_auth
from app.services.compare_service import (
    compare_companies, 
    get_user_compare_limits,
    generate_compare_report
)
from app.models_v2 import Company

router = APIRouter(prefix="/compare", tags=["Comparación"])


class CompareRequest(BaseModel):
    """Request para comparar múltiples RUCs"""
    rucs: List[str] = Field(..., min_length=2, max_length=10, description="Lista de RUCs a comparar")
    format: Optional[str] = Field("json", pattern="^(json|csv|pdf)$")
    
    @field_validator('rucs')
    @classmethod
    def validate_rucs(cls, v):
        if len(v) < 2:
            raise ValueError('Se requieren al menos 2 RUCs')
        if len(v) > 10:
            raise ValueError('Máximo 10 RUCs permitidos')
        # Validar formato de cada RUC
        for ruc in v:
            if not ruc.isdigit() or len(ruc) != 11:
                raise ValueError(f'RUC inválido: {ruc}. Debe tener 11 dígitos.')
        return v


class CompareLimitsResponse(BaseModel):
    """Respuesta con límites de comparación"""
    plan: str
    max_per_comparison: int
    comparisons_per_day: int
    features: List[str]


@router.post("/", summary="Comparar múltiples empresas")
async def compare_rucs(
    request: CompareRequest,
    current_company: Company = Depends(rate_limited_auth),
    db: Session = Depends(get_db)
):
    """
    Compara 2-10 empresas simultáneamente.
    
    - Requiere autenticación
    - Los límites dependen del plan del usuario
    - Cache de 15 minutos para datos externos
    """
    # Verificar límites según plan
    limits = get_user_compare_limits(current_company)
    
    if len(request.rucs) > limits["max_per_comparison"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Tu plan permite comparar máximo {limits['max_per_comparison']} empresas. "
                   f"Solicitaste: {len(request.rucs)}"
        )
    
    try:
        # Realizar comparación
        result = compare_companies(request.rucs, db)
        
        # Generar reporte en formato solicitado
        if request.format != "json":
            report = generate_compare_report(result, request.format)
            return {
                "success": True,
                "report": report,
                "limits_used": {
                    "rucs_compared": len(request.rucs),
                    "max_allowed": limits["max_per_comparison"]
                }
            }
        
        return {
            "success": True,
            **result,
            "limits_used": {
                "rucs_compared": len(request.rucs),
                "max_allowed": limits["max_per_comparison"]
            }
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al procesar comparación: {str(e)}"
        )


@router.get("/limits", summary="Obtener límites de comparación")
async def get_compare_limits(
    current_company: Company = Depends(get_current_company)
):
    """
    Retorna los límites de comparación según el plan del usuario actual.
    """
    limits = get_user_compare_limits(current_company)
    
    return CompareLimitsResponse(
        plan=current_company.plan_tier,
        max_per_comparison=limits["max_per_comparison"],
        comparisons_per_day=limits["comparisons_per_day"],
        features=limits["features"]
    )


@router.post("/validate", summary="Validar RUCs para comparación")
async def validate_rucs_for_compare(
    rucs: List[str],
    current_company: Company = Depends(get_current_company)
):
    """
    Valida una lista de RUCs sin realizar la comparación completa.
    Útil para pre-validación en el frontend.
    """
    from app.services.compare_service import validate_ruc_list
    
    limits = get_user_compare_limits(current_company)
    
    valid_rucs, errors = validate_ruc_list(rucs)
    
    return {
        "valid": len(errors) == 0,
        "valid_count": len(valid_rucs),
        "invalid_count": len(errors),
        "max_allowed": limits["max_per_comparison"],
        "valid_rucs": valid_rucs,
        "errors": errors
    }
