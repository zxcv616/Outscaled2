#!/usr/bin/env python3
"""
Export utilities for predictions and analytics data
Supports CSV, JSON, and Excel formats
"""

import csv
import json
import io
from typing import List, Dict, Any, Optional
from datetime import datetime
import pandas as pd
from fastapi import Response
from fastapi.responses import StreamingResponse

class PredictionExporter:
    """Export prediction data in various formats"""
    
    def __init__(self):
        pass
    
    def export_prediction_to_csv(self, prediction_result: Dict[str, Any], request_data: Dict[str, Any]) -> str:
        """Export a single prediction to CSV format"""
        # Flatten the prediction data
        flat_data = {
            'timestamp': datetime.now().isoformat(),
            'player_names': ', '.join(request_data.get('player_names', [])),
            'prop_type': request_data.get('prop_type'),
            'prop_value': request_data.get('prop_value'),
            'tournament': request_data.get('tournament'),
            'opponent': request_data.get('opponent'),
            'position_roles': ', '.join(request_data.get('position_roles', [])),
            'prediction': prediction_result.get('prediction'),
            'confidence': prediction_result.get('confidence'),
            'expected_stat': prediction_result.get('expected_stat'),
            'data_tier': prediction_result.get('data_tier'),
            'base_model_confidence': prediction_result.get('base_model_confidence'),
            'reasoning': prediction_result.get('reasoning', '').replace('\n', ' ').replace(',', ';'),
            'data_years': prediction_result.get('data_years', ''),
        }
        
        # Add player stats
        player_stats = prediction_result.get('player_stats', {})
        for key, value in player_stats.items():
            flat_data[f'player_stat_{key}'] = value
        
        # Add sample details
        sample_details = prediction_result.get('sample_details', {})
        if isinstance(sample_details, dict):
            tier_info = sample_details.get('tier_info', {})
            flat_data.update({
                'sample_size': sample_details.get('sample_size', 0),
                'tier_name': tier_info.get('name', ''),
                'tier_weight': tier_info.get('weight', 0),
                'fallback_used': sample_details.get('fallback_used', False),
                'volatility': sample_details.get('volatility', 0),
            })
        
        # Convert to CSV string
        output = io.StringIO()
        fieldnames = list(flat_data.keys())
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow(flat_data)
        
        return output.getvalue()
    
    def export_prediction_curve_to_csv(self, prediction_curve: List[Dict[str, Any]], request_data: Dict[str, Any]) -> str:
        """Export prediction curve data to CSV"""
        output = io.StringIO()
        
        if not prediction_curve:
            return "No prediction curve data available\n"
        
        # Add metadata
        fieldnames = ['prop_value', 'prediction', 'confidence', 'expected_stat', 'is_input_prop']
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        
        # Write header with metadata
        output.write(f"# Prediction Curve Export\n")
        output.write(f"# Generated: {datetime.now().isoformat()}\n")
        output.write(f"# Player(s): {', '.join(request_data.get('player_names', []))}\n")
        output.write(f"# Prop Type: {request_data.get('prop_type')}\n")
        output.write(f"# Tournament: {request_data.get('tournament')}\n")
        output.write(f"# Original Prop Value: {request_data.get('prop_value')}\n")
        output.write("\n")
        
        writer.writeheader()
        for point in prediction_curve:
            writer.writerow({
                'prop_value': point.get('prop_value'),
                'prediction': point.get('prediction'),
                'confidence': point.get('confidence'),
                'expected_stat': point.get('expected_stat'),
                'is_input_prop': point.get('is_input_prop', False)
            })
        
        return output.getvalue()
    
    def export_analytics_to_csv(self, analytics_data: List[Dict[str, Any]]) -> str:
        """Export analytics data to CSV"""
        if not analytics_data:
            return "No analytics data available\n"
        
        output = io.StringIO()
        
        # Get all unique keys for fieldnames
        all_keys = set()
        for item in analytics_data:
            all_keys.update(item.keys())
        
        fieldnames = sorted(list(all_keys))
        writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction='ignore')
        
        # Write header with metadata
        output.write(f"# Analytics Data Export\n")
        output.write(f"# Generated: {datetime.now().isoformat()}\n")
        output.write(f"# Total Records: {len(analytics_data)}\n")
        output.write("\n")
        
        writer.writeheader()
        writer.writerows(analytics_data)
        
        return output.getvalue()
    
    def create_csv_response(self, csv_content: str, filename: str) -> StreamingResponse:
        """Create a streaming CSV response"""
        def generate():
            yield csv_content
        
        headers = {
            'Content-Disposition': f'attachment; filename="{filename}"',
            'Content-Type': 'text/csv; charset=utf-8'
        }
        
        return StreamingResponse(
            generate(),
            media_type='text/csv',
            headers=headers
        )
    
    def export_to_json(self, data: Any, pretty: bool = True) -> str:
        """Export data to JSON format"""
        if pretty:
            return json.dumps(data, indent=2, default=str)
        return json.dumps(data, default=str)
    
    def create_json_response(self, data: Any, filename: str) -> StreamingResponse:
        """Create a streaming JSON response"""
        json_content = self.export_to_json(data)
        
        def generate():
            yield json_content
        
        headers = {
            'Content-Disposition': f'attachment; filename="{filename}"',
            'Content-Type': 'application/json; charset=utf-8'
        }
        
        return StreamingResponse(
            generate(),
            media_type='application/json',
            headers=headers
        )

