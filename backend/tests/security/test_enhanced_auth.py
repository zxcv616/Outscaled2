#!/usr/bin/env python3
"""
Comprehensive security testing suite for enhanced authentication
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.auth.security_enhanced import (
    PasswordValidator, SecureTokenManager, SecureAPIKeyManager,
    security_config
)
from app.auth.rate_limiter import RateLimiter
from app.auth.oauth import GoogleOAuthProvider, DiscordOAuthProvider
from app.auth.models import User, APIKey
from app.database_enhanced import get_db

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_security.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

class TestPasswordSecurity:
    """Test password validation and security"""
    
    def test_password_entropy_calculation(self):
        """Test password entropy calculation"""
        # Weak password
        weak_entropy = PasswordValidator.calculate_entropy("password")
        assert weak_entropy < 30
        
        # Strong password
        strong_entropy = PasswordValidator.calculate_entropy("MyS3cur3P@ssw0rd!")
        assert strong_entropy > 50
        
        # Empty password
        empty_entropy = PasswordValidator.calculate_entropy("")
        assert empty_entropy == 0
    
    def test_password_validation(self):
        """Test password strength validation"""
        # Too short
        is_valid, message = PasswordValidator.validate_password("short")
        assert not is_valid
        assert "at least" in message.lower()
        
        # Common pattern
        is_valid, message = PasswordValidator.validate_password("password123456")
        assert not is_valid
        assert "common patterns" in message.lower()
        
        # Sequential characters
        is_valid, message = PasswordValidator.validate_password("abcdefghijklmnop")
        assert not is_valid
        assert "sequential" in message.lower()
        
        # Strong password
        is_valid, message = PasswordValidator.validate_password("MyStr0ng!P@ssw0rd2024")
        assert is_valid
        assert "strong" in message.lower()
    
    def test_password_hashing(self):
        """Test secure password hashing with Argon2"""
        from app.auth.security_enhanced import get_password_hash, verify_password
        
        # Test valid password
        password = "MyStr0ng!P@ssw0rd2024"
        hashed = get_password_hash(password)
        
        # Should use Argon2
        assert hashed.startswith("$argon2")
        
        # Verification should work
        assert verify_password(password, hashed)
        assert not verify_password("wrong_password", hashed)
        
        # Test weak password rejection
        with pytest.raises(ValueError):
            get_password_hash("weak")

class TestJWTSecurity:
    """Test JWT token security"""
    
    def test_jwt_secret_validation(self):
        """Test JWT secret key validation"""
        # Should have a secure secret in production
        assert len(security_config.SECRET_KEY) >= 32
    
    def test_token_creation_and_validation(self):
        """Test secure token creation and validation"""
        # Create token
        data = {"sub": "testuser", "user_id": 123}
        token = SecureTokenManager.create_access_token(data)
        
        # Decode token
        payload = SecureTokenManager.decode_token(token)
        
        assert payload is not None
        assert payload["sub"] == "testuser"
        assert payload["user_id"] == 123
        assert payload["type"] == "access"
        assert "jti" in payload  # Unique token ID
        assert "exp" in payload
        assert "iat" in payload
        assert "nbf" in payload
    
    def test_token_expiration(self):
        """Test token expiration handling"""
        # Create expired token
        import jwt
        from datetime import datetime, timedelta
        
        expired_payload = {
            "sub": "testuser",
            "user_id": 123,
            "exp": datetime.utcnow() - timedelta(seconds=1),
            "iat": datetime.utcnow() - timedelta(minutes=5),
            "nbf": datetime.utcnow() - timedelta(minutes=5),
            "type": "access",
            "jti": "test_jti"
        }
        
        expired_token = jwt.encode(expired_payload, security_config.SECRET_KEY, algorithm="HS256")
        
        # Should return None for expired token
        payload = SecureTokenManager.decode_token(expired_token)
        assert payload is None
    
    def test_token_tampering(self):
        """Test token tampering detection"""
        # Create valid token
        data = {"sub": "testuser", "user_id": 123}
        token = SecureTokenManager.create_access_token(data)
        
        # Tamper with token
        tampered_token = token[:-5] + "12345"
        
        # Should return None for tampered token
        payload = SecureTokenManager.decode_token(tampered_token)
        assert payload is None

class TestAPIKeySecurity:
    """Test API key security"""
    
    def test_api_key_generation(self):
        """Test secure API key generation"""
        api_key, key_hash = SecureAPIKeyManager.generate_api_key()
        
        # Key should have proper format
        assert api_key.startswith("osk_")
        assert len(api_key) > 20
        
        # Hash should be different from key
        assert key_hash != api_key
        assert key_hash.startswith("$argon2")
    
    def test_api_key_verification(self):
        """Test API key verification"""
        api_key, key_hash = SecureAPIKeyManager.generate_api_key()
        
        # Should verify correctly
        assert SecureAPIKeyManager.verify_api_key(api_key, key_hash)
        
        # Should reject wrong key
        assert not SecureAPIKeyManager.verify_api_key("wrong_key", key_hash)
        assert not SecureAPIKeyManager.verify_api_key("osk_wrong_key", key_hash)

class TestRateLimiting:
    """Test rate limiting functionality"""
    
    def setup_method(self):
        """Setup for each test"""
        self.rate_limiter = RateLimiter()
        # Clear memory store if using fallback
        if hasattr(self.rate_limiter, '_memory_store'):
            self.rate_limiter._memory_store.clear()
    
    def test_rate_limit_enforcement(self):
        """Test rate limit enforcement"""
        # Mock request
        mock_request = Mock()
        mock_request.client.host = "127.0.0.1"
        mock_request.headers = {}
        
        # Should allow requests under limit
        for i in range(5):
            allowed, info = self.rate_limiter.check_rate_limit(mock_request, 10, 60)
            assert allowed
            assert info["remaining"] == 10 - i - 1
        
        # Should block requests over limit
        for i in range(6):
            allowed, info = self.rate_limiter.check_rate_limit(mock_request, 10, 60)
        
        # Last request should be blocked
        assert not allowed
        assert info["remaining"] == 0
    
    def test_rate_limit_different_ips(self):
        """Test rate limiting is per-IP"""
        # Mock different IPs
        mock_request1 = Mock()
        mock_request1.client.host = "127.0.0.1"
        mock_request1.headers = {}
        
        mock_request2 = Mock()
        mock_request2.client.host = "192.168.1.1"
        mock_request2.headers = {}
        
        # Exhaust limit for first IP
        for i in range(5):
            allowed, info = self.rate_limiter.check_rate_limit(mock_request1, 5, 60)
            assert allowed
        
        # First IP should be blocked
        allowed, info = self.rate_limiter.check_rate_limit(mock_request1, 5, 60)
        assert not allowed
        
        # Second IP should still be allowed
        allowed, info = self.rate_limiter.check_rate_limit(mock_request2, 5, 60)
        assert allowed
    
    def test_rate_limit_window_reset(self):
        """Test rate limit window reset"""
        mock_request = Mock()
        mock_request.client.host = "127.0.0.1"
        mock_request.headers = {}
        
        # Use very short window for testing
        allowed, info = self.rate_limiter.check_rate_limit(mock_request, 1, 1)
        assert allowed
        
        # Should be blocked immediately
        allowed, info = self.rate_limiter.check_rate_limit(mock_request, 1, 1)
        assert not allowed
        
        # Wait for window to reset
        time.sleep(1.1)
        
        # Should be allowed again
        allowed, info = self.rate_limiter.check_rate_limit(mock_request, 1, 1)
        assert allowed

class TestOAuthSecurity:
    """Test OAuth implementation security"""
    
    @patch('httpx.AsyncClient')
    async def test_google_oauth_flow(self, mock_client):
        """Test Google OAuth flow security"""
        # Mock successful token exchange
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"access_token": "test_token"}
        
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
        
        provider = GoogleOAuthProvider()
        
        # Test authorization URL generation
        auth_url = await provider.get_authorization_url("test_state")
        
        assert "accounts.google.com" in auth_url
        assert "state=test_state" in auth_url
        assert "scope=openid email profile" in auth_url
        
        # Test token exchange
        token = await provider.exchange_code_for_token("test_code", "test_state")
        assert token == "test_token"
    
    @patch('httpx.AsyncClient')
    async def test_discord_oauth_flow(self, mock_client):
        """Test Discord OAuth flow security"""
        # Mock successful token exchange
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"access_token": "test_token"}
        
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
        
        provider = DiscordOAuthProvider()
        
        # Test authorization URL generation
        auth_url = await provider.get_authorization_url("test_state")
        
        assert "discord.com" in auth_url
        assert "state=test_state" in auth_url
        assert "scope=identify email" in auth_url
        
        # Test token exchange
        token = await provider.exchange_code_for_token("test_code", "test_state")
        assert token == "test_token"

class TestAuthenticationEndpoints:
    """Test authentication endpoint security"""
    
    def test_registration_security(self):
        """Test user registration security"""
        # Test weak password rejection
        response = client.post("/auth/register", json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "weak"
        })
        assert response.status_code == 400
        assert "Password validation failed" in response.json()["detail"]
        
        # Test strong password acceptance
        response = client.post("/auth/register", json={
            "username": "testuser2",
            "email": "test2@example.com",
            "password": "MyStr0ng!P@ssw0rd2024"
        })
        assert response.status_code == 200
    
    def test_login_rate_limiting(self):
        """Test login rate limiting"""
        # Create user first
        client.post("/auth/register", json={
            "username": "ratelimituser",
            "email": "ratelimit@example.com",
            "password": "MyStr0ng!P@ssw0rd2024"
        })
        
        # Attempt multiple failed logins
        for i in range(6):  # Assuming 5 attempts per 5 minutes
            response = client.post("/auth/token", data={
                "username": "ratelimituser",
                "password": "wrong_password"
            })
            
            if i < 5:
                assert response.status_code == 401  # Unauthorized
            else:
                assert response.status_code == 429  # Too many requests

class TestSecurityHeaders:
    """Test security headers and responses"""
    
    def test_rate_limit_headers(self):
        """Test rate limit headers in responses"""
        response = client.get("/auth/me")
        
        # Should include rate limit headers (when authenticated)
        if response.status_code != 401:
            assert "X-RateLimit-Limit" in response.headers
            assert "X-RateLimit-Remaining" in response.headers
    
    def test_security_headers(self):
        """Test general security headers"""
        response = client.get("/")
        
        # Should not expose sensitive information
        assert "Server" not in response.headers or "FastAPI" not in response.headers.get("Server", "")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])