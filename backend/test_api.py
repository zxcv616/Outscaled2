#!/usr/bin/env python3
"""
Test script for Outscaled.GG Backend API
"""

import requests
import json
from typing import Dict, Any

def test_prediction_api():
    """Test the prediction endpoint with sample data"""
    
    # Sample request as specified in the MVP
    sample_request = {
        "player_names": ["Zika"],
        "prop_type": "kills",
        "prop_value": 3.5,
        "map_range": [1, 2],
        "opponent": "FPX",
        "tournament": "LPL",
        "team": "LNG Esports",
        "match_date": "2025-08-01T02:00:00",
        "position_roles": ["TOP"]
    }
    
    try:
        # Make request to the API
        response = requests.post(
            "http://localhost:8000/predict",
            json=sample_request,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ API Test Successful!")
            print(f"Prediction: {result['prediction']}")
            print(f"Confidence: {result['confidence']}%")
            print(f"Expected Stat: {result['expected_stat']}")
            print(f"Confidence Interval: {result['confidence_interval']}")
            print(f"Reasoning: {result['reasoning']}")
            print(f"Player Stats: {json.dumps(result['player_stats'], indent=2)}")
            print(f"Data Years: {result['data_years']}")
        else:
            print(f"❌ API Test Failed: {response.status_code}")
            print(f"Error: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to API. Make sure the server is running on localhost:8000")
    except Exception as e:
        print(f"❌ Test failed with error: {e}")

def test_health_endpoint():
    """Test the health check endpoint"""
    try:
        response = requests.get("http://localhost:8000/health")
        if response.status_code == 200:
            print("✅ Health check successful!")
            print(f"Status: {response.json()}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to health endpoint")
    except Exception as e:
        print(f"❌ Health check failed with error: {e}")

if __name__ == "__main__":
    print("🧪 Testing Outscaled.GG Backend API")
    print("=" * 50)
    
    print("\n1. Testing health endpoint...")
    test_health_endpoint()
    
    print("\n2. Testing prediction endpoint...")
    test_prediction_api()
    
    print("\n" + "=" * 50)
    print("🏁 Test completed!") 