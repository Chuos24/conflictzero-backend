"""
Conflict Zero - Mi Red (Supplier Network) Router
Endpoints para monitoreo continuo de proveedores
"""

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
import uuid

from app.core.database import get_db
from app.core.security import get_current_company
from app.models_v2 import Company
from app.models_network import SupplierNetwork, SupplierAlert, CompanySnapshot

router = APIRouter(prefix="/network", tags=["Mi Red - Supplier Network"])


# ============================================================
# SCHEMAS
# ============================================================

class SupplierAddRequest(BaseModel):
    ruc: str = Field(..., min_length=11, max_length=11, description="RUC del proveedor a monitorear")
    company_name: Optional[str] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = []
    alert_on_score_change: bool = True
    alert_on_new_sanction: bool = True
    alert_on_debt_increase: bool = True
    alert_threshold: int = Field(default=10, ge=0, le=100)


class SupplierUpdateRequest(BaseModel):
    notes: Optional[str] = None
    tags: Optional[List[str]] = None
    alert_on_score_change: Optional[bool] = None
    alert_on_new_sanction: Optional[bool] = None
    alert_on_debt_increase: Optional[bool] = None
    alert_threshold: Optional[int] = Field(None, ge=0, le=100)
    is_active: Optional[bool] = None


class SupplierResponse(BaseModel):
    id: str
    supplier_ruc_hash: str
    supplier_company_name: Optional[str]
    is_active: bool
    last_verified_at: Optional[datetime]
    created_at: datetime
    notes: Optional[str]
    tags: List[str]
    alert_on_score_change: bool
    alert_on_new_sanction: bool
    alert_on_debt_increase: bool
    alert_threshold: int


class AlertResponse(BaseModel):
    id: str
    supplier_company_name: str
    alert_type: str
    severity: str
    previous_score: Optional[int]
    new_score: Optional[int]
    previous_risk_level: Optional[str]
    new_risk_level: Optional[str]
    change_details: dict
    is_read: bool
    created_at: datetime


class AlertListResponse(BaseModel):
    alerts: List[AlertResponse]
    unread_count: int
    total_count: int


class NetworkStatsResponse(BaseModel):
    total_suppliers: int
    active_suppliers: int
    suppliers_with_alerts: int
    unread_alerts: int
    total_alerts_30d: int


# ============================================================
# ENDPOINTS
# ============================================================

@router.get("/", response_model=List[SupplierResponse])
async def list_network_suppliers(
    active_only: bool = Query(True, description="Solo proveedores activos"),
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_company)
):
    """
    Lista todos los proveedores en la red del usuario autenticado.
    """
    query = db.query(SupplierNetwork).filter(
        SupplierNetwork.company_id == current_company.id,
        SupplierNetwork.deleted_at.is_(None)
    )
    
    if active_only:
        query = query.filter(SupplierNetwork.is_active == True)
    
    suppliers = query.order_by(SupplierNetwork.created_at.desc()).all()
    
    return [
        SupplierResponse(
            id=str(s.id),
            supplier_ruc_hash=s.supplier_ruc_hash,
            supplier_company_name=s.supplier_company_name,
            is_active=s.is_active,
            last_verified_at=s.last_verified_at,
            created_at=s.created_at,
            notes=s.notes,
            tags=s.tags or [],
            alert_on_score_change=s.alert_on_score_change,
            alert_on_new_sanction=s.alert_on_new_sanction,
            alert_on_debt_increase=s.alert_on_debt_increase,
            alert_threshold=s.alert_threshold
        )
        for s in suppliers
    ]


