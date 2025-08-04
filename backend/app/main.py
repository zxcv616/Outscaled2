from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Union
import uvicorn

from .models.prediction_model import PredictionModel
from .utils.data_processor import DataProcessor

# Initialize global instances
data_processor = DataProcessor()
prediction_model = PredictionModel()

app = FastAPI(
    title="Outscaled.GG Backend API",
    description="Machine learning engine for League of Legends prop bet predictions",
    version="1.0.0",
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    # Force schema regeneration
    openapi_tags=[{"name": "predictions", "description": "Prediction endpoints"}]
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class PredictionRequest(BaseModel):
    player_names: List[str] = Field(..., description="List of player names")
    prop_type: str = Field(..., description="Type of prop (kills or assists)")
    prop_value: float = Field(..., description="Prop line value")
    map_range: List[int] = Field(..., description="Map range [start, end]")
    opponent: str = Field(..., description="Opponent team name")
    tournament: str = Field(..., description="Tournament name")
    team: Optional[str] = Field(default=None, description="Player's team name (optional - will be auto-inferred if not provided)")
    match_date: str = Field(..., description="Match date in YYYY-MM-DD format")
    position_roles: List[str] = Field(..., description="List of position roles")
    strict_mode: bool = Field(default=False, description="Use only exact tournament data")
    
    model_config = {
        "json_schema_extra": {"version": "2.5", "team_optional": True}
    }

class PredictionResponse(BaseModel):
    prediction: str  # "OVER" or "UNDER"
    confidence: float
    base_model_confidence: float
    data_tier: int
    expected_stat: float
    confidence_interval: List[float]
    reasoning: str
    player_stats: dict
    data_years: str
    sample_details: dict
    confidence_warning: str = ""
    prediction_curve: Optional[List[dict]] = None  # New field for prediction curve
    prop_value: float  # The prop line value from the request

@app.get("/")
async def root():
    return {"message": "Outscaled.GG Backend API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/predict", response_model=PredictionResponse)
async def predict_prop(request: PredictionRequest):
    """
    Predict OVER/UNDER for League of Legends player prop bets
    """
    # Validate inputs first
    if request.prop_type not in ["kills", "assists"]:
        raise HTTPException(status_code=400, detail="prop_type must be 'kills' or 'assists'")
    
    if len(request.map_range) != 2 or request.map_range[0] > request.map_range[1]:
        raise HTTPException(status_code=400, detail="map_range must be [start, end] with start <= end")
    
    try:
        # Process data and make prediction with tiered system
        features = data_processor.process_request(request, strict_mode=request.strict_mode)
        
        # Extract sample details from features
        sample_details = features.pop('sample_details', None)
        
        # Generate main prediction
        prediction_result = prediction_model.predict(features, request.prop_value, sample_details, request.prop_type)
        
        # Generate prediction curve around the input prop value
        prediction_curve = prediction_model.generate_prediction_curve(
            features, 
            request.prop_value, 
            step=0.5, 
            range_size=3
        )
        
        # Add prediction curve to the response
        prediction_result['prediction_curve'] = prediction_curve
        
        # Add the prop value from the request to the response
        prediction_result['prop_value'] = request.prop_value
        
        return prediction_result
        
    except ValueError as e:
        # Handle data validation errors with user-friendly message
        raise HTTPException(status_code=400, detail=f"Data validation error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

@app.get("/players")
async def get_available_players():
    """
    Get list of all available player names for autocomplete
    """
    try:
        players = data_processor.get_available_players()
        return {"players": players}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get players: {str(e)}")

@app.get("/teams")
async def get_available_teams():
    """
    Get list of all available team names for autocomplete
    """
    try:
        teams = data_processor.get_available_teams()
        return {"teams": teams}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get teams: {str(e)}")

@app.get("/tournaments")
async def get_available_tournaments():
    """
    Get list of all available tournament names for autocomplete
    """
    try:
        tournaments = data_processor.get_available_tournaments()
        return {"tournaments": tournaments}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get tournaments: {str(e)}")

@app.get("/positions")
async def get_available_positions():
    """
    Get list of all available player positions for role-based filtering
    """
    try:
        positions = data_processor.get_available_positions()
        return {"positions": positions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get positions: {str(e)}")

@app.post("/check-data-availability")
async def check_data_availability(request: dict):
    """
    Check if data is available for given criteria and return helpful suggestions
    """
    try:
        player_names = request.get('player_names', [])
        tournament = request.get('tournament')
        map_range = request.get('map_range', [1, 3])
        
        if not player_names:
            raise HTTPException(status_code=400, detail="player_names is required")
        
        availability = data_processor.check_data_availability(
            player_names=player_names,
            tournament=tournament,
            map_range=map_range
        )
        
        return availability
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to check data availability: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 