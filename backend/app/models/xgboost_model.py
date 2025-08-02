import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional
import logging
import joblib
import os
import json
from datetime import datetime
import shap
import xgboost as xgb
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import accuracy_score, log_loss, roc_auc_score, classification_report
from sklearn.preprocessing import StandardScaler
import optuna
import warnings
warnings.filterwarnings('ignore', category=UserWarning)

logger = logging.getLogger(__name__)

class XGBoostPredictionModel:
    """
    Enhanced XGBoost-based prediction model with SHAP explainability,
    hyperparameter optimization, and A/B testing capabilities.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or self._get_default_config()
        self.model = None
        self.scaler = StandardScaler()
        self.explainer = None
        self.is_trained = False
        self.feature_names = self._get_feature_names()
        self.performance_metrics = {}
        self.hyperparameters = None
        
        # Model versioning and persistence
        self.model_version = "1.0.0"
        self.model_dir = os.path.join(os.path.dirname(__file__), '../../models')
        os.makedirs(self.model_dir, exist_ok=True)
        
        # Initialize or load model
        if self.config.get('auto_train', True):
            self._initialize_model()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration for XGBoost model"""
        return {
            'auto_train': True,
            'use_hyperopt': True,
            'n_trials': 100,
            'cv_folds': 5,
            'test_size': 0.2,
            'random_state': 42,
            'enable_shap': True,
            'model_persistence': True,
            'performance_tracking': True,
            'calibration_method': 'isotonic',
            'early_stopping_rounds': 10,
            'verbose': False
        }
    
    def _get_feature_names(self) -> List[str]:
        """Define consistent feature names for the model"""
        return [
            'avg_kills', 'avg_assists', 'std_dev_kills', 'std_dev_assists',
            'maps_played', 'longterm_kills_avg', 'longterm_assists_avg',
            'form_z_score', 'form_deviation_ratio', 'position_factor',
            'sample_size_score', 'avg_deaths', 'avg_damage', 'avg_vision',
            'avg_cs', 'avg_gold_at_10', 'avg_xp_at_10', 'avg_cs_at_10',
            'avg_gold_diff_15', 'avg_xp_diff_15', 'avg_cs_diff_15'
        ]
    
    def _initialize_model(self):
        """Initialize the model with training"""
        logger.info("Initializing XGBoost prediction model...")
        
        # Try to load existing model first
        if self.config.get('model_persistence', True):
            if self._load_model():
                logger.info("Loaded existing XGBoost model")
                return
        
        # Train new model if loading failed
        self._train_model()
    
    def _train_model(self):
        """Train the XGBoost model with hyperparameter optimization"""
        logger.info("Training XGBoost model with hyperparameter optimization...")
        
        # Generate training data
        X, y, sample_weights = self._generate_real_training_data()
        
        if len(X) == 0:
            logger.warning("No training data available, using fallback model")
            self._create_fallback_model()
            return
        
        # Log training data statistics
        logger.info(f"Training data shape: {X.shape}")
        logger.info(f"Class balance - OVER: {np.sum(y)} ({np.mean(y)*100:.1f}%), UNDER: {len(y)-np.sum(y)} ({(1-np.mean(y))*100:.1f}%)")
        
        # Split data
        X_train, X_test, y_train, y_test, w_train, w_test = train_test_split(
            X, y, sample_weights, 
            test_size=self.config['test_size'], 
            random_state=self.config['random_state'], 
            stratify=y
        )
        
        # Hyperparameter optimization
        if self.config.get('use_hyperopt', True):
            best_params = self._optimize_hyperparameters(X_train, y_train, w_train)
        else:
            best_params = self._get_default_hyperparameters()
        
        self.hyperparameters = best_params
        logger.info(f"Best hyperparameters: {best_params}")
        
        # Train final model with best parameters
        self.model = self._train_final_model(X_train, y_train, w_train, X_test, y_test, best_params)
        
        # Evaluate model
        self._evaluate_model(X_test, y_test, w_test)
        
        # Initialize SHAP explainer
        if self.config.get('enable_shap', True):
            self._initialize_shap_explainer(X_train)
        
        # Save model
        if self.config.get('model_persistence', True):
            self._save_model()
        
        self.is_trained = True
        logger.info("XGBoost model training completed successfully")
    
    def _optimize_hyperparameters(self, X_train: np.ndarray, y_train: np.ndarray, 
                                sample_weights: np.ndarray) -> Dict[str, Any]:
        """Optimize hyperparameters using Optuna"""
        logger.info("Starting hyperparameter optimization...")
        
        def objective(trial):
            # Define hyperparameter search space
            params = {
                'n_estimators': trial.suggest_int('n_estimators', 100, 1000),
                'max_depth': trial.suggest_int('max_depth', 3, 10),
                'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3),
                'min_child_weight': trial.suggest_int('min_child_weight', 1, 10),
                'subsample': trial.suggest_float('subsample', 0.6, 1.0),
                'colsample_bytree': trial.suggest_float('colsample_bytree', 0.6, 1.0),
                'gamma': trial.suggest_float('gamma', 0, 0.5),
                'reg_alpha': trial.suggest_float('reg_alpha', 0, 1.0),
                'reg_lambda': trial.suggest_float('reg_lambda', 0, 1.0),
                'random_state': self.config['random_state'],
                'objective': 'binary:logistic',
                'eval_metric': 'logloss',
                'verbosity': 0
            }
            
            # Cross-validation
            kf = StratifiedKFold(n_splits=self.config['cv_folds'], shuffle=True, 
                               random_state=self.config['random_state'])
            
            cv_scores = []
            for train_idx, val_idx in kf.split(X_train, y_train):
                X_fold_train, X_fold_val = X_train[train_idx], X_train[val_idx]
                y_fold_train, y_fold_val = y_train[train_idx], y_train[val_idx]
                w_fold_train = sample_weights[train_idx]
                
                # Train model
                model = xgb.XGBClassifier(**params)
                model.fit(X_fold_train, y_fold_train, sample_weight=w_fold_train,
                         eval_set=[(X_fold_val, y_fold_val)],
                         early_stopping_rounds=self.config['early_stopping_rounds'],
                         verbose=False)
                
                # Predict and score
                y_pred_proba = model.predict_proba(X_fold_val)[:, 1]
                score = log_loss(y_fold_val, y_pred_proba)
                cv_scores.append(score)
            
            return np.mean(cv_scores)
        
        # Run optimization
        study = optuna.create_study(direction='minimize')
        study.optimize(objective, n_trials=self.config['n_trials'], show_progress_bar=False)
        
        logger.info(f"Hyperparameter optimization completed. Best value: {study.best_value:.4f}")
        return study.best_params
    
    def _get_default_hyperparameters(self) -> Dict[str, Any]:
        """Get default hyperparameters for XGBoost"""
        return {
            'n_estimators': 500,
            'max_depth': 6,
            'learning_rate': 0.1,
            'min_child_weight': 1,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'gamma': 0,
            'reg_alpha': 0,
            'reg_lambda': 1,
            'random_state': self.config['random_state'],
            'objective': 'binary:logistic',
            'eval_metric': 'logloss',
            'verbosity': 0
        }
    
    def _train_final_model(self, X_train: np.ndarray, y_train: np.ndarray, 
                          sample_weights: np.ndarray, X_val: np.ndarray, 
                          y_val: np.ndarray, params: Dict[str, Any]) -> xgb.XGBClassifier:
        """Train the final XGBoost model with calibration"""
        
        # Train base XGBoost model
        base_model = xgb.XGBClassifier(**params)
        base_model.fit(
            X_train, y_train, 
            sample_weight=sample_weights,
            eval_set=[(X_val, y_val)],
            early_stopping_rounds=self.config['early_stopping_rounds'],
            verbose=self.config['verbose']
        )
        
        # Calibrate probabilities
        calibrated_model = CalibratedClassifierCV(
            base_model,
            cv='prefit',
            method=self.config['calibration_method']
        )
        
        # Fit calibration on validation set
        calibrated_model.fit(X_val, y_val)
        
        return calibrated_model
    
    def _evaluate_model(self, X_test: np.ndarray, y_test: np.ndarray, 
                       sample_weights: np.ndarray):
        """Evaluate model performance and store metrics"""
        
        # Make predictions
        y_pred = self.model.predict(X_test)
        y_pred_proba = self.model.predict_proba(X_test)[:, 1]
        
        # Calculate metrics
        accuracy = accuracy_score(y_test, y_pred)
        log_loss_score = log_loss(y_test, y_pred_proba)
        roc_auc = roc_auc_score(y_test, y_pred_proba)
        
        # Store performance metrics
        self.performance_metrics = {
            'accuracy': accuracy,
            'log_loss': log_loss_score,
            'roc_auc': roc_auc,
            'training_date': datetime.now().isoformat(),
            'model_version': self.model_version,
            'sample_size': len(X_test),
            'class_balance': {
                'over_rate': np.mean(y_test),
                'under_rate': 1 - np.mean(y_test)
            }
        }
        
        # Log performance
        logger.info(f"Model Performance:")
        logger.info(f"  Accuracy: {accuracy:.4f}")
        logger.info(f"  Log Loss: {log_loss_score:.4f}")
        logger.info(f"  ROC AUC: {roc_auc:.4f}")
        
        # Detailed classification report
        if self.config['verbose']:
            logger.info(f"Classification Report:\n{classification_report(y_test, y_pred)}")
    
    def _initialize_shap_explainer(self, X_train: np.ndarray):
        """Initialize SHAP explainer for model interpretability"""
        try:
            # Use TreeExplainer for XGBoost
            if hasattr(self.model, 'estimators_'):
                # For CalibratedClassifierCV, get the base estimator
                base_model = self.model.calibrated_classifiers_[0].estimator
            else:
                base_model = self.model
            
            # Sample data for faster SHAP computation
            sample_size = min(100, len(X_train))
            sample_indices = np.random.choice(len(X_train), sample_size, replace=False)
            X_sample = X_train[sample_indices]
            
            self.explainer = shap.TreeExplainer(base_model)
            
            # Pre-compute SHAP values for background
            self.background_shap_values = self.explainer.shap_values(X_sample)
            
            logger.info("SHAP explainer initialized successfully")
            
        except Exception as e:
            logger.warning(f"Failed to initialize SHAP explainer: {e}")
            self.explainer = None
    
    def get_feature_importance(self, top_k: int = 10) -> Dict[str, float]:
        """Get feature importance with SHAP values"""
        if not self.is_trained:
            raise ValueError("Model must be trained before getting feature importance")
        
        if self.explainer is None:
            # Fallback to XGBoost built-in feature importance
            if hasattr(self.model, 'estimators_'):
                base_model = self.model.calibrated_classifiers_[0].estimator
            else:
                base_model = self.model
            
            importance_dict = base_model.get_booster().get_score(importance_type='weight')
            
            # Map feature indices to names
            feature_importance = {}
            for i, importance in enumerate(base_model.feature_importances_):
                if i < len(self.feature_names):
                    feature_importance[self.feature_names[i]] = importance
            
        else:
            # Use SHAP values for more accurate feature importance
            shap_values = np.abs(self.background_shap_values).mean(0)
            feature_importance = {
                name: float(importance) 
                for name, importance in zip(self.feature_names, shap_values)
            }
        
        # Sort by importance and return top_k
        sorted_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)
        return dict(sorted_features[:top_k])
    
    def explain_prediction(self, features: Dict[str, float]) -> Dict[str, Any]:
        """Explain a single prediction using SHAP"""
        if not self.is_trained:
            raise ValueError("Model must be trained before explaining predictions")
        
        if self.explainer is None:
            return {"error": "SHAP explainer not available"}
        
        # Prepare feature vector
        feature_vector = self._prepare_features(features)
        
        try:
            # Get SHAP values
            shap_values = self.explainer.shap_values(feature_vector)
            
            # Create explanation dictionary
            explanation = {
                'shap_values': {
                    name: float(value) 
                    for name, value in zip(self.feature_names, shap_values[0])
                },
                'expected_value': float(self.explainer.expected_value),
                'prediction_impact': {},
                'top_positive_features': [],
                'top_negative_features': []
            }
            
            # Calculate prediction impact
            for name, shap_value in explanation['shap_values'].items():
                explanation['prediction_impact'][name] = {
                    'shap_value': shap_value,
                    'feature_value': features.get(name, 0),
                    'impact': 'positive' if shap_value > 0 else 'negative'
                }
            
            # Get top contributing features
            sorted_shap = sorted(explanation['shap_values'].items(), key=lambda x: x[1], reverse=True)
            explanation['top_positive_features'] = [
                {'feature': name, 'impact': value} 
                for name, value in sorted_shap[:5] if value > 0
            ]
            explanation['top_negative_features'] = [
                {'feature': name, 'impact': value} 
                for name, value in sorted_shap[-5:] if value < 0
            ]
            
            return explanation
            
        except Exception as e:
            logger.error(f"Error generating SHAP explanation: {e}")
            return {"error": f"Failed to generate explanation: {str(e)}"}
    
    def _save_model(self):
        """Save the trained model and metadata"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save model
        model_path = os.path.join(self.model_dir, f'xgboost_model_{timestamp}.joblib')
        joblib.dump(self.model, model_path)
        
        # Save metadata
        metadata = {
            'model_version': self.model_version,
            'training_date': datetime.now().isoformat(),
            'hyperparameters': self.hyperparameters,
            'performance_metrics': self.performance_metrics,
            'feature_names': self.feature_names,
            'config': self.config
        }
        
        metadata_path = os.path.join(self.model_dir, f'xgboost_metadata_{timestamp}.json')
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # Update latest model symlinks
        latest_model_path = os.path.join(self.model_dir, 'latest_xgboost_model.joblib')
        latest_metadata_path = os.path.join(self.model_dir, 'latest_xgboost_metadata.json')
        
        # Create symlinks or copy files (Windows compatible)
        try:
            if os.path.exists(latest_model_path):
                os.remove(latest_model_path)
            if os.path.exists(latest_metadata_path):
                os.remove(latest_metadata_path)
            
            # Copy files as fallback
            import shutil
            shutil.copy2(model_path, latest_model_path)
            shutil.copy2(metadata_path, latest_metadata_path)
            
        except Exception as e:
            logger.warning(f"Failed to create latest model links: {e}")
        
        logger.info(f"Model saved: {model_path}")
    
    def _load_model(self) -> bool:
        """Load existing model and metadata"""
        try:
            model_path = os.path.join(self.model_dir, 'latest_xgboost_model.joblib')
            metadata_path = os.path.join(self.model_dir, 'latest_xgboost_metadata.json')
            
            if not (os.path.exists(model_path) and os.path.exists(metadata_path)):
                return False
            
            # Load model
            self.model = joblib.load(model_path)
            
            # Load metadata
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            self.hyperparameters = metadata.get('hyperparameters', {})
            self.performance_metrics = metadata.get('performance_metrics', {})
            self.model_version = metadata.get('model_version', '1.0.0')
            
            # Initialize SHAP if enabled
            if self.config.get('enable_shap', True):
                # We need training data to initialize SHAP, so we'll do it lazily
                pass
            
            self.is_trained = True
            logger.info(f"Loaded model from {model_path}")
            return True
            
        except Exception as e:
            logger.warning(f"Failed to load existing model: {e}")
            return False
    
    def _create_fallback_model(self):
        """Create a simple fallback model when training data is insufficient"""
        logger.warning("Creating fallback XGBoost model with synthetic data")
        
        # Generate minimal synthetic data
        n_samples = 1000
        X = np.random.normal(0, 1, (n_samples, len(self.feature_names)))
        y = np.random.choice([0, 1], n_samples, p=[0.6, 0.4])  # Slight under bias
        
        # Train simple model
        self.model = xgb.XGBClassifier(**self._get_default_hyperparameters())
        self.model.fit(X, y)
        
        # Calibrate
        self.model = CalibratedClassifierCV(self.model, cv=3, method='isotonic')
        self.model.fit(X, y)
        
        self.is_trained = True
        self.performance_metrics = {'accuracy': 0.6, 'note': 'fallback_model'}
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get comprehensive model information"""
        info = {
            'model_type': 'XGBoost with Calibration',
            'model_version': self.model_version,
            'is_trained': self.is_trained,
            'feature_count': len(self.feature_names),
            'feature_names': self.feature_names,
            'performance_metrics': self.performance_metrics,
            'hyperparameters': self.hyperparameters,
            'config': self.config,
            'shap_available': self.explainer is not None
        }
        
        if self.performance_metrics:
            info['last_trained'] = self.performance_metrics.get('training_date', 'Unknown')
        
        return info
    
    def predict(self, features: Dict[str, float], prop_value: float, 
               sample_details: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generate prediction with enhanced XGBoost model capabilities
        """
        # Call parent method for base prediction
        base_result = super().predict(features, prop_value, sample_details)
        
        # Add XGBoost-specific enhancements
        if self.is_trained and self.model:
            
            # Get feature importance for this prediction
            feature_importance = self.get_feature_importance(top_k=5)
            
            # Get SHAP explanation if available
            explanation = None
            if self.config.get('enable_shap', True):
                explanation = self.explain_prediction(features)
            
            # Add enhanced information to result
            base_result.update({
                'model_type': 'XGBoost',
                'model_version': self.model_version,
                'feature_importance': feature_importance,
                'shap_explanation': explanation,
                'model_performance': {
                    'accuracy': self.performance_metrics.get('accuracy', None),
                    'roc_auc': self.performance_metrics.get('roc_auc', None)
                }
            })
        
        return base_result

    def compare_with_baseline(self, features: Dict[str, float], prop_value: float,
                            baseline_model: Any, sample_details: Dict[str, Any] = None) -> Dict[str, Any]:
        """Compare XGBoost prediction with baseline Random Forest model"""
        
        # Get predictions from both models
        xgb_result = self.predict(features, prop_value, sample_details)
        baseline_result = baseline_model.predict(features, prop_value, sample_details)
        
        # Compare results
        comparison = {
            'xgboost_prediction': {
                'prediction': xgb_result['prediction'],
                'confidence': xgb_result['confidence'],
                'expected_stat': xgb_result['expected_stat']
            },
            'baseline_prediction': {
                'prediction': baseline_result['prediction'],
                'confidence': baseline_result['confidence'],
                'expected_stat': baseline_result['expected_stat']
            },
            'agreement': xgb_result['prediction'] == baseline_result['prediction'],
            'confidence_difference': abs(xgb_result['confidence'] - baseline_result['confidence']),
            'expected_stat_difference': abs(xgb_result['expected_stat'] - baseline_result['expected_stat']),
            'recommended_model': 'xgboost' if xgb_result['confidence'] > baseline_result['confidence'] else 'baseline'
        }
        
        # Add model performance comparison if available
        if hasattr(self, 'performance_metrics') and hasattr(baseline_model, 'performance_metrics'):
            comparison['model_performance_comparison'] = {
                'xgboost_accuracy': self.performance_metrics.get('accuracy', None),
                'baseline_accuracy': getattr(baseline_model, 'performance_metrics', {}).get('accuracy', None)
            }
        
        return comparison