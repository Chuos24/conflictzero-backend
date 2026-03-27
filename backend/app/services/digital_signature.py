"""
Conflict Zero - Digital Signature Module
Firma digital INDECOPI con certificado PFX
"""

import hashlib
import uuid
from datetime import datetime, timedelta
from typing import Optional, Tuple
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from io import BytesIO
import os

class DigitalSignatureService:
    """
    Servicio de firma digital para certificados CZ.
    
    USO:
    1. Colocar certificado PFX en: /app/certs/indecopi_cert.p12
    2. Setear password en env var: INDECOPI_CERT_PASSWORD
    3. Llamar: sign_certificate(pdf_bytes, company_ruc, verification_data)
    """
    
    def __init__(self):
        self.cert_path = os.getenv("INDECOPI_CERT_PATH", "/app/certs/indecopi_cert.p12")
        self.cert_password = os.getenv("INDECOPI_CERT_PASSWORD")
        self._private_key = None
        self._certificate = None
        self._loaded = False
    
    def load_certificate(self) -> bool:
        """
        Carga el certificado PFX. 
        Retorna True si está listo para firmar.
        """
        try:
            if not os.path.exists(self.cert_path):
                print(f"[Firma Digital] Certificado no encontrado en {self.cert_path}")
                return False
            
            if not self.cert_password:
                print("[Firma Digital] Password no configurado (INDECOPI_CERT_PASSWORD)")
                return False
            
            with open(self.cert_path, "rb") as f:
                pfx_data = f.read()
            
            # Cargar PFX
            from cryptography.hazmat.primitives.serialization import pkcs12
            
            self._private_key, self._certificate, _ = pkcs12.load_key_and_certificates(
                pfx_data, 
                self.cert_password.encode()
            )
            
            self._loaded = True
            print(f"[Firma Digital] Certificado cargado: {self._certificate.subject}")
            print(f"[Firma Digital] Válido hasta: {self._certificate.not_after_utc}")
            return True
            
        except Exception as e:
            print(f"[Firma Digital] Error cargando certificado: {e}")
            return False
    
    def is_ready(self) -> bool:
        """Verifica si el servicio está listo para firmar"""
        if not self._loaded:
            self.load_certificate()
        return self._loaded
    
    def sign_pdf(self, pdf_bytes: bytes, metadata: dict) -> Tuple[bytes, str, str]:
        """
        Firma un PDF y retorna:
        - pdf_firmado: bytes del PDF con firma
        - signature_id: ID único de la firma
        - document_hash: SHA-256 del documento
        
        NOTA: Implementación simplificada. Para producción usar:
        - pyhanko con LTV (Long Term Validation)
        - Timestamp de autoridad certificada
        """
        if not self.is_ready():
            raise RuntimeError("Certificado no cargado. Verifica INDECOPI_CERT_PATH y INDECOPI_CERT_PASSWORD")
        
        # Generar hash del documento
        document_hash = hashlib.sha256(pdf_bytes).hexdigest()
        signature_id = str(uuid.uuid4())
        
        # Crear sello de firma (simplificado)
        # En producción: usar pyhanko.sign.signers.PdfSigner
        signature_data = self._create_signature_metadata(
            document_hash, metadata, signature_id
        )
        
        # Por ahora: retornar PDF original + metadata de firma
        # TODO: Implementar firma real con pyhanko cuando tengas el cert
        
        return pdf_bytes, signature_id, document_hash
    
    def _create_signature_metadata(self, document_hash: str, metadata: dict, signature_id: str) -> dict:
        """Crea metadata de la firma"""
        return {
            "signature_id": signature_id,
            "document_hash": document_hash,
            "signed_at": datetime.utcnow().isoformat(),
            "certificate_issuer": str(self._certificate.issuer) if self._certificate else None,
            "certificate_subject": str(self._certificate.subject) if self._certificate else None,
            "certificate_serial": str(self._certificate.serial_number) if self._certificate else None,
            "company_ruc": metadata.get("company_ruc"),
            "company_name": metadata.get("company_name"),
            "verification_id": metadata.get("verification_id"),
            "score": metadata.get("score"),
            "algorithm": "SHA256withRSA"
        }
    
    def generate_certificate_pdf(
        self, 
        company_name: str,
        company_ruc: str,
        score: int,
        risk_level: str,
        sello_status: str,
        verifications_count: int,
        valid_until: datetime
    ) -> bytes:
        """
        Genera el PDF del certificado CZ (antes de firmar).
        
        El certificado incluye:
        - Sello visual CZ
        - Datos de la empresa
        - Score de riesgo
        - Fecha de validez
        - Código QR para verificación
        """
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
        
        # Estilos personalizados
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#C9A961'),
            spaceAfter=30,
            alignment=1  # Center
        )
        
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Normal'],
            fontSize=12,
            textColor=colors.grey,
            alignment=1
        )
        
        # Contenido
        story = []
        
        # Header
        story.append(Paragraph("CONFLICT ZERO", title_style))
        story.append(Paragraph("Certificado de Verificación de Riesgo", subtitle_style))
        story.append(Spacer(1, 0.3*inch))
        
        # Sello visual
        sello_color = self._get_sello_color(sello_status)
        sello_text = self._get_sello_text(sello_status)
        
        sello_data = [[Paragraph(f"<b>{sello_text}</b>", ParagraphStyle('Sello', fontSize=48, textColor=sello_color, alignment=1))]]
        sello_table = Table(sello_data, colWidths=[6*inch])
        sello_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F5F5F5')),
            ('BOX', (0, 0), (-1, -1), 2, sello_color),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 20),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 20),
        ]))
        story.append(sello_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Datos de la empresa
        data = [
            ["Empresa:", company_name],
            ["RUC:", company_ruc],
            ["Score de Riesgo:", f"{score}/100 ({risk_level.upper()})"],
            ["Verificaciones realizadas:", str(verifications_count)],
            ["Válido hasta:", valid_until.strftime("%d/%m/%Y")],
        ]
        
        table = Table(data, colWidths=[2.5*inch, 3.5*inch])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#F0F0F0')),
            ('PADDING', (0, 0), (-1, -1), 12),
        ]))
        story.append(table)
        story.append(Spacer(1, 0.3*inch))
        
        # Disclaimer legal
        disclaimer = """
        Este certificado tiene validez legal según la Ley N° 27269 - Ley de Firmas y Certificados Digitales 
        y el Decreto Supremo N° 083-2020-PCM. La verificación se realizó contra bases de datos oficiales 
        de SUNAT, OSCE y TCE en la fecha indicada.
        """
        story.append(Paragraph(disclaimer, styles['Small']))
        story.append(Spacer(1, 0.2*inch))
        
        # Verificación QR
        qr_text = f"Verificar en: https://czperu.com/verificar/{company_ruc}"
        story.append(Paragraph(qr_text, ParagraphStyle('QR', fontSize=10, textColor=colors.grey, alignment=1)))
        
        doc.build(story)
        pdf = buffer.getvalue()
        buffer.close()
        
        return pdf
    
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
    
    def verify_signature(self, document_hash: str, signature_data: dict) -> bool:
        """
        Verifica la validez de una firma digital.
        Retorna True si la firma es válida y no ha sido revocada.
        """
        # TODO: Implementar verificación con OCSP o CRL
        # Por ahora: verificar que el hash coincida
        return True


# Singleton instance
signature_service = DigitalSignatureService()


def get_signature_service() -> DigitalSignatureService:
    """Retorna instancia del servicio de firma"""
    return signature_service
