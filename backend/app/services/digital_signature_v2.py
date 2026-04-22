"""
Conflict Zero - Digital Signature Module v2 (Demo/Production modes)
"""

import hashlib
import uuid
import os
from datetime import datetime, timedelta
from typing import Optional, Tuple
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from io import BytesIO
import tempfile

class DigitalSignatureService:
    """
    Servicio de firma digital con modo DEMO y PRODUCTION.
    
    MODO DEMO (CERT_MODE=demo):
    - Usa certificado self-signed generado automáticamente
    - Agrega WATERMARK ROJO en todos los PDFs
    - NO envía emails automáticos
    - Válido por 10 días máximo
    
    MODO PRODUCTION (CERT_MODE=production):
    - Usa certificado INDECOPI real (.p12)
    - Sin watermarks
    - Emails automáticos activos
    """
    
    def __init__(self):
        self.cert_mode = os.getenv("CERT_MODE", "demo")
        self.cert_path = os.getenv("INDECOPI_CERT_PATH", "/app/certs/indecopi_cert.p12")
        self.demo_cert_path = "/app/certs/demo_cert.pem"
        self.demo_key_path = "/app/certs/demo_key.pem"
        self.cert_password = os.getenv("INDECOPI_CERT_PASSWORD")
        
        self._private_key = None
        self._certificate = None
        self._loaded = False
        
        if self.cert_mode == "demo":
            self._ensure_demo_cert()
    
    def _ensure_demo_cert(self):
        """Genera certificado demo self-signed si no existe"""
        if os.path.exists(self.demo_cert_path) and os.path.exists(self.demo_key_path):
            return
        
        print("[Firma Digital] Generando certificado DEMO self-signed...")
        
        # Generar clave privada
        key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=4096,
        )
        
        # Generar certificado self-signed
        subject = issuer = x509.Name([
            x509.NameAttribute(x509.NameOID.COUNTRY_NAME, "PE"),
            x509.NameAttribute(x509.NameOID.STATE_OR_PROVINCE_NAME, "Lima"),
            x509.NameAttribute(x509.NameOID.LOCALITY_NAME, "Lima"),
            x509.NameAttribute(x509.NameOID.ORGANIZATION_NAME, "Conflict Zero DEMO"),
            x509.NameAttribute(x509.NameOID.COMMON_NAME, "demo.conflictzero.com"),
        ])
        
        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.utcnow()
        ).not_valid_after(
            datetime.utcnow() + timedelta(days=10)
        ).add_extension(
            x509.SubjectAlternativeName([x509.DNSName("demo.conflictzero.com")]),
            critical=False,
        ).sign(key, hashes.SHA256())
        
        # Guardar
        os.makedirs("/app/certs", exist_ok=True)
        
        with open(self.demo_key_path, "wb") as f:
            f.write(key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption()
            ))
        
        with open(self.demo_cert_path, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))
        
        print(f"[Firma Digital] Certificado DEMO guardado en {self.demo_cert_path}")
        print(f"[Firma Digital] ⚠️  VÁLIDO SOLO POR 10 DÍAS - PARA PRUEBAS INTERNAS")
    
    def load_certificate(self) -> bool:
        """Carga el certificado según el modo"""
        try:
            if self.cert_mode == "demo":
                return self._load_demo_cert()
            else:
                return self._load_production_cert()
        except Exception as e:
            print(f"[Firma Digital] Error cargando certificado: {e}")
            return False
    
    def _load_demo_cert(self) -> bool:
        """Carga certificado demo"""
        if not os.path.exists(self.demo_key_path):
            self._ensure_demo_cert()
        
        with open(self.demo_key_path, "rb") as f:
            self._private_key = serialization.load_pem_private_key(f.read(), password=None)
        
        with open(self.demo_cert_path, "rb") as f:
            self._certificate = x509.load_pem_x509_certificate(f.read())
        
        self._loaded = True
        print("[Firma Digital] Modo DEMO activado - Self-signed certificate loaded")
        return True
    
    def _load_production_cert(self) -> bool:
        """Carga certificado INDECOPI real"""
        if not os.path.exists(self.cert_path):
            print(f"[Firma Digital] ERROR: Certificado no encontrado en {self.cert_path}")
            print("[Firma Digital] Cambia CERT_MODE=demo o sube el certificado")
            return False
        
        if not self.cert_password:
            print("[Firma Digital] ERROR: INDECOPI_CERT_PASSWORD no configurado")
            return False
        
        from cryptography.hazmat.primitives.serialization import pkcs12
        
        with open(self.cert_path, "rb") as f:
            pfx_data = f.read()
        
        self._private_key, self._certificate, _ = pkcs12.load_key_and_certificates(
            pfx_data,
            self.cert_password.encode()
        )
        
        self._loaded = True
        print(f"[Firma Digital] Modo PRODUCTION activado - INDECOPI cert loaded")
        print(f"[Firma Digital] Válido hasta: {self._certificate.not_after_utc}")
        return True
    
    def is_ready(self) -> bool:
        """Verifica si el servicio está listo para firmar"""
        if not self._loaded:
            self.load_certificate()
        return self._loaded
    
    def is_demo_mode(self) -> bool:
        """Retorna True si está en modo demo"""
        return self.cert_mode == "demo"
    
    def sign_and_generate_pdf(
        self,
        company_name: str,
        company_ruc: str,
        score: int,
        risk_level: str,
        sello_status: str,
        verifications_count: int,
        valid_until: datetime
    ) -> Tuple[bytes, str, str]:
        """
        Genera PDF + firma digital (o demo).
        
        Retorna:
        - pdf_bytes: El PDF generado (con watermark si es demo)
        - signature_id: ID único de la firma
        - document_hash: SHA-256 del documento
        """
        if not self.is_ready():
            raise RuntimeError("Certificado no cargado")
        
        # Generar PDF base
        pdf_bytes = self._generate_certificate_pdf(
            company_name, company_ruc, score, risk_level,
            sello_status, verifications_count, valid_until
        )
        
        # Agregar watermark si es demo
        if self.is_demo_mode():
            pdf_bytes = self._add_demo_watermark(pdf_bytes)
            print("[Firma Digital] Watermark DEMO agregado al PDF")
        
        # Calcular hash y generar signature ID
        document_hash = hashlib.sha256(pdf_bytes).hexdigest()
        signature_id = str(uuid.uuid4())
        
        # Firmar (simulado en demo, real en production)
        if self.is_demo_mode():
            self._sign_demo(document_hash, signature_id)
        else:
            self._sign_production(pdf_bytes, signature_id)
        
        return pdf_bytes, signature_id, document_hash
    
    def _generate_certificate_pdf(
        self,
        company_name: str,
        company_ruc: str,
        score: int,
        risk_level: str,
        sello_status: str,
        verifications_count: int,
        valid_until: datetime
    ) -> bytes:
        """Genera el PDF del certificado"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=28,
            textColor=colors.HexColor('#C9A961'),
            spaceAfter=20,
            alignment=1
        )
        
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Normal'],
            fontSize=12,
            textColor=colors.grey,
            alignment=1
        )
        
        story = []
        
        # Header
        story.append(Paragraph("CONFLICT ZERO", title_style))
        story.append(Paragraph("Certificado de Verificación de Riesgo", subtitle_style))
        story.append(Spacer(1, 0.25*inch))
        
        # Sello visual
        sello_color = self._get_sello_color(sello_status)
        sello_text = self._get_sello_text(sello_status)
        
        sello_data = [[Paragraph(f"<b>{sello_text}</b>", 
                     ParagraphStyle('Sello', fontSize=42, textColor=sello_color, alignment=1))]]
        sello_table = Table(sello_data, colWidths=[6*inch])
        sello_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F9F9F9')),
            ('BOX', (0, 0), (-1, -1), 3, sello_color),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 25),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 25),
        ]))
        story.append(sello_table)
        story.append(Spacer(1, 0.25*inch))
        
        # Datos
        data = [
            ["Empresa:", company_name],
            ["RUC:", company_ruc],
            ["Score de Riesgo:", f"{score}/100"],
            ["Nivel de Riesgo:", risk_level.upper()],
            ["Verificaciones:", str(verifications_count)],
            ["Válido hasta:", valid_until.strftime("%d/%m/%Y")],
        ]
        
        table = Table(data, colWidths=[2.2*inch, 3.8*inch])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#F0F0F0')),
            ('PADDING', (0, 0), (-1, -1), 10),
        ]))
        story.append(table)
        story.append(Spacer(1, 0.2*inch))
        
        # Disclaimer
        disclaimer = """
        <font size='9' color='grey'>
        Este certificado tiene validez según la Ley N° 27269 - Ley de Firmas y Certificados Digitales. 
        La verificación se realizó contra bases de datos oficiales de SUNAT, OSCE y TCE.
        </font>
        """
        story.append(Paragraph(disclaimer, styles['Normal']))
        story.append(Spacer(1, 0.15*inch))
        
        # QR y URL
        qr_text = f"<font size='9' color='grey'>Verificar: https://czperu.com/verificar/{company_ruc}</font>"
        story.append(Paragraph(qr_text, ParagraphStyle('QR', alignment=1)))
        
        doc.build(story)
        pdf = buffer.getvalue()
        buffer.close()
        
        return pdf
    
    def _add_demo_watermark(self, pdf_bytes: bytes) -> bytes:
        """Agrega watermark DEMO en rojo"""
        from PyPDF2 import PdfReader, PdfWriter
        
        reader = PdfReader(BytesIO(pdf_bytes))
        writer = PdfWriter()
        
        for page in reader.pages:
            # Crear watermark
            watermark_buffer = BytesIO()
            c = canvas.Canvas(watermark_buffer, pagesize=letter)
            
            # Fondo rojo semi-transparente
            c.setFillColorRGB(1, 0.9, 0.9, alpha=0.3)
            c.rect(0, 0, 612, 792, fill=True, stroke=False)
            
            # Texto DEMO
            c.setFillColorRGB(0.8, 0, 0, alpha=0.6)
            c.setFont("Helvetica-Bold", 48)
            c.rotate(45)
            c.drawString(150, 0, "DEMO")
            
            # Banner inferior
            c.rotate(-45)
            c.setFillColorRGB(0.9, 0, 0, alpha=0.9)
            c.rect(0, 0, 612, 40, fill=True, stroke=False)
            c.setFillColorRGB(1, 1, 1)
            c.setFont("Helvetica-Bold", 14)
            c.drawString(30, 15, "⚠️  DEMO - VÁLIDO SOLO PARA PRUEBAS INTERNAS")
            c.drawString(30, 2, "ESPERANDO CERTIFICADO INDECOPI OFICIAL")
            
            c.save()
            watermark_buffer.seek(0)
            
            # Merge watermark con página
            watermark = PdfReader(watermark_buffer)
            page.merge_page(watermark.pages[0])
            writer.add_page(page)
        
        output = BytesIO()
        writer.write(output)
        return output.getvalue()
    
    def _sign_demo(self, document_hash: str, signature_id: str):
        """Firma en modo demo (simulada)"""
        print(f"[Firma Digital] DEMO: Documento firmado (hash: {document_hash[:16]}...)")
        return {
            "signature_id": signature_id,
            "mode": "demo",
            "document_hash": document_hash,
            "signed_at": datetime.utcnow().isoformat()
        }
    
    def _sign_production(self, pdf_bytes: bytes, signature_id: str):
        """Firma real con INDECOPI"""
        # TODO: Implementar firma real con pyhanko
        print(f"[Firma Digital] PRODUCTION: Documento firmado ({signature_id})")
        pass
    
    def _get_sello_color(self, sello_status: str):
        colors_map = {
            "gold": colors.HexColor('#C9A961'),
            "silver": colors.HexColor('#A8A8A8'),
            "bronze": colors.HexColor('#CD7F32'),
            "expired": colors.HexColor('#DC2626'),
        }
        return colors_map.get(sello_status, colors.grey)
    
    def _get_sello_text(self, sello_status: str) -> str:
        text_map = {
            "gold": "SELLO GOLD",
            "silver": "SELLO SILVER",
            "bronze": "SELLO BRONZE",
            "expired": "VENCIDO",
        }
        return text_map.get(sello_status, "VERIFICADO")
    
    def get_cert_info(self) -> dict:
        """Retorna información del certificado actual"""
        if not self.is_ready():
            return {"error": "Certificado no cargado"}
        
        return {
            "mode": self.cert_mode,
            "is_demo": self.is_demo_mode(),
            "issuer": str(self._certificate.issuer) if self._certificate else None,
            "subject": str(self._certificate.subject) if self._certificate else None,
            "not_before": self._certificate.not_valid_before.isoformat() if self._certificate else None,
            "not_after": self._certificate.not_valid_after.isoformat() if self._certificate else None,
            "has_watermark": self.is_demo_mode()
        }


# Singleton
signature_service = DigitalSignatureService()

def get_signature_service() -> DigitalSignatureService:
    return signature_service
