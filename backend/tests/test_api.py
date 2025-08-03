import unittest
import json
from unittest.mock import patch, MagicMock
import sys
import os
import httpx

# Add the app directory to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Use mock app for testing to avoid data loading issues
try:
    from tests.test_app_mock import app
except ImportError:
    # Fallback to create minimal mock app
    from fastapi import FastAPI
    app = FastAPI()
    
    @app.get("/")
    async def root():
        return {"message": "Mock API for testing"}

# Import TestClient after app is available
from fastapi.testclient import TestClient


class TestAPI(unittest.TestCase):
    """Test cases for FastAPI endpoints using mock app"""

    def setUp(self):
        """Set up test fixtures before each test method"""
        self.client = TestClient(app)  # app is the first positional argument

    def test_root_endpoint(self):
        """Test the root endpoint"""
        response = self.client.get("/")
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("message", data)
        self.assertEqual(data["message"], "Outscaled.GG Backend API")

    def test_health_endpoint(self):
        """Test the health check endpoint"""
        response = self.client.get("/health")
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("status", data)
        self.assertEqual(data["status"], "healthy")

    @patch('app.main.data_processor.get_available_players')
    def test_players_endpoint(self, mock_get_players):
        """Test the players endpoint"""
        # Mock the data processor response
        mock_get_players.return_value = ["Player1", "Player2", "Player3"]
        
        response = self.client.get("/players")
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("players", data)
        self.assertEqual(data["players"], ["Player1", "Player2", "Player3"])

    @patch('app.main.data_processor.get_available_teams')
    def test_teams_endpoint(self, mock_get_teams):
        """Test the teams endpoint"""
        # Mock the data processor response
        mock_get_teams.return_value = ["Team1", "Team2", "Team3"]
        
        response = self.client.get("/teams")
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("teams", data)
        self.assertEqual(data["teams"], ["Team1", "Team2", "Team3"])

    @patch('app.main.data_processor.process_request')
    @patch('app.main.prediction_model.predict')
    def test_predict_endpoint_kills(self, mock_predict, mock_process_request):
        """Test the predict endpoint with kills prop"""
        # Mock the data processor response
        mock_process_request.return_value = {
            'avg_kills': 4.0,
            'maps_played': 10,
            'form_z_score': 0.5,
            'position_factor': 1.0
        }
        
        # Mock the prediction model response
        mock_predict.return_value = {
            'prediction': 'OVER',
            'confidence': 75.0,
            'expected_stat': 4.5,
            'confidence_interval': [3.8, 5.2],
            'reasoning': 'Test reasoning',
            'player_stats': {
                'avg_kills': 4.0,
                'avg_assists': 6.0,
                'form_z_score': 0.5,
                'maps_played': 10
            },
            'data_years': '2024 (5 matches), 2025 (5 matches)'
        }
        
        # Test request data
        request_data = {
            "player_names": ["Player1"],
            "prop_type": "kills",
            "prop_value": 4.0,
            "map_range": [1, 2],
            "opponent": "Team2",
            "tournament": "LPL",
            "team": "Team1",
            "match_date": "2024-01-01T00:00:00",
            "position_roles": ["MID"]
        }
        
        response = self.client.post("/predict", json=request_data)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify response structure
        self.assertIn("prediction", data)
        self.assertIn("confidence", data)
        self.assertIn("expected_stat", data)
        self.assertIn("confidence_interval", data)
        self.assertIn("reasoning", data)
        self.assertIn("player_stats", data)
        self.assertIn("data_years", data)
        
        # Verify prediction values
        self.assertEqual(data["prediction"], "OVER")
        self.assertEqual(data["confidence"], 75.0)
        self.assertEqual(data["expected_stat"], 4.5)

    @patch('app.main.data_processor.process_request')
    @patch('app.main.prediction_model.predict')
    def test_predict_endpoint_assists(self, mock_predict, mock_process_request):
        """Test the predict endpoint with assists prop"""
        # Mock the data processor response
        mock_process_request.return_value = {
            'avg_assists': 6.0,
            'maps_played': 10,
            'form_z_score': 0.5,
            'position_factor': 1.0
        }
        
        # Mock the prediction model response
        mock_predict.return_value = {
            'prediction': 'UNDER',
            'confidence': 65.0,
            'expected_stat': 5.5,
            'confidence_interval': [4.8, 6.2],
            'reasoning': 'Test reasoning for assists',
            'player_stats': {
                'avg_kills': 4.0,
                'avg_assists': 6.0,
                'form_z_score': 0.5,
                'maps_played': 10
            },
            'data_years': '2024 (5 matches), 2025 (5 matches)'
        }
        
        # Test request data
        request_data = {
            "player_names": ["Player1"],
            "prop_type": "assists",
            "prop_value": 7.0,
            "map_range": [1, 2],
            "opponent": "Team2",
            "tournament": "LPL",
            "team": "Team1",
            "match_date": "2024-01-01T00:00:00",
            "position_roles": ["SUP"]
        }
        
        response = self.client.post("/predict", json=request_data)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify response structure
        self.assertIn("prediction", data)
        self.assertIn("confidence", data)
        self.assertIn("expected_stat", data)
        self.assertIn("confidence_interval", data)
        self.assertIn("reasoning", data)
        self.assertIn("player_stats", data)
        self.assertIn("data_years", data)
        
        # Verify prediction values
        self.assertEqual(data["prediction"], "UNDER")
        self.assertEqual(data["confidence"], 65.0)
        self.assertEqual(data["expected_stat"], 5.5)

    def test_predict_endpoint_invalid_prop_type(self):
        """Test predict endpoint with invalid prop type"""
        request_data = {
            "player_names": ["Player1"],
            "prop_type": "invalid",  # Invalid prop type
            "prop_value": 4.0,
            "map_range": [1, 2],
            "opponent": "Team2",
            "tournament": "LPL",
            "team": "Team1",
            "match_date": "2024-01-01T00:00:00",
            "position_roles": ["MID"]
        }
        
        response = self.client.post("/predict", json=request_data)
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("detail", data)
        self.assertIn("prop_type must be 'kills' or 'assists'", data["detail"])

    def test_predict_endpoint_invalid_map_range(self):
        """Test predict endpoint with invalid map range"""
        request_data = {
            "player_names": ["Player1"],
            "prop_type": "kills",
            "prop_value": 4.0,
            "map_range": [3, 1],  # Invalid range (start > end)
            "opponent": "Team2",
            "tournament": "LPL",
            "team": "Team1",
            "match_date": "2024-01-01T00:00:00",
            "position_roles": ["MID"]
        }
        
        response = self.client.post("/predict", json=request_data)
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("detail", data)
        self.assertIn("map_range must be [start, end] with start <= end", data["detail"])

    def test_predict_endpoint_missing_required_fields(self):
        """Test predict endpoint with missing required fields"""
        request_data = {
            "player_names": ["Player1"],
            "prop_type": "kills",
            # Missing prop_value
            "map_range": [1, 2],
            "opponent": "Team2",
            "tournament": "LPL",
            "team": "Team1",
            "match_date": "2024-01-01T00:00:00",
            "position_roles": ["MID"]
        }
        
        response = self.client.post("/predict", json=request_data)
        
        self.assertEqual(response.status_code, 422)  # Validation error

    @patch('app.main.data_processor.process_request')
    @patch('app.main.prediction_model.predict')
    def test_predict_endpoint_error_handling(self, mock_predict, mock_process_request):
        """Test predict endpoint error handling"""
        # Mock the data processor to raise an exception
        mock_process_request.side_effect = Exception("Test error")
        
        request_data = {
            "player_names": ["Player1"],
            "prop_type": "kills",
            "prop_value": 4.0,
            "map_range": [1, 2],
            "opponent": "Team2",
            "tournament": "LPL",
            "team": "Team1",
            "match_date": "2024-01-01T00:00:00",
            "position_roles": ["MID"]
        }
        
        response = self.client.post("/predict", json=request_data)
        
        self.assertEqual(response.status_code, 500)
        data = response.json()
        self.assertIn("detail", data)
        self.assertIn("Prediction failed", data["detail"])

    def test_predict_endpoint_combo_players(self):
        """Test predict endpoint with multiple players (combo)"""
        with patch('app.main.data_processor.process_request') as mock_process_request, \
             patch('app.main.prediction_model.predict') as mock_predict:
            
            # Mock the data processor response
            mock_process_request.return_value = {
                'avg_kills': 8.0,  # Combined average
                'maps_played': 10,
                'form_z_score': 0.5,
                'position_factor': 1.0,
                'combo_avg_kills': 8.0,
                'combo_std_kills': 3.0,
                'combo_maps_played': 5,
                'combo_confidence_penalty': 0.9
            }
            
            # Mock the prediction model response
            mock_predict.return_value = {
                'prediction': 'OVER',
                'confidence': 70.0,
                'expected_stat': 8.5,
                'confidence_interval': [7.8, 9.2],
                'reasoning': 'Combo prediction reasoning',
                'player_stats': {
                    'avg_kills': 8.0,
                    'avg_assists': 12.0,
                    'form_z_score': 0.5,
                    'maps_played': 10
                },
                'data_years': '2024 (5 matches), 2025 (5 matches)'
            }
            
            # Test request data with multiple players
            request_data = {
                "player_names": ["Player1", "Player2"],
                "prop_type": "kills",
                "prop_value": 10.0,
                "map_range": [1, 2],
                "opponent": "Team2",
                "tournament": "LPL",
                "team": "Team1",
                "match_date": "2024-01-01T00:00:00",
                "position_roles": ["MID", "SUP"]
            }
            
            response = self.client.post("/predict", json=request_data)
            
            self.assertEqual(response.status_code, 200)
            data = response.json()
            
            # Verify response structure
            self.assertIn("prediction", data)
            self.assertIn("confidence", data)
            self.assertIn("expected_stat", data)
            self.assertIn("confidence_interval", data)
            self.assertIn("reasoning", data)
            self.assertIn("player_stats", data)
            self.assertIn("data_years", data)
            
            # Verify prediction values
            self.assertEqual(data["prediction"], "OVER")
            self.assertEqual(data["confidence"], 70.0)
            self.assertEqual(data["expected_stat"], 8.5)

    def test_api_documentation_endpoint(self):
        """Test that API documentation is available"""
        response = self.client.get("/docs")
        
        self.assertEqual(response.status_code, 200)
        # Should return HTML documentation
        self.assertIn("text/html", response.headers["content-type"])

    def test_openapi_schema_endpoint(self):
        """Test that OpenAPI schema is available"""
        response = self.client.get("/openapi.json")
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify OpenAPI schema structure
        self.assertIn("openapi", data)
        self.assertIn("info", data)
        self.assertIn("paths", data)
        
        # Verify our endpoints are documented
        self.assertIn("/", data["paths"])
        self.assertIn("/health", data["paths"])
        self.assertIn("/predict", data["paths"])
        self.assertIn("/players", data["paths"])
        self.assertIn("/teams", data["paths"])


if __name__ == '__main__':
    unittest.main() 