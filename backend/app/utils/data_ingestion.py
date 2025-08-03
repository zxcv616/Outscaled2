#!/usr/bin/env python3
"""
Data Ingestion Module for League of Legends Match Data
Supports multiple data sources including APIs and web scraping
"""

import requests
import pandas as pd
import numpy as np
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import os
from pathlib import Path
import time
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class DataSource(ABC):
    """Abstract base class for data sources"""
    
    @abstractmethod
    def fetch_matches(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Fetch match data for a given date range"""
        pass
    
    @abstractmethod
    def fetch_player_stats(self, player_name: str, tournament: str = None) -> pd.DataFrame:
        """Fetch player statistics"""
        pass

class RiotAPISource(DataSource):
    """Riot Games API data source (requires API key)"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('RIOT_API_KEY')
        self.base_url = "https://americas.api.riotgames.com"
        
        if not self.api_key:
            logger.warning("Riot API key not provided. Set RIOT_API_KEY environment variable.")
    
    def fetch_matches(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Fetch match data from Riot API"""
        if not self.api_key:
            logger.error("Cannot fetch from Riot API without API key")
            return pd.DataFrame()
        
        # TODO: Implement Riot API integration
        # This would require:
        # 1. Get tournament matches
        # 2. Get match details
        # 3. Extract player statistics
        # 4. Format into our expected DataFrame structure
        
        logger.info("Riot API integration not yet implemented")
        return pd.DataFrame()
    
    def fetch_player_stats(self, player_name: str, tournament: str = None) -> pd.DataFrame:
        """Fetch player stats from Riot API"""
        logger.info("Riot API player stats not yet implemented")
        return pd.DataFrame()

class LoLEsportsAPISource(DataSource):
    """LoL Esports API data source"""
    
    def __init__(self):
        self.base_url = "https://esports-api.lolesports.com/persisted/gw"
        self.headers = {
            'x-api-key': '0TvQnueqKa5mxJntVWt0w4LpLfEkrV1Ta8rQBb9Z'  # Public API key
        }
    
    def fetch_matches(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Fetch match data from LoL Esports API"""
        try:
            # Get leagues
            leagues_url = f"{self.base_url}/getLeagues?hl=en-US"
            leagues_response = requests.get(leagues_url, headers=self.headers)
            
            if leagues_response.status_code != 200:
                logger.error(f"Failed to fetch leagues: {leagues_response.status_code}")
                return pd.DataFrame()
            
            # TODO: Implement full match data fetching
            # 1. Get tournaments for each league
            # 2. Get matches for date range
            # 3. Get game details with player stats
            # 4. Format into DataFrame
            
            logger.info("LoL Esports API integration in progress")
            return pd.DataFrame()
            
        except Exception as e:
            logger.error(f"Error fetching from LoL Esports API: {e}")
            return pd.DataFrame()
    
    def fetch_player_stats(self, player_name: str, tournament: str = None) -> pd.DataFrame:
        """Fetch player stats from LoL Esports API"""
        logger.info("LoL Esports API player stats not yet implemented")
        return pd.DataFrame()

class OraclesElixirScraper(DataSource):
    """Oracle's Elixir data scraper (competitive LoL stats)"""
    
    def __init__(self):
        self.base_url = "https://oracleselixir.com"
        self.data_url = "https://oracleselixir.com/stats/players/byTournament"
    
    def fetch_matches(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Scrape match data from Oracle's Elixir"""
        try:
            # Oracle's Elixir provides downloadable CSVs
            # This is a simplified implementation
            logger.info("Fetching data from Oracle's Elixir...")
            
            # TODO: Implement web scraping for Oracle's Elixir
            # 1. Navigate to data pages
            # 2. Download relevant CSVs
            # 3. Parse and filter by date range
            # 4. Format into our structure
            
            return pd.DataFrame()
            
        except Exception as e:
            logger.error(f"Error scraping Oracle's Elixir: {e}")
            return pd.DataFrame()
    
    def fetch_player_stats(self, player_name: str, tournament: str = None) -> pd.DataFrame:
        """Scrape player stats from Oracle's Elixir"""
        logger.info("Oracle's Elixir player stats scraping not yet implemented")
        return pd.DataFrame()

class MockDataSource(DataSource):
    """Mock data source for testing and development"""
    
    def __init__(self):
        self.positions = ['TOP', 'JNG', 'MID', 'ADC', 'SUP']
        self.teams = ['T1', 'GenG', 'JDG', 'BLG', 'G2', 'FNC', 'C9', 'TL']
        self.players = {
            'TOP': ['Zeus', 'Kiin', '369', 'Bin', 'BrokenBlade', 'Wunder', 'Fudge', 'Impact'],
            'JNG': ['Oner', 'Canyon', 'Kanavi', 'Xun', 'Jankos', 'Razork', 'Blaber', 'Santorin'],
            'MID': ['Faker', 'Chovy', 'Knight', 'Scout', 'Caps', 'Humanoid', 'Jensen', 'Bjergsen'],
            'ADC': ['Gumayusi', 'Peyz', 'Ruler', 'Elk', 'Hans sama', 'Rekkles', 'Berserker', 'Doublelift'],
            'SUP': ['Keria', 'Lehends', 'Missing', 'ON', 'Mikyx', 'Hylissang', 'Zven', 'CoreJJ']
        }
    
    def fetch_matches(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Generate mock match data"""
        logger.info(f"Generating mock data from {start_date} to {end_date}")
        
        data = []
        current_date = start_date
        
        while current_date <= end_date:
            # Generate 2-4 matches per day
            num_matches = np.random.randint(2, 5)
            
            for match_idx in range(num_matches):
                team1_idx = np.random.randint(0, len(self.teams))
                team2_idx = np.random.randint(0, len(self.teams))
                if team1_idx == team2_idx:
                    team2_idx = (team1_idx + 1) % len(self.teams)
                
                team1 = self.teams[team1_idx]
                team2 = self.teams[team2_idx]
                
                # Generate best of 3
                num_games = np.random.choice([2, 3], p=[0.4, 0.6])
                
                for game_idx in range(num_games):
                    for pos_idx, position in enumerate(self.positions):
                        # Team 1 player
                        player1 = self.players[position][team1_idx % len(self.players[position])]
                        data.append(self._generate_player_game_stats(
                            player1, team1, team2, position, current_date, 
                            f"Mock_Tournament_{current_date.year}", game_idx + 1
                        ))
                        
                        # Team 2 player  
                        player2 = self.players[position][team2_idx % len(self.players[position])]
                        data.append(self._generate_player_game_stats(
                            player2, team2, team1, position, current_date,
                            f"Mock_Tournament_{current_date.year}", game_idx + 1
                        ))
            
            current_date += timedelta(days=np.random.randint(1, 4))
        
        df = pd.DataFrame(data)
        logger.info(f"Generated {len(df)} mock player-game records")
        return df
    
    def _generate_player_game_stats(self, player: str, team: str, opponent: str, 
                                   position: str, date: datetime, tournament: str,
                                   game_number: int) -> Dict[str, Any]:
        """Generate realistic player game statistics"""
        # Position-based stat distributions
        position_stats = {
            'TOP': {'kills': (2, 4), 'deaths': (2, 3), 'assists': (4, 7)},
            'JNG': {'kills': (3, 5), 'deaths': (2, 4), 'assists': (7, 10)},
            'MID': {'kills': (4, 6), 'deaths': (2, 3), 'assists': (5, 8)},
            'ADC': {'kills': (4, 7), 'deaths': (2, 3), 'assists': (5, 7)},
            'SUP': {'kills': (1, 3), 'deaths': (2, 4), 'assists': (10, 15)}
        }
        
        stats = position_stats[position]
        
        # Add some variance for star players
        if player in ['Faker', 'Chovy', 'Zeus', 'Gumayusi', 'Keria']:
            kill_bonus = 1
            death_reduction = -0.5
        else:
            kill_bonus = 0
            death_reduction = 0
        
        return {
            'playername': player,
            'teamname': team,
            'opponent': opponent,
            'position': position.lower(),
            'date': date.strftime('%Y-%m-%d'),
            'tournament': tournament,
            'league': tournament.replace('_', ' '),
            'gameid': f"{date.strftime('%Y%m%d')}_{team}_{opponent}_{game_number}",
            'map_index_within_series': game_number,
            'kills': max(0, int(np.random.normal(
                (stats['kills'][0] + stats['kills'][1]) / 2 + kill_bonus,
                1
            ))),
            'deaths': max(0, int(np.random.normal(
                (stats['deaths'][0] + stats['deaths'][1]) / 2 + death_reduction,
                1
            ))),
            'assists': max(0, int(np.random.normal(
                (stats['assists'][0] + stats['assists'][1]) / 2,
                2
            ))),
            'damage': int(np.random.normal(20000, 5000)),
            'vision': int(np.random.normal(30, 10)),
            'cs': int(np.random.normal(250, 50)),
            'gold': int(np.random.normal(13000, 2000)),
            'game_duration': int(np.random.normal(30, 5)) * 60  # in seconds
        }
    
    def fetch_player_stats(self, player_name: str, tournament: str = None) -> pd.DataFrame:
        """Generate mock player statistics"""
        # Find player position
        player_position = None
        for position, players in self.players.items():
            if player_name in players:
                player_position = position
                break
        
        if not player_position:
            logger.warning(f"Player {player_name} not found in mock data")
            return pd.DataFrame()
        
        # Generate historical stats
        end_date = datetime.now()
        start_date = end_date - timedelta(days=90)
        
        all_matches = self.fetch_matches(start_date, end_date)
        player_matches = all_matches[all_matches['playername'] == player_name]
        
        if tournament:
            player_matches = player_matches[player_matches['tournament'] == tournament]
        
        return player_matches

class DataIngestionManager:
    """Manages data ingestion from multiple sources"""
    
    def __init__(self):
        self.sources = {
            'riot': RiotAPISource(),
            'lolesports': LoLEsportsAPISource(),
            'oracleselixir': OraclesElixirScraper(),
            'mock': MockDataSource()
        }
        self.cache_dir = Path('data/cache')
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def fetch_recent_matches(self, days: int = 30, source: str = 'mock') -> pd.DataFrame:
        """Fetch recent match data from specified source"""
        if source not in self.sources:
            logger.error(f"Unknown data source: {source}")
            return pd.DataFrame()
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        logger.info(f"Fetching matches from {source} for last {days} days")
        
        # Check cache first
        cache_file = self.cache_dir / f"{source}_matches_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.csv"
        
        if cache_file.exists() and (datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)) < timedelta(hours=6):
            logger.info("Loading from cache")
            return pd.read_csv(cache_file)
        
        # Fetch from source
        data = self.sources[source].fetch_matches(start_date, end_date)
        
        if not data.empty:
            # Save to cache
            data.to_csv(cache_file, index=False)
            logger.info(f"Cached {len(data)} records")
        
        return data
    
    def update_data_files(self, source: str = 'mock'):
        """Update the main data files used by the application"""
        logger.info(f"Updating data files from {source}")
        
        # Fetch recent data
        recent_data = self.fetch_recent_matches(days=90, source=source)
        
        if recent_data.empty:
            logger.warning("No data fetched, skipping update")
            return False
        
        # Save to the expected data directory
        data_dir = Path('data')
        data_dir.mkdir(exist_ok=True)
        
        # Save by year
        for year in recent_data['date'].str[:4].unique():
            year_data = recent_data[recent_data['date'].str.startswith(year)]
            output_file = data_dir / f"{year}_player_stats.csv"
            year_data.to_csv(output_file, index=False)
            logger.info(f"Saved {len(year_data)} records to {output_file}")
        
        return True
    
    def get_available_sources(self) -> List[str]:
        """Get list of available data sources"""
        return list(self.sources.keys())
    
    def test_source_connection(self, source: str) -> bool:
        """Test if a data source is accessible"""
        if source not in self.sources:
            return False
        
        try:
            # Try to fetch minimal data
            end_date = datetime.now()
            start_date = end_date - timedelta(days=1)
            data = self.sources[source].fetch_matches(start_date, end_date)
            return not data.empty
        except Exception as e:
            logger.error(f"Failed to connect to {source}: {e}")
            return False

# CLI interface for testing
if __name__ == "__main__":
    import sys
    
    manager = DataIngestionManager()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "update":
            source = sys.argv[2] if len(sys.argv) > 2 else "mock"
            success = manager.update_data_files(source)
            print(f"Update {'successful' if success else 'failed'}")
        
        elif command == "test":
            for source in manager.get_available_sources():
                connected = manager.test_source_connection(source)
                print(f"{source}: {'✓' if connected else '✗'}")
        
        elif command == "fetch":
            source = sys.argv[2] if len(sys.argv) > 2 else "mock"
            days = int(sys.argv[3]) if len(sys.argv) > 3 else 30
            data = manager.fetch_recent_matches(days, source)
            print(f"Fetched {len(data)} records from {source}")
    
    else:
        print("Usage:")
        print("  python data_ingestion.py update [source]  - Update data files")
        print("  python data_ingestion.py test             - Test all sources")
        print("  python data_ingestion.py fetch [source] [days] - Fetch recent data")
        print(f"\nAvailable sources: {', '.join(manager.get_available_sources())}")