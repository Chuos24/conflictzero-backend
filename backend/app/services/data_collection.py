"""
Conflict Zero - Data Collection Service
Colecta datos de múltiples fuentes para verificaciones
"""

import os
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import requests
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models_v2 import ApiCache, Company

# ============================================================
# DATA COLLECTION SERVICE (Clase)
# ============================================================

class DataCollectionService:
    """Servicio para colectar datos de fuentes externas."""
    
    def get_sunat_data(self, ruc: str) -> Dict[str, Any]:
        """Obtiene datos de SUNAT para un RUC."""
        from app.core.database import SessionLocal
        db = SessionLocal()
        try:
            return get_sunat_data(ruc, db)
        finally:
            db.close()
    
    def get_osce_data(self, ruc: str) -> Dict[str, Any]:
        """Obtiene datos de OSCE para un RUC."""
        from app.core.database import SessionLocal
        db = SessionLocal()
        try:
            sanctions = get_osce_sanctions(ruc, db)
            return {
                "ruc": ruc,
                "sanctions": sanctions,
                "sanctions_count": len(sanctions)
            }
        finally:
            db.close()
    
    def get_tce_data(self, ruc: str) -> Dict[str, Any]:
        """Obtiene datos de TCE para un RUC."""
        from app.core.database import SessionLocal
        db = SessionLocal()
        try:
            sanctions = get_tce_sanctions(ruc, db)
            return {
                "ruc": ruc,
                "sanctions": sanctions,
                "sanctions_count": len(sanctions)
            }
        finally:
            db.close()
    
    def _mock_sunat_data(self, ruc: str) -> Dict[str, Any]:
        """Genera datos mock de SUNAT."""
        return {
            "found": True,
            "ruc": ruc,
            "razon_social": f"EMPRESA DEMO S.A.C. ({ruc[:6]})",
            "tax_status": "ACTIVO",
            "contributor_status": "HABIDO",
            "direccion": "Av. Demo 123, Lima",
            "departamento": "Lima",
            "provincia": "Lima",
            "distrito": "Miraflores",
            "debt_amount": 0,
            "source": "mock"
        }
    
    def _mock_osce_data(self, ruc: str) -> Dict[str, Any]:
        """Genera datos mock de OSCE."""
        return {
            "ruc": ruc,
            "sanctions": [],
            "sanctions_count": 0
        }
    
    def _mock_tce_data(self, ruc: str) -> Dict[str, Any]:
        """Genera datos mock de TCE."""
        return {
            "ruc": ruc,
            "sanctions": [],
            "sanctions_count": 0
        }


# ============================================================
# FUNCIONES ORIGINALES (Mantener compatibilidad)
# ============================================================
PERU_API_TOKEN = os.getenv("PERU_API_TOKEN", "")
PERU_API_BASE = "https://api.peruapi.com/v1"


def get_cache_key(query_type: str, identifier: str) -> str:
    """Genera clave de caché"""
    return hashlib.md5(f"{query_type}:{identifier}".encode()).hexdigest()


def get_cached_response(query_type: str, identifier: str, db: Session) -> Optional[Dict]:
    """Obtiene respuesta cacheada si existe y no expiró"""
    cache_key = get_cache_key(query_type, identifier)
    cache = db.query(ApiCache).filter(ApiCache.query_hash == cache_key).first()
    
    if cache and not cache.is_expired():
        cache.hit()
        db.commit()
        return cache.response_json
    return None


def set_cached_response(query_type: str, identifier: str, data: Dict, db: Session, ttl_minutes: int = 15):
    """Guarda respuesta en caché"""
    cache_key = get_cache_key(query_type, identifier)
    
    cache = db.query(ApiCache).filter(ApiCache.query_hash == cache_key).first()
    
    if cache:
        cache.response_json = data
        cache.expires_at = datetime.utcnow() + timedelta(minutes=ttl_minutes)
        cache.hit_count = 1
        cache.last_hit_at = datetime.utcnow()
    else:
        cache = ApiCache(
            query_hash=cache_key,
            query_type=query_type,
            query_identifier=identifier,
            response_json=data,
            expires_at=datetime.utcnow() + timedelta(minutes=ttl_minutes)
        )
        db.add(cache)
    
    db.commit()


