⚠️ Remaining High-Priority Fixes
Handled with domain-aware, risk-reducing strategies for predictive accuracy in esports betting models.

1. 🧠 Series Grouping Logic
Problem: Current logic assumes matches with similar timestamps and team names belong to the same series — unreliable in tournament formats with multiple games per day.
Why it matters: Many props (like "total kills in series" or "map 1-2 only") require accurate grouping to avoid inflated or diluted stats. Misgrouping results in bad training signals and misleading predictions.

Fix (Smart Quant Approach):

Use game_number == 1 as an anchor to identify series starts.

Assign a unique series_id by combining team_id + date + game_number == 1.

Optionally cross-check against match_id if available from external data sources (e.g., Oracle’s Elixir or Riot API).

Implement assertions: no more than 5 games per series, same teams only.

2. 📈 Temporal Confidence Calibration
Problem: Confidence is calibrated across pooled data instead of time-split sets. This assumes data stationarity, which doesn’t hold in esports due to rapid meta shifts.

Why it matters: A model well-calibrated in Patch 14.5 could be miscalibrated in Patch 14.13 due to role dominance flips or kill pacing changes. Bettors rely on accurate confidence — if drifted, they misprice risk.

Fix (Smart Quant Approach):

Use temporal cross-validation: train on one season or patch group, test on the next.

Update CalibratedClassifierCV with sliding windows (e.g., 2-month training, 1-month test).

Monitor confidence decay — retrain or re-calibrate when accuracy or log loss slips.

Visualize actual vs predicted probability (calibration curve) over time.

3. ⚖️ OVER/UNDER Balancing Review
Problem: Model is artificially weighted to produce ~48% OVER predictions, likely to simulate bookmaker behavior. This may skew results if you're not explicitly predicting book-adjusted outcomes.

Why it matters: In real-world betting, you'd want to model true performance, not mirror the market line — unless you're trying to beat or simulate the book. Artificial balancing introduces unnecessary bias into what should be a data-driven classification problem.

Fix (Smart Quant Approach):

Step 1: Evaluate the raw OVER rate from real-world props (e.g., 55% OVER, 45% UNDER).

Step 2: Decide the goal:

If building a forecasting model, use real distribution — remove class balancing.

If building a market simulation model, make the balancing explicit and tunable.

Step 3: Include the "distance to market line" as a feature, not an enforced label balance.