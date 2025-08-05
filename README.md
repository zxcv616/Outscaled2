# Outscaled.GG

Prediction Model for League of Legends

## Model Design Overview

Outscaled is designed for real-time, high-confidence forecasting of player performance metrics such as kills and assists. The model incorporates safe statistical practices, smart sample validation, and betting-context-aware feature engineering — with no artificial constraints or biases.

---

## Statistical Methodology

- **Bootstrap Confidence Intervals**: Predictions use bootstrap percentile confidence intervals (non-parametric) with quantile fallback for low samples. No gamma or normality assumptions are made.
- **Safe Division**: All volatility, z-score, and confidence calculations use `safe_divide()` to prevent division-by-zero or NaNs.
- **Sample Size Enforcement**:
  - `< 5 maps`: fallback prediction only
  - `5–9 maps`: quantile-based interval
  - `10–14 maps`: bootstrap with warnings
  - `15+ maps`: full feature activation and tight confidence

---

## Betting Logic Integration

- **Series Identification**:
  - Uses `game_number == 1` as an anchor to define new series.
  - Series grouped by team, date, and opponent context.
  - Enforced validation: max 5 maps, same teams, sequential games only.
- **No Role-Based Multipliers**:
  - Position multipliers (e.g. `SUP = 0.85`) have been eliminated.
  - All role-specific modeling is done through actual data only.
- **Market Intelligence Features**:
  - `market_distance` = `(expected_stat - implied_prop) / implied_prop`
  - `market_confidence_score` reflects expected stat confidence near betting line
  - No artificial class balance (e.g., 48% OVER targeting) is used.

---

## Meta-Aware Confidence Calibration

- **Patch Grouping**:
  - Matches are grouped into 2-week rolling patch windows.
  - Recency weighting applied to favor more recent data.
- **Temporal Sliding Calibration**:
  - Uses 2-month training / 1-month testing splits.
  - Separate confidence calibrators are trained for each patch window.
- **Confidence Decay Detection**:
  - Log loss is monitored across windows.
  - Triggers retraining if drift exceeds threshold.

---

## Feature Engineering

- `avg_kills`, `std_dev_kills`: Volatility-aware historical stats
- `form_z_score`: Safe z-score against historical baseline
- `maps_played`, `series_played`: Sample tracking and validation
- `patch_recency_weight`: Scales recent patches higher
- `market_distance`, `market_confidence_score`: Market-aware analysis
- `sample_size_score`: Tiered sample quality metric

---

## Safety & Validation

- `safe_divide()` used for all ratio metrics.
- Series groupings undergo structural validation before aggregation.
- Sample quality tiers strictly enforced before prediction is allowed.
- Fallback triggers are logged and transparent.

---

## Model Architecture

- **Base Model**: `RandomForestClassifier` (100 trees, max_depth=10)
- **Confidence Calibration**: `TemporalConfidenceCalibrator` (custom implementation)
- **Prediction Flow**:
  1. Input features validated
  2. Series grouped, meta weighted
  3. Raw model prediction
  4. Patch-aware confidence calibrated
  5. Bootstrap CI and final prediction returned

---

## Project Structure

- `app/models/prediction_model.py`: Core inference logic
- `app/models/temporal_calibration.py`: Temporal confidence calibration
- `app/utils/data_processor.py`: Smart series logic, validation
- `tests/`: Includes calibration + series validation test suites

---

## Testing

Run backend tests:
```bash
cd backend
python run_confidence_tests.py
python -m pytest tests/test_temporal_calibration.py -v
python -m pytest tests/test_betting_logic_validation.py -v
```

---

## API Example

Request:
```json
{
  "player_names": ["Player1"],
  "prop_type": "kills",
  "prop_value": 4.5,
  "map_range": [1, 2],
  "opponent": "Team2",
  "tournament": "LCS",
  "match_date": "2025-08-04",
  "position_roles": ["mid"]
}
```

Response:
```json
{
  "prediction": "OVER",
  "confidence": 72.3,
  "expected_stat": 5.2,
  "confidence_interval": [4.1, 6.3],
  "data_quality": "high",
  "patch_group": "patch_14_12",
  "confidence_warning": "",
  "temporal_calibration": {
    "calibration_method": "bootstrap_percentile",
    "patch_awareness": true,
    "needs_retraining": false
  }
}
```

---

## Final Notes

Outscaled.GG now operates with:
- Statistically sound methodology
- Smart series logic for tournament realism
- Meta-aware, adaptive confidence
- Real-world betting logic alignment
- Transparent fallback handling

It is designed for serious forecasting in the high-variance world of professional League of Legends esports.

