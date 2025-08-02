import unittest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
import sys
import os

# Add the app directory to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.utils.data_processor import DataProcessor


class TestDataProcessor(unittest.TestCase):
    """Test cases for DataProcessor class"""

    def setUp(self):
        """Set up test fixtures before each test method"""
        # Create mock data for testing
        self.mock_data_2024 = pd.DataFrame({
            'playername': ['Player1', 'Player2', 'Player1', 'Player3'],
            'teamname': ['Team1', 'Team1', 'Team2', 'Team3'],
            'gameid': ['game1_1', 'game1_2', 'game2_1', 'game3_1'],
            'date': ['2024-01-01', '2024-01-01', '2024-01-02', '2024-01-03'],
            'position': ['mid', 'sup', 'mid', 'jng'],
            'kills': [5, 2, 3, 4],
            'assists': [8, 12, 6, 3],
            'deaths': [2, 4, 1, 5],
            'damagetochampions': [15000, 8000, 12000, 18000],
            'visionscore': [25, 35, 20, 15],
            'total cs': [200, 50, 180, 120],
            'year': [2024, 2024, 2024, 2024],
            'league': ['LPL', 'LPL', 'LPL', 'LPL'],
            'goldat10': [3000, 2500, 2800, 3200],
            'xpat10': [2000, 1800, 1900, 2100],
            'csat10': [80, 60, 75, 90],
            'golddiffat15': [500, -200, 300, 800],
            'xpdiffat15': [300, -100, 200, 500],
            'csdiffat15': [20, -10, 15, 30],
            'killsat15': [2, 1, 1, 2],
            'assistsat15': [3, 5, 2, 1],
            'deathsat15': [1, 2, 0, 1],
            'goldat20': [6000, 5000, 5500, 6500],
            'xpat20': [4000, 3500, 3800, 4200],
            'csat20': [150, 120, 140, 160],
            'killsat20': [3, 1, 2, 3],
            'assistsat20': [5, 8, 3, 2],
            'deathsat20': [1, 3, 1, 2]
        })
        
        self.mock_data_2025 = pd.DataFrame({
            'playername': ['Player1', 'Player4', 'Player2', 'Player5'],
            'teamname': ['Team1', 'Team4', 'Team1', 'Team5'],
            'gameid': ['game4_1', 'game5_1', 'game4_2', 'game6_1'],
            'date': ['2025-01-01', '2025-01-01', '2025-01-01', '2025-01-02'],
            'position': ['mid', 'bot', 'sup', 'top'],
            'kills': [6, 4, 1, 3],
            'assists': [7, 5, 15, 2],
            'deaths': [1, 3, 2, 4],
            'damagetochampions': [16000, 14000, 6000, 12000],
            'visionscore': [30, 25, 40, 20],
            'total cs': [220, 200, 30, 180],
            'year': [2025, 2025, 2025, 2025],
            'league': ['LPL', 'LPL', 'LPL', 'LPL'],
            'goldat10': [3200, 2800, 2600, 3000],
            'xpat10': [2100, 1900, 1800, 2000],
            'csat10': [85, 75, 65, 80],
            'golddiffat15': [600, 200, -100, 400],
            'xpdiffat15': [400, 150, -50, 300],
            'csdiffat15': [25, 15, -5, 20],
            'killsat15': [3, 2, 0, 2],
            'assistsat15': [4, 3, 8, 1],
            'deathsat15': [0, 1, 1, 2],
            'goldat20': [6500, 5800, 5200, 6000],
            'xpat20': [4200, 3800, 3500, 4000],
            'csat20': [160, 140, 120, 150],
            'killsat20': [4, 3, 1, 3],
            'assistsat20': [6, 4, 12, 2],
            'deathsat20': [1, 2, 1, 3]
        })

    @patch('pandas.read_csv')
    def test_load_data(self, mock_read_csv):
        """Test data loading functionality"""
        # Add map_index_within_series to mock data
        self.mock_data_2024['map_index_within_series'] = [1, 2, 1, 1]
        self.mock_data_2025['map_index_within_series'] = [1, 1, 2, 1]
        
        # Mock the CSV reading
        mock_read_csv.side_effect = [self.mock_data_2024, self.mock_data_2025]
        
        # Create DataProcessor instance
        dp = DataProcessor()
        
        # Verify data was loaded
        self.assertIsNotNone(dp.combined_data)
        self.assertEqual(len(dp.combined_data), 8)  # 4 from 2024 + 4 from 2025
        self.assertTrue('map_index_within_series' in dp.combined_data.columns)

    def test_generate_map_index(self):
        """Test map index generation"""
        # Create a simple test dataset
        test_data = pd.DataFrame({
            'gameid': ['series1_1', 'series1_2', 'series1_3', 'series2_1', 'series2_2'],
            'playername': ['Player1', 'Player1', 'Player1', 'Player2', 'Player2']
        })
        
        # Manually test the map index generation logic
        test_data["match_series"] = test_data["gameid"].str.rsplit("_", n=1).str[0]
        test_data["map_index_within_series"] = (
            test_data.groupby("match_series")["gameid"]
            .rank("dense")
            .astype(int)
        )
        
        # Verify results
        expected_series1 = [1, 2, 3, 1, 2]
        actual_series1 = test_data["map_index_within_series"].tolist()
        self.assertEqual(actual_series1, expected_series1)

    def test_preprocess_data(self):
        """Test data preprocessing"""
        # Create test data with some NaN values
        test_data = pd.DataFrame({
            'date': ['2024-01-01', '2024-01-02', '2024-01-03'],
            'position': ['MID', 'SUP', 'JNG'],
            'kills': [5, np.nan, 3],
            'assists': [8, 12, np.nan]
        })
        
        # Apply preprocessing logic
        test_data['date'] = pd.to_datetime(test_data['date'])
        numeric_columns = test_data.select_dtypes(include=[np.number]).columns
        test_data[numeric_columns] = test_data[numeric_columns].fillna(0)
        test_data['position'] = test_data['position'].str.lower()
        
        # Verify preprocessing
        self.assertEqual(test_data['position'].iloc[0], 'mid')
        self.assertEqual(test_data['kills'].iloc[1], 0)  # NaN should be filled with 0
        self.assertEqual(test_data['assists'].iloc[2], 0)  # NaN should be filled with 0

    def test_filter_player_data(self):
        """Test player data filtering"""
        # Create DataProcessor with mock data
        dp = DataProcessor()
        dp.combined_data = pd.concat([self.mock_data_2024, self.mock_data_2025], ignore_index=True)
        dp._generate_map_index()
        dp._preprocess_data()
        
        # Test filtering
        filtered_data = dp.filter_player_data(
            player_names=['Player1'],
            map_range=[1, 2],
            team='Team1'
        )
        
        # Should return Player1's data from Team1 in maps 1-2
        self.assertGreater(len(filtered_data), 0)
        self.assertTrue(all(player in ['Player1'] for player in filtered_data['playername']))
        self.assertTrue(all(team == 'Team1' for team in filtered_data['teamname']))

    def test_aggregate_stats(self):
        """Test statistics aggregation"""
        dp = DataProcessor()
        
        # Create test player data
        test_player_data = pd.DataFrame({
            'playername': ['Player1', 'Player1', 'Player1', 'Player1', 'Player1'],
            'kills': [5, 3, 4, 6, 2],
            'assists': [8, 6, 7, 9, 5],
            'deaths': [2, 4, 1, 3, 5],
            'damagetochampions': [15000, 12000, 14000, 16000, 10000],
            'visionscore': [25, 30, 20, 35, 15],
            'total cs': [200, 180, 220, 240, 160],
            'goldat10': [3000, 2800, 3200, 3500, 2500],
            'xpat10': [2000, 1800, 2200, 2400, 1600],
            'csat10': [80, 70, 90, 100, 60],
            'golddiffat15': [500, 300, 700, 800, 200],
            'xpdiffat15': [300, 200, 400, 500, 100],
            'csdiffat15': [20, 15, 25, 30, 10],
            'killsat15': [2, 1, 2, 3, 1],
            'assistsat15': [3, 2, 3, 4, 2],
            'deathsat15': [1, 2, 0, 1, 2],
            'goldat20': [6000, 5500, 6500, 7000, 5000],
            'xpat20': [4000, 3500, 4500, 4800, 3200],
            'csat20': [150, 130, 170, 180, 120],
            'killsat20': [3, 2, 3, 4, 2],
            'assistsat20': [5, 4, 5, 6, 4],
            'deathsat20': [1, 2, 1, 2, 3]
        })
        
        # Test kills aggregation
        stats = dp.aggregate_stats(test_player_data, 'kills')
        
        # Verify aggregated statistics - stats is a dict with player names as keys
        self.assertIn('Player1', stats)
        player_stats = stats['Player1']
        self.assertIn('kills_mean', player_stats)
        self.assertIn('kills_std', player_stats)
        self.assertEqual(player_stats['kills_mean'], 4.0)  # (5+3+4+6+2)/5 = 4.0

    def test_engineer_features(self):
        """Test feature engineering"""
        dp = DataProcessor()
        
        # Create test player data
        test_player_data = pd.DataFrame({
            'playername': ['Player1', 'Player1', 'Player1', 'Player1', 'Player1'],
            'kills': [5, 3, 4, 6, 2],
            'assists': [8, 6, 7, 9, 5],
            'deaths': [2, 4, 1, 3, 5],
            'damagetochampions': [15000, 12000, 14000, 16000, 10000],
            'visionscore': [25, 30, 20, 35, 15],
            'total cs': [200, 180, 220, 240, 160],
            'position': ['mid', 'mid', 'mid', 'mid', 'mid'],
            'goldat10': [3000, 2800, 3200, 3500, 2500],
            'xpat10': [2000, 1800, 2200, 2400, 1600],
            'csat10': [80, 70, 90, 100, 60],
            'golddiffat15': [500, 300, 700, 800, 200],
            'xpdiffat15': [300, 200, 400, 500, 100],
            'csdiffat15': [20, 15, 25, 30, 10],
            'killsat15': [2, 1, 2, 3, 1],
            'assistsat15': [3, 2, 3, 4, 2],
            'deathsat15': [1, 2, 0, 1, 2],
            'goldat20': [6000, 5500, 6500, 7000, 5000],
            'xpat20': [4000, 3500, 4500, 4800, 3200],
            'csat20': [150, 130, 170, 180, 120],
            'killsat20': [3, 2, 3, 4, 2],
            'assistsat20': [5, 4, 5, 6, 4],
            'deathsat20': [1, 2, 1, 2, 3]
        })
        
        # Test feature engineering for kills
        features = dp.engineer_features(test_player_data, 'kills')
        
        # Verify key features are present
        self.assertIn('avg_kills', features)
        self.assertIn('maps_played', features)
        self.assertIn('form_z_score', features)
        self.assertIn('position_factor', features)
        
        # Verify feature values
        self.assertEqual(features['avg_kills'], 4.0)
        self.assertEqual(features['maps_played'], 5)

    def test_get_available_players(self):
        """Test getting available players"""
        dp = DataProcessor()
        dp.combined_data = pd.concat([self.mock_data_2024, self.mock_data_2025], ignore_index=True)
        
        players = dp.get_available_players()
        
        # Should return unique, sorted player names
        expected_players = ['Player1', 'Player2', 'Player3', 'Player4', 'Player5']
        self.assertEqual(players, expected_players)

    def test_get_available_teams(self):
        """Test getting available teams"""
        dp = DataProcessor()
        dp.combined_data = pd.concat([self.mock_data_2024, self.mock_data_2025], ignore_index=True)
        
        teams = dp.get_available_teams()
        
        # Should return unique, sorted team names
        expected_teams = ['Team1', 'Team2', 'Team3', 'Team4', 'Team5']
        self.assertEqual(teams, expected_teams)

    def test_get_data_summary(self):
        """Test data summary generation"""
        dp = DataProcessor()
        dp.combined_data = pd.concat([self.mock_data_2024, self.mock_data_2025], ignore_index=True)
        
        summary = dp.get_data_summary()
        
        # Should contain summary information
        self.assertIn('Data from years', summary)
        self.assertIn('Total matches', summary)
        self.assertIn('Total players', summary)

    def test_process_request(self):
        """Test complete request processing"""
        dp = DataProcessor()
        dp.combined_data = pd.concat([self.mock_data_2024, self.mock_data_2025], ignore_index=True)
        dp._generate_map_index()
        dp._preprocess_data()
        
        # Create mock request
        class MockRequest:
            def __init__(self):
                self.player_names = ['Player1']
                self.prop_type = 'kills'
                self.prop_value = 4.0
                self.map_range = [1, 2]
                self.opponent = 'Team2'
                self.tournament = 'LPL'
                self.team = 'Team1'
                self.match_date = '2024-01-01'
                self.position_roles = ['MID']
        
        request = MockRequest()
        features = dp.process_request(request)
        
        # Should return engineered features
        self.assertIsInstance(features, dict)
        self.assertIn('avg_kills', features)
        self.assertIn('maps_played', features)

    def test_error_handling(self):
        """Test error handling in data processing"""
        dp = DataProcessor()
        
        # Test with empty data
        dp.combined_data = None
        players = dp.get_available_players()
        teams = dp.get_available_teams()
        
        # Should return empty lists when no data
        self.assertEqual(players, [])
        self.assertEqual(teams, [])

    def test_add_combo_features(self):
        """Test combo feature addition"""
        dp = DataProcessor()
        
        # Create test features
        features = {
            'avg_kills': 4.0,
            'maps_played': 5
        }
        
        # Create test player data
        test_player_data = pd.DataFrame({
            'kills': [5, 3, 4, 6, 2],
            'gameid': ['game1', 'game1', 'game2', 'game2', 'game3']
        })
        
        # Test combo feature addition
        updated_features = dp._add_combo_features(features, test_player_data, 'kills')
        
        # Should have combo features added
        self.assertIn('combo_avg_kills', updated_features)
        self.assertIn('combo_std_kills', updated_features)
        self.assertIn('combo_maps_played', updated_features)
        self.assertIn('combo_confidence_penalty', updated_features)


if __name__ == '__main__':
    unittest.main() 