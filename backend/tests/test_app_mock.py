"""
Mock FastAPI app for testing without requiring real data files
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List
from tests.test_prediction_model_mock import MockPredictionModel

# Create FastAPI app
app = FastAPI(title="Outscaled.GG API (Test Mode)", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize mock model
prediction_model = MockPredictionModel()

# Pydantic models
class PredictionRequest(BaseModel):
    player_name: str
    prop_type: str
    prop_value: float
    team_name: str = ""
    tournament_name: str = ""

class PredictionResponse(BaseModel):
    prediction: str
    probability: float
    confidence: float
    prop_value: float
    confidence_interval: List[float]
    player_stats: Dict[str, Any]
    explanation: str

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Outscaled.GG API (Test Mode)", "status": "running"}

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "mode": "test"}

@app.post("/predict", response_model=PredictionResponse)
async def predict(request: PredictionRequest):
    """Main prediction endpoint using mock model"""
    try:
        result = prediction_model.predict(
            player_name=request.player_name,
            prop_type=request.prop_type,
            prop_value=request.prop_value,
            team_name=request.team_name,
            tournament_name=request.tournament_name
        )
        return PredictionResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/players")
async def get_players():
    """Get all available players"""
    return {"players": prediction_model.data_processor.get_all_players()}

@app.get("/teams")
async def get_teams():
    """Get all available teams"""
    return {"teams": prediction_model.data_processor.get_all_teams()}

@app.get("/tournaments")
async def get_tournaments():
    """Get all available tournaments"""
    return {"tournaments": prediction_model.data_processor.get_all_tournaments()}