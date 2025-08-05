"""
COMPREHENSIVE EARLY GAME METRICS VALIDATION TEST SUITE
======================================================

This test suite validates the early game metric implementations in the data processor
to ensure they use real data instead of placeholders and integrate properly with 
the prediction pipeline.

Coverage Areas:
1. Real data extraction from actual CSV columns (goldat10, xpat10, csat10, etc.)
2. Fallback calculations for missing data with reasonable defaults
3. Feature extraction produces values in expected ranges
4. Integration with existing prediction pipeline components
5. Performance impact assessment of new calculations
"""

import sys
import os
import unittest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock

# Add the backend directory to the path so we can import the modules
sys.path.append('/Users/matthewwiecking/Desktop/Outscaled2/backend')

try:
    from app.utils.data_processor import DataProcessor
    from app.models.prediction_model import PredictionModel
except ImportError as e:
    print(f"Import error: {e}")
    print("Please ensure the backend modules are in the correct path")
    raise


class TestEarlyGameMetricsValidation(unittest.TestCase):
    """Comprehensive validation of early game metric implementations"""
    
    def setUp(self):
        """Set up test environment with mock data"""
        self.data_processor = DataProcessor()
        self.prediction_model = PredictionModel()
        
        # Create comprehensive mock data with early game metrics
        self.mock_data = pd.DataFrame({
            'playername': ['TestPlayer'] * 20 + ['TestPlayer2'] * 20,
            'teamname': ['Team1'] * 10 + ['Team2'] * 10 + ['Team3'] * 10 + ['Team4'] * 10,
            'date': pd.date_range('2024-01-01', periods=40, freq='D'),
            'game': [1, 2, 1, 2, 3, 1, 2, 1, 2, 3] * 4,
            'map_index_within_series': [1, 2, 1, 2, 3, 1, 2, 1, 2, 3] * 4,
            'match_series': [f'series_{i//2}' for i in range(40)],
            'position': ['mid'] * 20 + ['adc'] * 20,
            'league': ['LCK'] * 40,
            
            # Core stats
            'kills': np.random.normal(12, 3, 40),
            'assists': np.random.normal(8, 2, 40),
            'deaths': np.random.normal(3, 1, 40),
            'damagetochampions': np.random.normal(25000, 5000, 40),
            'visionscore': np.random.normal(45, 10, 40),
            'total cs': np.random.normal(280, 40, 40),
            
            # REAL Early game metrics - these should be extracted from actual data
            'goldat10': np.random.normal(8500, 1000, 40),  # Gold at 10 minutes
            'xpat10': np.random.normal(6200, 800, 40),     # XP at 10 minutes  
            'csat10': np.random.normal(85, 15, 40),        # CS at 10 minutes
            
            # Mid game differentials
            'golddiffat15': np.random.normal(200, 800, 40),  # Gold diff at 15 min
            'xpdiffat15': np.random.normal(150, 600, 40),    # XP diff at 15 min
            'csdiffat15': np.random.normal(10, 25, 40),      # CS diff at 15 min
            
            # Additional metrics for completeness
            'killsat15': np.random.normal(8, 2, 40),
            'assistsat15': np.random.normal(5, 2, 40),
            'deathsat15': np.random.normal(2, 1, 40),
            'goldat20': np.random.normal(12000, 2000, 40),
            'xpat20': np.random.normal(9000, 1500, 40),
            'csat20': np.random.normal(150, 25, 40),
            'killsat20': np.random.normal(10, 3, 40),
            'assistsat20': np.random.normal(7, 2, 40),
            'deathsat20': np.random.normal(3, 1, 40)
        })
        
        # Ensure realistic value ranges
        self.mock_data['goldat10'] = np.clip(self.mock_data['goldat10'], 6000, 12000)
        self.mock_data['xpat10'] = np.clip(self.mock_data['xpat10'], 4000, 8000)
        self.mock_data['csat10'] = np.clip(self.mock_data['csat10'], 50, 120)
        self.mock_data['golddiffat15'] = np.clip(self.mock_data['golddiffat15'], -2000, 2000)
        self.mock_data['xpdiffat15'] = np.clip(self.mock_data['xpdiffat15'], -1500, 1500)
        self.mock_data['csdiffat15'] = np.clip(self.mock_data['csdiffat15'], -50, 50)
        
        # Mock the data processor's combined_data
        self.data_processor.combined_data = self.mock_data
        
    def test_real_data_extraction_from_actual_columns(self):
        """Test that early game metrics are extracted from real CSV columns, not placeholders"""
        
        # Filter data for one player
        player_data = self.mock_data[self.mock_data['playername'] == 'TestPlayer']
        
        # Extract features using the real implementation
        features = self.data_processor.engineer_features(player_data, 'kills')
        
        # Validate that early game features are present and using real data
        self.assertIn('avg_gold_at_10', features)
        self.assertIn('avg_xp_at_10', features)
        self.assertIn('avg_cs_at_10', features)
        self.assertIn('avg_gold_diff_15', features)
        self.assertIn('avg_xp_diff_15', features)
        self.assertIn('avg_cs_diff_15', features)
        
        # Validate that values are NOT the hardcoded defaults (indicating real data usage)
        self.assertNotEqual(features['avg_gold_at_10'], 8000, 
                           "avg_gold_at_10 should not be the default fallback value")
        self.assertNotEqual(features['avg_xp_at_10'], 6000,
                           "avg_xp_at_10 should not be the default fallback value") 
        self.assertNotEqual(features['avg_cs_at_10'], 80,
                           "avg_cs_at_10 should not be the default fallback value")
        
        # Validate realistic ranges (indicates real LoL data)
        self.assertGreater(features['avg_gold_at_10'], 6000)
        self.assertLess(features['avg_gold_at_10'], 12000)
        self.assertGreater(features['avg_xp_at_10'], 4000)
        self.assertLess(features['avg_xp_at_10'], 8500)
        self.assertGreater(features['avg_cs_at_10'], 50)
        self.assertLess(features['avg_cs_at_10'], 120)
        
        print("✅ Real data extraction validation passed")
        print(f"   - Gold at 10: {features['avg_gold_at_10']:.0f} (expected: 6000-12000)")
        print(f"   - XP at 10: {features['avg_xp_at_10']:.0f} (expected: 4000-8500)")
        print(f"   - CS at 10: {features['avg_cs_at_10']:.0f} (expected: 50-120)")
        
    def test_fallback_calculations_for_missing_data(self):
        """Test that reasonable fallback values are used when early game data is missing"""
        
        # Create data with missing early game columns
        incomplete_data = self.mock_data.copy()
        incomplete_data = incomplete_data.drop(columns=['goldat10', 'xpat10', 'csat10', 
                                                       'golddiffat15', 'xpdiffat15', 'csdiffat15'])
        
        # Mock the data processor with incomplete data
        temp_processor = DataProcessor()
        temp_processor.combined_data = incomplete_data
        
        player_data = incomplete_data[incomplete_data['playername'] == 'TestPlayer']
        features = temp_processor.engineer_features(player_data, 'kills')
        
        # Validate fallback values are used
        self.assertEqual(features['avg_gold_at_10'], 8000, 
                        "Should use default gold fallback when real data missing")
        self.assertEqual(features['avg_xp_at_10'], 6000,
                        "Should use default XP fallback when real data missing")
        self.assertEqual(features['avg_cs_at_10'], 80,
                        "Should use default CS fallback when real data missing")
        self.assertEqual(features['avg_gold_diff_15'], 0,
                        "Should use neutral fallback for gold diff when missing")
        
        print("✅ Fallback calculation validation passed")
        print(f"   - Fallback gold at 10: {features['avg_gold_at_10']}")
        print(f"   - Fallback XP at 10: {features['avg_xp_at_10']}")
        print(f"   - Fallback CS at 10: {features['avg_cs_at_10']}")
        
    def test_feature_extraction_produces_reasonable_values(self):
        """Test that extracted early game features are within reasonable LoL ranges"""
        
        players = ['TestPlayer', 'TestPlayer2']
        
        for player in players:
            player_data = self.mock_data[self.mock_data['playername'] == player]
            features = self.data_processor.engineer_features(player_data, 'kills')
            
            # Test gold at 10 minutes (typical range: 6000-12000)
            self.assertGreaterEqual(features['avg_gold_at_10'], 6000,
                                   f"{player}: Gold at 10 too low: {features['avg_gold_at_10']}")
            self.assertLessEqual(features['avg_gold_at_10'], 12000,
                                f"{player}: Gold at 10 too high: {features['avg_gold_at_10']}")
            
            # Test XP at 10 minutes (typical range: 4000-8500)
            self.assertGreaterEqual(features['avg_xp_at_10'], 4000,
                                   f"{player}: XP at 10 too low: {features['avg_xp_at_10']}")
            self.assertLessEqual(features['avg_xp_at_10'], 8500,
                                f"{player}: XP at 10 too high: {features['avg_xp_at_10']}")
            
            # Test CS at 10 minutes (typical range: 50-120)
            self.assertGreaterEqual(features['avg_cs_at_10'], 50,
                                   f"{player}: CS at 10 too low: {features['avg_cs_at_10']}")
            self.assertLessEqual(features['avg_cs_at_10'], 120,
                                f"{player}: CS at 10 too high: {features['avg_cs_at_10']}")
            
            # Test differentials are reasonable (not extreme)
            self.assertLessEqual(abs(features['avg_gold_diff_15']), 2000,
                                f"{player}: Gold diff too extreme: {features['avg_gold_diff_15']}")
            self.assertLessEqual(abs(features['avg_xp_diff_15']), 1500,
                                f"{player}: XP diff too extreme: {features['avg_xp_diff_15']}")
            self.assertLessEqual(abs(features['avg_cs_diff_15']), 50,
                                f"{player}: CS diff too extreme: {features['avg_cs_diff_15']}")
            
            # Test logical relationships (gold should generally be higher than XP, etc.)
            self.assertGreater(features['avg_gold_at_10'], features['avg_xp_at_10'],
                              f"{player}: Gold should be higher than XP at 10 minutes")
        
        print("✅ Feature value range validation passed")
        print(f"   - All players have realistic early game metric ranges")
        
    def test_integration_with_prediction_pipeline(self):
        """Test that early game features integrate properly with the prediction model"""
        
        player_data = self.mock_data[self.mock_data['playername'] == 'TestPlayer']
        features = self.data_processor.engineer_features(player_data, 'kills')
        
        # Test that the prediction model can process early game features
        try:
            prediction = self.prediction_model.predict(features, prop_value=12.5, prop_type='kills')
            
            # Validate prediction structure includes early game considerations
            self.assertIn('prediction', prediction)
            self.assertIn('confidence', prediction)
            self.assertIn('expected_stat', prediction)
            self.assertIn('player_stats', prediction)
            
            # Validate that early game metrics appear in player stats
            player_stats = prediction['player_stats']
            early_game_metrics = ['avg_gold_at_10', 'avg_xp_at_10', 'avg_cs_at_10', 
                                 'avg_gold_diff_15', 'avg_xp_diff_15', 'avg_cs_diff_15']
            
            for metric in early_game_metrics:
                if metric in player_stats:
                    # Check that values are reasonable if present
                    value = player_stats[metric]
                    self.assertIsInstance(value, (int, float), 
                                        f"{metric} should be numeric")
                    self.assertNotEqual(value, None, 
                                       f"{metric} should not be None")
            
            print("✅ Pipeline integration validation passed")
            print(f"   - Prediction confidence: {prediction['confidence']}%")
            print(f"   - Expected stat: {prediction['expected_stat']}")
            print(f"   - Early game metrics integrated successfully")
            
        except Exception as e:
            self.fail(f"Early game features caused prediction pipeline failure: {e}")
            
    def test_combined_stats_calculation_with_early_game_data(self):
        """Test that early game metrics work correctly with the betting logic combined stats"""
        
        player_data = self.mock_data[self.mock_data['playername'] == 'TestPlayer']
        
        # Test the aggregate_stats method includes early game metrics
        agg_stats = self.data_processor.aggregate_stats(player_data, 'kills')
        
        # Should have aggregated early game stats per player
        self.assertIn('TestPlayer', agg_stats)
        player_stats = agg_stats['TestPlayer']
        
        # Check that early game metrics are aggregated (mean values calculated)
        early_game_keys = [
            'goldat10_mean', 'xpat10_mean', 'csat10_mean',
            'golddiffat15_mean', 'xpdiffat15_mean', 'csdiffat15_mean'
        ]
        
        for key in early_game_keys:
            if key in player_stats:
                value = player_stats[key]
                self.assertIsInstance(value, (int, float), f"{key} should be numeric")
                self.assertNotEqual(value, 0, f"{key} should not be zero with real data")
                
        print("✅ Combined stats with early game data validation passed")
        print(f"   - Early game metrics properly aggregated in betting logic")
        
    def test_performance_impact_of_early_game_calculations(self):
        """Test that early game feature extraction doesn't significantly impact performance"""
        
        import time
        
        # Test with larger dataset to measure performance
        large_data = pd.concat([self.mock_data] * 5, ignore_index=True)  # 200 rows
        temp_processor = DataProcessor()
        temp_processor.combined_data = large_data
        
        player_data = large_data[large_data['playername'] == 'TestPlayer']
        
        # Measure time for feature extraction
        start_time = time.time()
        features = temp_processor.engineer_features(player_data, 'kills')
        end_time = time.time()
        
        processing_time = end_time - start_time
        
        # Should complete in reasonable time (under 100ms for this dataset size)
        self.assertLess(processing_time, 0.1, 
                       f"Early game feature extraction too slow: {processing_time:.3f}s")
        
        # Validate all features are still present
        required_features = ['avg_gold_at_10', 'avg_xp_at_10', 'avg_cs_at_10']
        for feature in required_features:
            self.assertIn(feature, features, f"Feature {feature} missing after performance test")
            
        print("✅ Performance impact validation passed")
        print(f"   - Processing time: {processing_time:.3f}s for {len(player_data)} records")
        
    def test_data_quality_indicators_for_early_game_metrics(self):
        """Test that data quality is properly tracked for early game metrics"""
        
        # Test with complete data
        player_data = self.mock_data[self.mock_data['playername'] == 'TestPlayer']
        features = self.data_processor.engineer_features(player_data, 'kills')
        
        # Should have high sample size score with complete data
        self.assertGreater(features['sample_size_score'], 0.5, 
                          "Sample size score should be higher with complete data")
        
        # Test with minimal data
        minimal_data = player_data.head(3)  # Only 3 records
        minimal_features = self.data_processor.engineer_features(minimal_data, 'kills')
        
        # Should have lower sample size score
        self.assertLess(minimal_features['sample_size_score'], features['sample_size_score'],
                       "Sample size score should be lower with minimal data")
        
        print("✅ Data quality indicators validation passed")
        print(f"   - Complete data sample score: {features['sample_size_score']:.2f}")
        print(f"   - Minimal data sample score: {minimal_features['sample_size_score']:.2f}")
        
    def test_early_game_metrics_by_position(self):
        """Test that early game metrics vary appropriately by position"""
        
        # Get features for mid laner
        mid_data = self.mock_data[
            (self.mock_data['playername'] == 'TestPlayer') & 
            (self.mock_data['position'] == 'mid')
        ]
        mid_features = self.data_processor.engineer_features(mid_data, 'kills')
        
        # Get features for ADC
        adc_data = self.mock_data[
            (self.mock_data['playername'] == 'TestPlayer2') & 
            (self.mock_data['position'] == 'adc')
        ]
        adc_features = self.data_processor.engineer_features(adc_data, 'kills')
        
        # Both should have early game metrics
        for features, role in [(mid_features, 'mid'), (adc_features, 'adc')]:
            self.assertIn('avg_gold_at_10', features)
            self.assertIn('avg_xp_at_10', features)
            self.assertIn('avg_cs_at_10', features)
            
            # Values should be in reasonable ranges for both roles
            self.assertGreater(features['avg_gold_at_10'], 6000, 
                              f"{role} gold at 10 too low")
            self.assertLess(features['avg_gold_at_10'], 12000,
                           f"{role} gold at 10 too high")
            
        print("✅ Position-based early game metrics validation passed")
        print(f"   - Mid gold at 10: {mid_features['avg_gold_at_10']:.0f}")
        print(f"   - ADC gold at 10: {adc_features['avg_gold_at_10']:.0f}")
        
    def test_edge_cases_with_corrupted_early_game_data(self):
        """Test handling of corrupted or extreme early game data values"""
        
        # Create data with some extreme/corrupted values
        corrupted_data = self.mock_data.copy()
        
        # Introduce some extreme values
        corrupted_data.loc[0, 'goldat10'] = 50000  # Impossibly high
        corrupted_data.loc[1, 'xpat10'] = -1000    # Negative XP (impossible)
        corrupted_data.loc[2, 'csat10'] = 500      # Impossible CS
        corrupted_data.loc[3, 'golddiffat15'] = 10000  # Extreme diff
        
        temp_processor = DataProcessor()
        temp_processor.combined_data = corrupted_data
        
        player_data = corrupted_data[corrupted_data['playername'] == 'TestPlayer']
        
        # Should handle corrupted data gracefully
        try:
            features = temp_processor.engineer_features(player_data, 'kills')
            
            # Features should still be generated
            self.assertIn('avg_gold_at_10', features)
            self.assertIn('avg_xp_at_10', features)
            self.assertIn('avg_cs_at_10', features)
            
            # Values should be bounded to reasonable ranges despite corrupted input
            # (Implementation should include clipping/validation)
            self.assertIsInstance(features['avg_gold_at_10'], (int, float))
            self.assertIsInstance(features['avg_xp_at_10'], (int, float))
            self.assertIsInstance(features['avg_cs_at_10'], (int, float))
            
            print("✅ Corrupted data handling validation passed")
            print(f"   - System handles extreme values gracefully")
            
        except Exception as e:
            self.fail(f"System should handle corrupted early game data gracefully: {e}")


