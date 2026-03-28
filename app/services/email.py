"""
Email service using Resend API.
"""

import logging
from typing import Optional
import resend

from app.config import config

logger = logging.getLogger(__name__)


class EmailService:
    def __init__(self):
        self.api_key = config.RESEND_API_KEY
        self.from_email = config.SMTP_FROM_EMAIL
        self.from_name = config.SMTP_FROM_NAME
        self.frontend_url = config.FRONTEND_URL
        
        if self.api_key:
            resend.api_key = self.api_key
    
    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)
    
    def send_verification_email(self, email: str, token: str) -> bool:
        verify_url = f"{self.frontend_url}/auth/verify?token={token}"
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="font-family: 'Segoe UI', Arial, sans-serif; background-color: #f9fafb; margin: 0; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background-color: white; border-radius: 12px; padding: 40px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                <h1 style="color: #1a1a1a; font-size: 24px; margin: 0 0 16px;">Welcome to Mercs.tech</h1>
                <p style="color: #4b5563; font-size: 16px; line-height: 1.6; margin: 0 0 24px;">
                    Thank you for signing up! Please verify your email address to activate your account and start posting bounties.
                </p>
                <a href="{verify_url}" 
                   style="display: inline-block; padding: 14px 28px; background-color: #6366f1; color: white; 
                          text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px;">
                    Verify Email Address
                </a>
                <p style="color: #9ca3af; font-size: 14px; margin: 24px 0 0;">
                    Or copy this link:<br>
                    <code style="background: #f3f4f6; padding: 8px 12px; border-radius: 6px; font-size: 13px; display: inline-block; margin-top: 8px; word-break: break-all;">
                        {verify_url}
                    </code>
                </p>
                <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 32px 0;">
                <p style="color: #9ca3af; font-size: 13px; margin: 0;">
                    If you didn't create an account at Mercs.tech, you can safely ignore this email.
                </p>
            </div>
        </body>
        </html>
        """
        
        return self._send_email(
            to=email,
            subject="Verify your email - Mercs.tech",
            html=html
        )
    
    def send_password_reset_email(self, email: str, token: str) -> bool:
        reset_url = f"{self.frontend_url}/auth/reset-password?token={token}"
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
        </head>
        <body style="font-family: 'Segoe UI', Arial, sans-serif; background-color: #f9fafb; margin: 0; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background-color: white; border-radius: 12px; padding: 40px;">
                <h1 style="color: #1a1a1a; font-size: 24px; margin: 0 0 16px;">Reset Your Password</h1>
                <p style="color: #4b5563; font-size: 16px; line-height: 1.6; margin: 0 0 24px;">
                    You requested a password reset for your Mercs.tech account.
                </p>
                <a href="{reset_url}" 
                   style="display: inline-block; padding: 14px 28px; background-color: #6366f1; color: white; 
                          text-decoration: none; border-radius: 8px; font-weight: 600;">
                    Reset Password
                </a>
                <p style="color: #9ca3af; font-size: 14px; margin: 24px 0 0;">
                    This link expires in 1 hour. If you didn't request this, you can ignore this email.
                </p>
            </div>
        </body>
        </html>
        """
        
        return self._send_email(
            to=email,
            subject="Reset your password - Mercs.tech",
            html=html
        )
    
    def send_bounty_completed_email(self, email: str, bounty_title: str, result: str) -> bool:
        html = f"""
        <!DOCTYPE html>
        <html>
        <body style="font-family: 'Segoe UI', Arial, sans-serif; background-color: #f9fafb; margin: 0; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background-color: white; border-radius: 12px; padding: 40px;">
                <h1 style="color: #1a1a1a; font-size: 24px; margin: 0 0 16px;">Bounty Completed!</h1>
                <p style="color: #4b5563; font-size: 16px; line-height: 1.6; margin: 0 0 16px;">
                    Your bounty <strong>"{bounty_title}"</strong> has been completed by an agent.
                </p>
                <div style="background: #f3f4f6; border-radius: 8px; padding: 16px; margin: 24px 0;">
                    <h3 style="margin: 0 0 8px; color: #374151;">Result:</h3>
                    <p style="margin: 0; color: #4b5563; white-space: pre-wrap;">{result[:500]}{'...' if len(result) > 500 else ''}</p>
                </div>
                <a href="{self.frontend_url}/dashboard" 
                   style="display: inline-block; padding: 14px 28px; background-color: #6366f1; color: white; 
                          text-decoration: none; border-radius: 8px; font-weight: 600;">
                    View in Dashboard
                </a>
            </div>
        </body>
        </html>
        """
        
        return self._send_email(
            to=email,
            subject=f"Bounty completed: {bounty_title}",
            html=html
        )
    
    def _send_email(self, to: str, subject: str, html: str) -> bool:
        if not self.is_configured:
            logger.warning(f"Resend not configured, skipping email to {to}")
            logger.info(f"Would send: {subject}")
            return True
        
        try:
            r = resend.Emails.send({
                "from": f"{self.from_name} <{self.from_email}>",
                "to": [to],
                "subject": subject,
                "html": html
            })
            logger.info(f"Email sent to {to}: {subject} (id: {r.get('id', 'unknown')})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to}: {e}")
            return False


email_service = EmailService()
