#!/usr/bin/env python3

import pandas as pd
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_data_loading():
    """Debug the data loading process to understand the position column issue"""
    
    # Try different paths for data files
    data_paths = [
        '/Users/matthewwiecking/Desktop/Outscaled2/data/2024_LoL_esports_match_data_from_OraclesElixir.csv',
        '/app/data/2024_LoL_esports_match_data_from_OraclesElixir.csv',
        '../data/2024_LoL_esports_match_data_from_OraclesElixir.csv',
        '../../data/2024_LoL_esports_match_data_from_OraclesElixir.csv'
    ]
    
    data_2024_path = None
    
    # Find the correct path for 2024 data
    for path in data_paths:
        if os.path.exists(path):
            data_2024_path = path
            break
    
    if data_2024_path is None:
        logger.error("Data files not found at expected paths.")
        return
    
    logger.info(f"Loading data from: {data_2024_path}")
    
    try:
        # Load the data
        data = pd.read_csv(data_2024_path, low_memory=False)
        logger.info(f"Data loaded successfully: {len(data)} rows")
        logger.info(f"Columns: {list(data.columns)}")
        
        # Check position column
        if 'position' in data.columns:
            logger.info(f"Position column found with values: {data['position'].unique()}")
            logger.info(f"Position value counts: {data['position'].value_counts().to_dict()}")
        else:
            logger.error("Position column not found!")
            
        # Check for Faker data
        faker_data = data[data['playername'] == 'Faker']
        logger.info(f"Faker data found: {len(faker_data)} rows")
        if len(faker_data) > 0:
            logger.info(f"Faker positions: {faker_data['position'].unique()}")
            
    except Exception as e:
        logger.error(f"Error loading data: {e}")

if __name__ == "__main__":
    debug_data_loading() 