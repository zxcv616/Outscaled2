#!/usr/bin/env python3
"""
PERFORMANCE AND CONSISTENCY VALIDATION
======================================

This test module validates performance metrics and consistency across 
different scenarios to ensure the prediction system behaves reliably.

Focus Areas:
1. Response time validation
2. Memory usage patterns
3. Consistency across multiple runs
4. Performance degradation detection
5. Resource utilization monitoring
"""

import sys
import os
import unittest
import time
import tracemalloc
import numpy as np
import pandas as pd
import logging
from typing import List, Dict, Any
import gc

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

try:
    from app.models.prediction_model import PredictionModel
    from app.utils.data_processor import DataProcessor
except ImportError as e:
    print(f"Error importing modules: {e}")
    sys.exit(1)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestPerformanceValidation(unittest.TestCase):
    """Test performance and consistency characteristics"""
    
    @classmethod
    def setUpClass(cls):
        """Set up performance testing environment"""
        cls.model = PredictionModel()
        cls.data_processor = DataProcessor()
        
        # Standard test features for consistency testing
        cls.standard_features = {
            'avg_kills': 4.0,
            'avg_assists': 6.0,
            'std_dev_kills': 1.5,
            'std_dev_assists': 2.0,
            'maps_played': 15,
            'longterm_kills_avg': 4.2,
            'longterm_assists_avg': 5.8,
            'form_z_score': 0.3,
            'form_deviation_ratio': 0.375,
            'position_factor': 1.0,
            'sample_size_score': 0.75
        }
    
    def test_prediction_response_time(self):
        """Test that predictions complete within acceptable time"""
        logger.info("Testing prediction response time...")
        
        response_times = []
        
        for i in range(20):  # Test 20 predictions
            start_time = time.time()
            
            result = self.model.predict(self.standard_features, 5.0 + i * 0.1)
            
            end_time = time.time()
            response_time = end_time - start_time
            response_times.append(response_time)
            
            # Each prediction should complete quickly
            self.assertLess(response_time, 2.0, f"Prediction {i} took {response_time:.3f}s")
        
        # Calculate statistics
        avg_time = np.mean(response_times)
        max_time = np.max(response_times)
        std_time = np.std(response_times)
        
        logger.info(f"Response time stats - Avg: {avg_time:.3f}s, Max: {max_time:.3f}s, Std: {std_time:.3f}s")
        
        # Performance requirements
        self.assertLess(avg_time, 0.5, f"Average response time {avg_time:.3f}s too high")
        self.assertLess(max_time, 1.0, f"Maximum response time {max_time:.3f}s too high")
        
        logger.info("✓ Prediction response time validated")
    
    def test_memory_usage_patterns(self):
        """Test memory usage patterns during prediction"""
        logger.info("Testing memory usage patterns...")
        
        # Start memory tracking
        tracemalloc.start()
        
        initial_snapshot = tracemalloc.take_snapshot()
        
        # Run multiple predictions
        for i in range(100):
            self.model.predict(self.standard_features, 5.0 + i * 0.01)
        
        # Take memory snapshot
        final_snapshot = tracemalloc.take_snapshot()
        
        # Compare memory usage
        top_stats = final_snapshot.compare_to(initial_snapshot, 'lineno')
        
        # Calculate total memory growth
        total_growth = sum(stat.size_diff for stat in top_stats if stat.size_diff > 0)
        
        logger.info(f"Memory growth after 100 predictions: {total_growth / 1024:.2f} KB")
        
        # Should not have significant memory leaks
        self.assertLess(total_growth, 10 * 1024 * 1024, "Memory growth too large (>10MB)")
        
        # Clean up
        tracemalloc.stop()
        gc.collect()
        
        logger.info("✓ Memory usage patterns validated")
    
    def test_prediction_consistency_multiple_runs(self):
        """Test that identical inputs produce identical outputs"""
        logger.info("Testing prediction consistency across multiple runs...")
        
        test_scenarios = [
            (self.standard_features, 5.0),
            (self.standard_features, 7.5),
            (self.standard_features, 3.0),
            # Different feature set
            ({**self.standard_features, 'avg_kills': 6.0}, 5.0),
        ]
        
        for scenario_idx, (features, prop_value) in enumerate(test_scenarios):
            with self.subTest(scenario=scenario_idx):
                results = []
                
                # Run same prediction multiple times
                for run in range(10):
                    result = self.model.predict(features, prop_value)
                    results.append({
                        'prediction': result['prediction'],
                        'confidence': result['confidence'],
                        'expected_stat': result['expected_stat'],
                        'run': run
                    })
                
                # All results should be identical
                predictions = [r['prediction'] for r in results]
                confidences = [r['confidence'] for r in results]
                expected_stats = [r['expected_stat'] for r in results]
                
                self.assertEqual(len(set(predictions)), 1, 
                               f"Predictions inconsistent: {set(predictions)}")
                self.assertEqual(len(set(confidences)), 1,
                               f"Confidences inconsistent: {set(confidences)}")
                self.assertEqual(len(set(expected_stats)), 1,
                               f"Expected stats inconsistent: {set(expected_stats)}")
        
        logger.info("✓ Prediction consistency validated")
    
    def test_feature_processing_performance(self):
        """Test feature processing performance"""
        logger.info("Testing feature processing performance...")
        
        # Test unified feature extraction
        processing_times = []
        
        for i in range(100):
            test_features = {
                **self.standard_features,
                'avg_kills': 4.0 + np.random.normal(0, 0.5),
                'avg_assists': 6.0 + np.random.normal(0, 0.5)
            }
            
            start_time = time.time()
            
            unified_features = self.model._extract_unified_features(test_features)
            
            end_time = time.time()
            processing_times.append(end_time - start_time)
            
            # Verify extraction completed
            self.assertEqual(len(unified_features), len(self.model.FEATURE_ORDER))
        
        avg_processing_time = np.mean(processing_times)
        max_processing_time = np.max(processing_times)
        
        logger.info(f"Feature processing - Avg: {avg_processing_time:.4f}s, Max: {max_processing_time:.4f}s")
        
        # Performance requirements
        self.assertLess(avg_processing_time, 0.01, "Feature processing too slow")
        self.assertLess(max_processing_time, 0.05, "Max feature processing time too slow")
        
        logger.info("✓ Feature processing performance validated")
    
    def test_confidence_interval_performance(self):
        """Test confidence interval calculation performance"""
        logger.info("Testing confidence interval calculation performance...")
        
        test_features = {
            **self.standard_features,
            'std_dev_kills': 1.5,
            'series_played': 15
        }
        
        # Test bootstrap CI performance
        bootstrap_times = []
        
        for i in range(20):  # Fewer iterations due to computational cost
            start_time = time.time()
            
            ci = self.model._calculate_bootstrap_confidence_interval(
                test_features, 4.0, n_bootstrap=100  # Reduced bootstrap samples for speed
            )
            
            end_time = time.time()
            bootstrap_times.append(end_time - start_time)
            
            # Verify CI is valid
            self.assertEqual(len(ci), 2)
            self.assertLess(ci[0], ci[1])
        
        avg_bootstrap_time = np.mean(bootstrap_times)
        max_bootstrap_time = np.max(bootstrap_times)
        
        logger.info(f"Bootstrap CI - Avg: {avg_bootstrap_time:.3f}s, Max: {max_bootstrap_time:.3f}s")
        
        # Performance requirements (bootstrap is computationally expensive)
        self.assertLess(avg_bootstrap_time, 0.5, "Bootstrap CI too slow")
        self.assertLess(max_bootstrap_time, 1.0, "Max bootstrap CI time too slow")
        
        logger.info("✓ Confidence interval performance validated")
    
    def test_prediction_curve_performance(self):
        """Test prediction curve generation performance"""
        logger.info("Testing prediction curve generation performance...")
        
        curve_times = []
        
        for i in range(10):
            start_time = time.time()
            
            curve = self.model.generate_prediction_curve(
                self.standard_features, 
                input_prop=5.0 + i * 0.5,
                step=0.25,
                range_size=5
            )
            
            end_time = time.time()
            curve_times.append(end_time - start_time)
            
            # Verify curve structure
            self.assertGreater(len(curve), 5)
            
            for point in curve:
                self.assertIn('prop_value', point)
                self.assertIn('prediction', point)
                self.assertIn('confidence', point)
        
        avg_curve_time = np.mean(curve_times)
        max_curve_time = np.max(curve_times)
        
        logger.info(f"Prediction curve - Avg: {avg_curve_time:.3f}s, Max: {max_curve_time:.3f}s")
        
        # Performance requirements
        self.assertLess(avg_curve_time, 0.2, "Curve generation too slow")
        self.assertLess(max_curve_time, 0.5, "Max curve generation time too slow")
        
        logger.info("✓ Prediction curve performance validated")
    
    def test_data_processor_performance(self):
        """Test DataProcessor performance with various data sizes"""
        logger.info("Testing DataProcessor performance...")
        
        # Create test data of various sizes
        data_sizes = [10, 50, 100, 500]
        processing_times = {}
        
        for size in data_sizes:
            # Create test data
            test_data = pd.DataFrame({
                'playername': ['TestPlayer'] * size,
                'position': ['mid'] * size,
                'kills': np.random.normal(4, 1.5, size),
                'assists': np.random.normal(6, 2, size),
                'deaths': np.random.normal(2.5, 0.8, size),
                'match_series': [f'series_{i//2}' for i in range(size)],
                'map_index_within_series': [(i % 2) + 1 for i in range(size)]
            })
            
            # Time feature engineering
            start_time = time.time()
            
            features = self.data_processor.engineer_features(test_data, 'kills')
            
            end_time = time.time()
            processing_time = end_time - start_time
            processing_times[size] = processing_time
            
            # Verify features were extracted
            self.assertIsInstance(features, dict)
            self.assertGreater(len(features), 0)
            
            logger.info(f"Data size {size}: {processing_time:.4f}s")
        
        # Check that processing scales reasonably
        max_time = max(processing_times.values())
        self.assertLess(max_time, 0.5, "Data processing too slow for large datasets")
        
        logger.info("✓ DataProcessor performance validated")
    
    def test_concurrent_predictions_safety(self):
        """Test that concurrent predictions don't interfere with each other"""
        logger.info("Testing concurrent predictions safety...")
        
        # Simulate concurrent-like behavior by rapidly switching between different predictions
        results = []
        
        test_scenarios = [
            ({'avg_kills': 3.0}, 4.0),
            ({'avg_kills': 5.0}, 6.0),
            ({'avg_kills': 7.0}, 8.0),
            ({'avg_kills': 2.0}, 3.0)
        ]
        
        # Rapidly alternate between scenarios
        for cycle in range(10):
            cycle_results = []
            
            for scenario_idx, (feature_update, prop_value) in enumerate(test_scenarios):
                features = {**self.standard_features, **feature_update}
                result = self.model.predict(features, prop_value)
                
                cycle_results.append({
                    'scenario': scenario_idx,
                    'cycle': cycle,
                    'expected_stat': result['expected_stat'],
                    'prediction': result['prediction']
                })
            
            results.extend(cycle_results)
        
        # Verify that results for each scenario are consistent across cycles
        for scenario_idx in range(len(test_scenarios)):
            scenario_results = [r for r in results if r['scenario'] == scenario_idx]
            
            expected_stats = [r['expected_stat'] for r in scenario_results]
            predictions = [r['prediction'] for r in scenario_results]
            
            # All results for the same scenario should be identical
            self.assertEqual(len(set(expected_stats)), 1,
                           f"Scenario {scenario_idx} expected stats inconsistent")
            self.assertEqual(len(set(predictions)), 1,
                           f"Scenario {scenario_idx} predictions inconsistent")
        
        logger.info("✓ Concurrent predictions safety validated")
    
    def test_resource_cleanup(self):
        """Test that resources are properly cleaned up"""
        logger.info("Testing resource cleanup...")
        
        # Track objects before and after operations
        initial_objects = len(gc.get_objects())
        
        # Perform operations that might create objects
        for i in range(50):
            # Create temporary model instance
            temp_model = PredictionModel()
            result = temp_model.predict(self.standard_features, 5.0)
            
            # Delete reference
            del temp_model
        
        # Force garbage collection
        gc.collect()
        
        final_objects = len(gc.get_objects())
        object_growth = final_objects - initial_objects
        
        logger.info(f"Object count growth: {object_growth}")
        
        # Should not have excessive object growth
        self.assertLess(object_growth, 1000, "Excessive object creation detected")
        
        logger.info("✓ Resource cleanup validated")
    
    def test_prediction_stability_under_load(self):
        """Test prediction stability under sustained load"""
        logger.info("Testing prediction stability under load...")
        
        # Run sustained predictions
        num_predictions = 200
        results = []
        errors = []
        
        start_time = time.time()
        
        for i in range(num_predictions):
            try:
                # Vary features slightly to simulate real usage
                features = {
                    **self.standard_features,
                    'avg_kills': 4.0 + np.sin(i * 0.1) * 0.5,
                    'form_z_score': np.cos(i * 0.1) * 0.3
                }
                
                result = self.model.predict(features, 5.0 + i * 0.01)
                results.append(result)
                
            except Exception as e:
                errors.append((i, str(e)))
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Performance metrics
        avg_time_per_prediction = total_time / num_predictions
        success_rate = len(results) / num_predictions
        
        logger.info(f"Load test results:")
        logger.info(f"  Total predictions: {num_predictions}")
        logger.info(f"  Successful: {len(results)}")
        logger.info(f"  Errors: {len(errors)}")
        logger.info(f"  Success rate: {success_rate:.3f}")
        logger.info(f"  Avg time per prediction: {avg_time_per_prediction:.4f}s")
        
        # Requirements
        self.assertGreaterEqual(success_rate, 0.99, "Success rate too low under load")
        self.assertLess(avg_time_per_prediction, 0.1, "Average prediction time too high under load")
        self.assertLessEqual(len(errors), 2, f"Too many errors under load: {errors}")
        
        logger.info("✓ Prediction stability under load validated")

def run_performance_validation():
    """Run the performance validation suite"""
    print("=" * 80)
    print("PERFORMANCE AND CONSISTENCY VALIDATION")
    print("=" * 80)
    
    # Run tests with detailed output
    unittest.main(
        module=__name__,
        verbosity=2,
        exit=False
    )

if __name__ == '__main__':
    run_performance_validation()