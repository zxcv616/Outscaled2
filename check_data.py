import requests

# Test different team combinations for DARKWINGS and Rahel
test_cases = [
    {"player": "DARKWINGS", "tournament": "LTA N", "team": None},
    {"player": "DARKWINGS", "tournament": "NACL", "team": None},
    {"player": "Rahel", "tournament": "LTA N", "team": None},
    {"player": "Rahel", "tournament": "LCKC", "team": None},
    {"player": "Rahel", "tournament": "LEC", "team": None},
]

for test in test_cases:
    payload = {
        "player_names": [test["player"]],
        "tournament": test["tournament"],
        "map_range": [1, 3]
    }
    
    response = requests.post("http://localhost:8000/check-data-availability", json=payload)
    
    try:
        if response.status_code == 200:
            data = response.json()
            print(f"\n{test['player']} ({test['tournament']}):")
            print(f"  Available: {data.get('available', False)}")
            print(f"  Message: {data.get('message', 'No message')}")
            if 'suggestions' in data:
                print(f"  Suggestions: {data['suggestions']}")
        else:
            print(f"\n{test['player']} ({test['tournament']}): Error {response.status_code} - {response.text}")
    except Exception as e:
        print(f"\n{test['player']} ({test['tournament']}): Exception - {e}") 