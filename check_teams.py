import requests

# Test different tournaments for DARKWINGS and Rahel
test_cases = [
    {"player": "DARKWINGS", "tournament": "NACL"},
    {"player": "Rahel", "tournament": "LCKC"},
    {"player": "Rahel", "tournament": "LEC"},
]

for test in test_cases:
    payload = {
        "player_names": [test["player"]],
        "prop_type": "kills",
        "prop_value": 5.5,
        "map_range": [1, 2],
        "match_date": "2025-08-04",
        "opponent": "Test Team",
        "tournament": test["tournament"],
        "position_roles": ["MID"],
    }
    
    response = requests.post("http://localhost:8000/predict", json=payload)
    
    try:
        if response.status_code == 200:
            data = response.json()
            print(f"\n{test['player']} ({test['tournament']}): SUCCESS")
            print(f"  Prediction: {data['prediction']}")
            print(f"  Expected: {data['expected_stat']:.1f}")
            print(f"  Confidence: {data['confidence']:.1f}%")
        else:
            print(f"\n{test['player']} ({test['tournament']}): Error {response.status_code}")
            print(f"  Response: {response.text}")
    except Exception as e:
        print(f"\n{test['player']} ({test['tournament']}): Exception - {e}") 