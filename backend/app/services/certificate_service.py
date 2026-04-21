"""
Conflict Zero - Certificate PDF Service
Generación de certificados PDF de verificación
"""

import os
import hashlib
import uuid
from datetime import datetime
from io import BytesIO
from typing import Optional

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, black, white
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image
import qrcode


class CertificateService:
    """
    Servicio para generar certificados PDF de verificación.
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

    def __init__(self, certificates_dir: str = "static/certificates"):
        self.certificates_dir = certificates_dir
        os.makedirs(certificates_dir, exist_ok=True)

    def _risk_color(self, risk_level: str) -> HexColor:
        """Retorna el color según nivel de riesgo"""
        mapping = {
            "bajo": self.COLOR_GREEN,
            "moderado": self.COLOR_YELLOW,
            "alto": self.COLOR_ORANGE,
            "crítico": self.COLOR_RED,
            "low": self.COLOR_GREEN,
            "moderate": self.COLOR_YELLOW,
            "high": self.COLOR_ORANGE,
            "critical": self.COLOR_RED,
        }
        return mapping.get(risk_level.lower(), self.COLOR_TEXT)

    def _risk_label(self, risk_level: str) -> str:
        """Retorna etiqueta localizada del riesgo"""
        mapping = {
            "bajo": "BAJO RIESGO",
            "moderado": "RIESGO MODERADO",
            "alto": "ALTO RIESGO",
            "crítico": "RIESGO CRÍTICO",
            "low": "BAJO RIESGO",
            "moderate": "RIESGO MODERADO",
            "high": "ALTO RIESGO",
            "critical": "RIESGO CRÍTICO",
        }
        return mapping.get(risk_level.lower(), "RIESGO DESCONOCIDO")

    def _draw_header(self, c: canvas.Canvas, width: float, height: float):
        """Dibuja el encabezado del certificado"""
        # Fondo oscuro superior
        c.setFillColor(self.COLOR_DARK_BG)
        c.rect(0, height - 120, width, 120, fill=1, stroke=0)

        # Línea dorada decorativa
        c.setStrokeColor(self.COLOR_GOLD)
        c.setLineWidth(2)
        c.line(50, height - 120, width - 50, height - 120)

        # Título
        c.setFillColor(self.COLOR_GOLD)
        c.setFont("Helvetica-Bold", 24)
        c.drawString(50, height - 60, "CONFLICT ZERO")

        # Subtítulo
        c.setFillColor(self.COLOR_TEXT_DIM)
        c.setFont("Helvetica", 12)
        c.drawString(50, height - 85, "Certificado de Verificación Predictiva")

        # Fecha
        c.setFillColor(self.COLOR_TEXT_DIM)
        c.setFont("Helvetica", 10)
        fecha_str = datetime.utcnow().strftime("%d de %B de %Y")
        c.drawRightString(width - 50, height - 60, f"Fecha: {fecha_str}")

    def _draw_score_circle(self, c: canvas.Canvas, x: float, y: float, score: int, risk_level: str):
        """Dibuja el círculo del score"""
        radius = 60
        color = self._risk_color(risk_level)

        # Círculo exterior dorado
        c.setStrokeColor(self.COLOR_GOLD)
        c.setLineWidth(3)
        c.circle(x, y, radius, fill=0, stroke=1)

        # Círculo interior con color de riesgo (semi-transparente visual)
        c.setFillColor(color)
        c.setStrokeColor(color)
        c.setLineWidth(1)
        c.circle(x, y, radius - 8, fill=1, stroke=0)

        # Score
        c.setFillColor(self.COLOR_DARK_BG)
        c.setFont("Helvetica-Bold", 28)
        score_text = str(score)
        text_width = c.stringWidth(score_text, "Helvetica-Bold", 28)
        c.drawString(x - text_width / 2, y - 8, score_text)

        # Label de riesgo debajo
        c.setFillColor(color)
        c.setFont("Helvetica-Bold", 10)
        label = self._risk_label(risk_level)
        label_width = c.stringWidth(label, "Helvetica-Bold", 10)
        c.drawString(x - label_width / 2, y - radius - 15, label)

    def _draw_data_row(self, c: canvas.Canvas, x: float, y: float, label: str, value: str, is_alert: bool = False):
        """Dibuja una fila de datos"""
        c.setFillColor(self.COLOR_TEXT_DIM)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(x, y, f"{label}:")

        if is_alert:
            c.setFillColor(self.COLOR_RED)
        else:
            c.setFillColor(self.COLOR_TEXT)
        c.setFont("Helvetica", 10)
        c.drawString(x + 150, y, str(value))

    def generate_certificate(
        self,
        verification_id: str,
        ruc_hash: str,
        company_name: Optional[str],
        score: int,
        risk_level: str,
        sunat_debt: float,
        sunat_tax_status: Optional[str],
        sunat_contributor_status: Optional[str],
        osce_sanctions_count: int,
        tce_sanctions_count: int,
        consultant_name: Optional[str] = None,
        certificate_id: Optional[str] = None
    ) -> tuple[str, str]:
        """
        Genera un certificado PDF y retorna (file_path, hash).

        Args:
            verification_id: ID de la verificación
            ruc_hash: Hash del RUC verificado
            company_name: Nombre de la empresa
            score: Score de 0-100
            risk_level: Nivel de riesgo (bajo/moderado/alto/crítico)
            sunat_debt: Deuda SUNAT
            sunat_tax_status: Estado tributario
            sunat_contributor_status: Estado del contribuyente
            osce_sanctions_count: Cantidad de sanciones OSCE
            tce_sanctions_count: Cantidad de sanciones TCE
            consultant_name: Nombre del consultor que solicitó
            certificate_id: ID opcional del certificado

        Returns:
            (file_path, hash_sha256)
        """
        if not certificate_id:
            certificate_id = str(uuid.uuid4())

        filename = f"CZ_{certificate_id[:8].upper()}.pdf"
        filepath = os.path.join(self.certificates_dir, filename)

        width, height = letter
        c = canvas.Canvas(filepath, pagesize=letter)

        # Fondo oscuro completo
        c.setFillColor(self.COLOR_DARK_BG)
        c.rect(0, 0, width, height, fill=1, stroke=0)

        # Header
        self._draw_header(c, width, height)

        # Score principal
        self._draw_score_circle(c, width / 2, height - 220, score, risk_level)

        # Info de la empresa
        y_start = height - 320
        c.setFillColor(self.COLOR_GOLD)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, y_start, "INFORMACIÓN DE LA EMPRESA")

        c.setStrokeColor(self.COLOR_GOLD)
        c.setLineWidth(1)
        c.line(50, y_start - 5, 250, y_start - 5)

        row_y = y_start - 30
        self._draw_data_row(c, 50, row_y, "RUC (Hash)", ruc_hash[:16] + "...")
        row_y -= 20
        self._draw_data_row(c, 50, row_y, "Razón Social", company_name or "No disponible")
        row_y -= 20
        self._draw_data_row(c, 50, row_y, "Verificado por", consultant_name or "Sistema Conflict Zero")

        # Detalles de verificación
        y_verif = height - 420
        c.setFillColor(self.COLOR_GOLD)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, y_verif, "DETALLES DE VERIFICACIÓN")
        c.setStrokeColor(self.COLOR_GOLD)
        c.setLineWidth(1)
        c.line(50, y_verif - 5, 250, y_verif - 5)

        row_y = y_verif - 30
        self._draw_data_row(c, 50, row_y, "Deuda SUNAT", f"S/ {sunat_debt:,.2f}", is_alert=sunat_debt > 0)
        row_y -= 20
        self._draw_data_row(c, 50, row_y, "Estado Tributario", sunat_tax_status or "No disponible")
        row_y -= 20
        self._draw_data_row(c, 50, row_y, "Estado Contribuyente", sunat_contributor_status or "No disponible")
        row_y -= 20
        self._draw_data_row(c, 50, row_y, "Sanciones OSCE", str(osce_sanctions_count), is_alert=osce_sanctions_count > 0)
        row_y -= 20
        self._draw_data_row(c, 50, row_y, "Sanciones TCE", str(tce_sanctions_count), is_alert=tce_sanctions_count > 0)

        # Score desglose
        y_score = height - 560
        c.setFillColor(self.COLOR_GOLD)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, y_score, "DESGLOSE DEL SCORE")
        c.setStrokeColor(self.COLOR_GOLD)
        c.setLineWidth(1)
        c.line(50, y_score - 5, 250, y_score - 5)

        row_y = y_score - 30
        c.setFillColor(self.COLOR_TEXT_DIM)
        c.setFont("Helvetica", 9)
        c.drawString(50, row_y, "El score se calcula ponderando: SUNAT (30%), OSCE (40%), y análisis predictivo (30%).")
        row_y -= 15
        c.drawString(50, row_y, "Este certificado tiene validez de 30 días desde la fecha de emisión.")

        # QR Code de verificación
        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=4,
                border=2
            )
            qr.add_data(f"https://czperu.com/verify/cert/{certificate_id}")
            qr.make(fit=True)
            qr_img = qr.make_image(fill_color="#c9a84c", back_color="#0a0a0f")
            qr_buffer = BytesIO()
            qr_img.save(qr_buffer, format="PNG")
            qr_buffer.seek(0)
            qr_reader = ImageReader(qr_buffer)
            c.drawImage(qr_reader, width - 150, 80, width=100, height=100)

            c.setFillColor(self.COLOR_TEXT_DIM)
            c.setFont("Helvetica", 8)
            c.drawRightString(width - 50, 70, "Escanea para verificar autenticidad")
        except Exception:
            pass  # Si falla el QR, no romper el certificado

        # Footer
        c.setStrokeColor(self.COLOR_GOLD)
        c.setLineWidth(1)
        c.line(50, 60, width - 50, 60)

        c.setFillColor(self.COLOR_TEXT_DIM)
        c.setFont("Helvetica", 8)
        c.drawString(50, 45, f"Certificado ID: {certificate_id}  |  Este documento es generado electrónicamente por Conflict Zero.")
        c.drawString(50, 30, "Conflict Zero — Verificación Predictiva de Riesgo para RUCs Peruanos  |  www.czperu.com")

        c.save()

        # Calcular hash
        with open(filepath, "rb") as f:
            file_hash = hashlib.sha256(f.read()).hexdigest()

        return filepath, file_hash

    def delete_certificate(self, filename: str) -> bool:
        """Elimina un certificado del disco"""
        filepath = os.path.join(self.certificates_dir, filename)
        if os.path.exists(filepath):
            os.remove(filepath)
            return True
        return False


# Instancia singleton
certificate_service = CertificateService()
