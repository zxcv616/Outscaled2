import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple, Optional
import logging
from datetime import datetime, timedelta
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity
import joblib
import os
from scipy import stats
from collections import defaultdict, deque

logger = logging.getLogger(__name__)

class AdvancedFeatureEngineer:
    """
    Advanced feature engineering system for sports analytics with temporal, 
    contextual, and embedding-based features.
    """
    
    def __init__(self, data_processor=None):
        self.data_processor = data_processor
        self.player_embeddings = {}
        self.meta_game_tracker = {}
        self.team_synergy_cache = {}
        self.feature_importance_cache = {}
        self._initialize_feature_store()
    
    def _initialize_feature_store(self):
        """Initialize feature store and cached computations"""
        self.feature_store = {
            'temporal_features': {},
            'player_embeddings': {},
            'meta_features': {},
            'synergy_features': {},
            'cached_computations': {}
        }
        logger.info("Advanced Feature Engineer initialized")
    
    # ==================== TEMPORAL MOMENTUM FEATURES ====================
    
    def extract_temporal_features(self, player_data: pd.DataFrame, player_name: str, 
                                prop_type: str) -> Dict[str, float]:
        """
        Extract comprehensive temporal momentum features including rolling windows,
        streaks, and performance acceleration.
        """
        temporal_features = {}
        
        if player_data.empty:
            return self._get_default_temporal_features()
        
        # Sort by date to ensure proper temporal order
        if 'date' in player_data.columns:
            player_data = player_data.sort_values('date')
        
        stat_column = prop_type
        stat_values = player_data[stat_column].dropna()
        
        if len(stat_values) < 3:
            return self._get_default_temporal_features()
        
        # Rolling Window Features (3, 7, 14 games)
        temporal_features.update(self._calculate_rolling_windows(stat_values))
        
        # Momentum and Streak Features
        temporal_features.update(self._calculate_momentum_features(stat_values))
        
        # Performance Acceleration
        temporal_features.update(self._calculate_acceleration_features(stat_values))
        
        # Temporal Volatility
        temporal_features.update(self._calculate_temporal_volatility(stat_values))
        
        # Recency Weighted Features
        temporal_features.update(self._calculate_recency_weighted_features(stat_values))
        
        # Trend Analysis
        temporal_features.update(self._calculate_trend_features(stat_values))
        
        logger.info(f"Extracted {len(temporal_features)} temporal features for {player_name}")
        return temporal_features
    
    def _calculate_rolling_windows(self, stat_values: pd.Series) -> Dict[str, float]:
        """Calculate rolling window averages and statistics"""
        features = {}
        
        # Rolling averages
        for window in [3, 7, 14]:
            if len(stat_values) >= window:
                rolling_avg = stat_values.tail(window).mean()
                rolling_std = stat_values.tail(window).std()
                rolling_min = stat_values.tail(window).min()
                rolling_max = stat_values.tail(window).max()
                
                features[f'rolling_{window}_avg'] = rolling_avg
                features[f'rolling_{window}_std'] = rolling_std
                features[f'rolling_{window}_range'] = rolling_max - rolling_min
                features[f'rolling_{window}_cv'] = rolling_std / max(rolling_avg, 0.1)
            else:
                # Use available data if window is larger than data
                available_data = stat_values.tail(len(stat_values))
                features[f'rolling_{window}_avg'] = available_data.mean()
                features[f'rolling_{window}_std'] = available_data.std()
                features[f'rolling_{window}_range'] = available_data.max() - available_data.min()
                features[f'rolling_{window}_cv'] = available_data.std() / max(available_data.mean(), 0.1)
        
        # Rolling window comparisons
        if len(stat_values) >= 7:
            recent_3 = stat_values.tail(3).mean()
            older_7 = stat_values.tail(7).head(4).mean() if len(stat_values) >= 7 else recent_3
            features['short_vs_medium_trend'] = (recent_3 - older_7) / max(older_7, 0.1)
        
        if len(stat_values) >= 14:
            recent_7 = stat_values.tail(7).mean()
            older_14 = stat_values.tail(14).head(7).mean()
            features['medium_vs_long_trend'] = (recent_7 - older_14) / max(older_14, 0.1)
        
        return features
    
    def _calculate_momentum_features(self, stat_values: pd.Series) -> Dict[str, float]:
        """Calculate momentum indicators and streak detection"""
        features = {}
        
        # Streak detection
        if len(stat_values) >= 5:
            recent_values = stat_values.tail(5)
            overall_avg = stat_values.mean()
            
            # Current streak (consecutive games above/below average)
            current_streak = 0
            for val in reversed(recent_values):
                if val > overall_avg:
                    if current_streak >= 0:
                        current_streak += 1
                    else:
                        break
                else:
                    if current_streak <= 0:
                        current_streak -= 1
                    else:
                        break
            
            features['current_streak'] = current_streak
            features['streak_strength'] = abs(current_streak) / 5.0  # Normalize to 0-1
        
        # Hot/Cold streaks
        if len(stat_values) >= 3:
            recent_3 = stat_values.tail(3)
            avg_stat = stat_values.mean()
            
            hot_games = sum(1 for val in recent_3 if val > avg_stat * 1.2)
            cold_games = sum(1 for val in recent_3 if val < avg_stat * 0.8)
            
            features['hot_streak_intensity'] = hot_games / 3.0
            features['cold_streak_intensity'] = cold_games / 3.0
        
        # Momentum score (weighted recent performance)
        if len(stat_values) >= 5:
            weights = np.array([0.4, 0.3, 0.2, 0.1])  # Recent games weighted more
            recent_4 = stat_values.tail(4)
            if len(recent_4) == 4:
                weighted_avg = np.average(recent_4, weights=weights)
                overall_avg = stat_values.mean()
                features['momentum_score'] = (weighted_avg - overall_avg) / max(overall_avg, 0.1)
        
        return features
    
    def _calculate_acceleration_features(self, stat_values: pd.Series) -> Dict[str, float]:
        """Calculate performance acceleration and trend changes"""
        features = {}
        
        if len(stat_values) < 4:
            return features
        
        # Calculate first and second derivatives (acceleration)
        values = stat_values.values
        
        # First derivative (velocity)
        velocity = np.diff(values)
        if len(velocity) > 0:
            features['performance_velocity'] = np.mean(velocity[-3:]) if len(velocity) >= 3 else np.mean(velocity)
        
        # Second derivative (acceleration)
        if len(velocity) > 1:
            acceleration = np.diff(velocity)
            features['performance_acceleration'] = np.mean(acceleration[-2:]) if len(acceleration) >= 2 else np.mean(acceleration)
        
        # Trend strength
        if len(stat_values) >= 5:
            x = np.arange(len(stat_values))
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, stat_values)
            features['trend_slope'] = slope
            features['trend_strength'] = abs(r_value)
            features['trend_significance'] = 1 - p_value if p_value < 0.05 else 0
        
        return features
    
    def _calculate_temporal_volatility(self, stat_values: pd.Series) -> Dict[str, float]:
        """Calculate various volatility measures over time"""
        features = {}
        
        if len(stat_values) < 3:
            return features
        
        # Rolling volatility
        for window in [3, 7]:
            if len(stat_values) >= window:
                rolling_vol = stat_values.tail(window).std()
                rolling_mean = stat_values.tail(window).mean()
                features[f'volatility_{window}'] = rolling_vol / max(rolling_mean, 0.1)
        
        # Volatility of volatility (second-order)
        if len(stat_values) >= 6:
            vol_3_series = []
            for i in range(3, len(stat_values) + 1):
                window_data = stat_values.iloc[i-3:i]
                vol_3_series.append(window_data.std())
            if len(vol_3_series) > 1:
                features['volatility_of_volatility'] = np.std(vol_3_series)
        
        # Consistency score (inverse of coefficient of variation)
        cv = stat_values.std() / max(stat_values.mean(), 0.1)
        features['consistency_score'] = 1 / (1 + cv)  # Transform to 0-1 range
        
        return features
    
    def _calculate_recency_weighted_features(self, stat_values: pd.Series) -> Dict[str, float]:
        """Calculate features with exponential decay weights favoring recent games"""
        features = {}
        
        if len(stat_values) < 2:
            return features
        
        # Exponential weights (more recent = higher weight)
        n = len(stat_values)
        decay_rate = 0.9
        weights = np.array([decay_rate ** (n - i - 1) for i in range(n)])
        weights = weights / weights.sum()  # Normalize
        
        # Weighted statistics
        weighted_mean = np.average(stat_values, weights=weights)
        features['recency_weighted_avg'] = weighted_mean
        
        # Weighted volatility
        weighted_var = np.average((stat_values - weighted_mean) ** 2, weights=weights)
        features['recency_weighted_volatility'] = np.sqrt(weighted_var)
        
        # Compare recent vs historical
        overall_avg = stat_values.mean()
        features['recency_bias'] = (weighted_mean - overall_avg) / max(overall_avg, 0.1)
        
        return features
    
    def _calculate_trend_features(self, stat_values: pd.Series) -> Dict[str, float]:
        """Calculate trend analysis features"""
        features = {}
        
        if len(stat_values) < 4:
            return features
        
        # Linear trend
        x = np.arange(len(stat_values))
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, stat_values)
        
        features['linear_trend_slope'] = slope
        features['linear_trend_r2'] = r_value ** 2
        features['trend_reliability'] = 1 - p_value if p_value < 0.05 else 0
        
        # Quadratic trend (for acceleration/deceleration)
        if len(stat_values) >= 6:
            x_quad = np.column_stack([x**2, x, np.ones(len(x))])
            try:
                coeffs = np.linalg.lstsq(x_quad, stat_values, rcond=None)[0]
                features['quadratic_trend_coeff'] = coeffs[0]  # x^2 coefficient
                features['linear_component'] = coeffs[1]       # x coefficient
            except:
                features['quadratic_trend_coeff'] = 0
                features['linear_component'] = slope
        
        return features
    
    def _get_default_temporal_features(self) -> Dict[str, float]:
        """Default temporal features when insufficient data"""
        return {
            'rolling_3_avg': 0, 'rolling_7_avg': 0, 'rolling_14_avg': 0,
            'rolling_3_std': 1, 'rolling_7_std': 1, 'rolling_14_std': 1,
            'rolling_3_cv': 0.3, 'rolling_7_cv': 0.3, 'rolling_14_cv': 0.3,
            'current_streak': 0, 'momentum_score': 0, 'performance_velocity': 0,
            'performance_acceleration': 0, 'trend_slope': 0, 'trend_strength': 0,
            'volatility_3': 0.3, 'volatility_7': 0.3, 'consistency_score': 0.5,
            'recency_weighted_avg': 0, 'recency_bias': 0, 'linear_trend_r2': 0
        }
    
    # ==================== PLAYER EMBEDDING FEATURES ====================
    
    def generate_player_embeddings(self, all_player_data: pd.DataFrame) -> Dict[str, np.ndarray]:
        """
        Generate player style embeddings using PCA on performance patterns.
        Creates similarity-based features for player comparison.
        """
        if all_player_data.empty:
            return {}
        
        logger.info("Generating player embeddings...")
        
        # Feature columns for embedding
        feature_cols = [
            'kills', 'assists', 'deaths', 'damagetochampions', 'visionscore',
            'total cs', 'goldat10', 'xpat10', 'csat10'
        ]
        
        # Filter available columns
        available_cols = [col for col in feature_cols if col in all_player_data.columns]
        
        if len(available_cols) < 3:
            logger.warning("Insufficient columns for player embeddings")
            return {}
        
        # Aggregate player statistics
        player_profiles = all_player_data.groupby('playername')[available_cols].agg([
            'mean', 'std', 'median'
        ]).round(3)
        
        # Flatten column names
        player_profiles.columns = ['_'.join(col).strip() for col in player_profiles.columns.values]
        
        # Handle missing values
        player_profiles = player_profiles.fillna(player_profiles.mean())
        
        if len(player_profiles) < 5:
            logger.warning("Too few players for meaningful embeddings")
            return {}
        
        # Standardize features
        scaler = StandardScaler()
        scaled_features = scaler.fit_transform(player_profiles)
        
        # Apply PCA for dimensionality reduction
        n_components = min(8, scaled_features.shape[1], scaled_features.shape[0])
        pca = PCA(n_components=n_components)
        embeddings = pca.fit_transform(scaled_features)
        
        # Store embeddings
        player_embeddings = {}
        for i, player in enumerate(player_profiles.index):
            player_embeddings[player] = embeddings[i]
        
        self.player_embeddings = player_embeddings
        logger.info(f"Generated embeddings for {len(player_embeddings)} players")
        
        return player_embeddings
    
    def extract_player_similarity_features(self, target_player: str, 
                                         player_embeddings: Dict[str, np.ndarray]) -> Dict[str, float]:
        """Extract features based on player similarity analysis"""
        features = {}
        
        if target_player not in player_embeddings or len(player_embeddings) < 2:
            return self._get_default_similarity_features()
        
        target_embedding = player_embeddings[target_player]
        
        # Calculate similarities to all other players
        similarities = []
        for other_player, other_embedding in player_embeddings.items():
            if other_player != target_player:
                similarity = cosine_similarity([target_embedding], [other_embedding])[0][0]
                similarities.append(similarity)
        
        if not similarities:
            return self._get_default_similarity_features()
        
        similarities = np.array(similarities)
        
        # Similarity-based features
        features['avg_player_similarity'] = np.mean(similarities)
        features['max_player_similarity'] = np.max(similarities)
        features['min_player_similarity'] = np.min(similarities)
        features['similarity_std'] = np.std(similarities)
        
        # Player uniqueness (inverse of average similarity)
        features['player_uniqueness'] = 1 - np.mean(similarities)
        
        # Find player archetype (cluster analysis)
        if len(player_embeddings) >= 5:
            all_embeddings = np.array(list(player_embeddings.values()))
            
            # Simple clustering
            try:
                n_clusters = min(5, len(player_embeddings) // 2)
                kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
                cluster_labels = kmeans.fit_predict(all_embeddings)
                
                # Find target player's cluster
                player_names = list(player_embeddings.keys())
                target_idx = player_names.index(target_player)
                target_cluster = cluster_labels[target_idx]
                
                features['player_archetype'] = target_cluster
                features['archetype_size'] = np.sum(cluster_labels == target_cluster)
                
                # Distance to cluster center
                cluster_center = kmeans.cluster_centers_[target_cluster]
                features['distance_to_archetype'] = np.linalg.norm(target_embedding - cluster_center)
                
            except Exception as e:
                logger.warning(f"Clustering failed: {e}")
                features['player_archetype'] = 0
                features['archetype_size'] = 1
                features['distance_to_archetype'] = 0
        
        return features
    
    def _get_default_similarity_features(self) -> Dict[str, float]:
        """Default similarity features"""
        return {
            'avg_player_similarity': 0.5,
            'max_player_similarity': 0.7,
            'min_player_similarity': 0.3,
            'similarity_std': 0.1,
            'player_uniqueness': 0.5,
            'player_archetype': 0,
            'archetype_size': 1,
            'distance_to_archetype': 0
        }
    
    # ==================== OPPONENT AND MATCHUP FEATURES ====================
    
    def extract_opponent_adjustment_features(self, player_data: pd.DataFrame, 
                                           opponent: str = None) -> Dict[str, float]:
        """Extract opponent-specific performance adjustment features"""
        features = {}
        
        if player_data.empty:
            return self._get_default_opponent_features()
        
        # Overall vs opponent performance
        if opponent and 'opponent' in player_data.columns:
            opponent_data = player_data[player_data['opponent'] == opponent]
            overall_data = player_data
            
            if len(opponent_data) > 0:
                # Performance vs specific opponent
                for stat in ['kills', 'assists', 'deaths']:
                    if stat in player_data.columns:
                        opponent_avg = opponent_data[stat].mean()
                        overall_avg = overall_data[stat].mean()
                        
                        if overall_avg > 0:
                            features[f'{stat}_vs_opponent_ratio'] = opponent_avg / overall_avg
                        else:
                            features[f'{stat}_vs_opponent_ratio'] = 1.0
                
                features['opponent_sample_size'] = len(opponent_data)
            else:
                # No specific opponent data
                for stat in ['kills', 'assists', 'deaths']:
                    features[f'{stat}_vs_opponent_ratio'] = 1.0
                features['opponent_sample_size'] = 0
        
        # Team strength analysis
        if 'opponent' in player_data.columns:
            opponents = player_data['opponent'].value_counts()
            
            # Opponent diversity
            features['opponent_diversity'] = len(opponents) / max(len(player_data), 1)
            
            # Average opponent strength (based on frequency as proxy)
            if len(opponents) > 0:
                # More frequent opponents might be stronger teams
                avg_opponent_strength = opponents.mean() / len(player_data)
                features['avg_opponent_strength'] = avg_opponent_strength
            else:
                features['avg_opponent_strength'] = 0.5
        
        # Head-to-head record features
        if opponent and 'result' in player_data.columns:
            h2h_data = player_data[player_data.get('opponent', '') == opponent]
            if len(h2h_data) > 0:
                wins = h2h_data['result'].str.contains('win|victory', case=False, na=False).sum()
                features['h2h_win_rate'] = wins / len(h2h_data)
                features['h2h_games'] = len(h2h_data)
            else:
                features['h2h_win_rate'] = 0.5
                features['h2h_games'] = 0
        
        return features
    
    def _get_default_opponent_features(self) -> Dict[str, float]:
        """Default opponent features"""
        return {
            'kills_vs_opponent_ratio': 1.0,
            'assists_vs_opponent_ratio': 1.0,
            'deaths_vs_opponent_ratio': 1.0,
            'opponent_sample_size': 0,
            'opponent_diversity': 0.5,
            'avg_opponent_strength': 0.5,
            'h2h_win_rate': 0.5,
            'h2h_games': 0
        }
    
    # ==================== META-GAME TRACKING ====================
    
    def extract_meta_game_features(self, player_data: pd.DataFrame, 
                                 current_patch: str = None) -> Dict[str, float]:
        """Extract meta-game adaptation and patch-specific features"""
        features = {}
        
        if player_data.empty:
            return self._get_default_meta_features()
        
        # Patch adaptation analysis
        if 'patch' in player_data.columns and current_patch:
            current_patch_data = player_data[player_data['patch'] == current_patch]
            
            if len(current_patch_data) > 0:
                # Current patch performance
                for stat in ['kills', 'assists']:
                    if stat in player_data.columns:
                        patch_avg = current_patch_data[stat].mean()
                        overall_avg = player_data[stat].mean()
                        
                        if overall_avg > 0:
                            features[f'{stat}_patch_adaptation'] = patch_avg / overall_avg
                        else:
                            features[f'{stat}_patch_adaptation'] = 1.0
                
                features['current_patch_games'] = len(current_patch_data)
            else:
                # No games on current patch
                for stat in ['kills', 'assists']:
                    features[f'{stat}_patch_adaptation'] = 1.0
                features['current_patch_games'] = 0
        
        # Champion pool analysis
        if 'champion' in player_data.columns:
            champion_counts = player_data['champion'].value_counts()
            
            # Champion pool diversity
            features['champion_pool_size'] = len(champion_counts)
            features['champion_diversity'] = len(champion_counts) / max(len(player_data), 1)
            
            # Meta champion usage
            if len(champion_counts) > 0:
                most_played = champion_counts.iloc[0]
                features['main_champion_rate'] = most_played / len(player_data)
                
                # One-trick vs flexible player
                if features['main_champion_rate'] > 0.7:
                    features['player_flexibility'] = 0.3  # One-trick
                elif features['main_champion_rate'] > 0.5:
                    features['player_flexibility'] = 0.6  # Semi-flexible
                else:
                    features['player_flexibility'] = 1.0  # Very flexible
            else:
                features['main_champion_rate'] = 0
                features['player_flexibility'] = 0.5
        
        # Meta adaptation speed
        if 'date' in player_data.columns and len(player_data) >= 10:
            # Analyze performance improvement over time
            player_data_sorted = player_data.sort_values('date')
            
            # Compare first half vs second half performance
            midpoint = len(player_data_sorted) // 2
            first_half = player_data_sorted.iloc[:midpoint]
            second_half = player_data_sorted.iloc[midpoint:]
            
            for stat in ['kills', 'assists']:
                if stat in player_data.columns:
                    first_avg = first_half[stat].mean()
                    second_avg = second_half[stat].mean()
                    
                    if first_avg > 0:
                        features[f'{stat}_improvement_rate'] = (second_avg - first_avg) / first_avg
                    else:
                        features[f'{stat}_improvement_rate'] = 0
        
        return features
    
    def _get_default_meta_features(self) -> Dict[str, float]:
        """Default meta-game features"""
        return {
            'kills_patch_adaptation': 1.0,
            'assists_patch_adaptation': 1.0,
            'current_patch_games': 0,
            'champion_pool_size': 5,
            'champion_diversity': 0.5,
            'main_champion_rate': 0.4,
            'player_flexibility': 0.6,
            'kills_improvement_rate': 0,
            'assists_improvement_rate': 0
        }
    
    # ==================== TEAM SYNERGY FEATURES ====================
    
    def extract_team_synergy_features(self, player_data: pd.DataFrame, 
                                    team: str = None) -> Dict[str, float]:
        """Extract team synergy and coordination features"""
        features = {}
        
        if player_data.empty:
            return self._get_default_synergy_features()
        
        # Team performance correlation
        if 'teamname' in player_data.columns and team:
            team_data = player_data[player_data['teamname'] == team]
            
            if len(team_data) >= 3:
                # Team game performance metrics
                if 'result' in team_data.columns:
                    wins = team_data['result'].str.contains('win|victory', case=False, na=False).sum()
                    features['team_win_rate'] = wins / len(team_data)
                else:
                    features['team_win_rate'] = 0.5
                
                # Individual performance on team
                for stat in ['kills', 'assists']:
                    if stat in player_data.columns:
                        team_avg = team_data[stat].mean()
                        overall_avg = player_data[stat].mean()
                        
                        if overall_avg > 0:
                            features[f'{stat}_team_synergy'] = team_avg / overall_avg
                        else:
                            features[f'{stat}_team_synergy'] = 1.0
                
                features['team_games'] = len(team_data)
            else:
                # Insufficient team data
                features['team_win_rate'] = 0.5
                for stat in ['kills', 'assists']:
                    features[f'{stat}_team_synergy'] = 1.0
                features['team_games'] = 0
        
        # Position synergy (if position data available)
        if 'position' in player_data.columns:
            position_data = player_data.groupby('position')['kills', 'assists'].mean()
            
            if len(position_data) > 0:
                # Position consistency
                positions = player_data['position'].value_counts()
                main_position_rate = positions.iloc[0] / len(player_data) if len(positions) > 0 else 1.0
                features['position_consistency'] = main_position_rate
                
                # Role adaptation
                features['role_flexibility'] = len(positions) / max(len(player_data), 1)
            else:
                features['position_consistency'] = 1.0
                features['role_flexibility'] = 0.1
        
        return features
    
    def _get_default_synergy_features(self) -> Dict[str, float]:
        """Default team synergy features"""
        return {
            'team_win_rate': 0.5,
            'kills_team_synergy': 1.0,
            'assists_team_synergy': 1.0,
            'team_games': 0,
            'position_consistency': 1.0,
            'role_flexibility': 0.1
        }
    
    # ==================== COMPREHENSIVE FEATURE EXTRACTION ====================
    
    def extract_all_advanced_features(self, player_data: pd.DataFrame, player_name: str,
                                    prop_type: str, opponent: str = None, team: str = None,
                                    current_patch: str = None) -> Dict[str, float]:
        """
        Extract all advanced features in one comprehensive call.
        Combines temporal, embedding, opponent, meta-game, and synergy features.
        """
        all_features = {}
        
        logger.info(f"Extracting comprehensive advanced features for {player_name}")
        
        # 1. Temporal momentum features
        temporal_features = self.extract_temporal_features(player_data, player_name, prop_type)
        all_features.update({f'temporal_{k}': v for k, v in temporal_features.items()})
        
        # 2. Player similarity features (requires full dataset)
        if hasattr(self.data_processor, 'combined_data') and self.data_processor.combined_data is not None:
            if not self.player_embeddings:
                self.generate_player_embeddings(self.data_processor.combined_data)
            
            similarity_features = self.extract_player_similarity_features(player_name, self.player_embeddings)
            all_features.update({f'similarity_{k}': v for k, v in similarity_features.items()})
        
        # 3. Opponent adjustment features
        opponent_features = self.extract_opponent_adjustment_features(player_data, opponent)
        all_features.update({f'opponent_{k}': v for k, v in opponent_features.items()})
        
        # 4. Meta-game features
        meta_features = self.extract_meta_game_features(player_data, current_patch)
        all_features.update({f'meta_{k}': v for k, v in meta_features.items()})
        
        # 5. Team synergy features
        synergy_features = self.extract_team_synergy_features(player_data, team)
        all_features.update({f'synergy_{k}': v for k, v in synergy_features.items()})
        
        # 6. Feature interactions and composites
        interaction_features = self._calculate_feature_interactions(all_features)
        all_features.update({f'interaction_{k}': v for k, v in interaction_features.items()})
        
        logger.info(f"Extracted {len(all_features)} advanced features for {player_name}")
        return all_features
    
    def _calculate_feature_interactions(self, features: Dict[str, float]) -> Dict[str, float]:
        """Calculate important feature interactions and composite scores"""
        interactions = {}
        
        # Momentum * Form interaction
        momentum = features.get('temporal_momentum_score', 0)
        streak = features.get('temporal_current_streak', 0)
        interactions['momentum_streak_combo'] = momentum * abs(streak) / 5.0
        
        # Consistency * Opponent strength
        consistency = features.get('temporal_consistency_score', 0.5)
        opp_strength = features.get('opponent_avg_opponent_strength', 0.5)
        interactions['consistency_vs_strength'] = consistency * (1 - opp_strength)
        
        # Team synergy * Role consistency
        team_synergy = features.get('synergy_kills_team_synergy', 1.0)
        position_consistency = features.get('synergy_position_consistency', 1.0)
        interactions['synergy_consistency_combo'] = team_synergy * position_consistency
        
        # Recent form * Meta adaptation
        recent_trend = features.get('temporal_recency_bias', 0)
        meta_adaptation = features.get('meta_kills_patch_adaptation', 1.0)
        interactions['form_meta_alignment'] = recent_trend * meta_adaptation
        
        # Volatility risk score
        volatility_3 = features.get('temporal_volatility_3', 0.3)
        volatility_7 = features.get('temporal_volatility_7', 0.3)
        interactions['volatility_risk'] = (volatility_3 + volatility_7) / 2.0
        
        # Overall form composite
        rolling_3 = features.get('temporal_rolling_3_avg', 0)
        rolling_7 = features.get('temporal_rolling_7_avg', 0)
        trend_strength = features.get('temporal_trend_strength', 0)
        
        if rolling_7 > 0:
            short_term_bias = rolling_3 / rolling_7
        else:
            short_term_bias = 1.0
        
        interactions['composite_form_score'] = (short_term_bias * 0.4 + 
                                              trend_strength * 0.3 + 
                                              momentum * 0.3)
        
        return interactions