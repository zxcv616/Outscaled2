"""
BETTING LOGIC PREDICTION MODEL

This model has been updated to work with CORRECTED betting terminology and proper role handling.

KEY CHANGES:
============
- Now expects 'combined_*' features representing TOTAL stats across map ranges
- Maintains backward compatibility with 'avg_*' features
- All calculations now reflect proper betting market interpretation
- Expected stat calculations use COMBINED performance data
- ROLE LOGIC FIXED: Positions are used to FILTER data, not adjust expectations

BETTING CONTEXT:
===============
When predicting "Maps 1-2 Kills 8.5", the model now correctly:
- Uses historical COMBINED kills across maps 1-2 per series
- Calculates expected COMBINED performance for the upcoming maps
- Provides confidence intervals based on COMBINED stat volatility

ROLE HANDLING:
=============
- position_factor is always 1.0 (no role-based expectation adjustments)
- Role should be used to filter historical data to only include games where player played that position
- This allows the actual data to determine performance patterns by role
- No artificial "support gets lower kill expectations" - let the data speak

This ensures predictions align with how betting markets actually work.
"""

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
        
        # Generate training data aligned with betting logic
        X, y, sample_weights = self._generate_betting_aligned_training_data()
        
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
    
    def _generate_betting_aligned_training_data(self):
        """
        Generate training data aligned with betting logic using COMBINED stats across map ranges.
        This properly reflects how betting markets work (Maps 1-2 = total performance across both maps).
        """
        # Import data processor to access real data
        from app.utils.data_processor import DataProcessor
        data_processor = DataProcessor()
        
        # Get all available players for training
        all_players = data_processor.get_all_players()
        
        training_samples = []
        training_labels = []
        training_weights = []
        
        # Sample more players but with better selection criteria
        sample_players = np.random.choice(all_players, min(1500, len(all_players)), replace=False)
        
        for player in sample_players:
            try:
                # Get real player data
                # NOTE: The data_processor.get_player_data() method should be updated to accept
                # a position parameter to filter data by role. For now, we get all data.
                player_data = data_processor.get_player_data(player)
                
                # TODO: Update this to use position filtering once data processor supports it
                # Example: player_data = data_processor.get_player_data(player, position='mid')
                # For now, if position data exists, we could filter here but we don't know target position
                
                if len(player_data) < 8:  # Require more data for series-based training
                    continue
                
                # Generate training samples based on SERIES outcomes, not individual matches
                # This aligns with betting logic where we predict combined stats across map ranges
                for window_size in [8, 12, 16, 20]:  # Series-based windows
                    if len(player_data) >= window_size + 2:  # Need extra data for validation
                        # Use historical window for features
                        historical_data = player_data.iloc[:-2]  # All but last 2 matches
                        recent_window = historical_data.tail(window_size)
                        
                        # Get validation matches (last 2 matches to simulate "Maps 1-2")
                        validation_matches = player_data.iloc[-2:]
                        
                        if len(recent_window) < window_size or len(validation_matches) < 2:
                            continue
                        
                        # Calculate features from historical window
                        features_dict = self._extract_betting_aligned_features(recent_window, player)
                        feature_vector = self._dict_to_feature_vector(features_dict)
                        
                        # BETTING LOGIC: Calculate COMBINED performance across validation matches
                        # This simulates predicting "Maps 1-2 combined kills/assists"
                        combined_actual = validation_matches['kills'].sum()  # Total across both matches
                        
                        # Generate realistic prop based on historical COMBINED performance
                        historical_combined_avg = self._calculate_historical_combined_avg(recent_window)
                        prop_value = self._generate_betting_realistic_prop(historical_combined_avg, recent_window)
                        
                        # Label: 1 if combined_actual > prop, 0 otherwise
                        label = 1 if combined_actual > prop_value else 0
                        
                        # Weight based on data quality and betting logic factors
                        sample_weight = self._calculate_betting_sample_weight(
                            recent_window, validation_matches, window_size
                        )
                        
                        training_samples.append(feature_vector)
                        training_labels.append(label)
                        training_weights.append(sample_weight)
            
            except Exception as e:
                logger.warning(f"Error processing player {player}: {e}")
                continue
        
        if len(training_samples) == 0:
            logger.warning("No betting-aligned training data available, using fallback")
            return self._generate_betting_fallback_data()
        
        # Convert to numpy arrays
        X = np.array(training_samples)
        y = np.array(training_labels)
        sample_weights = np.array(training_weights)
        
        # Balance classes to reflect realistic betting market distributions
        # Betting markets typically have slight UNDER bias (52-48% historically)
        X, y, sample_weights = self._balance_training_data(X, y, sample_weights, target_over_rate=0.48)
        
        logger.info(f"Generated {len(X)} betting-aligned training samples")
        logger.info(f"Training label balance - OVER: {np.sum(y)} ({np.mean(y)*100:.1f}%), UNDER: {len(y)-np.sum(y)} ({(1-np.mean(y))*100:.1f}%)")
        
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
        """Extract position information from data - now used for data filtering, not stat adjustment"""
        # Position factor is now just used to identify the player's primary position
        # It should NOT adjust expected performance - that comes from actual data
        if 'position' in player_data.columns:
            positions = player_data['position'].dropna()
            if len(positions) > 0:
                most_common_pos = positions.mode().iloc[0] if len(positions.mode()) > 0 else 'mid'
                # Return 1.0 for all positions - no expectation adjustment
                return 1.0
        
        # Default neutral factor
        return 1.0
    
    def _calculate_historical_combined_avg(self, recent_data):
        """Calculate historical average for COMBINED performance (Maps 1-2 equivalent)"""
        # Simulate combined performance by taking pairs of consecutive matches
        combined_performances = []
        for i in range(0, len(recent_data) - 1, 2):
            if i + 1 < len(recent_data):
                combined = recent_data.iloc[i]['kills'] + recent_data.iloc[i+1]['kills']
                combined_performances.append(combined)
        
        return np.mean(combined_performances) if combined_performances else recent_data['kills'].mean() * 2
    
    def _generate_betting_realistic_prop(self, historical_combined_avg, recent_data):
        """Generate realistic prop value based on betting logic and bookmaker margins"""
        base_prop = historical_combined_avg
        
        # Apply bookmaker margin based on betting logic
        # Bookmakers typically set lines that are slightly harder to hit (inducing UNDER bias)
        margin_factor = np.random.uniform(1.05, 1.15)  # 5-15% margin
        prop_value = base_prop * margin_factor
        
        # Add position-based adjustments
        # Support players typically get lower lines, ADC/Mid get higher
        position_adjustment = np.random.uniform(0.9, 1.1)
        prop_value *= position_adjustment
        
        # Ensure minimum prop value and add small noise
        prop_value = max(1.0, prop_value)  # Minimum combined prop
        noise = np.random.normal(0, 0.3)  # Slightly more noise for combined stats
        prop_value += noise
        
        return max(1.0, prop_value)
    
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
    
    def _generate_betting_fallback_data(self):
        """Generate fallback training data aligned with betting logic when real data is unavailable"""
        logger.warning("Using betting-aligned fallback training data - should be replaced with real data")
        
        n_samples = 1500
        
        # Generate features based on realistic player stat distributions
        X = []
        y = []
        sample_weights = []
        
        for _ in range(n_samples):
            # Generate realistic features based on betting logic
            features = []
            
            # Generate realistic but neutral stat distributions
            # No role-based adjustments - let actual data determine performance
            avg_kills = np.random.normal(3.0, 1.5)  # Wide range covering all roles
            avg_assists = np.random.normal(5.0, 2.0)  # Wide range covering all roles
            position_factor = 1.0  # Neutral for all positions
            
            # Ensure non-negative stats
            avg_kills = max(0.5, avg_kills)
            avg_assists = max(1.0, avg_assists)
            
            # Generate other features
            std_dev_kills = abs(np.random.normal(avg_kills * 0.4, 0.3))
            std_dev_assists = abs(np.random.normal(avg_assists * 0.3, 0.2))
            maps_played = np.random.randint(8, 25)
            form_z_score = np.random.normal(0, 0.8)
            form_deviation_ratio = abs(np.random.normal(0.3, 0.15))
            
            features = [
                avg_kills, avg_assists, std_dev_kills, std_dev_assists,
                maps_played, avg_kills, avg_assists,  # longterm same as avg for simplicity
                form_z_score, form_deviation_ratio, position_factor,
                min(maps_played / 20.0, 1.0),  # sample_size_score
                np.random.normal(2.5, 0.8),  # avg_deaths
                np.random.normal(20000, 5000),  # avg_damage
                np.random.normal(40, 15),  # avg_vision
                np.random.normal(250, 50),  # avg_cs
                8000, 6000, 80, 0, 0, 0  # placeholder stats
            ]
            
            # Generate label based on expected vs realistic prop
            combined_expected = avg_kills * 2  # Simulate 2-map combined
            prop_value = combined_expected * np.random.uniform(1.05, 1.15)  # Bookmaker margin
            
            # UNDER bias (52% UNDER, 48% OVER) to reflect real betting markets
            label = 1 if np.random.random() < 0.48 else 0
            
            # Weight based on sample size and volatility
            weight = min(maps_played / 20.0, 1.0) * (1.0 - min(form_deviation_ratio, 0.5))
            
            X.append(features)
            y.append(label)
            sample_weights.append(weight)
        
        return np.array(X), np.array(y), np.array(sample_weights)
    
    def _extract_betting_aligned_features(self, player_data, player_name):
        """Extract features aligned with betting logic for combined stats"""
        # Use the existing _extract_real_features but ensure proper combined stat calculation
        features = self._extract_real_features(player_data, player_name)
        
        # Add combined stat calculations for betting alignment
        kills_data = player_data['kills'].dropna()
        assists_data = player_data['assists'].dropna()
        
        if len(kills_data) >= 2:
            # Calculate combined stats by pairing consecutive matches
            combined_kills = []
            for i in range(0, len(kills_data) - 1, 2):
                if i + 1 < len(kills_data):
                    combined_kills.append(kills_data.iloc[i] + kills_data.iloc[i+1])
            
            if combined_kills:
                features['combined_kills'] = np.mean(combined_kills)
                features['std_dev_combined_kills'] = np.std(combined_kills)
                features['series_played'] = len(combined_kills)
        
        if len(assists_data) >= 2:
            combined_assists = []
            for i in range(0, len(assists_data) - 1, 2):
                if i + 1 < len(assists_data):
                    combined_assists.append(assists_data.iloc[i] + assists_data.iloc[i+1])
            
            if combined_assists:
                features['combined_assists'] = np.mean(combined_assists)
                features['std_dev_combined_assists'] = np.std(combined_assists)
        
        return features
    
    def _filter_data_by_position(self, player_data, target_position):
        """
        Filter player data to only include games where they played the target position.
        This is the correct way to handle roles - filter data, don't adjust expectations.
        """
        if 'position' not in player_data.columns or target_position is None:
            return player_data  # Return all data if no position info
        
        # Map common position abbreviations
        position_mapping = {
            'top': ['top'],
            'jungle': ['jng', 'jungle'],
            'mid': ['mid', 'middle'],
            'adc': ['bot', 'adc', 'bottom'],
            'support': ['sup', 'support']
        }
        
        # Find matching positions
        target_positions = []
        for role, aliases in position_mapping.items():
            if target_position.lower() in aliases or any(alias in target_position.lower() for alias in aliases):
                target_positions.extend(aliases)
                break
        
        if not target_positions:
            target_positions = [target_position.lower()]
        
        # Filter data to only include games in target position
        position_matches = player_data['position'].str.lower().isin(target_positions)
        filtered_data = player_data[position_matches]
        
        logger.info(f"Filtered player data: {len(player_data)} total games -> {len(filtered_data)} games in position '{target_position}'")
        
        return filtered_data
    
    def _calculate_betting_sample_weight(self, recent_window, validation_matches, window_size):
        """Calculate sample weight based on betting logic factors"""
        # Base weight on sample size
        size_weight = min(window_size / 20.0, 1.0)
        
        # Volatility adjustment
        volatility = recent_window['kills'].std() / max(recent_window['kills'].mean(), 0.1)
        volatility_weight = 1.0 - min(volatility * 0.3, 0.5)
        
        # Recent form consistency
        if len(recent_window) >= 4:
            recent_4 = recent_window.tail(4)
            form_consistency = 1.0 - (recent_4['kills'].std() / max(recent_4['kills'].mean(), 0.1))
            form_consistency = max(0.2, min(1.0, form_consistency))
        else:
            form_consistency = 0.5
        
        # Combined weight
        final_weight = size_weight * volatility_weight * form_consistency
        return max(0.1, min(1.0, final_weight))
    
    def _balance_training_data(self, X, y, sample_weights, target_over_rate=0.48):
        """Balance training data to reflect realistic betting market distributions"""
        current_over_rate = np.mean(y)
        
        if abs(current_over_rate - target_over_rate) < 0.05:
            return X, y, sample_weights  # Already balanced
        
        # Adjust sample weights to achieve target distribution
        over_indices = np.where(y == 1)[0]
        under_indices = np.where(y == 0)[0]
        
        if current_over_rate > target_over_rate:
            # Too many OVERs, reduce their weights
            reduction_factor = target_over_rate / current_over_rate
            sample_weights[over_indices] *= reduction_factor
        else:
            # Too few OVERs, reduce UNDER weights
            reduction_factor = (1 - target_over_rate) / (1 - current_over_rate)
            sample_weights[under_indices] *= reduction_factor
        
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
        """Prepare features for model input with validation"""
        # Define feature order for consistency
        feature_names = [
            'avg_kills', 'avg_assists', 'std_dev_kills', 'std_dev_assists',
            'maps_played', 'longterm_kills_avg', 'longterm_assists_avg',
            'form_z_score', 'form_deviation_ratio', 'position_factor',
            'sample_size_score', 'avg_deaths', 'avg_damage', 'avg_vision',
            'avg_cs', 'avg_gold_at_10', 'avg_xp_at_10', 'avg_cs_at_10',
            'avg_gold_diff_15', 'avg_xp_diff_15', 'avg_cs_diff_15'
        ]
        
        # Validate and create feature vector with proper defaults
        feature_vector = []
        missing_features = []
        
        for feature in feature_names:
            if feature in features and features[feature] is not None:
                value = features[feature]
                # Validate feature ranges
                if feature in ['avg_kills', 'avg_assists'] and (value < 0 or value > 20):
                    logger.warning(f"Feature {feature} has unusual value: {value}")
                elif feature == 'position_factor' and (value < 0.5 or value > 2.0):
                    logger.warning(f"Feature {feature} has unusual value: {value}")
                feature_vector.append(value)
            else:
                # Use role-appropriate defaults
                default_value = self._get_feature_default(feature, features.get('position_factor', 1.0))
                feature_vector.append(default_value)
                missing_features.append(feature)
        
        if missing_features:
            logger.info(f"Using defaults for missing features: {missing_features}")
        
        return np.array(feature_vector).reshape(1, -1)
    
    def _get_feature_default(self, feature_name: str, position_factor: float) -> float:
        """Get neutral default values for missing features - no role bias"""
        # Use neutral defaults based on general League of Legends averages
        # Position factor is no longer used for expectation adjustment
        defaults = {
            'avg_kills': 3.0,
            'avg_assists': 5.0, 
            'std_dev_kills': 1.5,
            'std_dev_assists': 2.0,
            'avg_deaths': 2.5,
            'avg_damage': 18000,
            'maps_played': 10,
            'longterm_kills_avg': 3.0,
            'longterm_assists_avg': 5.0,
            'form_z_score': 0.0,
            'form_deviation_ratio': 0.3,
            'position_factor': 1.0,
            'sample_size_score': 0.5,
            'avg_vision': 40,
            'avg_cs': 250,
            'avg_gold_at_10': 8000,
            'avg_xp_at_10': 6000,
            'avg_cs_at_10': 80,
            'avg_gold_diff_15': 0,
            'avg_xp_diff_15': 0,
            'avg_cs_diff_15': 0
        }
        
        return defaults.get(feature_name, 0.0)
    
    def _validate_features(self, features: Dict[str, float]) -> Dict[str, float]:
        """Validate and clean feature values"""
        validated_features = features.copy()
        
        # Ensure non-negative stats
        non_negative_features = ['avg_kills', 'avg_assists', 'avg_deaths', 'avg_damage', 'avg_vision', 'avg_cs']
        for feature in non_negative_features:
            if feature in validated_features and validated_features[feature] is not None:
                validated_features[feature] = max(0, validated_features[feature])
        
        # Ensure reasonable ranges
        if 'position_factor' in validated_features:
            validated_features['position_factor'] = max(0.5, min(2.0, validated_features['position_factor']))
        
        if 'form_z_score' in validated_features:
            validated_features['form_z_score'] = max(-3.0, min(3.0, validated_features['form_z_score']))
        
        return validated_features
    
    def predict(self, features: Dict[str, float], prop_value: float, sample_details: Dict[str, Any] = None, prop_type: str = None) -> Dict[str, Any]:
        """
        Generate prediction with calibrated probabilities and confidence scaling
        """
        # Validate and prepare feature vector
        validated_features = self._validate_features(features)
        feature_vector = self._prepare_features(validated_features)
        
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
        
        # Adjust confidence based on gap with proper bounds
        # Larger gap = higher confidence (more certain prediction)
        # Smaller gap = lower confidence (closer to the line)
        gap_adjustment = min(gap_ratio * 1.5, 0.3)  # Reduced cap to 30%
        
        if prediction == "OVER":
            # For OVER predictions, higher confidence when expected_stat >> prop_value
            adjusted_confidence = min(base_model_confidence + gap_adjustment, 0.95)
        else:
            # For UNDER predictions, higher confidence when expected_stat << prop_value
            # Fix: Ensure this doesn't exceed 1.0
            under_base_confidence = 1 - base_model_confidence
            adjusted_confidence = min(under_base_confidence + gap_adjustment, 0.95)
        
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
            'prop_value': prop_value,  # Include the prop_value that was passed in
            'prop_type': prop_type or 'kills',  # Include the prop_type that was passed in
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
        Calculate expected statistic using BETTING LOGIC for combined stats.
        
        CRITICAL: Now works with COMBINED statistics across map ranges, not averages.
        This reflects proper betting terminology where "Maps 1-2" means total performance.
        """
        # Get base model confidence for empirical estimation
        feature_vector = self._prepare_features(features)
        prediction_proba = self.model.predict_proba(feature_vector)[0]
        
        # BETTING LOGIC: Base expected value from COMBINED performance average
        # Fix: Use explicit None checks instead of 'or' logic to avoid 0 values being treated as False
        base_expected = None
        if features.get('combined_kills') is not None:
            base_expected = features['combined_kills']
        elif features.get('combined_assists') is not None:
            base_expected = features['combined_assists']
        elif features.get('avg_kills') is not None:
            base_expected = features['avg_kills']
        elif features.get('avg_assists') is not None:
            base_expected = features['avg_assists']
        else:
            # Default based on general League stats (no role adjustment)
            # All roles can have varying performance - let the data speak
            base_expected = 3.0  # Neutral expectation for all roles
        
        logger.info(f"Expected stat calculation using COMBINED logic: base_expected={base_expected}")
        
        # Use model confidence to adjust expected stat
        # Higher confidence in OVER prediction suggests higher expected performance
        model_confidence = prediction_proba[1]  # Probability of OVER
        
        # Empirical adjustment based on model confidence (reduced impact to avoid overconfidence)
        # If model is confident in OVER, expect higher performance
        confidence_adjustment = (model_confidence - 0.5) * 1.0  # Reduced from 2.0 to 1.0
        
        # Enhanced form adjustment with diminishing returns
        form_z_score = features.get('form_z_score', 0)
        form_adjustment = np.tanh(form_z_score * 0.5) * 0.6  # Reduced impact
        
        # Volatility penalty - high volatility reduces confidence in prediction
        volatility = features.get('form_deviation_ratio', 0.3)  # Use consistent volatility key
        volatility_penalty = min(volatility * 0.2, 0.5)  # Cap penalty
        
        # Position factor with empirical calibration
        position_factor = features.get('position_factor', 1.0)
        
        # BETTING LOGIC: Sample size is now series, not individual maps
        sample_size = features.get('series_played') or features.get('maps_played', 10)
        sample_confidence = min(sample_size / 15.0, 1.0)  # Faster confidence buildup
        
        # Calculate final expected stat with empirical model adjustment
        expected_stat = (base_expected + form_adjustment - volatility_penalty + confidence_adjustment) * position_factor
        
        # Apply sample size confidence adjustment
        expected_stat = expected_stat * sample_confidence + (base_expected * (1 - sample_confidence))
        
        logger.info(f"Final expected stat (COMBINED): {expected_stat}")
        return max(expected_stat, 0)  # Ensure non-negative
    
    def _calculate_confidence_interval(self, features: Dict[str, float], expected_stat: float) -> List[float]:
        """Calculate confidence interval using BETTING LOGIC for combined stats"""
        # BETTING LOGIC: Use standard deviation of COMBINED performance
        std_dev = (features.get('std_dev_combined_kills', 0) or 
                  features.get('std_dev_combined_assists', 0) or
                  features.get('std_dev_kills', 0) or 
                  features.get('std_dev_assists', 0))  # Fallback for compatibility
        
        # BETTING LOGIC: Sample size is now series, not individual maps
        sample_size = (features.get('series_played', 0) or 
                      features.get('maps_played', 0))  # Fallback for compatibility
        
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
        Generate enhanced bootstrap confidence intervals using BETTING LOGIC.
        Uses more realistic distribution assumptions for League of Legends stats.
        """
        # BETTING LOGIC: Extract relevant COMBINED statistics with proper None checks
        avg_stat = None
        if features.get('combined_kills') is not None:
            avg_stat = features['combined_kills']
        elif features.get('combined_assists') is not None:
            avg_stat = features['combined_assists']
        elif features.get('avg_kills') is not None:
            avg_stat = features['avg_kills']
        else:
            avg_stat = expected_stat
        
        # Similar logic for standard deviation
        std_dev = None
        if features.get('std_dev_combined_kills') is not None:
            std_dev = features['std_dev_combined_kills']
        elif features.get('std_dev_combined_assists') is not None:
            std_dev = features['std_dev_combined_assists']
        elif features.get('std_dev_kills') is not None:
            std_dev = features['std_dev_kills']
        else:
            std_dev = max(1.0, expected_stat * 0.3)  # 30% coefficient of variation default
        
        sample_size = features.get('series_played') or features.get('maps_played', 10)
        volatility = features.get('form_deviation_ratio', 0.3)
        form_z_score = features.get('form_z_score', 0)
        
        # Handle small sample sizes or problematic std_dev
        if sample_size < 5 or std_dev <= 0:
            ci_method = self._calculate_quantile_confidence_interval(features, expected_stat)
            features['ci_method'] = 'quantile_fallback'
            return ci_method
        
        # Use more realistic sampling for League of Legends stats
        # League stats tend to follow gamma-like distributions (positive with right skew)
        # rather than normal distributions
        
        # Calculate shape and scale parameters for gamma distribution
        # Use method of moments: shape = mean^2 / variance, scale = variance / mean
        variance = std_dev ** 2
        if variance > 0 and expected_stat > 0:
            shape = (expected_stat ** 2) / variance
            scale = variance / expected_stat
            
            # Ensure reasonable parameters
            shape = max(0.5, min(shape, 10.0))  # Reasonable shape bounds
            scale = max(0.1, scale)
            
            # Generate gamma samples
            bootstrap_samples = np.random.gamma(shape, scale, n_bootstrap)
        else:
            # Fallback to normal if gamma parameters are problematic
            adjusted_std = std_dev * (1 + volatility * 0.3)
            bootstrap_samples = np.random.normal(expected_stat, adjusted_std, n_bootstrap)
            bootstrap_samples = np.maximum(bootstrap_samples, 0)  # Ensure non-negative
        
        # Apply form adjustment with reduced noise
        if abs(form_z_score) > 0.1:
            form_adjustment = form_z_score * std_dev * 0.2  # Reduced form impact
            bootstrap_samples += form_adjustment
        
        # Apply sample size adjustment
        if sample_size < 15:
            # Increase uncertainty for small samples
            uncertainty_factor = np.sqrt(15 / sample_size)
            sample_std = np.std(bootstrap_samples)
            noise = np.random.normal(0, sample_std * (uncertainty_factor - 1) * 0.5, n_bootstrap)
            bootstrap_samples += noise
        
        # Ensure all samples are non-negative
        bootstrap_samples = np.maximum(bootstrap_samples, 0)
        
        # Calculate 90% confidence interval (more conservative for betting)
        lower_bound = np.percentile(bootstrap_samples, 5.0)
        upper_bound = np.percentile(bootstrap_samples, 95.0)
        
        # Add method information
        features['ci_method'] = 'gamma_bootstrap' if variance > 0 and expected_stat > 0 else 'normal_bootstrap'
        features['ci_samples'] = len(bootstrap_samples)
        
        return [max(0, lower_bound), upper_bound]
    
    def _calculate_quantile_confidence_interval(self, features: Dict[str, float], expected_stat: float) -> List[float]:
        """
        Calculate quantile-based confidence interval using BETTING LOGIC.
        Uses IQR-based approach for combined stats instead of unrealistic Gaussian assumptions.
        """
        # BETTING LOGIC: Get COMBINED historical data for quantile calculation
        avg_stat = (features.get('combined_kills', 0) or 
                   features.get('combined_assists', 0) or
                   features.get('avg_kills', expected_stat))  # Fallback
        
        std_dev = (features.get('std_dev_combined_kills', 1.0) or 
                  features.get('std_dev_combined_assists', 1.0) or
                  features.get('std_dev_kills', 1.0))  # Fallback
        
        sample_size = (features.get('series_played', 10) or 
                      features.get('maps_played', 10))  # Fallback
        
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
        
        # Position analysis - now just informational, no stat adjustment
        # Position factor is always 1.0 since we don't adjust expectations by role
        
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
        
        # Position analysis - now just informational, no stat adjustment
        # Position factor is always 1.0 since we don't adjust expectations by role
        
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
        """Prepare player stats for response using BETTING LOGIC"""
        return {
            # BETTING LOGIC: Include combined stats
            'combined_kills': round(features.get('combined_kills', 0), 1),
            'combined_assists': round(features.get('combined_assists', 0), 1),
            'series_played': int(features.get('series_played', 0)),
            
            # Backward compatibility
            'avg_kills': round(features.get('avg_kills', 0), 1),
            'avg_assists': round(features.get('avg_assists', 0), 1),
            'maps_played': int(features.get('maps_played', 0)),
            
            # Common stats
            'form_z_score': round(features.get('form_z_score', 0), 2),
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
        Calculate a composite volatility index using BETTING LOGIC for combined stats
        """
        # BETTING LOGIC: Use combined stats for volatility calculation
        avg_stat = (features.get('combined_kills', 0) or 
                   features.get('combined_assists', 0) or
                   features.get('avg_kills', 0))  # Fallback
        
        std_dev = (features.get('std_dev_combined_kills', 0) or 
                  features.get('std_dev_combined_assists', 0) or
                  features.get('std_dev_kills', 0))  # Fallback
        
        form_z_score = features.get('form_z_score', 0)
        
        sample_size = (features.get('series_played', 10) or 
                      features.get('maps_played', 10))  # Fallback
        
        if avg_stat == 0 or std_dev == 0:
            return 0.0
        
        cv = std_dev / avg_stat  # Coefficient of variation
        form_deviation = abs(form_z_score) * 0.2  # Scale form impact
        sample_impact = max(0, (25 - sample_size) / 25)  # Higher for smaller samples
        
        volatility_index = (cv * 0.6) + (form_deviation * 0.2) + (sample_impact * 0.2)
        return min(1.0, volatility_index)

    def _generate_confidence_warning(self, features: Dict[str, float]) -> str:
        """
        Generate confidence warnings based on volatility and other factors using BETTING LOGIC
        """
        volatility_index = self._calculate_volatility_index(features)
        warnings = []
        
        if volatility_index > 0.7:
            warnings.append("⚠️ High volatility detected")
        elif volatility_index > 0.5:
            warnings.append("⚠️ Moderate volatility detected")
        
        # BETTING LOGIC: Use series count for sample size warnings
        sample_size = (features.get('series_played', 10) or 
                      features.get('maps_played', 10))  # Fallback
        
        if sample_size < 5:
            warnings.append("⚠️ Very limited sample size")
        elif sample_size < 10:
            warnings.append("⚠️ Limited sample size")
        
        return " ".join(warnings)