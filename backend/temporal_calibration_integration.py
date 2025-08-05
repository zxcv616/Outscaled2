"""
TEMPORAL CALIBRATION INTEGRATION MODULE
=====================================

Integration layer to retrofit the existing PredictionModel with temporal confidence calibration.
Provides seamless upgrade path from static CalibratedClassifierCV to dynamic temporal calibration.

INTEGRATION STRATEGY:
1. Wrapper around existing PredictionModel
2. Intercepts confidence calculations
3. Applies temporal calibration based on recent performance
4. Maintains backward compatibility

USAGE:
Replace: model = PredictionModel()
With: model = TemporallyCalibatedModel()
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
import logging
from datetime import datetime, timedelta
from app.models.prediction_model import PredictionModel
from temporal_confidence_calibration import TemporalConfidenceCalibrator
import joblib
import os

logger = logging.getLogger(__name__)

class TemporallyCalibatedModel:
    """
    Wrapper around PredictionModel that adds temporal confidence calibration.
    
    Maintains full backward compatibility while adding temporal features:
    - Patch-aware calibration
    - Confidence decay monitoring  
    - Automatic recalibration triggers
    - Performance trend visualization
    """
    
    def __init__(self, 
                 base_model: Optional[PredictionModel] = None,
                 calibration_config: Optional[Dict] = None):
        """
        Initialize temporally calibrated model.
        
        Args:
            base_model: Existing PredictionModel instance (creates new if None)
            calibration_config: Configuration for temporal calibrator
        """
        # Initialize base model
        self.base_model = base_model or PredictionModel()
        
        # Default calibration configuration
        default_config = {
            'window_size_months': 2,
            'test_size_months': 1, 
            'min_samples_per_window': 50,
            'decay_threshold': 0.05,
            'auto_retrain': True
        }
        
        config = {**default_config, **(calibration_config or {})}
        
        # Initialize temporal calibrator
        self.temporal_calibrator = TemporalConfidenceCalibrator(**config)
        
        # Performance tracking
        self.recent_predictions = []
        self.calibration_active = False
        self.last_calibration_date = None
        self.performance_cache = {}
        
        # Patch tracking for meta shifts
        self.current_patch = None
        self.patch_performance = {}
        
        logger.info("TemporallyCalibatedModel initialized with temporal confidence calibration")
    
    def predict(self, 
                features: Dict[str, float], 
                prop_value: float,
                sample_details: Dict[str, Any] = None,
                prop_type: str = None,
                match_metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Generate prediction with temporal confidence calibration.
        
        Args:
            features: Player features
            prop_value: Betting prop value
            sample_details: Sample metadata
            prop_type: Type of prop (kills/assists)
            match_metadata: Match metadata including patch, date
            
        Returns:
            Enhanced prediction with temporal confidence
        """
        # Get base prediction from original model
        base_result = self.base_model.predict(
            features, prop_value, sample_details, prop_type
        )
        
        # Apply temporal calibration if active
        if self.calibration_active and match_metadata:
            calibrated_result = self._apply_temporal_calibration(
                base_result, match_metadata
            )
            
            # Track prediction for decay monitoring
            self._track_prediction(
                calibrated_result['confidence'] / 100.0,
                match_metadata.get('actual_outcome')
            )
            
            return calibrated_result
        
        # Return base result if no temporal calibration
        return base_result
    
    def _apply_temporal_calibration(self, 
                                  base_result: Dict[str, Any],
                                  match_metadata: Dict) -> Dict[str, Any]:
        """
        Apply temporal calibration to base prediction.
        
        Args:
            base_result: Base prediction result
            match_metadata: Match metadata with patch/date info
            
        Returns:
            Temporally calibrated prediction result
        """
        try:
            # Extract patch information
            patch = match_metadata.get('patch_version', 'unknown')
            match_date = match_metadata.get('match_date', datetime.now())
            
            # Check if we have calibration for this patch
            if patch in self.temporal_calibrator.patch_calibrators:
                calibrator = self.temporal_calibrator.patch_calibrators[patch]
                
                # Get base confidence as probability
                base_confidence = base_result['confidence'] / 100.0
                
                # Apply calibration
                calibrated_prob = calibrator.predict_proba(
                    np.array([[base_confidence]])
                )[0, 1]
                
                # Update result with calibrated confidence
                calibrated_result = base_result.copy()
                calibrated_result['confidence'] = calibrated_prob * 100.0
                calibrated_result['base_confidence'] = base_result['confidence']
                
                # Add temporal metadata
                calibrated_result['temporal_calibration'] = {
                    'applied': True,
                    'patch': patch,
                    'calibration_date': self.last_calibration_date,
                    'base_confidence': base_result['confidence'],
                    'calibrated_confidence': calibrated_prob * 100.0,
                    'adjustment': (calibrated_prob * 100.0) - base_result['confidence']
                }
                
                logger.debug(f"Applied temporal calibration for patch {patch}: "
                           f"{base_result['confidence']:.1f}% -> {calibrated_prob*100:.1f}%")
                
                return calibrated_result
            
            else:
                # No calibration available for this patch
                result = base_result.copy()
                result['temporal_calibration'] = {
                    'applied': False,
                    'reason': f'No calibration available for patch {patch}',
                    'patch': patch
                }
                return result
                
        except Exception as e:
            logger.warning(f"Temporal calibration failed: {e}")
            result = base_result.copy()
            result['temporal_calibration'] = {
                'applied': False,
                'reason': f'Calibration error: {str(e)}'
            }
            return result
    
    def _track_prediction(self, probability: float, actual_outcome: Optional[int]):
        """Track prediction for decay monitoring."""
        if actual_outcome is not None:
            self.recent_predictions.append((probability, actual_outcome))
            
            # Limit tracking history
            if len(self.recent_predictions) > 1000:
                self.recent_predictions = self.recent_predictions[-500:]
    
    def train_temporal_calibration(self, 
                                 historical_data: pd.DataFrame,
                                 retrain: bool = False) -> Dict[str, Any]:
        """
        Train temporal calibration on historical data.
        
        Args:
            historical_data: Historical match data with outcomes
            retrain: Whether to retrain existing calibration
            
        Returns:
            Training results and performance metrics
        """
        logger.info("Training temporal confidence calibration...")
        
        if not retrain and self.calibration_active:
            logger.info("Temporal calibration already active. Use retrain=True to force retrain.")
            return {'status': 'already_trained', 'active': True}
        
        try:
            # Prepare data for temporal calibration
            features_list = []
            predictions_list = []
            probabilities_list = []
            
            for _, row in historical_data.iterrows():
                # Extract features (this should match PredictionModel feature extraction)
                features = self._extract_features_from_row(row)
                
                # Get base model prediction
                base_result = self.base_model.predict(
                    features, 
                    row.get('prop_value', 5.0),
                    prop_type=row.get('prop_type', 'kills')
                )
                
                features_list.append(features)
                predictions_list.append(row.get('actual_outcome', 0))
                probabilities_list.append(base_result['confidence'] / 100.0)
            
            # Convert to arrays
            predictions = np.array(predictions_list)
            probabilities = np.array(probabilities_list)
            
            # Prepare temporal data
            temporal_data = self.temporal_calibrator.prepare_temporal_data(
                historical_data, 
                predictions,
                probabilities,
                timestamp_col='match_date',
                patch_col='patch_version'
            )
            
            # Fit temporal calibration
            calibration_results = self.temporal_calibrator.fit_temporal_calibration(
                self.base_model,
                temporal_data,
                method='isotonic'
            )
            
            # Activate calibration
            self.calibration_active = True
            self.last_calibration_date = datetime.now()
            
            logger.info(f"Temporal calibration trained successfully. "
                       f"Overall log loss: {calibration_results['overall_log_loss']:.4f}")
            
            return {
                'status': 'success',
                'calibration_results': calibration_results,
                'n_splits': calibration_results['n_splits'],
                'overall_improvement': calibration_results['calibration_improvement'],
                'trained_date': self.last_calibration_date
            }
            
        except Exception as e:
            logger.error(f"Temporal calibration training failed: {e}")
            return {
                'status': 'failed',
                'error': str(e),
                'calibration_active': False
            }
    
    def _extract_features_from_row(self, row: pd.Series) -> Dict[str, float]:
        """Extract features from data row for prediction."""
        # This should match the feature extraction in PredictionModel
        feature_mapping = {
            'avg_kills': 'avg_kills',
            'avg_assists': 'avg_assists', 
            'std_dev_kills': 'std_dev_kills',
            'std_dev_assists': 'std_dev_assists',
            'maps_played': 'maps_played',
            'form_z_score': 'form_z_score',
            'position_factor': 'position_factor'
        }
        
        features = {}
        for model_feature, data_column in feature_mapping.items():
            features[model_feature] = row.get(data_column, 0.0)
        
        return features
    
    def monitor_calibration_decay(self, window_size: int = 50) -> Dict[str, Any]:
        """
        Monitor calibration performance and detect decay.
        
        Args:
            window_size: Window size for decay detection
            
        Returns:
            Decay monitoring results
        """
        if not self.calibration_active:
            return {
                'status': 'calibration_inactive',
                'message': 'Temporal calibration not active'
            }
        
        if len(self.recent_predictions) < window_size:
            return {
                'status': 'insufficient_data',
                'n_predictions': len(self.recent_predictions),
                'required': window_size
            }
        
        # Monitor decay using temporal calibrator
        decay_results = self.temporal_calibrator.monitor_confidence_decay(
            self.recent_predictions,
            window_size
        )
        
        # Check if retraining is needed
        retrain_check = self.temporal_calibrator.auto_retrain_check(decay_results)
        
        return {
            'status': 'monitoring_active',
            'decay_results': decay_results,
            'retrain_recommendation': retrain_check,
            'last_calibration': self.last_calibration_date,
            'n_recent_predictions': len(self.recent_predictions)
        }
    
    def get_calibration_status(self) -> Dict[str, Any]:
        """Get current calibration status and performance."""
        return {
            'calibration_active': self.calibration_active,
            'last_calibration_date': self.last_calibration_date,
            'n_recent_predictions': len(self.recent_predictions),
            'available_patch_calibrators': list(self.temporal_calibrator.patch_calibrators.keys()),
            'baseline_log_loss': self.temporal_calibrator.baseline_log_loss,
            'current_log_loss': self.temporal_calibrator.current_log_loss,
            'calibration_history_length': len(self.temporal_calibrator.calibration_history)
        }
    
    def visualize_calibration_performance(self, save_path: Optional[str] = None):
        """Generate calibration performance visualization."""
        if not self.calibration_active:
            logger.warning("Cannot visualize - temporal calibration not active")
            return None
        
        # This would use the temporal_calibrator's visualization method
        # with the most recent calibration results
        if hasattr(self.temporal_calibrator, 'last_temporal_results'):
            return self.temporal_calibrator.visualize_temporal_calibration(
                self.temporal_calibrator.last_temporal_results,
                save_path
            )
        else:
            logger.warning("No calibration results available for visualization")
            return None
    
    def save_calibration_state(self, path: str):
        """Save temporal calibration state to disk."""
        calibration_state = {
            'calibration_active': self.calibration_active,
            'last_calibration_date': self.last_calibration_date,
            'recent_predictions': self.recent_predictions[-100:],  # Save last 100
            'performance_cache': self.performance_cache,
            'current_patch': self.current_patch,
            'patch_performance': self.patch_performance
        }
        
        # Save calibrator state
        calibrator_path = path.replace('.pkl', '_calibrator.pkl')
        self.temporal_calibrator.save_calibrator(
            self.temporal_calibrator.current_calibrator,
            calibrator_path
        )
        
        # Save wrapper state
        joblib.dump(calibration_state, path)
        logger.info(f"Temporal calibration state saved to {path}")
    
    def load_calibration_state(self, path: str):
        """Load temporal calibration state from disk."""
        try:
            # Load wrapper state
            calibration_state = joblib.load(path)
            
            self.calibration_active = calibration_state['calibration_active']
            self.last_calibration_date = calibration_state['last_calibration_date']
            self.recent_predictions = calibration_state['recent_predictions']
            self.performance_cache = calibration_state['performance_cache']
            self.current_patch = calibration_state['current_patch']
            self.patch_performance = calibration_state['patch_performance']
            
            # Load calibrator state
            calibrator_path = path.replace('.pkl', '_calibrator.pkl')
            if os.path.exists(calibrator_path):
                self.temporal_calibrator.current_calibrator = self.temporal_calibrator.load_calibrator(
                    calibrator_path
                )
            
            logger.info(f"Temporal calibration state loaded from {path}")
            
        except Exception as e:
            logger.error(f"Failed to load calibration state: {e}")
            self.calibration_active = False


# Factory function for easy integration
def create_temporally_calibrated_model(historical_data: Optional[pd.DataFrame] = None,
                                     config: Optional[Dict] = None) -> TemporallyCalibatedModel:
    """
    Factory function to create and optionally train a temporally calibrated model.
    
    Args:
        historical_data: Historical data for training (optional)
        config: Calibration configuration (optional)
        
    Returns:
        TemporallyCalibatedModel instance
    """
    model = TemporallyCalibatedModel(calibration_config=config)
    
    if historical_data is not None:
        logger.info("Training temporal calibration with provided historical data...")
        training_result = model.train_temporal_calibration(historical_data)
        
        if training_result['status'] == 'success':
            logger.info("Temporal calibration training completed successfully")
        else:
            logger.warning(f"Temporal calibration training failed: {training_result.get('error')}")
    
    return model


# Backward compatibility alias
def get_enhanced_prediction_model() -> TemporallyCalibatedModel:
    """Backward compatibility function."""
    return create_temporally_calibrated_model()