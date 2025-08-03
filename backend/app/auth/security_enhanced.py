#!/usr/bin/env python3
"""
Enhanced Security utilities for authentication
"""

import os
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Union
from jose import JWTError, jwt
from passlib.context import CryptContext
from passlib.hash import argon2
from cryptography.fernet import Fernet
import base64
from dotenv import load_dotenv

load_dotenv()

class SecurityConfig:
    """Centralized security configuration with validation"""
    
    def __init__(self):
        self._validate_environment()
        
    def _validate_environment(self):
        """Validate critical security environment variables"""
        secret_key = os.getenv("SECRET_KEY")
        
        # Critical: Ensure secret key is secure
        if not secret_key or secret_key == "your-secret-key-here-change-in-production":
            if os.getenv("ENV") == "production":
                raise ValueError(
                    "CRITICAL SECURITY ERROR: Must set a secure SECRET_KEY in production. "
                    "Generate one with: python -c 'import secrets; print(secrets.token_urlsafe(64))'"
                )
            else:
                # Auto-generate for development
                secret_key = secrets.token_urlsafe(64)
                print(f"WARNING: Using auto-generated SECRET_KEY for development: {secret_key}")
        
        # Validate minimum entropy
        if len(secret_key) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
            
        self.SECRET_KEY = secret_key
        self.ALGORITHM = "HS256"
        self.ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
        self.REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7))
        
        # Rate limiting configuration
        self.RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", 60))
        self.RATE_LIMIT_BURST = int(os.getenv("RATE_LIMIT_BURST", 10))
        
        # Password security
        self.MIN_PASSWORD_LENGTH = int(os.getenv("MIN_PASSWORD_LENGTH", 12))
        self.PASSWORD_ENTROPY_BITS = int(os.getenv("PASSWORD_ENTROPY_BITS", 50))

# Initialize global config
security_config = SecurityConfig()

# Enhanced password hashing with Argon2
pwd_context = CryptContext(
    schemes=["argon2", "bcrypt"],
    deprecated="auto",
    argon2__memory_cost=102400,  # 100MB
    argon2__time_cost=2,         # 2 iterations
    argon2__parallelism=8,       # 8 parallel threads
)

class PasswordValidator:
    """Enhanced password validation with entropy checking"""
    
    @staticmethod
    def calculate_entropy(password: str) -> float:
        """Calculate password entropy in bits"""
        if not password:
            return 0
            
        # Character set sizes
        charset_size = 0
        if any(c.islower() for c in password):
            charset_size += 26
        if any(c.isupper() for c in password):
            charset_size += 26
        if any(c.isdigit() for c in password):
            charset_size += 10
        if any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            charset_size += 23
            
        if charset_size == 0:
            return 0
            
        import math
        return len(password) * math.log2(charset_size)
    
    @staticmethod
    def validate_password(password: str) -> tuple[bool, str]:
        """Validate password strength"""
        if len(password) < security_config.MIN_PASSWORD_LENGTH:
            return False, f"Password must be at least {security_config.MIN_PASSWORD_LENGTH} characters long"
        
        # Check entropy
        entropy = PasswordValidator.calculate_entropy(password)
        if entropy < security_config.PASSWORD_ENTROPY_BITS:
            return False, f"Password too weak. Use a mix of uppercase, lowercase, numbers and symbols (entropy: {entropy:.1f} bits, required: {security_config.PASSWORD_ENTROPY_BITS})"
        
        # Check for common patterns
        common_patterns = ["123456", "password", "qwerty", "abc123", "admin"]
        if any(pattern in password.lower() for pattern in common_patterns):
            return False, "Password contains common patterns"
        
        # Check for sequential characters
        if any(ord(password[i]) == ord(password[i-1]) + 1 for i in range(1, len(password))):
            return False, "Password contains sequential characters"
            
        return True, "Password is strong"

class SecureTokenManager:
    """Enhanced JWT token management with rotation and validation"""
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create secure JWT access token with additional claims"""
        to_encode = data.copy()
        
        # Add security claims
        now = datetime.utcnow()
        if expires_delta:
            expire = now + expires_delta
        else:
            expire = now + timedelta(minutes=security_config.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({
            "exp": expire,
            "iat": now,
            "nbf": now,
            "type": "access",
            "jti": secrets.token_urlsafe(32),  # Unique token ID for blacklisting
        })
        
        return jwt.encode(to_encode, security_config.SECRET_KEY, algorithm=security_config.ALGORITHM)
    
    @staticmethod
    def create_refresh_token(data: dict) -> str:
        """Create secure refresh token"""
        to_encode = data.copy()
        
        now = datetime.utcnow()
        expire = now + timedelta(days=security_config.REFRESH_TOKEN_EXPIRE_DAYS)
        
        to_encode.update({
            "exp": expire,
            "iat": now,
            "nbf": now,
            "type": "refresh",
            "jti": secrets.token_urlsafe(32),
        })
        
        return jwt.encode(to_encode, security_config.SECRET_KEY, algorithm=security_config.ALGORITHM)
    
    @staticmethod
    def decode_token(token: str) -> Optional[dict]:
        """Decode and validate JWT token with enhanced security checks"""
        try:
            payload = jwt.decode(
                token, 
                security_config.SECRET_KEY, 
                algorithms=[security_config.ALGORITHM],
                options={
                    "verify_exp": True,
                    "verify_iat": True,
                    "verify_nbf": True,
                    "require": ["exp", "iat", "jti"]
                }
            )
            
            # Additional validation
            if "jti" not in payload:
                return None
                
            return payload
            
        except JWTError as e:
            print(f"JWT validation error: {e}")
            return None

class SecureAPIKeyManager:
    """Secure API key management with proper hashing"""
    
    @staticmethod
    def generate_api_key() -> tuple[str, str]:
        """Generate a new API key and return (key, hash)"""
        # Generate a secure random key
        raw_key = secrets.token_urlsafe(32)
        
        # Create a prefixed key for identification
        api_key = f"osk_{raw_key}"
        
        # Hash the key for storage
        key_hash = pwd_context.hash(api_key)
        
        return api_key, key_hash
    
    @staticmethod
    def verify_api_key(api_key: str, stored_hash: str) -> bool:
        """Verify API key against stored hash"""
        return pwd_context.verify(api_key, stored_hash)
    
    @staticmethod
    def hash_api_key(api_key: str) -> str:
        """Hash an API key for storage"""
        return pwd_context.hash(api_key)

# Backwards compatibility functions
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Generate secure password hash"""
    # Validate password strength
    is_valid, message = PasswordValidator.validate_password(password)
    if not is_valid:
        raise ValueError(f"Password validation failed: {message}")
        
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token (backwards compatibility)"""
    return SecureTokenManager.create_access_token(data, expires_delta)

def create_refresh_token(data: dict):
    """Create JWT refresh token (backwards compatibility)"""
    return SecureTokenManager.create_refresh_token(data)

def decode_token(token: str) -> Optional[dict]:
    """Decode and validate JWT token (backwards compatibility)"""
    return SecureTokenManager.decode_token(token)

def create_api_key_hash(api_key: str) -> str:
    """Create a hash for API key storage (backwards compatibility)"""
    return SecureAPIKeyManager.hash_api_key(api_key)

def verify_api_key(api_key: str, hashed_key: str) -> bool:
    """Verify an API key against its hash (backwards compatibility)"""
    return SecureAPIKeyManager.verify_api_key(api_key, hashed_key)