#!/usr/bin/env python3
"""
Enhanced security module for Outscaled.GG
Fixes critical JWT secret vulnerability and improves password security
"""

import os
import secrets
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import re
from math import log2

from jose import JWTError, jwt
from passlib.context import CryptContext
from passlib.hash import argon2

logger = logging.getLogger(__name__)

# Enhanced security configuration
class SecurityConfig:
    """Centralized security configuration with validation"""
    
    def __init__(self):
        self._validate_environment()
        self.SECRET_KEY = self._get_secure_secret_key()
        self.ALGORITHM = "HS256"
        self.ACCESS_TOKEN_EXPIRE_MINUTES = 30
        self.REFRESH_TOKEN_EXPIRE_DAYS = 7
        self.API_KEY_PREFIX = "osk_"  # Outscaled Key prefix
        
        # Enhanced password context with Argon2
        self.pwd_context = CryptContext(
            schemes=["argon2", "bcrypt"],
            default="argon2",
            argon2__memory_cost=102400,  # 100MB
            argon2__time_cost=2,
            argon2__parallelism=8,
            deprecated="bcrypt"
        )
        
    def _validate_environment(self):
        """Validate security environment settings"""
        env = os.getenv("ENVIRONMENT", "development")
        if env == "production":
            # Enforce strict security in production
            if not os.getenv("SECRET_KEY"):
                raise ValueError("SECRET_KEY must be set in production environment")
            if os.getenv("SECRET_KEY") == "your-secret-key-here-change-in-production":
                raise ValueError("Default SECRET_KEY detected in production!")
                
    def _get_secure_secret_key(self) -> str:
        """Get or generate a secure secret key"""
        secret_key = os.getenv("SECRET_KEY")
        
        # Check for weak/default keys
        weak_keys = [
            "your-secret-key-here-change-in-production",
            "secret",
            "changeme",
            "password",
            "12345678"
        ]
        
        if not secret_key or secret_key in weak_keys:
            if os.getenv("ENVIRONMENT") == "production":
                raise ValueError("Secure SECRET_KEY required in production")
            else:
                # Generate secure key for development
                logger.warning("Generating random SECRET_KEY for development")
                secret_key = secrets.token_urlsafe(64)
                
        # Validate key strength
        if len(secret_key) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters")
            
        return secret_key

# Global security config instance
security_config = SecurityConfig()

# Enhanced password validation
class PasswordValidator:
    """Advanced password validation with entropy checking"""
    
    MIN_LENGTH = 8
    MIN_ENTROPY_BITS = 50
    
    # Common password patterns to reject
    COMMON_PASSWORDS = {
        "password", "12345678", "qwerty", "abc123", "password123",
        "admin", "letmein", "welcome", "123456789", "football"
    }
    
    @classmethod
    def validate_password(cls, password: str, username: Optional[str] = None) -> Dict[str, Any]:
        """
        Validate password strength with multiple criteria
        Returns dict with is_valid and feedback messages
        """
        feedback = []
        is_valid = True
        
        # Length check
        if len(password) < cls.MIN_LENGTH:
            feedback.append(f"Password must be at least {cls.MIN_LENGTH} characters")
            is_valid = False
            
        # Common password check
        if password.lower() in cls.COMMON_PASSWORDS:
            feedback.append("Password is too common")
            is_valid = False
            
        # Username similarity check
        if username and username.lower() in password.lower():
            feedback.append("Password cannot contain username")
            is_valid = False
            
        # Character variety check
        has_upper = bool(re.search(r'[A-Z]', password))
        has_lower = bool(re.search(r'[a-z]', password))
        has_digit = bool(re.search(r'\d', password))
        has_special = bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', password))
        
        variety_score = sum([has_upper, has_lower, has_digit, has_special])
        if variety_score < 3:
            feedback.append("Password should contain uppercase, lowercase, numbers, and symbols")
            is_valid = False
            
        # Sequential character check
        if cls._has_sequential_chars(password):
            feedback.append("Password contains sequential characters")
            is_valid = False
            
        # Entropy calculation
        entropy = cls._calculate_entropy(password)
        if entropy < cls.MIN_ENTROPY_BITS:
            feedback.append(f"Password is too predictable (entropy: {entropy:.1f} bits, required: {cls.MIN_ENTROPY_BITS})")
            is_valid = False
            
        return {
            "is_valid": is_valid,
            "feedback": feedback,
            "entropy_bits": entropy,
            "strength_score": min(100, int(entropy / cls.MIN_ENTROPY_BITS * 100))
        }
    
    @staticmethod
    def _has_sequential_chars(password: str) -> bool:
        """Check for sequential characters like 'abc' or '123'"""
        for i in range(len(password) - 2):
            if ord(password[i]) + 1 == ord(password[i+1]) == ord(password[i+2]) - 1:
                return True
        return False
    
    @staticmethod
    def _calculate_entropy(password: str) -> float:
        """Calculate password entropy in bits"""
        charset_size = 0
        
        if re.search(r'[a-z]', password):
            charset_size += 26
        if re.search(r'[A-Z]', password):
            charset_size += 26
        if re.search(r'\d', password):
            charset_size += 10
        if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            charset_size += 32
            
        if charset_size == 0:
            return 0
            
        # Shannon entropy approximation
        entropy = len(password) * log2(charset_size)
        return entropy

