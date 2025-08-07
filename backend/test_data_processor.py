#!/usr/bin/env python3

import sys
import os
sys.path.append('/app')

from app.utils.data_processor import DataProcessor
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_data_processor():
    """Test the DataProcessor with the specific case that was failing"""
    
    # Initialize DataProcessor
    data_processor = DataProcessor()
    
    # Test the specific case from the error
    player_names = ['Faker']
    tournament = 'AC'
    team = 'T1'
    map_range = [1, 2]
    position = 'MID'
    
    logger.info(f"Testing DataProcessor with: {player_names}, tournament: {tournament}, team: {team}, map_range: {map_range}, position: {position}")
    
    # Test the tiered filtering
    try:
        result = data_processor.filter_player_data_with_tiers(
            player_names=player_names,
            map_range=map_range,
            team=team,
            opponent=None,
            tournament=tournament,
            strict_mode=False,
            position=position
        )
        
        logger.info(f"Tier filtering result: {len(result['data'])} rows")
        logger.info(f"Tier info: {result['tier_info']}")
        
        if len(result['data']) > 0:
            logger.info(f"Sample data columns: {list(result['data'].columns)}")
            logger.info(f"Position values: {result['data']['position'].unique()}")
            logger.info(f"Map index values: {result['data']['map_index_within_series'].unique()}")
        else:
            logger.warning("No data found - this is expected since Faker has no AC tournament data")
            
    except Exception as e:
        logger.error(f"Error in tier filtering: {e}")
    
    # Test with a tournament that Faker actually has data for
    logger.info("\nTesting with LCK tournament (which Faker has data for):")
    try:
        result = data_processor.filter_player_data_with_tiers(
            player_names=player_names,
            map_range=map_range,
            team=team,
            opponent=None,
            tournament='LCK',
            strict_mode=False,
            position=position
        )
        
        logger.info(f"LCK tier filtering result: {len(result['data'])} rows")
        logger.info(f"LCK tier info: {result['tier_info']}")
        
        if len(result['data']) > 0:
            logger.info(f"LCK sample data columns: {list(result['data'].columns)}")
            logger.info(f"LCK position values: {result['data']['position'].unique()}")
            logger.info(f"LCK map index values: {result['data']['map_index_within_series'].unique()}")
            
    except Exception as e:
        logger.error(f"Error in LCK tier filtering: {e}")

if __name__ == "__main__":
    test_data_processor() 