@router.post("/add", response_model=SupplierResponse, status_code=201)
async def add_supplier_to_network(
    request: SupplierAddRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_company)
):
    """
    Agrega un proveedor a la red de monitoreo del usuario.
    
    - Verifica que el RUC sea válido
    - Crea el registro de monitoreo
    - Inicia verificación inicial en background
    """
    from app.models_v2 import hash_ruc
    
    # Validar RUC
    if not request.ruc.isdigit() or len(request.ruc) != 11:
        raise HTTPException(400, detail="RUC inválido. Debe contener 11 dígitos.")
    
    ruc_hash = hash_ruc(request.ruc)
    
    # Verificar si ya existe en la red
    existing = db.query(SupplierNetwork).filter(
        SupplierNetwork.company_id == current_company.id,
        SupplierNetwork.supplier_ruc_hash == ruc_hash,
        SupplierNetwork.deleted_at.is_(None)
    ).first()
    
    if existing:
        raise HTTPException(409, detail="Este proveedor ya está en tu red de monitoreo.")
    
    # Verificar límites del plan
    current_count = db.query(SupplierNetwork).filter(
        SupplierNetwork.company_id == current_company.id,
        SupplierNetwork.deleted_at.is_(None),
        SupplierNetwork.is_active == True
    ).count()
    
    # Límites por plan (usar plan_tier o plan_type según el modelo)
    max_suppliers = {
        'bronze': 10,
        'silver': 50,
        'gold': 200,
        'founder': 500
    }.get(current_company.plan_tier, 10)
    
    if current_count >= max_suppliers:
        raise HTTPException(403, detail=f"Límite de proveedores alcanzado ({max_suppliers}). Actualiza tu plan.")
    
    # Crear registro
    # Nota: en producción, aquí deberíamos encriptar el RUC
    from app.core.security import encrypt_ruc, decrypt_ruc
    
    supplier = SupplierNetwork(
        company_id=current_company.id,
        supplier_ruc_hash=ruc_hash,
        supplier_ruc_encrypted=encrypt_ruc(request.ruc),
        supplier_company_name=request.company_name or f"Proveedor {request.ruc[-4:]}",
        notes=request.notes,
        tags=request.tags or [],
        alert_on_score_change=request.alert_on_score_change,
        alert_on_new_sanction=request.alert_on_new_sanction,
        alert_on_debt_increase=request.alert_on_debt_increase,
        alert_threshold=request.alert_threshold,
        is_active=True
    )
    
    db.add(supplier)
    db.commit()
    db.refresh(supplier)
    
    # En producción: iniciar verificación inicial en background
    # background_tasks.add_task(verify_supplier_initial, supplier.id, request.ruc)
    
    return SupplierResponse(
        id=str(supplier.id),
        supplier_ruc_hash=supplier.supplier_ruc_hash,
        supplier_company_name=supplier.supplier_company_name,
        is_active=supplier.is_active,
        last_verified_at=supplier.last_verified_at,
        created_at=supplier.created_at,
        notes=supplier.notes,
        tags=supplier.tags or [],
        alert_on_score_change=supplier.alert_on_score_change,
        alert_on_new_sanction=supplier.alert_on_new_sanction,
        alert_on_debt_increase=supplier.alert_on_debt_increase,
        alert_threshold=supplier.alert_threshold
    )


@router.get("/{supplier_id}", response_model=SupplierResponse)
async def get_supplier_details(
    supplier_id: str,
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_company)
):
    """
    Obtiene detalles de un proveedor específico en la red.
    """
    try:
        supplier_uuid = uuid.UUID(supplier_id)
    except ValueError:
        raise HTTPException(400, detail="ID inválido")
    
    supplier = db.query(SupplierNetwork).filter(
        SupplierNetwork.id == supplier_uuid,
        SupplierNetwork.company_id == current_company.id,
        SupplierNetwork.deleted_at.is_(None)
    ).first()
    
    if not supplier:
        raise HTTPException(404, detail="Proveedor no encontrado")
    
    return SupplierResponse(
        id=str(supplier.id),
        supplier_ruc_hash=supplier.supplier_ruc_hash,
        supplier_company_name=supplier.supplier_company_name,
        is_active=supplier.is_active,
        last_verified_at=supplier.last_verified_at,
        created_at=supplier.created_at,
        notes=supplier.notes,
        tags=supplier.tags or [],
        alert_on_score_change=supplier.alert_on_score_change,
        alert_on_new_sanction=supplier.alert_on_new_sanction,
        alert_on_debt_increase=supplier.alert_on_debt_increase,
        alert_threshold=supplier.alert_threshold
    )


