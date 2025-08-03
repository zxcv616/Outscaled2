"""
Mock data processor for testing without requiring large CSV files
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Any

class MockDataProcessor:
    """Mock data processor that doesn't require real data files"""
    
    def __init__(self):
        self.data_2024 = self._create_mock_data()
        self.data_2025 = self._create_mock_data()
        self.combined_data = pd.concat([self.data_2024, self.data_2025])
        
    def _create_mock_data(self):
        """Create mock data with required columns"""
        mock_data = pd.DataFrame({
            'playername': ['TestPlayer1', 'TestPlayer2', 'TestPlayer3'],
            'teamname': ['TestTeam1', 'TestTeam2', 'TestTeam1'],
            'tournamentname': ['TestTournament', 'TestTournament', 'TestTournament'],
            'kills': [5, 3, 7],
            'assists': [8, 12, 6],
            'deaths': [2, 4, 1],
            'position': ['mid', 'adc', 'jungle'],
            'result': [1, 0, 1],
            'mapsPlayed': [1, 1, 1],
            'date': ['2024-01-01', '2024-01-02', '2024-01-03']
        })
        return mock_data
    
    def get_all_players(self) -> List[str]:
        """Get all unique player names"""
        if self.combined_data.empty:
            return []
        return self.combined_data['playername'].dropna().unique().tolist()
    
    def get_all_teams(self) -> List[str]:
        """Get all unique team names"""
        if self.combined_data.empty:
            return []
        return self.combined_data['teamname'].dropna().unique().tolist()
    
    def get_all_tournaments(self) -> List[str]:
        """Get all unique tournament names"""
        if self.combined_data.empty:
            return []
        return self.combined_data['tournamentname'].dropna().unique().tolist()
    
    def calculate_statistics(self, player_name: str, prop_type: str) -> Dict[str, Any]:
        """Calculate mock statistics for a player"""
        return {
            'avg_kills': 5.0,
            'std_dev_kills': 2.0,
            'form_z_score': 0.5,
            'maps_played': 10,
            'position_factor': 1.0,
            'volatility': 0.3
        }