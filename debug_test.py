import requests
import json

# Test DARKWINGS without team parameter
payload = {
    "player_names": ["DARKWINGS"],
    "prop_type": "kills",
    "prop_value": 5.5,
    "map_range": [1, 2],
    "match_date": "2025-08-04",
    "opponent": "Shopify Rebellion",
    "tournament": "LTA N",
    "position_roles": ["MID"],
}

print("Sending payload:")
print(json.dumps(payload, indent=2))

response = requests.post("http://localhost:8000/predict", json=payload)

print(f"\nResponse status: {response.status_code}")
print(f"Response body: {response.text}") 