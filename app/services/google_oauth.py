"""
Google OAuth service for authentication.
"""

import httpx
from typing import Optional
from dataclasses import dataclass

from app.config import config


@dataclass
class GoogleUserInfo:
    google_id: str
    email: str
    name: str
    picture: Optional[str]


class GoogleOAuthService:
    TOKEN_URL = "https://oauth2.googleapis.com/token"
    USER_INFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"
    
    def __init__(self):
        self.client_id = config.GOOGLE_CLIENT_ID
        self.client_secret = config.GOOGLE_CLIENT_SECRET
        self.redirect_uri = config.GOOGLE_REDIRECT_URI
    
    def get_auth_url(self, state: str) -> str:
        """Generate Google OAuth authorization URL."""
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": "email profile",
            "state": state,
            "access_type": "offline",
        }
        query = "&".join(f"{k}={v}" for k, v in params.items())
        return f"https://accounts.google.com/o/oauth2/v2/auth?{query}"
    
    async def exchange_code(self, code: str) -> dict:
        """Exchange authorization code for tokens."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.TOKEN_URL,
                data={
                    "code": code,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "redirect_uri": self.redirect_uri,
                    "grant_type": "authorization_code",
                }
            )
            response.raise_for_status()
            return response.json()
    
    async def get_user_info(self, access_token: str) -> GoogleUserInfo:
        """Get user info from Google API."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.USER_INFO_URL,
                headers={"Authorization": f"Bearer {access_token}"}
            )
            response.raise_for_status()
            data = response.json()
            return GoogleUserInfo(
                google_id=data["id"],
                email=data["email"],
                name=data.get("name", ""),
                picture=data.get("picture"),
            )


google_oauth_service = GoogleOAuthService()
