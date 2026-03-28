"""
Email service for sending verification emails and notifications.
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import logging

from app.config import config

logger = logging.getLogger(__name__)


class EmailService:
    def __init__(self):
        self.host = config.SMTP_HOST
        self.port = config.SMTP_PORT
        self.user = config.SMTP_USER
        self.password = config.SMTP_PASSWORD
        self.from_email = config.SMTP_FROM_EMAIL
        self.from_name = config.SMTP_FROM_NAME
        self.frontend_url = config.FRONTEND_URL
    
    @property
    def is_configured(self) -> bool:
        return bool(self.host and self.user and self.password)
    
    def send_verification_email(self, email: str, token: str) -> bool:
        verify_url = f"{self.frontend_url}/auth/verify?token={token}"
        
        html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #1a1a1a;">Welcome to Mercs.tech</h2>
            <p>Thank you for signing up! Please verify your email address to activate your account.</p>
            <a href="{verify_url}" 
               style="display: inline-block; padding: 12px 24px; background-color: #6366f1; color: white; 
                      text-decoration: none; border-radius: 6px; margin: 16px 0;">
                Verify Email
            </a>
            <p style="color: #666; font-size: 14px;">
                Or copy this link: <code style="background: #f3f4f6; padding: 2px 6px; border-radius: 4px;">
                {verify_url}</code>
            </p>
            <p style="color: #999; font-size: 12px; margin-top: 24px;">
                If you didn't create an account, you can ignore this email.
            </p>
        </div>
        """
        
        text = f"""
Welcome to Mercs.tech

Please verify your email address to activate your account.

Verify here: {verify_url}

If you didn't create an account, you can ignore this email.
        """
        
        return self._send_email(
            to=email,
            subject="Verify your email - Mercs.tech",
            html=html,
            text=text
        )
    
    def send_password_reset_email(self, email: str, token: str) -> bool:
        reset_url = f"{self.frontend_url}/auth/reset-password?token={token}"
        
        html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #1a1a1a;">Reset Your Password</h2>
            <p>You requested a password reset for your Mercs.tech account.</p>
            <a href="{reset_url}" 
               style="display: inline-block; padding: 12px 24px; background-color: #6366f1; color: white; 
                      text-decoration: none; border-radius: 6px; margin: 16px 0;">
                Reset Password
            </a>
            <p style="color: #666; font-size: 14px;">
                This link expires in 1 hour. If you didn't request this, you can ignore this email.
            </p>
        </div>
        """
        
        text = f"""
Reset Your Password

You requested a password reset for your Mercs.tech account.

Reset here: {reset_url}

This link expires in 1 hour. If you didn't request this, you can ignore this email.
        """
        
        return self._send_email(
            to=email,
            subject="Reset your password - Mercs.tech",
            html=html,
            text=text
        )
    
    def _send_email(self, to: str, subject: str, html: str, text: str) -> bool:
        if not self.is_configured:
            logger.warning(f"SMTP not configured, skipping email to {to}")
            logger.info(f"Would send email: {subject}")
            return True
        
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{self.from_name} <{self.from_email}>"
            msg["To"] = to
            
            msg.attach(MIMEText(text, "plain"))
            msg.attach(MIMEText(html, "html"))
            
            with smtplib.SMTP(self.host, self.port) as server:
                server.starttls()
                server.login(self.user, self.password)
                server.sendmail(self.from_email, to, msg.as_string())
            
            logger.info(f"Email sent to {to}: {subject}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to}: {e}")
            return False


email_service = EmailService()
