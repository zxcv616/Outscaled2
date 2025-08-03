from fastapi import FastAPI, HTTPException, Request, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Union
from sqlalchemy.orm import Session
import uvicorn
import time
import uuid
import json
from datetime import datetime

from .models.prediction_model import PredictionModel
from .utils.data_processor import DataProcessor
from .utils.monitoring import monitor, time_function, log_prediction, log_api_request, create_monitoring_report, get_logger
from .utils.cache import cache_manager, cache_prediction_response, get_cache_health
from .utils.export import prediction_exporter, analytics_exporter, generate_export_filename
from .auth.routes import router as auth_router
from .auth.dependencies import get_current_user_optional, rate_limit_check, get_current_active_user
from .auth.models import User, PredictionHistory
from .database import get_db, init_db
from .monitoring_dashboard import router as dashboard_router

# Initialize global instances
data_processor = DataProcessor()
prediction_model = PredictionModel(use_xgboost=False)  # XGBoost available but needs more integration work

app = FastAPI(
    title="Outscaled.GG Backend API",
    description="Machine learning engine for League of Legends prop bet predictions",
    version="2.0.0",
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    # Force schema regeneration
    openapi_tags=[
        {"name": "predictions", "description": "Prediction endpoints"},
        {"name": "authentication", "description": "User authentication and management"}
    ]
)

# Include authentication routes
app.include_router(auth_router)

# Include monitoring dashboard
app.include_router(dashboard_router)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize logger
logger = get_logger(__name__)

@app.middleware("http")
async def monitor_requests(request: Request, call_next):
    """Monitor all HTTP requests"""
    start_time = time.time()
    request_id = str(uuid.uuid4())
    
    # Set request ID for logging correlation
    logger.set_request_id(request_id)
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    log_api_request(
        endpoint=str(request.url.path),
        method=request.method,
        status_code=response.status_code,
        duration=duration
    )
    
    # Add request ID to response headers
    response.headers["X-Request-ID"] = request_id
    
    return response

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
    confidence_explanation: Optional[dict] = None  # New field for detailed confidence breakdown

@app.get("/")
async def root():
    return {"message": "Outscaled.GG Backend API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/predict", response_model=PredictionResponse, dependencies=[Depends(rate_limit_check)])
