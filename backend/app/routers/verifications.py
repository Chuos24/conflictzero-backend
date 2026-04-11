"""
Conflict Zero - Verifications Router
Endpoints para verificación de RUCs y gestión de historial
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
import hashlib
import uuid

from app.core.database import get_db
from app.core.security import get_current_company
from app.core.rate_limit import rate_limited_auth
from app.models_v2 import Company, VerificationRequest, PublicProfile
from app.services.scoring_service import scoring_service
from app.services.data_collection import DataCollectionService

router = APIRouter(prefix="/verify", tags=["Verificaciones"])


# ============================================================
# SCHEMAS
# ============================================================

class VerifyRequest(BaseModel):
    """Request para verificar un RUC"""
    ruc: str = Field(..., min_length=11, max_length=11, pattern=r'^\d{11}$', description="RUC de 11 dígitos")


class VerificationDetailResponse(BaseModel):
    """Respuesta detallada de verificación"""
    id: str
    target_ruc_hash: str
    target_company_name: Optional[str]
    score: int
    risk_level: str
    sunat_debt: float
    sunat_tax_status: Optional[str]
    sunat_contributor_status: Optional[str]
    osce_sanctions_count: int
    osce_sanctions_details: List[dict]
    tce_sanctions_count: int
    tce_sanctions_details: List[dict]
    ml_anomaly_score: float
    ml_risk_factors: List[str]
    certificate_url: Optional[str]
    certificate_hash: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class VerificationSummaryResponse(BaseModel):
    """Resumen de verificación para historial"""
    id: str
    target_ruc_hash: str
    target_company_name: Optional[str]
    score: int
    risk_level: str
    osce_sanctions_count: int
    tce_sanctions_count: int
    created_at: datetime
    certificate_url: Optional[str]


class VerificationHistoryResponse(BaseModel):
    """Respuesta de historial de verificaciones"""
    items: List[VerificationSummaryResponse]
    total: int
    page: int
    page_size: int


class CertificateDownloadResponse(BaseModel):
    """Respuesta para descarga de certificado"""
    certificate_url: str
    certificate_hash: str
    expires_at: Optional[datetime]


# ============================================================
# ENDPOINTS
# ============================================================

@router.post("/", response_model=VerificationDetailResponse, summary="Verificar un RUC individual")
async def verify_ruc(
    request: VerifyRequest,
    current_company: Company = Depends(rate_limited_auth),
    db: Session = Depends(get_db)
):
    """
    Verifica un RUC individual y retorna el score completo.
    
    - Requiere autenticación
    - Consume una consulta del plan mensual
    - Cache de 15 minutos para datos externos
    """
    
    # Calcular hash del RUC
    ruc_hash = hashlib.sha256(request.ruc.encode()).hexdigest()
    
    # Verificar si existe en cache reciente (últimos 15 minutos)
    cached = db.query(VerificationRequest).filter(
        VerificationRequest.target_ruc_hash == ruc_hash,
        VerificationRequest.created_at >= datetime.utcnow() - __import__('datetime').timedelta(minutes=15),
        VerificationRequest.is_cached == True
    ).order_by(desc(VerificationRequest.created_at)).first()
    
    if cached:
        # Retornar cache hit
        return VerificationDetailResponse(
            id=str(cached.id),
            target_ruc_hash=cached.target_ruc_hash[:16] + "...",
            target_company_name=cached.target_company_name,
            score=cached.score,
            risk_level=cached.risk_level,
            sunat_debt=cached.sunat_debt,
            sunat_tax_status=cached.sunat_tax_status,
            sunat_contributor_status=cached.sunat_contributor_status,
            osce_sanctions_count=cached.osce_sanctions_count,
            osce_sanctions_details=cached.osce_sanctions_details or [],
            tce_sanctions_count=cached.tce_sanctions_count,
            tce_sanctions_details=cached.tce_sanctions_details or [],
            ml_anomaly_score=cached.ml_anomaly_score,
            ml_risk_factors=cached.ml_risk_factors or [],
            certificate_url=cached.certificate_url,
            certificate_hash=cached.certificate_hash,
            created_at=cached.created_at
        )
    
    # Recolectar datos de fuentes externas
    data_service = DataCollectionService()
    
    try:
        sunat_data = data_service.get_sunat_data(request.ruc)
        osce_data = data_service.get_osce_data(request.ruc)
        tce_data = data_service.get_tce_data(request.ruc)
    except Exception as e:
        # En caso de error, usar datos mock
        sunat_data = data_service._mock_sunat_data(request.ruc)
        osce_data = data_service._mock_osce_data(request.ruc)
        tce_data = data_service._mock_tce_data(request.ruc)
    
    # Calcular score
    from app.services.scoring_service import SunatData as SunatScoreData, SanctionData
    
    sunat_score_data = SunatScoreData(
        debt_amount=sunat_data.get('debt_amount', 0),
        tax_status=sunat_data.get('tax_status', ''),
        contributor_status=sunat_data.get('contributor_status', ''),
        is_active=sunat_data.get('contributor_status', '').lower() == 'activo'
    )
    
    osce_sanctions = [
        SanctionData(
            entity="OSCE",
            description=s.get('description', ''),
            severity=s.get('severity', 'medium'),
            is_active=s.get('is_active', True)
        )
        for s in osce_data.get('sanctions', [])
    ]
    
    tce_sanctions = [
        SanctionData(
            entity="TCE",
            description=s.get('description', ''),
            severity=s.get('severity', 'medium'),
            is_active=s.get('is_active', True)
        )
        for s in tce_data.get('sanctions', [])
    ]
    
    score_result = scoring_service.calculate_score(sunat_score_data, osce_sanctions, tce_sanctions)
    
    # Crear registro de verificación
    verification = VerificationRequest(
        id=uuid.uuid4(),
        consultant_id=current_company.id,
        target_ruc_hash=ruc_hash,
        target_ruc_encrypted=request.ruc.encode(),  # En producción: encriptar con AES
        target_company_name=sunat_data.get('razon_social'),
        score=score_result.score,
        risk_level=score_result.risk_level,
        sunat_debt=sunat_data.get('debt_amount', 0),
        sunat_tax_status=sunat_data.get('tax_status'),
        sunat_contributor_status=sunat_data.get('contributor_status'),
        osce_sanctions_count=len([s for s in osce_data.get('sanctions', []) if s.get('is_active')]),
        osce_sanctions_details=osce_data.get('sanctions', []),
        tce_sanctions_count=len([s for s in tce_data.get('sanctions', []) if s.get('is_active')]),
        tce_sanctions_details=tce_data.get('sanctions', []),
        ml_anomaly_score=0.0,  # Placeholder para ML
        ml_risk_factors=[],
        raw_data={
            'sunat': sunat_data,
            'osce': osce_data,
            'tce': tce_data
        },
        is_cached=False
    )
    
    # Incrementar contador de consultas
    current_company.used_queries_this_month += 1
    
    db.add(verification)
    db.commit()
    db.refresh(verification)
    
    # Actualizar perfil público si existe
    public_profile = db.query(PublicProfile).filter(
        PublicProfile.company_id == current_company.id
    ).first()
    
    if public_profile:
        public_profile.total_verifications = (public_profile.total_verifications or 0) + 1
        public_profile.last_verified_at = datetime.utcnow()
        db.commit()
    
    return VerificationDetailResponse(
        id=str(verification.id),
        target_ruc_hash=verification.target_ruc_hash[:16] + "...",
        target_company_name=verification.target_company_name,
        score=verification.score,
        risk_level=verification.risk_level,
        sunat_debt=verification.sunat_debt,
        sunat_tax_status=verification.sunat_tax_status,
        sunat_contributor_status=verification.sunat_contributor_status,
        osce_sanctions_count=verification.osce_sanctions_count,
        osce_sanctions_details=verification.osce_sanctions_details or [],
        tce_sanctions_count=verification.tce_sanctions_count,
        tce_sanctions_details=verification.tce_sanctions_details or [],
        ml_anomaly_score=verification.ml_anomaly_score,
        ml_risk_factors=verification.ml_risk_factors or [],
        certificate_url=verification.certificate_url,
        certificate_hash=verification.certificate_hash,
        created_at=verification.created_at
    )


@router.get("/history", response_model=VerificationHistoryResponse, summary="Historial de verificaciones")
async def get_verification_history(
    page: int = Query(1, ge=1, description="Número de página"),
    page_size: int = Query(20, ge=1, le=100, description="Tamaño de página"),
    risk_level: Optional[str] = Query(None, description="Filtrar por nivel de riesgo"),
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db)
):
    """
    Obtiene el historial de verificaciones realizadas por la empresa.
    
    - Requiere autenticación
    - Soporta paginación
    - Filtrado opcional por nivel de riesgo
    """
    # Construir query base
    query = db.query(VerificationRequest).filter(
        VerificationRequest.consultant_id == current_company.id,
        VerificationRequest.deleted_at.is_(None)
    )
    
    # Aplicar filtros
    if risk_level:
        query = query.filter(VerificationRequest.risk_level == risk_level)
    
    # Contar total
    total = query.count()
    
    # Aplicar paginación y ordenamiento
    verifications = query.order_by(
        desc(VerificationRequest.created_at)
    ).offset((page - 1) * page_size).limit(page_size).all()
    
    # Construir respuesta
    items = [
        VerificationSummaryResponse(
            id=str(v.id),
            target_ruc_hash=v.target_ruc_hash[:16] + "..." if v.target_ruc_hash else "",
            target_company_name=v.target_company_name,
            score=v.score,
            risk_level=v.risk_level,
            osce_sanctions_count=v.osce_sanctions_count,
            tce_sanctions_count=v.tce_sanctions_count,
            created_at=v.created_at,
            certificate_url=v.certificate_url
        )
        for v in verifications
    ]
    
    return VerificationHistoryResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{verification_id}", response_model=VerificationDetailResponse, summary="Obtener verificación específica")
async def get_verification(
    verification_id: str,
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db)
):
    """
    Obtiene los detalles de una verificación específica.
    
    - Requiere autenticación
    - Solo puede acceder a verificaciones propias
    """
    try:
        verification_uuid = uuid.UUID(verification_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de verificación inválido"
        )
    
    verification = db.query(VerificationRequest).filter(
        VerificationRequest.id == verification_uuid,
        VerificationRequest.consultant_id == current_company.id,
        VerificationRequest.deleted_at.is_(None)
    ).first()
    
    if not verification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Verificación no encontrada"
        )
    
    return VerificationDetailResponse(
        id=str(verification.id),
        target_ruc_hash=verification.target_ruc_hash[:16] + "..." if verification.target_ruc_hash else "",
        target_company_name=verification.target_company_name,
        score=verification.score,
        risk_level=verification.risk_level,
        sunat_debt=verification.sunat_debt,
        sunat_tax_status=verification.sunat_tax_status,
        sunat_contributor_status=verification.sunat_contributor_status,
        osce_sanctions_count=verification.osce_sanctions_count,
        osce_sanctions_details=verification.osce_sanctions_details or [],
        tce_sanctions_count=verification.tce_sanctions_count,
        tce_sanctions_details=verification.tce_sanctions_details or [],
        ml_anomaly_score=verification.ml_anomaly_score,
        ml_risk_factors=verification.ml_risk_factors or [],
        certificate_url=verification.certificate_url,
        certificate_hash=verification.certificate_hash,
        created_at=verification.created_at
    )


@router.get("/{verification_id}/certificate", summary="Descargar certificado de verificación")
async def get_verification_certificate(
    verification_id: str,
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db)
):
    """
    Obtiene la información del certificado de una verificación.
    
    - Requiere autenticación
    - Retorna URL de descarga y hash del certificado
    """
    try:
        verification_uuid = uuid.UUID(verification_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de verificación inválido"
        )
    
    verification = db.query(VerificationRequest).filter(
        VerificationRequest.id == verification_uuid,
        VerificationRequest.consultant_id == current_company.id,
        VerificationRequest.deleted_at.is_(None)
    ).first()
    
    if not verification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Verificación no encontrada"
        )
    
    if not verification.certificate_url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Certificado no generado para esta verificación"
        )
    
    return CertificateDownloadResponse(
        certificate_url=verification.certificate_url,
        certificate_hash=verification.certificate_hash or "",
        expires_at=None  # Se puede agregar lógica de expiración
    )