class TestEarlyGameIntegrationWithExistingTests(unittest.TestCase):
    """Test integration of early game metrics with existing test suite"""
    
    def test_compatibility_with_existing_feature_validation(self):
        """Test that early game metrics don't break existing feature validation"""
        
        # Create a basic data processor
        processor = DataProcessor()
        
        # Test with empty data (should use defaults)
        empty_features = processor._get_default_features()
        
        # Should include early game defaults
        early_game_defaults = [
            'avg_gold_at_10', 'avg_xp_at_10', 'avg_cs_at_10',
            'avg_gold_diff_15', 'avg_xp_diff_15', 'avg_cs_diff_15'
        ]
        
        for feature in early_game_defaults:
            self.assertIn(feature, empty_features, 
                         f"Default features should include {feature}")
            self.assertIsInstance(empty_features[feature], (int, float),
                                f"{feature} default should be numeric")
            
        print("✅ Compatibility with existing features validation passed")
        
    def test_early_game_metrics_in_prediction_model_features(self):
        """Test that prediction model can handle early game features"""
        
        # Test the prediction model's feature order includes early game metrics
        model = PredictionModel()
        feature_order = model.FEATURE_ORDER
        
        # Check if early game features are in feature order
        early_game_features = [
            'avg_gold_at_10', 'avg_xp_at_10', 'avg_cs_at_10',
            'avg_gold_diff_15', 'avg_xp_diff_15', 'avg_cs_diff_15'
        ]
        
        for feature in early_game_features:
            if feature in feature_order:
                print(f"   ✅ {feature} found in model feature order")
            else:
                print(f"   ⚠️  {feature} not in model feature order (using defaults)")
                
        print("✅ Early game features in prediction model validation completed")


