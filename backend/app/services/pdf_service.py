"""
PDF Generation Service for Audit Reports
Genera PDFs profesionales usando ReportLab
"""

import os
import hashlib
from datetime import datetime, timezone
from io import BytesIO
from typing import Dict, Any, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image, ListFlowable, ListItem, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfgen import canvas


class PDFReportGenerator:
    """Generador de PDFs para reportes de auditoría"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Configura estilos personalizados"""
        self.styles.add(ParagraphStyle(
            name='ReportTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            leading=30,
            alignment=TA_CENTER,
            spaceAfter=20,
            textColor=colors.HexColor('#1a1a2e')
        ))
        
        self.styles.add(ParagraphStyle(
            name='ReportSubtitle',
            parent=self.styles['Heading2'],
            fontSize=14,
            leading=18,
            alignment=TA_CENTER,
            spaceAfter=30,
            textColor=colors.HexColor('#4a4a6a')
        ))
        
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=16,
            leading=20,
            spaceBefore=20,
            spaceAfter=10,
            textColor=colors.HexColor('#16213e'),
            borderColor=colors.HexColor('#e94560'),
            borderWidth=2,
            borderPadding=5,
            leftIndent=0,
            backColor=colors.HexColor('#f8f9fa')
        ))
        
        self.styles.add(ParagraphStyle(
            name='ReportBodyText',
            parent=self.styles['BodyText'],
            fontSize=10,
            leading=14,
            alignment=TA_JUSTIFY,
            spaceAfter=8
        ))
        
        self.styles.add(ParagraphStyle(
            name='Footer',
            parent=self.styles['Normal'],
            fontSize=8,
            leading=10,
            alignment=TA_CENTER,
            textColor=colors.grey
        ))
    
    def _draw_header_footer(self, canvas_obj, doc):
        """Dibuja header y footer en cada página"""
        canvas_obj.saveState()
        
        # Header
        canvas_obj.setFont('Helvetica-Bold', 10)
        canvas_obj.setFillColor(colors.HexColor('#1a1a2e'))
        canvas_obj.drawString(72, letter[1] - 40, "CONFLICT ZERO")
        canvas_obj.setFont('Helvetica', 8)
        canvas_obj.setFillColor(colors.grey)
        canvas_obj.drawString(72, letter[1] - 52, "Reporte de Auditoría")
        
        # Linea decorativa
        canvas_obj.setStrokeColor(colors.HexColor('#e94560'))
        canvas_obj.setLineWidth(2)
        canvas_obj.line(72, letter[1] - 60, letter[0] - 72, letter[1] - 60)
        
        # Footer
        canvas_obj.setFont('Helvetica', 8)
        canvas_obj.setFillColor(colors.grey)
        canvas_obj.drawString(72, 40, f"Generado: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
        canvas_obj.drawRightString(letter[0] - 72, 40, f"Página {doc.page}")
        
        canvas_obj.restoreState()
    
    def generate_audit_report(self, report_data: Dict[str, Any], 
                             report_number: str,
                             company_name: str = "Empresa") -> bytes:
        """
        Genera un PDF de reporte de auditoría.
        
        Args:
            report_data: Datos del reporte (dict con estructura del reporte)
            report_number: Número del reporte
            company_name: Nombre de la empresa
            
        Returns:
            bytes: Contenido del PDF
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=80,
            bottomMargin=60
        )
        
        elements = []
        
        # === PORTADA ===
        elements.append(Spacer(1, 2*inch))
        elements.append(Paragraph("CONFLICT ZERO", self.styles['ReportTitle']))
        elements.append(Paragraph("Reporte de Auditoría", self.styles['ReportSubtitle']))
        
        elements.append(Spacer(1, 0.5*inch))
        
        # Info del reporte
        info_data = [
            ["Número de Reporte:", report_number],
            ["Empresa:", company_name],
            ["Fecha de Generación:", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")],
            ["Tipo:", report_data.get('report_type', 'No especificado').upper()],
            ["Período:", f"{report_data.get('period_start', 'N/A')} - {report_data.get('period_end', 'N/A')}"],
        ]
        
        info_table = Table(info_data, colWidths=[2*inch, 4*inch])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8f9fa')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        elements.append(info_table)
        
        elements.append(Spacer(1, 0.5*inch))
        
        # Estado del reporte
        status = report_data.get('status', 'completed')
        status_colors = {
            'completed': colors.green,
            'pending': colors.orange,
            'generating': colors.blue,
            'failed': colors.red
        }
        status_color = status_colors.get(status, colors.grey)
        
        status_data = [["Estado:", status.upper()]]
        status_table = Table(status_data, colWidths=[2*inch, 4*inch])
        status_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BACKGROUND', (1, 0), (1, -1), status_color),
            ('TEXTCOLOR', (1, 0), (1, -1), colors.white),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('LEFTPADDING', (1, 0), (1, -1), 10),
        ]))
        elements.append(status_table)
        
        elements.append(PageBreak())
        
        # === CONTENIDO DEL REPORTE ===
        elements.append(Paragraph("Resumen Ejecutivo", self.styles['SectionHeader']))
        
        summary = report_data.get('summary', 'No hay resumen disponible para este período.')
        elements.append(Paragraph(summary, self.styles['ReportBodyText']))
        elements.append(Spacer(1, 0.2*inch))
        
        # Métricas clave
        elements.append(Paragraph("Métricas Clave", self.styles['SectionHeader']))
        
        metrics = report_data.get('metrics', {})
        if metrics:
            metric_rows = []
            for key, value in metrics.items():
                # Formatear key
                label = key.replace('_', ' ').title()
                metric_rows.append([label, str(value)])
            
            if metric_rows:
                metric_table = Table(metric_rows, colWidths=[3*inch, 3*inch])
                metric_table.setStyle(TableStyle([
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                    ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                    ('TOPPADDING', (0, 0), (-1, -1), 6),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
                    ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
                ]))
                elements.append(metric_table)
        else:
            elements.append(Paragraph("No hay métricas disponibles para este período.", self.styles['ReportBodyText']))
        
        elements.append(Spacer(1, 0.2*inch))
        
        # Hallazgos
        elements.append(Paragraph("Hallazgos", self.styles['SectionHeader']))
        
        findings = report_data.get('findings', [])
        if findings:
            for i, finding in enumerate(findings, 1):
                severity = finding.get('severity', 'info')
                severity_colors = {
                    'critical': colors.HexColor('#dc3545'),
                    'high': colors.HexColor('#fd7e14'),
                    'medium': colors.HexColor('#ffc107'),
                    'low': colors.HexColor('#17a2b8'),
                    'info': colors.HexColor('#6c757d')
                }
                sev_color = severity_colors.get(severity, colors.grey)
                
                finding_text = f"<b>{i}. {finding.get('title', 'Hallazgo sin título')}</b><br/>"
                finding_text += f"<font color='{sev_color.hexval()}'><b>Severidad: {severity.upper()}</b></font><br/>"
                finding_text += f"{finding.get('description', 'Sin descripción')}<br/>"
                if finding.get('recommendation'):
                    finding_text += f"<i>Recomendación: {finding['recommendation']}</i>"
                
                elements.append(Paragraph(finding_text, self.styles['ReportBodyText']))
                elements.append(Spacer(1, 0.1*inch))
        else:
            elements.append(Paragraph("No se identificaron hallazgos para este período.", self.styles['ReportBodyText']))
        
        elements.append(Spacer(1, 0.2*inch))
        
        # Recomendaciones
        elements.append(Paragraph("Recomendaciones", self.styles['SectionHeader']))
        
        recommendations = report_data.get('recommendations', [])
        if recommendations:
            for rec in recommendations:
                elements.append(Paragraph(f"• {rec}", self.styles['ReportBodyText']))
        else:
            elements.append(Paragraph("No hay recomendaciones pendientes.", self.styles['ReportBodyText']))
        
        elements.append(PageBreak())
        
        # === DETALLES TÉCNICOS ===
        elements.append(Paragraph("Detalles Técnicos", self.styles['SectionHeader']))
        
        # Firmas de integridad
        elements.append(Paragraph("Integridad del Documento", self.styles['SectionHeader']))
        
        integrity_hash = report_data.get('integrity_hash')
        if integrity_hash:
            integrity_data = [
                ["Hash SHA-256:", integrity_hash],
                ["Algoritmo:", "SHA-256"],
                ["Generado por:", report_data.get('generated_by', 'Sistema')],
            ]
            integrity_table = Table(integrity_data, colWidths=[2*inch, 4*inch])
            integrity_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#fff3cd')),
            ]))
            elements.append(integrity_table)
        else:
            elements.append(Paragraph("Hash de integridad no disponible.", self.styles['ReportBodyText']))
        
        elements.append(Spacer(1, 0.3*inch))
        
        # Disclaimer legal
        elements.append(Paragraph("Aviso Legal", self.styles['SectionHeader']))
        disclaimer = """
        Este documento es confidencial y está destinado únicamente al uso interno de la empresa titular. 
        La información contenida en este reporte se basa en datos disponibles al momento de su generación. 
        Conflict Zero no se hace responsable por decisiones tomadas basadas en este reporte sin consulta 
        adicional con asesores legales o de cumplimiento cualificados. Los datos personales contenidos 
        en este documento están protegidos bajo las leyes de protección de datos aplicables (Ley 29733, RGPD).
        """
        elements.append(Paragraph(disclaimer, self.styles['ReportBodyText']))
        
        # Construir PDF
        doc.build(elements, onFirstPage=self._draw_header_footer, onLaterPages=self._draw_header_footer)
        
        pdf_content = buffer.getvalue()
        buffer.close()
        
        return pdf_content
    
    def generate_gdpr_export_pdf(self, export_data: Dict[str, Any], 
                                  company_name: str,
                                  request_number: str) -> bytes:
        """
        Genera PDF de exportación GDPR (Art. 20 - Portabilidad)
        
        Args:
            export_data: Datos exportados del titular
            company_name: Nombre de la empresa
            request_number: Número de solicitud GDPR
            
        Returns:
            bytes: Contenido del PDF
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=80,
            bottomMargin=60
        )
        
        elements = []
        
        # Título
        elements.append(Spacer(1, 1*inch))
        elements.append(Paragraph("EXPORTACIÓN DE DATOS PERSONALES", self.styles['ReportTitle']))
        elements.append(Paragraph("Solicitud GDPR - Derecho a la Portabilidad (Art. 20)", self.styles['ReportSubtitle']))
        elements.append(Spacer(1, 0.3*inch))
        
        # Info de la solicitud
        info_data = [
            ["Solicitud:", request_number],
            ["Empresa:", company_name],
            ["Fecha de Exportación:", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")],
            ["Formato:", "PDF (Portable Document Format)"],
        ]
        
        info_table = Table(info_data, colWidths=[2.5*inch, 4*inch])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#e8f5e9')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#4caf50')),
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 0.3*inch))
        
        # Categorías de datos
        elements.append(Paragraph("Categorías de Datos Incluidos", self.styles['SectionHeader']))
        
        categories = export_data.get('data_categories', [])
        if categories:
            for cat in categories:
                elements.append(Paragraph(f"• {cat.replace('_', ' ').title()}", self.styles['ReportBodyText']))
        else:
            elements.append(Paragraph("No se especificaron categorías de datos.", self.styles['ReportBodyText']))
        
        elements.append(PageBreak())
        
        # Perfil
        elements.append(Paragraph("Perfil de la Empresa", self.styles['SectionHeader']))
        profile = export_data.get('data', {}).get('profile', {})
        if profile:
            profile_rows = []
            for key, value in profile.items():
                label = key.replace('_', ' ').title()
                profile_rows.append([label, str(value)])
            
            profile_table = Table(profile_rows, colWidths=[3*inch, 3*inch])
            profile_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
                ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
            ]))
            elements.append(profile_table)
        else:
            elements.append(Paragraph("No hay datos de perfil disponibles.", self.styles['ReportBodyText']))
        
        elements.append(Spacer(1, 0.2*inch))
        
        # Verificaciones
        elements.append(Paragraph("Historial de Verificaciones", self.styles['SectionHeader']))
        verifications = export_data.get('data', {}).get('verifications', [])
        if verifications:
            elements.append(Paragraph(f"Total de verificaciones: {len(verifications)}", self.styles['ReportBodyText']))
            for v in verifications[:10]:  # Limitar a 10 para PDF
                v_text = f"<b>ID:</b> {v.get('id', 'N/A')} | "
                v_text += f"<b>Score:</b> {v.get('score', 'N/A')} | "
                v_text += f"<b>Riesgo:</b> {v.get('risk_level', 'N/A')}<br/>"
                v_text += f"<b>Empresa:</b> {v.get('target_company_name', 'N/A')}<br/>"
                v_text += f"<b>Fecha:</b> {v.get('created_at', 'N/A')}"
                elements.append(Paragraph(v_text, self.styles['ReportBodyText']))
                elements.append(Spacer(1, 0.05*inch))
            
            if len(verifications) > 10:
                elements.append(Paragraph(
                    f"... y {len(verifications) - 10} verificaciones más (ver exportación JSON completa)",
                    self.styles['ReportBodyText']
                ))
        else:
            elements.append(Paragraph("No hay verificaciones registradas.", self.styles['ReportBodyText']))
        
        elements.append(PageBreak())
        
        # Aviso legal GDPR
        elements.append(Paragraph("Aviso Legal - Protección de Datos", self.styles['SectionHeader']))
        
        legal_text = """
        <b>Derechos del Titular de Datos:</b><br/>
        De conformidad con el Reglamento General de Protección de Datos (RGPD) y la Ley 29733 (Perú), 
        usted tiene derecho a:<br/>
        • Acceder a sus datos personales (Art. 15)<br/>
        • Rectificar datos inexactos (Art. 16)<br/>
        • Solicitar la supresión de sus datos (Art. 17)<br/>
        • Limitar el tratamiento (Art. 18)<br/>
        • Portabilidad de datos (Art. 20)<br/>
        • Oponerse al tratamiento (Art. 21)<br/><br/>
        
        <b>Responsable del Tratamiento:</b><br/>
        Conflict Zero S.A.C. / Conflict Zero S.L.<br/>
        Contacto DPO: dpo@conflictzero.com<br/><br/>
        
        <b>Retención de Datos:</b><br/>
        Sus datos se conservarán durante el período necesario para cumplir con las finalidades del tratamiento 
        y las obligaciones legales aplicables. Para más información, consulte nuestra política de retención de datos.<br/><br/>
        
        <b>Destinatarios:</b><br/>
        No se cederán datos a terceros salvo obligación legal o consentimiento expreso.<br/><br/>
        
        <b>Base Legal:</b><br/>
        El tratamiento de sus datos se basa en la ejecución del contrato de servicios y en el interés legítimo 
        de verificación de riesgo de proveedores, conforme al Art. 6 del RGPD.
        """
        elements.append(Paragraph(legal_text, self.styles['ReportBodyText']))
        
        # Footer
        elements.append(Spacer(1, 0.5*inch))
        elements.append(Paragraph(
            f"Documento generado automáticamente por Conflict Zero | {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
            self.styles['Footer']
        ))
        
        doc.build(elements, onFirstPage=self._draw_header_footer, onLaterPages=self._draw_header_footer)
        
        pdf_content = buffer.getvalue()
        buffer.close()
        
        return pdf_content


# Instancia singleton
pdf_generator = PDFReportGenerator()
