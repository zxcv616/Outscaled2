"""
TEMPORAL CONFIDENCE CALIBRATION TEST SCRIPT
==========================================

Test script to validate the temporal confidence calibration implementation.
Demonstrates the smart quant fix for confidence calibration issues in esports betting.

USAGE:
python test_temporal_calibration.py
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import logging
import sys
import os

# Add the backend directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from temporal_calibration_integration import TemporallyCalibatedModel, create_temporally_calibrated_model
from temporal_confidence_calibration import TemporalConfidenceCalibrator

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def generate_synthetic_historical_data(n_samples: int = 500) -> pd.DataFrame:
    """
    Generate synthetic historical match data for testing temporal calibration.
    Simulates meta shifts and patch changes that affect model calibration.
    """
    logger.info(f"Generating {n_samples} synthetic historical data points...")
    
    # Generate date range over 6 months
    start_date = datetime.now() - timedelta(days=180)
    dates = [start_date + timedelta(days=i) for i in range(n_samples)]
    
    # Simulate 3 patches with different meta characteristics
    patch_boundaries = [
        (0, n_samples // 3, "14.1", 0.45),      # Patch 14.1 - UNDER favored meta
        (n_samples // 3, 2 * n_samples // 3, "14.2", 0.55),  # Patch 14.2 - OVER favored meta  
        (2 * n_samples // 3, n_samples, "14.3", 0.48)        # Patch 14.3 - Balanced meta
    ]
    
    data = []
    
    for i in range(n_samples):
        # Determine patch and meta characteristics
        patch_version = "14.1"
        base_over_rate = 0.45
        
        for start_idx, end_idx, patch, over_rate in patch_boundaries:
            if start_idx <= i < end_idx:
                patch_version = patch
                base_over_rate = over_rate
                break
        
        # Generate player features with realistic distributions
        avg_kills = np.random.normal(3.5, 1.2)
        avg_assists = np.random.normal(5.2, 1.8)
        std_dev_kills = abs(np.random.normal(1.5, 0.4))
        std_dev_assists = abs(np.random.normal(2.1, 0.5))
        maps_played = np.random.randint(8, 25)
        form_z_score = np.random.normal(0, 0.8)
        
        # Generate prop value around player's average
        prop_value = max(1.0, avg_kills + np.random.normal(0, 0.5))
        
        # Calculate probability based on gap and patch meta
        gap = avg_kills - prop_value
        base_prob = 0.5 + (gap * 0.3)  # Gap-based probability
        
        # Apply patch meta bias
        meta_adjustment = (base_over_rate - 0.5) * 2  # Scale to [-1, 1]
        adjusted_prob = base_prob + (meta_adjustment * 0.1)
        adjusted_prob = max(0.1, min(0.9, adjusted_prob))
        
        # Generate actual outcome
        actual_outcome = 1 if np.random.random() < adjusted_prob else 0
        
        # Simulate model confidence (with calibration errors)
        model_confidence = adjusted_prob + np.random.normal(0, 0.05)  # Add noise
        model_confidence = max(0.1, min(0.9, model_confidence))
        
        data.append({
            'match_date': dates[i],
            'patch_version': patch_version,
            'player_name': f"Player_{i % 50}",  # 50 different players
            'avg_kills': avg_kills,
            'avg_assists': avg_assists,
            'std_dev_kills': std_dev_kills,
            'std_dev_assists': std_dev_assists,
            'maps_played': maps_played,
            'form_z_score': form_z_score,
            'position_factor': 1.0,
            'prop_value': prop_value,
            'prop_type': 'kills',
            'model_confidence': model_confidence,
            'actual_outcome': actual_outcome
        })
    
    df = pd.DataFrame(data)
    logger.info(f"Generated data spans {df['match_date'].min()} to {df['match_date'].max()}")
    logger.info(f"Patches: {df['patch_version'].value_counts().to_dict()}")
    logger.info(f"Overall OVER rate: {df['actual_outcome'].mean():.3f}")
    
    return df

def test_temporal_calibration_basic():
    """Test basic temporal calibration functionality."""
    logger.info("=== Testing Basic Temporal Calibration ===")
    
    # Generate synthetic data
    historical_data = generate_synthetic_historical_data(300)
    
    # Create temporally calibrated model
    model = create_temporally_calibrated_model()
    
    # Train temporal calibration
    logger.info("Training temporal calibration...")
    training_result = model.train_temporal_calibration(historical_data)
    
    print(f"Training Status: {training_result['status']}")
    if training_result['status'] == 'success':
        print(f"Number of temporal splits: {training_result['n_splits']}")
        print(f"Overall log loss: {training_result['calibration_results']['overall_log_loss']:.4f}")
        print(f"Average improvement: {training_result['overall_improvement']['avg_log_loss_improvement']:.4f}")
    
    # Test prediction with temporal calibration
    logger.info("Testing prediction with temporal calibration...")
    
    test_features = {
        'avg_kills': 4.2,
        'avg_assists': 6.1,
        'std_dev_kills': 1.3,
        'std_dev_assists': 1.8,
        'maps_played': 15,
        'form_z_score': 0.5,
        'position_factor': 1.0
    }
    
    test_metadata = {
        'patch_version': '14.2',
        'match_date': datetime.now(),
        'actual_outcome': None  # Unknown for prediction
    }
    
    result = model.predict(
        features=test_features,
        prop_value=4.5,
        prop_type='kills',
        match_metadata=test_metadata
    )
    
    print(f"\nPrediction Result:")
    print(f"Prediction: {result['prediction']}")
    print(f"Confidence: {result['confidence']:.1f}%")
    
    if 'temporal_calibration' in result:
        tc = result['temporal_calibration']
        print(f"Temporal Calibration Applied: {tc['applied']}")
        if tc['applied']:
            print(f"Base Confidence: {tc['base_confidence']:.1f}%")
            print(f"Calibrated Confidence: {tc['calibrated_confidence']:.1f}%")
            print(f"Adjustment: {tc['adjustment']:.1f}%")
        else:
            print(f"Reason: {tc.get('reason', 'Unknown')}")
    
    return model

def test_confidence_decay_monitoring():
    """Test confidence decay monitoring functionality."""
    logger.info("=== Testing Confidence Decay Monitoring ===")
    
    # Create model with known calibration
    model = create_temporally_calibrated_model()
    model.calibration_active = True  # Simulate active calibration
    
    # Generate some recent predictions with degrading performance
    logger.info("Simulating recent predictions with performance decay...")
    
    # Good performance initially
    for i in range(30):
        prob = 0.7 + np.random.normal(0, 0.05)
        actual = 1 if np.random.random() < prob else 0
        model._track_prediction(prob, actual)
    
    # Degrading performance (miscalibration)
    for i in range(30):
        prob = 0.7 + np.random.normal(0, 0.05)  # Model still confident
        actual = 1 if np.random.random() < 0.4 else 0  # But actual rate dropped
        model._track_prediction(prob, actual)
    
    # Monitor decay
    decay_results = model.monitor_calibration_decay(window_size=50)
    
    print(f"Decay Monitoring Status: {decay_results['status']}")
    
    if 'decay_results' in decay_results:
        dr = decay_results['decay_results']
        print(f"Decay Detected: {dr['decay_detected']}")
        print(f"Current Log Loss: {dr['current_log_loss']:.4f}")
        print(f"Baseline Log Loss: {dr.get('baseline_log_loss', 'N/A')}")
        print(f"Reliability: {dr['reliability']:.4f}")
        print(f"Resolution: {dr['resolution']:.4f}")
        print(f"Sharpness: {dr['sharpness']:.4f}")
        
        retrain_rec = decay_results['retrain_recommendation']
        print(f"Retrain Needed: {retrain_rec['retrain_needed']}")
        print(f"Recommendation: {retrain_rec['recommendation']}")
        if retrain_rec['reasons']:
            print(f"Reasons: {', '.join(retrain_rec['reasons'])}")

def test_patch_awareness():
    """Test patch-aware calibration functionality."""
    logger.info("=== Testing Patch-Aware Calibration ===")
    
    # Generate data with clear patch-based shifts
    data_patch_1 = generate_synthetic_historical_data(100)
    data_patch_1['patch_version'] = '14.1'
    data_patch_1['actual_outcome'] = (np.random.random(100) < 0.4).astype(int)  # UNDER meta
    
    data_patch_2 = generate_synthetic_historical_data(100) 
    data_patch_2['patch_version'] = '14.2'
    data_patch_2['actual_outcome'] = (np.random.random(100) < 0.6).astype(int)  # OVER meta
    
    combined_data = pd.concat([data_patch_1, data_patch_2], ignore_index=True)
    
    # Initialize temporal calibrator directly
    calibrator = TemporalConfidenceCalibrator(
        window_size_months=1,
        test_size_months=1,
        min_samples_per_window=20
    )
    
    # Prepare temporal data
    predictions = combined_data['actual_outcome'].values
    probabilities = combined_data['model_confidence'].values
    
    temporal_data = calibrator.prepare_temporal_data(
        combined_data,
        predictions,
        probabilities,
        timestamp_col='match_date',
        patch_col='patch_version'
    )
    
    print(f"Patch Info:")
    for patch, info in temporal_data['patch_info'].items():
        print(f"  {patch}: {info['n_samples']} samples, "
              f"avg_prob={info['avg_probability']:.3f}, "
              f"actual_rate={info['actual_rate']:.3f}")
    
    print(f"Created {len(temporal_data['temporal_splits'])} temporal splits")

def main():
    """Run all temporal calibration tests."""
    logger.info("Starting Temporal Confidence Calibration Tests")
    
    try:
        # Test 1: Basic temporal calibration
        model = test_temporal_calibration_basic()
        
        print("\n" + "="*60 + "\n")
        
        # Test 2: Confidence decay monitoring
        test_confidence_decay_monitoring()
        
        print("\n" + "="*60 + "\n")
        
        # Test 3: Patch awareness
        test_patch_awareness()
        
        logger.info("All temporal calibration tests completed successfully!")
        
        # Show final calibration status
        print(f"\nFinal Calibration Status:")
        status = model.get_calibration_status()
        for key, value in status.items():
            print(f"  {key}: {value}")
        
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()