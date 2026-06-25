"""
Audit Router
Endpoints para generación y gestión de reportes de auditoría y GDPR.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse, StreamingResponse
from datetime import datetime, timedelta, timezone
from typing import Optional, List
from sqlalchemy.orm import Session
from io import BytesIO

from app.core.database import get_db
from app.core.security import get_current_company, get_current_admin
from app.services.audit_service import (
    AuditReportGenerator,
    AuditReportType,
    AuditScheduler,
    AuditReportService
)
from app.services.pdf_service import pdf_generator
from app.core.gdpr import GDPRComplianceService, DataSubjectRight

router = APIRouter(prefix="/audit", tags=["audit"])


# ============================================================
# REPORTES DE AUDITORÍA
# ============================================================

@router.post("/reports/compliance")
async def generate_compliance_report(
    start_date: datetime = Query(..., description="Fecha inicio (ISO 8601)"),
    end_date: datetime = Query(..., description="Fecha fin (ISO 8601)"),
    db: Session = Depends(get_db),
    current_company: dict = Depends(get_current_company)
):
    """
    Genera reporte de compliance del programa Founder.
    
    Requiere: Autenticación + Rol admin o founder
    """
    report = AuditReportGenerator.generate_compliance_report(
        company_id=current_company.id,
        start_date=start_date,
        end_date=end_date,
        db=db
    )
    
    # Guardar en DB
    saved = AuditReportService.create_report_db(db, report)
    
    return {
        "report_id": report.report_id,
        "type": report.report_type.value,
        "status": report.status,
        "period": {
            "start": report.start_date.isoformat(),
            "end": report.end_date.isoformat()
        },
        "saved_to_db": saved is not None,
        "data": report.data
    }


@router.post("/reports/security")
async def generate_security_report(
    start_date: datetime = Query(default=None, description="Fecha inicio"),
    end_date: datetime = Query(default=None, description="Fecha fin"),
    db: Session = Depends(get_db),
    current_company: dict = Depends(get_current_company)
):
    """
    Genera reporte de eventos de seguridad.
    
    Período por defecto: últimos 7 días
    """
    end = end_date or datetime.now(timezone.utc)
    start = start_date or (end - timedelta(days=7))
    
    report = AuditReportGenerator.generate_security_report(
        company_id=current_company.id,
        start_date=start,
        end_date=end,
        db=db
    )
    
    saved = AuditReportService.create_report_db(db, report)
    
    return {
        "report_id": report.report_id,
        "type": report.report_type.value,
        "status": report.status,
        "period": {
            "start": report.start_date.isoformat(),
            "end": report.end_date.isoformat()
        },
        "saved_to_db": saved is not None,
        "data": report.data
    }


@router.post("/reports/data-processing")
async def generate_data_processing_report(
    start_date: datetime = Query(default=None),
    end_date: datetime = Query(default=None),
    db: Session = Depends(get_db),
    current_company: dict = Depends(get_current_company)
):
    """
    Genera reporte de procesamiento de datos (GDPR/LGPD).
    """
    end = end_date or datetime.now(timezone.utc)
    start = start_date or (end - timedelta(days=90))  # Trimestral por defecto
    
    report = AuditReportGenerator.generate_data_processing_report(
        company_id=current_company.id,
        start_date=start,
        end_date=end,
        db=db
    )
    
    saved = AuditReportService.create_report_db(db, report)
    
    return {
        "report_id": report.report_id,
        "type": report.report_type.value,
        "status": report.status,
        "period": {
            "start": report.start_date.isoformat(),
            "end": report.end_date.isoformat()
        },
        "saved_to_db": saved is not None,
        "data": report.data
    }


@router.post("/reports/network-changes")
async def generate_network_changes_report(
    start_date: datetime = Query(default=None),
    end_date: datetime = Query(default=None),
    db: Session = Depends(get_db),
    current_company: dict = Depends(get_current_company)
):
    """
    Genera reporte de cambios en red de proveedores.
    """
    end = end_date or datetime.now(timezone.utc)
    start = start_date or (end - timedelta(days=1))  # Diario por defecto
    
    report = AuditReportGenerator.generate_network_changes_report(
        company_id=current_company.id,
        start_date=start,
        end_date=end,
        db=db
    )
    
    saved = AuditReportService.create_report_db(db, report)
    
    return {
        "report_id": report.report_id,
        "type": report.report_type.value,
        "status": report.status,
        "period": {
            "start": report.start_date.isoformat(),
            "end": report.end_date.isoformat()
        },
        "saved_to_db": saved is not None,
        "data": report.data
    }


@router.get("/reports")
async def list_audit_reports(
    report_type: Optional[AuditReportType] = Query(None, description="Filtrar por tipo"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_company: dict = Depends(get_current_company)
):
    """
    Lista reportes de auditoría generados.
    
    Returns:
        Lista de reportes con metadatos
    """
    reports = AuditReportService.get_reports_by_company(
        db, 
        company_id=current_company.id,
        report_type=report_type.value if report_type else None
    )
    
    return {
        "reports": reports[offset:offset + limit],
        "total": len(reports),
        "limit": limit,
        "offset": offset
    }


@router.get("/reports/{report_number}")
async def get_audit_report(
    report_number: str,
    db: Session = Depends(get_db),
    current_company: dict = Depends(get_current_company)
):
    """
    Obtiene un reporte de auditoría específico por su número.
    """
    report = AuditReportService.get_report_by_number(db, report_number)
    
    if not report:
        raise HTTPException(status_code=404, detail="Reporte no encontrado")
    
    # Verificar que pertenece a la empresa actual
    if report["company_id"] != str(current_company.id):
        raise HTTPException(status_code=403, detail="No tienes acceso a este reporte")
    
    return report


@router.post("/reports/{report_number}/sign")
async def sign_audit_report(
    report_number: str,
    db: Session = Depends(get_db),
    current_company: dict = Depends(get_current_company)
):
    """
    Firma un reporte de auditoría para garantizar integridad.
    
    Una vez firmado, el reporte no puede modificarse.
    """
    # Verificar que el reporte existe y pertenece a la empresa
    report = AuditReportService.get_report_by_number(db, report_number)
    if not report:
        raise HTTPException(status_code=404, detail="Reporte no encontrado")
    
    if report["company_id"] != str(current_company.id):
        raise HTTPException(status_code=403, detail="No tienes acceso a este reporte")
    
    # Firmar
    signature = AuditReportService.sign_report_db(
        db, 
        report_number=report_number,
        signed_by=getattr(current_company, 'email', 'user'),
        signed_by_type="user"
    )
    
    if not signature:
        raise HTTPException(status_code=500, detail="Error al firmar el reporte")
    
    return {
        "report_number": report_number,
        "status": "signed",
        "signed_by": signature["signed_by"],
        "signed_by_type": signature["signed_by_type"],
        "signature_hash": signature["signature_hash"],
        "signed_at": signature["verified_at"]
    }


@router.get("/schedule")
async def get_audit_schedule(
    current_company: dict = Depends(get_current_company)
):
    """
    Obtiene el calendario de auditorías programadas.
    
    Returns:
        Próximas fechas de generación automática de reportes
    """
    return {
        "schedule": AuditScheduler.get_schedule_calendar()
    }


# ============================================================
# GDPR ENDPOINTS
# ============================================================

@router.post("/gdpr/requests")
async def create_gdpr_request(
    request_type: DataSubjectRight = Query(..., description="Tipo de solicitud GDPR"),
    description: Optional[str] = Query(None, description="Descripción de la solicitud"),
    db: Session = Depends(get_db),
    current_company: dict = Depends(get_current_company)
):
    """
    Crea una nueva solicitud GDPR (Art. 15-21).
    
    Tipos de solicitud:
    - access: Derecho de acceso (Art. 15)
    - rectification: Derecho de rectificación (Art. 16)
    - erasure: Derecho al olvido (Art. 17)
    - portability: Derecho a la portabilidad (Art. 20)
    - objection: Derecho de oposición (Art. 21)
    - restriction: Derecho a la limitación (Art. 18)
    """
    contact_email = getattr(current_company, 'contact_email', '')
    
    result = GDPRComplianceService.create_request(
        db=db,
        company_id=current_company.id,
        request_type=request_type.value,
        contact_email=contact_email,
        description=description
    )
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al crear la solicitud GDPR"
        )
    
    return {
        "status": "created",
        "request": result,
        "message": f"Solicitud {request_type.value} recibida. Será procesada en un máximo de 30 días."
    }


@router.get("/gdpr/requests")
async def list_gdpr_requests(
    status: Optional[str] = Query(None, description="Filtrar por estado"),
    db: Session = Depends(get_db),
    current_company: dict = Depends(get_current_company)
):
    """
    Lista las solicitudes GDPR de la empresa.
    """
    requests = GDPRComplianceService.get_requests_by_company(
        db,
        company_id=current_company.id,
        status=status
    )
    
    return {
        "requests": requests,
        "total": len(requests)
    }


@router.get("/gdpr/requests/pending")
async def get_pending_gdpr_requests(
    db: Session = Depends(get_db),
    current_company: dict = Depends(get_current_company)
):
    """
    Obtiene el número de solicitudes GDPR pendientes.
    """
    count = GDPRComplianceService.get_pending_requests_count(db)
    
    return {
        "pending_count": count
    }


@router.get("/gdpr/requests/overdue")
async def get_overdue_gdpr_requests(
    db: Session = Depends(get_db),
    current_company: dict = Depends(get_current_company)
):
    """
    Obtiene solicitudes GDPR vencidas (más de 30 días sin responder).
    """
    overdue = GDPRComplianceService.get_overdue_requests(db)
    
    return {
        "overdue_requests": overdue,
        "total_overdue": len(overdue)
    }


@router.get("/gdpr/export")
async def export_personal_data(
    db: Session = Depends(get_db),
    current_company: dict = Depends(get_current_company)
):
    """
    Exporta todos los datos personales del usuario (GDPR Art. 20).
    
    Derecho a la portabilidad de datos.
    """
    export = GDPRComplianceService.generate_data_export(
        db=db,
        company_id=current_company.id
    )
    
    return JSONResponse(
        content=export,
        headers={
            "Content-Disposition": f"attachment; filename=gdpr-export-{str(current_company.id)[:8]}.json"
        }
    )


@router.delete("/gdpr/erase")
async def request_data_erasure(
    db: Session = Depends(get_db),
    current_company: dict = Depends(get_current_company)
):
    """
    Solicita borrado de datos personales (GDPR Art. 17).
    
    Derecho al olvido. Inicia proceso de validación.
    """
    validation = GDPRComplianceService.validate_erasure_request(
        db=db,
        company_id=current_company.id
    )
    
    if not validation["can_erase"]:
        return {
            "status": "rejected",
            "reasons": validation["restrictions"],
            "message": "No se puede proceder con el borrado debido a restricciones legales"
        }
    
    # Crear solicitud formal de borrado en DB
    contact_email = getattr(current_company, 'contact_email', '')
    request = GDPRComplianceService.create_request(
        db=db,
        company_id=current_company.id,
        request_type="erasure",
        contact_email=contact_email,
        description="Solicitud de borrado de datos personales (Art. 17 GDPR)"
    )
    
    return {
        "status": "pending",
        "request_id": request["request_number"] if request else None,
        "message": "Solicitud recibida. Será procesada en un máximo de 30 días.",
        "data_to_anonymize": validation["data_to_anonymize"],
        "data_to_delete": validation["data_to_delete"],
        "data_to_retain": validation["data_to_retain"]
    }


@router.post("/gdpr/requests/{request_number}/status")
async def update_gdpr_request_status(
    request_number: str,
    status: str = Query(..., description="Nuevo estado: in_review, fulfilled, rejected, partially_fulfilled"),
    response_summary: Optional[str] = Query(None, description="Resumen de la respuesta"),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin)
):
    """
    Actualiza el estado de una solicitud GDPR (solo admin).
    """
    result = GDPRComplianceService.update_request_status(
        db=db,
        request_number=request_number,
        status=status,
        response_summary=response_summary
    )
    
    if not result:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    
    return {
        "status": "updated",
        "request": result
    }


# ============================================================
# PDF ENDPOINTS
# ============================================================

@router.get("/reports/{report_number}/pdf")
async def download_audit_report_pdf(
    report_number: str,
    db: Session = Depends(get_db),
    current_company: dict = Depends(get_current_company)
):
    """
    Descarga un reporte de auditoría en formato PDF.
    """
    # Obtener reporte de la DB
    report = AuditReportService.get_report_by_number(db, report_number)
    
    if not report:
        raise HTTPException(status_code=404, detail="Reporte no encontrado")
    
    # Verificar que pertenece a la empresa actual
    if report["company_id"] != str(current_company.id):
        raise HTTPException(status_code=403, detail="No tienes acceso a este reporte")
    
    # Preparar datos para el PDF
    report_data = {
        "report_type": report.get("report_type", "compliance"),
        "status": report.get("status", "completed"),
        "period_start": report.get("period_start", "N/A"),
        "period_end": report.get("period_end", "N/A"),
        "summary": report.get("report_data", {}).get("summary", "No hay resumen disponible."),
        "metrics": report.get("report_data", {}).get("metrics", {}),
        "findings": report.get("report_data", {}).get("findings", []),
        "recommendations": report.get("report_data", {}).get("recommendations", []),
        "integrity_hash": report.get("integrity_hash"),
        "generated_by": report.get("generated_by", "system"),
    }
    
    # Generar PDF
    pdf_bytes = pdf_generator.generate_audit_report(
        report_data=report_data,
        report_number=report_number,
        company_name=getattr(current_company, 'razon_social', 'Empresa')
    )
    
    # Crear response
    buffer = BytesIO(pdf_bytes)
    
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=audit-report-{report_number}.pdf"
        }
    )


@router.get("/gdpr/export/pdf")
async def export_gdpr_pdf(
    db: Session = Depends(get_db),
    current_company: dict = Depends(get_current_company)
):
    """
    Exporta datos personales en formato PDF (GDPR Art. 20 - Portabilidad).
    
    Versión PDF de la exportación de datos para facilitar lectura humana.
    """
    export = GDPRComplianceService.generate_data_export(
        db=db,
        company_id=current_company.id
    )
    
    # Generar número de solicitud para tracking
    request_number = export.get("export_id", f"GDPR-EXPORT-{str(current_company.id)[:8]}")
    
    # Generar PDF
    pdf_bytes = pdf_generator.generate_gdpr_export_pdf(
        export_data=export,
        company_name=getattr(current_company, 'razon_social', 'Empresa'),
        request_number=request_number
    )
    
    buffer = BytesIO(pdf_bytes)
    
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=gdpr-export-{request_number}.pdf"
        }
    )
