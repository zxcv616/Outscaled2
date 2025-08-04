from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
import threading
import time

app = FastAPI(
    title="Outscaled.GG Backend API - Quick Start",
    description="Machine learning engine for League of Legends prop bet predictions",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
data_loaded = False
players_cache = []
player_details_cache = {}

def load_data_background():
    """Load data in background thread"""
    global data_loaded, players_cache, player_details_cache
    print("Loading data in background...")
    
    try:
        from .utils.data_processor import DataProcessor
        from .models.prediction_model import PredictionModel
        
        data_processor = DataProcessor()
        prediction_model = PredictionModel()
        
        # Copy data to global state
        players_cache = data_processor._player_cache or []
        player_details_cache = data_processor._player_details_cache or {}
        data_loaded = True
        
        print(f"Data loaded: {len(players_cache)} players")
        
    except Exception as e:
        print(f"Error loading data: {e}")

# Start background loading
threading.Thread(target=load_data_background, daemon=True).start()

@app.get("/")
async def root():
    return {"message": "Outscaled.GG Backend API - Quick Start Mode"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "data_loaded": data_loaded}

@app.get("/players")
async def get_available_players():
    if not data_loaded:
        return {"players": ["Loading..."]}
    return {"players": players_cache}

@app.get("/players/search")
async def search_players(q: str = "", limit: int = 50):
    if not data_loaded:
        return {"players": [], "total_matches": 0}
    
    if not q or len(q) < 2:
        return {"players": [], "total_matches": 0}
    
    # Simple search
    query = q.lower()
    matching_players = [p for p in players_cache if query in p.lower()]
    
    # Sort by relevance
    matching_players.sort(key=lambda p: (
        0 if p.lower() == query else
        1 if p.lower().startswith(query) else 2
    ))
    
    return {"players": matching_players[:limit], "total_matches": len(matching_players)}

@app.get("/player-details") 
async def get_player_details():
    return {"player_details": player_details_cache}

@app.get("/teams")
async def get_available_teams():
    return {"teams": ["Loading..."]}

@app.get("/tournaments")
async def get_available_tournaments():
    return {"tournaments": ["Loading..."]}

@app.get("/opponents")
async def get_available_opponents():
    return {"opponents": ["Loading..."]}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)