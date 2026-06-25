"""
Audit Report Generator
Generador de reportes de auditoría para compliance y terceros.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any
from enum import Enum
import json
import hashlib

import json

from sqlalchemy.orm import Session
from sqlalchemy import func, and_

# Import DB models - handle gracefully if not available
try:
    from app.models_v2 import AuditReport as AuditReportDB, AuditReportSignature
    from app.models_v2 import Company, VerificationRequest, Invite, AuditLog, CompanyHierarchy
except ImportError:
    AuditReportDB = None
    AuditReportSignature = None
    Company = None
    VerificationRequest = None
    Invite = None
    AuditLog = None
    CompanyHierarchy = None


class AuditReportType(str, Enum):
    """Tipos de reportes de auditoría"""
    COMPLIANCE = "compliance"           # Estado de compliance
    SECURITY = "security"               # Eventos de seguridad
    ACCESS = "access"                   # Logs de acceso
    DATA_PROCESSING = "data_processing" # Procesamiento de datos
    NETWORK_CHANGES = "network_changes" # Cambios en red de proveedores
    FINANCIAL = "financial"             # Transacciones financieras


class AuditReport:
    """Reporte de auditoría individual (estructura de datos)"""
    
    def __init__(
        self,
        report_type: AuditReportType,
        company_id: str,
        start_date: datetime,
        end_date: datetime,
        generated_by: str = "system"
    ):
        self.report_id = self._generate_report_id(company_id, report_type)
        self.report_type = report_type
        self.company_id = company_id
        self.start_date = start_date
        self.end_date = end_date
        self.generated_at = datetime.now(timezone.utc)
        self.generated_by = generated_by
        self.status = "pending"
        self.data: Dict[str, Any] = {}
        self.hash: Optional[str] = None
        self.signed: bool = False
    
    def _generate_report_id(self, company_id: str, report_type: AuditReportType) -> str:
        """Genera ID único de reporte"""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        base = f"{company_id}-{report_type.value}-{timestamp}"
        return f"AUD-{hashlib.sha256(base.encode()).hexdigest()[:12].upper()}"
    
    def add_section(self, title: str, content: Dict[str, Any]):
        """Añade sección al reporte"""
        if "sections" not in self.data:
            self.data["sections"] = []
        self.data["sections"].append({
            "title": title,
            "content": content,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
    
    def sign_report(self, signer_id: str):
        """Firma el reporte para integridad"""
        content = json.dumps(self.data, sort_keys=True)
        self.hash = hashlib.sha256(content.encode()).hexdigest()
        self.signed = True
        self.status = "signed"
        self.signed_by = signer_id
        self.signed_at = datetime.now(timezone.utc).isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Exporta reporte como diccionario"""
        return {
            "report_id": self.report_id,
            "report_type": self.report_type.value,
            "company_id": self.company_id,
            "period": {
                "start": self.start_date.isoformat(),
                "end": self.end_date.isoformat()
            },
            "generated": {
                "at": self.generated_at.isoformat(),
                "by": self.generated_by
            },
            "status": self.status,
            "data": self.data,
            "integrity": {
                "hash": self.hash,
                "signed": self.signed
            }
        }


