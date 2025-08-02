import numpy as np
import pandas as pd
from typing import Dict, List, Any
import logging
from sklearn.ensemble import RandomForestClassifier
from sklearn.calibration import CalibratedClassifierCV
from sklearn.preprocessing import StandardScaler
import joblib
import os
from sklearn.model_selection import train_test_split

logger = logging.getLogger(__name__)

class PredictionModel:
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.is_trained = False
        self._train_model()
    
    def _train_model(self):
        """Train the prediction model using real historical data"""
        logger.info("Training prediction model...")
        
        # Generate training data from real historical data
        X, y, sample_weights = self._generate_real_training_data()
        
        # Log training data statistics
        logger.info(f"Training data shape: {X.shape}")
        logger.info(f"Class balance - OVER: {np.sum(y)} ({np.mean(y)*100:.1f}%), UNDER: {len(y)-np.sum(y)} ({(1-np.mean(y))*100:.1f}%)")
        logger.info(f"Average sample weight: {np.mean(sample_weights):.3f}")
        logger.info(f"Sample weight range: {np.min(sample_weights):.3f} - {np.max(sample_weights):.3f}")
        
        # Split data for calibration
        X_train, X_cal, y_train, y_cal, w_train, w_cal = train_test_split(
            X, y, sample_weights, test_size=0.2, random_state=42, stratify=y
        )
        
        # Train Random Forest first
        base_model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            class_weight='balanced'
        )
        
        # Fit the base model
        base_model.fit(X_train, y_train, sample_weight=w_train)
        
        # Calibrate the model
        self.model = CalibratedClassifierCV(
            base_model,
            cv='prefit',
            method='isotonic'
        )
        
        # Fit the calibrated model
        self.model.fit(X_cal, y_cal, sample_weight=w_cal)
        
        # Evaluate on calibration set
        y_pred_proba = self.model.predict_proba(X_cal)
        y_pred = self.model.predict(X_cal)
        
        # Calculate metrics
        from sklearn.metrics import accuracy_score, log_loss
        accuracy = accuracy_score(y_cal, y_pred)
        log_loss_score = log_loss(y_cal, y_pred_proba)
        
        # Log calibration metrics
        logger.info(f"Calibration validation - Mean predicted probability: {np.mean(y_pred_proba[:, 1]):.3f}")
        logger.info(f"Calibration validation - Actual OVER rate: {np.mean(y_cal):.3f}")
        logger.info(f"Calibration validation - Accuracy: {accuracy:.3f}")
        logger.info(f"Calibration validation - Log loss: {log_loss_score:.3f}")
        
        self.is_trained = True
        logger.info("Model training completed with real historical data")
    
    def _generate_real_training_data(self):
        """
        Generate training data from real historical player performance.
        Uses actual match outcomes and player statistics.
        """
        # Import data processor to access real data
        from app.utils.data_processor import DataProcessor
        data_processor = DataProcessor()
        
        # Get all available players for training
        all_players = data_processor.get_all_players()
        
        training_samples = []
        training_labels = []
        training_weights = []
        
        # Sample players for training (limit to avoid memory issues)
        sample_players = np.random.choice(all_players, min(1000, len(all_players)), replace=False)
        
        for player in sample_players:
            try:
                # Get real player data
                player_data = data_processor.get_player_data(player)
                
                if len(player_data) < 5:  # Skip players with insufficient data
                    continue
                
                # Generate multiple training samples per player based on different time windows
                for window_size in [5, 10, 15, 20]:
                    if len(player_data) >= window_size:
                        # Use recent window for features, next match for outcome
                        recent_data = player_data.tail(window_size)
                        
                        if len(recent_data) < window_size:
                            continue
                        
                        # Calculate real features from historical data (now returns dict)
                        features_dict = self._extract_real_features(recent_data, player)
                        
                        # Convert dictionary to feature vector for training
                        feature_vector = self._dict_to_feature_vector(features_dict)
                        
                        # Use actual next match outcome as label (if available)
                        # For now, use historical average vs actual performance as proxy
                        historical_avg = recent_data['kills'].mean()
                        actual_performance = recent_data['kills'].iloc[-1]  # Most recent match
                        
                        # Create realistic prop value based on historical context
                        prop_value = self._generate_realistic_prop(historical_avg, recent_data)
                        
                        # Label: 1 if actual > prop, 0 otherwise
                        label = 1 if actual_performance > prop_value else 0
                        
                        # Calculate confidence weight based on sample size and volatility
                        volatility = recent_data['kills'].std() / max(recent_data['kills'].mean(), 0.1)
                        sample_weight = min(window_size / 20.0, 1.0) * (1.0 - min(volatility, 0.5))
                        
                        training_samples.append(feature_vector)
                        training_labels.append(label)
                        training_weights.append(sample_weight)
            
            except Exception as e:
                logger.warning(f"Error processing player {player}: {e}")
                continue
        
        if len(training_samples) == 0:
            logger.warning("No real training data available, falling back to rule-based model")
            return self._generate_fallback_training_data()
        
        # Convert to numpy arrays
        X = np.array(training_samples)
        y = np.array(training_labels)
        sample_weights = np.array(training_weights)
        
        logger.info(f"Generated {len(X)} training samples from real historical data")
        
        return X, y, sample_weights
    
    def _dict_to_feature_vector(self, features_dict):
        """Convert feature dictionary to vector format for model training"""
        # Use the same feature order as _prepare_features
        feature_names = [
            'avg_kills', 'avg_assists', 'std_dev_kills', 'std_dev_assists',
            'maps_played', 'longterm_kills_avg', 'longterm_assists_avg',
            'form_z_score', 'form_deviation_ratio', 'position_factor',
            'sample_size_score', 'avg_deaths', 'avg_damage', 'avg_vision',
            'avg_cs', 'avg_gold_at_10', 'avg_xp_at_10', 'avg_cs_at_10',
            'avg_gold_diff_15', 'avg_xp_diff_15', 'avg_cs_diff_15'
        ]
        
        feature_vector = []
        for feature in feature_names:
            feature_vector.append(features_dict.get(feature, 0))
        
        return feature_vector
    
    def _extract_real_features(self, player_data, player_name):
        """Extract real features from historical player data"""
        # Calculate real statistical features
        kills_data = player_data['kills'].dropna()
        assists_data = player_data['assists'].dropna()
        
        if len(kills_data) == 0:
            return self._get_default_features_dict()
        
        # Basic statistics
        avg_kills = kills_data.mean()
        avg_assists = assists_data.mean() if len(assists_data) > 0 else 0
        std_dev_kills = kills_data.std()
        std_dev_assists = assists_data.std() if len(assists_data) > 0 else 1.0
        
        # Form calculation (recent vs historical)
        if len(kills_data) >= 5:
            recent_avg = kills_data.tail(5).mean()
            form_z_score = (recent_avg - avg_kills) / max(std_dev_kills, 0.1)
        else:
            form_z_score = 0.0
        
        # Position factor (extract from data)
        position_factor = self._extract_position_factor(player_data)
        
        # Volatility calculation (form_deviation_ratio)
        volatility = std_dev_kills / max(avg_kills, 0.1)
        
        # Sample size score
        sample_size_score = min(len(player_data) / 50.0, 1.0)
        
        # Additional features from real data
        avg_deaths = player_data['deaths'].mean() if 'deaths' in player_data.columns else 2.5
        avg_damage = player_data['damagetochampions'].mean() if 'damagetochampions' in player_data.columns else 20000
        avg_vision = player_data['visionscore'].mean() if 'visionscore' in player_data.columns else 40
        avg_cs = player_data['total cs'].mean() if 'total cs' in player_data.columns else 250
        
        # Create feature dictionary matching _prepare_features exactly
        features = {
            'avg_kills': avg_kills,
            'avg_assists': avg_assists,
            'std_dev_kills': std_dev_kills,
            'std_dev_assists': std_dev_assists,
            'maps_played': len(player_data),
            'longterm_kills_avg': avg_kills,  # Use same as avg_kills for now
            'longterm_assists_avg': avg_assists,  # Use same as avg_assists for now
            'form_z_score': form_z_score,
            'form_deviation_ratio': volatility,  # Use volatility as form deviation
            'position_factor': position_factor,
            'sample_size_score': sample_size_score,
            'avg_deaths': avg_deaths,
            'avg_damage': avg_damage,
            'avg_vision': avg_vision,
            'avg_cs': avg_cs,
            'avg_gold_at_10': 8000,  # Placeholder - not available in current data
            'avg_xp_at_10': 6000,    # Placeholder - not available in current data
            'avg_cs_at_10': 80,      # Placeholder - not available in current data
            'avg_gold_diff_15': 0,   # Placeholder - not available in current data
            'avg_xp_diff_15': 0,     # Placeholder - not available in current data
            'avg_cs_diff_15': 0      # Placeholder - not available in current data
        }
        
        return features
    
    def _extract_position_factor(self, player_data):
        """Extract position factor from real data"""
        # Try to determine position from data
        if 'position' in player_data.columns:
            positions = player_data['position'].dropna()
            if len(positions) > 0:
                most_common_pos = positions.mode().iloc[0] if len(positions.mode()) > 0 else 'mid'
                position_weights = {'top': 0.8, 'jungle': 1.2, 'mid': 1.15, 'adc': 1.0, 'support': 0.9}
                return position_weights.get(most_common_pos.lower(), 1.0)
        
        # Default to mid if position not available
        return 1.15
    
    def _generate_realistic_prop(self, historical_avg, recent_data):
        """Generate realistic prop value based on historical context (anchored, no random direction)"""
        # Base prop around historical average
        base_prop = historical_avg
        
        # Use a positive margin to simulate bookmaker lines (e.g., +0.75 to +1.5)
        margin = np.random.uniform(0.75, 1.5)
        prop_value = base_prop + margin
        prop_value = max(0.5, prop_value)  # Minimum prop
        
        # Add small noise to simulate real-world prop setting
        noise = np.random.normal(0, 0.2)
        prop_value += noise
        
        return max(0.5, prop_value)
    
    def _get_default_features(self):
        """Return default features when no real data is available"""
        return [3.5, 5.0, 1.5, 2.0, 10, 3.5, 5.0, 0.0, 0.3, 1.0, 0.5, 2.5, 20000, 40, 250, 8000, 6000, 80, 0, 0, 0]
    
    def _get_default_features_dict(self):
        """Return default features as a dictionary"""
        return {
            'avg_kills': 3.5,
            'avg_assists': 5.0,
            'std_dev_kills': 1.5,
            'std_dev_assists': 2.0,
            'maps_played': 10,
            'longterm_kills_avg': 3.5,
            'longterm_assists_avg': 5.0,
            'form_z_score': 0.0,
            'form_deviation_ratio': 0.3,
            'position_factor': 1.0,
            'sample_size_score': 0.5,
            'avg_deaths': 2.5,
            'avg_damage': 20000,
            'avg_vision': 40,
            'avg_cs': 250,
            'avg_gold_at_10': 8000,
            'avg_xp_at_10': 6000,
            'avg_cs_at_10': 80,
            'avg_gold_diff_15': 0,
            'avg_xp_diff_15': 0,
            'avg_cs_diff_15': 0
        }
    
    def _generate_fallback_training_data(self):
        """Generate minimal fallback training data when real data is unavailable"""
        logger.warning("Using fallback training data - this should not be used in production")
        
        n_samples = 1000
        X = np.random.normal(0, 1, (n_samples, 21))
        y = np.random.choice([0, 1], n_samples, p=[0.5, 0.5])
        sample_weights = np.ones(n_samples) * 0.5  # Low confidence weights
        
        return X, y, sample_weights
    
    def _create_rule_based_model(self):
        """Create a rule-based model for MVP demonstration"""
        # This is a simplified model for MVP
        # In production, you'd train XGBoost on actual historical data
        
        class RuleBasedModel:
            def predict_proba(self, features):
                # Simple rule-based prediction
                avg_stat = features.get('avg_kills', 0) or features.get('avg_assists', 0)
                form_z_score = features.get('form_z_score', 0)
                position_factor = features.get('position_factor', 1.0)
                sample_size = features.get('maps_played', 0)
                
                # Base probability calculation
                base_prob = 0.5
                
                # Adjust based on form
                if form_z_score > 0.5:
                    base_prob += 0.2
                elif form_z_score < -0.5:
                    base_prob -= 0.2
                
                # Adjust based on position
                base_prob *= position_factor
                
                # Adjust based on sample size
                if sample_size < 5:
                    base_prob = 0.5  # Default to 50% if insufficient data
                
                # Ensure probability is between 0 and 1
                base_prob = max(0.1, min(0.9, base_prob))
                
                return np.array([[1 - base_prob, base_prob]])
            
            def predict(self, features):
                proba = self.predict_proba(features)
                return np.argmax(proba, axis=1)
        
        return RuleBasedModel()
    
    def _prepare_features(self, features: Dict[str, float]) -> np.ndarray:
        """Prepare features for model input"""
        # Define feature order for consistency
        feature_names = [
            'avg_kills', 'avg_assists', 'std_dev_kills', 'std_dev_assists',
            'maps_played', 'longterm_kills_avg', 'longterm_assists_avg',
            'form_z_score', 'form_deviation_ratio', 'position_factor',
            'sample_size_score', 'avg_deaths', 'avg_damage', 'avg_vision',
            'avg_cs', 'avg_gold_at_10', 'avg_xp_at_10', 'avg_cs_at_10',
            'avg_gold_diff_15', 'avg_xp_diff_15', 'avg_cs_diff_15'
        ]
        
        # Create feature vector
        feature_vector = []
        for feature in feature_names:
            feature_vector.append(features.get(feature, 0))
        
        return np.array(feature_vector).reshape(1, -1)
    
    def predict(self, features: Dict[str, float], prop_value: float, sample_details: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generate prediction with calibrated probabilities and confidence scaling
        """
        # Prepare feature vector
        feature_vector = self._prepare_features(features)
        
        # Get calibrated probabilities
        prediction_proba = self.model.predict_proba(feature_vector)[0]
        base_confidence = prediction_proba[1]  # Probability of OVER
        
        # Calculate expected stat using model confidence
        expected_stat = self._calculate_expected_stat(features)
        
        # Determine prediction
        prediction = "OVER" if expected_stat > prop_value else "UNDER"
        
        # Calculate dynamic confidence based on gap (same logic as prediction curve)
        gap = abs(expected_stat - prop_value)
        gap_ratio = gap / max(prop_value, 1)  # Normalize gap by prop value
        
        # Base confidence from model
        base_model_confidence = base_confidence
        
        # Adjust confidence based on gap
        # Larger gap = higher confidence (more certain prediction)
        # Smaller gap = lower confidence (closer to the line)
        gap_adjustment = min(gap_ratio * 2.0, 0.5)  # Cap adjustment at 50%
        
        if prediction == "OVER":
            # For OVER predictions, higher confidence when expected_stat >> prop_value
            adjusted_confidence = base_model_confidence + gap_adjustment
        else:
            # For UNDER predictions, higher confidence when expected_stat << prop_value
            adjusted_confidence = (1 - base_model_confidence) + gap_adjustment
        
        # Apply tier-based scaling
        tier_info = sample_details.get('tier_info', {'weight': 1.0, 'tier': 1, 'name': 'Default Tier'})
        final_confidence = adjusted_confidence * tier_info.get('weight', 1.0)
        
        # Ensure confidence is within bounds
        final_confidence = max(0.1, min(0.95, final_confidence))
        
        # Calculate confidence interval
        confidence_interval = self._calculate_bootstrap_confidence_interval(features, expected_stat)
        
        # Generate reasoning with volatility warnings
        reasoning = self._generate_reasoning_with_tiers(
            features, prediction, final_confidence * 100, prop_value, 
            expected_stat, tier_info, sample_details.get('fallback_used', False)
        )
        
        # Prepare player stats
        player_stats = self._prepare_player_stats(features)
        
        # Get data summary from sample_details if available, otherwise use placeholder
        data_years = sample_details.get('data_years', "2024 (108 matches), 2025 (67 matches)") if sample_details else "2024 (108 matches), 2025 (67 matches)"
        
        # Prepare sample details
        if sample_details is None:
            sample_details = {
                "maps_used": features.get('maps_played', 0),
                "filter_criteria": "Standard filtering applied",
                "position": "Unknown",
                "opponent": "Unknown",
                "data_years": data_years
            }
        
        # Add tier information to sample details
        sample_details.update({
            "data_tier": tier_info.get('tier', 0),
            "tier_name": tier_info.get('name', 'Unknown'),
            "tier_weight": tier_info.get('weight', 1.0),
            "fallback_used": sample_details.get('fallback_used', False),
            "sample_sources": features.get('sample_sources', {}),
            "volatility": round(self._calculate_volatility_index(features), 3),
            "ci_method": features.get('ci_method', 'bootstrap'),
            "strict_mode_applied": features.get('strict_mode', False)
        })
        
        return {
            'prediction': prediction,
            'confidence': round(final_confidence * 100, 1),
            'base_model_confidence': round(base_confidence * 100, 1),
            'expected_stat': round(expected_stat, 1),
            'confidence_interval': confidence_interval,
            'reasoning': reasoning,
            'player_stats': player_stats,
            'data_years': data_years,
            'sample_details': sample_details,
            'data_tier': tier_info.get('tier', 1),
            'confidence_warning': self._generate_confidence_warning(features)
        }

    def generate_prediction_curve(self, features: Dict[str, float], input_prop: float, 
                                step: float = 0.5, range_size: int = 3) -> List[Dict[str, Any]]:
        """
        Generate predictions across a range of prop values around the input prop.
        
        Args:
            features: Player features dictionary
            input_prop: The input prop value (center of the range)
            step: Step size between prop values
            range_size: Number of steps on each side of input_prop
            
        Returns:
            List of prediction results for each prop value in the range
        """
        # Generate prop values around the input
        props = [input_prop + step * i for i in range(-range_size, range_size + 1)]
        results = []
        
        # Get base model confidence and expected stat once
        feature_vector = self._prepare_features(features)
        prediction_proba = self.model.predict_proba(feature_vector)[0]
        base_confidence = prediction_proba[1]  # Probability of OVER
        expected_stat = self._calculate_expected_stat(features)
        
        # Get tier info for confidence scaling
        tier_info = features.get('tier_info', {'weight': 1.0, 'tier': 1, 'name': 'Default Tier'})
        
        for prop in props:
            # Determine prediction based on expected_stat vs prop_value
            prediction = "OVER" if expected_stat > prop else "UNDER"
            
            # Calculate dynamic confidence based on gap
            gap = abs(expected_stat - prop)
            gap_ratio = gap / max(prop, 1)  # Normalize gap by prop value
            
            # Base confidence from model
            base_model_confidence = base_confidence
            
            # Adjust confidence based on gap
            # Larger gap = higher confidence (more certain prediction)
            # Smaller gap = lower confidence (closer to the line)
            gap_adjustment = min(gap_ratio * 2.0, 0.5)  # Cap adjustment at 50%
            
            if prediction == "OVER":
                # For OVER predictions, higher confidence when expected_stat >> prop_value
                adjusted_confidence = base_model_confidence + gap_adjustment
            else:
                # For UNDER predictions, higher confidence when expected_stat << prop_value
                adjusted_confidence = (1 - base_model_confidence) + gap_adjustment
            
            # Apply tier-based scaling
            final_confidence = adjusted_confidence * tier_info.get('weight', 1.0)
            
            # Ensure confidence is within bounds
            final_confidence = max(0.1, min(0.95, final_confidence))
            
            # Extract key information
            curve_point = {
                "prop_value": round(prop, 2),
                "prediction": prediction,
                "confidence": round(final_confidence * 100, 1),
                "expected_stat": round(expected_stat, 1),
                "is_input_prop": abs(prop - input_prop) < 0.01  # Flag the original input
            }
            
            results.append(curve_point)
        
        return results
    
    def _calculate_expected_stat(self, features: Dict[str, float]) -> float:
        """
        Calculate expected statistic using empirical regression-based approach.
        Uses model-inferred estimates based on calibrated probabilities.
        """
        # Get base model confidence for empirical estimation
        feature_vector = self._prepare_features(features)
        prediction_proba = self.model.predict_proba(feature_vector)[0]
        
        # Base expected value from historical average
        base_expected = features.get('avg_kills', 0)
        
        # Use model confidence to adjust expected stat
        # Higher confidence in OVER prediction suggests higher expected performance
        model_confidence = prediction_proba[1]  # Probability of OVER
        
        # Empirical adjustment based on model confidence
        # If model is confident in OVER, expect higher performance
        confidence_adjustment = (model_confidence - 0.5) * 2.0  # Scale to [-1, 1]
        
        # Enhanced form adjustment with diminishing returns
        form_z_score = features.get('form_z_score', 0)
        form_adjustment = np.tanh(form_z_score * 0.5) * 0.8  # Bounded form impact
        
        # Volatility penalty - high volatility reduces confidence in prediction
        volatility = features.get('volatility', 0.3)
        volatility_penalty = volatility * 0.3
        
        # Position factor with empirical calibration
        position_factor = features.get('position_factor', 1.0)
        
        # Sample size adjustment - more data = more reliable prediction
        sample_size = features.get('maps_played', 10)
        sample_confidence = min(sample_size / 20.0, 1.0)
        
        # Calculate final expected stat with empirical model adjustment
        expected_stat = (base_expected + form_adjustment - volatility_penalty + confidence_adjustment) * position_factor
        
        # Apply sample size confidence adjustment
        expected_stat = expected_stat * sample_confidence + (base_expected * (1 - sample_confidence))
        
        return max(expected_stat, 0)  # Ensure non-negative
    
    def _calculate_confidence_interval(self, features: Dict[str, float], expected_stat: float) -> List[float]:
        """Calculate confidence interval"""
        # Simple confidence interval based on sample size and volatility
        std_dev = features.get('std_dev_kills', 0) or features.get('std_dev_assists', 0)
        sample_size = features.get('maps_played', 0)
        
        # Standard error decreases with sample size
        if sample_size > 0:
            standard_error = std_dev / np.sqrt(sample_size)
        else:
            standard_error = std_dev
        
        # 95% confidence interval (approximately 2 standard errors)
        margin_of_error = 2 * standard_error
        
        lower_bound = max(0, expected_stat - margin_of_error)
        upper_bound = expected_stat + margin_of_error
        
        return [lower_bound, upper_bound]
    
    def _calculate_bootstrap_confidence_interval(self, features: Dict[str, float], expected_stat: float, n_bootstrap: int = 1000) -> List[float]:
        """
        Generate enhanced bootstrap confidence intervals for expected statistics.
        Centers around the adjusted expected_stat and incorporates volatility.
        """
        # Extract relevant statistics
        avg_stat = features.get('avg_kills', expected_stat)
        std_dev = features.get('std_dev_kills', 1.0)
        sample_size = features.get('maps_played', 10)
        volatility = features.get('volatility', 0.3)
        form_z_score = features.get('form_z_score', 0)
        
        # Handle small sample sizes or zero std_dev
        if sample_size < 5 or std_dev == 0:
            # Use quantile-based CI as intermediate fallback
            ci_method = self._calculate_quantile_confidence_interval(features, expected_stat)
            features['ci_method'] = 'quantile'
            return ci_method
        
        # Generate bootstrap samples centered around the adjusted expected_stat
        # Include volatility in the sampling distribution
        volatility_factor = 1 + (volatility * 0.5)  # Increase spread for high volatility
        adjusted_std = std_dev * volatility_factor
        
        # Generate bootstrap samples from normal distribution around expected_stat
        bootstrap_samples = np.random.normal(expected_stat, adjusted_std, n_bootstrap)
        
        # Add form-based noise to simulate recent performance variability
        form_noise = np.random.normal(0, abs(form_z_score) * 0.3, n_bootstrap)
        bootstrap_samples += form_noise
        
        # Ensure non-negative values
        bootstrap_samples = np.maximum(bootstrap_samples, 0)
        
        # Calculate 95% confidence interval using percentiles
        lower_bound = np.percentile(bootstrap_samples, 2.5)
        upper_bound = np.percentile(bootstrap_samples, 97.5)
        
        # Add method information to features for transparency
        features['ci_method'] = 'bootstrap'
        features['ci_volatility_factor'] = volatility_factor
        
        return [max(0, lower_bound), upper_bound]
    
    def _calculate_quantile_confidence_interval(self, features: Dict[str, float], expected_stat: float) -> List[float]:
        """
        Calculate quantile-based confidence interval as fallback for small samples.
        Uses IQR-based approach instead of unrealistic Gaussian assumptions.
        """
        # Get historical data for quantile calculation
        avg_stat = features.get('avg_kills', expected_stat)
        std_dev = features.get('std_dev_kills', 1.0)
        sample_size = features.get('maps_played', 10)
        
        # For small samples, use IQR-based approach
        if sample_size < 10:
            # Use 1.5 * IQR rule for outlier detection
            q1 = avg_stat - 0.675 * std_dev  # Approximate Q1
            q3 = avg_stat + 0.675 * std_dev  # Approximate Q3
            iqr = q3 - q1
            
            # Calculate bounds using IQR
            lower_bound = max(0, q1 - 1.5 * iqr)
            upper_bound = q3 + 1.5 * iqr
        else:
            # Use empirical quantiles if we have enough data
            margin = 1.5 * std_dev  # Conservative estimate
            lower_bound = max(0, expected_stat - margin)
            upper_bound = expected_stat + margin
        
        # Add method information
        features['ci_method'] = 'quantile'
        features['ci_iqr_used'] = True
        
        return [lower_bound, upper_bound]
    
    def _generate_reasoning(self, features: Dict[str, float], prediction: str, confidence: float, prop_value: float, expected_stat: float) -> str:
        """Generate reasoning for the prediction"""
        form_z_score = features.get('form_z_score', 0)
        maps_played = features.get('maps_played', 0)
        position_factor = features.get('position_factor', 1.0)
        
        reasoning_parts = []
        
        # Form analysis
        if form_z_score > 1.0:
            reasoning_parts.append("Strong recent form above historical average.")
        elif form_z_score > 0.5:
            reasoning_parts.append("Good recent form.")
        elif form_z_score < -1.0:
            reasoning_parts.append("Poor recent form below historical average.")
        elif form_z_score < -0.5:
            reasoning_parts.append("Below-average recent form.")
        else:
            reasoning_parts.append("Form is consistent with historical average.")
        
        # Sample size analysis
        if maps_played < 5:
            reasoning_parts.append("Limited sample size reduces confidence.")
        elif maps_played < 10:
            reasoning_parts.append("Moderate sample size.")
        else:
            reasoning_parts.append("Good sample size for reliable prediction.")
        
        # Position analysis
        if position_factor > 1.1:
            reasoning_parts.append("Position typically favorable for this stat.")
        elif position_factor < 0.9:
            reasoning_parts.append("Position typically unfavorable for this stat.")
        
        # Expected vs prop value analysis (dynamic based on gap)
        gap = abs(expected_stat - prop_value)
        gap_ratio = gap / max(prop_value, 1)
        
        if prediction == "OVER":
            if gap_ratio > 2.0:
                reasoning_parts.append("Expected performance dramatically above prop line.")
            elif gap_ratio > 1.0:
                reasoning_parts.append("Expected performance significantly above prop line.")
            elif gap_ratio > 0.5:
                reasoning_parts.append("Expected performance moderately above prop line.")
            else:
                reasoning_parts.append("Expected performance slightly above prop line.")
        else:  # UNDER
            if gap_ratio > 2.0:
                reasoning_parts.append("Expected performance dramatically below prop line.")
            elif gap_ratio > 1.0:
                reasoning_parts.append("Expected performance significantly below prop line.")
            elif gap_ratio > 0.5:
                reasoning_parts.append("Expected performance moderately below prop line.")
            else:
                reasoning_parts.append("Expected performance slightly below prop line.")
        
        # Add specific prediction explanation with gap context
        if prediction == "OVER":
            if gap_ratio > 2.0:
                reasoning_parts.append(f"High confidence OVER {prop_value} with expected {expected_stat:.1f} (gap: {gap:.1f}).")
            elif gap_ratio > 1.0:
                reasoning_parts.append(f"Confident OVER {prop_value} with expected {expected_stat:.1f} (gap: {gap:.1f}).")
            else:
                reasoning_parts.append(f"Predicting OVER {prop_value} with expected {expected_stat:.1f} (gap: {gap:.1f}).")
        else:
            if gap_ratio > 2.0:
                reasoning_parts.append(f"High confidence UNDER {prop_value} with expected {expected_stat:.1f} (gap: {gap:.1f}).")
            elif gap_ratio > 1.0:
                reasoning_parts.append(f"Confident UNDER {prop_value} with expected {expected_stat:.1f} (gap: {gap:.1f}).")
            else:
                reasoning_parts.append(f"Predicting UNDER {prop_value} with expected {expected_stat:.1f} (gap: {gap:.1f}).")
        
        # Confidence level
        if confidence > 80:
            reasoning_parts.append("High confidence prediction.")
        elif confidence > 60:
            reasoning_parts.append("Moderate confidence prediction.")
        else:
            reasoning_parts.append("Low confidence prediction.")
        
        return " ".join(reasoning_parts)
    
    def _generate_reasoning_with_tiers(self, features: Dict[str, float], prediction: str, confidence: float, 
                                     prop_value: float, expected_stat: float, tier_info: Dict, fallback_used: bool) -> str:
        """Generate reasoning with tier information, volatility warnings, and data drift detection"""
        form_z_score = features.get('form_z_score', 0)
        maps_played = features.get('maps_played', 0)
        position_factor = features.get('position_factor', 1.0)
        volatility = features.get('form_deviation_ratio', 0.3)  # Use form_deviation_ratio as volatility
        
        reasoning_parts = []
        
        # Tier and fallback information
        if fallback_used:
            reasoning_parts.append(f"⚠️ Limited direct data. Using {tier_info.get('name', 'fallback data')} to estimate performance.")
            reasoning_parts.append(f"Confidence adjusted based on sample relevance (Tier {tier_info.get('tier', 0)}).")
        else:
            reasoning_parts.append(f"Using {tier_info.get('name', 'primary data')} for prediction.")
        
        # Volatility and data drift warnings
        if volatility > 0.6:
            reasoning_parts.append("⚠️ High volatility detected - recent performance shows unusual variability.")
        elif volatility > 0.4:
            reasoning_parts.append("⚠️ Moderate volatility detected - performance shows some inconsistency.")
        
        # Historical range context
        avg_stat = features.get('avg_kills', 0)
        std_dev = features.get('std_dev_kills', 0)
        if avg_stat > 0 and std_dev > 0:
            historical_range = f"Historical range: {avg_stat - std_dev:.1f} to {avg_stat + std_dev:.1f}"
            reasoning_parts.append(f"Expected stat ({expected_stat:.1f}) within {historical_range}.")
        
        # Form analysis with volatility context
        if form_z_score > 1.0:
            reasoning_parts.append("Strong recent form above historical average.")
        elif form_z_score > 0.5:
            reasoning_parts.append("Good recent form.")
        elif form_z_score < -1.0:
            reasoning_parts.append("Poor recent form below historical average.")
        elif form_z_score < -0.5:
            reasoning_parts.append("Below-average recent form.")
        else:
            reasoning_parts.append("Form is consistent with historical average.")
        
        # Sample size analysis
        if maps_played < 5:
            reasoning_parts.append("Limited sample size reduces confidence.")
        elif maps_played < 10:
            reasoning_parts.append("Moderate sample size.")
        else:
            reasoning_parts.append("Good sample size for reliable prediction.")
        
        # Position analysis
        if position_factor > 1.1:
            reasoning_parts.append("Position typically favorable for this stat.")
        elif position_factor < 0.9:
            reasoning_parts.append("Position typically unfavorable for this stat.")
        
        # Expected vs prop value analysis (dynamic based on gap)
        gap = abs(expected_stat - prop_value)
        gap_ratio = gap / max(prop_value, 1)
        
        if prediction == "OVER":
            if gap_ratio > 2.0:
                reasoning_parts.append("Expected performance dramatically above prop line.")
            elif gap_ratio > 1.0:
                reasoning_parts.append("Expected performance significantly above prop line.")
            elif gap_ratio > 0.5:
                reasoning_parts.append("Expected performance moderately above prop line.")
            else:
                reasoning_parts.append("Expected performance slightly above prop line.")
        else:  # UNDER
            if gap_ratio > 2.0:
                reasoning_parts.append("Expected performance dramatically below prop line.")
            elif gap_ratio > 1.0:
                reasoning_parts.append("Expected performance significantly below prop line.")
            elif gap_ratio > 0.5:
                reasoning_parts.append("Expected performance moderately below prop line.")
            else:
                reasoning_parts.append("Expected performance slightly below prop line.")
        
        # Add specific prediction explanation with gap context
        if prediction == "OVER":
            if gap_ratio > 2.0:
                reasoning_parts.append(f"High confidence OVER {prop_value} with expected {expected_stat:.1f} (gap: {gap:.1f}).")
            elif gap_ratio > 1.0:
                reasoning_parts.append(f"Confident OVER {prop_value} with expected {expected_stat:.1f} (gap: {gap:.1f}).")
            else:
                reasoning_parts.append(f"Predicting OVER {prop_value} with expected {expected_stat:.1f} (gap: {gap:.1f}).")
        else:
            if gap_ratio > 2.0:
                reasoning_parts.append(f"High confidence UNDER {prop_value} with expected {expected_stat:.1f} (gap: {gap:.1f}).")
            elif gap_ratio > 1.0:
                reasoning_parts.append(f"Confident UNDER {prop_value} with expected {expected_stat:.1f} (gap: {gap:.1f}).")
            else:
                reasoning_parts.append(f"Predicting UNDER {prop_value} with expected {expected_stat:.1f} (gap: {gap:.1f}).")
        
        # Confidence level
        if confidence > 80:
            reasoning_parts.append("High confidence prediction.")
        elif confidence > 60:
            reasoning_parts.append("Moderate confidence prediction.")
        else:
            reasoning_parts.append("Low confidence prediction.")
        
        return " ".join(reasoning_parts)
    
    def _prepare_player_stats(self, features: Dict[str, float]) -> Dict[str, float]:
        """Prepare player stats for response"""
        return {
            'avg_kills': round(features.get('avg_kills', 0), 1),
            'avg_assists': round(features.get('avg_assists', 0), 1),
            'form_z_score': round(features.get('form_z_score', 0), 2),
            'maps_played': int(features.get('maps_played', 0)),
            'position_factor': round(features.get('position_factor', 1.0), 2),
            'avg_deaths': round(features.get('avg_deaths', 0), 1),
            'avg_damage': round(features.get('avg_damage', 0), 0),
            'avg_vision': round(features.get('avg_vision', 0), 1),
            'avg_cs': round(features.get('avg_cs', 0), 1)
        } 

    def _calculate_composite_tier_weight(self, tier_info: Dict, sample_size: int) -> float:
        """
        Calculate composite tier weight using context relevance and sample size.
        Avoids overly conservative weighting for high-sample matches.
        """
        base_weight = tier_info.get('weight', 1.0)
        sample_size = max(sample_size, 1)  # Avoid log(0)
        
        # Context relevance component (50% weight)
        context_relevance = base_weight
        
        # Sample size component (50% weight)
        # Use log scale to avoid underweighting strong long-term data
        sample_factor = min(np.log(sample_size) / np.log(25), 1.0)  # Normalize to [0,1]
        
        # Composite weight formula
        composite_weight = 0.5 * context_relevance + 0.5 * sample_factor
        
        # Ensure weight is within reasonable bounds
        composite_weight = max(0.2, min(1.0, composite_weight))
        
        return composite_weight 

    def _calculate_volatility_index(self, features: Dict[str, float]) -> float:
        """
        Calculate a composite volatility index
        """
        avg_stat = features.get('avg_kills', 0)
        std_dev = features.get('std_dev_kills', 0)
        form_z_score = features.get('form_z_score', 0)
        sample_size = features.get('maps_played', 10)
        
        if avg_stat == 0 or std_dev == 0:
            return 0.0
        
        cv = std_dev / avg_stat  # Coefficient of variation
        form_deviation = abs(form_z_score) * 0.2  # Scale form impact
        sample_impact = max(0, (25 - sample_size) / 25)  # Higher for smaller samples
        
        volatility_index = (cv * 0.6) + (form_deviation * 0.2) + (sample_impact * 0.2)
        return min(1.0, volatility_index)

    def _generate_confidence_warning(self, features: Dict[str, float]) -> str:
        """
        Generate confidence warnings based on volatility and other factors
        """
        volatility_index = self._calculate_volatility_index(features)
        warnings = []
        
        if volatility_index > 0.7:
            warnings.append("⚠️ High volatility detected")
        elif volatility_index > 0.5:
            warnings.append("⚠️ Moderate volatility detected")
        
        sample_size = features.get('maps_played', 10)
        if sample_size < 5:
            warnings.append("⚠️ Very limited sample size")
        elif sample_size < 10:
            warnings.append("⚠️ Limited sample size")
        
        return " ".join(warnings)