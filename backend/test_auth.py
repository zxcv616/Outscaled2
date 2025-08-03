#!/usr/bin/env python3
"""
Test authentication system
"""

import requests
import json
import sys

BASE_URL = "http://localhost:8000"

def test_registration():
    """Test user registration"""
    print("Testing user registration...")
    
    response = requests.post(
        f"{BASE_URL}/auth/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpassword123",
            "full_name": "Test User"
        }
    )
    
    if response.status_code == 200:
        print("✓ Registration successful")
        return response.json()
    else:
        print(f"✗ Registration failed: {response.text}")
        return None

def test_login(username, password):
    """Test user login"""
    print("\nTesting user login...")
    
    response = requests.post(
        f"{BASE_URL}/auth/token",
        data={
            "username": username,
            "password": password
        }
    )
    
    if response.status_code == 200:
        print("✓ Login successful")
        return response.json()
    else:
        print(f"✗ Login failed: {response.text}")
        return None

def test_authenticated_request(token):
    """Test authenticated prediction request"""
    print("\nTesting authenticated prediction...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.post(
        f"{BASE_URL}/predict",
        headers=headers,
        json={
            "player_names": ["TestPlayer"],
            "prop_type": "kills",
            "prop_value": 4.0,
            "map_range": [1, 3],
            "opponent": "TestOpponent",
            "tournament": "TestTournament",
            "match_date": "2024-12-01",
            "position_roles": ["MID"]
        }
    )
    
    if response.status_code == 200:
        print("✓ Authenticated prediction successful")
        result = response.json()
        print(f"  Prediction: {result['prediction']}")
        print(f"  Confidence: {result['confidence']}%")
    else:
        print(f"✗ Authenticated prediction failed: {response.text}")

def test_api_key_creation(token):
    """Test API key creation"""
    print("\nTesting API key creation...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.post(
        f"{BASE_URL}/auth/api-keys",
        headers=headers,
        json={
            "name": "Test API Key",
            "expires_in_days": 30
        }
    )
    
    if response.status_code == 200:
        print("✓ API key creation successful")
        return response.json()
    elif response.status_code == 403:
        print("✗ API key creation failed: Feature not available in free tier")
        return None
    else:
        print(f"✗ API key creation failed: {response.text}")
        return None

def test_subscription_info(token):
    """Test subscription information endpoint"""
    print("\nTesting subscription info...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(
        f"{BASE_URL}/auth/subscription",
        headers=headers
    )
    
    if response.status_code == 200:
        print("✓ Subscription info retrieved")
        info = response.json()
        print(f"  Tier: {info['tier']}")
        print(f"  API Calls: {info['api_calls_used']}/{info['api_calls_limit']}")
        print(f"  Features: {', '.join(info['features'])}")
    else:
        print(f"✗ Subscription info failed: {response.text}")

def main():
    """Run authentication tests"""
    print("Authentication System Test Suite")
    print("================================\n")
    
    # Test registration
    user = test_registration()
    if not user:
        print("\nRegistration failed, trying with existing user...")
        # Try login with test credentials
        login_result = test_login("testuser", "testpassword123")
    else:
        # Test login
        login_result = test_login("testuser", "testpassword123")
    
    if login_result:
        token = login_result["access_token"]
        
        # Test authenticated request
        test_authenticated_request(token)
        
        # Test subscription info
        test_subscription_info(token)
        
        # Test API key creation
        test_api_key_creation(token)
    
    print("\n✓ Authentication tests completed!")

if __name__ == "__main__":
    main()