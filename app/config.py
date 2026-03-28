"""
Mercenary service configuration.
All settings loaded from environment variables.
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class MercenaryConfig:
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8001
    SECRET_KEY: str = ""
    
    DATABASE_URL: str = ""
    
    CORE_API_URL: str = "http://localhost:8000/api/internal"
    CORE_API_KEY: str = ""
    
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    
    JWT_SECRET_KEY: str = ""
    JWT_EXPIRY_MINUTES: int = 60
    
    # Email (Resend)
    RESEND_API_KEY: str = ""
    SMTP_FROM_EMAIL: str = "noreply@mercs.tech"
    SMTP_FROM_NAME: str = "Mercs.tech"
    FRONTEND_URL: str = "https://mercs.tech"
    
    # Google OAuth
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = ""
    
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 60
    
    PLATFORM_FEE_PERCENT: float = 15.0
    MIN_BOUNTY: float = 5.0
    MAX_BOUNTY: float = 1000.0
    
    @classmethod
    def from_env(cls) -> "MercenaryConfig":
        return cls(
            API_HOST=os.environ.get("API_HOST", "0.0.0.0"),
            API_PORT=int(os.environ.get("PORT", os.environ.get("API_PORT", "8001"))),
            SECRET_KEY=os.environ.get("SECRET_KEY", "dev-secret-key"),
            DATABASE_URL=os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/mercenary"),
            CORE_API_URL=os.environ.get("CORE_API_URL", "http://localhost:8000/api/internal"),
            CORE_API_KEY=os.environ.get("CORE_API_KEY", ""),
            STRIPE_SECRET_KEY=os.environ.get("STRIPE_SECRET_KEY", ""),
            STRIPE_WEBHOOK_SECRET=os.environ.get("STRIPE_WEBHOOK_SECRET", ""),
            JWT_SECRET_KEY=os.environ.get("JWT_SECRET", "dev-jwt-secret"),
            JWT_EXPIRY_MINUTES=int(os.environ.get("JWT_EXPIRY_MINUTES", "60")),
            RESEND_API_KEY=os.environ.get("RESEND_API_KEY", ""),
            SMTP_FROM_EMAIL=os.environ.get("SMTP_FROM_EMAIL", "noreply@mercs.tech"),
            SMTP_FROM_NAME=os.environ.get("SMTP_FROM_NAME", "Mercs.tech"),
            FRONTEND_URL=os.environ.get("FRONTEND_URL", "https://mercs.tech"),
            GOOGLE_CLIENT_ID=os.environ.get("GOOGLE_CLIENT_ID", ""),
            GOOGLE_CLIENT_SECRET=os.environ.get("GOOGLE_CLIENT_SECRET", ""),
            GOOGLE_REDIRECT_URI=os.environ.get("GOOGLE_REDIRECT_URI", "http://localhost:3000/auth/google/callback"),
            RATE_LIMIT_REQUESTS=int(os.environ.get("RATE_LIMIT_REQUESTS", "100")),
            RATE_LIMIT_WINDOW=int(os.environ.get("RATE_LIMIT_WINDOW", "60")),
            PLATFORM_FEE_PERCENT=float(os.environ.get("PLATFORM_FEE_PERCENT", "15.0")),
            MIN_BOUNTY=float(os.environ.get("MIN_BOUNTY", "5.0")),
            MAX_BOUNTY=float(os.environ.get("MAX_BOUNTY", "1000.0")),
        )


config = MercenaryConfig.from_env()
