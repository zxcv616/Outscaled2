import unittest
import numpy as np
from unittest.mock import patch, MagicMock
import sys
import os

# Add the app directory to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.models.prediction_model import PredictionModel


class TestPredictionModel(unittest.TestCase):
    """Test cases for PredictionModel class"""

    def setUp(self):
        """Set up test fixtures before each test method"""
        self.model = PredictionModel()

    def test_model_initialization(self):
        """Test model initialization"""
        # Verify model is initialized
        self.assertIsNotNone(self.model)
        self.assertIsNotNone(self.model.model)

    def test_prepare_features(self):
        """Test feature preparation"""
        # Create test features
        features = {
            'avg_kills': 4.0,
            'maps_played': 10,
            'form_z_score': 0.5,
            'position_factor': 1.0,
            'std_dev_kills': 2.0,
            'longterm_kills_avg': 3.5,
            'form_deviation_ratio': 1.2,
            'sample_size_score': 0.8,
            'avg_deaths': 2.5,
            'avg_damage': 15000,
            'avg_vision': 25,
            'avg_cs': 200
        }
        
        # Test feature preparation
        X = self.model._prepare_features(features)
        
        # Should return numpy array
        self.assertIsInstance(X, np.ndarray)
        self.assertEqual(X.shape[0], 1)  # Single sample

    def test_calculate_expected_stat(self):
        """Test expected stat calculation"""
        features = {
            'avg_kills': 4.0,
            'form_z_score': 0.5,
            'position_factor': 1.0,
            'maps_played': 10
        }
        
        expected_stat = self.model._calculate_expected_stat(features)
        
        # Should return a reasonable expected stat
        self.assertIsInstance(expected_stat, float)
        self.assertGreater(expected_stat, 0)

    def test_calculate_confidence_interval(self):
        """Test confidence interval calculation"""
        features = {
            'std_dev_kills': 2.0,
            'maps_played': 10
        }
        expected_stat = 4.0
        
        interval = self.model._calculate_confidence_interval(features, expected_stat)
        
        # Should return a list with lower and upper bounds
        self.assertIsInstance(interval, list)
        self.assertEqual(len(interval), 2)
        self.assertLess(interval[0], interval[1])  # Lower bound < upper bound

    def test_generate_reasoning(self):
        """Test reasoning generation"""
        features = {
            'avg_kills': 4.0,
            'maps_played': 10,
            'form_z_score': 0.5,
            'position_factor': 1.0,
            'std_dev_kills': 2.0,
            'longterm_kills_avg': 3.5,
            'form_deviation_ratio': 1.2,
            'sample_size_score': 0.8
        }
        
        prop_value = 5.0
        prediction = 'OVER'
        confidence = 70.0  # Percentage value
        
        expected_stat = 5.5
        reasoning = self.model._generate_reasoning(features, prediction, confidence, prop_value, expected_stat)
        
        # Should return a string with reasoning
        self.assertIsInstance(reasoning, str)
        self.assertGreater(len(reasoning), 0)

    def test_prepare_player_stats(self):
        """Test player stats preparation"""
        features = {
            'avg_kills': 4.0,
            'avg_assists': 6.0,
            'form_z_score': 0.5,
            'maps_played': 10,
            'avg_deaths': 2.5,
            'avg_damage': 15000,
            'avg_vision': 25,
            'avg_cs': 200,
            'position_factor': 1.0
        }
        
        stats = self.model._prepare_player_stats(features)
        
        # Should return a dictionary with player stats
        self.assertIsInstance(stats, dict)
        self.assertIn('avg_kills', stats)
        self.assertIn('avg_assists', stats)
        self.assertIn('form_z_score', stats)
        self.assertIn('maps_played', stats)
        self.assertIn('avg_deaths', stats)
        self.assertIn('avg_damage', stats)
        self.assertIn('avg_vision', stats)
        self.assertIn('avg_cs', stats)
        self.assertIn('position_factor', stats)

    def test_predict_kills(self):
        """Test prediction for kills prop"""
        features = {
            'avg_kills': 4.0,
            'maps_played': 10,
            'form_z_score': 0.5,
            'position_factor': 1.0,
            'std_dev_kills': 2.0,
            'longterm_kills_avg': 3.5,
            'form_deviation_ratio': 1.2,
            'sample_size_score': 0.8,
            'avg_deaths': 2.5,
            'avg_damage': 15000,
            'avg_vision': 25,
            'avg_cs': 200
        }
        
        prop_value = 5.0
        
        result = self.model.predict(features, prop_value)
        
        # Should return a dictionary with prediction results
        self.assertIsInstance(result, dict)
        self.assertIn('prediction', result)
        self.assertIn('confidence', result)
        self.assertIn('expected_stat', result)
        self.assertIn('confidence_interval', result)
        self.assertIn('reasoning', result)
        self.assertIn('player_stats', result)
        self.assertIn('data_years', result)
        
        # Verify prediction is either OVER or UNDER
        self.assertIn(result['prediction'], ['OVER', 'UNDER'])
        
        # Verify confidence is between 0 and 100
        self.assertGreaterEqual(result['confidence'], 0)
        self.assertLessEqual(result['confidence'], 100)

    def test_predict_assists(self):
        """Test prediction for assists prop"""
        features = {
            'avg_assists': 6.0,
            'maps_played': 10,
            'form_z_score': 0.5,
            'position_factor': 1.0,
            'std_dev_assists': 2.0,
            'longterm_assists_avg': 5.5,
            'form_deviation_ratio': 1.2,
            'sample_size_score': 0.8,
            'avg_deaths': 2.5,
            'avg_damage': 15000,
            'avg_vision': 25,
            'avg_cs': 200
        }
        
        prop_value = 7.0
        
        result = self.model.predict(features, prop_value)
        
        # Should return a dictionary with prediction results
        self.assertIsInstance(result, dict)
        self.assertIn('prediction', result)
        self.assertIn('confidence', result)
        self.assertIn('expected_stat', result)
        self.assertIn('confidence_interval', result)
        self.assertIn('reasoning', result)
        self.assertIn('player_stats', result)
        self.assertIn('data_years', result)

    def test_edge_cases(self):
        """Test edge cases and error handling"""
        # Test with minimal features
        minimal_features = {
            'avg_kills': 0.0,
            'maps_played': 1,
            'form_z_score': 0.0,
            'position_factor': 1.0,
            'std_dev_kills': 0.0,
            'longterm_kills_avg': 0.0,
            'form_deviation_ratio': 1.0,
            'sample_size_score': 0.1,
            'avg_deaths': 0.0,
            'avg_damage': 0,
            'avg_vision': 0,
            'avg_cs': 0
        }
        
        prop_value = 1.0
        
        result = self.model.predict(minimal_features, prop_value)
        
        # Should still return valid prediction
        self.assertIsInstance(result, dict)
        self.assertIn('prediction', result)
        self.assertIn('confidence', result)

    def test_high_confidence_scenario(self):
        """Test high confidence prediction scenario"""
        features = {
            'avg_kills': 5.0,
            'maps_played': 50,  # High sample size
            'form_z_score': 1.5,  # Strong form
            'position_factor': 1.0,
            'std_dev_kills': 1.0,  # Low variance
            'longterm_kills_avg': 4.8,
            'form_deviation_ratio': 1.1,
            'sample_size_score': 1.0,
            'avg_deaths': 2.0,
            'avg_damage': 18000,
            'avg_vision': 30,
            'avg_cs': 250
        }
        
        prop_value = 4.0  # Below average
        
        result = self.model.predict(features, prop_value)
        
        # Should have reasonable confidence
        self.assertGreater(result['confidence'], 0)
        self.assertLessEqual(result['confidence'], 100)

    def test_low_confidence_scenario(self):
        """Test low confidence prediction scenario"""
        features = {
            'avg_kills': 3.0,
            'maps_played': 3,  # Low sample size
            'form_z_score': -0.5,  # Poor form
            'position_factor': 0.8,
            'std_dev_kills': 3.0,  # High variance
            'longterm_kills_avg': 2.5,
            'form_deviation_ratio': 0.8,
            'sample_size_score': 0.3,
            'avg_deaths': 4.0,
            'avg_damage': 12000,
            'avg_vision': 20,
            'avg_cs': 150
        }
        
        prop_value = 3.5  # Close to average
        
        result = self.model.predict(features, prop_value)
        
        # Should have lower confidence due to uncertainty
        self.assertGreater(result['confidence'], 0)
        self.assertLessEqual(result['confidence'], 100)

    def test_combo_prediction(self):
        """Test combo prediction scenario"""
        features = {
            'avg_kills': 4.0,
            'maps_played': 10,
            'form_z_score': 0.5,
            'position_factor': 1.0,
            'std_dev_kills': 2.0,
            'longterm_kills_avg': 3.5,
            'form_deviation_ratio': 1.2,
            'sample_size_score': 0.8,
            'avg_deaths': 2.5,
            'avg_damage': 15000,
            'avg_vision': 25,
            'avg_cs': 200,
            'combo_avg_kills': 8.0,  # Combo feature
            'combo_std_kills': 3.0,
            'combo_maps_played': 5,
            'combo_confidence_penalty': 0.9
        }
        
        prop_value = 10.0
        
        result = self.model.predict(features, prop_value)
        
        # Should handle combo features
        self.assertIsInstance(result, dict)
        self.assertIn('prediction', result)
        self.assertIn('confidence', result)

    def test_model_consistency(self):
        """Test that model predictions are consistent for same inputs"""
        features = {
            'avg_kills': 4.0,
            'maps_played': 10,
            'form_z_score': 0.5,
            'position_factor': 1.0,
            'std_dev_kills': 2.0,
            'longterm_kills_avg': 3.5,
            'form_deviation_ratio': 1.2,
            'sample_size_score': 0.8,
            'avg_deaths': 2.5,
            'avg_damage': 15000,
            'avg_vision': 25,
            'avg_cs': 200
        }
        
        prop_value = 5.0
        
        # Run prediction twice
        result1 = self.model.predict(features, prop_value)
        result2 = self.model.predict(features, prop_value)
        
        # Should be consistent (same prediction and confidence)
        self.assertEqual(result1['prediction'], result2['prediction'])
        self.assertEqual(result1['confidence'], result2['confidence'])


if __name__ == '__main__':
    unittest.main() 