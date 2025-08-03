"""
Mock prediction model for testing without requiring real data files
"""
import numpy as np
from typing import Dict, Any, List, Tuple
from tests.test_data_processor_mock import MockDataProcessor

class MockPredictionModel:
    """Mock prediction model that doesn't require real data"""
    
    def __init__(self):
        self.data_processor = MockDataProcessor()
        self.model = None
        self.calibrator = None
        self.is_trained = True  # Always consider it trained for testing
        
    def predict(self, player_name: str, prop_type: str, prop_value: float, **kwargs) -> Dict[str, Any]:
        """Mock prediction that returns consistent test data"""
        
        # Mock prediction based on prop value
        base_prob = 0.6 if prop_value < 5.0 else 0.4
        
        # Add some variance based on player name hash for consistency
        variance = (hash(player_name) % 100) / 1000.0
        probability = max(0.1, min(0.9, base_prob + variance))
        
        confidence_interval = [prop_value - 1.0, prop_value + 1.0]
        
        return {
            'prediction': 'OVER' if probability > 0.5 else 'UNDER',
            'probability': probability,
            'confidence': 0.75,
            'prop_value': prop_value,
            'confidence_interval': confidence_interval,
            'player_stats': {
                'avg_kills': 5.0,
                'std_dev_kills': 2.0,
                'form_z_score': 0.5,
                'maps_played': 10,
                'position_factor': 1.0,
                'volatility': 0.3
            },
            'explanation': f"Mock prediction for {player_name} with {prop_type} prop value {prop_value}"
        }
    
    def generate_prediction_curve(self, player_name: str, prop_type: str, **kwargs) -> List[Dict[str, float]]:
        """Generate mock prediction curve data"""
        curve_data = []
        base_value = 5.0
        
        for i in range(-5, 6):
            prop_value = base_value + i
            prob = max(0.1, min(0.9, 0.6 - (i * 0.05)))  # Decreasing probability
            
            curve_data.append({
                'prop_value': prop_value,
                'probability': prob
            })
            
        return curve_data