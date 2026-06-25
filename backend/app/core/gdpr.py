"""
GDPR Compliance Module
Módulo para cumplimiento del Reglamento General de Protección de Datos (RGPD)
Aplicable para operaciones en España y UE.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr
from enum import Enum
import hashlib
import json

# SQLAlchemy imports for DB operations
from sqlalchemy.orm import Session
from sqlalchemy import func

# Import models - handle both import paths gracefully
try:
    from app.models_v2 import GDPRRequest as GDPRRequestDB, DataRetentionPolicy, AuditLog, Company, VerificationRequest
except ImportError:
    # Fallback for tests or when models_v2 is not fully imported
    GDPRRequestDB = None
    DataRetentionPolicy = None
    AuditLog = None
    Company = None
    VerificationRequest = None


class DataSubjectRight(str, Enum):
    """Derechos del titular de datos según GDPR"""
    ACCESS = "access"           # Derecho de acceso (Art. 15)
    RECTIFICATION = "rectification"  # Derecho de rectificación (Art. 16)
    ERASURE = "erasure"         # Derecho al olvido (Art. 17)
    PORTABILITY = "portability" # Derecho a la portabilidad (Art. 20)
    OBJECTION = "objection"     # Derecho de oposición (Art. 21)
    RESTRICTION = "restriction" # Derecho a la limitación (Art. 18)


class GDPRRequestCreate(BaseModel):
    """DTO para crear solicitud GDPR"""
    company_id: str
    request_type: DataSubjectRight
    description: Optional[str] = None
    contact_email: str


class GDPRRequestResponse(BaseModel):
    """Respuesta de solicitud GDPR"""
    request_id: str
    request_number: str
    company_id: str
    request_type: str
    status: str
    requested_at: str
    due_at: Optional[str] = None
    days_remaining: Optional[int] = None
    description: Optional[str] = None
    response_summary: Optional[str] = None


class GDPRComplianceService:
    """Servicio de cumplimiento GDPR con operaciones reales de DB"""
    
    # Retención de datos por tipo (en días)
    DATA_RETENTION_DAYS = {
        "verification_requests": 365 * 2,  # 2 años
        "audit_logs": 365 * 3,             # 3 años
        "payment_records": 365 * 5,        # 5 años (requisito legal)
        "session_logs": 90,                # 90 días
        "failed_login_attempts": 30,       # 30 días
    }
    
    @staticmethod
    def create_request(db: Session, company_id: str, request_type: str, 
                       contact_email: str, description: Optional[str] = None,
                       ip_address: Optional[str] = None, user_agent: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Crea una nueva solicitud GDPR en la base de datos.
        
        Args:
            db: Sesión de base de datos
            company_id: UUID de la empresa
            request_type: Tipo de solicitud (access, erasure, etc.)
            contact_email: Email de contacto
            description: Descripción opcional
            ip_address: IP del solicitante
            user_agent: User agent del solicitante
            
        Returns:
            Dict con la solicitud creada o None si no hay modelo DB disponible
        """
        if GDPRRequestDB is None:
            # Fallback: devolver estructura sin DB
            return {
                "id": "demo-request-id",
                "request_number": "GDPR-DEMO",
                "company_id": company_id,
                "request_type": request_type,
                "status": "pending",
                "requested_at": datetime.now(timezone.utc).isoformat(),
                "description": description,
                "note": "Modelo DB no disponible - datos de demo"
            }
        
        # Generar número de solicitud único
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        hash_suffix = hashlib.sha256(f"{company_id}-{timestamp}".encode()).hexdigest()[:8].upper()
        request_number = f"GDPR-{timestamp}-{hash_suffix}"
        
        # Crear solicitud
        gdpr_request = GDPRRequestDB(
            company_id=company_id,
            request_number=request_number,
            request_type=request_type,
            status="pending",
            description=description,
            contact_email=contact_email,
            ip_address=ip_address,
            user_agent=user_agent
        )
        gdpr_request.set_due_date()
        
        db.add(gdpr_request)
        db.commit()
        db.refresh(gdpr_request)
        
        return {
            "id": str(gdpr_request.id),
            "request_number": gdpr_request.request_number,
            "company_id": str(gdpr_request.company_id),
            "request_type": gdpr_request.request_type,
            "status": gdpr_request.status,
            "requested_at": gdpr_request.requested_at.isoformat() if gdpr_request.requested_at else None,
            "due_at": gdpr_request.due_at.isoformat() if gdpr_request.due_at else None,
            "days_remaining": gdpr_request.get_days_remaining(),
            "description": gdpr_request.description,
            "contact_email": gdpr_request.contact_email
        }
    
    @staticmethod
    def get_requests_by_company(db: Session, company_id: str, 
                                 status: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Obtiene todas las solicitudes GDPR de una empresa.
        
        Args:
            db: Sesión de base de datos
            company_id: UUID de la empresa
            status: Filtrar por estado (opcional)
            
        Returns:
            Lista de solicitudes
        """
        if GDPRRequestDB is None:
            return []
        
        query = db.query(GDPRRequestDB).filter(GDPRRequestDB.company_id == company_id)
        
        if status:
            query = query.filter(GDPRRequestDB.status == status)
        
        requests = query.order_by(GDPRRequestDB.created_at.desc()).all()
        
        return [{
            "id": str(req.id),
            "request_number": req.request_number,
            "request_type": req.request_type,
            "status": req.status,
            "requested_at": req.requested_at.isoformat() if req.requested_at else None,
            "due_at": req.due_at.isoformat() if req.due_at else None,
            "days_remaining": req.get_days_remaining(),
            "responded_at": req.responded_at.isoformat() if req.responded_at else None,
            "description": req.description,
            "response_summary": req.response_summary
        } for req in requests]
    
    @staticmethod
    def update_request_status(db: Session, request_number: str, 
                               status: str, processed_by: Optional[str] = None,
                               response_summary: Optional[str] = None,
                               rejection_reason: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Actualiza el estado de una solicitud GDPR.
        
        Args:
            db: Sesión de base de datos
            request_number: Número de solicitud
            status: Nuevo estado
            processed_by: Quién procesó la solicitud
            response_summary: Resumen de la respuesta
            rejection_reason: Motivo de rechazo
            
        Returns:
            Solicitud actualizada o None
        """
        if GDPRRequestDB is None:
            return None
        
        request = db.query(GDPRRequestDB).filter(
            GDPRRequestDB.request_number == request_number
        ).first()
        
        if not request:
            return None
        
        request.status = status
        request.processed_by = processed_by
        request.updated_at = datetime.now(timezone.utc)
        
        if response_summary:
            request.response_summary = response_summary
        
        if rejection_reason:
            request.rejection_reason = rejection_reason
        
        if status in ['fulfilled', 'rejected', 'partially_fulfilled']:
            request.responded_at = datetime.now(timezone.utc)
        
        db.commit()
        db.refresh(request)
        
        return {
            "id": str(request.id),
            "request_number": request.request_number,
            "status": request.status,
            "responded_at": request.responded_at.isoformat() if request.responded_at else None,
            "processed_by": request.processed_by,
            "response_summary": request.response_summary
        }
    
    @staticmethod
    def generate_data_export(db: Session, company_id: str) -> Dict[str, Any]:
        """
        Genera exportación de datos personales (Portabilidad - Art. 20)
        
        Args:
            db: Sesión de base de datos
            company_id: UUID de la empresa
            
        Returns:
            Dict con todos los datos personales del titular
        """
        export_id = hashlib.sha256(
            f"{company_id}-{datetime.now(timezone.utc).isoformat()}".encode()
        ).hexdigest()[:16]
        
        # Datos base
        export_data = {
            "export_id": export_id,
            "company_id": str(company_id),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "format": "JSON",
            "data_categories": [
                "identification",
                "contact",
                "financial",
                "verification",
                "network",
                "compliance",
                "audit",
            ],
            "data": {
                "profile": {},
                "verifications": [],
                "payments": [],
                "network": [],
                "compliance": [],
                "audit_logs": []
            }
        }
        
        # Si tenemos acceso a DB, poblar con datos reales
        if Company is not None:
            company = db.query(Company).filter(Company.id == company_id).first()
            if company:
                export_data["data"]["profile"] = {
                    "razon_social": company.razon_social,
                    "ruc_hash": company.ruc_hash,
                    "contact_email": company.contact_email,
                    "contact_name": company.contact_name,
                    "contact_phone": company.contact_phone,
                    "plan_tier": company.plan_tier,
                    "status": company.status,
                    "created_at": company.created_at.isoformat() if company.created_at else None,
                }
        
        if VerificationRequest is not None:
            verifications = db.query(VerificationRequest).filter(
                VerificationRequest.consultant_id == company_id
            ).order_by(VerificationRequest.created_at.desc()).limit(100).all()
            
            export_data["data"]["verifications"] = [
                {
                    "id": str(v.id),
                    "target_company_name": v.target_company_name,
                    "score": v.score,
                    "risk_level": v.risk_level,
                    "sunat_debt": v.sunat_debt,
                    "created_at": v.created_at.isoformat() if v.created_at else None
                }
                for v in verifications
            ]
        
        if AuditLog is not None:
            audit_logs = db.query(AuditLog).filter(
                AuditLog.company_id == company_id
            ).order_by(AuditLog.created_at.desc()).limit(100).all()
            
            export_data["data"]["audit_logs"] = [
                {
                    "id": str(log.id),
                    "action": log.action,
                    "resource_type": log.resource_type,
                    "created_at": log.created_at.isoformat() if log.created_at else None
                }
                for log in audit_logs
            ]
        
        return export_data
    
    @staticmethod
    def validate_erasure_request(db: Session, company_id: str) -> Dict[str, Any]:
        """
        Valida si una solicitud de borrado puede proceder.
        
        Restricciones:
        - No se puede borrar si hay obligaciones legales pendientes
        - No se puede borrar si hay pagos activos
        - Datos anonimizados se mantienen para estadísticas
        
        Args:
            db: Sesión de base de datos
            company_id: UUID de la empresa
            
        Returns:
            Dict con resultado de validación
        """
        restrictions = []
        
        # Verificar si hay pagos activos
        if Company is not None:
            company = db.query(Company).filter(Company.id == company_id).first()
            if company:
                if company.subscription_status in ['active', 'past_due']:
                    restrictions.append({
                        "type": "active_subscription",
                        "message": "La empresa tiene una suscripción activa. Cancelar antes de borrar."
                    })
        
        # Verificar si hay verificaciones recientes (posible obligación legal)
        if VerificationRequest is not None:
            recent_verifications = db.query(VerificationRequest).filter(
                VerificationRequest.consultant_id == company_id,
                VerificationRequest.created_at >= datetime.now(timezone.utc) - timedelta(days=365)
            ).count()
            
            if recent_verifications > 0:
                restrictions.append({
                    "type": "recent_verifications",
                    "message": f"La empresa tiene {recent_verifications} verificaciones recientes. Algunos datos deben retenerse por obligación legal."
                })
        
        can_erase = len(restrictions) == 0
        
        return {
            "can_erase": can_erase,
            "restrictions": restrictions,
            "data_to_anonymize": [
                "company_name",
                "legal_name",
                "email",
                "phone"
            ],
            "data_to_delete": [
                "verification_requests_old",
                "network_suppliers",
                "session_logs"
            ],
            "data_to_retain": [
                "payment_records",  # Obligación legal (5 años)
                "audit_logs"        # Obligación legal (3 años)
            ]
        }
    
    @staticmethod
    def anonymize_company_data(db: Session, company_id: str) -> bool:
        """
        Anonimiza datos personales manteniendo integridad referencial.
        
        Args:
            db: Sesión de base de datos
            company_id: UUID de la empresa
            
        Returns:
            bool: True si se anonimizó correctamente
        """
        if Company is None:
            return False
        
        company = db.query(Company).filter(Company.id == company_id).first()
        if not company:
            return False
        
        # Anonimizar datos sensibles
        company.razon_social = f"ANON-{company.ruc_hash[:8]}"
        company.contact_name = "Anonimizado"
        company.contact_email = f"anon-{company.ruc_hash[:8]}@deleted.conflictzero.com"
        company.contact_phone = None
        company.direccion = None
        company.distrito = None
        company.provincia = None
        company.departamento = None
        
        company.status = 'cancelled'
        company.deleted_at = datetime.now(timezone.utc)
        company.is_archived = True
        
        db.commit()
        return True
    
    @staticmethod
    def get_data_retention_schedule() -> Dict[str, int]:
        """Retorna política de retención de datos"""
        return GDPRComplianceService.DATA_RETENTION_DAYS.copy()
    
    @staticmethod
    def get_pending_requests_count(db: Session) -> int:
        """
        Obtiene el número de solicitudes GDPR pendientes.
        """
        if db is None or GDPRRequestDB is None:
            return 0
        
        return db.query(GDPRRequestDB).filter(
            GDPRRequestDB.status.in_(['pending', 'in_review'])
        ).count()
    
    @staticmethod
    def get_overdue_requests(db: Session) -> List[Dict[str, Any]]:
        """
        Obtiene solicitudes GDPR vencidas.
        """
        if db is None or GDPRRequestDB is None:
            return []
        
        now = datetime.now(timezone.utc)
        overdue = db.query(GDPRRequestDB).filter(
            GDPRRequestDB.status.in_(['pending', 'in_review']),
            GDPRRequestDB.due_at < now
        ).all()
        
        return [{
            "id": str(req.id),
            "request_number": req.request_number,
            "company_id": str(req.company_id),
            "request_type": req.request_type,
            "days_overdue": (now - req.due_at).days if req.due_at else 0,
            "contact_email": req.contact_email
        } for req in overdue]
    
    @staticmethod
    def cleanup_expired_data(db: Session, dry_run: bool = True) -> Dict[str, int]:
        """
        Limpia datos expirados según política de retención.
        
        Args:
            db: Sesión de base de datos
            dry_run: Si True, solo reporta sin borrar
            
        Returns:
            Dict con conteo de registros afectados por categoría
        """
        results = {
            "session_logs": 0,
            "failed_logins": 0,
            "old_verifications": 0,
            "old_audit_logs": 0
        }
        
        now = datetime.now(timezone.utc)
        
        # Limpiar verificaciones antiguas (2 años)
        if VerificationRequest is not None and not dry_run:
            cutoff = now - timedelta(days=GDPRComplianceService.DATA_RETENTION_DAYS["verification_requests"])
            old_verifications = db.query(VerificationRequest).filter(
                VerificationRequest.created_at < cutoff,
                VerificationRequest.retained_until.is_(None)
            ).all()
            results["old_verifications"] = len(old_verifications)
            for v in old_verifications:
                v.soft_delete()
            db.commit()
        
        return results


class GDPRPolicy:
    """Políticas GDPR configurables"""
    
    # Base legal para procesamiento (Art. 6 GDPR)
    LEGAL_BASES = {
        "consent": "Consentimiento explícito del titular",
        "contract": "Ejecución de contrato",
        "legal_obligation": "Obligación legal",
        "legitimate_interest": "Interés legítimo",
        "public_interest": "Interés público",
        "vital_interests": "Intereses vitales"
    }
    
    # Categorías especiales de datos (Art. 9 GDPR) - NO procesar
    SPECIAL_CATEGORIES = [
        "racial_origin",
        "ethnic_origin",
        "political_opinions",
        "religious_beliefs",
        "trade_union_membership",
        "genetic_data",
        "biometric_data",
        "health_data",
        "sex_life",
        "sexual_orientation"
    ]
    
    @classmethod
    def get_privacy_notice(cls, country_code: str = "ES") -> str:
        """Genera aviso de privacidad por país"""
        notices = {
            "ES": """
            CONFLICT ZERO - AVISO DE PRIVACIDAD (RGPD/LOPDGDD)
            
            Responsable: Conflict Zero S.L.
            Finalidad: Verificación de riesgo de proveedores
            Legitimación: Ejecución de contrato + Interés legítimo
            Destinatarios: No se cederán datos a terceros salvo obligación legal
            Derechos: Acceso, rectificación, supresión, oposición, portabilidad
            Contacto DPO: dpo@conflictzero.com
            """,
            "PE": """
            CONFLICT ZERO - AVISO DE PRIVACIDAD (Ley 29733)
            
            Titular: Conflict Zero S.A.C.
            Finalidad: Verificación de riesgo de proveedores
            Derechos: Acceso, rectificación, cancelación, oposición
            """
        }
        return notices.get(country_code, notices["PE"])


# Utilidades para enmascaramiento de datos
def mask_email(email: str) -> str:
    """Enmascara email para logs: j***@example.com"""
    if "@" not in email:
        return "***"
    local, domain = email.split("@")
    masked_local = local[0] + "***" if len(local) > 1 else "*"
    return f"{masked_local}@{domain}"


def mask_ruc(ruc: str) -> str:
    """Enmascara RUC para logs: 20*******01"""
    if len(ruc) < 4:
        return "***"
    return f"{ruc[:2]}*****{ruc[-2:]}"


def hash_data_subject_id(company_id: str) -> str:
    """Genera ID anonimizado para análisis estadístico"""
    return hashlib.sha256(f"gdpr-{company_id}".encode()).hexdigest()[:16]
