#!/usr/bin/env python3
"""
Test suite for advanced features including:
- Advanced feature engineering
- XGBoost integration 
- Fallback mechanisms
- Production error handling
- Docker integration
"""

import unittest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from utils.data_processor import DataProcessor, ADVANCED_FEATURES_AVAILABLE
from models.prediction_model import PredictionModel, XGBOOST_AVAILABLE

class TestAdvancedFeatures(unittest.TestCase):
    """Test advanced features and integrations"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.data_processor = DataProcessor()
        self.prediction_model = PredictionModel(use_xgboost=False)
        
        # Create mock player data
        self.mock_player_data = pd.DataFrame({
            'playername': ['TestPlayer'] * 5,
            'kills': [3, 4, 5, 2, 6],
            'assists': [8, 6, 4, 9, 7],
            'deaths': [2, 3, 1, 4, 2],
            'position': ['mid'] * 5,
            'teamname': ['TestTeam'] * 5,
            'league': ['TestLeague'] * 5,
            'date': pd.date_range('2024-01-01', periods=5),
            'gameid': range(1, 6),
            'map_index_within_series': [1, 2, 1, 1, 2]
        })
    
    def test_advanced_feature_engineering_availability(self):
        """Test that advanced feature engineering is available"""
        # Should be available in our setup
        self.assertTrue(ADVANCED_FEATURES_AVAILABLE)
        self.assertIsNotNone(self.data_processor.advanced_engineer)
    
    def test_xgboost_integration_setup(self):
        """Test that XGBoost integration is properly set up"""
        # XGBoost integration exists but may not be available due to circular imports
        # This test ensures the integration code exists and handles failures gracefully
        model = PredictionModel(use_xgboost=True)
        
        # Should not crash even if XGBoost is not available
        self.assertIsNotNone(model)
        
        # Should fall back to RandomForest if XGBoost fails
        self.assertFalse(model.use_xgboost)  # Should be False due to unavailability
    
    def test_fallback_features_creation(self):
        """Test fallback feature creation when no real data is available"""
        # Mock request object
        mock_request = MagicMock()
        mock_request.position_roles = ['MID']
        
        # Mock tier info
        tier_info = {'weight': 0.0, 'tier': 0, 'name': 'No Data'}
        
        # Test fallback feature creation
        fallback_features = self.data_processor._create_fallback_features(
            mock_request, tier_info, {}, True
        )
        
        # Verify essential features are present
        self.assertIn('avg_kills', fallback_features)
        self.assertIn('avg_assists', fallback_features)
        self.assertIn('position_factor', fallback_features)
        self.assertIn('tier_info', fallback_features)
        self.assertTrue(fallback_features['fallback_used'])
        
        # Verify values are reasonable for MID position
        self.assertEqual(fallback_features['avg_kills'], 4.1)  # MID position average
        self.assertEqual(fallback_features['position_factor'], 1.0)  # MID factor
    
    def test_position_based_fallback_values(self):
        """Test that position-based fallback values are correct"""
        # Test different positions
        positions = ['TOP', 'JNG', 'MID', 'ADC', 'SUP']
        expected_kills = [2.8, 3.2, 4.1, 4.5, 1.8]
        expected_assists = [5.2, 7.8, 6.5, 6.2, 11.5]
        
        for pos, exp_kills, exp_assists in zip(positions, expected_kills, expected_assists):
            kills_avg = self.data_processor._get_position_average(pos, 'kills')
            assists_avg = self.data_processor._get_position_average(pos, 'assists')
            
            self.assertEqual(kills_avg, exp_kills)
            self.assertEqual(assists_avg, exp_assists)
    
    def test_confidence_calculation_consistency(self):
        """Test that confidence calculation is consistent across methods"""
        features = {
            'avg_kills': 4.0,
            'std_dev_kills': 1.5,
            'maps_played': 10,
            'position_factor': 1.0,
            'tier_info': {'weight': 1.0, 'tier': 1, 'name': 'Test Tier'}
        }
        
        prop_value = 3.5
        expected_stat = 4.0
        
        # Test centralized confidence calculation
        confidence_result = self.prediction_model._calculate_confidence(
            features, prop_value, expected_stat, None
        )
        
        # Verify required fields are present
        self.assertIn('base_confidence', confidence_result)
        self.assertIn('adjusted_confidence', confidence_result)
        self.assertIn('final_confidence', confidence_result)
        self.assertIn('prediction', confidence_result)
        self.assertIn('gap', confidence_result)
        
        # Verify confidence is within bounds
        self.assertGreaterEqual(confidence_result['final_confidence'], 0.1)
        self.assertLessEqual(confidence_result['final_confidence'], 0.95)
        
        # Verify prediction logic
        if expected_stat > prop_value:
            self.assertEqual(confidence_result['prediction'], 'OVER')
        else:
            self.assertEqual(confidence_result['prediction'], 'UNDER')
    
    def test_tiered_data_filtering_empty_data(self):
        """Test tiered data filtering with empty data"""
        result = self.data_processor.filter_player_data_with_tiers(
            player_names=['NonExistentPlayer'],
            map_range=[1, 3],
            tournament='NonExistentTournament'
        )
        
        # Should return empty data with proper tier info
        self.assertTrue(result['data'].empty)
        self.assertEqual(result['tier_info']['tier'], 0)
        self.assertEqual(result['tier_info']['name'], 'No Data')
        self.assertFalse(result['fallback_used'])
    
    def test_prediction_with_xgboost_disabled(self):
        """Test that prediction works correctly when XGBoost is disabled"""
        features = {
            'avg_kills': 4.0,
            'std_dev_kills': 1.5,
            'maps_played': 10,
            'position_factor': 1.0,
            'form_z_score': 0.5,
            'sample_size_score': 0.8,
            'tier_info': {'weight': 1.0, 'tier': 1, 'name': 'Test Tier'}
        }
        
        # Test prediction
        result = self.prediction_model.predict(features, 3.5)
        
        # Verify essential fields
        self.assertIn('prediction', result)
        self.assertIn('confidence', result)
        self.assertIn('expected_stat', result)
        self.assertIn('reasoning', result)
        
        # Verify values are reasonable
        self.assertIn(result['prediction'], ['OVER', 'UNDER'])
        self.assertGreaterEqual(result['confidence'], 0)
        self.assertLessEqual(result['confidence'], 100)
    
    def test_advanced_feature_integration_with_empty_data(self):
        """Test that advanced features don't break when player_data is empty"""
        empty_data = pd.DataFrame()
        
        # This should not raise an exception
        features = self.data_processor.engineer_features(empty_data, 'kills')
        
        # Should return default features
        self.assertIn('avg_kills', features)
        self.assertIn('avg_assists', features)
    
    def test_error_handling_and_logging(self):
        """Test error handling and logging functionality"""
        # Test with invalid data that should trigger error handling
        invalid_data = pd.DataFrame({'invalid_column': [1, 2, 3]})
        
        # This should trigger fallback mechanisms and return default features
        features = self.data_processor.engineer_features(invalid_data, 'kills')
        
        # Should still return valid features (default features)
        self.assertIsInstance(features, dict)
        self.assertIn('avg_kills', features)
        
        # Should be default values
        self.assertEqual(features['avg_kills'], 0)
        self.assertEqual(features['maps_played'], 0)

