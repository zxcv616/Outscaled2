import requests
import json

# Test without tournament parameter
payload = {
    "player_names": ["DARKWINGS"],
    "prop_type": "kills",
    "prop_value": 5.5,
    "map_range": [1, 2],
    "match_date": "2025-08-04",
    "opponent": "Shopify Rebellion",
    "position_roles": ["MID"],
}

print("Sending payload WITHOUT tournament:")
print(json.dumps(payload, indent=2))

response = requests.post("http://localhost:8000/predict", json=payload)

print(f"\nResponse status: {response.status_code}")
print(f"Response body: {response.text}")

# Also test with a player we know works
print("\n" + "="*50)
print("Testing with Castle (known to work):")

payload_castle = {
    "player_names": ["Castle"],
    "prop_type": "kills",
    "prop_value": 4.0,
    "map_range": [1, 2],
    "match_date": "2025-08-04",
    "opponent": "Shopify Rebellion",
    "position_roles": ["TOP"],
}

print("Sending payload WITHOUT tournament for Castle:")
print(json.dumps(payload_castle, indent=2))

response_castle = requests.post("http://localhost:8000/predict", json=payload_castle)

print(f"\nResponse status: {response_castle.status_code}")
print(f"Response body: {response_castle.text}") 