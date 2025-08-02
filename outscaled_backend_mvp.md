# Outscaled.GG Backend & Model MVP Specification

## 🌟 Objective

Build a robust machine learning engine that predicts **OVER/UNDER** for League of Legends player (or combo) prop bets (kills or assists), scoped to a specific map range (e.g., Maps 1-2), using real match data.

---

## 🔹 1. CSV Dataset Format

The model is trained on professional match data from Oracle’s Elixir. Each row in the dataset represents a **player performance in a single game**. Multiple rows with the same `gameid` correspond to different players in the same match.

### Key Columns (subset):

| Column                                         | Description                    |
| ---------------------------------------------- | ------------------------------ |
| `gameid`                                       | Unique match ID                |
| `league`, `split`                              | Tournament details             |
| `date`, `patch`                                | Temporal context               |
| `playername`                                   | Summoner name                  |
| `teamname`, `side`                             | Team and side (Blue/Red)       |
| `position`                                     | Role: top, jng, mid, bot, sup  |
| `kills`, `assists`, `deaths`                   | Core stats                     |
| `damagetochampions`, `visionscore`, `total cs` | Performance indicators         |
| `goldat10`, `xpat10`, `csat10`                 | Early-game power metrics       |
| `golddiffat15`, etc.                           | Time-window deltas vs opponent |

### Map Index Generation

* `map_index_within_series` is inferred by grouping `gameid` prefix and ranking maps:

```python
df["match_series"] = df["gameid"].str.split("_").str[0]
df["map_index_within_series"] = df.groupby("match_series")["gameid"].rank("dense").astype(int)
```

---

## 📊 2. Required Inputs (Frontend/API)

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

---

## ⚖️ 3. Data Pipeline

### a. Data Filtering

* Match players by `player_names`
* Select rows within `map_range`
* Filter by team/opponent/tournament

### b. Aggregation & Normalization

* Aggregate stats (e.g., kills, assists) across `map_range`
* Normalize per map played
* Handle NaNs, low sample size, patch drift

---

## 🧠 4. Feature Engineering

| Feature Group      | Examples                                                     |
| ------------------ | ------------------------------------------------------------ |
| Recent Stats       | `avg_kills`, `avg_assists`, `std_dev_assists` (within range) |
| Long-Term          | Full dataset averages: `longterm_kills_avg`                  |
| Deviation          | `form_z_score`, `form_deviation_ratio`                       |
| Role-Aware         | `position_factor` (e.g., SUP high assists weight)            |
| Opponent Context   | `opponent_strength` based on team stats                      |
| Pressure           | `tournament_importance` scale (e.g. Worlds = 1.0)            |
| Quality/Volatility | `maps_played`, `sample_size_score`                           |

For combos:

* Aggregate key stats
* Optionally average or concatenate features
* Apply confidence penalty

---

## 📊 5. Model Architecture

| Component   | Value                              |
| ----------- | ---------------------------------- |
| Model       | `XGBoostClassifier` (binary)       |
| Type        | OVER (1) / UNDER (0) classifier    |
| Label       | `actual_stat > prop_value`         |
| Calibration | `CalibratedClassifierCV` (sigmoid) |
| Output      | Class + Probability                |

---

## 🔢 6. Labeling Strategy

* Each training point is labeled:

```python
label = 1 if actual > prop_value else 0
```

* Simulate multiple `prop_value`s per player-match (e.g., actual±2) to expand training size

---

## 🔄 7. Inference Output

```json
{
  "prediction": "LESS",
  "confidence": 82.3,
  "expected_stat": 17.8,
  "confidence_interval": [15.2, 21.1],
  "reasoning": "Recent form lower than prop line. Low volatility. Opponent is top-tier.",
  "player_stats": {
    "avg_assists": 17.8,
    "form_z_score": -1.25,
    ...
  },
  "data_years": "2024 (108 matches), 2025 (67 matches)"
}
```

---

## 🔬 8. Reasoning Engine

* Rule-based generator interprets:

  * Stat deltas vs prop
  * `form_z_score` magnitude
  * Volatility
  * Opponent/tournament pressure

---

## ✅ 9. MVP Checklist

| Task                                  | Description                                 |
| ------------------------------------- | ------------------------------------------- |
| ✅ Data ingestion from multi-year CSVs | `pandas` + preprocessing                    |
| ✅ Map range aggregation               | `map_index_within_series` logic             |
| ✅ Feature engineering pipeline        | 40+ robust features                         |
| ✅ Simulated labeling                  | `actual_stat > prop_value` + variations     |
| ✅ XGBoostClassifier + calibration     | Stable, interpretable classifier            |
| ✅ API prediction output               | JSON with prediction, confidence, reasoning |
| ✅ Combo prop support                  | Feature aggregation + adjusted confidence   |
| ✅ Dynamic reasoning engine            | Rule-based explainability                   |

---

## 🔁 Stretch Goals (Post-MVP)

* Quantile regression for predicted confidence intervals
* SHAP feature explanation
* EV calculator vs prop lines
* Patch-based meta drift detection
* Role-specific sub-models
* Time-decay weighting for recent matches

---

## 🐳 Docker + docker-compose Setup

To ensure portable development and deployment:

### Dockerfile (backend/)

```Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY ./backend /app
RUN pip install --upgrade pip && pip install -r requirements.txt
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### docker-compose.yml

```yaml
version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app
    environment:
      - ENV=production
```

### .dockerignore

```
__pycache__/
*.pyc
*.csv
*.log
.env
```

---

To start:

```bash
docker-compose up --build
```

The API will be available at [http://localhost:8000/docs](http://localhost:8000/docs).

Use this setup for local dev, staging, or deploy to cloud with tools like Fly.io, Render, or EC2.
