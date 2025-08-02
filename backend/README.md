# Outscaled.GG Backend API

A machine learning engine that predicts **OVER/UNDER** for League of Legends player prop bets using real match data from Oracle's Elixir.

## 🚀 Features

- **Prop Bet Predictions**: Predict OVER/UNDER for kills and assists
- **Map Range Support**: Analyze specific map ranges (e.g., Maps 1-2)
- **Player & Combo Support**: Handle single players or player combinations
- **Feature Engineering**: 40+ robust features including form analysis, position factors, and volatility metrics
- **Confidence Intervals**: Statistical confidence intervals for predictions
- **Reasoning Engine**: Rule-based explanations for predictions
- **Real Data**: Trained on 2024-2025 professional match data

## 📊 API Endpoints

### POST `/predict`

Predict OVER/UNDER for League of Legends player prop bets.

**Request Body:**
```json
{
  "player_names": ["Wink"],
  "prop_type": "assists",
  "prop_value": 21.5,
  "map_range": [1, 2],
  "opponent": "FPX",
  "tournament": "LPL",
  "team": "JDG",
  "match_date": "2025-08-01T02:00:00",
  "position_roles": ["SUP"]
}
```

**Response:**
```json
{
  "prediction": "OVER",
  "confidence": 82.3,
  "expected_stat": 17.8,
  "confidence_interval": [15.2, 21.1],
  "reasoning": "Recent form lower than prop line. Low volatility. Opponent is top-tier.",
  "player_stats": {
    "avg_assists": 17.8,
    "form_z_score": -1.25,
    "maps_played": 15,
    "position_factor": 1.2
  },
  "data_years": "2024 (108 matches), 2025 (67 matches)"
}
```

### GET `/health`

Health check endpoint.

## 🛠️ Setup

### Option 1: Docker (Recommended)

1. **Build and run with Docker Compose:**
   ```bash
   docker-compose up --build
   ```

2. **Access the API:**
   - API: http://localhost:8000
   - Documentation: http://localhost:8000/docs

### Option 2: Local Development

1. **Install dependencies:**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Run the server:**
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

## 🧪 Testing

Run the test script to verify the API functionality:

```bash
cd backend
python test_api.py
```

## 📁 Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI application
│   ├── models/
│   │   └── prediction_model.py  # ML model implementation
│   └── utils/
│       └── data_processor.py    # Data processing & feature engineering
├── requirements.txt         # Python dependencies
├── Dockerfile              # Docker configuration
├── test_api.py            # API test script
└── README.md              # This file
```

## 🔧 Configuration

The system uses the following data sources:
- `data/2024_LoL_esports_match_data_from_OraclesElixir.csv`
- `data/2025_LoL_esports_match_data_from_OraclesElixir.csv`

## 📈 Feature Engineering

The system engineers 40+ features including:

- **Recent Stats**: Average kills/assists, standard deviations
- **Long-term Trends**: Historical averages across full dataset
- **Form Analysis**: Z-scores and deviation ratios
- **Position Factors**: Role-specific adjustments
- **Quality Metrics**: Sample size and volatility scores
- **Early/Mid Game**: Gold, XP, CS differentials at 10/15/20 minutes

## 🎯 Model Architecture

- **Classifier**: Rule-based model (MVP) / XGBoost (Production)
- **Type**: Binary classification (OVER/UNDER)
- **Calibration**: Probability calibration for confidence scores
- **Output**: Prediction + confidence + reasoning

## 🚀 Deployment

### Docker Deployment
```bash
docker-compose up --build -d
```

### Cloud Deployment
The Docker setup is compatible with:
- **Fly.io**: `fly deploy`
- **Render**: Connect GitHub repository
- **AWS EC2**: `docker-compose up -d`

## 📝 API Documentation

Once running, visit http://localhost:8000/docs for interactive API documentation powered by Swagger UI.

## 🔍 Troubleshooting

1. **Data Loading Issues**: Ensure CSV files are in the `data/` directory
2. **Port Conflicts**: Change port in `docker-compose.yml` if 8000 is occupied
3. **Memory Issues**: The system loads large CSV files - ensure sufficient RAM

## 📊 Data Sources

- **Oracle's Elixir**: Professional League of Legends match data
- **Years**: 2024-2025 professional matches
- **Format**: Player performance per game with map indexing

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes
4. Test with `python test_api.py`
5. Submit a pull request

## 📄 License

This project is proprietary software for Outscaled.GG. 