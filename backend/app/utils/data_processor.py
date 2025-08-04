"""
CRITICAL BETTING LOGIC IMPLEMENTATION + POSITION FILTERING

This module implements the corrected betting logic for League of Legends prediction system
with proper role-based data filtering.

BETTING TERMINOLOGY EXPLANATION:
===============================

When betting markets refer to "Maps 1-2 Kills" or similar map range props, they mean:
- COMBINED/TOTAL statistics across those maps, NOT averages
- Example: "Maps 1-2 Kills" = Player's kills in Map 1 + Player's kills in Map 2

PREVIOUS (INCORRECT) IMPLEMENTATION:
- System calculated AVERAGE kills per map in the range
- This fundamentally misunderstood betting terminology
- Led to incorrect predictions for all map range props

CORRECTED IMPLEMENTATION:
- System now calculates COMBINED stats per series (map range)
- Groups data by player and match_series
- Sums statistics across maps within each series
- Then calculates mean/std on those COMBINED totals
- This correctly reflects how betting markets work

POSITION FILTERING IMPLEMENTATION:
=================================

NEW: Role-based data filtering is now properly implemented:
- get_player_data(player, position) filters CSV data by 'position' column
- Only includes games where player played the specified role
- Maps common aliases: 'bot' -> 'adc', 'jng' -> 'jungle', etc.
- No artificial stat adjustments - let actual positional data determine patterns
- This ensures predictions are based on relevant role-specific performance

EXAMPLE:
========
Player has 3 kills in Map 1, 5 kills in Map 2
- OLD (WRONG): "Maps 1-2" = (3+5)/2 = 4.0 average
- NEW (CORRECT): "Maps 1-2" = 3+5 = 8 combined

Player played ADC in 50 games, Support in 20 games
- OLD (WRONG): Used all 70 games regardless of prediction context
- NEW (CORRECT): Filter to only ADC games when predicting ADC performance

This change affects every prediction and is critical for accuracy.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any
import os
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataProcessor:
    def __init__(self):
        self.data_2024 = None
        self.data_2025 = None
        self.combined_data = None
        self._load_data()
    
    def _load_data(self):
        """Load and preprocess the CSV datasets"""
        try:
            import os
            
            # Try different paths for data files
            data_paths = [
                '/Users/matthewwiecking/Desktop/Outscaled2/data/2024_LoL_esports_match_data_from_OraclesElixir.csv',
                '/app/data/2024_LoL_esports_match_data_from_OraclesElixir.csv',
                '../data/2024_LoL_esports_match_data_from_OraclesElixir.csv',
                '../../data/2024_LoL_esports_match_data_from_OraclesElixir.csv'
            ]
            
            data_2024_path = None
            data_2025_path = None
            
            # Find the correct path for 2024 data
            for path in data_paths:
                if os.path.exists(path):
                    data_2024_path = path
                    data_2025_path = path.replace('2024_', '2025_')
                    break
            
            if data_2024_path is None:
                logger.warning("Data files not found at expected paths. Using empty DataFrame for testing.")
                logger.warning("Expected paths checked:")
                for path in data_paths:
                    logger.warning(f"  - {path}")
                self.data_2024 = pd.DataFrame()
                self.data_2025 = pd.DataFrame()
                self.combined_data = pd.DataFrame()
                return
            
            # Load 2024 data
            logger.info(f"Loading 2024 data from: {data_2024_path}")
            try:
                self.data_2024 = pd.read_csv(data_2024_path)
                logger.info(f"2024 data loaded successfully: {len(self.data_2024)} rows")
            except Exception as e:
                logger.error(f"Error loading 2024 data: {e}")
                self.data_2024 = pd.DataFrame()
            
            # Load 2025 data
            logger.info(f"Loading 2025 data from: {data_2025_path}")
            try:
                self.data_2025 = pd.read_csv(data_2025_path)
                logger.info(f"2025 data loaded successfully: {len(self.data_2025)} rows")
            except Exception as e:
                logger.error(f"Error loading 2025 data: {e}")
                self.data_2025 = pd.DataFrame()
            
            # Combine datasets
            self.combined_data = pd.concat([self.data_2024, self.data_2025], ignore_index=True)
            
            # Generate map index within series
            self._generate_map_index()
            
            # Clean and preprocess
            self._preprocess_data()
            
            logger.info(f"Data loaded successfully. Total records: {len(self.combined_data)}")
            
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            # For testing, create empty DataFrame
            self.data_2024 = pd.DataFrame()
            self.data_2025 = pd.DataFrame()
            self.combined_data = pd.DataFrame()
    
    def _generate_map_index(self):
        """Generate map_index_within_series as specified in MVP"""
        # Use the 'game' column which contains the actual game number within a series
        # Group by date and team to identify series (games on the same day for the same team)
        # Convert date to datetime first if it's not already
        if not pd.api.types.is_datetime64_any_dtype(self.combined_data["date"]):
            self.combined_data["date"] = pd.to_datetime(self.combined_data["date"])
        
        self.combined_data["match_series"] = (
            self.combined_data["date"].dt.date.astype(str) + "_" + 
            self.combined_data["teamname"]
        )
        
        # Use the 'game' column as the map index within series
        self.combined_data["map_index_within_series"] = self.combined_data["game"]
        
        logger.info("Map index generated successfully")
    
    def _preprocess_data(self):
        """Clean and preprocess the data"""
        try:
            # Convert date to datetime
            if 'date' in self.combined_data.columns:
                self.combined_data['date'] = pd.to_datetime(self.combined_data['date'], errors='coerce')
            
            # Fill NaN values
            numeric_columns = self.combined_data.select_dtypes(include=[np.number]).columns
            self.combined_data[numeric_columns] = self.combined_data[numeric_columns].fillna(0)
            
            # Convert position to lowercase for consistency
            if 'position' in self.combined_data.columns:
                self.combined_data['position'] = self.combined_data['position'].astype(str).str.lower()
            
            logger.info("Data preprocessing completed")
        except Exception as e:
            logger.error(f"Error in data preprocessing: {e}")
            logger.warning("Continuing with minimal preprocessing")
    
    def filter_player_data(self, player_names: List[str], map_range: List[int], 
                          team: str = None, opponent: str = None, tournament: str = None) -> pd.DataFrame:
        """Filter data for specific players and map range"""
        # Filter by player names
        player_data = self.combined_data[
            self.combined_data['playername'].isin(player_names)
        ].copy()
        
        # Filter by map range
        player_data = player_data[
            player_data['map_index_within_series'].between(map_range[0], map_range[1])
        ]
        
        # Apply additional filters if provided
        if team:
            player_data = player_data[player_data['teamname'] == team]
        
        if opponent:
            # For opponent filtering, we need to look at the opposing team
            # This is a simplified approach - in practice you'd need to match by gameid
            pass
        
        if tournament:
            player_data = player_data[player_data['league'] == tournament]
        
        return player_data
    
    def filter_player_data_with_tiers(self, player_names: List[str], map_range: List[int], 
                                    team: str = None, opponent: str = None, tournament: str = None,
                                    strict_mode: bool = False, position: str = None) -> Dict[str, Any]:
        """
        Filter player data using tiered fallback system with confidence weighting
        Returns: {'data': DataFrame, 'tier_info': Dict, 'sample_sources': Dict}
        """
        logger.info(f"Filtering data for {player_names} with tiered fallback system")
        
        # Define tier weights and criteria
        tiers = [
            {
                'name': 'Tier 1 - Exact Tournament',
                'weight': 1.0,
                'description': 'Most relevant and recent',
                'criteria': {'tournament': tournament, 'map_range': map_range}
            },
            {
                'name': 'Tier 2 - Same Region/Year',
                'weight': 0.8,
                'description': 'Region-relevant but broader scope',
                'criteria': {'region': self._get_region(tournament), 'year': 2025, 'map_range': map_range}
            },
            {
                'name': 'Tier 3 - Same Team/Year',
                'weight': 0.7,
                'description': 'Same roster context',
                'criteria': {'team': team, 'year': 2025, 'map_range': map_range}
            },
            {
                'name': 'Tier 4 - Recent Matches',
                'weight': 0.5,
                'description': 'Recent but less relevant',
                'criteria': {'year': [2024, 2025], 'map_range': map_range}
            },
            {
                'name': 'Tier 5 - Fallback',
                'weight': 0.3,
                'description': 'Weak context, fallback only',
                'criteria': {'map_range': map_range}
            }
        ]
        
        # If strict mode, only use Tier 1
        if strict_mode:
            tiers = tiers[:1]
            logger.info("Strict mode enabled - using Tier 1 only")
        
        # Try each tier until we get sufficient data
        for tier_idx, tier in enumerate(tiers):
            logger.info(f"Trying {tier['name']} (weight: {tier['weight']})")
            
            # Filter data for this tier with position filtering
            tier_data = self._filter_by_tier_criteria(player_names, tier['criteria'], team, opponent, position)
            
            if len(tier_data) >= 5:  # Minimum viable sample size
                logger.info(f"Tier {tier_idx + 1} successful: {len(tier_data)} maps")
                
                # Calculate sample sources breakdown
                sample_sources = self._calculate_sample_sources(tier_data)
                
                # Prepare tier info
                tier_info = {
                    'tier': tier_idx + 1,
                    'weight': tier['weight'],
                    'name': tier['name'],
                    'description': tier['description'],
                    'maps_used': len(tier_data),
                    'sample_quality': self._assess_sample_quality(len(tier_data))
                }
                
                return {
                    'data': tier_data,
                    'tier_info': tier_info,
                    'sample_sources': sample_sources,
                    'fallback_used': tier_idx > 0
                }
        
        # If we get here, no tier provided sufficient data
        logger.warning("All tiers failed to provide sufficient data")
        return {
            'data': pd.DataFrame(),
            'tier_info': {
                'tier': 0, 
                'weight': 0.0, 
                'name': 'No Data', 
                'description': 'No data available',
                'maps_used': 0
            },
            'sample_sources': {},
            'fallback_used': False
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
    
    def _filter_by_tier_criteria(self, player_names: List[str], criteria: Dict, team: str = None, opponent: str = None, position: str = None) -> pd.DataFrame:
        """Filter data based on tier-specific criteria"""
        filtered_data = self.combined_data.copy()
        
        # Filter by player names
        filtered_data = filtered_data[filtered_data['playername'].isin(player_names)]
        
        # Apply tier-specific criteria
        if 'tournament' in criteria and criteria['tournament']:
            filtered_data = filtered_data[filtered_data['league'] == criteria['tournament']]
        
        if 'region' in criteria and criteria['region']:
            filtered_data = filtered_data[filtered_data['league'].str.contains(criteria['region'], na=False)]
        
        if 'year' in criteria:
            if isinstance(criteria['year'], list):
                # Handle year range
                filtered_data = filtered_data[filtered_data['year'].isin(criteria['year'])]
            else:
                # Handle single year
                filtered_data = filtered_data[filtered_data['year'] == criteria['year']]
        
        if 'team' in criteria and criteria['team']:
            filtered_data = filtered_data[filtered_data['teamname'] == criteria['team']]
        
        # Apply map range filter
        if 'map_range' in criteria:
            map_start, map_end = criteria['map_range']
            filtered_data = filtered_data[
                (filtered_data['map_index_within_series'] >= map_start) & 
                (filtered_data['map_index_within_series'] <= map_end)
            ]
        
        # Apply team/opponent filters if provided
        if team:
            filtered_data = filtered_data[filtered_data['teamname'] == team]
        
        if opponent and 'opponent' in filtered_data.columns:
            filtered_data = filtered_data[filtered_data['opponent'] == opponent]
        
        # Apply position filtering if specified
        if position is not None:
            try:
                filtered_data = self._filter_data_by_position(filtered_data, position)
                logger.info(f"Applied position filter '{position}': {len(filtered_data)} matches remaining")
            except Exception as e:
                logger.error(f"Error applying position filter '{position}': {e}")
                logger.warning("Continuing without position filter")
        
        return filtered_data
    
    def _get_region(self, tournament: str) -> str:
        """Extract region from tournament name"""
        region_mapping = {
            'LCK': 'LCK',
            'LPL': 'LPL', 
            'LEC': 'LEC',
            'LCS': 'LCS',
            'MSI': 'International',
            'Worlds': 'International'
        }
        return region_mapping.get(tournament, tournament)
    
    def _calculate_sample_sources(self, data: pd.DataFrame) -> Dict[str, int]:
        """Calculate breakdown of sample sources"""
        if data.empty:
            return {}
        
        # Group by tournament and count
        sources = data.groupby('league').size().to_dict()
        
        # Add year information if available
        if 'year' in data.columns:
            year_sources = data.groupby(['league', 'year']).size()
            sources = {}
            for (league, year), count in year_sources.items():
                key = f"{league} {year}"
                sources[key] = count
        
        return sources
    
    def aggregate_stats(self, player_data: pd.DataFrame, prop_type: str) -> Dict[str, float]:
        """
        Aggregate statistics across the map range using BETTING LOGIC.
        
        CRITICAL: For map ranges (e.g., "Maps 1-2"), betting terminology means COMBINED/TOTAL
        stats across those maps, NOT AVERAGES. This reflects how betting markets work.
        
        Example: "Maps 1-2 Kills" means total kills across maps 1 AND 2 combined.
        """
        if prop_type not in ['kills', 'assists']:
            raise ValueError("prop_type must be 'kills' or 'assists'")
        
        # Debug logging
        logger.info(f"Aggregating COMBINED stats for {prop_type} across {len(player_data)} maps (BETTING LOGIC)")
        logger.info(f"Sample {prop_type} values: {player_data[prop_type].head(10).tolist()}")
        logger.info(f"Position distribution: {player_data['position'].value_counts().to_dict()}")
        
        # BETTING LOGIC FIX: For map ranges, we want TOTAL/COMBINED stats across the maps
        # First sum within each match series, then get stats on those totals
        logger.info("Calculating series totals (combined stats per series) for betting logic")
        
        # Group by player and match series, then sum to get combined stats per series
        series_totals = player_data.groupby(['playername', 'match_series']).agg({
            prop_type: 'sum',  # COMBINED stats across maps in the range
            'deaths': 'sum',
            'damagetochampions': 'sum', 
            'visionscore': 'sum',
            'total cs': 'sum',
            'goldat10': 'sum',
            'xpat10': 'sum',
            'csat10': 'sum',
            'golddiffat15': 'sum',
            'xpdiffat15': 'sum',
            'csdiffat15': 'sum',
            'killsat15': 'sum',
            'assistsat15': 'sum',
            'deathsat15': 'sum',
            'goldat20': 'sum',
            'xpat20': 'sum',
            'csat20': 'sum',
            'killsat20': 'sum',
            'assistsat20': 'sum',
            'deathsat20': 'sum'
        }).round(2)
        
        logger.info(f"Generated {len(series_totals)} series totals for combined stats")
        
        # Now aggregate these series totals per player to get mean/std of combined performance
        agg_stats = series_totals.groupby('playername').agg({
            prop_type: ['mean', 'std', 'count'],  # Stats on the COMBINED performance
            'deaths': 'mean',
            'damagetochampions': 'mean',
            'visionscore': 'mean', 
            'total cs': 'mean',
            'goldat10': 'mean',
            'xpat10': 'mean',
            'csat10': 'mean',
            'golddiffat15': 'mean',
            'xpdiffat15': 'mean',
            'csdiffat15': 'mean',
            'killsat15': 'mean',
            'assistsat15': 'mean',
            'deathsat15': 'mean',
            'goldat20': 'mean',
            'xpat20': 'mean',
            'csat20': 'mean',
            'killsat20': 'mean',
            'assistsat20': 'mean',
            'deathsat20': 'mean'
        }).round(2)
        
        # Flatten column names
        agg_stats.columns = ['_'.join(col).strip() for col in agg_stats.columns.values]
        
        # Debug logging for aggregated results
        for player_name in agg_stats.index:
            player_stats = agg_stats.loc[player_name]
            combined_avg = player_stats.get(f'{prop_type}_mean', 0)
            logger.info(f"Player {player_name} - {prop_type} COMBINED avg per series: {combined_avg}")
        
        return agg_stats.to_dict('index')
    
    def engineer_features(self, player_data: pd.DataFrame, prop_type: str) -> Dict[str, float]:
        """
        Engineer features using BETTING LOGIC for combined statistics.
        
        CRITICAL: Features now reflect COMBINED stats across map ranges, not averages.
        This aligns with betting terminology where "Maps 1-2" means total performance.
        """
        features = {}
        
        # Get aggregated stats (now uses combined/total logic)
        agg_stats = self.aggregate_stats(player_data, prop_type)
        
        # For simplicity, we'll use the first player's stats
        # In practice, you'd handle multiple players differently
        player_name = player_data['playername'].iloc[0] if not player_data.empty else None
        if not player_name or player_name not in agg_stats:
            return self._get_default_features()
        
        stats = agg_stats[player_name]
        
        # BETTING LOGIC: These are now COMBINED stats per series, not individual map averages
        features['combined_' + prop_type] = stats.get(f'{prop_type}_mean', 0)  # Average of combined performance
        features['std_dev_combined_' + prop_type] = stats.get(f'{prop_type}_std', 0)  # Std dev of combined performance
        features['series_played'] = stats.get(f'{prop_type}_count', 0)  # Number of series (not individual maps)
        
        # For backward compatibility, keep old feature names but mark them as combined
        features['avg_' + prop_type] = features['combined_' + prop_type]  # Backward compatibility
        features['std_dev_' + prop_type] = features['std_dev_combined_' + prop_type]  # Backward compatibility
        features['maps_played'] = features['series_played']  # Backward compatibility (though it's really series)
        
        # Long-term averages (need to calculate combined stats from full dataset for betting logic)
        logger.info("Calculating long-term combined averages for betting context")
        
        # Get all data for this player and calculate combined stats per series
        player_full_data = self.combined_data[self.combined_data['playername'] == player_name]
        if not player_full_data.empty and 'match_series' in player_full_data.columns:
            # Calculate combined stats per series for long-term average
            longterm_series_totals = player_full_data.groupby('match_series')[prop_type].sum()
            longterm_combined_avg = longterm_series_totals.mean()
        else:
            # Fallback to simple average if match_series not available
            longterm_combined_avg = self.combined_data[self.combined_data['playername'] == player_name][prop_type].mean()
        
        features['longterm_combined_' + prop_type] = longterm_combined_avg
        features['longterm_' + prop_type + '_avg'] = longterm_combined_avg  # Backward compatibility
        
        # Deviation metrics (now based on combined performance)
        recent_combined = features['combined_' + prop_type]
        longterm_combined = features['longterm_combined_' + prop_type]
        
        if longterm_combined > 0:
            features['form_z_score'] = (recent_combined - longterm_combined) / max(features['std_dev_combined_' + prop_type], 0.1)
            features['form_deviation_ratio'] = recent_combined / longterm_combined
        else:
            features['form_z_score'] = 0
            features['form_deviation_ratio'] = 1
        
        # Position information (no longer used for stat adjustment)
        position = player_data['position'].iloc[0] if not player_data.empty else 'mid'
        # Position factor is always 1.0 - no role-based expectation adjustments
        # Role filtering should happen at the data level, not through stat multipliers
        features['position_factor'] = 1.0
        
        # Quality/Volatility metrics
        features['sample_size_score'] = min(features['maps_played'] / 10, 1.0)  # Normalize to 0-1
        
        # Additional performance metrics
        features['avg_deaths'] = stats.get('deaths_mean', 0)
        features['avg_damage'] = stats.get('damagetochampions_mean', 0)
        features['avg_vision'] = stats.get('visionscore_mean', 0)
        features['avg_cs'] = stats.get('total cs_mean', 0)
        
        # Early game metrics
        features['avg_gold_at_10'] = stats.get('goldat10_mean', 0)
        features['avg_xp_at_10'] = stats.get('xpat10_mean', 0)
        features['avg_cs_at_10'] = stats.get('csat10_mean', 0)
        
        # Mid game metrics
        features['avg_gold_diff_15'] = stats.get('golddiffat15_mean', 0)
        features['avg_xp_diff_15'] = stats.get('xpdiffat15_mean', 0)
        features['avg_cs_diff_15'] = stats.get('csdiffat15_mean', 0)
        
        return features
    
    def _get_default_features(self) -> Dict[str, float]:
        """Return default features when no data is available (using betting logic naming)"""
        return {
            # New betting logic features (combined stats)
            'combined_kills': 0, 'combined_assists': 0, 
            'std_dev_combined_kills': 0, 'std_dev_combined_assists': 0,
            'series_played': 0, 'longterm_combined_kills': 0, 'longterm_combined_assists': 0,
            
            # Backward compatibility features 
            'avg_kills': 0, 'avg_assists': 0, 'std_dev_kills': 0, 'std_dev_assists': 0,
            'maps_played': 0, 'longterm_kills_avg': 0, 'longterm_assists_avg': 0,
            
            # Common features
            'form_z_score': 0, 'form_deviation_ratio': 1, 'position_factor': 1.0,
            'sample_size_score': 0, 'avg_deaths': 0, 'avg_damage': 0, 'avg_vision': 0,
            'avg_cs': 0, 'avg_gold_at_10': 0, 'avg_xp_at_10': 0, 'avg_cs_at_10': 0,
            'avg_gold_diff_15': 0, 'avg_xp_diff_15': 0, 'avg_cs_diff_15': 0
        }
    
    def _infer_most_recent_team(self, player_name: str, match_date: str = None) -> str:
        """
        Infer the most recent team for a player based on their match history.
        
        Args:
            player_name: Name of the player
            match_date: Optional match date to use as reference point
            
        Returns:
            Most recent team name for the player
        """
        if self.combined_data is None:
            logger.warning("No data available for team inference")
            return None
        
        # Filter data for the specific player
        player_data = self.combined_data[self.combined_data['playername'] == player_name].copy()
        
        if player_data.empty:
            logger.warning(f"No data found for player: {player_name}")
            return None
        
        # Convert date column to datetime for proper sorting
        player_data['date'] = pd.to_datetime(player_data['date'], errors='coerce')
        player_data = player_data.dropna(subset=['date'])
        
        if player_data.empty:
            logger.warning(f"No valid dates found for player: {player_name}")
            return None
        
        # If match_date is provided, use it as reference point
        if match_date:
            try:
                reference_date = pd.to_datetime(match_date)
                # Get data before or on the reference date
                player_data = player_data[player_data['date'] <= reference_date]
                if player_data.empty:
                    logger.warning(f"No data found for {player_name} before {match_date}")
                    return None
            except Exception as e:
                logger.warning(f"Invalid match_date format: {match_date}, using most recent data")
        
        # Sort by date and get the most recent match
        player_data = player_data.sort_values('date', ascending=False)
        most_recent_match = player_data.iloc[0]
        
        inferred_team = most_recent_match['teamname']
        match_date = most_recent_match['date'].strftime('%Y-%m-%d')
        
        logger.info(f"Inferred team for {player_name}: {inferred_team} (from match on {match_date})")
        return inferred_team

    def process_request(self, request, strict_mode: bool = False) -> Dict[str, Any]:
        """Process the prediction request and return engineered features with tier information"""
        
        # Extract position information from request if available
        target_position = None
        try:
            if hasattr(request, 'position_roles') and request.position_roles:
                # Ensure position_roles is a list and has at least one element
                if isinstance(request.position_roles, list) and len(request.position_roles) > 0:
                    target_position = request.position_roles[0]
                    if target_position and str(target_position).strip():  # Ensure it's not empty or whitespace
                        target_position = str(target_position).strip()
                        logger.info(f"Using position '{target_position}' for data filtering")
                    else:
                        target_position = None
                        logger.info("Position role is empty, using all positions")
                else:
                    logger.info("No valid position roles found, using all positions")
            else:
                logger.info("No position_roles attribute or empty, using all positions")
        except Exception as e:
            logger.error(f"Error extracting position from request: {e}")
            logger.info("Using all positions due to error")
            target_position = None
        
        # Auto-infer team if not provided
        if not request.team or request.team.strip() == "":
            if len(request.player_names) == 1:
                # Single player - infer their team
                inferred_team = self._infer_most_recent_team(request.player_names[0], request.match_date)
                if inferred_team:
                    request.team = inferred_team
                    logger.warning(f"No team provided for {request.player_names[0]}. Auto-inferred: {inferred_team}")
                else:
                    logger.warning(f"Could not infer team for {request.player_names[0]}. Proceeding without team filtering.")
            else:
                # Multiple players - try to infer team from first player
                inferred_team = self._infer_most_recent_team(request.player_names[0], request.match_date)
                if inferred_team:
                    request.team = inferred_team
                    logger.warning(f"No team provided for combo prediction. Using team from {request.player_names[0]}: {inferred_team}")
                else:
                    logger.warning(f"Could not infer team for combo prediction. Proceeding without team filtering.")
        
        # Use tiered filtering system with position filtering
        try:
            tier_result = self.filter_player_data_with_tiers(
                player_names=request.player_names,
                map_range=request.map_range,
                team=request.team,
                opponent=request.opponent,
                tournament=request.tournament,
                strict_mode=strict_mode,
                position=target_position  # Pass position for filtering
            )
        except Exception as e:
            logger.error(f"Error in tier filtering: {e}")
            # Return empty result with error info
            tier_result = {
                'data': pd.DataFrame(),
                'tier_info': {'tier': 0, 'weight': 0.0, 'name': 'Error', 'description': f'Filtering error: {str(e)}', 'maps_used': 0},
                'sample_sources': {},
                'fallback_used': False
            }
        
        player_data = tier_result['data']
        tier_info = tier_result['tier_info']
        sample_sources = tier_result['sample_sources']
        fallback_used = tier_result['fallback_used']
        
        # Log tier information
        logger.info(f"Using {tier_info['name']} with {tier_info['maps_used']} maps (weight: {tier_info['weight']})")
        
        if player_data.empty:
            # Create detailed error message for better debugging
            error_details = {
                'players': request.player_names,
                'tournament': request.tournament,
                'team': request.team,
                'map_range': request.map_range,
                'available_players': self.get_available_players()[:10],  # First 10 for reference
                'available_tournaments': sorted(self.combined_data['league'].unique()) if self.combined_data is not None else []
            }
            
            error_msg = (
                f"No valid data found for the specified criteria:\n"
                f"- Players: {request.player_names}\n"
                f"- Tournament: {request.tournament}\n"
                f"- Team: {request.team}\n"
                f"- Map Range: {request.map_range}\n\n"
                f"Available tournaments: {error_details['available_tournaments']}\n"
                f"Sample available players: {error_details['available_players']}"
            )
            
            logger.warning(error_msg)
            raise ValueError(error_msg)
        
        # Log final sample size and tier info
        logger.info(f"Final sample size: {len(player_data)} maps from {tier_info['name']}")
        if fallback_used:
            logger.warning(f"Fallback used: {tier_info['name']} (confidence will be adjusted)")
        
        # Engineer features
        features = self.engineer_features(player_data, request.prop_type)
        
        # Add combo-specific features if multiple players
        if len(request.player_names) > 1:
            features = self._add_combo_features(features, player_data, request.prop_type)
        
        # Generate sample details for transparency
        sample_details = self._generate_sample_details(player_data, request)
        
        # Add tier information to features
        features['tier_info'] = tier_info
        features['sample_sources'] = sample_sources
        features['fallback_used'] = fallback_used
        features['sample_details'] = sample_details
        
        return features
    
    def _add_combo_features(self, features: Dict[str, float], player_data: pd.DataFrame, prop_type: str) -> Dict[str, float]:
        """
        Add features specific to combo predictions using BETTING LOGIC.
        
        CRITICAL: For combos, we need COMBINED stats across players AND maps in the range.
        """
        # BETTING LOGIC: For combos across map ranges, sum all players' performance within each series
        # Then get stats on those combined totals
        logger.info("Calculating combo features using betting logic (combined stats across players and maps)")
        
        # Group by match_series and sum across all players for the combo
        combo_series_totals = player_data.groupby('match_series')[prop_type].sum().reset_index()
        
        features['combo_combined_' + prop_type] = combo_series_totals[prop_type].mean()  # Avg of combined performance
        features['combo_std_combined_' + prop_type] = combo_series_totals[prop_type].std()  # Std of combined performance
        features['combo_series_played'] = len(combo_series_totals)  # Number of series
        
        # Backward compatibility
        features['combo_avg_' + prop_type] = features['combo_combined_' + prop_type]
        features['combo_std_' + prop_type] = features['combo_std_combined_' + prop_type]
        features['combo_maps_played'] = features['combo_series_played']
        
        # Apply confidence penalty for combos (betting markets are harder to predict)
        features['combo_confidence_penalty'] = 0.9  # 10% penalty for combo predictions
        
        return features
    
    def get_data_summary(self) -> str:
        """Get summary of available data"""
        if self.combined_data is None:
            return "No data loaded"
        
        years = self.combined_data['year'].unique()
        total_matches = len(self.combined_data['gameid'].unique())
        total_players = len(self.combined_data['playername'].unique())
        
        return f"Data from years: {list(years)}, Total matches: {total_matches}, Total players: {total_players}"
    
    def get_available_players(self) -> List[str]:
        """Get list of all available player names"""
        if self.combined_data is None:
            return []
        try:
            # Filter out any non-string values and handle NaN values
            player_names = self.combined_data['playername'].dropna().astype(str)
            unique_players = player_names.unique().tolist()
            return sorted(unique_players)
        except Exception as e:
            logger.error(f"Error getting available players: {e}")
            return []
    
    def get_available_teams(self) -> List[str]:
        """Get list of all available team names"""
        if self.combined_data is None:
            return []
        try:
            # Filter out any non-string values and handle NaN values
            team_names = self.combined_data['teamname'].dropna().astype(str)
            unique_teams = team_names.unique().tolist()
            return sorted(unique_teams)
        except Exception as e:
            logger.error(f"Error getting available teams: {e}")
            return []
    
    def get_available_tournaments(self) -> List[str]:
        """Get list of all available tournament names"""
        if self.combined_data is None:
            return []
        try:
            # Filter out any non-string values and handle NaN values
            tournament_names = self.combined_data['league'].dropna().astype(str)
            unique_tournaments = tournament_names.unique().tolist()
            return sorted(unique_tournaments)
        except Exception as e:
            logger.error(f"Error getting available tournaments: {e}")
            return []
    
    def check_data_availability(self, player_names: List[str], tournament: str = None, 
                              map_range: List[int] = None) -> Dict[str, any]:
        """
        Check data availability for given criteria and return helpful suggestions
        """
        if self.combined_data is None:
            return {
                'available': False,
                'message': 'No data loaded',
                'suggestions': []
            }
        
        # Check if players exist
        available_players = self.get_available_players()
        missing_players = [p for p in player_names if p not in available_players]
        
        if missing_players:
            return {
                'available': False,
                'message': f'Players not found: {missing_players}',
                'suggestions': {
                    'similar_players': [p for p in available_players if any(name.lower() in p.lower() for name in missing_players)][:5],
                    'available_players': available_players[:10]
                }
            }
        
        # Check tournament availability
        if tournament:
            available_tournaments = sorted(self.combined_data['league'].unique())
            if tournament not in available_tournaments:
                return {
                    'available': False,
                    'message': f'Tournament "{tournament}" not found',
                    'suggestions': {
                        'available_tournaments': available_tournaments,
                        'player_tournaments': sorted(self.combined_data[
                            self.combined_data['playername'].isin(player_names)
                        ]['league'].unique())
                    }
                }
        
        # Check map range data
        if map_range:
            player_data = self.filter_player_data(player_names, map_range, tournament=tournament)
            if player_data.empty:
                return {
                    'available': False,
                    'message': f'No data found for maps {map_range[0]}-{map_range[1]}',
                    'suggestions': {
                        'player_tournaments': sorted(self.combined_data[
                            self.combined_data['playername'].isin(player_names)
                        ]['league'].unique()),
                        'available_map_ranges': self._get_available_map_ranges(player_names, tournament)
                    }
                }
        
        return {
            'available': True,
            'message': 'Data available',
            'data_count': len(self.filter_player_data(player_names, map_range or [1, 3], tournament=tournament))
        }
    
    def _get_available_map_ranges(self, player_names: List[str], tournament: str = None) -> List[List[int]]:
        """Get available map ranges for given players"""
        if self.combined_data is None:
            return []
        
        player_data = self.combined_data[self.combined_data['playername'].isin(player_names)]
        if tournament:
            player_data = player_data[player_data['league'] == tournament]
        
        if player_data.empty:
            return []
        
        map_indices = sorted(player_data['map_index_within_series'].unique())
        
        # Group consecutive map indices
        ranges = []
        start = map_indices[0]
        end = start
        
        for i in range(1, len(map_indices)):
            if map_indices[i] == end + 1:
                end = map_indices[i]
            else:
                ranges.append([start, end])
                start = map_indices[i]
                end = start
        
        ranges.append([start, end])
        return ranges[:5]  # Return first 5 ranges 

    def _generate_sample_details(self, player_data: pd.DataFrame, request) -> Dict[str, Any]:
        """Generate detailed sample information for transparency"""
        if player_data.empty:
            return {
                "maps_used": 0,
                "filter_criteria": "No data available",
                "position": "Unknown",
                "opponent": request.opponent or "Unknown",
                "tournament": request.tournament or "Unknown",
                "map_range": f"Maps {request.map_range[0]}-{request.map_range[1]}",
                "data_years": "No data",
                "sample_quality": "Poor"
            }
        
        # Get position information
        positions = player_data['position'].unique() if 'position' in player_data.columns else ['Unknown']
        position_str = ", ".join(positions) if len(positions) <= 3 else f"{len(positions)} positions"
        
        # Get tournament information
        tournaments = player_data['league'].unique() if 'league' in player_data.columns else [request.tournament]
        tournament_str = ", ".join(tournaments) if len(tournaments) <= 2 else f"{len(tournaments)} tournaments"
        
        # Get opponent information
        opponents = player_data['opponent'].unique() if 'opponent' in player_data.columns else [request.opponent]
        opponent_str = ", ".join(opponents) if len(opponents) <= 2 else f"{len(opponents)} opponents"
        
        # Get date range
        if 'date' in player_data.columns:
            min_date = player_data['date'].min()
            max_date = player_data['date'].max()
            date_range = f"{min_date} to {max_date}"
        else:
            date_range = "2024-2025"
        
        # Build filter criteria description
        filter_parts = []
        if request.tournament:
            filter_parts.append(f"Tournament: {request.tournament}")
        if request.team:
            filter_parts.append(f"Team: {request.team}")
        if request.opponent:
            filter_parts.append(f"Opponent: {request.opponent}")
        filter_parts.append(f"Maps {request.map_range[0]}-{request.map_range[1]}")
        
        filter_criteria = " | ".join(filter_parts)
        
        return {
            "maps_used": len(player_data),
            "filter_criteria": filter_criteria,
            "position": position_str,
            "opponent": opponent_str,
            "tournament": tournament_str,
            "map_range": f"Maps {request.map_range[0]}-{request.map_range[1]}",
            "data_years": date_range,
            "sample_quality": self._assess_sample_quality(len(player_data))
        }
    
    def _assess_sample_quality(self, sample_size: int) -> str:
        """Assess the quality of the sample size"""
        if sample_size >= 20:
            return "Excellent"
        elif sample_size >= 10:
            return "Good"
        elif sample_size >= 5:
            return "Fair"
        else:
            return "Poor" 

    def get_all_players(self) -> List[str]:
        """Get list of all available players in the dataset"""
        # Combine data from both years
        combined_data = pd.concat([self.data_2024, self.data_2025], ignore_index=True)
        
        # Get unique player names
        all_players = combined_data['playername'].dropna().unique().tolist()
        
        # Filter out empty strings and clean player names
        cleaned_players = [player.strip() for player in all_players if player.strip()]
        
        logger.info(f"Found {len(cleaned_players)} unique players in dataset")
        return cleaned_players
    
    def get_player_data(self, player_name: str, position: str = None) -> pd.DataFrame:
        """Get historical data for a specific player, optionally filtered by position"""
        # Use combined_data which is already loaded and preprocessed
        if self.combined_data is None or self.combined_data.empty:
            logger.warning("No combined data available")
            return pd.DataFrame()
        
        # Filter for the specific player
        player_data = self.combined_data[self.combined_data['playername'] == player_name].copy()
        
        if player_data.empty:
            logger.warning(f"No data found for player: {player_name}")
            return pd.DataFrame()
        
        # Apply position filtering if specified
        if position is not None:
            player_data = self._filter_data_by_position(player_data, position)
            logger.info(f"Filtered to {len(player_data)} matches for {player_name} in position '{position}'")
        else:
            logger.info(f"Retrieved {len(player_data)} total matches for player {player_name}")
        
        # Sort by date if available
        if 'date' in player_data.columns:
            player_data['date'] = pd.to_datetime(player_data['date'], errors='coerce')
            player_data = player_data.sort_values('date')
        
        return player_data
    
    def get_available_positions(self) -> List[str]:
        """Get list of all available positions in the dataset"""
        if self.combined_data is None or self.combined_data.empty:
            return []
        
        try:
            # Get unique positions and clean them
            positions = self.combined_data['position'].dropna().unique().tolist()
            cleaned_positions = [pos.strip().lower() for pos in positions if pos.strip()]
            return sorted(set(cleaned_positions))
        except Exception as e:
            logger.error(f"Error getting available positions: {e}")
            return []
    
    def validate_position_filtering(self, player_name: str, position: str) -> Dict[str, Any]:
        """Validate position filtering for a specific player"""
        if self.combined_data is None or self.combined_data.empty:
            return {'valid': False, 'error': 'No data loaded'}
        
        # Get all data for player
        all_player_data = self.get_player_data(player_name)
        if all_player_data.empty:
            return {'valid': False, 'error': f'No data found for player {player_name}'}
        
        # Get position-filtered data
        position_filtered_data = self.get_player_data(player_name, position)
        
        # Get position distribution for this player
        position_counts = all_player_data['position'].value_counts().to_dict()
        
        return {
            'valid': True,
            'player': player_name,
            'target_position': position,
            'total_matches': len(all_player_data),
            'filtered_matches': len(position_filtered_data),
            'position_distribution': position_counts,
            'filter_effectiveness': len(position_filtered_data) / len(all_player_data) if len(all_player_data) > 0 else 0
        }
    
    def _filter_data_by_position(self, player_data: pd.DataFrame, target_position: str) -> pd.DataFrame:
        """Filter player data to only include games where they played the target position"""
        try:
            if player_data.empty:
                logger.warning("Empty player data provided to position filter")
                return player_data
            
            if 'position' not in player_data.columns:
                logger.warning("No position column found in data - returning all data")
                return player_data
            
            if target_position is None or not target_position.strip():
                logger.info("No target position specified - returning all data")
                return player_data
            
            # Map common position abbreviations - based on actual CSV data (CSV uses lowercase)
            position_mapping = {
                'top': ['top'],  # Note: CSV might not have 'top', could be different
                'jungle': ['jng'],  # CSV uses 'jng' 
                'jng': ['jng'],
                'mid': ['mid'],  # CSV uses 'mid'
                'adc': ['bot'],  # CSV uses 'bot' for ADC
                'bot': ['bot'],  # CSV uses 'bot'
                'support': ['sup'],  # CSV might use 'sup'
                'sup': ['sup']
            }
            
            # Normalize target position
            target_position_lower = target_position.lower().strip()
            
            # Find matching positions
            target_positions = []
            for role, aliases in position_mapping.items():
                if target_position_lower == role or target_position_lower in aliases:
                    target_positions.extend(aliases)
                    break
            
            # If no mapping found, use the position as-is
            if not target_positions:
                target_positions = [target_position_lower]
            
            # Filter data to only include games in target position
            initial_count = len(player_data)
            position_matches = player_data['position'].str.lower().isin(target_positions)
            filtered_data = player_data[position_matches]
            
            logger.info(f"Position filtering: {initial_count} total games -> {len(filtered_data)} games in position '{target_position}' (matched: {target_positions})")
            
            return filtered_data
        
        except Exception as e:
            logger.error(f"Error in position filtering: {e}")
            logger.error(f"Returning all data for safety")
            return player_data 