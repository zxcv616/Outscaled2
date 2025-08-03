import requests
from datetime import datetime

players = [
    {"name": "Castle", "opponent": "Shopify Rebellion", "role": "TOP", "value": 4, "tournament": "LCS"},
    {"name": "eXyu", "opponent": "Shopify Rebellion", "role": "JNG", "value": 4, "tournament": "LCS"},
    {"name": "DARKWINGS", "opponent": "Shopify Rebellion", "role": "MID", "value": 5.5, "tournament": "NACL"},
    {"name": "Rahel", "opponent": "Shopify Rebellion", "role": "BOT", "value": 6, "tournament": "LEC"},
    {"name": "Fudge", "opponent": "Disguised", "role": "TOP", "value": 7.5, "tournament": "LCS"},
    {"name": "Contractz", "opponent": "Disguised", "role": "JNG", "value": 6.5, "tournament": "LCS"},
    {"name": "Palafox", "opponent": "Disguised", "role": "MID", "value": 8, "tournament": "LCS"},
    {"name": "Bvoy", "opponent": "Disguised", "role": "BOT", "value": 10.5, "tournament": "LCS"},
]

for player in players:
    payload = {
        "player_names": [player["name"]],
        "prop_type": "kills",
        "prop_value": player["value"],
        "map_range": [1, 2],  # Correct betting logic for Maps 1-2
        "match_date": "2025-08-04",  # YYYY-MM-DD format
        "opponent": player["opponent"],
        "tournament": player["tournament"],
        "position_roles": [player["role"]],
    }

    response = requests.post("http://localhost:8000/predict", json=payload)

    try:
        if response.status_code == 200:
            data = response.json()
            prediction = data["prediction"]
            expected = data["expected_stat"]
            confidence = data["confidence"]
            print(f"{player['name']} (Auto - {player['role']}): {prediction} {player['value']} → expected={expected:.1f}, conf={confidence:.1f}%")
        else:
            print(f"Error with {player['name']}: {response.status_code}, {response.text}")
    except Exception as e:
        print(f"Error with {player['name']}: {response.status_code}, {response.text}")
        print(f"Exception: {e}")
