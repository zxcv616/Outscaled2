#!/usr/bin/env python3
"""
Test confidence calculation consistency without requiring data files
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

# Mock the data processor to avoid data file dependency
class MockDataProcessor:
    def __init__(self):
        self.data = None
    
    def get_all_players(self):
        return []
    
    def load_data(self):
        pass

# Replace the data processor before importing the model
import app.utils.data_processor
app.utils.data_processor.DataProcessor = MockDataProcessor

from app.models.prediction_model import PredictionModel
import json

def test_confidence_consistency():
    """Test that confidence calculations are consistent between predict and curve"""
    print("Testing Confidence Calculation Consistency")
    print("=" * 50)
    
    # Initialize model
    model = PredictionModel()
    
    # Test features
    test_features = {
        'avg_kills': 3.5,
        'avg_assists': 5.0,
        'std_dev_kills': 1.5,
        'std_dev_assists': 2.0,
        'maps_played': 20,
        'longterm_kills_avg': 3.5,
        'longterm_assists_avg': 5.0,
        'form_z_score': 0.5,
        'form_deviation_ratio': 0.3,
        'position_factor': 1.15,
        'sample_size_score': 0.8,
        'avg_deaths': 2.5,
        'avg_damage': 25000,
        'avg_vision': 45,
        'avg_cs': 280,
        'avg_gold_at_10': 8500,
        'avg_xp_at_10': 6200,
        'avg_cs_at_10': 85,
        'avg_gold_diff_15': 500,
        'avg_xp_diff_15': 300,
        'avg_cs_diff_15': 10,
        'volatility': 0.3,
        'tier_info': {'weight': 0.8, 'tier': 2, 'name': 'Same Region/Year'}
    }
    
    # Test cases with different prop values
    test_cases = [
        {"name": "Low Prop (High Gap)", "prop": 1.0},
        {"name": "Medium Prop (Medium Gap)", "prop": 2.5},
        {"name": "High Prop (Low Gap)", "prop": 3.5},
        {"name": "Very High Prop (UNDER prediction)", "prop": 5.0}
    ]
    
    all_consistent = True
    
    for test in test_cases:
        prop_value = test["prop"]
        print(f"\nTest: {test['name']} (Prop: {prop_value})")
        
        # Get prediction from main predict method
        prediction_result = model.predict(test_features, prop_value)
        main_confidence = prediction_result['confidence']
        
        # Get prediction curve
        curve = model.generate_prediction_curve(test_features, prop_value, step=0.5, range_size=3)
        
        # Find the matching prop value in the curve
        curve_confidence = None
        for point in curve:
            if abs(point['prop_value'] - prop_value) < 0.01:
                curve_confidence = point['confidence']
                break
        
        print(f"  Main Prediction: {prediction_result['prediction']}")
        print(f"  Main Confidence: {main_confidence}%")
        print(f"  Curve Confidence: {curve_confidence}%")
        print(f"  Expected Stat: {prediction_result['expected_stat']}")
        
        if curve_confidence is not None:
            if abs(main_confidence - curve_confidence) < 0.1:
                print(f"  Status: CONSISTENT")
            else:
                print(f"  Status: INCONSISTENT (Difference: {abs(main_confidence - curve_confidence):.1f}%)")
                all_consistent = False
        else:
            print(f"  Status: ERROR - No matching prop value in curve")
            all_consistent = False
    
    print("\n" + "=" * 50)
    if all_consistent:
        print("SUCCESS: All confidence calculations are consistent!")
    else:
        print("FAILURE: Some confidence calculations are inconsistent!")
    
    return all_consistent

if __name__ == "__main__":
    success = test_confidence_consistency()
    sys.exit(0 if success else 1)