"""
TEMPORAL CONFIDENCE CALIBRATION SYSTEM
======================================

Addresses the core problem: Confidence calibrated on pooled data assumes stationarity.
In esports, meta shifts cause model miscalibration across patches.

SMART QUANT FIX IMPLEMENTATION:
1. Temporal cross-validation with patch-aware grouping
2. Sliding window calibration (2-month training, 1-month test)
3. Confidence decay monitoring with automatic retrain triggers
4. Real-time actual vs predicted probability visualization

This system replaces static CalibratedClassifierCV with dynamic temporal calibration.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Tuple, Optional
import logging
from datetime import datetime, timedelta
from sklearn.calibration import CalibratedClassifierCV
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import log_loss, brier_score_loss
import matplotlib.pyplot as plt
import seaborn as sns
from collections import defaultdict, deque
import warnings
import pickle
import os

logger = logging.getLogger(__name__)

class TemporalConfidenceCalibrator:
    """
    Temporal confidence calibration system for esports betting models.
    
    Addresses model miscalibration due to meta shifts by:
    - Using temporal cross-validation instead of random splits
    - Implementing sliding window calibration
    - Monitoring confidence decay over time
    - Auto-retraining when calibration degrades
    """
    
    def __init__(self, 
                 window_size_months: int = 2,
                 test_size_months: int = 1,
                 min_samples_per_window: int = 50,
                 decay_threshold: float = 0.05,
                 auto_retrain: bool = True):
        """
        Initialize temporal calibrator.
        
        Args:
            window_size_months: Training window size in months
            test_size_months: Test window size in months  
            min_samples_per_window: Minimum samples required per window
            decay_threshold: Log loss increase threshold for retraining
            auto_retrain: Whether to automatically retrain on decay
        """
        self.window_size_months = window_size_months
        self.test_size_months = test_size_months
        self.min_samples_per_window = min_samples_per_window
        self.decay_threshold = decay_threshold
        self.auto_retrain = auto_retrain
        
        # Calibration history tracking
        self.calibration_history = []
        self.performance_history = deque(maxlen=100)  # Last 100 predictions
        self.patch_calibrators = {}  # Patch-specific calibrators
        self.current_calibrator = None
        
        # Performance monitoring
        self.baseline_log_loss = None
        self.current_log_loss = None
        self.calibration_metrics = {
            'reliability': [],
            'resolution': [], 
            'sharpness': [],
            'log_loss': [],
            'brier_score': []
        }
        
        logger.info(f"Initialized TemporalConfidenceCalibrator with {window_size_months}m training, {test_size_months}m test windows")
    
    def prepare_temporal_data(self, 
                            data: pd.DataFrame, 
                            predictions: np.ndarray,
                            probabilities: np.ndarray,
                            timestamp_col: str = 'match_date',
                            patch_col: str = 'patch_version') -> Dict[str, Any]:
        """
        Prepare data for temporal cross-validation with patch awareness.
        
        Args:
            data: Historical match data with timestamps
            predictions: Model predictions (0/1)
            probabilities: Model probability estimates
            timestamp_col: Column name for timestamps
            patch_col: Column name for patch versions
            
        Returns:
            Dict with temporal splits and metadata
        """
        logger.info("Preparing temporal data for calibration...")
        
        # Ensure timestamps are datetime
        if not pd.api.types.is_datetime64_any_dtype(data[timestamp_col]):
            data[timestamp_col] = pd.to_datetime(data[timestamp_col])
        
        # Sort by timestamp
        data_sorted = data.sort_values(timestamp_col).copy()
        data_sorted['predictions'] = predictions
        data_sorted['probabilities'] = probabilities
        
        # Group by patch for meta-aware splits
        patch_groups = data_sorted.groupby(patch_col)
        patch_info = {}
        
        for patch, group in patch_groups:
            patch_info[patch] = {
                'start_date': group[timestamp_col].min(),
                'end_date': group[timestamp_col].max(),
                'n_samples': len(group),
                'avg_probability': group['probabilities'].mean(),
                'actual_rate': group['predictions'].mean()
            }
        
        # Create temporal splits
        temporal_splits = self._create_temporal_splits(data_sorted, timestamp_col)
        
        return {
            'data': data_sorted,
            'patch_info': patch_info,
            'temporal_splits': temporal_splits,
            'n_patches': len(patch_groups),
            'date_range': (data_sorted[timestamp_col].min(), data_sorted[timestamp_col].max())
        }
    
    def _create_temporal_splits(self, 
                              data: pd.DataFrame, 
                              timestamp_col: str) -> List[Dict[str, Any]]:
        """
        Create temporal cross-validation splits with sliding windows.
        
        Args:
            data: Sorted temporal data
            timestamp_col: Timestamp column name
            
        Returns:
            List of temporal splits with train/test indices
        """
        splits = []
        
        # Calculate window sizes in days
        window_days = self.window_size_months * 30
        test_days = self.test_size_months * 30
        
        start_date = data[timestamp_col].min()
        end_date = data[timestamp_col].max()
        
        current_date = start_date + timedelta(days=window_days)
        
        while current_date + timedelta(days=test_days) <= end_date:
            # Define training window
            train_start = current_date - timedelta(days=window_days)
            train_end = current_date
            
            # Define test window
            test_start = current_date
            test_end = current_date + timedelta(days=test_days)
            
            # Get indices
            train_mask = (data[timestamp_col] >= train_start) & (data[timestamp_col] < train_end)
            test_mask = (data[timestamp_col] >= test_start) & (data[timestamp_col] < test_end)
            
            train_indices = data[train_mask].index.tolist()
            test_indices = data[test_mask].index.tolist()
            
            # Only include if sufficient samples
            if len(train_indices) >= self.min_samples_per_window and len(test_indices) >= 10:
                splits.append({
                    'train_indices': train_indices,
                    'test_indices': test_indices,
                    'train_period': (train_start, train_end),
                    'test_period': (test_start, test_end),
                    'train_size': len(train_indices),
                    'test_size': len(test_indices)
                })
            
            # Move window forward by test period
            current_date += timedelta(days=test_days)
        
        logger.info(f"Created {len(splits)} temporal splits")
        return splits
    
    def fit_temporal_calibration(self, 
                                base_model,
                                temporal_data: Dict[str, Any],
                                method: str = 'isotonic') -> Dict[str, Any]:
        """
        Fit temporal calibration using sliding windows.
        
        Args:
            base_model: Base prediction model
            temporal_data: Prepared temporal data
            method: Calibration method ('isotonic' or 'sigmoid')
            
        Returns:
            Dict with calibration results and performance metrics
        """
        logger.info(f"Fitting temporal calibration with {method} method...")
        
        data = temporal_data['data']
        splits = temporal_data['temporal_splits']
        
        calibration_results = []
        all_predictions = []
        all_probabilities = []
        all_true_labels = []
        
        for i, split in enumerate(splits):
            logger.info(f"Processing temporal split {i+1}/{len(splits)}")
            
            # Get training and test data
            train_data = data.iloc[split['train_indices']]
            test_data = data.iloc[split['test_indices']]
            
            # Extract features and labels for training
            X_train = self._extract_features(train_data)
            y_train = train_data['predictions'].values
            
            # Extract features for testing  
            X_test = self._extract_features(test_data)
            y_test = test_data['predictions'].values
            
            # Get base model predictions on training set
            base_probs_train = base_model.predict_proba(X_train)[:, 1]
            
            # Fit calibrator on training data
            calibrator = CalibratedClassifierCV(
                base_estimator=None,  # We'll use prefit predictions
                method=method,
                cv='prefit'
            )
            
            # Reshape for calibrator
            base_probs_train_reshaped = base_probs_train.reshape(-1, 1)
            calibrator.fit(base_probs_train_reshaped, y_train)
            
            # Get calibrated predictions on test set
            base_probs_test = base_model.predict_proba(X_test)[:, 1]
            calibrated_probs = calibrator.predict_proba(base_probs_test.reshape(-1, 1))[:, 1]
            
            # Calculate metrics
            uncalibrated_log_loss = log_loss(y_test, base_probs_test)
            calibrated_log_loss = log_loss(y_test, calibrated_probs)
            
            uncalibrated_brier = brier_score_loss(y_test, base_probs_test)
            calibrated_brier = brier_score_loss(y_test, calibrated_probs)
            
            # Store results
            split_result = {
                'split_id': i,
                'period': split['test_period'],
                'calibrator': calibrator,
                'uncalibrated_log_loss': uncalibrated_log_loss,
                'calibrated_log_loss': calibrated_log_loss,
                'uncalibrated_brier': uncalibrated_brier,
                'calibrated_brier': calibrated_brier,
                'improvement_log_loss': uncalibrated_log_loss - calibrated_log_loss,
                'improvement_brier': uncalibrated_brier - calibrated_brier,
                'n_test_samples': len(y_test)
            }
            
            calibration_results.append(split_result)
            
            # Collect all predictions for overall analysis
            all_predictions.extend(y_test.tolist())
            all_probabilities.extend(calibrated_probs.tolist())
            all_true_labels.extend(y_test.tolist())
        
        # Calculate overall performance
        overall_log_loss = log_loss(all_true_labels, all_probabilities)
        overall_brier = brier_score_loss(all_true_labels, all_probabilities)
        
        # Store baseline performance
        if self.baseline_log_loss is None:
            self.baseline_log_loss = overall_log_loss
        self.current_log_loss = overall_log_loss
        
        # Update calibration history
        self.calibration_history.append({
            'timestamp': datetime.now(),
            'method': method,
            'log_loss': overall_log_loss,
            'brier_score': overall_brier,
            'n_splits': len(splits),
            'total_samples': len(all_predictions)
        })
        
        return {
            'split_results': calibration_results,
            'overall_log_loss': overall_log_loss,
            'overall_brier_score': overall_brier,
            'n_splits': len(splits),
            'total_test_samples': len(all_predictions),
            'calibration_improvement': self._calculate_calibration_improvement(calibration_results)
        }
    
    def _extract_features(self, data: pd.DataFrame) -> np.ndarray:
        """
        Extract features from data for model input.
        This should match the feature extraction used in the base model.
        """
        # This is a placeholder - in practice, this should match
        # the exact feature extraction from PredictionModel
        feature_columns = [
            'avg_kills', 'avg_assists', 'std_dev_kills', 'std_dev_assists',
            'maps_played', 'longterm_kills_avg', 'longterm_assists_avg',
            'form_z_score', 'form_deviation_ratio', 'position_factor',
            'sample_size_score'
        ]
        
        # Fill missing columns with defaults
        for col in feature_columns:
            if col not in data.columns:
                data[col] = 0.0
        
        return data[feature_columns].fillna(0).values
    
    def monitor_confidence_decay(self, 
                                recent_predictions: List[Tuple[float, int]],
                                window_size: int = 50) -> Dict[str, Any]:
        """
        Monitor confidence decay by tracking recent prediction performance.
        
        Args:
            recent_predictions: List of (probability, actual) pairs
            window_size: Window size for moving average
            
        Returns:
            Dict with decay metrics and recommendations
        """
        if len(recent_predictions) < window_size:
            return {
                'status': 'insufficient_data',
                'n_samples': len(recent_predictions),
                'required': window_size
            }
        
        # Add to performance history
        self.performance_history.extend(recent_predictions)
        
        # Calculate recent performance
        recent_window = list(self.performance_history)[-window_size:]
        probs, actuals = zip(*recent_window)
        
        current_log_loss = log_loss(actuals, probs)
        current_brier = brier_score_loss(actuals, probs)
        
        # Compare to baseline
        decay_detected = False
        if self.baseline_log_loss is not None:
            log_loss_increase = current_log_loss - self.baseline_log_loss
            decay_detected = log_loss_increase > self.decay_threshold
        
        # Calculate calibration metrics
        reliability = self._calculate_reliability(probs, actuals)
        resolution = self._calculate_resolution(probs, actuals)
        sharpness = self._calculate_sharpness(probs)
        
        result = {
            'decay_detected': decay_detected,
            'current_log_loss': current_log_loss,
            'baseline_log_loss': self.baseline_log_loss,
            'log_loss_increase': current_log_loss - (self.baseline_log_loss or current_log_loss),
            'current_brier_score': current_brier,
            'reliability': reliability,
            'resolution': resolution,
            'sharpness': sharpness,
            'n_recent_samples': len(recent_window),
            'recommendation': 'retrain' if decay_detected else 'continue'
        }
        
        # Update metrics history
        self.calibration_metrics['log_loss'].append(current_log_loss)
        self.calibration_metrics['brier_score'].append(current_brier)
        self.calibration_metrics['reliability'].append(reliability)
        self.calibration_metrics['resolution'].append(resolution)
        self.calibration_metrics['sharpness'].append(sharpness)
        
        return result
    
    def _calculate_reliability(self, probabilities: List[float], outcomes: List[int]) -> float:
        """Calculate reliability (calibration) component."""
        # Bin probabilities and calculate reliability
        bins = np.linspace(0, 1, 11)
        bin_indices = np.digitize(probabilities, bins) - 1
        
        reliability = 0.0
        total_weight = 0.0
        
        for i in range(len(bins) - 1):
            mask = bin_indices == i
            if np.sum(mask) > 0:
                bin_prob = np.mean(probabilities[mask])
                bin_outcome = np.mean(outcomes[mask])
                bin_weight = np.sum(mask) / len(probabilities)
                
                reliability += bin_weight * (bin_prob - bin_outcome) ** 2
                total_weight += bin_weight
        
        return reliability / max(total_weight, 0.001)
    
    def _calculate_resolution(self, probabilities: List[float], outcomes: List[int]) -> float:
        """Calculate resolution component."""
        overall_rate = np.mean(outcomes)
        
        bins = np.linspace(0, 1, 11)
        bin_indices = np.digitize(probabilities, bins) - 1
        
        resolution = 0.0
        
        for i in range(len(bins) - 1):
            mask = bin_indices == i
            if np.sum(mask) > 0:
                bin_outcome = np.mean(outcomes[mask])
                bin_weight = np.sum(mask) / len(probabilities)
                
                resolution += bin_weight * (bin_outcome - overall_rate) ** 2
        
        return resolution
    
    def _calculate_sharpness(self, probabilities: List[float]) -> float:
        """Calculate sharpness (how extreme the probabilities are)."""
        overall_rate = np.mean(probabilities)
        return np.mean([(p - overall_rate) ** 2 for p in probabilities])
    
    def _calculate_calibration_improvement(self, results: List[Dict]) -> Dict[str, float]:
        """Calculate average calibration improvement across splits."""
        log_loss_improvements = [r['improvement_log_loss'] for r in results]
        brier_improvements = [r['improvement_brier'] for r in results]
        
        return {
            'avg_log_loss_improvement': np.mean(log_loss_improvements),
            'avg_brier_improvement': np.mean(brier_improvements),
            'std_log_loss_improvement': np.std(log_loss_improvements),
            'std_brier_improvement': np.std(brier_improvements),
            'positive_improvements': sum(1 for x in log_loss_improvements if x > 0),
            'total_splits': len(results)
        }
    
    def visualize_temporal_calibration(self, 
                                     temporal_results: Dict[str, Any],
                                     save_path: Optional[str] = None) -> plt.Figure:
        """
        Visualize actual vs predicted probability over time.
        
        Args:
            temporal_results: Results from fit_temporal_calibration
            save_path: Optional path to save the plot
            
        Returns:
            Matplotlib figure
        """
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('Temporal Confidence Calibration Analysis', fontsize=16)
        
        # Plot 1: Log Loss over time
        split_results = temporal_results['split_results']
        periods = [r['period'][0] for r in split_results]
        uncalibrated_losses = [r['uncalibrated_log_loss'] for r in split_results]
        calibrated_losses = [r['calibrated_log_loss'] for r in split_results]
        
        axes[0, 0].plot(periods, uncalibrated_losses, 'r-', label='Uncalibrated', marker='o')
        axes[0, 0].plot(periods, calibrated_losses, 'b-', label='Calibrated', marker='s')
        axes[0, 0].set_title('Log Loss Over Time')
        axes[0, 0].set_ylabel('Log Loss')
        axes[0, 0].legend()
        axes[0, 0].tick_params(axis='x', rotation=45)
        
        # Plot 2: Calibration improvement
        improvements = [r['improvement_log_loss'] for r in split_results]
        axes[0, 1].bar(range(len(improvements)), improvements, 
                      color=['green' if x > 0 else 'red' for x in improvements])
        axes[0, 1].set_title('Calibration Improvement by Split')
        axes[0, 1].set_ylabel('Log Loss Improvement')
        axes[0, 1].axhline(y=0, color='black', linestyle='--', alpha=0.5)
        
        # Plot 3: Brier Score over time
        uncalibrated_brier = [r['uncalibrated_brier'] for r in split_results]
        calibrated_brier = [r['calibrated_brier'] for r in split_results]
        
        axes[1, 0].plot(periods, uncalibrated_brier, 'r-', label='Uncalibrated', marker='o')
        axes[1, 0].plot(periods, calibrated_brier, 'b-', label='Calibrated', marker='s')
        axes[1, 0].set_title('Brier Score Over Time')
        axes[1, 0].set_ylabel('Brier Score')
        axes[1, 0].legend()
        axes[1, 0].tick_params(axis='x', rotation=45)
        
        # Plot 4: Performance metrics history
        if self.calibration_metrics['log_loss']:
            axes[1, 1].plot(self.calibration_metrics['log_loss'], 'b-', label='Log Loss')
            axes[1, 1].plot(self.calibration_metrics['reliability'], 'r-', label='Reliability')
            axes[1, 1].plot(self.calibration_metrics['resolution'], 'g-', label='Resolution')
            axes[1, 1].set_title('Calibration Metrics History')
            axes[1, 1].set_ylabel('Metric Value')
            axes[1, 1].legend()
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Calibration visualization saved to {save_path}")
        
        return fig
    
    def auto_retrain_check(self, recent_performance: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check if automatic retraining is needed based on performance decay.
        
        Args:
            recent_performance: Recent performance metrics
            
        Returns:
            Dict with retrain recommendation and reasoning
        """
        if not self.auto_retrain:
            return {'retrain_needed': False, 'reason': 'Auto-retrain disabled'}
        
        retrain_needed = False
        reasons = []
        
        # Check log loss decay
        if recent_performance.get('decay_detected', False):
            retrain_needed = True
            reasons.append(f"Log loss increased by {recent_performance['log_loss_increase']:.4f}")
        
        # Check reliability degradation
        reliability = recent_performance.get('reliability', 0)
        if reliability > 0.02:  # High miscalibration
            retrain_needed = True
            reasons.append(f"Poor reliability: {reliability:.4f}")
        
        # Check sample size
        if recent_performance.get('n_recent_samples', 0) < self.min_samples_per_window:
            reasons.append("Insufficient recent samples for reliable assessment")
        
        return {
            'retrain_needed': retrain_needed,
            'reasons': reasons,
            'current_log_loss': recent_performance.get('current_log_loss'),
            'baseline_log_loss': self.baseline_log_loss,
            'recommendation': 'retrain_immediately' if retrain_needed else 'continue_monitoring'
        }
    
    def save_calibrator(self, calibrator, path: str) -> None:
        """Save calibrator to disk."""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'wb') as f:
            pickle.dump({
                'calibrator': calibrator,
                'metadata': {
                    'created': datetime.now(),
                    'baseline_log_loss': self.baseline_log_loss,
                    'current_log_loss': self.current_log_loss,
                    'calibration_history': self.calibration_history[-10:]  # Last 10 entries
                }
            }, f)
        logger.info(f"Calibrator saved to {path}")
    
    def load_calibrator(self, path: str) -> Any:
        """Load calibrator from disk."""
        with open(path, 'rb') as f:
            data = pickle.load(f)
            calibrator = data['calibrator']
            metadata = data['metadata']
            
            # Restore state
            self.baseline_log_loss = metadata.get('baseline_log_loss')
            self.current_log_loss = metadata.get('current_log_loss')
            if 'calibration_history' in metadata:
                self.calibration_history.extend(metadata['calibration_history'])
            
            logger.info(f"Calibrator loaded from {path}")
            return calibrator


def integrate_temporal_calibration(base_model, historical_data: pd.DataFrame) -> TemporalConfidenceCalibrator:
    """
    Integration function to set up temporal calibration for the existing model.
    
    Args:
        base_model: Existing PredictionModel instance
        historical_data: Historical match data with timestamps
        
    Returns:
        Configured TemporalConfidenceCalibrator
    """
    logger.info("Integrating temporal confidence calibration...")
    
    # Initialize calibrator
    calibrator = TemporalConfidenceCalibrator(
        window_size_months=2,
        test_size_months=1,
        min_samples_per_window=50,
        decay_threshold=0.05,
        auto_retrain=True
    )
    
    # This would be called during model training/setup
    logger.info("Temporal confidence calibration system ready for integration")
    return calibrator