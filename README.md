# Outscaled2 - League of Legends Prediction Platform

A full-stack web application for predicting League of Legends player performance using machine learning.

## Testing

### Backend Tests
```bash
cd backend
python run_confidence_tests.py quick    # Quick confidence test
python run_confidence_tests.py          # Full test suite
```

### Frontend Tests
```bash
cd frontend
npm test
```

## Data Requirements

The application requires League of Legends match data in CSV format. Place your data files in:
- `data/` (root level)
- `backend/data/`

## Model Algorithm

### Core Machine Learning Architecture

**Base Model**: Random Forest Classifier with Calibrated Probabilities
- **Algorithm**: RandomForestClassifier (n_estimators=100, max_depth=10)
- **Calibration**: CalibratedClassifierCV with isotonic regression
- **Training Data**: Real historical player performance from 2024-2025 datasets
- **Class Balance**: Balanced class weights for OVER/UNDER predictions

### Feature Engineering

**Statistical Features**:
- `avg_kills`: Historical average kills per map
- `std_dev_kills`: Standard deviation of kills (volatility measure)
- `form_z_score`: Recent performance vs historical average (Z-score)
- `maps_played`: Sample size for statistical reliability
- `position_factor`: Position-specific performance multipliers
- `volatility`: Composite volatility index (0.1-0.9 scale)

**Tier-Based Data Filtering**:
- **Tier 1**: Exact tournament matches (weight: 1.0)
- **Tier 2**: Same region/year (weight: 0.8)
- **Tier 3**: Same team/year (weight: 0.7)
- **Tier 4**: Recent matches 6-12 months (weight: 0.5)
- **Tier 5**: Older matches/other teams (weight: 0.3)

### Prediction Logic

**Expected Statistic Calculation**:
```
expected_stat = (base_expected + form_adjustment - volatility_penalty + confidence_adjustment) * position_factor
```

Where:
- `base_expected`: Historical average kills
- `form_adjustment`: tanh(form_z_score * 0.5) * 0.8 (bounded impact)
- `volatility_penalty`: volatility * 0.3
- `confidence_adjustment`: (model_confidence - 0.5) * 2.0
- `position_factor`: Position-specific multiplier

**Confidence Calculation**:
```
gap = abs(expected_stat - prop_value)
gap_ratio = gap / max(prop_value, 1)
gap_adjustment = min(gap_ratio * 2.0, 0.5)

if prediction == "OVER":
    adjusted_confidence = base_model_confidence + gap_adjustment
else:
    adjusted_confidence = (1 - base_model_confidence) + gap_adjustment

final_confidence = adjusted_confidence * tier_weight
```

**Confidence Intervals**: Bootstrap method with 1000 samples
- Incorporates volatility and form factors
- 95% confidence intervals using percentile method
- Handles small sample sizes with quantile-based fallback

### Statistical Validation

**Model Performance Metrics**:
- **Accuracy**: Measured on calibration set
- **Log Loss**: Probability calibration quality
- **Mean Predicted Probability**: Calibration validation
- **Actual OVER Rate**: Ground truth comparison

**Sample Quality Assessment**:
- **High Quality**: 20+ maps, low volatility
- **Medium Quality**: 10-19 maps, moderate volatility  
- **Low Quality**: <10 maps, high volatility

### Prediction Curve Generation

Generates predictions across prop value range (±1.5 from input):
- **Step Size**: 0.5 increments
- **Confidence Scaling**: Dynamic based on gap ratio
- **Tier Weighting**: Applied to all curve points
- **Volatility Integration**: Affects confidence bounds

## Confidence Calculation Fix

The application includes a comprehensive confidence calculation system that ensures consistency between top-level confidence and prediction curve confidence.

### Testing the Fix
```bash
cd backend
python run_confidence_tests.py quick
```

### Documentation
- `backend/TESTING_GUIDE.md` - Complete testing guide
- `backend/CONFIDENCE_FIX_SUMMARY.md` - Fix details