@cache_prediction_response(ttl=300)  # Cache for 5 minutes
@time_function("prediction_endpoint")
async def predict_prop(
    request: PredictionRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Predict OVER/UNDER for League of Legends player prop bets
    """
    start_time = time.time()
    
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
        prediction_result = prediction_model.predict(features, request.prop_value, sample_details)
        
        # Generate prediction curve around the input prop value
        prediction_curve = prediction_model.generate_prediction_curve(
            features, 
            request.prop_value, 
            step=0.5, 
            range_size=3
        )
        
        # Add prediction curve to the response
        prediction_result['prediction_curve'] = prediction_curve
        
        # Log the prediction for monitoring
        log_prediction(prediction_result, request.dict())
        
        # Store prediction history if user is authenticated
        if current_user:
            prediction_history = PredictionHistory(
                user_id=current_user.id,
                player_names=json.dumps(request.player_names),
                prop_type=request.prop_type,
                prop_value=request.prop_value,
                tournament=request.tournament,
                prediction=prediction_result['prediction'],
                confidence=prediction_result['confidence'],
                expected_stat=prediction_result['expected_stat'],
                response_time_ms=int((time.time() - start_time) * 1000),
                model_version="2.0.0"
            )
            db.add(prediction_history)
            db.commit()
        
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
        # Check cache first
        cached_players = cache_manager.get_cached_static_data("players")
        if cached_players is not None:
            return {"players": cached_players}
        
        # Get from data processor and cache
        players = data_processor.get_available_players()
        cache_manager.cache_static_data("players", players, ttl=1800)  # 30 minutes
        return {"players": players}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get players: {str(e)}")

@app.get("/teams")
async def get_available_teams():
    """
    Get list of all available team names for autocomplete
    """
    try:
        # Check cache first
        cached_teams = cache_manager.get_cached_static_data("teams")
        if cached_teams is not None:
            return {"teams": cached_teams}
        
        # Get from data processor and cache
        teams = data_processor.get_available_teams()
        cache_manager.cache_static_data("teams", teams, ttl=1800)  # 30 minutes
        return {"teams": teams}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get teams: {str(e)}")

@app.get("/tournaments")
async def get_available_tournaments():
    """
    Get list of all available tournament names for autocomplete
    """
    try:
        # Check cache first
        cached_tournaments = cache_manager.get_cached_static_data("tournaments")
        if cached_tournaments is not None:
            return {"tournaments": cached_tournaments}
        
        # Get from data processor and cache
        tournaments = data_processor.get_available_tournaments()
        cache_manager.cache_static_data("tournaments", tournaments, ttl=1800)  # 30 minutes
        return {"tournaments": tournaments}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get tournaments: {str(e)}")

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

@app.get("/metrics")
async def get_metrics():
    """
    Get system metrics and monitoring data
    """
    try:
        return monitor.get_summary()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")

@app.get("/health/detailed")
async def get_detailed_health():
    """
    Get detailed health status with performance metrics
    """
    try:
        return create_monitoring_report()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get health status: {str(e)}")

@app.get("/performance")
async def get_performance_metrics():
    """
    Get performance metrics and statistics
    """
    try:
        return {
            "performance_summary": monitor._get_performance_summary(),
            "thresholds": monitor.thresholds,
            "recent_errors": monitor.errors[-5:] if monitor.errors else []
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get performance metrics: {str(e)}")

@app.get("/cache/stats")
async def get_cache_stats():
    """
    Get cache statistics and performance metrics
    """
    try:
        return {
            "cache_stats": cache_manager.get_cache_stats(),
            "cache_health": get_cache_health(),
            "cache_info": cache_manager.get_cache_info()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get cache stats: {str(e)}")

@app.post("/cache/invalidate")
async def invalidate_cache(
    cache_type: str = "prediction",
    current_user: User = Depends(get_current_user_optional)
):
    """
    Invalidate cache entries (requires authentication)
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required for cache management"
        )
    
    try:
        if cache_type == "prediction":
            count = cache_manager.invalidate_prediction_cache()
            return {"message": f"Invalidated {count} prediction cache entries"}
        elif cache_type == "static":
            cache_manager.long_term_cache.clear()
            return {"message": "Invalidated all static data cache"}
        elif cache_type == "all":
            cache_manager.memory_cache.clear()
            cache_manager.long_term_cache.clear()
            cache_manager.player_cache.clear()
            return {"message": "Invalidated all cache entries"}
        else:
            raise HTTPException(status_code=400, detail="Invalid cache type")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to invalidate cache: {str(e)}")

