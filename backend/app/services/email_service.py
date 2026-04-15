"""
Conflict Zero - Email Service
Envío de emails transaccionales con SendGrid
"""

from typing import Optional, List
from datetime import datetime
import os

# Simulación de SendGrid (para demo sin API key real)
class MockSendGridClient:
    """Mock para desarrollo sin SendGrid"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        print(f"[EmailService] Mock SendGrid initialized (API key: {api_key[:10]}...)")
    
    def send(self, message: dict) -> dict:
        """Simula envío de email"""
        print(f"[EmailService] MOCK EMAIL SENT:")
        print(f"  To: {message.get('to')}")
        print(f"  Subject: {message.get('subject')}")
        print(f"  ---")
        return {"status_code": 202, "mock": True}


# Intentar importar SendGrid real
try:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail, Email, Content
    SENDGRID_AVAILABLE = True
except ImportError:
    SENDGRID_AVAILABLE = False
    print("[EmailService] SendGrid not installed, using mock")


class EmailService:
    """
    Servicio de envío de emails.
    En modo demo: solo loguea (no envía realmente)
    En producción: usa SendGrid
    """
    
    def __init__(self):
        self.api_key = os.getenv("SENDGRID_API_KEY", "")
        self.from_email = os.getenv("SENDGRID_FROM_EMAIL", "noreply@czperu.com")
        self.enabled = os.getenv("EMAIL_ENABLED", "false").lower() == "true"
        self.is_demo = os.getenv("CERT_MODE", "demo") == "demo"
        
        if self.enabled and SENDGRID_AVAILABLE and self.api_key:
            self.client = SendGridAPIClient(self.api_key)
            self.mock = False
        else:
            self.client = MockSendGridClient(self.api_key)
            self.mock = True
            if self.is_demo:
                print("[EmailService] DEMO MODE: Emails will be logged only, not sent")
    
    def _send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        from_name: str = "Conflict Zero"
    ) -> dict:
        """Envía un email"""
        if self.mock:
            return self.client.send({
                "to": to_email,
                "subject": subject,
                "from": f"{from_name} <{self.from_email}>"
            })
        
        # Envío real con SendGrid
        message = Mail(
            from_email=Email(self.from_email, from_name),
            to_emails=to_email,
            subject=subject,
            html_content=Content("text/html", html_content)
        )
        
        response = self.client.send(message)
        return {
            "status_code": response.status_code,
            "headers": dict(response.headers)
        }
    
    def send_founder_welcome(self, to_email: str, company_name: str, invite_link: str) -> dict:
        """
        Email de bienvenida para nuevos Fundadores aprobados.
        """
        html = f"""
        <html>
        <body style="font-family: Inter, sans-serif; background: #0A0A0A; color: #F5F5F5; padding: 40px;">
            <div style="max-width: 600px; margin: 0 auto; background: #141414; border: 1px solid #C9A961; border-radius: 16px; padding: 40px;">
                <h1 style="color: #C9A961; font-family: 'Playfair Display', serif;">Bienvenido al Programa Fundador</h1>
                <p>Hola <strong>{company_name}</strong>,</p>
                <p>Tu aplicación al Programa Fundador de Conflict Zero ha sido <strong style="color: #C9A961;">APROBADA</strong>.</p>
                
                <div style="background: rgba(201,169,97,0.1); border-left: 4px solid #C9A961; padding: 20px; margin: 24px 0;">
                    <h3 style="margin-top: 0; color: #C9A961;">Tu Beneficio:</h3>
                    <ul>
                        <li>3 meses de acceso Enterprise gratuito</li>
                        <li>Consultas ilimitadas</li>
                        <li>API completa</li>
                        <li>Soporte directo con fundadores</li>
                    </ul>
                </div>
                
                <p style="text-align: center; margin: 32px 0;">
                    <a href="{invite_link}" style="background: #C9A961; color: #0A0A0A; padding: 16px 32px; text-decoration: none; border-radius: 8px; font-weight: 600; display: inline-block;">Completar Registro</a>
                </p>
                
                <p style="color: #888; font-size: 12px;">Este enlace expira en 7 días.</p>
            </div>
        </body>
        </html>
        """
        
        return self._send_email(
            to_email=to_email,
            subject="🎉 Aprobado: Programa Fundador Conflict Zero",
            html_content=html
        )
    
    def send_invite_to_subcontractor(
        self,
        to_email: str,
        inviter_company: str,
        invite_code: str,
        registration_link: str
    ) -> dict:
        """
        Email de invitación a subcontratista (efecto red).
        El 'miedo' psicológico: "Tu cliente te exige".
        """
        html = f"""
        <html>
        <body style="font-family: Inter, sans-serif; background: #0A0A0A; color: #F5F5F5; padding: 40px;">
            <div style="max-width: 600px; margin: 0 auto; background: #141414; border: 1px solid #DC2626; border-radius: 16px; padding: 40px;">
                <h1 style="color: #DC2626;">⚠️ Tu Cliente Te Exige Verificación</h1>
                
                <p><strong>{inviter_company}</strong> te ha registrado como subcontratista y <strong>requiere</strong> que obtengas el Sello de Cumplimiento Conflict Zero.</p>
                
                <div style="background: rgba(220,38,38,0.1); border-left: 4px solid #DC2626; padding: 20px; margin: 24px 0;">
                    <p style="margin: 0;"><strong>Sin este sello:</strong></p>
                    <ul style="margin: 10px 0;">
                        <li>No podrás participar en sus obras</li>
                        <li>Riesgo de exclusión de sus procesos</li>
                    </ul>
                </div>
                
                <p style="text-align: center; margin: 32px 0;">
                    <a href="{registration_link}?code={invite_code}" style="background: #C9A961; color: #0A0A0A; padding: 16px 32px; text-decoration: none; border-radius: 8px; font-weight: 600; display: inline-block;">Obtener Sello Ahora</a>
                </p>
                
                <p style="color: #888; font-size: 12px;">
                    Código de invitación: <code style="background: #0A0A0A; padding: 4px 8px; border-radius: 4px;">{invite_code}</code>
                </p>
            </div>
        </body>
        </html>
        """
        
        return self._send_email(
            to_email=to_email,
            subject=f"⚠️ {inviter_company} te exige verificación de cumplimiento",
            html_content=html
        )
    
    def send_low_credit_alert(self, to_email: str, company_name: str, remaining: int, total: int) -> dict:
        """
        Alerta de créditos bajos (para clientes de pago).
        """
        percentage = (remaining / total * 100) if total > 0 else 0
        
        html = f"""
        <html>
        <body style="font-family: Inter, sans-serif; background: #0A0A0A; color: #F5F5F5; padding: 40px;">
            <div style="max-width: 600px; margin: 0 auto; background: #141414; border: 1px solid #DC2626; border-radius: 16px; padding: 40px;">
                <h1 style="color: #DC2626;">⚠️ Créditos Bajos</h1>
                
                <p>Hola <strong>{company_name}</strong>,</p>
                <p>Tu cuenta tiene <strong style="color: #DC2626;">{remaining}</strong> consultas restantes ({percentage:.0f}%).</p>
                
                <div style="background: rgba(201,169,97,0.1); border: 1px solid #C9A961; padding: 20px; margin: 24px 0; border-radius: 8px; text-align: center;">
                    <p style="margin: 0 0 16px 0;">Actualiza tu plan para continuar verificando</p>
                    <a href="https://czperu.com/dashboard/billing" style="background: #C9A961; color: #0A0A0A; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: 600; display: inline-block;">Ver Planes</a>
                </div>
            </div>
        </body>
        </html>
        """
        
        return self._send_email(
            to_email=to_email,
            subject="⚠️ Alerta: Créditos de consulta bajos",
            html_content=html
        )
    
    def send_monthly_report(
        self,
        to_email: str,
        company_name: str,
        month: str,
        verifications_count: int,
        avg_score: float,
        new_sanctions: int
    ) -> dict:
        """
        Reporte mensual de actividad.
        """
        html = f"""
        <html>
        <body style="font-family: Inter, sans-serif; background: #0A0A0A; color: #F5F5F5; padding: 40px;">
            <div style="max-width: 600px; margin: 0 auto; background: #141414; border: 1px solid #C9A961; border-radius: 16px; padding: 40px;">
                <h1 style="color: #C9A961; font-family: 'Playfair Display', serif;">Reporte Mensual - {month}</h1>
                
                <p>Hola <strong>{company_name}</strong>,</p>
                <p>Este es tu resumen de actividad en Conflict Zero:</p>
                
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin: 24px 0;">
                    <div style="background: #0A0A0A; padding: 20px; border-radius: 8px; text-align: center;">
                        <div style="font-size: 32px; color: #C9A961; font-weight: bold;">{verifications_count}</div>
                        <div style="color: #888; font-size: 12px;">Verificaciones</div>
                    </div>
                    <div style="background: #0A0A0A; padding: 20px; border-radius: 8px; text-align: center;">
                        <div style="font-size: 32px; color: #C9A961; font-weight: bold;">{avg_score:.1f}</div>
                        <div style="color: #888; font-size: 12px;">Score Promedio</div>
                    </div>
                </div>
                
                {f'<p style="color: #DC2626;">⚠️ Se detectaron {new_sanctions} nuevas sanciones en tu red de contrapartes</p>' if new_sanctions > 0 else '<p style="color: #16A34A;">✓ No se detectaron nuevas sanciones</p>'}
                
                <p style="text-align: center; margin-top: 32px;">
                    <a href="https://czperu.com/dashboard" style="background: #C9A961; color: #0A0A0A; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: 600; display: inline-block;">Ver Dashboard</a>
                </p>
            </div>
        </body>
        </html>
        """
        
        return self._send_email(
            to_email=to_email,
            subject=f"📊 Reporte Mensual Conflict Zero - {month}",
            html_content=html
        )
    
    def send_founder_compliance_reminder(
        self,
        to_email: str,
        company_name: str,
        days_remaining: int,
        pending_invites: int
    ) -> dict:
        """
        Recordatorio de cumplimiento contractual para Funders.
        El "miedo" de perder el beneficio.
        """
        urgency_color = "#DC2626" if days_remaining <= 7 else "#C9A961"
        
        html = f"""
        <html>
        <body style="font-family: Inter, sans-serif; background: #0A0A0A; color: #F5F5F5; padding: 40px;">
            <div style="max-width: 600px; margin: 0 auto; background: #141414; border: 1px solid {urgency_color}; border-radius: 16px; padding: 40px;">
                <h1 style="color: {urgency_color};">⏰ Recordatorio de Cumplimiento</h1>
                
                <p>Hola <strong>{company_name}</strong>,</p>
                
                <p>Tienes <strong style="color: {urgency_color}; font-size: 24px;">{days_remaining} días</strong> para mantener tu estatus de Founder.</p>
                
                <div style="background: rgba(220,38,38,0.1); border-left: 4px solid #DC2626; padding: 20px; margin: 24px 0;">
                    <p style="margin: 0;"><strong>Tu obligación contractual:</strong></p>
                    <p style="margin: 10px 0;">50% de tus subcontratistas deben estar verificados.</p>
                    <p style="margin: 0; color: #DC2626;">Tienes {pending_invites} invitaciones pendientes de respuesta.</p>
                </div>
                
                <p style="text-align: center; margin: 32px 0;">
                    <a href="https://founders.czperu.com/compliance" style="background: {urgency_color}; color: #0A0A0A; padding: 16px 32px; text-decoration: none; border-radius: 8px; font-weight: 600; display: inline-block;">Ver Estado de Cumplimiento</a>
                </p>
                
                <p style="color: #888; font-size: 12px;">
                    Sin cumplimiento, tu beneficio de Founder será revocado el {datetime.now().strftime('%d/%m/%Y')}.
                </p>
            </div>
        </body>
        </html>
        """
        
        return self._send_email(
            to_email=to_email,
            subject=f"⏰ {days_remaining} días para mantener tu beneficio Founder",
            html_content=html
        )
    
    def send_welcome_email(self, to_email: str, company_name: str, login_url: str = "https://czperu.com/login") -> dict:
        """
        Email de bienvenida después del registro exitoso.
        """
        html = f"""
        <html>
        <body style="font-family: Inter, sans-serif; background: #0A0A0A; color: #F5F5F5; padding: 40px;">
            <div style="max-width: 600px; margin: 0 auto; background: #141414; border: 1px solid #C9A961; border-radius: 16px; padding: 40px;">
                <h1 style="color: #C9A961; font-family: 'Playfair Display', serif;">¡Bienvenido a Conflict Zero!</h1>
                
                <p>Hola <strong>{company_name}</strong>,</p>
                
                <p>Tu cuenta ha sido creada exitosamente. Ya puedes comenzar a verificar el cumplimiento de tus contrapartes.</p>
                
                <div style="background: rgba(201,169,97,0.1); border-left: 4px solid #C9A961; padding: 20px; margin: 24px 0;">
                    <p style="margin: 0;"><strong>Con tu cuenta puedes:</strong></p>
                    <ul style="margin: 10px 0;">
                        <li>Verificar RUCs de proveedores en segundos</li>
                        <li>Obtener tu Sello de Cumplimiento</li>
                        <li>Comparar múltiples contrapartes</li>
                        <li>Acceder a reportes de riesgo</li>
                    </ul>
                </div>
                
                <p style="text-align: center; margin: 32px 0;">
                    <a href="{login_url}" style="background: #C9A961; color: #0A0A0A; padding: 16px 32px; text-decoration: none; border-radius: 8px; font-weight: 600; display: inline-block;">Iniciar Sesión</a>
                </p>
                
                <p style="color: #888; font-size: 12px; margin-top: 32px;">
                    Si no creaste esta cuenta, ignora este mensaje.<br>
                    Conflict Zero - Estándar Institucional en Verificación
                </p>
            </div>
        </body>
        </html>
        """
        
        return self._send_email(
            to_email=to_email,
            subject="✅ Bienvenido a Conflict Zero - Tu cuenta está lista",
            html_content=html
        )


# Singleton
email_service = EmailService()

def get_email_service() -> EmailService:
    return email_service
