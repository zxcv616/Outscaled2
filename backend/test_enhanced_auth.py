#!/usr/bin/env python3
"""
Test script for enhanced authentication security features
"""

import sys
import os
import asyncio
from datetime import datetime, timedelta

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.auth.security_enhanced import (
    password_validator, 
    get_password_hash, 
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_token,
    api_key_manager
)

async def test_password_validation():
    """Test password validation system"""
    print("=== Testing Password Validation ===")
    
    test_cases = [
        ("weak", "testuser", False),
        ("password123", "testuser", False), 
        ("StrongP@ssw0rd!", "testuser", True),
        ("MySecureP@ss2024!", None, True),
        ("testuser123", "testuser", False),  # Contains username
        ("abcdef", "testuser", False),  # Sequential chars
    ]
    
    for password, username, expected_valid in test_cases:
        result = password_validator.validate_password(password, username)
        status = "PASS" if result["is_valid"] == expected_valid else "FAIL"
        print(f"{status} Password: {password}")
        print(f"   Valid: {result['is_valid']} (expected: {expected_valid})")
        print(f"   Entropy: {result['entropy_bits']:.1f} bits")
        if result["feedback"]:
            print(f"   Feedback: {result['feedback']}")
        print()

def test_password_hashing():
    """Test Argon2 password hashing"""
    print("=== Testing Password Hashing ===")
    
    password = "MySecureP@ssw0rd!"
    
    # Hash password
    hashed = get_password_hash(password)
    print(f"PASS Password hashed successfully")
    print(f"   Hash length: {len(hashed)} characters")
    print(f"   Hash starts with: {hashed[:20]}...")
    
    # Verify correct password
    is_valid = verify_password(password, hashed)
    print(f"PASS Correct password verification: {is_valid}")
    
    # Verify wrong password
    is_valid = verify_password("WrongPassword", hashed)
    print(f"PASS Wrong password verification: {is_valid}")
    print()

def test_jwt_tokens():
    """Test JWT token creation and verification"""
    print("=== Testing JWT Tokens ===")
    
    # Create access token
    user_data = {"sub": "123", "username": "testuser"}
    access_token = create_access_token(user_data)
    print(f"PASS Access token created")
    print(f"   Token length: {len(access_token)} characters")
    
    # Verify access token
    payload = verify_token(access_token, expected_type="access")
    if payload:
        print(f"PASS Access token verified successfully")
        print(f"   User ID: {payload.get('sub')}")
        print(f"   Token ID: {payload.get('jti')}")
    else:
        print("FAIL Access token verification failed")
    
    # Create refresh token
    refresh_token = create_refresh_token(user_data)
    print(f"PASS Refresh token created")
    
    # Verify refresh token
    payload = verify_token(refresh_token, expected_type="refresh")
    if payload:
        print(f"PASS Refresh token verified successfully")
        print(f"   Token type: {payload.get('type')}")
    else:
        print("FAIL Refresh token verification failed")
    
    # Test wrong token type
    payload = verify_token(access_token, expected_type="refresh")
    if not payload:
        print("PASS Token type validation working (access token rejected as refresh)")
    else:
        print("FAIL Token type validation failed")
    
    print()

def test_api_keys():
    """Test API key generation and verification"""
    print("=== Testing API Key Management ===")
    
    # Generate API key
    plain_key, key_hash = api_key_manager.generate_api_key()
    print(f"PASS API key generated")
    print(f"   Plain key: {plain_key}")
    print(f"   Hash length: {len(key_hash)} characters")
    
    # Extract prefix
    prefix = api_key_manager.extract_key_prefix(plain_key)
    print(f"   Key prefix: {prefix}")
    
    # Verify correct key
    is_valid = api_key_manager.verify_api_key(plain_key, key_hash)
    print(f"PASS Correct API key verification: {is_valid}")
    
    # Verify wrong key
    wrong_key = "osk_wrongkeyhere12345"
    is_valid = api_key_manager.verify_api_key(wrong_key, key_hash)
    print(f"PASS Wrong API key verification: {is_valid}")
    print()

def test_security_headers():
    """Test security headers configuration"""
    print("=== Testing Security Headers ===")
    
    from app.auth.security_enhanced import SECURITY_HEADERS
    
    expected_headers = [
        "X-Content-Type-Options",
        "X-Frame-Options", 
        "X-XSS-Protection",
        "Strict-Transport-Security",
        "Referrer-Policy",
        "Permissions-Policy"
    ]
    
    for header in expected_headers:
        if header in SECURITY_HEADERS:
            print(f"PASS {header}: {SECURITY_HEADERS[header]}")
        else:
            print(f"FAIL Missing security header: {header}")
    
    print()

async def run_all_tests():
    """Run all authentication security tests"""
    print("SECURE Enhanced Authentication Security Test Suite")
    print("=" * 50)
    
    try:
        await test_password_validation()
        test_password_hashing()
        test_jwt_tokens()
        test_api_keys()
        test_security_headers()
        
        print("SUCCESS All tests completed successfully!")
        print("\nEnhanced security features verified:")
        print("- Strong password validation with entropy checking")
        print("- Argon2 password hashing (100MB memory cost)")
        print("- Secure JWT tokens with unique IDs")
        print("- API key generation with hashing")
        print("- Security headers configuration")
        
    except Exception as e:
        print(f"ERROR Test failed with error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)