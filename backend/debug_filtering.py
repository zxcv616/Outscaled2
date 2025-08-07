#!/usr/bin/env python3

import pandas as pd
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_filtering():
    """Debug the filtering logic step by step"""
    
    # Load data
    data_path = '/app/data/2024_LoL_esports_match_data_from_OraclesElixir.csv'
    data = pd.read_csv(data_path, low_memory=False)
    logger.info(f"Loaded {len(data)} rows of data")
    
    # Test the specific case from the error
    player_names = ['Faker']
    tournament = 'AC'
    team = 'T1'
    map_range = [1, 2]
    position = 'MID'
    
    logger.info(f"Testing filters for: {player_names}, tournament: {tournament}, team: {team}, map_range: {map_range}, position: {position}")
    
    # Step 1: Filter by player names
    filtered_data = data.copy()
    filtered_data = filtered_data[filtered_data['playername'].isin(player_names)]
    logger.info(f"After player filter: {len(filtered_data)} rows")
    
    # Step 2: Filter by tournament
    filtered_data = filtered_data[filtered_data['league'] == tournament]
    logger.info(f"After tournament filter: {len(filtered_data)} rows")
    
    # Step 3: Filter by team
    filtered_data = filtered_data[filtered_data['teamname'] == team]
    logger.info(f"After team filter: {len(filtered_data)} rows")
    
    # Step 4: Filter by map range
    if 'map_index_within_series' in filtered_data.columns:
        filtered_data = filtered_data[
            (filtered_data['map_index_within_series'] >= map_range[0]) & 
            (filtered_data['map_index_within_series'] <= map_range[1])
        ]
        logger.info(f"After map range filter: {len(filtered_data)} rows")
    else:
        logger.warning("No map_index_within_series column found")
    
    # Step 5: Filter by position
    if len(filtered_data) > 0:
        logger.info(f"Position values in filtered data: {filtered_data['position'].unique()}")
        
        # Test position mapping
        position_mapping = {
            'MID': ['mid'],
            'mid': ['mid'],
            'Mid': ['mid']
        }
        
        target_csv_positions = position_mapping.get(position, [position.lower()])
        logger.info(f"Target CSV positions: {target_csv_positions}")
        
        # Convert to lowercase for comparison
        player_positions_lower = filtered_data['position'].astype(str).str.lower()
        position_matches = player_positions_lower.isin(target_csv_positions)
        filtered_data = filtered_data[position_matches]
        logger.info(f"After position filter: {len(filtered_data)} rows")
    else:
        logger.warning("No data remaining for position filtering")
    
    # Show available tournaments and teams for Faker
    faker_data = data[data['playername'] == 'Faker']
    logger.info(f"All Faker data: {len(faker_data)} rows")
    logger.info(f"Faker tournaments: {faker_data['league'].unique()}")
    logger.info(f"Faker teams: {faker_data['teamname'].unique()}")

if __name__ == "__main__":
    debug_filtering() 