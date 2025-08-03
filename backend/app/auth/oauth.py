#!/usr/bin/env python3
"""
OAuth2 Social Login Implementation (Google & Discord)
"""

import os
import httpx
import secrets
from typing import Optional, Dict, Any
from fastapi import HTTPException, status
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta
import jwt
from dotenv import load_dotenv

load_dotenv()

class OAuthConfig:
    """OAuth configuration for social providers"""
    
    # Google OAuth
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
    GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:3000/auth/google/callback")
    
    # Discord OAuth
    DISCORD_CLIENT_ID = os.getenv("DISCORD_CLIENT_ID")
    DISCORD_CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET")
    DISCORD_REDIRECT_URI = os.getenv("DISCORD_REDIRECT_URI", "http://localhost:3000/auth/discord/callback")
    
    # Base URLs
    GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/auth"
    GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
    GOOGLE_USER_INFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"
    
    DISCORD_AUTH_URL = "https://discord.com/api/oauth2/authorize"
    DISCORD_TOKEN_URL = "https://discord.com/api/oauth2/token"
    DISCORD_USER_INFO_URL = "https://discord.com/api/users/@me"

oauth_config = OAuthConfig()

class OAuthUserInfo(BaseModel):
    """Standardized OAuth user information"""
    provider: str
    provider_id: str
    email: EmailStr
    name: str
    avatar_url: Optional[str] = None
    username: Optional[str] = None

class OAuthProvider:
    """Base OAuth provider class"""
    
    def __init__(self, provider_name: str):
        self.provider_name = provider_name
    
    async def get_authorization_url(self, state: str) -> str:
        """Get OAuth authorization URL"""
        raise NotImplementedError
    
    async def exchange_code_for_token(self, code: str, state: str) -> str:
        """Exchange authorization code for access token"""
        raise NotImplementedError
    
    async def get_user_info(self, access_token: str) -> OAuthUserInfo:
        """Get user information using access token"""
        raise NotImplementedError

class GoogleOAuthProvider(OAuthProvider):
    """Google OAuth provider implementation"""
    
    def __init__(self):
        super().__init__("google")
        if not oauth_config.GOOGLE_CLIENT_ID or not oauth_config.GOOGLE_CLIENT_SECRET:
            raise ValueError("Google OAuth credentials not configured")
    
    async def get_authorization_url(self, state: str) -> str:
        """Get Google OAuth authorization URL"""
        params = {
            "client_id": oauth_config.GOOGLE_CLIENT_ID,
            "redirect_uri": oauth_config.GOOGLE_REDIRECT_URI,
            "scope": "openid email profile",
            "response_type": "code",
            "state": state,
            "access_type": "offline",
            "prompt": "consent"
        }
        
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{oauth_config.GOOGLE_AUTH_URL}?{query_string}"
    
    async def exchange_code_for_token(self, code: str, state: str) -> str:
        """Exchange Google authorization code for access token"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                oauth_config.GOOGLE_TOKEN_URL,
                data={
                    "client_id": oauth_config.GOOGLE_CLIENT_ID,
                    "client_secret": oauth_config.GOOGLE_CLIENT_SECRET,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": oauth_config.GOOGLE_REDIRECT_URI,
                },
                headers={"Accept": "application/json"}
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to exchange code for token"
                )
            
            token_data = response.json()
            return token_data.get("access_token")
    
    async def get_user_info(self, access_token: str) -> OAuthUserInfo:
        """Get Google user information"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                oauth_config.GOOGLE_USER_INFO_URL,
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to get user information"
                )
            
            user_data = response.json()
            
            return OAuthUserInfo(
                provider="google",
                provider_id=user_data["id"],
                email=user_data["email"],
                name=user_data["name"],
                avatar_url=user_data.get("picture"),
                username=user_data.get("email", "").split("@")[0]
            )

class DiscordOAuthProvider(OAuthProvider):
    """Discord OAuth provider implementation"""
    
    def __init__(self):
        super().__init__("discord")
        if not oauth_config.DISCORD_CLIENT_ID or not oauth_config.DISCORD_CLIENT_SECRET:
            raise ValueError("Discord OAuth credentials not configured")
    
    async def get_authorization_url(self, state: str) -> str:
        """Get Discord OAuth authorization URL"""
        params = {
            "client_id": oauth_config.DISCORD_CLIENT_ID,
            "redirect_uri": oauth_config.DISCORD_REDIRECT_URI,
            "response_type": "code",
            "scope": "identify email",
            "state": state
        }
        
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{oauth_config.DISCORD_AUTH_URL}?{query_string}"
    
    async def exchange_code_for_token(self, code: str, state: str) -> str:
        """Exchange Discord authorization code for access token"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                oauth_config.DISCORD_TOKEN_URL,
                data={
                    "client_id": oauth_config.DISCORD_CLIENT_ID,
                    "client_secret": oauth_config.DISCORD_CLIENT_SECRET,
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": oauth_config.DISCORD_REDIRECT_URI,
                },
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Accept": "application/json"
                }
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to exchange code for token"
                )
            
            token_data = response.json()
            return token_data.get("access_token")
    
    async def get_user_info(self, access_token: str) -> OAuthUserInfo:
        """Get Discord user information"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                oauth_config.DISCORD_USER_INFO_URL,
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to get user information"
                )
            
            user_data = response.json()
            
            # Construct avatar URL
            avatar_url = None
            if user_data.get("avatar"):
                avatar_url = f"https://cdn.discordapp.com/avatars/{user_data['id']}/{user_data['avatar']}.png"
            
            return OAuthUserInfo(
                provider="discord",
                provider_id=user_data["id"],
                email=user_data["email"],
                name=user_data.get("global_name", user_data.get("username", "")),
                avatar_url=avatar_url,
                username=user_data["username"]
            )

class OAuthStateManager:
    """Secure OAuth state management"""
    
    @staticmethod
    def generate_state() -> str:
        """Generate secure state parameter"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def create_state_token(provider: str, redirect_url: Optional[str] = None) -> str:
        """Create JWT state token with provider and redirect info"""
        payload = {
            "provider": provider,
            "redirect_url": redirect_url,
            "exp": datetime.utcnow() + timedelta(minutes=10),  # 10 minute expiry
            "iat": datetime.utcnow(),
            "jti": secrets.token_urlsafe(16)
        }
        
        # Use the same secret as JWT tokens for consistency
        from .security_enhanced import security_config
        return jwt.encode(payload, security_config.SECRET_KEY, algorithm="HS256")
    
    @staticmethod
    def validate_state_token(state_token: str) -> Dict[str, Any]:
        """Validate and decode state token"""
        try:
            from .security_enhanced import security_config
            payload = jwt.decode(
                state_token, 
                security_config.SECRET_KEY, 
                algorithms=["HS256"],
                options={"require": ["exp", "iat", "jti"]}
            )
            return payload
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired state token"
            )

# Provider instances
google_provider = GoogleOAuthProvider() if oauth_config.GOOGLE_CLIENT_ID else None
discord_provider = DiscordOAuthProvider() if oauth_config.DISCORD_CLIENT_ID else None

def get_oauth_provider(provider_name: str) -> OAuthProvider:
    """Get OAuth provider by name"""
    providers = {
        "google": google_provider,
        "discord": discord_provider
    }
    
    provider = providers.get(provider_name)
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth provider '{provider_name}' not configured"
        )
    
    return provider