@app.post("/export/prediction")
async def export_prediction(
    request: PredictionRequest,
    export_format: str = "csv",
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Export a prediction result in specified format
    """
    try:
        # Generate prediction (without caching for export)
        features = data_processor.process_request(request, strict_mode=request.strict_mode)
        sample_details = features.pop('sample_details', None)
        prediction_result = prediction_model.predict(features, request.prop_value, sample_details)
        
        # Generate prediction curve
        prediction_curve = prediction_model.generate_prediction_curve(
            features, request.prop_value, step=0.5, range_size=3
        )
        prediction_result['prediction_curve'] = prediction_curve
        
        request_data = request.dict()
        
        if export_format.lower() == "csv":
            # Export main prediction
            csv_content = prediction_exporter.export_prediction_to_csv(prediction_result, request_data)
            filename = generate_export_filename("prediction", "csv")
            return prediction_exporter.create_csv_response(csv_content, filename)
        
        elif export_format.lower() == "json":
            # Export as JSON
            export_data = {
                "request": request_data,
                "prediction": prediction_result,
                "exported_at": datetime.now().isoformat()
            }
            filename = generate_export_filename("prediction", "json")
            return prediction_exporter.create_json_response(export_data, filename)
        
        else:
            raise HTTPException(status_code=400, detail="Unsupported export format. Use 'csv' or 'json'")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

@app.post("/export/prediction-curve")
async def export_prediction_curve(
    request: PredictionRequest,
    export_format: str = "csv",
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Export prediction curve data in specified format
    """
    try:
        # Generate prediction curve only
        features = data_processor.process_request(request, strict_mode=request.strict_mode)
        sample_details = features.pop('sample_details', None)
        
        prediction_curve = prediction_model.generate_prediction_curve(
            features, request.prop_value, step=0.25, range_size=4  # More detailed curve
        )
        
        request_data = request.dict()
        
        if export_format.lower() == "csv":
            csv_content = prediction_exporter.export_prediction_curve_to_csv(prediction_curve, request_data)
            filename = generate_export_filename("prediction_curve", "csv")
            return prediction_exporter.create_csv_response(csv_content, filename)
        
        elif export_format.lower() == "json":
            export_data = {
                "request": request_data,
                "prediction_curve": prediction_curve,
                "exported_at": datetime.now().isoformat()
            }
            filename = generate_export_filename("prediction_curve", "json")
            return prediction_exporter.create_json_response(export_data, filename)
        
        else:
            raise HTTPException(status_code=400, detail="Unsupported export format. Use 'csv' or 'json'")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

@app.get("/export/history")
async def export_prediction_history(
    export_format: str = "csv",
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Export user's prediction history (requires authentication)
    """
    try:
        # Get user's prediction history
        predictions = db.query(PredictionHistory).filter(
            PredictionHistory.user_id == current_user.id
        ).order_by(PredictionHistory.created_at.desc()).limit(limit).all()
        
        # Convert to dict format
        prediction_dicts = []
        for pred in predictions:
            prediction_dicts.append({
                'created_at': pred.created_at.isoformat() if pred.created_at else '',
                'player_names': pred.player_names,
                'prop_type': pred.prop_type,
                'prop_value': pred.prop_value,
                'tournament': pred.tournament,
                'prediction': pred.prediction,
                'confidence': pred.confidence,
                'expected_stat': pred.expected_stat,
                'response_time_ms': pred.response_time_ms,
                'model_version': pred.model_version
            })
        
        if export_format.lower() == "csv":
            csv_content = analytics_exporter.export_user_prediction_history(prediction_dicts, current_user.id)
            filename = generate_export_filename(f"history_user_{current_user.id}", "csv")
            return prediction_exporter.create_csv_response(csv_content, filename)
        
        elif export_format.lower() == "json":
            export_data = {
                "user_id": current_user.id,
                "username": current_user.username,
                "predictions": prediction_dicts,
                "total_count": len(prediction_dicts),
                "exported_at": datetime.now().isoformat()
            }
            filename = generate_export_filename(f"history_user_{current_user.id}", "json")
            return prediction_exporter.create_json_response(export_data, filename)
        
        else:
            raise HTTPException(status_code=400, detail="Unsupported export format. Use 'csv' or 'json'")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

@app.get("/export/metrics")
async def export_system_metrics(
    export_format: str = "csv",
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Export system metrics (requires authentication)
    """
    try:
        # Get system metrics
        metrics_data = monitor.get_summary()
        
        if export_format.lower() == "csv":
            csv_content = analytics_exporter.export_system_metrics(metrics_data)
            filename = generate_export_filename("system_metrics", "csv")
            return prediction_exporter.create_csv_response(csv_content, filename)
        
        elif export_format.lower() == "json":
            export_data = {
                "metrics": metrics_data,
                "exported_at": datetime.now().isoformat(),
                "exported_by": current_user.username
            }
            filename = generate_export_filename("system_metrics", "json")
            return prediction_exporter.create_json_response(export_data, filename)
        
        else:
            raise HTTPException(status_code=400, detail="Unsupported export format. Use 'csv' or 'json'")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

@app.on_event("startup")
async def startup_event():
    """Initialize database and other resources on startup"""
    logger.info("Initializing database...")
    init_db()
    logger.info("Database initialized successfully")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 