"""
TEMPORAL CONFIDENCE CALIBRATION SYSTEM

Smart Quant Fix for temporal confidence calibration per user directives.
Addresses the core problem that confidence is calibrated on pooled data instead of 
time-split sets, which doesn't account for rapid meta shifts in esports.

Key Features:
1. Temporal cross-validation: train on one patch group, test on next
2. Sliding window calibration: 2-month training, 1-month test
3. Confidence decay monitoring: retrain when accuracy/log loss slips  
4. Real-time visualization: actual vs predicted probability over time
"""

import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import log_loss, brier_score_loss
import logging
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

logger = logging.getLogger(__name__)

class TemporalConfidenceCalibrator:
    """
    Smart Quant temporal confidence calibration system.
    
    Implements sliding window calibration with patch awareness to handle
    esports meta shifts and maintain reliable confidence estimates over time.
    """
    
    def __init__(self, 
                 training_window_months: int = 2,
                 test_window_months: int = 1,
                 decay_threshold: float = 0.1,
                 min_samples_per_window: int = 100):
        """
        Initialize temporal calibration system.
        
        Args:
            training_window_months: Training window size in months
            test_window_months: Test window size in months  
            decay_threshold: Log loss increase threshold for retraining
            min_samples_per_window: Minimum samples required per window
        """
        self.training_window_months = training_window_months
        self.test_window_months = test_window_months
        self.decay_threshold = decay_threshold
        self.min_samples_per_window = min_samples_per_window
        
        # Calibration state
        self.calibrators = {}  # patch_group -> calibrator mapping
        self.baseline_performance = {}  # patch_group -> performance metrics
        self.calibration_history = []  # Historical performance tracking
        
        # Monitoring
        self.needs_retraining = False
        self.last_calibration_date = None
        
    def fit_temporal_calibration(self, 
                                X: np.ndarray, 
                                y: np.ndarray, 
                                timestamps: pd.Series,
                                patch_groups: pd.Series,
                                base_predictions: np.ndarray) -> Dict[str, Any]:
        """
        Fit temporal calibration using sliding windows per user directives.
        
        Args:
            X: Feature matrix
            y: True labels
            timestamps: Timestamps for temporal splitting
            patch_groups: Patch group identifiers for meta awareness
            base_predictions: Base model predictions to calibrate
            
        Returns:
            Calibration results and performance metrics
        """
        logger.info("Starting temporal confidence calibration")
        
        # Create temporal splits using sliding windows
        temporal_splits = self._create_temporal_splits(timestamps, patch_groups)
        
        calibration_results = {
            'patch_calibrators': {},
            'performance_metrics': {},
            'temporal_validation': []
        }
        
        for split_idx, (train_idx, test_idx, patch_group) in enumerate(temporal_splits):
            logger.info(f"Processing temporal split {split_idx + 1}/{len(temporal_splits)} for patch {patch_group}")
            
            # Extract training and test data for this temporal window
            X_train_cal, y_train_cal = X[train_idx], y[train_idx]
            X_test_cal, y_test_cal = X[test_idx], y[test_idx]
            pred_train_cal = base_predictions[train_idx]
            pred_test_cal = base_predictions[test_idx]
            
            # Skip if insufficient samples
            if len(X_train_cal) < self.min_samples_per_window:
                logger.warning(f"Insufficient training samples ({len(X_train_cal)}) for patch {patch_group}")
                continue
                
            if len(X_test_cal) < self.min_samples_per_window // 2:
                logger.warning(f"Insufficient test samples ({len(X_test_cal)}) for patch {patch_group}")
                continue
            
            # Fit calibrator for this patch group
            calibrator = CalibratedClassifierCV(
                method='isotonic',  # Better for small samples than 'sigmoid'
                cv='prefit'  # We're doing our own temporal splits
            )
            
            try:
                # Calibrate using training window
                calibrator.fit(pred_train_cal.reshape(-1, 1), y_train_cal)
                
                # Generate calibrated predictions for test window
                calibrated_probs = calibrator.predict_proba(pred_test_cal.reshape(-1, 1))[:, 1]
                
                # Calculate performance metrics
                metrics = self._calculate_calibration_metrics(
                    y_test_cal, calibrated_probs, pred_test_cal
                )
                
                # Store calibrator and results
                self.calibrators[patch_group] = calibrator
                self.baseline_performance[patch_group] = metrics
                calibration_results['patch_calibrators'][patch_group] = calibrator
                calibration_results['performance_metrics'][patch_group] = metrics
                
                # Store temporal validation results
                validation_result = {
                    'split_idx': split_idx,
                    'patch_group': patch_group,
                    'train_size': len(X_train_cal),
                    'test_size': len(X_test_cal),
                    'metrics': metrics,
                    'timestamp': timestamps.iloc[test_idx[len(test_idx)//2]]  # Middle timestamp
                }
                calibration_results['temporal_validation'].append(validation_result)
                
                logger.info(f"Patch {patch_group} calibration - Log loss: {metrics['log_loss']:.4f}, "
                          f"Brier score: {metrics['brier_score']:.4f}")
                
            except Exception as e:
                logger.error(f"Error calibrating patch {patch_group}: {e}")
                continue
        
        # Set calibration timestamp
        self.last_calibration_date = datetime.now()
        self.needs_retraining = False
        
        logger.info(f"Temporal calibration completed. Calibrated {len(self.calibrators)} patch groups.")
        
        return calibration_results
    
    def predict_calibrated_confidence(self, 
                                    base_predictions: np.ndarray,
                                    patch_groups: pd.Series,
                                    current_patch: str = None) -> np.ndarray:
        """
        Generate calibrated confidence scores using appropriate temporal calibrator.
        
        Args:
            base_predictions: Base model predictions to calibrate
            patch_groups: Patch groups for each prediction
            current_patch: Current patch for fallback
            
        Returns:
            Calibrated confidence scores
        """
        calibrated_scores = np.zeros(len(base_predictions))
        
        for i, (pred, patch) in enumerate(zip(base_predictions, patch_groups)):
            # Use patch-specific calibrator if available
            if patch in self.calibrators:
                calibrator = self.calibrators[patch]
            elif current_patch and current_patch in self.calibrators:
                # Fallback to current patch calibrator
                calibrator = self.calibrators[current_patch]
                logger.debug(f"Using current patch calibrator for patch {patch}")
            else:
                # Fallback to most recent calibrator
                if self.calibrators:
                    latest_patch = max(self.calibrators.keys())
                    calibrator = self.calibrators[latest_patch]
                    logger.debug(f"Using latest calibrator ({latest_patch}) for patch {patch}")
                else:
                    # No calibration available - return uncalibrated prediction
                    calibrated_scores[i] = pred
                    continue
            
            try:
                calibrated_prob = calibrator.predict_proba(pred.reshape(1, -1))[0, 1]
                calibrated_scores[i] = calibrated_prob
            except Exception as e:
                logger.warning(f"Error calibrating prediction for patch {patch}: {e}")
                calibrated_scores[i] = pred
        
        return calibrated_scores
    
    def monitor_confidence_decay(self, 
                               recent_predictions: np.ndarray,
                               recent_actuals: np.ndarray,
                               current_patch: str) -> Dict[str, Any]:
        """
        Monitor confidence decay and trigger retraining per user directives.
        
        Args:
            recent_predictions: Recent calibrated predictions
            recent_actuals: Recent actual outcomes
            current_patch: Current patch group
            
        Returns:
            Decay monitoring results and retraining recommendation
        """
        if len(recent_predictions) < 20:  # Need minimum samples for reliable assessment
            return {'status': 'insufficient_data', 'needs_retraining': False}
        
        # Calculate current performance metrics
        current_metrics = self._calculate_calibration_metrics(
            recent_actuals, recent_predictions, recent_predictions  # Using calibrated as base
        )
        
        # Compare with baseline performance for this patch
        decay_detected = False
        decay_details = {}
        
        if current_patch in self.baseline_performance:
            baseline = self.baseline_performance[current_patch]
            
            # Check log loss degradation
            log_loss_increase = current_metrics['log_loss'] - baseline['log_loss']
            if log_loss_increase > self.decay_threshold:
                decay_detected = True
                decay_details['log_loss_degradation'] = log_loss_increase
            
            # Check Brier score degradation  
            brier_increase = current_metrics['brier_score'] - baseline['brier_score']
            if brier_increase > self.decay_threshold:
                decay_detected = True
                decay_details['brier_degradation'] = brier_increase
            
            # Check reliability degradation
            reliability_decrease = baseline['reliability'] - current_metrics['reliability']
            if reliability_decrease > 0.05:  # 5% reliability drop threshold
                decay_detected = True
                decay_details['reliability_degradation'] = reliability_decrease
        
        # Update retraining flag
        if decay_detected:
            self.needs_retraining = True
            logger.warning(f"Confidence decay detected for patch {current_patch}: {decay_details}")
        
        # Store monitoring results
        monitoring_result = {
            'timestamp': datetime.now(),
            'patch_group': current_patch,
            'current_metrics': current_metrics,
            'baseline_metrics': self.baseline_performance.get(current_patch, {}),
            'decay_detected': decay_detected,
            'decay_details': decay_details,
            'needs_retraining': decay_detected,
            'sample_size': len(recent_predictions)
        }
        
        self.calibration_history.append(monitoring_result)
        
        return monitoring_result
    
    def _create_temporal_splits(self, 
                              timestamps: pd.Series, 
                              patch_groups: pd.Series) -> List[Tuple[np.ndarray, np.ndarray, str]]:
        """
        Create temporal splits using sliding windows with patch awareness.
        
        Returns:
            List of (train_indices, test_indices, patch_group) tuples
        """
        # Convert to DataFrame for easier manipulation
        df = pd.DataFrame({
            'timestamp': timestamps,
            'patch_group': patch_groups,
            'index': range(len(timestamps))
        }).sort_values('timestamp')
        
        splits = []
        
        # Get unique patches in chronological order
        patch_chronology = df.groupby('patch_group')['timestamp'].min().sort_values()
        
        for i, patch in enumerate(patch_chronology.index[1:], 1):  # Start from second patch
            # Training window: previous patches within time window
            train_end_time = patch_chronology[patch]
            train_start_time = train_end_time - timedelta(days=30 * self.training_window_months)
            
            train_mask = (df['timestamp'] >= train_start_time) & (df['timestamp'] < train_end_time)
            train_indices = df[train_mask]['index'].values
            
            # Test window: current patch within time window
            test_end_time = min(
                train_end_time + timedelta(days=30 * self.test_window_months),
                df['timestamp'].max()
            )
            
            test_mask = (df['timestamp'] >= train_end_time) & (df['timestamp'] <= test_end_time)
            test_indices = df[test_mask]['index'].values
            
            if len(train_indices) >= self.min_samples_per_window and len(test_indices) >= self.min_samples_per_window // 2:
                splits.append((train_indices, test_indices, patch))
        
        logger.info(f"Created {len(splits)} temporal splits for calibration")
        return splits
    
    def _calculate_calibration_metrics(self, 
                                     y_true: np.ndarray, 
                                     y_pred_proba: np.ndarray,
                                     y_pred_base: np.ndarray) -> Dict[str, float]:
        """Calculate comprehensive calibration performance metrics."""
        
        metrics = {}
        
        try:
            # Basic metrics
            metrics['log_loss'] = log_loss(y_true, y_pred_proba)
            metrics['brier_score'] = brier_score_loss(y_true, y_pred_proba)
            
            # Reliability (calibration quality)
            n_bins = min(10, len(np.unique(y_pred_proba)))
            bin_boundaries = np.linspace(0, 1, n_bins + 1)
            bin_lowers = bin_boundaries[:-1]
            bin_uppers = bin_boundaries[1:]
            
            reliability = 0
            resolution = 0
            
            for bin_lower, bin_upper in zip(bin_lowers, bin_uppers):
                in_bin = (y_pred_proba > bin_lower) & (y_pred_proba <= bin_upper)
                prop_in_bin = in_bin.mean()
                
                if prop_in_bin > 0:
                    accuracy_in_bin = y_true[in_bin].mean()
                    avg_confidence_in_bin = y_pred_proba[in_bin].mean()
                    
                    reliability += prop_in_bin * ((avg_confidence_in_bin - accuracy_in_bin) ** 2)
                    resolution += prop_in_bin * ((accuracy_in_bin - y_true.mean()) ** 2)
            
            metrics['reliability'] = reliability
            metrics['resolution'] = resolution
            metrics['sharpness'] = np.var(y_pred_proba)
            
            # Improvement over base model
            if len(y_pred_base) == len(y_true):
                base_log_loss = log_loss(y_true, y_pred_base)
                metrics['log_loss_improvement'] = base_log_loss - metrics['log_loss']
            
        except Exception as e:
            logger.error(f"Error calculating calibration metrics: {e}")
            metrics['log_loss'] = float('inf')
            metrics['brier_score'] = float('inf')
            metrics['reliability'] = 1.0
            metrics['resolution'] = 0.0
            metrics['sharpness'] = 0.0
        
        return metrics
    
    def visualize_calibration_over_time(self, save_path: Optional[str] = None) -> None:
        """
        Visualize actual vs predicted probability over time per user directives.
        """
        if not self.calibration_history:
            logger.warning("No calibration history available for visualization")
            return
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('Temporal Confidence Calibration Analysis', fontsize=16)
        
        # Extract data for plotting
        history_df = pd.DataFrame([
            {
                'timestamp': h['timestamp'],
                'patch_group': h['patch_group'],
                'log_loss': h['current_metrics']['log_loss'],
                'brier_score': h['current_metrics']['brier_score'],
                'reliability': h['current_metrics']['reliability'],
                'sample_size': h['sample_size']
            }
            for h in self.calibration_history
        ])
        
        # Plot 1: Log loss over time
        axes[0, 0].plot(history_df['timestamp'], history_df['log_loss'], 'b-o')
        axes[0, 0].set_title('Log Loss Over Time')
        axes[0, 0].set_ylabel('Log Loss')
        axes[0, 0].tick_params(axis='x', rotation=45)
        
        # Plot 2: Brier score over time
        axes[0, 1].plot(history_df['timestamp'], history_df['brier_score'], 'r-o')
        axes[0, 1].set_title('Brier Score Over Time')
        axes[0, 1].set_ylabel('Brier Score')
        axes[0, 1].tick_params(axis='x', rotation=45)
        
        # Plot 3: Reliability over time
        axes[1, 0].plot(history_df['timestamp'], history_df['reliability'], 'g-o')
        axes[1, 0].set_title('Reliability Over Time')
        axes[1, 0].set_ylabel('Reliability (lower is better)')
        axes[1, 0].tick_params(axis='x', rotation=45)
        
        # Plot 4: Sample sizes
        axes[1, 1].bar(range(len(history_df)), history_df['sample_size'])
        axes[1, 1].set_title('Sample Sizes')
        axes[1, 1].set_ylabel('Sample Size')
        axes[1, 1].set_xlabel('Calibration Window')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Calibration visualization saved to {save_path}")
        else:
            plt.show()
    
    def get_calibration_status(self) -> Dict[str, Any]:
        """Get current calibration status and recommendations."""
        
        status = {
            'last_calibration': self.last_calibration_date,
            'needs_retraining': self.needs_retraining,
            'active_calibrators': list(self.calibrators.keys()),
            'calibration_windows': len(self.calibration_history),
            'recommendations': []
        }
        
        # Generate recommendations
        if self.needs_retraining:
            status['recommendations'].append("⚠️ RETRAIN REQUIRED: Confidence decay detected")
        
        if not self.calibrators:
            status['recommendations'].append("🔧 SETUP REQUIRED: No calibrators available")
        
        if self.last_calibration_date:
            days_since_calibration = (datetime.now() - self.last_calibration_date).days
            if days_since_calibration > 30:
                status['recommendations'].append(f"📅 Consider recalibration ({days_since_calibration} days old)")
        
        return status