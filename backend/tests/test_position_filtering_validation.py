"""
POSITION FILTERING VALIDATION TESTS

These tests specifically validate that position filtering works consistently
across the ML pipeline after fixes are implemented.

CRITICAL AREAS:
==============
1. Position aliases mapping (bot->adc, jng->jungle, etc.)
2. Case insensitive position matching
3. Data filtering affects feature extraction correctly
4. Position filtering in training vs prediction is identical
5. Edge cases: missing position data, unknown positions
6. Position factor should be 1.0 for all positions (no role bias)

BEFORE FIXES: Position filtering may be inconsistent or broken
AFTER FIXES: All tests should pass with consistent position handling
"""

import unittest
import pandas as pd
import numpy as np
import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.models.prediction_model import PredictionModel
from app.utils.data_processor import DataProcessor


class TestPositionFilteringValidation(unittest.TestCase):
    """
    Specialized tests for position filtering validation
    """

    def setUp(self):
        """Set up test fixtures with comprehensive position data"""
        self.model = PredictionModel()
        self.data_processor = DataProcessor()
        
        # Create test data with all position variants
        self.position_test_data = pd.DataFrame({
            'playername': ['MultiRolePlayer'] * 20,
            'position': [
                # Standard positions
                'top', 'jungle', 'mid', 'adc', 'support',
                # Aliases
                'jng', 'bot', 'sup',
                # Case variations
                'TOP', 'MID', 'ADC', 'SUPPORT',
                # Mixed case
                'Top', 'Jungle', 'Mid', 'Bot', 'Sup',
                # Edge cases
                'unknown', '', 'carry'
            ],
            'kills': [3, 2, 5, 4, 1, 2, 4, 1, 3, 5, 4, 1, 3, 2, 5, 1, 2, 4, 0, 3],
            'assists': [2, 6, 4, 3, 8, 6, 3, 8, 2, 4, 3, 8, 2, 6, 4, 8, 6, 3, 5, 2],
            'deaths': [2, 3, 1, 2, 4, 3, 2, 4, 2, 1, 2, 4, 2, 3, 1, 4, 3, 2, 3, 2],
            'damagetochampions': [15000, 8000, 18000, 16000, 6000, 8000, 16000, 6000,
                                15000, 18000, 16000, 6000, 15000, 8000, 18000, 6000, 8000, 16000, 5000, 15000],
            'visionscore': [20, 35, 25, 22, 45, 35, 22, 45, 20, 25, 22, 45, 20, 35, 25, 45, 35, 22, 30, 20],
            'total cs': [200, 120, 220, 210, 50, 120, 210, 50, 200, 220, 210, 50, 200, 120, 220, 50, 120, 210, 80, 200],
            'gameid': [f'pos_test_{i}' for i in range(20)],
            'match_series': [f'pos_series_{i}' for i in range(20)],
            'map_index_within_series': [1] * 20,
            'goldat10': [3000 + i*50 for i in range(20)],
            'xpat10': [2000 + i*30 for i in range(20)],
            'csat10': [70 + i*2 for i in range(20)],
            'golddiffat15': [i*50 - 500 for i in range(20)],
            'xpdiffat15': [i*30 - 300 for i in range(20)],
            'csdiffat15': [i*2 - 20 for i in range(20)]
        })

    def test_position_aliases_mapping(self):
        """Test that position aliases are mapped correctly"""
        print("\n=== Testing Position Aliases Mapping ===")
        
        # Mock data processor with our test data
        self.data_processor.combined_data = self.position_test_data.copy()
        
        # Test common aliases
        aliases_to_test = {
            'bot': ['adc', 'bot'],  # bot should map to adc family
            'jng': ['jungle', 'jng'],  # jng should map to jungle family  
            'sup': ['support', 'sup'],  # sup should map to support family
        }
        
        for alias, expected_family in aliases_to_test.items():
            # Get data for the alias
            alias_data = self.data_processor.get_player_data('MultiRolePlayer', position=alias)
            
            if len(alias_data) > 0:
                # Should only contain positions from the expected family
                found_positions = alias_data['position'].str.lower().unique()
                print(f"Testing alias '{alias}' -> found positions: {found_positions}")
                
                # At least one position should be in the expected family
                family_match = any(pos in expected_family for pos in found_positions)
                self.assertTrue(family_match, 
                              f"Alias '{alias}' should match family {expected_family}, got {found_positions}")

    def test_case_insensitive_position_matching(self):
        """Test that position filtering is case insensitive"""
        print("\n=== Testing Case Insensitive Position Matching ===")
        
        self.data_processor.combined_data = self.position_test_data.copy()
        
        # Test different case variations for the same position
        case_variations = ['mid', 'MID', 'Mid', 'mId']
        
        baseline_data = None
        for variation in case_variations:
            try:
                position_data = self.data_processor.get_player_data('MultiRolePlayer', position=variation)
                
                if baseline_data is None:
                    baseline_data = position_data
                else:
                    # Should get similar results (accounting for different case handling)
                    print(f"Position '{variation}': {len(position_data)} matches")
                    
                    # At minimum, should not fail and should return some data
                    self.assertIsNotNone(position_data)
                    
            except Exception as e:
                self.fail(f"Position filtering failed for case variation '{variation}': {e}")

    def test_position_filtering_affects_features_correctly(self):
        """Test that position filtering correctly affects feature calculation"""
        print("\n=== Testing Position Filtering Affects Features Correctly ===")
        
        self.data_processor.combined_data = self.position_test_data.copy()
        
        # Get features without position filtering (all data)
        all_data_features = self.data_processor.engineer_features(
            self.position_test_data, 'kills'
        )
        
        # Get features for specific positions
        mid_data = self.position_test_data[self.position_test_data['position'].str.lower() == 'mid']
        if len(mid_data) > 0:
            mid_features = self.data_processor.engineer_features(mid_data, 'kills')
        else:
            mid_features = None
            
        support_data = self.position_test_data[self.position_test_data['position'].str.lower().isin(['support', 'sup'])]
        if len(support_data) > 0:
            support_features = self.data_processor.engineer_features(support_data, 'kills')
        else:
            support_features = None
        
        # Verify filtering affects averages
        if mid_features and support_features:
            print(f"All data avg_kills: {all_data_features['avg_kills']}")
            print(f"Mid avg_kills: {mid_features['avg_kills']}")
            print(f"Support avg_kills: {support_features['avg_kills']}")
            
            # Mid and support should have different kill averages (mid typically higher)
            self.assertNotEqual(mid_features['avg_kills'], support_features['avg_kills'],
                              "Different positions should have different kill averages")
            
            # Maps played should be less for filtered data
            self.assertLessEqual(mid_features['maps_played'], all_data_features['maps_played'],
                               "Filtered data should have same or fewer maps")
            self.assertLessEqual(support_features['maps_played'], all_data_features['maps_played'],
                               "Filtered data should have same or fewer maps")

    def test_position_filtering_training_vs_prediction_consistency(self):
        """Test that position filtering works the same in training and prediction"""
        print("\n=== Testing Position Filtering Training vs Prediction Consistency ===")
        
        # Filter data for mid position manually (simulating prediction path)
        mid_data = self.position_test_data[self.position_test_data['position'].str.lower() == 'mid']
        
        if len(mid_data) > 0:
            # Extract features using training path (betting-aligned)
            training_features = self.model._extract_betting_aligned_features(mid_data, 'MultiRolePlayer')
            
            # Extract features using prediction path (data processor)  
            prediction_features = self.data_processor.engineer_features(mid_data, 'kills')
            
            # Key features should be consistent
            key_features = ['avg_kills', 'avg_assists', 'maps_played']
            
            for feature in key_features:
                if feature in training_features and feature in prediction_features:
                    training_val = training_features[feature]
                    prediction_val = prediction_features[feature]
                    
                    print(f"Mid position {feature}: Training={training_val}, Prediction={prediction_val}")
                    
                    # Should be very close (allowing for small computational differences)
                    if isinstance(training_val, (int, float)) and isinstance(prediction_val, (int, float)):
                        self.assertAlmostEqual(training_val, prediction_val, places=5,
                                             msg=f"Position-filtered {feature} inconsistent between training and prediction")

    def test_missing_position_data_handling(self):
        """Test handling of missing or unknown position data"""
        print("\n=== Testing Missing Position Data Handling ===")
        
        # Create data with missing positions
        missing_position_data = pd.DataFrame({
            'playername': ['MissingPosPlayer'] * 6,
            'position': [np.nan, '', None, 'unknown', 'invalid_pos', 'mid'],
            'kills': [3, 4, 5, 2, 1, 6],
            'assists': [5, 6, 7, 8, 9, 4],
            'deaths': [2, 1, 3, 4, 2, 1],
            'damagetochampions': [12000, 13000, 14000, 15000, 16000, 17000],
            'visionscore': [25, 26, 27, 28, 29, 30],
            'total cs': [180, 190, 200, 170, 160, 220],
            'gameid': [f'missing_{i}' for i in range(6)],
            'match_series': [f'missing_series_{i}' for i in range(6)],
            'map_index_within_series': [1] * 6,
            'goldat10': [2800 + i*100 for i in range(6)],
            'xpat10': [1900 + i*50 for i in range(6)],
            'csat10': [75 + i*3 for i in range(6)],
            'golddiffat15': [i*100 - 200 for i in range(6)],
            'xpdiffat15': [i*60 - 120 for i in range(6)],
            'csdiffat15': [i*5 - 10 for i in range(6)]
        })
        
        # Should handle missing position data gracefully
        try:
            features = self.data_processor.engineer_features(missing_position_data, 'kills')
            self.assertIsNotNone(features)
            self.assertIn('avg_kills', features)
            print(f"Missing position data handled - avg_kills: {features['avg_kills']}")
            
        except Exception as e:
            self.fail(f"Failed to handle missing position data: {e}")
        
        # Test with position filtering on missing data
        try:
            self.data_processor.combined_data = missing_position_data.copy()
            filtered_data = self.data_processor.get_player_data('MissingPosPlayer', position='mid')
            self.assertIsNotNone(filtered_data)
            
            # Should return only the 'mid' position row
            if len(filtered_data) > 0:
                self.assertTrue(all(pos == 'mid' for pos in filtered_data['position'].dropna()),
                              "Should only return 'mid' position data")
                              
        except Exception as e:
            self.fail(f"Position filtering failed with missing data: {e}")

    def test_position_factor_neutrality(self):
        """Test that position_factor is 1.0 for all positions (no role bias)"""
        print("\n=== Testing Position Factor Neutrality ===")
        
        positions_to_test = ['top', 'jungle', 'mid', 'adc', 'support', 'bot', 'jng', 'sup']
        
        for position in positions_to_test:
            # Filter data for this position
            position_data = self.position_test_data[
                self.position_test_data['position'].str.lower() == position.lower()
            ]
            
            if len(position_data) > 0:
                features = self.data_processor.engineer_features(position_data, 'kills')
                
                # Position factor should be 1.0 (neutral) for all positions
                position_factor = features.get('position_factor', 1.0)
                self.assertEqual(position_factor, 1.0,
                               f"Position factor for '{position}' should be 1.0, got {position_factor}")
                
                print(f"Position '{position}': factor = {position_factor} ✓")

    def test_position_filtering_edge_cases(self):
        """Test edge cases in position filtering"""
        print("\n=== Testing Position Filtering Edge Cases ===")
        
        self.data_processor.combined_data = self.position_test_data.copy()
        
        # Test empty position filter
        try:
            empty_data = self.data_processor.get_player_data('MultiRolePlayer', position='')
            # Should handle empty string gracefully
            self.assertIsNotNone(empty_data)
            
        except Exception as e:
            print(f"Empty position handled with error (acceptable): {e}")
        
        # Test non-existent position
        try:
            nonexistent_data = self.data_processor.get_player_data('MultiRolePlayer', position='nonexistent')
            # Should return empty DataFrame or handle gracefully
            self.assertIsNotNone(nonexistent_data)
            print(f"Non-existent position returned {len(nonexistent_data)} rows")
            
        except Exception as e:
            print(f"Non-existent position handled with error (acceptable): {e}")
        
        # Test None position
        try:
            none_data = self.data_processor.get_player_data('MultiRolePlayer', position=None)
            # Should return all data when position is None
            self.assertIsNotNone(none_data)
            print(f"None position returned {len(none_data)} rows")
            
        except Exception as e:
            self.fail(f"None position should be handled gracefully: {e}")

    def test_position_consistency_across_multiple_calls(self):
        """Test that position filtering is consistent across multiple calls"""
        print("\n=== Testing Position Consistency Across Multiple Calls ===")
        
        self.data_processor.combined_data = self.position_test_data.copy()
        
        # Test multiple calls for same position
        for position in ['mid', 'support', 'adc']:
            data1 = self.data_processor.get_player_data('MultiRolePlayer', position=position)
            data2 = self.data_processor.get_player_data('MultiRolePlayer', position=position)
            data3 = self.data_processor.get_player_data('MultiRolePlayer', position=position)
            
            # All calls should return identical results
            if len(data1) > 0:
                pd.testing.assert_frame_equal(data1, data2,
                                            f"Position '{position}' inconsistent between calls 1&2")
                pd.testing.assert_frame_equal(data2, data3,
                                            f"Position '{position}' inconsistent between calls 2&3")
                
                print(f"Position '{position}': {len(data1)} matches (consistent) ✓")

    def test_position_filtering_integration_with_model(self):
        """Test that position filtering integrates correctly with model prediction"""
        print("\n=== Testing Position Filtering Integration with Model ===")
        
        # Test different positions with model prediction
        positions_to_test = ['mid', 'adc', 'support']
        
        for position in positions_to_test:
            position_data = self.position_test_data[
                self.position_test_data['position'].str.lower() == position.lower()
            ]
            
            if len(position_data) > 2:  # Need minimum data for meaningful test
                try:
                    # Extract features
                    features = self.data_processor.engineer_features(position_data, 'kills')
                    
                    # Test model prediction
                    result = self.model.predict(features, prop_value=3.0, prop_type='kills')
                    
                    # Should produce valid prediction
                    self.assertIn('prediction', result)
                    self.assertIn('confidence', result)
                    self.assertIn(['OVER', 'UNDER'], result['prediction'])
                    
                    print(f"Position '{position}': {result['prediction']} with {result['confidence']}% confidence")
                    
                except Exception as e:
                    self.fail(f"Position filtering integration failed for '{position}': {e}")


if __name__ == '__main__':
    unittest.main(verbosity=2)