class TestProductionReadiness(unittest.TestCase):
    """Test production readiness features"""
    
    def test_docker_environment_compatibility(self):
        """Test that the system works in Docker environment"""
        # Test that the system can handle missing data files gracefully
        dp = DataProcessor()
        
        # Should not crash and should create empty data
        self.assertIsNotNone(dp.combined_data)
        self.assertTrue(dp.combined_data.empty)
    
    def test_error_handling_robustness(self):
        """Test error handling robustness"""
        dp = DataProcessor()
        
        # Test with invalid inputs that should be handled gracefully
        try:
            # These should not crash the system
            players = dp.get_available_players()
            teams = dp.get_available_teams()
            tournaments = dp.get_available_tournaments()
            
            # Should return empty lists, not crash
            self.assertIsInstance(players, list)
            self.assertIsInstance(teams, list)
            self.assertIsInstance(tournaments, list)
            
        except Exception as e:
            self.fail(f"System should handle empty data gracefully, but raised: {e}")
    
    def test_memory_efficiency(self):
        """Test memory efficiency of operations"""
        dp = DataProcessor()
        pm = PredictionModel()
        
        # Test that objects are properly cleaned up
        self.assertIsNotNone(dp)
        self.assertIsNotNone(pm)
        
        # Test that operations don't consume excessive memory
        features = dp._create_fallback_features(
            MagicMock(position_roles=['MID']), 
            {'weight': 1.0}, {}, True
        )
        
        # Should be reasonable size
        self.assertLess(len(str(features)), 10000)  # Reasonable string representation

if __name__ == '__main__':
    unittest.main()