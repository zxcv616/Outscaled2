# Outscaled.GG

Series-level player-prop prediction for League of Legends esports, with a live
market-line paper-trading pipeline and dashboard.

## How it works

```
Oracle's Elixir CSVs (data/)          Underdog LoL board (public API)
        │                                      │
        ▼                                      ▼
  series identification              scripts/log_lines.py  ──►  data/lines/lines_log.csv
  (day + team pair + game seq)                │                        │
        │                                     ▼                        ▼
        ▼                            model p_over vs payout    scripts/grade_lines.py
  app/props/model.py                 break-even per line       (outcomes + track record)
  recency-weighted empirical                                           │
  + negative binomial blend,                                           ▼
  opponent kill-env adjustment                              frontend dashboard (Board /
                                                            Track record / Explorer)
```

- **Betting semantics** (see `Betting_Logic.md`): "Maps 1-2 kills 8.5" is graded
  on the SUM of kills across games 1-2 of a series. One data point per series;
  sample size counts series, never maps.
- **Model** (`backend/app/props/model.py`): P(over) blends a recency-weighted
  empirical distribution of the player's actual series totals (half-life 120
  days) with a Negative Binomial fit to the weighted moments; the blend weight
  grows with effective sample size. Optional opponent adjustment scales the
  expected kill environment by how many kills the opponent allows vs. the
  global average (dampened, clipped). Bootstrap CIs resample real series
  totals. All calculations honor an `as_of` cutoff (leak-free).

## Validation

Walk-forward backtest on 2026 out-of-sample data (~136K graded predictions,
lines at players' prior 35/50/65th percentiles):

| Config | Brier (coin flip .250) | Log loss (coin flip .693) |
|---|---|---|
| Kills, Maps 1-2 | .2281 | .6486 |
| Kills, Map 1 | .2276 | .6477 |
| Assists, Maps 1-2 | .2285 | .6495 |

Calibration holds within 1-2 points across the 0.35-0.75 range, stable every
month of 2026. Reproduce with:

```bash
cd backend && venv/bin/python -m app.props.backtest --data-dir ../data
```

**Status: paper-trade mode.** Backtest lines are synthetic; the pipeline is now
logging real Underdog lines daily and grading them. Real-money threshold: the
>=6% edge bucket must hold a hit rate above ~58% over a few hundred graded
picks (per-leg break-even on a 2-pick 3x entry is 57.7%).

## Running

```bash
# dashboard (API + built frontend on one port)
cd backend && venv/bin/uvicorn app.props.server:app --port 8010

# frontend dev server (hot reload, proxies /api to :8010)
cd frontend && npm install && npm run dev

# one-off prediction
cd backend && venv/bin/python scripts/props_predict.py \
  --player Faker --prop kills --line 5.5 --maps 1-2 --opponent-team "Gen.G"

# line logging / grading (cron runs these at 10:00+20:00 / 12:30 daily)
backend/scripts/daily_lines.sh log
backend/scripts/daily_lines.sh grade
```

Data: place Oracle's Elixir match-data CSVs in `data/` (gitignored; re-download
the current-year file from oracleselixir.com to grade recent matches).

## Layout

- `backend/app/props/` — data loading + series identification, model, backtest,
  line ingestion (Underdog API; PrizePicks via captured JSON), FastAPI server
- `backend/scripts/` — prediction CLI, line logger, grader, daily cron wrapper
- `frontend/` — Vite + React + TS dashboard (Board / Track record / Explorer)
- `data/lines/` — logged market lines with frozen model predictions, graded results
