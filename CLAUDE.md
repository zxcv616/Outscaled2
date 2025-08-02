# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Outscaled2 is a full-stack web application for predicting League of Legends player performance using machine learning. It consists of:
- **Backend**: Python FastAPI service with ML prediction models
- **Frontend**: React TypeScript application with Material-UI
- **ML Model**: Random Forest Classifier with calibrated probabilities for OVER/UNDER predictions

## Key Commands

### Backend Development
```bash
cd backend
python -m uvicorn app.main:app --reload  # Run development server
python run_tests.py                       # Run all backend tests
python run_confidence_tests.py quick      # Quick confidence test
python run_confidence_tests.py            # Full test suite
```

### Frontend Development
```bash
cd frontend
npm start                    # Start development server
npm test                     # Run tests
npm test:ci                  # Run tests in CI mode
npm run build               # Build for production
```

### Full Stack
```bash
docker-compose up            # Run both services
docker-compose up --build    # Rebuild and run
```

## Architecture & Key Components

### Backend Structure
- **FastAPI Application**: `backend/app/main.py` - REST API endpoints
- **ML Model**: `backend/app/models/prediction_model.py` - Random Forest with calibration
- **Data Processing**: `backend/app/utils/data_processor.py` - Handles player data and feature engineering
- **Tiered Data System**: Weights data by relevance (Tier 1-5) for better predictions

### Frontend Structure
- **Main App**: `frontend/src/App.tsx` - Theme and routing setup
- **Enhanced Form**: `frontend/src/components/enhanced/EnhancedPredictionForm.tsx` - Multi-step prediction form
- **API Service**: `frontend/src/services/api.ts` - Backend communication
- **Type Definitions**: `frontend/src/types/api.ts` - TypeScript interfaces

### ML Model Features
- **Statistical Features**: avg_kills, std_dev_kills, form_z_score, maps_played, position_factor, volatility
- **Confidence Calculation**: Gap-based adjustment with tier weighting
- **Prediction Curve**: Generates predictions across prop value range

## Data Requirements

The application expects League of Legends match data in CSV format:
- Place files in `data/` (root) or `backend/data/`
- Must contain player performance statistics (kills, assists, etc.)

## Testing Strategy

### Backend Testing
- Unit tests in `backend/tests/`
- Run `python run_tests.py` for full suite
- Use `run_confidence_tests.py` for confidence calculation validation

### Frontend Testing
- Jest tests with React Testing Library
- Mock API responses in `frontend/__mocks__/`
- Run `npm test` for interactive mode

## API Endpoints

- `POST /predict` - Main prediction endpoint
- `GET /players` - Available player names
- `GET /teams` - Available team names  
- `GET /tournaments` - Available tournament names
- `POST /check-data-availability` - Check if data exists for criteria

## Development Patterns

### Backend Patterns
- Pydantic models for request/response validation
- Tiered data filtering for relevance
- Calibrated probability outputs
- Comprehensive error handling with HTTPException

### Frontend Patterns
- Material-UI dark theme with custom styling
- Multi-step form with validation
- Real-time autocomplete for player/team selection
- Responsive prediction curve visualization with Recharts

## Key Dependencies

### Backend
- fastapi==0.104.1
- scikit-learn>=1.4.0
- pandas>=2.2.0
- numpy>=1.26.0

### Frontend
- React 19 with TypeScript
- Material-UI v7
- Recharts for data visualization
- Axios for API calls

## Important Configuration

- Backend runs on port 8000
- Frontend runs on port 3000 with proxy to backend
- CORS configured for all origins in development
- Docker Compose available for containerized deployment