@router.patch("/{supplier_id}", response_model=SupplierResponse)
async def update_supplier(
    supplier_id: str,
    request: SupplierUpdateRequest,
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_company)
):
    """
    Actualiza configuración de un proveedor monitoreado.
    """
    try:
        supplier_uuid = uuid.UUID(supplier_id)
    except ValueError:
        raise HTTPException(400, detail="ID inválido")
    
    supplier = db.query(SupplierNetwork).filter(
        SupplierNetwork.id == supplier_uuid,
        SupplierNetwork.company_id == current_company.id,
        SupplierNetwork.deleted_at.is_(None)
    ).first()
    
    if not supplier:
        raise HTTPException(404, detail="Proveedor no encontrado")
    
    # Actualizar campos
    if request.notes is not None:
        supplier.notes = request.notes
    if request.tags is not None:
        supplier.tags = request.tags
    if request.alert_on_score_change is not None:
        supplier.alert_on_score_change = request.alert_on_score_change
    if request.alert_on_new_sanction is not None:
        supplier.alert_on_new_sanction = request.alert_on_new_sanction
    if request.alert_on_debt_increase is not None:
        supplier.alert_on_debt_increase = request.alert_on_debt_increase
    if request.alert_threshold is not None:
        supplier.alert_threshold = request.alert_threshold
    if request.is_active is not None:
        supplier.is_active = request.is_active
    
    supplier.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(supplier)
    
    return SupplierResponse(
        id=str(supplier.id),
        supplier_ruc_hash=supplier.supplier_ruc_hash,
        supplier_company_name=supplier.supplier_company_name,
        is_active=supplier.is_active,
        last_verified_at=supplier.last_verified_at,
        created_at=supplier.created_at,
        notes=supplier.notes,
        tags=supplier.tags or [],
        alert_on_score_change=supplier.alert_on_score_change,
        alert_on_new_sanction=supplier.alert_on_new_sanction,
        alert_on_debt_increase=supplier.alert_on_debt_increase,
        alert_threshold=supplier.alert_threshold
    )


@router.delete("/{supplier_id}", status_code=204)
async def remove_supplier_from_network(
    supplier_id: str,
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_company)
):
    """
    Elimina un proveedor de la red de monitoreo (soft delete).
    """
    try:
        supplier_uuid = uuid.UUID(supplier_id)
    except ValueError:
        raise HTTPException(400, detail="ID inválido")
    
    supplier = db.query(SupplierNetwork).filter(
        SupplierNetwork.id == supplier_uuid,
        SupplierNetwork.company_id == current_company.id,
        SupplierNetwork.deleted_at.is_(None)
    ).first()
    
    if not supplier:
        raise HTTPException(404, detail="Proveedor no encontrado")
    
    supplier.soft_delete()
    db.commit()
    
    return None


@router.get("/alerts", response_model=AlertListResponse)
async def list_alerts(
    unread_only: bool = Query(False, description="Solo alertas no leídas"),
    severity: Optional[str] = Query(None, description="Filtrar por severidad: low, medium, high, critical"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_company)
):
    """
    Lista las alertas de cambios en proveedores monitoreados.
    """
    query = db.query(SupplierAlert).filter(
        SupplierAlert.company_id == current_company.id,
        SupplierAlert.deleted_at.is_(None)
    )
    
    if unread_only:
        query = query.filter(SupplierAlert.is_read == False)
    
    if severity:
        query = query.filter(SupplierAlert.severity == severity)
    
    total_count = query.count()
    unread_count = db.query(SupplierAlert).filter(
        SupplierAlert.company_id == current_company.id,
        SupplierAlert.is_read == False,
        SupplierAlert.deleted_at.is_(None)
    ).count()
    
    alerts = query.order_by(SupplierAlert.created_at.desc()).offset(offset).limit(limit).all()
    
    return AlertListResponse(
        alerts=[
            AlertResponse(
                id=str(a.id),
                supplier_company_name=a.supplier_company_name,
                alert_type=a.alert_type,
                severity=a.severity,
                previous_score=a.previous_score,
                new_score=a.new_score,
                previous_risk_level=a.previous_risk_level,
                new_risk_level=a.new_risk_level,
                change_details=a.change_details or {},
                is_read=a.is_read,
                created_at=a.created_at
            )
            for a in alerts
        ],
        unread_count=unread_count,
        total_count=total_count
    )


