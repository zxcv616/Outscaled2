#!/usr/bin/env python3
"""
Test script to verify the position filtering fix for the 500 error
"""

import sys
import os
sys.path.append('/Users/matthewwiecking/Desktop/Outscaled2/backend')

from app.utils.data_processor import DataProcessor
from app.main import PredictionRequest
from pydantic import Field

def test_position_filtering():
    """Test the position filtering functionality"""
    print("Testing position filtering fix...")
    
    # Initialize data processor
    processor = DataProcessor()
    
    # Check if data loaded
    if processor.combined_data is None or processor.combined_data.empty:
        print("❌ No data loaded - cannot test")
        return False
    
    print(f"✅ Data loaded: {len(processor.combined_data)} rows")
    
    # Get available positions
    positions = processor.get_available_positions()
    print(f"✅ Available positions: {positions}")
    
    # Test position filtering with various inputs
    test_positions = ['TOP', 'top', 'jng', 'jungle', 'mid', 'bot', 'adc']
    
    for test_pos in test_positions:
        try:
            # Test the position filtering method directly
            sample_data = processor.combined_data.head(100)  # Use first 100 rows
            filtered = processor._filter_data_by_position(sample_data, test_pos)
            print(f"✅ Position '{test_pos}': {len(sample_data)} -> {len(filtered)} matches")
        except Exception as e:
            print(f"❌ Error testing position '{test_pos}': {e}")
            return False
    
    # Create a test request similar to what caused the 500 error
    class TestRequest:
        def __init__(self):
            self.player_names = ["Mojito"]  # From example.md
            self.prop_type = "kills"
            self.prop_value = 5.5
            self.map_range = [1, 3]
            self.opponent = "TestOpponent"
            self.tournament = "TSC"
            self.team = "Misa Esports"
            self.match_date = "2024-01-06"
            self.position_roles = ["TOP"]  # This was causing the 500 error
            self.strict_mode = False
    
    # Test the full processing pipeline
    try:
        request = TestRequest()
        features = processor.process_request(request, strict_mode=False)
        print(f"✅ Full processing test successful")
        print(f"   Features generated: {len(features)} items")
        print(f"   Sample size: {features.get('maps_played', 0)} maps")
        return True
    except Exception as e:
        print(f"❌ Full processing test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_position_filtering()
    print(f"\n{'✅ All tests passed!' if success else '❌ Tests failed!'}")
    sys.exit(0 if success else 1)