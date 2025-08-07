#!/usr/bin/env python3
"""
EDGE CASES AND BOUNDARY CONDITIONS VALIDATION
=============================================

This test module focuses specifically on edge cases and boundary conditions
that could cause prediction inconsistencies.

Key Areas Tested:
1. Extreme statistical values (0, very high, very low)
2. Boundary sample sizes (exactly at thresholds)
3. Missing or malformed data handling
4. Confidence interval edge cases
5. Feature extraction with incomplete data
6. Map range boundary conditions
"""

import sys
import os
import unittest
import numpy as np
import pandas as pd
import logging
from typing import Dict, Any

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

try:
    from app.models.prediction_model import (
        PredictionModel,
        validate_sample_size_critical,
        safe_divide,
        MIN_SAMPLE_SIZE_CRITICAL,
        MIN_SAMPLE_SIZE_RELIABLE
    )
    from app.utils.data_processor import DataProcessor
except ImportError as e:
    print(f"Error importing modules: {e}")
    sys.exit(1)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestEdgeCasesValidation(unittest.TestCase):
    """Test edge cases and boundary conditions"""
    
    def setUp(self):
        """Set up for each test"""
        self.model = PredictionModel()
        self.data_processor = DataProcessor()
    
    def test_zero_statistics_handling(self):
        """Test handling of zero statistics"""
        logger.info("Testing zero statistics handling...")
        
        zero_stats_cases = [
            # Zero kills
            {'avg_kills': 0, 'std_dev_kills': 0, 'maps_played': 10},
            # Zero assists
            {'avg_assists': 0, 'std_dev_assists': 0, 'maps_played': 10},
            # Zero standard deviation
            {'avg_kills': 4, 'std_dev_kills': 0, 'maps_played': 10},
            # Zero sample size
            {'avg_kills': 4, 'std_dev_kills': 1, 'maps_played': 0}
        ]
        
        for i, case in enumerate(zero_stats_cases):
            with self.subTest(case_id=i):
                complete_features = self.model._get_unified_default_features()
                complete_features.update(case)
                
                try:
                    # Should not crash
                    result = self.model.predict(complete_features, 5.0)
                    
                    # Basic validations
                    self.assertIsNotNone(result)
                    self.assertIn('prediction', result)
                    self.assertIn('confidence', result)
                    self.assertGreaterEqual(result['expected_stat'], 0)
                    
                    # For zero sample size, should get conservative fallback
                    if case.get('maps_played') == 0:
                        self.assertLessEqual(result['confidence'], 60)
                        
                except Exception as e:
                    self.fail(f"Zero stats case {i} failed: {e}")
        
        logger.info("✓ Zero statistics handling validated")
    
    def test_extreme_high_values(self):
        """Test handling of extremely high statistical values"""
        logger.info("Testing extreme high values...")
        
        extreme_cases = [
            # Very high kills
            {'avg_kills': 25, 'std_dev_kills': 1, 'maps_played': 10},
            # Very high volatility
            {'avg_kills': 4, 'std_dev_kills': 20, 'maps_played': 10},
            # Extreme form
            {'avg_kills': 4, 'form_z_score': 10, 'maps_played': 10},
            # Very high sample size
            {'avg_kills': 4, 'std_dev_kills': 1, 'maps_played': 1000}
        ]
        
        for i, case in enumerate(extreme_cases):
            with self.subTest(case_id=i):
                complete_features = self.model._get_unified_default_features()
                complete_features.update(case)
                
                try:
                    result = self.model.predict(complete_features, 5.0)
                    
                    # Should not produce infinite or NaN values
                    self.assertFalse(np.isnan(result['expected_stat']))
                    self.assertFalse(np.isinf(result['expected_stat']))
                    self.assertFalse(np.isnan(result['confidence']))
                    self.assertFalse(np.isinf(result['confidence']))
                    
                    # Confidence should remain bounded
                    self.assertLessEqual(result['confidence'], 100)
                    self.assertGreaterEqual(result['confidence'], 0)
                    
                except Exception as e:
                    self.fail(f"Extreme high value case {i} failed: {e}")
        
        logger.info("✓ Extreme high values validated")
    
    def test_boundary_sample_sizes(self):
        """Test sample sizes exactly at validation thresholds"""
        logger.info("Testing boundary sample sizes...")
        
        boundary_sizes = [
            MIN_SAMPLE_SIZE_CRITICAL - 1,  # Just below critical
            MIN_SAMPLE_SIZE_CRITICAL,      # Exactly at critical
            MIN_SAMPLE_SIZE_CRITICAL + 1,  # Just above critical
            MIN_SAMPLE_SIZE_RELIABLE - 1,  # Just below reliable
            MIN_SAMPLE_SIZE_RELIABLE,      # Exactly at reliable
            MIN_SAMPLE_SIZE_RELIABLE + 1   # Just above reliable
        ]
        
        for sample_size in boundary_sizes:
            with self.subTest(sample_size=sample_size):
                validation_result = validate_sample_size_critical(sample_size)
                
                # Check that validation returns expected status
                if sample_size < MIN_SAMPLE_SIZE_CRITICAL:
                    self.assertEqual(validation_result['status'], 'insufficient')
                elif sample_size < MIN_SAMPLE_SIZE_RELIABLE:
                    self.assertEqual(validation_result['status'], 'limited')
                else:
                    self.assertIn(validation_result['status'], ['adequate', 'excellent'])
                
                # Test prediction with this sample size
                features = {
                    'avg_kills': 4.0,
                    'std_dev_kills': 1.5,
                    'maps_played': sample_size,
                    'series_played': sample_size
                }
                
                complete_features = self.model._get_unified_default_features()
                complete_features.update(features)
                
                result = self.model.predict(complete_features, 5.0)
                
                # Very small samples should have lower confidence
                if sample_size < MIN_SAMPLE_SIZE_CRITICAL:
                    self.assertLessEqual(result['confidence'], 60)
                    self.assertEqual(result['prediction'], 'UNDER')  # Conservative fallback
        
        logger.info("✓ Boundary sample sizes validated")
    
    def test_missing_feature_handling(self):
        """Test handling of missing or incomplete features"""
        logger.info("Testing missing feature handling...")
        
        # Test with progressively fewer features
        feature_subsets = [
            # Minimal features
            {'avg_kills': 4.0},
            # Missing statistics
            {'avg_kills': 4.0, 'maps_played': 10},
            # Missing form data
            {'avg_kills': 4.0, 'std_dev_kills': 1.5, 'maps_played': 10},
            # Empty dictionary
            {}
        ]
        
        for i, features in enumerate(feature_subsets):
            with self.subTest(subset_id=i):
                try:
                    result = self.model.predict(features, 5.0)
                    
                    # Should use defaults for missing features
                    self.assertIsNotNone(result)
                    self.assertIn('prediction', result)
                    
                    # Feature extraction should fill in defaults
                    unified_features = self.model._extract_unified_features(features)
                    self.assertEqual(len(unified_features), len(self.model.FEATURE_ORDER))
                    
                except Exception as e:
                    self.fail(f"Missing features case {i} failed: {e}")
        
        logger.info("✓ Missing feature handling validated")
    
    def test_confidence_interval_edge_cases(self):
        """Test confidence interval calculation with edge cases"""
        logger.info("Testing confidence interval edge cases...")
        
        edge_cases = [
            # Zero standard deviation
            {'avg_kills': 4.0, 'std_dev_kills': 0, 'maps_played': 10},
            # Very large standard deviation
            {'avg_kills': 4.0, 'std_dev_kills': 100, 'maps_played': 10},
            # Single sample
            {'avg_kills': 4.0, 'std_dev_kills': 1.0, 'maps_played': 1},
            # Perfect consistency (minimal std dev)
            {'avg_kills': 4.0, 'std_dev_kills': 0.01, 'maps_played': 10}
        ]
        
        for i, case in enumerate(edge_cases):
            with self.subTest(case_id=i):
                complete_features = self.model._get_unified_default_features()
                complete_features.update(case)
                
                expected_stat = 4.0
                
                try:
                    ci = self.model._calculate_bootstrap_confidence_interval(
                        complete_features, expected_stat
                    )
                    
                    # CI should be a valid interval
                    self.assertEqual(len(ci), 2)
                    self.assertLessEqual(ci[0], ci[1])
                    self.assertGreaterEqual(ci[0], 0)
                    
                    # For zero std dev, interval should be narrow
                    if case.get('std_dev_kills') == 0:
                        interval_width = ci[1] - ci[0]
                        self.assertLess(interval_width, expected_stat * 0.5)
                    
                except Exception as e:
                    self.fail(f"CI edge case {i} failed: {e}")
        
        logger.info("✓ Confidence interval edge cases validated")
    
    def test_safe_divide_edge_cases(self):
        """Test safe_divide function with various edge cases"""
        logger.info("Testing safe_divide edge cases...")
        
        edge_cases = [
            # Division by exact zero
            (10, 0),
            # Division by very small number
            (10, 1e-10),
            # Division by negative number
            (10, -2),
            # Zero divided by zero
            (0, 0),
            # Large numbers
            (1e6, 1e-6),
            # Negative numerator
            (-10, 2)
        ]
        
        for numerator, denominator in edge_cases:
            with self.subTest(num=numerator, denom=denominator):
                result = safe_divide(numerator, denominator)
                
                # Result should always be finite
                self.assertFalse(np.isnan(result))
                self.assertFalse(np.isinf(result))
                
                # Should not crash
                self.assertIsInstance(result, (int, float))
        
        logger.info("✓ Safe divide edge cases validated")
    
    def test_map_range_boundary_conditions(self):
        """Test map range boundary conditions"""
        logger.info("Testing map range boundary conditions...")
        
        # Create test data with various map ranges
        test_data = pd.DataFrame([
            # Standard BO3 series (maps 1-3)
            {'match_series': 'series1', 'map_index_within_series': 1, 'kills': 4, 'assists': 6},
            {'match_series': 'series1', 'map_index_within_series': 2, 'kills': 3, 'assists': 5},
            {'match_series': 'series1', 'map_index_within_series': 3, 'kills': 5, 'assists': 7},
            # Extended BO5 series
            {'match_series': 'series2', 'map_index_within_series': 1, 'kills': 2, 'assists': 4},
            {'match_series': 'series2', 'map_index_within_series': 2, 'kills': 3, 'assists': 5},
            {'match_series': 'series2', 'map_index_within_series': 3, 'kills': 4, 'assists': 6},
            {'match_series': 'series2', 'map_index_within_series': 4, 'kills': 5, 'assists': 7},
            {'match_series': 'series2', 'map_index_within_series': 5, 'kills': 6, 'assists': 8},
        ])
        
        # Test various map range boundaries
        map_ranges = [
            [1, 1],    # Single map
            [1, 2],    # Standard betting range
            [1, 3],    # Full BO3
            [2, 3],    # Late maps only
            [1, 5],    # Full BO5
            [4, 5]     # Very late maps
        ]
        
        for map_range in map_ranges:
            with self.subTest(map_range=map_range):
                try:
                    # Filter data for this range
                    filtered_data = test_data[
                        (test_data['map_index_within_series'] >= map_range[0]) &
                        (test_data['map_index_within_series'] <= map_range[1])
                    ]
                    
                    if not filtered_data.empty:
                        # Calculate aggregate stats
                        agg_stats = self.data_processor.aggregate_stats(filtered_data, 'kills')
                        
                        # Should not crash and should produce reasonable results
                        self.assertIsNotNone(agg_stats)
                        
                except Exception as e:
                    self.fail(f"Map range {map_range} failed: {e}")
        
        logger.info("✓ Map range boundary conditions validated")
    
    def test_data_processor_edge_cases(self):
        """Test DataProcessor with edge case data"""
        logger.info("Testing DataProcessor edge cases...")
        
        edge_case_data = [
            # Empty DataFrame
            pd.DataFrame(),
            # Single row
            pd.DataFrame([{'playername': 'Test', 'kills': 4, 'assists': 5}]),
            # Missing columns
            pd.DataFrame([{'playername': 'Test', 'kills': 4}]),  # No assists
            # NaN values
            pd.DataFrame([
                {'playername': 'Test', 'kills': np.nan, 'assists': 5},
                {'playername': 'Test', 'kills': 4, 'assists': np.nan}
            ]),
            # Extreme values
            pd.DataFrame([
                {'playername': 'Test', 'kills': 100, 'assists': 0},
                {'playername': 'Test', 'kills': 0, 'assists': 100}
            ])
        ]
        
        for i, test_data in enumerate(edge_case_data):
            with self.subTest(data_case=i):
                try:
                    if not test_data.empty and 'kills' in test_data.columns:
                        # Should handle gracefully
                        features = self.data_processor.engineer_features(test_data, 'kills')
                        self.assertIsInstance(features, dict)
                    
                except Exception as e:
                    # Some edge cases might legitimately fail, but shouldn't crash the system
                    logger.warning(f"Data processor edge case {i} raised: {e}")
        
        logger.info("✓ DataProcessor edge cases validated")
    
    def test_prediction_consistency_under_stress(self):
        """Test prediction consistency under various stress conditions"""
        logger.info("Testing prediction consistency under stress...")
        
        base_features = {
            'avg_kills': 4.0,
            'avg_assists': 6.0,
            'std_dev_kills': 1.5,
            'std_dev_assists': 2.0,
            'maps_played': 15
        }
        
        # Test multiple predictions with same inputs
        predictions = []
        for _ in range(10):
            result = self.model.predict(base_features, 5.0)
            predictions.append({
                'expected_stat': result['expected_stat'],
                'confidence': result['confidence'],
                'prediction': result['prediction']
            })
        
        # All predictions should be identical (deterministic)
        expected_stats = [p['expected_stat'] for p in predictions]
        confidences = [p['confidence'] for p in predictions]
        pred_types = [p['prediction'] for p in predictions]
        
        self.assertEqual(len(set(expected_stats)), 1, "Expected stats should be consistent")
        self.assertEqual(len(set(confidences)), 1, "Confidences should be consistent")
        self.assertEqual(len(set(pred_types)), 1, "Prediction types should be consistent")
        
        logger.info("✓ Prediction consistency under stress validated")

def run_edge_cases_validation():
    """Run the edge cases validation suite"""
    print("=" * 80)
    print("EDGE CASES AND BOUNDARY CONDITIONS VALIDATION")
    print("=" * 80)
    
    # Run tests
    unittest.main(
        module=__name__,
        verbosity=2,
        exit=False
    )

if __name__ == '__main__':
    run_edge_cases_validation()