@router.patch("/alerts/{alert_id}/read", response_model=AlertResponse)
async def mark_alert_as_read(
    alert_id: str,
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_company)
):
    """
    Marca una alerta específica como leída.
    """
    try:
        alert_uuid = uuid.UUID(alert_id)
    except ValueError:
        raise HTTPException(400, detail="ID inválido")
    
    alert = db.query(SupplierAlert).filter(
        SupplierAlert.id == alert_uuid,
        SupplierAlert.company_id == current_company.id,
        SupplierAlert.deleted_at.is_(None)
    ).first()
    
    if not alert:
        raise HTTPException(404, detail="Alerta no encontrada")
    
    alert.mark_as_read()
    db.commit()
    
    return AlertResponse(
        id=str(alert.id),
        supplier_company_name=alert.supplier_company_name,
        alert_type=alert.alert_type,
        severity=alert.severity,
        previous_score=alert.previous_score,
        new_score=alert.new_score,
        previous_risk_level=alert.previous_risk_level,
        new_risk_level=alert.new_risk_level,
        change_details=alert.change_details or {},
        is_read=alert.is_read,
        created_at=alert.created_at
    )


@router.post("/alerts/mark-all-read", status_code=200)
async def mark_all_alerts_as_read(
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_company)
):
    """
    Marca todas las alertas como leídas.
    """
    now = datetime.utcnow()
    
    db.query(SupplierAlert).filter(
        SupplierAlert.company_id == current_company.id,
        SupplierAlert.is_read == False,
        SupplierAlert.deleted_at.is_(None)
    ).update({
        'is_read': True,
        'read_at': now
    }, synchronize_session=False)
    
    db.commit()
    
    return {"message": "Todas las alertas han sido marcadas como leídas", "marked_at": now.isoformat()}


@router.get("/stats/dashboard", response_model=NetworkStatsResponse)
async def get_network_stats(
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_company)
):
    """
    Obtiene estadísticas de la red de proveedores.
    """
    from datetime import timedelta
    
    total_suppliers = db.query(SupplierNetwork).filter(
        SupplierNetwork.company_id == current_company.id,
        SupplierNetwork.deleted_at.is_(None)
    ).count()
    
    active_suppliers = db.query(SupplierNetwork).filter(
        SupplierNetwork.company_id == current_company.id,
        SupplierNetwork.deleted_at.is_(None),
        SupplierNetwork.is_active == True
    ).count()
    
    # Proveedores con alertas no leídas en los últimos 30 días
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    
    suppliers_with_alerts = db.query(SupplierAlert.supplier_ruc_hash).filter(
        SupplierAlert.company_id == current_company.id,
        SupplierAlert.created_at >= thirty_days_ago,
        SupplierAlert.deleted_at.is_(None)
    ).distinct().count()
    
    unread_alerts = db.query(SupplierAlert).filter(
        SupplierAlert.company_id == current_company.id,
        SupplierAlert.is_read == False,
        SupplierAlert.deleted_at.is_(None)
    ).count()
    
    total_alerts_30d = db.query(SupplierAlert).filter(
        SupplierAlert.company_id == current_company.id,
        SupplierAlert.created_at >= thirty_days_ago,
        SupplierAlert.deleted_at.is_(None)
    ).count()
    
    return NetworkStatsResponse(
        total_suppliers=total_suppliers,
        active_suppliers=active_suppliers,
        suppliers_with_alerts=suppliers_with_alerts,
        unread_alerts=unread_alerts,
        total_alerts_30d=total_alerts_30d
    )


# ============================================================
# UTILIDADES PARA BACKGROUND TASKS
# ============================================================

async def verify_supplier_initial(supplier_id: uuid.UUID, ruc: str):
    """
    Realiza verificación inicial de un proveedor agregado.
    Esta función se ejecuta en background.
    """
    # TODO: Implementar integración con servicios de verificación
    pass
