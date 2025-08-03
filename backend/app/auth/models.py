#!/usr/bin/env python3
"""
Authentication Models and Database Schema
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, ForeignKey, Text, Enum
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime
import uuid
import enum

Base = declarative_base()

class SubscriptionTier(enum.Enum):
    """Subscription tier levels"""
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"

class User(Base):
    """User model for authentication"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(200), nullable=False)
    full_name = Column(String(100))
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Security fields
    email_verified = Column(Boolean, default=False)
    failed_login_attempts = Column(Integer, default=0)
    account_locked_until = Column(DateTime, nullable=True)
    last_login = Column(DateTime, nullable=True)
    password_changed_at = Column(DateTime, default=datetime.utcnow)
    two_factor_enabled = Column(Boolean, default=False)
    two_factor_secret = Column(String(100), nullable=True)
    
    # Subscription tier
    subscription_tier = Column(Enum(SubscriptionTier), default=SubscriptionTier.FREE)
    api_calls_limit = Column(Integer, default=100)  # Daily limit
    api_calls_used = Column(Integer, default=0)
    last_api_reset = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")
    predictions = relationship("PredictionHistory", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(username='{self.username}', email='{self.email}')>"

class APIKey(Base):
    """API Key model for programmatic access"""
    __tablename__ = "api_keys"
    
    id = Column(Integer, primary_key=True, index=True)
    key_hash = Column(String(200), unique=True, index=True, nullable=False)  # Store hash instead of raw key
    key_prefix = Column(String(12), nullable=False)  # Store prefix for identification (osk_xxxx)
    name = Column(String(100), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used = Column(DateTime)
    expires_at = Column(DateTime)
    
    # Security features
    rate_limit = Column(Integer, default=60)  # Requests per minute
    allowed_ips = Column(Text)  # JSON array of allowed IPs
    permissions = Column(Text)  # JSON array of allowed permissions
    
    # Relationships
    user = relationship("User", back_populates="api_keys")
    
    def __repr__(self):
        return f"<APIKey(name='{self.name}', user_id={self.user_id}, prefix='{self.key_prefix}')>"

class PredictionHistory(Base):
    """Store prediction history for users"""
    __tablename__ = "prediction_history"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    request_id = Column(String(36), unique=True, index=True, default=lambda: str(uuid.uuid4()))
    
    # Request data
    player_names = Column(Text)  # JSON array
    prop_type = Column(String(20))
    prop_value = Column(Float)
    tournament = Column(String(100))
    
    # Response data
    prediction = Column(String(10))
    confidence = Column(Float)
    expected_stat = Column(Float)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    response_time_ms = Column(Integer)
    model_version = Column(String(20))
    
    # Relationships
    user = relationship("User", back_populates="predictions")
    
    def __repr__(self):
        return f"<PredictionHistory(user_id={self.user_id}, prediction='{self.prediction}')>"

# Pydantic models for API
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=8)

class UserInDB(UserBase):
    id: int
    is_active: bool
    is_superuser: bool
    subscription_tier: str
    api_calls_limit: int
    api_calls_used: int
    created_at: datetime
    
    model_config = {"from_attributes": True}

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int

class TokenData(BaseModel):
    username: Optional[str] = None
    user_id: Optional[int] = None

class APIKeyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    expires_in_days: Optional[int] = Field(None, ge=1, le=365)
    allowed_ips: Optional[list[str]] = None  # IP whitelist
    permissions: Optional[list[str]] = None  # Permission scopes

class APIKeyResponse(BaseModel):
    id: int
    key_prefix: str  # Only show prefix, never full key
    name: str
    is_active: bool
    created_at: datetime
    expires_at: Optional[datetime]
    last_used: Optional[datetime]
    rate_limit: int
    allowed_ips: Optional[list[str]] = None
    permissions: Optional[list[str]] = None
    
    model_config = {"from_attributes": True}

class APIKeyCreateResponse(BaseModel):
    """Response when creating API key - includes the actual key once"""
    id: int
    key: str  # Full key shown only on creation
    key_prefix: str
    name: str
    is_active: bool
    created_at: datetime
    expires_at: Optional[datetime]
    rate_limit: int
    allowed_ips: Optional[list[str]] = None
    permissions: Optional[list[str]] = None
    
    model_config = {"from_attributes": True}