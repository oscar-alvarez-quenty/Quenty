"""Email service for sending authentication emails"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# Email configuration from environment variables
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", SMTP_USER)
SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "Quenty Auth")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")


class EmailService:
    """Service for sending emails"""

    def __init__(self):
        self.smtp_host = SMTP_HOST
        self.smtp_port = SMTP_PORT
        self.smtp_user = SMTP_USER
        self.smtp_password = SMTP_PASSWORD
        self.from_email = SMTP_FROM_EMAIL
        self.from_name = SMTP_FROM_NAME
        self.frontend_url = FRONTEND_URL

    def _send_email(self, to_email: str, subject: str, html_content: str) -> bool:
        """
        Send an email using SMTP

        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML content of the email

        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email

            # Attach HTML content
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)

            # Connect to SMTP server and send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                if self.smtp_user and self.smtp_password:
                    server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)

            logger.info(f"Email sent successfully to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False

    def send_password_reset_email(self, to_email: str, reset_token: str, user_name: Optional[str] = None) -> bool:
        """
        Send password reset email

        Args:
            to_email: User's email address
            reset_token: Password reset token
            user_name: User's name (optional)

        Returns:
            bool: True if email sent successfully
        """
        reset_url = f"{self.frontend_url}/auth/reset-password?token={reset_token}"

        greeting = f"Hola {user_name}," if user_name else "Hola,"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background-color: #4CAF50;
                    color: white;
                    padding: 20px;
                    text-align: center;
                    border-radius: 5px 5px 0 0;
                }}
                .content {{
                    background-color: #f9f9f9;
                    padding: 30px;
                    border-radius: 0 0 5px 5px;
                }}
                .button {{
                    display: inline-block;
                    padding: 12px 30px;
                    background-color: #4CAF50;
                    color: white;
                    text-decoration: none;
                    border-radius: 5px;
                    margin: 20px 0;
                }}
                .footer {{
                    margin-top: 20px;
                    padding-top: 20px;
                    border-top: 1px solid #ddd;
                    font-size: 12px;
                    color: #666;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Recuperación de Contraseña</h1>
                </div>
                <div class="content">
                    <p>{greeting}</p>
                    <p>Hemos recibido una solicitud para restablecer la contraseña de tu cuenta en Quenty.</p>
                    <p>Para crear una nueva contraseña, haz clic en el siguiente botón:</p>
                    <center>
                        <a href="{reset_url}" class="button">Restablecer Contraseña</a>
                    </center>
                    <p>O copia y pega este enlace en tu navegador:</p>
                    <p style="word-break: break-all; color: #4CAF50;">{reset_url}</p>
                    <p><strong>Este enlace expirará en 1 hora.</strong></p>
                    <p>Si no solicitaste restablecer tu contraseña, puedes ignorar este correo de forma segura.</p>
                    <div class="footer">
                        <p>Este es un correo automático, por favor no respondas a este mensaje.</p>
                        <p>&copy; 2025 Quenty. Todos los derechos reservados.</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """

        return self._send_email(
            to_email=to_email,
            subject="Recuperación de Contraseña - Quenty",
            html_content=html_content
        )

    def send_welcome_email(self, to_email: str, user_name: str, user_type: str) -> bool:
        """
        Send welcome email after successful registration

        Args:
            to_email: User's email address
            user_name: User's name
            user_type: Type of user (natural or juridica)

        Returns:
            bool: True if email sent successfully
        """
        user_type_text = "empresa" if user_type == "juridica" else "usuario"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background-color: #4CAF50;
                    color: white;
                    padding: 20px;
                    text-align: center;
                    border-radius: 5px 5px 0 0;
                }}
                .content {{
                    background-color: #f9f9f9;
                    padding: 30px;
                    border-radius: 0 0 5px 5px;
                }}
                .button {{
                    display: inline-block;
                    padding: 12px 30px;
                    background-color: #4CAF50;
                    color: white;
                    text-decoration: none;
                    border-radius: 5px;
                    margin: 20px 0;
                }}
                .footer {{
                    margin-top: 20px;
                    padding-top: 20px;
                    border-top: 1px solid #ddd;
                    font-size: 12px;
                    color: #666;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>¡Bienvenido a Quenty!</h1>
                </div>
                <div class="content">
                    <p>Hola {user_name},</p>
                    <p>¡Gracias por registrarte en Quenty como {user_type_text}!</p>
                    <p>Tu cuenta ha sido creada exitosamente. Ahora puedes acceder a nuestra plataforma y comenzar a disfrutar de todos nuestros servicios.</p>
                    <center>
                        <a href="{self.frontend_url}/dashboard" class="button">Ir al Dashboard</a>
                    </center>
                    <p>Si tienes alguna pregunta o necesitas ayuda, no dudes en contactarnos.</p>
                    <div class="footer">
                        <p>Este es un correo automático, por favor no respondas a este mensaje.</p>
                        <p>&copy; 2025 Quenty. Todos los derechos reservados.</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """

        return self._send_email(
            to_email=to_email,
            subject="¡Bienvenido a Quenty!",
            html_content=html_content
        )

    def send_email_verification(self, to_email: str, verification_token: str, user_name: Optional[str] = None) -> bool:
        """
        Send email verification email

        Args:
            to_email: User's email address
            verification_token: Email verification token
            user_name: User's name (optional)

        Returns:
            bool: True if email sent successfully
        """
        verification_url = f"{self.frontend_url}/auth/verify-email?token={verification_token}"

        greeting = f"Hola {user_name}," if user_name else "Hola,"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background-color: #4CAF50;
                    color: white;
                    padding: 20px;
                    text-align: center;
                    border-radius: 5px 5px 0 0;
                }}
                .content {{
                    background-color: #f9f9f9;
                    padding: 30px;
                    border-radius: 0 0 5px 5px;
                }}
                .button {{
                    display: inline-block;
                    padding: 12px 30px;
                    background-color: #4CAF50;
                    color: white;
                    text-decoration: none;
                    border-radius: 5px;
                    margin: 20px 0;
                }}
                .footer {{
                    margin-top: 20px;
                    padding-top: 20px;
                    border-top: 1px solid #ddd;
                    font-size: 12px;
                    color: #666;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Verificación de Email</h1>
                </div>
                <div class="content">
                    <p>{greeting}</p>
                    <p>Por favor verifica tu dirección de correo electrónico haciendo clic en el siguiente botón:</p>
                    <center>
                        <a href="{verification_url}" class="button">Verificar Email</a>
                    </center>
                    <p>O copia y pega este enlace en tu navegador:</p>
                    <p style="word-break: break-all; color: #4CAF50;">{verification_url}</p>
                    <p><strong>Este enlace expirará en 24 horas.</strong></p>
                    <div class="footer">
                        <p>Este es un correo automático, por favor no respondas a este mensaje.</p>
                        <p>&copy; 2025 Quenty. Todos los derechos reservados.</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """

        return self._send_email(
            to_email=to_email,
            subject="Verifica tu Email - Quenty",
            html_content=html_content
        )


# Singleton instance
email_service = EmailService()