def get_sunat_data(ruc: str, db: Session) -> Dict[str, Any]:
    """
    Obtiene datos de SUNAT para un RUC.
    Usa caché de 15 minutos.
    """
    # Verificar caché
    cached = get_cached_response("sunat", ruc, db)
    if cached:
        return cached
    
    # Si hay token de Peru API, usarlo
    if PERU_API_TOKEN:
        try:
            response = requests.get(
                f"{PERU_API_BASE}/ruc",
                headers={"Authorization": f"Bearer {PERU_API_TOKEN}"},
                params={"document": ruc},
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                sunat_data = {
                    "found": True,
                    "ruc": ruc,
                    "razon_social": data.get("nombre_o_razon_social", ""),
                    "estado": data.get("estado_del_contribuyente", ""),
                    "condicion": data.get("condicion_de_domicilio", ""),
                    "direccion": data.get("direccion", ""),
                    "departamento": data.get("departamento", ""),
                    "provincia": data.get("provincia", ""),
                    "distrito": data.get("distrito", ""),
                    "deuda": 0,  # Peru API no tiene deuda
                    "source": "peru_api"
                }
                set_cached_response("sunat", ruc, sunat_data, db)
                return sunat_data
        except Exception as e:
            print(f"Error consultando Peru API: {e}")
    
    # Fallback: datos simulados para demo
    demo_data = {
        "found": True,
        "ruc": ruc,
        "razon_social": f"EMPRESA DEMO S.A.C. ({ruc[:6]})",
        "estado": "ACTIVO",
        "condicion": "HABIDO",
        "direccion": "Av. Demo 123, Lima",
        "departamento": "Lima",
        "provincia": "Lima",
        "distrito": "Miraflores",
        "deuda": 0,
        "source": "demo"
    }
    set_cached_response("sunat", ruc, demo_data, db)
    return demo_data


def get_osce_sanctions(ruc: str, db: Session) -> List[Dict[str, Any]]:
    """
    Obtiene sanciones de OSCE desde la base de datos local.
    Los datos se cargan desde datos abiertos de OSCE.
    """
    from sqlalchemy import text
    
    try:
        result = db.execute(
            text("""
                SELECT 
                    sancion_id,
                    entidad,
                    tipo_sancion,
                    fecha_inicio,
                    fecha_fin,
                    estado
                FROM osce_sanciones 
                WHERE ruc_sancionado = :ruc
                AND estado = 'Vigente'
            """),
            {"ruc": ruc}
        )
        
        sanctions = []
        for row in result:
            sanctions.append({
                "sanction_id": row[0],
                "entity": row[1],
                "type": row[2],
                "start_date": row[3].isoformat() if row[3] else None,
                "end_date": row[4].isoformat() if row[4] else None,
                "status": row[5]
            })
        
        return sanctions
    except Exception as e:
        print(f"Error consultando OSCE: {e}")
        return []


def get_rnp_sanctions(ruc: str, db: Session) -> List[Dict[str, Any]]:
    """
    Obtiene sanciones del RNP (Registro Nacional de Proveedores).
    """
    from sqlalchemy import text
    
    try:
        result = db.execute(
            text("""
                SELECT 
                    sancion_id,
                    motivo,
                    fecha_sancion,
                    tiempo_sancion,
                    estado
                FROM rnp_sanciones 
                WHERE ruc = :ruc
                AND estado = 'Vigente'
            """),
            {"ruc": ruc}
        )
        
        sanctions = []
        for row in result:
            sanctions.append({
                "sanction_id": row[0],
                "reason": row[1],
                "date": row[2].isoformat() if row[2] else None,
                "duration": row[3],
                "status": row[4]
            })
        
        return sanctions
    except Exception as e:
        print(f"Error consultando RNP: {e}")
        return []


def get_tce_sanctions(ruc: str, db: Session) -> List[Dict[str, Any]]:
    """
    Obtiene sanciones de TCE (Tribunal de Contrataciones del Estado).
    """
    from sqlalchemy import text
    
    try:
        result = db.execute(
            text("""
                SELECT 
                    sancion_id,
                    entidad,
                    resolucion,
                    fecha_sancion,
                    plazo,
                    estado
                FROM tce_sanciones 
                WHERE ruc = :ruc
                AND estado = 'Vigente'
            """),
            {"ruc": ruc}
        )
        
        sanctions = []
        for row in result:
            sanctions.append({
                "sanction_id": row[0],
                "entity": row[1],
                "resolution": row[2],
                "date": row[3].isoformat() if row[3] else None,
                "term": row[4],
                "status": row[5]
            })
        
        return sanctions
    except Exception as e:
        print(f"Error consultando TCE: {e}")
        return []


# Alias para compatibilidad con monitoring_service.py
def collect_company_data(ruc: str) -> Dict[str, Any]:
    """Colecta datos para un RUC (alias para monitoring_service)."""
    from app.core.database import SessionLocal
    db = SessionLocal()
    try:
        return collect_all_data(ruc, db)
    finally:
        db.close()


def collect_all_data(ruc: str, db: Session) -> Dict[str, Any]:
    """
    Colecta todos los datos disponibles para un RUC.
    
    Returns:
        Dict con:
        - sunat: Datos de SUNAT
        - osce_sanctions: Lista de sanciones OSCE
        - rnp_sanctions: Lista de sanciones RNP
        - tce_sanctions: Lista de sanciones TCE
        - summary: Resumen de riesgo
    """
    # Obtener datos de todas las fuentes
    sunat_data = get_sunat_data(ruc, db)
    osce_sanctions = get_osce_sanctions(ruc, db)
    rnp_sanctions = get_rnp_sanctions(ruc, db)
    tce_sanctions = get_tce_sanctions(ruc, db)
    
    # Calcular totales
    total_sanctions = len(osce_sanctions) + len(rnp_sanctions) + len(tce_sanctions)
    
    # Generar resumen
    summary = {
        "ruc": ruc,
        "found": sunat_data.get("found", False),
        "razon_social": sunat_data.get("razon_social", ""),
        "estado_contribuyente": sunat_data.get("estado", ""),
        "condicion_domicilio": sunat_data.get("condicion", ""),
        "deuda_sunat": sunat_data.get("deuda", 0),
        "total_sanctions": total_sanctions,
        "osce_count": len(osce_sanctions),
        "rnp_count": len(rnp_sanctions),
        "tce_count": len(tce_sanctions),
        "has_debt": sunat_data.get("deuda", 0) > 0,
        "has_sanctions": total_sanctions > 0,
        "risk_indicators": []
    }
    
    # Agregar indicadores de riesgo
    if sunat_data.get("estado") != "ACTIVO":
        summary["risk_indicators"].append("Contribuyente no activo")
    if sunat_data.get("condicion") != "HABIDO":
        summary["risk_indicators"].append("Contribuyente no habido")
    if sunat_data.get("deuda", 0) > 0:
        summary["risk_indicators"].append(f"Deuda SUNAT: S/ {sunat_data['deuda']:,.2f}")
    if total_sanctions > 0:
        summary["risk_indicators"].append(f"{total_sanctions} sanciones vigentes")
    
    return {
        "sunat": sunat_data,
        "osce_sanctions": osce_sanctions,
        "rnp_sanctions": rnp_sanctions,
        "tce_sanctions": tce_sanctions,
        "summary": summary,
        "collected_at": datetime.utcnow().isoformat()
    }


def collect_multiple_rucs(rucs: List[str], db: Session) -> Dict[str, Any]:
    """
    Colecta datos para múltiples RUCs (para comparación).
    
    Returns:
        Dict con resultados para cada RUC y comparativa
    """
    results = []
    
    for ruc in rucs:
        try:
            data = collect_all_data(ruc, db)
            results.append(data)
        except Exception as e:
            print(f"Error colectando datos para {ruc}: {e}")
            results.append({
                "sunat": {"found": False, "ruc": ruc},
                "osce_sanctions": [],
                "rnp_sanctions": [],
                "tce_sanctions": [],
                "summary": {"ruc": ruc, "found": False, "error": str(e)},
                "collected_at": datetime.utcnow().isoformat()
            })
    
    # Generar comparativa
    comparison = generate_comparison(results)
    
    return {
        "results": results,
        "comparison": comparison,
        "total_processed": len(results),
        "total_found": sum(1 for r in results if r["summary"].get("found", False))
    }


def generate_comparison(results: List[Dict]) -> Dict[str, Any]:
    """
    Genera análisis comparativo entre múltiples empresas.
    """
    if not results:
        return {}
    
    # Extraer scores (simulados si no existen)
    companies = []
    for r in results:
        summary = r.get("summary", {})
        
        # Calcular score simple basado en datos
        score = 100
        deductions = 0
        
        if summary.get("has_debt"):
            debt = r.get("sunat", {}).get("deuda", 0)
            deductions += min(30, int(debt / 1000))  # -1 por cada 1000 soles, max 30
        
        total_sanctions = summary.get("total_sanctions", 0)
        deductions += min(40, total_sanctions * 10)  # -10 por sanción, max 40
        
        if summary.get("estado_contribuyente") != "ACTIVO":
            deductions += 15
        if summary.get("condicion_domicilio") != "HABIDO":
            deductions += 15
        
        score = max(0, score - deductions)
        
        # Determinar nivel de riesgo
        if score >= 80:
            risk_level = "low"
        elif score >= 60:
            risk_level = "medium"
        elif score >= 40:
            risk_level = "high"
        else:
            risk_level = "critical"
        
        companies.append({
            "ruc": summary.get("ruc", ""),
            "razon_social": summary.get("razon_social", "Desconocido"),
            "score": score,
            "risk_level": risk_level,
            "deuda": r.get("sunat", {}).get("deuda", 0),
            "total_sanctions": summary.get("total_sanctions", 0),
            "estado": summary.get("estado_contribuyente", ""),
            "condicion": summary.get("condicion_domicilio", "")
        })
    
    # Ordenar por score (descendente)
    companies_sorted = sorted(companies, key=lambda x: x["score"], reverse=True)
    
    # Calcular estadísticas
    scores = [c["score"] for c in companies]
    
    return {
        "ranking": companies_sorted,
        "best": companies_sorted[0] if companies_sorted else None,
        "worst": companies_sorted[-1] if companies_sorted else None,
        "average_score": sum(scores) / len(scores) if scores else 0,
        "highest_risk": [c for c in companies if c["risk_level"] in ["high", "critical"]],
        "risk_distribution": {
            "low": len([c for c in companies if c["risk_level"] == "low"]),
            "medium": len([c for c in companies if c["risk_level"] == "medium"]),
            "high": len([c for c in companies if c["risk_level"] == "high"]),
            "critical": len([c for c in companies if c["risk_level"] == "critical"])
        }
    }
