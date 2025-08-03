import requests

# Test different team names for DARKWINGS and Rahel
test_cases = [
    {"player": "DARKWINGS", "tournament": "NACL", "team": "Disguised"},
    {"player": "DARKWINGS", "tournament": "NACL", "team": "Team Liquid Academy"},
    {"player": "DARKWINGS", "tournament": "NACL", "team": "TL Academy"},
    {"player": "Rahel", "tournament": "LEC", "team": "Disguised"},
    {"player": "Rahel", "tournament": "LEC", "team": "Team Vitality"},
    {"player": "Rahel", "tournament": "LEC", "team": "Vitality"},
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
        "team": test["team"],
        "position_roles": ["MID"],
    }
    
    response = requests.post("http://localhost:8000/predict", json=payload)
    
    try:
        if response.status_code == 200:
            data = response.json()
            print(f"\n{test['player']} ({test['tournament']} - {test['team']}): SUCCESS")
            print(f"  Prediction: {data['prediction']}")
            print(f"  Expected: {data['expected_stat']:.1f}")
            print(f"  Confidence: {data['confidence']:.1f}%")
        else:
            print(f"\n{test['player']} ({test['tournament']} - {test['team']}): Error {response.status_code}")
            print(f"  Response: {response.text}")
    except Exception as e:
        print(f"\n{test['player']} ({test['tournament']} - {test['team']}): Exception - {e}") 