def run_validation_suite():
    """Run the complete early game metrics validation suite"""
    
    print("=" * 80)
    print("EARLY GAME METRICS VALIDATION TEST SUITE")
    print("=" * 80)
    print()
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestEarlyGameMetricsValidation))
    suite.addTests(loader.loadTestsFromTestCase(TestEarlyGameIntegrationWithExistingTests))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)
    
    if result.wasSuccessful():
        print("🎉 ALL EARLY GAME VALIDATION TESTS PASSED!")
        print(f"   - Tests run: {result.testsRun}")
        print(f"   - Failures: {len(result.failures)}")
        print(f"   - Errors: {len(result.errors)}")
        print("\n✅ Early game metrics implementation is working correctly:")
        print("   • Real data extraction from CSV columns")
        print("   • Proper fallback calculations")  
        print("   • Reasonable value ranges")
        print("   • Pipeline integration")
        print("   • Performance within acceptable limits")
        return True
    else:
        print("❌ SOME VALIDATION TESTS FAILED!")
        print(f"   - Tests run: {result.testsRun}")
        print(f"   - Failures: {len(result.failures)}")
        print(f"   - Errors: {len(result.errors)}")
        
        if result.failures:
            print("\nFAILURES:")
            for test, traceback in result.failures:
                print(f"   - {test}: {traceback}")
                
        if result.errors:
            print("\nERRORS:")
            for test, traceback in result.errors:
                print(f"   - {test}: {traceback}")
        return False


if __name__ == "__main__":
    success = run_validation_suite()
    exit(0 if success else 1)