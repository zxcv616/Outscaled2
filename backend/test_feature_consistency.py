#!/usr/bin/env python3
"""
Test script to verify feature extraction consistency fixes
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from models.prediction_model import PredictionModel
from utils.data_processor import DataProcessor
import pandas as pd
import numpy as np

def test_unified_feature_extraction():
    """Test unified feature extraction method"""
    print("Testing unified feature extraction...")
    
    model = PredictionModel()
    
    # Test features dictionary
    test_features = {
        'avg_kills': 4.2,
        'avg_assists': 6.8,
        'std_dev_kills': 1.5,
        'maps_played': 15,
        'form_z_score': 0.5
    }
    
    # Test unified extraction
    unified_dict = model._extract_unified_features(test_features, return_as_vector=False)
    unified_vector = model._extract_unified_features(test_features, return_as_vector=True)
    
    print(f"Input features: {len(test_features)}")
    print(f"Unified dict features: {len(unified_dict)}")
    print(f"Unified vector length: {len(unified_vector)}")
    print(f"Expected vector length: {len(model.FEATURE_ORDER)}")
    
    # Verify consistency
    assert len(unified_vector) == len(model.FEATURE_ORDER), "Vector length mismatch"
    assert len(unified_dict) == len(model.FEATURE_ORDER), "Dict length mismatch"
    
    # Verify order consistency
    for i, feature_name in enumerate(model.FEATURE_ORDER):
        expected_value = unified_dict[feature_name]
        actual_value = unified_vector[i]
        assert expected_value == actual_value, f"Order mismatch for {feature_name}: {expected_value} != {actual_value}"
    
    print("✅ Unified feature extraction test passed!")
    return True

def test_feature_validation():
    """Test feature validation methods"""
    print("\nTesting feature validation...")
    
    model = PredictionModel()
    
    # Test with complete features
    complete_features = {feature: 1.0 for feature in model.FEATURE_ORDER}
    validation = model.validate_feature_consistency(complete_features)
    
    print(f"Complete features validation: {validation['is_valid']}")
    print(f"Warnings: {len(validation['warnings'])}")
    print(f"Errors: {len(validation['errors'])}")
    
    # Test with missing features
    incomplete_features = {'avg_kills': 3.0, 'avg_assists': 5.0}
    validation = model.validate_feature_consistency(incomplete_features)
    
    print(f"Incomplete features validation: {validation['is_valid']}")
    print(f"Missing features: {len(validation['feature_coverage']['missing'])}")
    
    # Test with invalid values
    invalid_features = {
        'avg_kills': -1.0,  # Invalid negative value
        'std_dev_kills': -0.5,  # Invalid negative std dev
        'position_factor': 2.5  # Non-neutral position factor
    }
    validation = model.validate_feature_consistency(invalid_features)
    
    print(f"Invalid features validation: {validation['is_valid']}")
    print(f"Errors: {validation['errors']}")
    print(f"Warnings: {validation['warnings']}")
    
    print("✅ Feature validation test passed!")
    return True

def test_training_prediction_consistency():
    """Test that training and prediction use identical feature logic"""
    print("\nTesting training/prediction consistency...")
    
    model = PredictionModel()
    
    # Create mock player data
    mock_data = pd.DataFrame({
        'kills': [3, 5, 4, 6, 2, 4, 3, 5],
        'assists': [7, 9, 6, 8, 5, 7, 6, 8],
        'deaths': [2, 3, 2, 2, 4, 3, 2, 3],
        'damagetochampions': [18000, 22000, 19000, 21000, 16000, 20000, 18500, 21500],
        'visionscore': [35, 42, 38, 45, 32, 40, 36, 43],
        'total cs': [240, 260, 245, 265, 235, 255, 242, 262],
        'position': ['mid', 'mid', 'mid', 'mid', 'mid', 'mid', 'mid', 'mid']
    })
    
    # Extract features using two different methods
    features_from_data = model._extract_unified_features_from_data(mock_data, 'TestPlayer')
    
    # Test dict to vector conversion consistency
    vector_from_dict = model._dict_to_feature_vector(features_from_data)
    vector_from_prepare = model._prepare_features(features_from_data).flatten()
    
    print(f"Vector from dict conversion: length={len(vector_from_dict)}")
    print(f"Vector from prepare_features: length={len(vector_from_prepare)}")
    
    # They should be identical
    assert len(vector_from_dict) == len(vector_from_prepare), "Vector length mismatch"
    
    for i, (a, b) in enumerate(zip(vector_from_dict, vector_from_prepare)):
        assert abs(a - b) < 1e-10, f"Value mismatch at index {i}: {a} != {b}"
    
    print("✅ Training/prediction consistency test passed!")
    return True

def test_expected_stat_calculation():
    """Test expected stat calculation with unified features"""
    print("\nTesting expected stat calculation...")
    
    model = PredictionModel()
    
    test_features = {
        'combined_kills': 8.5,
        'avg_kills': 4.2,
        'std_dev_kills': 1.5,
        'maps_played': 20,
        'form_z_score': 0.3,
        'form_deviation_ratio': 0.25,
        'position_factor': 1.0
    }
    
    # This should not raise any exceptions
    expected_stat = model._calculate_expected_stat(test_features)
    
    print(f"Expected stat calculated: {expected_stat}")
    assert expected_stat >= 0, "Expected stat should be non-negative"
    assert expected_stat < 50, "Expected stat should be reasonable"
    
    print("✅ Expected stat calculation test passed!")
    return True

def main():
    """Run all tests"""
    print("Running feature extraction consistency tests...\n")
    
    tests = [
        test_unified_feature_extraction,
        test_feature_validation,
        test_training_prediction_consistency,
        test_expected_stat_calculation
    ]
    
    passed = 0
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed: {e}")
    
    print(f"\n🎯 Results: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 All feature extraction consistency tests passed!")
        return 0
    else:
        print("⚠️ Some tests failed - feature extraction needs more work")
        return 1

if __name__ == "__main__":
    exit(main())