class AnalyticsExporter:
    """Export analytics and reporting data"""
    
    def __init__(self):
        self.prediction_exporter = PredictionExporter()
    
    def export_user_prediction_history(self, predictions: List[Dict[str, Any]], user_id: int) -> str:
        """Export user's prediction history to CSV"""
        if not predictions:
            return "No prediction history available\n"
        
        output = io.StringIO()
        
        # Define fieldnames based on prediction history structure
        fieldnames = [
            'timestamp', 'player_names', 'prop_type', 'prop_value', 'tournament',
            'prediction', 'confidence', 'expected_stat', 'response_time_ms', 'model_version'
        ]
        
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        
        # Write header with metadata
        output.write(f"# User Prediction History Export\n")
        output.write(f"# User ID: {user_id}\n")
        output.write(f"# Generated: {datetime.now().isoformat()}\n")
        output.write(f"# Total Predictions: {len(predictions)}\n")
        output.write("\n")
        
        writer.writeheader()
        
        for pred in predictions:
            # Parse JSON fields
            player_names = pred.get('player_names', '[]')
            if isinstance(player_names, str):
                try:
                    player_names = json.loads(player_names)
                except:
                    player_names = [player_names]
            
            writer.writerow({
                'timestamp': pred.get('created_at', ''),
                'player_names': ', '.join(player_names) if isinstance(player_names, list) else str(player_names),
                'prop_type': pred.get('prop_type', ''),
                'prop_value': pred.get('prop_value', ''),
                'tournament': pred.get('tournament', ''),
                'prediction': pred.get('prediction', ''),
                'confidence': pred.get('confidence', ''),
                'expected_stat': pred.get('expected_stat', ''),
                'response_time_ms': pred.get('response_time_ms', ''),
                'model_version': pred.get('model_version', '')
            })
        
        return output.getvalue()
    
    def export_system_metrics(self, metrics_data: Dict[str, Any]) -> str:
        """Export system metrics to CSV"""
        output = io.StringIO()
        
        # Write header
        output.write(f"# System Metrics Export\n")
        output.write(f"# Generated: {datetime.now().isoformat()}\n")
        output.write("\n")
        
        # Export counters
        output.write("# Counters\n")
        output.write("metric_name,value\n")
        counters = metrics_data.get('counters', {})
        for name, value in counters.items():
            output.write(f"{name},{value}\n")
        
        output.write("\n")
        
        # Export gauges
        output.write("# Gauges\n")
        output.write("metric_name,value\n")
        gauges = metrics_data.get('gauges', {})
        for name, value in gauges.items():
            output.write(f"{name},{value}\n")
        
        output.write("\n")
        
        # Export health status
        health = metrics_data.get('health_status', {})
        output.write("# Health Status\n")
        output.write("metric_name,value\n")
        for name, value in health.items():
            output.write(f"health_{name},{value}\n")
        
        return output.getvalue()

# Global exporter instances
prediction_exporter = PredictionExporter()
analytics_exporter = AnalyticsExporter()

def generate_export_filename(base_name: str, format_type: str = "csv", include_timestamp: bool = True) -> str:
    """Generate standardized export filename"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S') if include_timestamp else ""
    
    if include_timestamp:
        return f"outscaled_{base_name}_{timestamp}.{format_type}"
    else:
        return f"outscaled_{base_name}.{format_type}"