#!/usr/bin/env python3
"""
Debug script to test DataProcessor independently
"""

from app.utils.data_processor import DataProcessor

print("=== TESTING DATAPROCESSOR DIRECTLY ===")

# Create a new DataProcessor instance
dp = DataProcessor()

print(f"Combined data is None: {dp.combined_data is None}")
if dp.combined_data is not None:
    print(f"Combined data shape: {dp.combined_data.shape}")
    print(f"Combined data empty: {dp.combined_data.empty}")
    
    if not dp.combined_data.empty:
        print(f"First 10 players: {dp.combined_data['playername'].dropna().head(10).tolist()}")

# Test the get_all_players method
players = dp.get_all_players()
print(f"Total players returned: {len(players)}")
print(f"First 10 players from method: {players[:10]}")