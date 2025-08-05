"""
FEATURE EXTRACTION VALIDATION TESTS

These tests validate that feature extraction produces consistent results between
training and prediction phases after the ML pipeline fixes.

CRITICAL VALIDATION AREAS:
========================
1. Training vs Prediction Feature Consistency
2. Feature Vector Ordering Consistency  
3. Edge Case Handling (missing data, zero values)
4. Position Filtering Consistency
5. Combined vs Average Statistics Logic
6. Feature Extraction Determinism

TESTING METHODOLOGY:
===================
- Create identical data scenarios for training and prediction
- Extract features using both paths and compare results
- Test with various edge cases and data conditions
- Validate position filtering affects features consistently
- Ensure feature vectors maintain order across calls

These tests should PASS after the ML pipeline fixes are implemented.
They currently may FAIL until fixes are complete.
"""

import unittest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.models.prediction_model import PredictionModel
from app.utils.data_processor import DataProcessor


class TestFeatureExtractionValidation(unittest.TestCase):
    """
    Comprehensive tests for feature extraction consistency
    """

    def setUp(self):
        """Set up test fixtures"""
        self.model = PredictionModel()
        self.data_processor = DataProcessor()
        
        # Create comprehensive test data that covers all scenarios
        self.test_player_data = pd.DataFrame({
            'playername': ['TestPlayer'] * 20,
            'position': ['mid'] * 10 + ['adc'] * 5 + ['sup'] * 5,
            'kills': [5, 3, 7, 2, 4, 6, 8, 1, 3, 5, 4, 6, 7, 3, 2, 1, 0, 2, 1, 3],
            'assists': [8, 6, 4, 12, 7, 5, 3, 15, 9, 6, 2, 4, 3, 5, 8, 12, 15, 10, 13, 8],
            'deaths': [2, 4, 1, 5, 3, 2, 1, 6, 2, 3, 3, 2, 1, 4, 5, 6, 4, 3, 2, 1],
            'damagetochampions': [15000, 12000, 18000, 8000, 16000, 14000, 20000, 6000, 13000, 17000,
                                12000, 16000, 18000, 14000, 10000, 8000, 6000, 9000, 7000, 11000],
            'visionscore': [25, 30, 20, 45, 28, 22, 18, 50, 26, 24, 15, 18, 20, 22, 25, 35, 40, 30, 38, 28],
            'total cs': [200, 180, 220, 60, 210, 190, 240, 40, 195, 205, 180, 200, 220, 190, 150, 80, 50, 70, 60, 90],
            'gameid': [f'series{i//2}_map{i%2+1}' for i in range(20)],  # Creates series1_map1, series1_map2, etc.
            'match_series': [f'series{i//2}' for i in range(20)],
            'map_index_within_series': [(i % 2) + 1 for i in range(20)],
            'goldat10': [3000, 2800, 3200, 2200, 3100, 2900, 3300, 2000, 2950, 3050,
                        2800, 3000, 3200, 2900, 2600, 2300, 2100, 2400, 2200, 2500],
            'xpat10': [2000, 1800, 2200, 1600, 2100, 1900, 2300, 1500, 1950, 2050,
                      1800, 2000, 2200, 1900, 1700, 1550, 1400, 1600, 1500, 1650],
            'csat10': [80, 70, 90, 45, 85, 75, 95, 35, 78, 82, 70, 80, 90, 75, 65, 50, 40, 55, 45, 60],
            'golddiffat15': [500, -200, 800, -400, 600, 300, 900, -600, 400, 700,
                           200, 500, 800, 300, 100, -300, -500, -200, -400, -100],
            'xpdiffat15': [300, -100, 500, -300, 400, 200, 600, -400, 250, 450,
                          150, 300, 500, 200, 50, -200, -350, -150, -250, -50],
            'csdiffat15': [20, -10, 30, -20, 25, 15, 35, -25, 18, 28, 10, 20, 30, 15, 5, -15, -20, -10, -18, -5]
        })
        
        # Create edge case data (missing values, zeros)
        self.edge_case_data = pd.DataFrame({
            'playername': ['EdgePlayer'] * 6,
            'position': ['mid'] * 6,
            'kills': [0, np.nan, 1, 0, np.nan, 2],
            'assists': [np.nan, 0, 5, 0, 1, np.nan],
            'deaths': [1, 2, np.nan, 0, 3, 1],
            'damagetochampions': [0, 5000, np.nan, 8000, 0, 12000],
            'visionscore': [np.nan, 10, 15, 0, 20, np.nan],
            'total cs': [50, np.nan, 80, 0, 100, 60],
            'gameid': [f'edge_series{i//2}_map{i%2+1}' for i in range(6)],
            'match_series': [f'edge_series{i//2}' for i in range(6)],
            'map_index_within_series': [(i % 2) + 1 for i in range(6)],
            'goldat10': [2000, np.nan, 2500, 0, 2200, 2400],
            'xpat10': [1500, 1600, np.nan, 0, 1700, 1800],
            'csat10': [50, np.nan, 60, 0, 65, 70],
            'golddiffat15': [0, np.nan, 200, -500, 100, np.nan],
            'xpdiffat15': [np.nan, -100, 150, -300, 50, 0],
            'csdiffat15': [5, 0, np.nan, -15, 10, 8]
        })

    def test_training_vs_prediction_feature_consistency(self):
        """
        Test that feature extraction produces identical results for training and prediction
        when given the same data
        """
        print("\n=== Testing Training vs Prediction Feature Consistency ===")
        
        # Extract features using training path (betting-aligned extraction)
        training_features = self.model._extract_betting_aligned_features(
            self.test_player_data, 'TestPlayer'
        )
        
        # Extract features using prediction path (data processor)
        prediction_features = self.data_processor.engineer_features(
            self.test_player_data, 'kills'
        )
        
        # Compare key features that should be identical
        key_features = ['avg_kills', 'avg_assists', 'std_dev_kills', 'std_dev_assists', 
                       'maps_played', 'position_factor']
        
        for feature in key_features:
            if feature in training_features and feature in prediction_features:
                training_val = training_features[feature]
                prediction_val = prediction_features[feature]
                
                print(f"{feature}: Training={training_val}, Prediction={prediction_val}")
                
                # Allow small floating point differences
                if isinstance(training_val, (int, float)) and isinstance(prediction_val, (int, float)):
                    self.assertAlmostEqual(
                        training_val, prediction_val, places=5,
                        msg=f"Feature {feature} inconsistent: training={training_val}, prediction={prediction_val}"
                    )
                else:
                    self.assertEqual(
                        training_val, prediction_val,
                        msg=f"Feature {feature} inconsistent: training={training_val}, prediction={prediction_val}"
                    )

    def test_feature_vector_ordering_consistency(self):
        """
        Test that feature vectors maintain consistent ordering across multiple calls
        """
        print("\n=== Testing Feature Vector Ordering Consistency ===")
        
        # Create feature dictionary
        features = {
            'avg_kills': 4.0,
            'avg_assists': 6.0,
            'std_dev_kills': 1.5,
            'std_dev_assists': 2.0,
            'maps_played': 10,
            'longterm_kills_avg': 3.8,
            'longterm_assists_avg': 5.8,
            'form_z_score': 0.5,
            'form_deviation_ratio': 0.3,
            'position_factor': 1.0,
            'sample_size_score': 0.8,
            'avg_deaths': 2.5,
            'avg_damage': 15000,
            'avg_vision': 25,
            'avg_cs': 200,
            'avg_gold_at_10': 8000,
            'avg_xp_at_10': 6000,
            'avg_cs_at_10': 80,
            'avg_gold_diff_10': 0,
            'avg_xp_diff_10': 0,
            'avg_cs_diff_10': 0,
            'avg_gold_at_15': 12000,
            'avg_xp_at_15': 9000,
            'avg_cs_at_15': 120,
            'avg_gold_diff_15': 0,
            'avg_xp_diff_15': 0,
            'avg_cs_diff_15': 0,
            'avg_gold_at_20': 16000,
            'avg_xp_at_20': 12000,
            'avg_cs_at_20': 160,
            'avg_gold_diff_20': 0,
            'avg_xp_diff_20': 0,
            'avg_cs_diff_20': 0
        }
        
        # Extract feature vectors multiple times
        vector1 = self.model._dict_to_feature_vector(features)
        vector2 = self.model._dict_to_feature_vector(features)
        vector3 = self.model._dict_to_feature_vector(features)
        
        # Verify vectors are identical
        np.testing.assert_array_equal(vector1, vector2, 
                                     "Feature vectors not consistent between calls")
        np.testing.assert_array_equal(vector2, vector3,
                                     "Feature vectors not consistent between calls")
        
        # Verify vector length matches expected feature count
        expected_length = len(self.model.FEATURE_ORDER)  # Dynamic based on FEATURE_ORDER
        self.assertEqual(len(vector1), expected_length,
                        f"Feature vector length {len(vector1)} != expected {expected_length}")
        
        print(f"Feature vector length: {len(vector1)}")
        print(f"First 5 features: {vector1[:5]}")

    def test_edge_case_handling_consistency(self):
        """
        Test that edge cases (missing data, zero values) are handled consistently
        between training and prediction
        """
        print("\n=== Testing Edge Case Handling Consistency ===")
        
        # Test with edge case data containing NaN and zero values
        training_features = self.model._extract_betting_aligned_features(
            self.edge_case_data, 'EdgePlayer'
        )
        
        prediction_features = self.data_processor.engineer_features(
            self.edge_case_data, 'kills'
        )
        
        # Verify no NaN values in final features
        for feature_name, value in training_features.items():
            self.assertFalse(np.isnan(value) if isinstance(value, (int, float)) else False,
                           f"Training feature {feature_name} contains NaN: {value}")
        
        for feature_name, value in prediction_features.items():
            self.assertFalse(np.isnan(value) if isinstance(value, (int, float)) else False,
                           f"Prediction feature {feature_name} contains NaN: {value}")
        
        # Test zero value handling
        zero_data = self.edge_case_data.copy()
        zero_data['kills'] = 0
        zero_data['assists'] = 0
        
        zero_training_features = self.model._extract_betting_aligned_features(
            zero_data, 'EdgePlayer'
        )
        
        zero_prediction_features = self.data_processor.engineer_features(
            zero_data, 'kills'
        )
        
        # Both should handle zero values gracefully
        self.assertIsNotNone(zero_training_features)
        self.assertIsNotNone(zero_prediction_features)
        
        print(f"Edge case training features: {len(training_features)} features")
        print(f"Edge case prediction features: {len(prediction_features)} features")

    def test_position_filtering_consistency(self):
        """
        Test that position filtering affects feature extraction consistently
        """
        print("\n=== Testing Position Filtering Consistency ===")
        
        # Extract features for all positions
        all_positions_features = self.data_processor.engineer_features(
            self.test_player_data, 'kills'
        )
        
        # Extract features for mid position only 
        mid_data = self.test_player_data[self.test_player_data['position'] == 'mid']
        mid_features = self.data_processor.engineer_features(mid_data, 'kills')
        
        # Extract features for adc position only
        adc_data = self.test_player_data[self.test_player_data['position'] == 'adc']
        adc_features = self.data_processor.engineer_features(adc_data, 'kills')
        
        # Features should be different when position filtering is applied
        self.assertNotEqual(all_positions_features['avg_kills'], mid_features['avg_kills'],
                           "Position filtering should affect average kills")
        
        self.assertNotEqual(mid_features['avg_kills'], adc_features['avg_kills'],
                           "Different positions should have different averages")
        
        # Maps played should reflect filtering
        self.assertLess(mid_features['maps_played'], all_positions_features['maps_played'],
                       "Filtered data should have fewer maps")
        
        print(f"All positions avg_kills: {all_positions_features['avg_kills']}")
        print(f"Mid position avg_kills: {mid_features['avg_kills']}")  
        print(f"ADC position avg_kills: {adc_features['avg_kills']}")
        
        # Test position factor consistency (should be 1.0 for all after fixes)
        self.assertEqual(all_positions_features.get('position_factor', 1.0), 1.0,
                        "Position factor should be 1.0 (no role adjustments)")
        self.assertEqual(mid_features.get('position_factor', 1.0), 1.0,
                        "Position factor should be 1.0 (no role adjustments)")
        self.assertEqual(adc_features.get('position_factor', 1.0), 1.0,
                        "Position factor should be 1.0 (no role adjustments)")

    def test_combined_vs_average_statistics_logic(self):
        """
        Test that combined statistics logic works correctly for betting terminology
        """
        print("\n=== Testing Combined vs Average Statistics Logic ===")
        
        # Create series data (pairs of maps)
        series_data = self.test_player_data.head(4)  # 2 series, 2 maps each
        
        # Extract features with combined logic
        features = self.model._extract_betting_aligned_features(series_data, 'TestPlayer')
        
        # Manually calculate expected combined averages
        # Series 1: maps 0,1 -> kills [5,3] -> combined = 8
        # Series 2: maps 2,3 -> kills [7,2] -> combined = 9
        # Expected combined average: (8+9)/2 = 8.5
        
        if 'combined_kills' in features:
            expected_combined = (5+3+7+2) / 2  # Total kills / number of series
            print(f"Expected combined kills per series: {expected_combined}")
            print(f"Actual combined kills: {features['combined_kills']}")
            
            # Verify combined logic vs simple average
            simple_average = series_data['kills'].mean()  # (5+3+7+2)/4 = 4.25
            print(f"Simple average kills: {simple_average}")
            
            # Combined should be different from simple average
            self.assertNotEqual(features['combined_kills'], simple_average,
                               "Combined kills should differ from simple average")
        
        # Test that series_played is calculated correctly
        if 'series_played' in features:
            expected_series = 2  # We have 2 complete series
            self.assertEqual(features['series_played'], expected_series,
                           f"Expected {expected_series} series, got {features['series_played']}")

    def test_feature_extraction_determinism(self):
        """
        Test that feature extraction is deterministic (same input -> same output)
        """
        print("\n=== Testing Feature Extraction Determinism ===")
        
        # Extract features multiple times with same data
        features1 = self.model._extract_betting_aligned_features(
            self.test_player_data, 'TestPlayer'
        )
        features2 = self.model._extract_betting_aligned_features(
            self.test_player_data, 'TestPlayer'
        )
        features3 = self.model._extract_betting_aligned_features(
            self.test_player_data, 'TestPlayer'
        )
        
        # Compare all numeric features
        for feature_name in features1.keys():
            if isinstance(features1[feature_name], (int, float)):
                self.assertAlmostEqual(
                    features1[feature_name], features2[feature_name], places=10,
                    msg=f"Feature {feature_name} not deterministic between calls 1&2"
                )
                self.assertAlmostEqual(
                    features2[feature_name], features3[feature_name], places=10,
                    msg=f"Feature {feature_name} not deterministic between calls 2&3"
                )
        
        print(f"Tested {len(features1)} features for determinism")

    def test_feature_validation_with_model_prediction(self):
        """
        Test that extracted features work correctly with model prediction
        """
        print("\n=== Testing Feature Validation with Model Prediction ===")
        
        # Extract features using betting-aligned method
        features = self.model._extract_betting_aligned_features(
            self.test_player_data, 'TestPlayer'
        )
        
        # Convert to feature vector format expected by model
        feature_vector = self.model._dict_to_feature_vector(features)
        
        # Verify vector can be used with model
        try:
            prepared_features = self.model._prepare_features(features)
            self.assertIsNotNone(prepared_features)
            self.assertEqual(prepared_features.shape[0], 1)  # Single sample
            
            # Test actual prediction
            prediction_result = self.model.predict(features, prop_value=5.0)
            
            # Verify prediction structure
            required_keys = ['prediction', 'confidence', 'expected_stat', 
                           'confidence_interval', 'reasoning']
            for key in required_keys:
                self.assertIn(key, prediction_result,
                            f"Missing key {key} in prediction result")
            
            print(f"Prediction: {prediction_result['prediction']}")
            print(f"Confidence: {prediction_result['confidence']}%")
            print(f"Expected: {prediction_result['expected_stat']}")
            
        except Exception as e:
            self.fail(f"Feature vector failed in model prediction: {e}")

    def test_data_processor_get_player_data_consistency(self):
        """
        Test that DataProcessor.get_player_data produces consistent results
        """
        print("\n=== Testing DataProcessor get_player_data Consistency ===")
        
        # Mock the data processor's combined_data
        self.data_processor.combined_data = self.test_player_data.copy()
        
        # Get player data multiple times
        player_data1 = self.data_processor.get_player_data('TestPlayer')
        player_data2 = self.data_processor.get_player_data('TestPlayer')
        
        # Should be identical
        pd.testing.assert_frame_equal(player_data1, player_data2,
                                     "get_player_data not consistent between calls")
        
        # Test with position filtering
        mid_data1 = self.data_processor.get_player_data('TestPlayer', position='mid')
        mid_data2 = self.data_processor.get_player_data('TestPlayer', position='mid')
        
        pd.testing.assert_frame_equal(mid_data1, mid_data2,
                                     "get_player_data with position not consistent")
        
        # Verify position filtering works
        self.assertTrue(all(pos == 'mid' for pos in mid_data1['position']),
                       "Position filtering not working correctly")
        
        print(f"Total player data: {len(player_data1)} matches")
        print(f"Mid position data: {len(mid_data1)} matches")

    def test_missing_feature_handling(self):
        """
        Test handling of missing or incomplete features
        """
        print("\n=== Testing Missing Feature Handling ===")
        
        # Create incomplete feature dictionary
        incomplete_features = {
            'avg_kills': 4.0,
            'maps_played': 5
            # Missing many required features
        }
        
        # Test _prepare_features with incomplete data
        prepared = self.model._prepare_features(incomplete_features)
        
        # Should still produce valid feature vector
        self.assertIsNotNone(prepared)
        self.assertEqual(prepared.shape[0], 1)
        self.assertEqual(prepared.shape[1], 21)  # Expected feature count
        
        # Test prediction with incomplete features
        try:
            result = self.model.predict(incomplete_features, prop_value=3.5)
            self.assertIn('prediction', result)
            self.assertIn('confidence', result)
            print(f"Prediction with incomplete features: {result['prediction']}")
        except Exception as e:
            self.fail(f"Model failed with incomplete features: {e}")

    def test_extreme_values_handling(self):
        """
        Test handling of extreme statistical values
        """
        print("\n=== Testing Extreme Values Handling ===")
        
        # Create data with extreme values
        extreme_data = pd.DataFrame({
            'playername': ['ExtremePlayer'] * 4,
            'position': ['mid'] * 4,
            'kills': [0, 0, 50, 0],  # Extreme outlier
            'assists': [0, 100, 0, 0],  # Extreme outlier  
            'deaths': [0, 0, 0, 20],  # Extreme outlier
            'damagetochampions': [0, 0, 100000, 0],  # Extreme outlier
            'visionscore': [0, 200, 0, 0],  # Extreme outlier
            'total cs': [0, 0, 1000, 0],  # Extreme outlier
            'gameid': ['extreme1_1', 'extreme1_2', 'extreme2_1', 'extreme2_2'],
            'match_series': ['extreme1', 'extreme1', 'extreme2', 'extreme2'],
            'map_index_within_series': [1, 2, 1, 2],
            'goldat10': [0, 0, 20000, 0],
            'xpat10': [0, 0, 15000, 0],
            'csat10': [0, 0, 500, 0],
            'golddiffat15': [-10000, 10000, 0, 0],
            'xpdiffat15': [-5000, 5000, 0, 0],
            'csdiffat15': [-200, 200, 0, 0]
        })
        
        # Extract features with extreme values
        extreme_features = self.model._extract_betting_aligned_features(
            extreme_data, 'ExtremePlayer'
        )
        
        # Features should be calculated without errors
        self.assertIsNotNone(extreme_features)
        
        # Test prediction with extreme features
        try:
            result = self.model.predict(extreme_features, prop_value=10.0)
            self.assertIn('prediction', result)
            print(f"Prediction with extreme values: {result['prediction']}")
        except Exception as e:
            self.fail(f"Model failed with extreme values: {e}")

    def test_feature_validation_integration(self):
        """
        Integration test combining multiple validation aspects
        """
        print("\n=== Integration Test for Feature Validation ===")
        
        # Test full pipeline: data -> features -> prediction
        test_scenarios = [
            ('normal_data', self.test_player_data),
            ('edge_case_data', self.edge_case_data)
        ]
        
        for scenario_name, data in test_scenarios:
            print(f"\nTesting scenario: {scenario_name}")
            
            # Extract features
            features = self.model._extract_betting_aligned_features(
                data, data['playername'].iloc[0]
            )
            
            # Validate feature completeness
            required_features = ['avg_kills', 'maps_played', 'position_factor']
            for req_feature in required_features:
                self.assertIn(req_feature, features,
                            f"Missing required feature {req_feature} in {scenario_name}")
            
            # Test prediction
            try:
                result = self.model.predict(features, prop_value=4.0)
                self.assertIn('prediction', result)
                self.assertIn('confidence', result)
                self.assertGreaterEqual(result['confidence'], 0)
                self.assertLessEqual(result['confidence'], 100)
                
                print(f"{scenario_name} - Prediction: {result['prediction']}, "
                      f"Confidence: {result['confidence']}%")
                
            except Exception as e:
                self.fail(f"Integration test failed for {scenario_name}: {e}")


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)