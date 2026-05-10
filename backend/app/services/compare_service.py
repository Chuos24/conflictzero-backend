"""
Conflict Zero - Compare Service
Servicio para comparar múltiples empresas simultáneamente
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from io import BytesIO
from sqlalchemy.orm import Session

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, black, white
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import qrcode

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
        return _generate_compare_pdf(data)
    
    else:
        raise ValueError(f"Formato no soportado: {format}")


def _generate_compare_pdf(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Genera PDF profesional de comparación de empresas.
    Diseño premium dark/gold acorde a la marca Conflict Zero.
    """
    # Colores de marca
    COLOR_DARK_BG = HexColor("#0a0a0f")
    COLOR_GOLD = HexColor("#c9a84c")
    COLOR_GOLD_LIGHT = HexColor("#d4b76a")
    COLOR_TEXT = HexColor("#e0e0e0")
    COLOR_TEXT_DIM = HexColor("#888888")
    COLOR_RED = HexColor("#e74c3c")
    COLOR_GREEN = HexColor("#2ecc71")
    COLOR_YELLOW = HexColor("#f1c40f")
    COLOR_ORANGE = HexColor("#e67e22")
    COLOR_WHITE = HexColor("#ffffff")

    def risk_color(level: str) -> HexColor:
        mapping = {
            "low": COLOR_GREEN, "bajo": COLOR_GREEN,
            "medium": COLOR_YELLOW, "moderado": COLOR_YELLOW, "moderate": COLOR_YELLOW,
            "high": COLOR_ORANGE, "alto": COLOR_ORANGE,
            "critical": COLOR_RED, "crítico": COLOR_RED, "critico": COLOR_RED,
        }
        return mapping.get(level.lower(), COLOR_TEXT)

    def risk_label(level: str) -> str:
        mapping = {
            "low": "BAJO", "bajo": "BAJO",
            "medium": "MODERADO", "moderado": "MODERADO", "moderate": "MODERADO",
            "high": "ALTO", "alto": "ALTO",
            "critical": "CRÍTICO", "crítico": "CRÍTICO", "critico": "CRÍTICO",
        }
        return mapping.get(level.lower(), "DESCONOCIDO")

    companies = data.get("data", {}).get("results", [])
    rucs = data.get("rucs", [])
    comparison = data.get("data", {}).get("comparison", {})
    generated_at = datetime.utcnow()

    buffer = BytesIO()
    width, height = letter
    c = canvas.Canvas(buffer, pagesize=letter)

    # Fondo oscuro
    c.setFillColor(COLOR_DARK_BG)
    c.rect(0, 0, width, height, fill=1, stroke=0)

    # Header
    c.setFillColor(COLOR_DARK_BG)
    c.rect(0, height - 100, width, 100, fill=1, stroke=0)
    c.setStrokeColor(COLOR_GOLD)
    c.setLineWidth(2)
    c.line(40, height - 100, width - 40, height - 100)

    c.setFillColor(COLOR_GOLD)
    c.setFont("Helvetica-Bold", 24)
    c.drawString(40, height - 55, "CONFLICT ZERO")

    c.setFillColor(COLOR_TEXT_DIM)
    c.setFont("Helvetica", 11)
    c.drawString(40, height - 80, f"Reporte de Comparación — {generated_at.strftime('%d/%m/%Y %H:%M')}")

    # Cantidad de empresas
    c.setFillColor(COLOR_TEXT)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, height - 140, f"Empresas comparadas: {len(companies)}")

    # Tabla de resultados
    y = height - 180
    row_height = 28
    col_x = [40, 140, 280, 380, 460, 540]
    col_w = [90, 130, 90, 70, 70, 70]

    # Header de tabla
    c.setFillColor(COLOR_GOLD)
    c.setFont("Helvetica-Bold", 9)
    headers = ["RUC", "RAZÓN SOCIAL", "SCORE", "RIESGO", "DEUDA", "SANC."]
    for i, h in enumerate(headers):
        c.drawString(col_x[i], y, h)

    y -= 8
    c.setStrokeColor(COLOR_GOLD)
    c.setLineWidth(0.5)
    c.line(40, y, width - 40, y)
    y -= row_height

    # Filas
    for company in companies:
        summary = company.get("summary", {})
        sunat = company.get("sunat", {})
        osce = company.get("osce", {})
        tce = company.get("tce", {})
        score = summary.get("final_score", summary.get("score", 0))
        risk = summary.get("risk_level", "unknown")
        total_sanc = (osce.get("total_sanciones", 0) + tce.get("total_sanciones", 0))

        c.setFillColor(COLOR_TEXT)
        c.setFont("Helvetica", 8)
        c.drawString(col_x[0], y + 8, summary.get("ruc", "")[:11])
        c.drawString(col_x[1], y + 8, summary.get("razon_social", "")[:22])

        # Score
        c.setFont("Helvetica-Bold", 9)
        c.drawString(col_x[2], y + 8, str(score))

        # Risk badge
        rc = risk_color(risk)
        c.setFillColor(rc)
        c.setStrokeColor(rc)
        c.roundRect(col_x[3] - 2, y + 2, 60, 16, 4, fill=1, stroke=1)
        c.setFillColor(COLOR_DARK_BG)
        c.setFont("Helvetica-Bold", 7)
        label = risk_label(risk)
        c.drawString(col_x[3] + 4, y + 6, label)

        c.setFillColor(COLOR_TEXT)
        c.setFont("Helvetica", 8)
        c.drawString(col_x[4], y + 8, f"S/ {sunat.get('deuda', 0):,.0f}")
        c.drawString(col_x[5], y + 8, str(total_sanc))

        # Línea separadora sutil
        c.setStrokeColor(HexColor("#222222"))
        c.setLineWidth(0.3)
        c.line(40, y - 2, width - 40, y - 2)

        y -= row_height
        if y < 120:
            c.showPage()
            c.setFillColor(COLOR_DARK_BG)
            c.rect(0, 0, width, height, fill=1, stroke=0)
            y = height - 60

    # Análisis comparativo
    if comparison:
        y -= 30
        if y < 200:
            c.showPage()
            c.setFillColor(COLOR_DARK_BG)
            c.rect(0, 0, width, height, fill=1, stroke=0)
            y = height - 60

        c.setStrokeColor(COLOR_GOLD)
        c.setLineWidth(1)
        c.line(40, y, width - 40, y)
        y -= 25

        c.setFillColor(COLOR_GOLD_LIGHT)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(40, y, "ANÁLISIS COMPARATIVO")
        y -= 20

        c.setFillColor(COLOR_TEXT)
        c.setFont("Helvetica", 10)
        if comparison.get("best"):
            best = comparison["best"]
            c.drawString(40, y, f"✓ Mejor opción: {best.get('name', '')} (Score: {best.get('score', 0)})")
            y -= 16
        if comparison.get("worst"):
            worst = comparison["worst"]
            c.drawString(40, y, f"⚠ Mayor riesgo: {worst.get('name', '')} (Score: {worst.get('score', 0)})")
            y -= 16
        if comparison.get("average_score"):
            c.drawString(40, y, f"→ Score promedio: {comparison['average_score']:.1f}")
            y -= 16

    # Footer
    c.setFillColor(COLOR_TEXT_DIM)
    c.setFont("Helvetica", 8)
    c.drawString(40, 30, f"Generado por Conflict Zero — conflictzero.com — {generated_at.strftime('%Y')}")

    c.save()
    buffer.seek(0)
    pdf_bytes = buffer.getvalue()
    buffer.close()

    return {
        "format": "pdf",
        "content": pdf_bytes,
        "filename": f"comparacion_{generated_at.strftime('%Y%m%d_%H%M%S')}.pdf",
        "companies_count": len(companies),
        "content_type": "application/pdf"
    }
