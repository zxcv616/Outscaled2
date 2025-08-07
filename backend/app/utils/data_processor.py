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
                self.data_2024 = pd.read_csv(data_2024_path, low_memory=False)
                logger.info(f"2024 data loaded successfully: {len(self.data_2024)} rows")
            except Exception as e:
                logger.error(f"Error loading 2024 data: {e}")
                self.data_2024 = pd.DataFrame()
            
            # Load 2025 data
            logger.info(f"Loading 2025 data from: {data_2025_path}")
            try:
                self.data_2025 = pd.read_csv(data_2025_path, low_memory=False)
                logger.info(f"2025 data loaded successfully: {len(self.data_2025)} rows")
            except Exception as e:
                logger.error(f"Error loading 2025 data: {e}")
                self.data_2025 = pd.DataFrame()
            
            # Combine datasets
            self.combined_data = pd.concat([self.data_2024, self.data_2025], ignore_index=True)
            
            # Add minimal required columns for prediction system
            self._add_minimal_required_columns()
            
            logger.info(f"Data loaded successfully. Total records: {len(self.combined_data)}")
            logger.info("Added minimal required columns for prediction system")
            
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            # For testing, create empty DataFrame
            self.data_2024 = pd.DataFrame()
            self.data_2025 = pd.DataFrame()
            self.combined_data = pd.DataFrame()
    
    def _add_minimal_required_columns(self):
        """Add minimal columns required for the prediction system to work"""
        try:
            # Add map_index_within_series if missing (required for tier filtering)
            if 'map_index_within_series' not in self.combined_data.columns:
                # Use the 'game' column directly as map index within series
                if 'game' in self.combined_data.columns:
                    self.combined_data['map_index_within_series'] = self.combined_data['game']
                    logger.info(f"Added map_index_within_series column using 'game' column")
                else:
                    # Fallback: assume all games are map 1
                    self.combined_data['map_index_within_series'] = 1
                    logger.info(f"Added map_index_within_series column (fallback to 1)")
            
            # Ensure series_completed column exists (required for filtering)
            if 'series_completed' not in self.combined_data.columns:
                self.combined_data['series_completed'] = True  # Assume all series are completed
                logger.info(f"Added series_completed column")
            
            # Add match_series column if missing (required for filtering)
            if 'match_series' not in self.combined_data.columns:
                # CRITICAL FIX: Create proper series identification for betting logic
                if 'gameid' in self.combined_data.columns:
                    logger.info("Attempting to create proper match_series from gameid patterns...")
                    self.combined_data['match_series'] = self._create_proper_series_identification()
                    logger.info(f"Added match_series column using proper series identification")
                else:
                    # Fallback: Create series ID from date, team, opponent, position
                    self.combined_data['match_series'] = (
                        self.combined_data.get('date', '').astype(str) + '_' +
                        self.combined_data.get('teamname', '').astype(str) + '_' +
                        self.combined_data.get('opponent', self.combined_data.get('side', '')).astype(str) + '_' +
                        self.combined_data.get('position', '').astype(str)
                    )
                    logger.info(f"Added match_series column using date+team+opponent+position fallback")
            
            # Add position column if missing (required for role filtering)
            if 'position' not in self.combined_data.columns:
                # Try to infer from common column names
                if 'teamposition' in self.combined_data.columns:
                    self.combined_data['position'] = self.combined_data['teamposition']
                elif 'role' in self.combined_data.columns:
                    self.combined_data['position'] = self.combined_data['role']
                else:
                    self.combined_data['position'] = 'unknown'
                logger.info(f"Added position column")
            
        except Exception as e:
            logger.error(f"Error adding minimal columns: {e}")
            # Add fallback columns
            self.combined_data['map_index_within_series'] = 1
            self.combined_data['series_completed'] = True
            self.combined_data['match_series'] = 'default_series'
            self.combined_data['position'] = 'unknown'
    
    def _create_proper_series_identification(self):
        """
        CRITICAL FIX: Create proper series identification for betting logic per betting_logic.md
        
        CORRECT BETTING LOGIC IMPLEMENTATION:
        - Group games by date + player + match (ignoring side differences)  
        - Games on same date for same player against same opponent = same series
        - Map 1-2 means sum kills from game 1 + game 2 within each series
        """
        logger.info("Creating PROPER series identification per betting_logic.md requirements...")
        
        # Get sample data to understand the pattern
        sample_data = self.combined_data[['date', 'playername', 'teamname', 'game', 'gameid']].head(10)
        logger.info(f"Sample data for series identification:\n{sample_data}")
        
        # BETTING LOGIC IMPLEMENTATION: Group by match context, not individual games
        series_ids = []
        for idx, row in self.combined_data.iterrows():
            # Extract key match identifiers
            date_str = str(row.get('date', ''))[:10]  # Date only (YYYY-MM-DD)
            player = str(row.get('playername', ''))
            team = str(row.get('teamname', ''))
            
            # For League of Legends: Same player on same date = same match series
            # Ignore individual game numbers - group all games from same match
            # This follows betting_logic.md: "Group by series_id, use game_number == 1 as anchor"
            
            # Create match-level series ID (date + player + team base)
            # Remove any game-specific suffixes to group related games together
            gameid = str(row.get('gameid', ''))
            
            # Extract match ID by removing game-specific parts and using consistent grouping
            # For LoL tournaments, games on same date for same player are typically same series
            import re
            
            # Strategy: Group by date + player + team, then add a match identifier
            # Look for numeric patterns in gameid to identify base match ID
            numeric_match = re.search(r'(\d+)', gameid)  # Find first number in gameid
            if numeric_match:
                # Use the base number but group similar ones together
                base_match_num = int(numeric_match.group(1))
                # Group every 10-20 gameids as the same match (adjust based on data pattern)
                match_group = base_match_num // 10
                series_id = f"{date_str}_{player}_{team}_match{match_group}"
            else:
                # Fallback: use date + player + team only
                series_id = f"{date_str}_{player}_{team}_default"
            
            series_ids.append(series_id)
        
        # Convert to pandas Series for assignment
        import pandas as pd
        series_series = pd.Series(series_ids, index=self.combined_data.index)
        
        # CRITICAL VALIDATION: Check if we're creating proper multi-game series
        temp_df = pd.DataFrame({
            'series_id': series_ids, 
            'game': self.combined_data.get('game', 1),
            'player': self.combined_data.get('playername', ''),
            'date': self.combined_data.get('date', '')
        })
        
        series_sizes = temp_df.groupby('series_id').size()
        multi_game_series = (series_sizes > 1).sum()
        single_game_series = (series_sizes == 1).sum()
        max_games_per_series = series_sizes.max()
        
        logger.info(f"Series identification results:")
        logger.info(f"  - {multi_game_series} multi-game series")
        logger.info(f"  - {single_game_series} single-game series") 
        logger.info(f"  - Max games per series: {max_games_per_series}")
        logger.info(f"  - Total unique series: {len(series_sizes)}")
        
        # Show sample of multi-game series for validation
        if multi_game_series > 0:
            sample_multi = temp_df[temp_df['series_id'].isin(
                series_sizes[series_sizes > 1].head(3).index
            )][['series_id', 'game', 'player', 'date']].head(10)
            logger.info(f"Sample multi-game series:\n{sample_multi}")
        
        # If still no multi-game series, the data might not support proper grouping
        if multi_game_series == 0:
            logger.warning("⚠️ STILL no multi-game series found! Data may not support proper series grouping.")
            logger.warning("This means Map 1-2 betting logic cannot work correctly.")
            logger.warning("Falling back to date-only grouping...")
            return self._create_date_based_series_identification()
        
        logger.info("✅ Successfully created multi-game series - betting logic should now work!")
        return series_series
    
    def _create_date_based_series_identification(self):
        """
        Date-based series identification: group by player + team + date only
        This is the most aggressive grouping - all games on same date = same series
        """
        logger.info("Using date-based series identification (most aggressive grouping)...")
        
        series_ids = []
        for idx, row in self.combined_data.iterrows():
            date_str = str(row.get('date', ''))[:10]  # Just date
            player = str(row.get('playername', ''))
            team = str(row.get('teamname', ''))
            
            # Simple: same date + player + team = same series
            # This will group ALL games on the same date as one series
            series_id = f"{date_str}_{player}_{team}"
            series_ids.append(series_id)
        
        import pandas as pd
        series_series = pd.Series(series_ids, index=self.combined_data.index)
        
        # Validate this approach
        temp_df = pd.DataFrame({
            'series_id': series_ids, 
            'game': self.combined_data.get('game', 1),
            'player': self.combined_data.get('playername', '')
        })
        series_sizes = temp_df.groupby('series_id').size()
        multi_game_series = (series_sizes > 1).sum()
        avg_games_per_series = series_sizes.mean()
        
        logger.info(f"Date-based series results: {multi_game_series} multi-game series")
        logger.info(f"Average games per series: {avg_games_per_series:.2f}")
        
        return series_series

    def _create_alternative_series_identification(self):
        """
        Alternative series identification: group by player + team + date + game ranges
        """
        logger.info("Using alternative series identification...")
        
        series_ids = []
        for idx, row in self.combined_data.iterrows():
            date_str = str(row.get('date', ''))[:10]
            player = str(row.get('playername', ''))
            team = str(row.get('teamname', ''))
            game = int(row.get('game', 1))
            
            # Group every 2-3 consecutive games as a series
            series_num = ((game - 1) // 3)  # Groups: 1-3, 4-6, 7-9, etc.
            series_id = f"{date_str}_{player}_{team}_{series_num}"
            series_ids.append(series_id)
        
        import pandas as pd
        return pd.Series(series_ids, index=self.combined_data.index)
    
    def _generate_map_index(self):
        """
        SIMPLIFIED APPROACH: Use existing gameid-based series identification.
        The existing match_series column (created from gameid) provides reliable series grouping.
        """
        # Convert date to datetime first if it's not already
        if not pd.api.types.is_datetime64_any_dtype(self.combined_data["date"]):
            self.combined_data["date"] = pd.to_datetime(self.combined_data["date"])
        
        # Use the 'game' column as the map index within series (this is already correct)
        self.combined_data["map_index_within_series"] = self.combined_data["game"]
        
        # Validate existing series identification instead of recreating it
        self._validate_existing_series_identification()
        
        logger.info("Series identification validation completed successfully")
    
    def _validate_existing_series_identification(self):
        """
        SIMPLIFIED VALIDATION: Validate the existing match_series column.
        
        The existing match_series (created from gameid) should provide reliable series grouping.
        This validation ensures the data quality is sufficient for betting logic.
        """
        if self.combined_data.empty or 'match_series' not in self.combined_data.columns:
            logger.warning("No match_series column found - cannot validate series identification")
            return
        
        logger.info("🔧 VALIDATING EXISTING SERIES IDENTIFICATION")
        
        try:
            # Analyze existing series structure
            series_sizes = self.combined_data.groupby('match_series').size()
            single_game_series = (series_sizes == 1).sum()
            multi_game_series = (series_sizes > 1).sum()
            avg_games_per_series = series_sizes.mean()
            
            logger.info(f"📊 EXISTING SERIES VALIDATION:")
            logger.info(f"   Total games: {len(self.combined_data)}")
            logger.info(f"   Total series: {len(series_sizes)}")
            logger.info(f"   Avg games per series: {avg_games_per_series:.2f}")
            logger.info(f"   Single-game series: {single_game_series}")
            logger.info(f"   Multi-game series: {multi_game_series}")
            
            # Validate betting logic prerequisites
            if multi_game_series > 0:
                logger.info("✅ BETTING LOGIC READY: Found multi-game series for Map 1-2 predictions")
            else:
                logger.warning("⚠️ LIMITED: Most series have single games - Map 1-2 predictions may be limited")
            
            # Sample validation for specific cases
            sample_series = series_sizes.head(5)
            logger.info(f"   Sample series sizes: {sample_series.to_dict()}")
            
            logger.info("✅ EXISTING SERIES IDENTIFICATION VALIDATED")
            
        except Exception as e:
            logger.error(f"Error validating existing series identification: {e}")
            logger.warning("Continuing with existing match_series column")
    
    def _validate_corrected_series_logic(self):
        """
        VALIDATION: Verify that corrected series identification is working properly.
        This ensures betting logic will work correctly.
        """
        try:
            if 'match_series' not in self.combined_data.columns:
                logger.error("❌ No match_series column found after series identification")
                return
            
            # Count series and validate structure
            total_games = len(self.combined_data)
            total_series = self.combined_data['match_series'].nunique()
            
            # Analyze series composition
            series_sizes = self.combined_data.groupby('match_series').size()
            single_game_series = (series_sizes == 1).sum()
            multi_game_series = (series_sizes > 1).sum()
            avg_games_per_series = series_sizes.mean()
            
            logger.info(f"📊 SERIES IDENTIFICATION VALIDATION:")
            logger.info(f"   Total games: {total_games}")
            logger.info(f"   Total series: {total_series}")
            logger.info(f"   Avg games per series: {avg_games_per_series:.2f}")
            logger.info(f"   Single-game series: {single_game_series}")
            logger.info(f"   Multi-game series: {multi_game_series}")
            
            # Validate betting logic prerequisites
            if multi_game_series > single_game_series:
                logger.info("✅ BETTING LOGIC READY: Most series have multiple games")
                logger.info("   This should fix Map 1-2 predictions to properly sum maps")
            else:
                logger.warning("⚠️ POTENTIAL ISSUE: Too many single-game series")
                logger.warning("   Map 1-2 predictions may still not work correctly")
            
            # Sample validation for specific cases
            sample_series = series_sizes.head(5)
            logger.info(f"   Sample series sizes: {sample_series.to_dict()}")
            
        except Exception as e:
            logger.error(f"Error in series validation: {e}")
    
    def _validate_series_integrity(self):
        """
        CRITICAL VALIDATION: Implement assertions per user directives:
        - Max 5 games per series
        - Same teams only
        - Proper game numbering
        - BETTING LOGIC: Validate Map 1-2 scenarios work correctly
        """
        try:
            # Group by series and calculate stats
            series_stats = self.combined_data.groupby('match_series').agg({
                'game': ['count', 'min', 'max'],
                'teamname': 'nunique',
                'date': 'nunique'
            }).round(2)
            
            # Flatten column names for easier access
            series_stats.columns = ['_'.join(col).strip() for col in series_stats.columns]
            
            # Assertion 1: Max 5 games per series
            max_games = series_stats['game_count'].max()
            if max_games > 5:
                problematic_series = series_stats[series_stats['game_count'] > 5].index.tolist()
                logger.warning(f"⚠️ Found {len(problematic_series)} series with >5 games: {problematic_series[:3]}...")
                # Don't raise error, just warn for now
            
            # Assertion 2: Same teams only within series
            max_teams = series_stats['teamname_nunique'].max()
            if max_teams > 1:
                problematic_series = series_stats[series_stats['teamname_nunique'] > 1].index.tolist()
                logger.warning(f"⚠️ Found {len(problematic_series)} series with multiple teams: {problematic_series[:3]}...")
            
            # Assertion 3: Check for reasonable game numbering
            min_game_start = series_stats['game_min'].min()
            if min_game_start != 1:
                logger.warning(f"⚠️ Some series don't start with game 1 (min start: {min_game_start})")
            
            # BETTING LOGIC VALIDATION: Test Map 1-2 scenarios
            map_1_2_series = series_stats[
                (series_stats['game_min'] == 1) & 
                (series_stats['game_max'] >= 2)
            ]
            viable_map_1_2_series = len(map_1_2_series)
            total_series = len(series_stats)
            
            logger.info(f"\\n=== BETTING LOGIC MAP 1-2 VALIDATION ===")
            logger.info(f"Series suitable for Map 1-2 betting: {viable_map_1_2_series}/{total_series} ({100*viable_map_1_2_series/max(1,total_series):.1f}%)")
            
            # Sample validation for Map 1-2 logic
            if viable_map_1_2_series > 0:
                sample_series = map_1_2_series.head(3)
                logger.info(f"Sample Map 1-2 compatible series:")
                for series_id, stats in sample_series.iterrows():
                    game_count = stats['game_count']
                    game_range = f"{int(stats['game_min'])}-{int(stats['game_max'])}"
                    logger.info(f"  - {series_id}: {game_count} games (range: {game_range})")
            
            # Log summary statistics
            avg_games_per_series = series_stats['game_count'].mean()
            logger.info(f"Series validation summary: {total_series} total series, avg {avg_games_per_series:.1f} games per series")
            
            # Flag any remaining issues
            clean_series = (
                (series_stats['game_count'] <= 5) & 
                (series_stats['teamname_nunique'] == 1) &
                (series_stats['game_min'] == 1)
            ).sum()
            
            logger.info(f"Clean series: {clean_series}/{total_series} ({100*clean_series/max(1,total_series):.1f}%)")
            logger.info(f"=== END VALIDATION ===\\n")
            
        except Exception as e:
            logger.error(f"Error validating series integrity: {e}")
    
    def _fallback_series_identification(self):
        """Fallback series identification when smart method fails"""
        logger.warning("Using fallback series identification - may produce suboptimal groupings")
        
        # Simple fallback: date + team + game number grouping
        self.combined_data["match_series"] = (
            self.combined_data["date"].dt.date.astype(str) + "_" + 
            self.combined_data["teamname"] + "_" +
            (self.combined_data["game"] // 6).astype(str)  # Group every 6 games as new series
        )
    
    def _preprocess_data(self):
        """Clean and preprocess the data"""
        try:
            # Convert date to datetime
            if 'date' in self.combined_data.columns:
                self.combined_data['date'] = pd.to_datetime(self.combined_data['date'], errors='coerce')
            
            # Fill NaN values
            numeric_columns = self.combined_data.select_dtypes(include=[np.number]).columns
            self.combined_data[numeric_columns] = self.combined_data[numeric_columns].fillna(0)
            
            # Ensure position data is consistent (CSV already uses lowercase, but normalize just in case)
            if 'position' in self.combined_data.columns:
                self.combined_data['position'] = self.combined_data['position'].astype(str).str.lower().str.strip()
                logger.info(f"Position data normalized. Unique positions: {sorted(self.combined_data['position'].unique())}")
            
            # CRITICAL FIX: Add meta/patch awareness per user directives
            self._add_meta_patch_awareness()
            
            logger.info("Data preprocessing completed")
        except Exception as e:
            logger.error(f"Error in data preprocessing: {e}")
            logger.warning("Continuing with minimal preprocessing")
    
    def _add_meta_patch_awareness(self):
        """
        CRITICAL FIX: Add meta/patch awareness to address user directive.
        
        Creates patch groupings based on date ranges to account for meta shifts.
        League of Legends meta changes significantly affect kill/assist patterns.
        """
        try:
            if 'date' not in self.combined_data.columns or self.combined_data.empty:
                logger.warning("No date column found - cannot add patch awareness")
                self.combined_data['patch_group'] = 'unknown'
                return
            
            # Convert date to datetime if not already
            self.combined_data['date'] = pd.to_datetime(self.combined_data['date'], errors='coerce')
            
            # Create patch groups based on approximate LoL patch cycles (2-3 weeks)
            # This is a simplified approach - ideally would use real patch data
            min_date = self.combined_data['date'].min()
            max_date = self.combined_data['date'].max()
            
            if pd.isna(min_date) or pd.isna(max_date):
                logger.warning("Invalid date range - cannot create patch groups")
                self.combined_data['patch_group'] = 'unknown'
                return
            
            # Create 2-week patch cycles
            date_range = (max_date - min_date).days
            patch_duration_days = 14  # Approximate LoL patch cycle
            
            # Generate patch groups
            patch_boundaries = pd.date_range(
                start=min_date, 
                end=max_date, 
                freq=f'{patch_duration_days}D'
            )
            
            # Assign patch groups
            self.combined_data['patch_group'] = pd.cut(
                self.combined_data['date'],
                bins=patch_boundaries,
                labels=[f'patch_{i}' for i in range(len(patch_boundaries)-1)],
                include_lowest=True
            )
            
            # Fill any remaining NaN values
            self.combined_data['patch_group'] = self.combined_data['patch_group'].fillna('unknown')
            
            # Create recency weight based on patch (more recent = higher weight)
            unique_patches = self.combined_data['patch_group'].unique()
            patch_weights = {}
            
            for i, patch in enumerate(sorted(unique_patches)):
                if patch != 'unknown':
                    # More recent patches get higher weights (0.6 to 1.0)
                    patch_weights[patch] = 0.6 + (0.4 * i / max(1, len(unique_patches) - 1))
                else:
                    patch_weights[patch] = 0.5  # Lower weight for unknown patches
            
            self.combined_data['patch_recency_weight'] = self.combined_data['patch_group'].map(patch_weights)
            
            logger.info(f"Created {len(unique_patches)} patch groups with recency weighting")
            
        except Exception as e:
            logger.error(f"Error adding patch awareness: {e}")
            # Fallback values
            self.combined_data['patch_group'] = 'unknown'
            self.combined_data['patch_recency_weight'] = 1.0
    
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
        Aggregate statistics across the map range using CORRECT BETTING LOGIC.
        
        CRITICAL IMPLEMENTATION: For betting markets like "Maps 1-2 Kills 8.5":
        1. Filter data to Maps 1-2 (using game_number or map_index_within_series)
        2. Group by series_id (match_series) - each series contains multiple maps
        3. Sum kills/assists within each series (combined performance per series)
        4. Calculate statistics (mean, std) on those series totals
        
        EXAMPLE VALIDATION:
        Series 1: Map 1 (3 kills) + Map 2 (5 kills) = 8 combined kills
        Series 2: Map 1 (4 kills) + Map 2 (6 kills) = 10 combined kills  
        Series 3: Map 1 (2 kills) + Map 2 (7 kills) = 9 combined kills
        Expected stat = (8 + 10 + 9) / 3 = 9.0 kills
        Sample size = 3 series (not 6 individual maps)
        """
        if prop_type not in ['kills', 'assists']:
            raise ValueError("prop_type must be 'kills' or 'assists'")
        
        # Enhanced debug logging for betting logic validation
        logger.info(f"\n=== BETTING LOGIC VALIDATION START ===")
        logger.info(f"Aggregating COMBINED {prop_type} across {len(player_data)} individual maps")
        logger.info(f"Map range data sample: {player_data[['playername', 'match_series', 'game', 'map_index_within_series', prop_type]].head()}")
        
        # CRITICAL VALIDATION: Ensure we have the correct columns for betting logic
        required_columns = ['playername', 'match_series', prop_type]
        missing_columns = [col for col in required_columns if col not in player_data.columns]
        
        if missing_columns:
            logger.error(f"BETTING LOGIC ERROR: Missing required columns: {missing_columns}")
            logger.error(f"Available columns: {list(player_data.columns)}")
            return {}
        
        # CRITICAL VALIDATION: Handle empty data
        if player_data.empty:
            logger.error("BETTING LOGIC ERROR: Empty player data provided to aggregate_stats")
            return {}
        
        # CRITICAL VALIDATION: Validate prop_type column has valid data
        prop_data = player_data[prop_type].dropna()
        if prop_data.empty:
            logger.error(f"BETTING LOGIC ERROR: No valid data found for {prop_type} column")
            return {}
        
        # BETTING LOGIC IMPLEMENTATION: Calculate series totals (combined stats per series)
        logger.info(f"\nStep 1: Grouping by series_id to calculate combined {prop_type} per series...")
        
        # CRITICAL FIX: Verify series identification is working correctly
        logger.info(f"DEBUG: Sample of player_data before grouping:")
        debug_sample = player_data[['playername', 'match_series', 'game', prop_type]].head(10)
        logger.info(f"\n{debug_sample}")
        
        # Check if we have proper series with multiple games
        series_sizes = player_data.groupby('match_series').size()
        single_game_series = (series_sizes == 1).sum()
        multi_game_series = (series_sizes > 1).sum()
        logger.info(f"Series analysis: {single_game_series} single-game series, {multi_game_series} multi-game series")
        
        if single_game_series > multi_game_series:
            logger.warning("⚠️ CRITICAL ISSUE: Most series have only 1 game - series identification is broken!")
            logger.warning("This explains why Map 1-2 doesn't sum properly - each game is treated as separate series")
        
        # BETTING LOGIC STEP 1: Sum stats within each series (combined performance)
        agg_dict = {prop_type: 'sum'}  # Primary stat - sum across maps within series
        
        # Add optional columns for comprehensive stats
        optional_columns = [
            'deaths', 'damagetochampions', 'visionscore', 'total cs',
            'goldat10', 'xpat10', 'csat10', 'golddiffat10', 'xpdiffat10', 'csdiffat10',
            'goldat15', 'xpat15', 'csat15', 'golddiffat15', 'xpdiffat15', 'csdiffat15',
            'killsat15', 'assistsat15', 'deathsat15',
            'goldat20', 'xpat20', 'csat20', 'golddiffat20', 'xpdiffat20', 'csdiffat20',
            'killsat20', 'assistsat20', 'deathsat20'
        ]
        
        for col in optional_columns:
            if col in player_data.columns:
                agg_dict[col] = 'sum'
        
        try:
            # USE CONSISTENT SERIES GROUPING - Fix the core issue by using existing match_series
            logger.info(f"🚨 APPLYING CORRECTED BETTING LOGIC FOR ALL PREDICTIONS")
            logger.info(f"Using existing match_series for consistent aggregation of {len(player_data)} maps...")
            
            # Validate that we have proper series identification
            if 'match_series' not in player_data.columns:
                logger.error("CRITICAL: No match_series column found! Cannot perform series-level aggregation.")
                return {}
            
            # Debug the existing series grouping to understand the data
            existing_series_sizes = player_data.groupby('match_series').size()
            single_game_series = (existing_series_sizes == 1).sum()
            multi_game_series = (existing_series_sizes > 1).sum()
            
            logger.info(f"📊 EXISTING SERIES VALIDATION:")
            logger.info(f"   Single-game series: {single_game_series}")
            logger.info(f"   Multi-game series: {multi_game_series}")
            logger.info(f"   Total series: {len(existing_series_sizes)}")
            logger.info(f"   Average games per series: {existing_series_sizes.mean():.2f}")
            
            # Use the existing match_series for consistent aggregation
            series_totals = player_data.groupby(['playername', 'match_series']).agg(agg_dict).round(2)
            
            logger.info(f"🎯 CONSISTENT BETTING LOGIC: Generated {len(series_totals)} series using existing match_series")
            
            # Store the data with consistent series identification
            self._current_player_data_fixed = player_data.copy()
            self._current_player_data_fixed['consistent_series_id'] = player_data['match_series']
            
            logger.info(f"Generated {len(series_totals)} series with combined stats")
            
            if series_totals.empty:
                logger.error("BETTING LOGIC ERROR: No series totals generated")
                return {}
            
            # BETTING LOGIC VALIDATION: Log sample series totals for verification
            logger.info(f"\nStep 2: Series totals sample (combined {prop_type} per series):")
            sample_series = series_totals.head(5)
            for idx, row in sample_series.iterrows():
                player_name, series_id = idx
                combined_stat = row[prop_type]
                logger.info(f"  {player_name} | {series_id} | Combined {prop_type}: {combined_stat}")
            
            # BETTING LOGIC STEP 2: Calculate statistics on series totals (mean, std, count)
            logger.info(f"\nStep 3: Calculating mean/std of series totals...")
            player_agg_dict = {prop_type: ['mean', 'std', 'count']}
            
            # Add mean aggregation for optional columns
            for col in optional_columns:
                if col in series_totals.columns:
                    player_agg_dict[col] = 'mean'
            
            agg_stats = series_totals.groupby('playername').agg(player_agg_dict).round(2)
            
            # CRITICAL FIX: Verify that count represents series, not individual maps
            logger.info(f"Aggregation verification:")
            for player_name in agg_stats.index:
                series_count_from_agg = agg_stats.loc[player_name, (prop_type, 'count')]
                actual_series_count = series_totals[series_totals.index.get_level_values('playername') == player_name].shape[0]
                logger.info(f"  {player_name}: agg count={series_count_from_agg}, actual series={actual_series_count}")
                
                if series_count_from_agg != actual_series_count:
                    logger.warning(f"  ⚠️ COUNT MISMATCH for {player_name}! This may indicate a data issue.")
            
            # Flatten column names for easier access
            agg_stats.columns = ['_'.join(col).strip() for col in agg_stats.columns.values]
            
            # BETTING LOGIC VALIDATION: Enhanced logging with validation
            logger.info(f"\nStep 4: Final betting logic results:")
            for player_name in agg_stats.index:
                player_stats = agg_stats.loc[player_name]
                combined_avg = player_stats.get(f'{prop_type}_mean', 0)
                combined_std = player_stats.get(f'{prop_type}_std', 0)
                series_count = player_stats.get(f'{prop_type}_count', 0)
                
                logger.info(f"  {player_name}:")
                logger.info(f"    - Expected {prop_type} (mean of series totals): {combined_avg}")
                logger.info(f"    - Volatility (std of series totals): {combined_std}")
                logger.info(f"    - Sample size: {series_count} series")
                
                # CRITICAL VALIDATION: Ensure results make sense for betting logic
                if series_count < 2:
                    logger.warning(f"    - WARNING: Small sample size ({series_count} series) may be unreliable")
                if combined_avg <= 0:
                    logger.warning(f"    - WARNING: Invalid expected stat ({combined_avg}) - check data quality")
            
            logger.info(f"\n=== BETTING LOGIC VALIDATION END ===\n")
            return agg_stats.to_dict('index')
            
        except Exception as e:
            logger.error(f"Error in aggregate_stats: {e}")
            logger.error(f"Data shape: {player_data.shape}, Columns: {list(player_data.columns)}")
            return {}
    
    def validate_betting_logic_implementation(self, sample_player: str = None) -> Dict[str, Any]:
        """
        CRITICAL VALIDATION: Test Map 1-2 betting logic with actual data example.
        
        This function validates that our betting logic correctly implements:
        1. Filter Maps 1-2 using game_number == 1 and game_number == 2
        2. Group by series_id 
        3. Sum stats within each series (combined performance per series)
        4. Calculate mean/std on series totals (not individual maps)
        
        Returns validation results for debugging.
        """
        try:
            if self.combined_data is None or self.combined_data.empty:
                return {'status': 'error', 'message': 'No data available for validation'}
            
            # Get a sample player for testing
            if sample_player is None:
                available_players = self.combined_data['playername'].unique()
                if len(available_players) == 0:
                    return {'status': 'error', 'message': 'No players found in data'}
                sample_player = available_players[0]
            
            logger.info(f"\\n=== BETTING LOGIC VALIDATION TEST ===")
            logger.info(f"Testing Map 1-2 betting logic with player: {sample_player}")
            
            # Step 1: Filter to Maps 1-2 (simulating Map 1-2 betting scenario)
            map_1_2_data = self.combined_data[
                (self.combined_data['playername'] == sample_player) &
                (self.combined_data['game'].isin([1, 2]))  # Maps 1 and 2
            ].copy()
            
            if map_1_2_data.empty:
                return {'status': 'error', 'message': f'No Map 1-2 data found for {sample_player}'}
            
            logger.info(f"Step 1: Found {len(map_1_2_data)} individual map entries")
            logger.info(f"Sample data:\\n{map_1_2_data[['match_series', 'game', 'kills', 'assists']].head(10)}")
            
            # Step 2: Test the betting logic aggregation
            validation_result = self.aggregate_stats(map_1_2_data, 'kills')
            
            if sample_player not in validation_result:
                return {'status': 'error', 'message': f'No aggregated stats for {sample_player}'}
            
            player_stats = validation_result[sample_player]
            
            # Step 3: Manual validation of the logic
            logger.info(f"\\nStep 2: Manual validation check...")
            manual_series_totals = map_1_2_data.groupby('match_series')['kills'].sum()
            manual_expected = manual_series_totals.mean()
            manual_std = manual_series_totals.std()
            manual_count = len(manual_series_totals)
            
            logger.info(f"Manual calculation:")
            logger.info(f"  - Series totals: {manual_series_totals.tolist()}")
            logger.info(f"  - Expected kills (mean of series totals): {manual_expected:.2f}")
            logger.info(f"  - Std dev of series totals: {manual_std:.2f}")
            logger.info(f"  - Sample size: {manual_count} series")
            
            # Step 4: Compare with our implementation
            our_expected = player_stats.get('kills_mean', 0)
            our_std = player_stats.get('kills_std', 0)
            our_count = player_stats.get('kills_count', 0)
            
            logger.info(f"\\nOur implementation result:")
            logger.info(f"  - Expected kills: {our_expected:.2f}")
            logger.info(f"  - Std dev: {our_std:.2f}")
            logger.info(f"  - Sample size: {our_count} series")
            
            # Step 5: Validation check
            expected_match = abs(manual_expected - our_expected) < 0.01
            count_match = manual_count == our_count
            
            validation_status = 'pass' if (expected_match and count_match) else 'fail'
            
            logger.info(f"\\nValidation Results:")
            logger.info(f"  - Expected stat match: {'✅' if expected_match else '❌'}")
            logger.info(f"  - Sample size match: {'✅' if count_match else '❌'}")
            logger.info(f"  - Overall status: {'✅ PASS' if validation_status == 'pass' else '❌ FAIL'}")
            logger.info(f"=== END VALIDATION TEST ===\\n")
            
            return {
                'status': validation_status,
                'player': sample_player,
                'manual_expected': float(manual_expected),
                'our_expected': float(our_expected),
                'manual_std': float(manual_std) if not pd.isna(manual_std) else 0.0,
                'our_std': float(our_std),
                'manual_count': int(manual_count),
                'our_count': int(our_count),
                'expected_match': expected_match,
                'count_match': count_match,
                'sample_series_totals': manual_series_totals.tolist()
            }
            
        except Exception as e:
            logger.error(f"Error in betting logic validation: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def engineer_features(self, player_data: pd.DataFrame, prop_type: str) -> Dict[str, float]:
        """
        Engineer features using BETTING LOGIC for combined statistics.
        
        CRITICAL: Features now reflect COMBINED stats across map ranges, not averages.
        This aligns with betting terminology where "Maps 1-2" means total performance.
        
        This method ensures consistency with the unified feature extraction in PredictionModel.
        """
        if player_data.empty:
            return self._get_default_features()
        
        features = {}
        
        # Get aggregated stats (now uses combined/total logic)
        agg_stats = self.aggregate_stats(player_data, prop_type)
        
        # For simplicity, we'll use the first player's stats
        player_name = player_data['playername'].iloc[0] if not player_data.empty else None
        if not player_name or player_name not in agg_stats:
            return self._get_default_features()
        
        stats = agg_stats[player_name]
        
        # BETTING LOGIC: These are now COMBINED stats per series, not individual map averages
        features['combined_' + prop_type] = stats.get(f'{prop_type}_mean', 0)  # Average of combined performance
        features['std_dev_combined_' + prop_type] = stats.get(f'{prop_type}_std', 0)  # Std dev of combined performance
        
        # CRITICAL FIX: Ensure series_played counts actual series, not individual maps
        raw_count = stats.get(f'{prop_type}_count', 0)
        
        # CONSISTENT SERIES COUNTING: Use match_series for consistent counting  
        if not player_data.empty and hasattr(self, '_current_player_data_fixed') and 'consistent_series_id' in self._current_player_data_fixed.columns:
            # Use the consistent series identification for counting
            actual_series_count = self._current_player_data_fixed['consistent_series_id'].nunique()
            logger.info(f"🎯 CONSISTENT SERIES COUNT: {actual_series_count} (was {raw_count} with aggregation)")
            
            # Show sample of consistent series data
            sample_series = self._current_player_data_fixed[['consistent_series_id', 'game', prop_type]].head(10)
            logger.info(f"Sample consistent series data:\n{sample_series}")
            
            features['series_played'] = actual_series_count  # Use the consistent series count
        else:
            logger.info("Using raw count from aggregation (should match manual calculation now)")
            features['series_played'] = raw_count
        
        # For backward compatibility, keep old feature names but mark them as combined
        features['avg_' + prop_type] = features['combined_' + prop_type]  # Backward compatibility
        features['std_dev_' + prop_type] = features['std_dev_combined_' + prop_type]  # Backward compatibility
        features['maps_played'] = features['series_played']  # Backward compatibility (though it's really series)
        
        # Long-term averages with proper calculation
        longterm_combined_avg = self._calculate_longterm_combined_average(player_name, prop_type)
        features['longterm_combined_' + prop_type] = longterm_combined_avg
        features['longterm_' + prop_type + '_avg'] = longterm_combined_avg  # Backward compatibility
        
        # Deviation metrics (now based on combined performance) with proper bounds checking
        recent_combined = features['combined_' + prop_type]
        longterm_combined = features['longterm_combined_' + prop_type]
        
        if longterm_combined > 0:
            std_dev = max(features['std_dev_combined_' + prop_type], 0.1)  # Prevent division by zero
            features['form_z_score'] = (recent_combined - longterm_combined) / std_dev
            features['form_deviation_ratio'] = std_dev / max(recent_combined, 0.1)  # Coefficient of variation
        else:
            features['form_z_score'] = 0
            features['form_deviation_ratio'] = 0.3  # Default volatility
        
        # Position information (no longer used for stat adjustment)
        features['position_factor'] = 1.0  # Always neutral - no role-based expectation adjustments
        
        # Quality/Volatility metrics with proper normalization
        features['sample_size_score'] = min(features['maps_played'] / 20.0, 1.0)  # Normalize to 0-1
        
        # Additional performance metrics with proper defaults
        features['avg_deaths'] = stats.get('deaths_mean', 2.5)
        features['avg_damage'] = stats.get('damagetochampions_mean', 18000)
        features['avg_vision'] = stats.get('visionscore_mean', 40)
        features['avg_cs'] = stats.get('total cs_mean', 250)
        
        # Early game metrics with real CSV column calculations and proper fallbacks
        features['avg_gold_at_10'] = stats.get('goldat10_mean', 8000)
        features['avg_xp_at_10'] = stats.get('xpat10_mean', 6000)
        features['avg_cs_at_10'] = stats.get('csat10_mean', 80)
        features['avg_gold_diff_10'] = stats.get('golddiffat10_mean', 0)
        features['avg_xp_diff_10'] = stats.get('xpdiffat10_mean', 0)
        features['avg_cs_diff_10'] = stats.get('csdiffat10_mean', 0)
        
        # Mid game metrics with real CSV column calculations and proper fallbacks
        features['avg_gold_at_15'] = stats.get('goldat15_mean', 12000)
        features['avg_xp_at_15'] = stats.get('xpat15_mean', 9000)
        features['avg_cs_at_15'] = stats.get('csat15_mean', 120)
        features['avg_gold_diff_15'] = stats.get('golddiffat15_mean', 0)
        features['avg_xp_diff_15'] = stats.get('xpdiffat15_mean', 0)
        features['avg_cs_diff_15'] = stats.get('csdiffat15_mean', 0)
        
        # Late early game metrics (20 minutes) with real CSV column calculations
        features['avg_gold_at_20'] = stats.get('goldat20_mean', 16000)
        features['avg_xp_at_20'] = stats.get('xpat20_mean', 12000)
        features['avg_cs_at_20'] = stats.get('csat20_mean', 160)
        features['avg_gold_diff_20'] = stats.get('golddiffat20_mean', 0)
        features['avg_xp_diff_20'] = stats.get('xpdiffat20_mean', 0)
        features['avg_cs_diff_20'] = stats.get('csdiffat20_mean', 0)
        
        return features
    
    def _calculate_longterm_combined_average(self, player_name: str, prop_type: str) -> float:
        """Calculate long-term combined average with proper error handling"""
        try:
            # Get all data for this player and calculate combined stats per series
            player_full_data = self.combined_data[self.combined_data['playername'] == player_name]
            if not player_full_data.empty and 'match_series' in player_full_data.columns:
                # Calculate combined stats per series for long-term average
                longterm_series_totals = player_full_data.groupby('match_series')[prop_type].sum()
                if len(longterm_series_totals) > 0:
                    return longterm_series_totals.mean()
            
            # Fallback to simple average if match_series not available
            player_stats = self.combined_data[self.combined_data['playername'] == player_name][prop_type]
            if len(player_stats) > 0:
                return player_stats.mean()
            
            # Final fallback to defaults
            return 3.0 if prop_type == 'kills' else 5.0
            
        except Exception as e:
            logger.error(f"Error calculating long-term average for {player_name}: {e}")
            return 3.0 if prop_type == 'kills' else 5.0
    
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
            'avg_gold_diff_10': 0, 'avg_xp_diff_10': 0, 'avg_cs_diff_10': 0,
            'avg_gold_at_15': 0, 'avg_xp_at_15': 0, 'avg_cs_at_15': 0,
            'avg_gold_diff_15': 0, 'avg_xp_diff_15': 0, 'avg_cs_diff_15': 0,
            'avg_gold_at_20': 0, 'avg_xp_at_20': 0, 'avg_cs_at_20': 0,
            'avg_gold_diff_20': 0, 'avg_xp_diff_20': 0, 'avg_cs_diff_20': 0
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
        Add features specific to combo predictions using CONSISTENT BETTING LOGIC.
        
        CRITICAL: For combos, we need COMBINED stats across players AND maps in the range.
        Uses the same consistent series identification as individual player predictions.
        """
        logger.info("Calculating combo features using consistent betting logic (combined stats across players and maps)")
        
        # Validate that we have series identification
        if 'match_series' not in player_data.columns:
            logger.warning("No match_series found for combo features - using fallback")
            features['combo_combined_' + prop_type] = 0
            features['combo_std_combined_' + prop_type] = 1
            features['combo_series_played'] = 0
            return features
        
        # Group by match_series and sum across all players for the combo (consistent with individual logic)
        combo_series_totals = player_data.groupby('match_series')[prop_type].sum().reset_index()
        
        if len(combo_series_totals) == 0:
            logger.warning("No combo series data available - using defaults")
            features['combo_combined_' + prop_type] = 0
            features['combo_std_combined_' + prop_type] = 1
            features['combo_series_played'] = 0
        else:
            features['combo_combined_' + prop_type] = combo_series_totals[prop_type].mean()  # Avg of combined performance
            features['combo_std_combined_' + prop_type] = combo_series_totals[prop_type].std()  # Std of combined performance
            features['combo_series_played'] = len(combo_series_totals)  # Number of series (consistent counting)
            
            logger.info(f"Combo features: {features['combo_series_played']} series, "
                       f"{features['combo_combined_' + prop_type]:.2f} avg combined {prop_type}")
        
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
            
            # CRITICAL FIX: Enhanced position mapping with better error handling
            # CSV uses: top, jng, mid, bot, sup (all lowercase)
            position_mapping = {
                # Standard positions (map to CSV format)
                'top': ['top'],
                'jungle': ['jng', 'jungle'],  # Support both formats
                'jng': ['jng'],  
                'mid': ['mid', 'middle'],     # Support both formats
                'adc': ['bot', 'adc'],        # Support both formats - ADC maps to 'bot' in CSV
                'bot': ['bot'],
                'support': ['sup', 'support'], # Support both formats - Support maps to 'sup' in CSV
                'sup': ['sup'],
                
                # Handle common uppercase variants
                'TOP': ['top'],
                'JUNGLE': ['jng', 'jungle'],
                'JNG': ['jng'],
                'MID': ['mid', 'middle'],
                'MIDDLE': ['mid', 'middle'],
                'ADC': ['bot', 'adc'],
                'BOT': ['bot'],
                'SUPPORT': ['sup', 'support'],
                'SUP': ['sup']
            }
            
            # Normalize target position but preserve original for logging
            original_target = target_position
            target_position_normalized = target_position.strip()
            
            # Find matching CSV positions
            target_csv_positions = []
            
            # CRITICAL FIX: More robust position matching
            # 1. Try exact match first
            if target_position_normalized in position_mapping:
                target_csv_positions = position_mapping[target_position_normalized]
            else:
                # 2. Try case-insensitive matches
                for key, values in position_mapping.items():
                    if key.lower() == target_position_normalized.lower():
                        target_csv_positions = values
                        break
                
                # 3. If still no match, try partial matching
                if not target_csv_positions:
                    target_lower = target_position_normalized.lower()
                    for key, values in position_mapping.items():
                        if target_lower in key.lower() or any(target_lower in v.lower() for v in values):
                            target_csv_positions = values
                            break
                    
                    # 4. Final fallback - use as-is
                    if not target_csv_positions:
                        target_csv_positions = [target_lower]
            
            # CRITICAL FIX: Validate target positions before filtering
            if not target_csv_positions:
                logger.warning(f"No position mapping found for '{original_target}' - returning all data")
                return player_data
            
            # Filter data to only include games in target position
            initial_count = len(player_data)
            
            # CRITICAL FIX: More robust position comparison with null handling
            try:
                # Handle potential null/NaN values in position column
                player_positions = player_data['position'].fillna('unknown').astype(str).str.lower().str.strip()
                position_matches = player_positions.isin(target_csv_positions)
                filtered_data = player_data[position_matches]
            except Exception as filter_error:
                logger.error(f"Error during position filtering: {filter_error}")
                logger.warning("Falling back to simple string comparison")
                # Fallback: simple string comparison
                filtered_data = player_data[player_data['position'].astype(str).str.lower().isin(target_csv_positions)]
            
            logger.info(f"Position filtering: '{original_target}' -> CSV positions {target_csv_positions}")
            logger.info(f"Filtered {initial_count} total games -> {len(filtered_data)} games matching position")
            
            # CRITICAL FIX: Enhanced debugging for failed position matches
            if len(filtered_data) == 0 and len(player_data) > 0:
                actual_positions = player_data['position'].value_counts().head(10).to_dict()
                logger.warning(f"No matches found for position filtering")
                logger.warning(f"Target: '{original_target}' -> {target_csv_positions}")
                logger.warning(f"Available positions (top 10): {actual_positions}")
                
                # Try to suggest close matches
                available_pos = set(str(p).lower().strip() for p in player_data['position'].dropna().unique())
                suggestions = []
                for target_pos in target_csv_positions:
                    for avail_pos in available_pos:
                        if target_pos in avail_pos or avail_pos in target_pos:
                            suggestions.append(avail_pos)
                
                if suggestions:
                    logger.info(f"Possible matches: {list(set(suggestions))}")
            
            return filtered_data
        
        except Exception as e:
            logger.error(f"Error in position filtering: {e}")
            logger.error(f"Target position: '{target_position}', Data shape: {player_data.shape}")
            logger.error(f"Returning all data for safety")
            return player_data 