class AuditReportService:
    """Servicio de reportes de auditoría con persistencia en DB"""
    
    @staticmethod
    def create_report_db(db: Session, report: AuditReport) -> Optional[Dict[str, Any]]:
        """
        Guarda un reporte de auditoría en la base de datos.
        
        Args:
            db: Sesión de base de datos
            report: Reporte generado
            
        Returns:
            Dict con datos del reporte guardado o None
        """
        if AuditReportDB is None:
            return None
        
        # Serializar report_data para compatibilidad con SQLite (Text)
        report_data_json = json.dumps(report.data) if isinstance(report.data, dict) else report.data
        
        db_report = AuditReportDB(
            company_id=report.company_id,
            report_number=report.report_id,
            report_type=report.report_type.value,
            status=report.status,
            period_start=report.start_date,
            period_end=report.end_date,
            report_data=report_data_json,
            integrity_hash=report.hash,
            generated_at=report.generated_at,
            generated_by=report.generated_by
        )
        
        db.add(db_report)
        db.commit()
        db.refresh(db_report)
        
        return {
            "id": str(db_report.id),
            "report_number": db_report.report_number,
            "company_id": str(db_report.company_id),
            "report_type": db_report.report_type,
            "status": db_report.status,
            "period_start": db_report.period_start.isoformat() if db_report.period_start else None,
            "period_end": db_report.period_end.isoformat() if db_report.period_end else None,
            "generated_at": db_report.generated_at.isoformat() if db_report.generated_at else None,
            "generated_by": db_report.generated_by
        }
    
    @staticmethod
    def get_reports_by_company(db: Session, company_id: str,
                                report_type: Optional[str] = None,
                                status: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Obtiene reportes de auditoría de una empresa.
        """
        if db is None or AuditReportDB is None:
            return []
        
        query = db.query(AuditReportDB).filter(AuditReportDB.company_id == company_id)
        
        if report_type:
            query = query.filter(AuditReportDB.report_type == report_type)
        if status:
            query = query.filter(AuditReportDB.status == status)
        
        reports = query.order_by(AuditReportDB.created_at.desc()).all()
        
        return [{
            "id": str(r.id),
            "report_number": r.report_number,
            "report_type": r.report_type,
            "status": r.status,
            "period_start": r.period_start.isoformat() if r.period_start else None,
            "period_end": r.period_end.isoformat() if r.period_end else None,
            "generated_at": r.generated_at.isoformat() if r.generated_at else None,
            "generated_by": r.generated_by,
            "integrity_hash": r.integrity_hash
        } for r in reports]
    
    @staticmethod
    def get_report_by_number(db: Session, report_number: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene un reporte por su número.
        
        Args:
            db: Sesión de base de datos
            report_number: Número del reporte
            
        Returns:
            Dict con datos del reporte o None
        """
        if AuditReportDB is None:
            return None
        
        report = db.query(AuditReportDB).filter(
            AuditReportDB.report_number == report_number
        ).first()
        
        if not report:
            return None
        
        # Deserializar report_data si es string JSON
        report_data = report.report_data
        if isinstance(report_data, str):
            try:
                report_data = json.loads(report_data)
            except (json.JSONDecodeError, TypeError):
                report_data = {}
        
        return {
            "id": str(report.id),
            "report_number": report.report_number,
            "company_id": str(report.company_id),
            "report_type": report.report_type,
            "status": report.status,
            "period_start": report.period_start.isoformat() if report.period_start else None,
            "period_end": report.period_end.isoformat() if report.period_end else None,
            "report_data": report_data,
            "pdf_url": report.pdf_url,
            "json_url": report.json_url,
            "integrity_hash": report.integrity_hash,
            "generated_at": report.generated_at.isoformat() if report.generated_at else None,
            "generated_by": report.generated_by
        }
    
    @staticmethod
    def sign_report_db(db: Session, report_number: str, 
                        signed_by: str = "system",
                        signed_by_type: str = "system") -> Optional[Dict[str, Any]]:
        """
        Firma un reporte en la base de datos.
        
        Args:
            db: Sesión de base de datos
            report_number: Número del reporte
            signed_by: Quién firma
            signed_by_type: Tipo de firmante
            
        Returns:
            Dict con datos de la firma o None
        """
        if AuditReportDB is None or AuditReportSignature is None:
            return None
        
        report = db.query(AuditReportDB).filter(
            AuditReportDB.report_number == report_number
        ).first()
        
        if not report:
            return None
        
        # Generar hash de integridad
        content = json.dumps(report.report_data, sort_keys=True) if report.report_data else ""
        doc_hash = hashlib.sha256(content.encode()).hexdigest()
        sig_hash = hashlib.sha256(f"{doc_hash}-{signed_by}-{datetime.now(timezone.utc).isoformat()}".encode()).hexdigest()
        
        # Crear firma
        signature = AuditReportSignature(
            report_id=report.id,
            signed_by=signed_by,
            signed_by_type=signed_by_type,
            signature_hash=sig_hash,
            document_hash=doc_hash,
            algorithm="SHA256",
            is_valid=True,
            verified_at=datetime.now(timezone.utc)
        )
        
        db.add(signature)
        db.commit()
        db.refresh(signature)
        
        return {
            "id": str(signature.id),
            "report_id": str(signature.report_id),
            "signed_by": signature.signed_by,
            "signed_by_type": signature.signed_by_type,
            "signature_hash": signature.signature_hash,
            "document_hash": signature.document_hash,
            "algorithm": signature.algorithm,
            "is_valid": signature.is_valid,
            "verified_at": signature.verified_at.isoformat() if signature.verified_at else None
        }


class AuditReportGenerator:
    """Generador de reportes de auditoría con datos reales de DB"""
    
    @staticmethod
    def _get_verification_stats(db: Session, company_id: str, 
                                 start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Obtiene estadísticas de verificaciones de la DB"""
        if VerificationRequest is None:
            return {"total": 0, "avg_score": 0, "by_risk": {}}
        
        query = db.query(VerificationRequest).filter(
            VerificationRequest.consultant_id == company_id,
            VerificationRequest.created_at >= start_date,
            VerificationRequest.created_at <= end_date,
            VerificationRequest.deleted_at.is_(None)
        )
        
        total = query.count()
        avg_score = db.query(func.avg(VerificationRequest.score)).filter(
            VerificationRequest.consultant_id == company_id,
            VerificationRequest.created_at >= start_date,
            VerificationRequest.created_at <= end_date
        ).scalar() or 0
        
        risk_counts = {}
        for risk in ['low', 'medium', 'high', 'critical']:
            count = query.filter(VerificationRequest.risk_level == risk).count()
            if count > 0:
                risk_counts[risk] = count
        
        return {
            "total": total,
            "avg_score": round(float(avg_score), 1),
            "by_risk": risk_counts
        }
    
    @staticmethod
    def _get_invite_stats(db: Session, company_id: str,
                          start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Obtiene estadísticas de invitaciones de la DB"""
        if Invite is None:
            return {"total": 0, "converted": 0, "conversion_rate": 0}
        
        query = db.query(Invite).filter(
            Invite.inviter_id == company_id,
            Invite.created_at >= start_date,
            Invite.created_at <= end_date,
            Invite.deleted_at.is_(None)
        )
        
        total = query.count()
        converted = query.filter(Invite.status == 'paid').count()
        
        return {
            "total": total,
            "converted": converted,
            "conversion_rate": round((converted / total * 100), 1) if total > 0 else 0
        }
    
    @staticmethod
    def _get_audit_logs(db: Session, company_id: str,
                        start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Obtiene logs de auditoría de la DB"""
        if AuditLog is None:
            return []
        
        logs = db.query(AuditLog).filter(
            AuditLog.company_id == company_id,
            AuditLog.created_at >= start_date,
            AuditLog.created_at <= end_date
        ).order_by(AuditLog.created_at.desc()).limit(50).all()
        
        return [{
            "id": str(log.id),
            "action": log.action,
            "resource_type": log.resource_type,
            "actor_type": log.actor_type,
            "created_at": log.created_at.isoformat() if log.created_at else None
        } for log in logs]
    
    @staticmethod
    def _get_network_stats(db: Session, company_id: str,
                           start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Obtiene estadísticas de red de proveedores de la DB"""
        if CompanyHierarchy is None:
            return {"total_suppliers": 0, "active": 0}
        
        total = db.query(CompanyHierarchy).filter(
            CompanyHierarchy.parent_id == company_id,
            CompanyHierarchy.created_at >= start_date,
            CompanyHierarchy.created_at <= end_date
        ).count()
        
        active = db.query(CompanyHierarchy).filter(
            CompanyHierarchy.parent_id == company_id,
            CompanyHierarchy.is_active == True,
            CompanyHierarchy.deleted_at.is_(None)
        ).count()
        
        return {
            "total_suppliers": total,
            "active": active
        }
    
    @staticmethod
    def generate_compliance_report(
        company_id: str,
        start_date: datetime,
        end_date: datetime,
        db: Session
    ) -> AuditReport:
        """
        Genera reporte de compliance con datos reales de la DB.
        """
        report = AuditReport(
            report_type=AuditReportType.COMPLIANCE,
            company_id=company_id,
            start_date=start_date,
            end_date=end_date
        )
        
        # Obtener estadísticas reales
        verif_stats = AuditReportGenerator._get_verification_stats(db, company_id, start_date, end_date)
        invite_stats = AuditReportGenerator._get_invite_stats(db, company_id, start_date, end_date)
        
        # Calcular estado general
        estado_general = "compliant"
        if invite_stats["conversion_rate"] < 30 and invite_stats["total"] > 0:
            estado_general = "needs_attention"
        if verif_stats["by_risk"].get("high", 0) + verif_stats["by_risk"].get("critical", 0) > 5:
            estado_general = "at_risk"
        
        # Sección: Resumen ejecutivo
        report.add_section("Resumen Ejecutivo", {
            "periodo": f"{start_date.date()} a {end_date.date()}",
            "estado_general": estado_general,
            "verificaciones_realizadas": verif_stats["total"],
            "score_promedio": verif_stats["avg_score"],
            "invitaciones_enviadas": invite_stats["total"],
            "conversiones": invite_stats["converted"],
            "tasa_conversion": f"{invite_stats['conversion_rate']}%"
        })
        
        # Sección: Riesgo
        report.add_section("Análisis de Riesgo", {
            "distribucion_riesgo": verif_stats["by_risk"],
            "score_promedio": verif_stats["avg_score"],
            "alertas": "Verificar proveedores con riesgo alto"
        })
        
        # Sección: Cumplimiento contractual (Founder)
        report.add_section("Cumplimiento Contractual", {
            "invitaciones_enviadas": invite_stats["total"],
            "conversiones": invite_stats["converted"],
            "tasa_conversion_porcentaje": invite_stats["conversion_rate"],
            "meta_minima": "50%",
            "cumple_meta": invite_stats["conversion_rate"] >= 50
        })
        
        return report
    
    @staticmethod
    def generate_security_report(
        company_id: str,
        start_date: datetime,
        end_date: datetime,
        db: Session
    ) -> AuditReport:
        """
        Genera reporte de eventos de seguridad con datos reales.
        """
        report = AuditReport(
            report_type=AuditReportType.SECURITY,
            company_id=company_id,
            start_date=start_date,
            end_date=end_date
        )
        
        # Obtener logs de auditoría reales
        logs = AuditReportGenerator._get_audit_logs(db, company_id, start_date, end_date)
        
        # Contar por tipo de acción
        auth_logs = [l for l in logs if l["action"] in ["login", "logout", "password_change"]]
        config_logs = [l for l in logs if l["action"] in ["config_change", "webhook_update"]]
        
        report.add_section("Eventos de Autenticación", {
            "logins_exitosos": len([l for l in auth_logs if l["action"] == "login"]),
            "logins_fallidos": len([l for l in auth_logs if l["action"] == "login_failed"]),
            "cambios_password": len([l for l in auth_logs if l["action"] == "password_change"]),
            "total_eventos": len(auth_logs)
        })
        
        report.add_section("Cambios Críticos", {
            "cambios_configuracion": len(config_logs),
            "detalle_cambios": config_logs[:10]
        })
        
        report.add_section("Logs de Auditoría", {
            "total_logs": len(logs),
            "ultimos_logs": logs[:5]
        })
        
        return report
    
    @staticmethod
    def generate_data_processing_report(
        company_id: str,
        start_date: datetime,
        end_date: datetime,
        db: Session
    ) -> AuditReport:
        """
        Genera reporte de procesamiento de datos (GDPR/LGPD).
        """
        report = AuditReport(
            report_type=AuditReportType.DATA_PROCESSING,
            company_id=company_id,
            start_date=start_date,
            end_date=end_date
        )
        
        verif_stats = AuditReportGenerator._get_verification_stats(db, company_id, start_date, end_date)
        
        report.add_section("Actividad de Verificación", {
            "verificaciones_realizadas": verif_stats["total"],
            "rucs_unicos_verificados": verif_stats["total"],  # Simplificado
            "score_promedio": verif_stats["avg_score"]
        })
        
        report.add_section("Retención de Datos", {
            "politica_aplicada": "2 años para verificaciones, 3 años para audit logs, 5 años para pagos",
            "periodo_reporte": f"{start_date.date()} a {end_date.date()}"
        })
        
        return report
    
    @staticmethod
    def generate_network_changes_report(
        company_id: str,
        start_date: datetime,
        end_date: datetime,
        db: Session
    ) -> AuditReport:
        """
        Genera reporte de cambios en red de proveedores.
        """
        report = AuditReport(
            report_type=AuditReportType.NETWORK_CHANGES,
            company_id=company_id,
            start_date=start_date,
            end_date=end_date
        )
        
        network_stats = AuditReportGenerator._get_network_stats(db, company_id, start_date, end_date)
        verif_stats = AuditReportGenerator._get_verification_stats(db, company_id, start_date, end_date)
        
        report.add_section("Estado de la Red", {
            "proveedores_activos": network_stats["active"],
            "proveedores_agregados_periodo": network_stats["total_suppliers"],
            "verificaciones_periodo": verif_stats["total"]
        })
        
        report.add_section("Tendencias de Riesgo", {
            "score_promedio": verif_stats["avg_score"],
            "distribucion_riesgo": verif_stats["by_risk"],
            "alertas": verif_stats["by_risk"].get("high", 0) + verif_stats["by_risk"].get("critical", 0)
        })
        
        return report


class AuditScheduler:
    """Programador de auditorías automáticas"""
    
    # Frecuencias de reportes automáticos
    SCHEDULES = {
        "compliance": "monthly",      # Mensual para founders
        "security": "weekly",         # Semanal
        "data_processing": "quarterly",  # Trimestral
        "network_changes": "daily",   # Diario (resumen)
    }
    
    @staticmethod
    def get_next_report_date(last_report: datetime, report_type: str) -> datetime:
        """Calcula próxima fecha de reporte"""
        frequency = AuditScheduler.SCHEDULES.get(report_type, "monthly")
        
        if frequency == "daily":
            return last_report + timedelta(days=1)
        elif frequency == "weekly":
            return last_report + timedelta(weeks=1)
        elif frequency == "monthly":
            return last_report + timedelta(days=30)
        elif frequency == "quarterly":
            return last_report + timedelta(days=90)
        else:
            return last_report + timedelta(days=30)
    
    @staticmethod
    def should_generate_report(
        company_id: str,
        report_type: str,
        last_report_date: Optional[datetime]
    ) -> bool:
        """Determina si se debe generar un reporte"""
        if last_report_date is None:
            return True
        
        next_date = AuditScheduler.get_next_report_date(last_report_date, report_type)
        return datetime.now(timezone.utc) >= next_date
    
    @staticmethod
    def get_schedule_calendar() -> List[Dict[str, Any]]:
        """
        Retorna calendario de auditorías programadas.
        
        Returns:
            Lista de auditorías con frecuencia y próxima ejecución
        """
        now = datetime.now(timezone.utc)
        calendar = []
        
        for report_type, frequency in AuditScheduler.SCHEDULES.items():
            if frequency == "daily":
                next_run = now + timedelta(days=1)
                description = "Resumen diario de cambios en red"
            elif frequency == "weekly":
                next_run = now + timedelta(weeks=1)
                description = "Reporte semanal de seguridad"
            elif frequency == "monthly":
                next_run = now + timedelta(days=30)
                description = "Reporte mensual de compliance"
            else:  # quarterly
                next_run = now + timedelta(days=90)
                description = "Reporte trimestral de procesamiento de datos"
            
            calendar.append({
                "report_type": report_type,
                "frequency": frequency,
                "description": description,
                "next_scheduled": next_run.isoformat(),
                "is_active": True
            })
        
        return calendar