# Enhanced token management
class TokenManager:
    """Secure token creation and validation with blacklisting support"""
    
    def __init__(self):
        self.config = security_config
        self.blacklisted_tokens = set()  # In production, use Redis
        
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create a secure access token with unique ID"""
        to_encode = data.copy()
        
        # Add token metadata
        to_encode.update({
            "type": "access",
            "jti": secrets.token_urlsafe(16),  # Unique token ID
            "iat": datetime.utcnow()
        })
        
        # Set expiration
        expire = datetime.utcnow() + (expires_delta or timedelta(minutes=self.config.ACCESS_TOKEN_EXPIRE_MINUTES))
        to_encode.update({"exp": expire})
        
        # Encode token
        encoded_jwt = jwt.encode(to_encode, self.config.SECRET_KEY, algorithm=self.config.ALGORITHM)
        return encoded_jwt
    
    def create_refresh_token(self, data: dict) -> str:
        """Create a secure refresh token"""
        to_encode = data.copy()
        
        # Add token metadata
        to_encode.update({
            "type": "refresh",
            "jti": secrets.token_urlsafe(16),
            "iat": datetime.utcnow()
        })
        
        # Longer expiration for refresh tokens
        expire = datetime.utcnow() + timedelta(days=self.config.REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire})
        
        encoded_jwt = jwt.encode(to_encode, self.config.SECRET_KEY, algorithm=self.config.ALGORITHM)
        return encoded_jwt
    
    def verify_token(self, token: str, expected_type: str = "access") -> Optional[Dict[str, Any]]:
        """Verify and decode a token with type checking"""
        try:
            payload = jwt.decode(token, self.config.SECRET_KEY, algorithms=[self.config.ALGORITHM])
            
            # Check token type
            if payload.get("type") != expected_type:
                logger.warning(f"Invalid token type: expected {expected_type}, got {payload.get('type')}")
                return None
                
            # Check if token is blacklisted
            jti = payload.get("jti")
            if jti and jti in self.blacklisted_tokens:
                logger.warning(f"Blacklisted token attempted: {jti}")
                return None
                
            return payload
            
        except JWTError as e:
            logger.error(f"Token verification failed: {e}")
            return None
    
    def blacklist_token(self, token: str):
        """Add token to blacklist (logout functionality)"""
        try:
            payload = jwt.decode(token, self.config.SECRET_KEY, algorithms=[self.config.ALGORITHM])
            jti = payload.get("jti")
            if jti:
                self.blacklisted_tokens.add(jti)
                logger.info(f"Token blacklisted: {jti}")
        except JWTError:
            pass

# Enhanced API key generation and validation
class APIKeyManager:
    """Secure API key generation with hashing"""
    
    def __init__(self):
        self.config = security_config
        
    def generate_api_key(self) -> tuple[str, str]:
        """
        Generate a secure API key
        Returns: (plain_key, key_hash)
        """
        # Generate secure random key
        key_bytes = secrets.token_bytes(32)
        plain_key = f"{self.config.API_KEY_PREFIX}{secrets.token_urlsafe(32)}"
        
        # Hash the key for storage (like passwords)
        key_hash = self.hash_api_key(plain_key)
        
        return plain_key, key_hash
    
    def hash_api_key(self, api_key: str) -> str:
        """Hash an API key for secure storage"""
        # Use Argon2 for API key hashing too
        return argon2.hash(api_key)
    
    def verify_api_key(self, plain_key: str, key_hash: str) -> bool:
        """Verify an API key against its hash"""
        try:
            return argon2.verify(plain_key, key_hash)
        except Exception:
            return False
    
    def extract_key_prefix(self, api_key: str) -> str:
        """Extract prefix for identifying keys (first 12 chars)"""
        return api_key[:12] if len(api_key) > 12 else api_key

# Global instances
token_manager = TokenManager()
api_key_manager = APIKeyManager()
password_validator = PasswordValidator()

# Enhanced security utilities
def get_password_hash(password: str) -> str:
    """Get secure password hash using Argon2"""
    return security_config.pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return security_config.pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create access token (convenience function)"""
    return token_manager.create_access_token(data, expires_delta)

def create_refresh_token(data: dict) -> str:
    """Create refresh token (convenience function)"""
    return token_manager.create_refresh_token(data)

def verify_token(token: str, expected_type: str = "access") -> Optional[Dict[str, Any]]:
    """Verify token (convenience function)"""
    return token_manager.verify_token(token, expected_type)

# Security headers middleware
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()"
}

if __name__ == "__main__":
    # Test security enhancements
    print("Security Configuration Test")
    print(f"Secret key length: {len(security_config.SECRET_KEY)}")
    print(f"API key prefix: {security_config.API_KEY_PREFIX}")
    
    # Test password validation
    test_passwords = ["weak", "StrongP@ssw0rd!", "password123", "MyStr0ng!Pass"]
    for pwd in test_passwords:
        result = password_validator.validate_password(pwd, "testuser")
        print(f"\nPassword: {pwd}")
        print(f"Valid: {result['is_valid']}")
        print(f"Entropy: {result['entropy_bits']:.1f} bits")
        print(f"Feedback: {result['feedback']}")