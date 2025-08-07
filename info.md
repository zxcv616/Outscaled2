# Map 1-1 vs Map 1-2 Betting Logic in League of Legends (Clarification for ML Model Behavior)

## 🎯 Core Clarification

In the context of **sports betting on League of Legends**, the terms **"Map 1-1"** and **"Map 1-2"** are not just filters for certain games — they refer to **how sportsbooks define the statistical scope of the bet**.

---

## ✅ Correct Interpretation (Sportsbook Logic)

- **Map 1-1**
  - Refers to **Map 1 only** of each series.
  - Bets are graded solely on the player's performance in Map 1.
  - This is a per-game stat — each player has **one entry per series**.

- **Map 1-2**
  - Refers to the **combined performance across Map 1 and Map 2** of each series.
  - This is **not** a per-map average.
  - It means **summing kills (or other stats) from both Map 1 and Map 2**, and then using that total as the prediction target.
  - Each series contributes **one data point per player** — the total from Map 1 + Map 2.

---

## ❌ Incorrect Interpretation (Likely Model Behavior)

The model currently appears to treat `Map 1-2` as:
- A filter over game data: "show me all Map 1 and Map 2 games"
- Then applies **per-map averages or volatility**
- This would result in:
  - Misleading expected values
  - Improper confidence scaling
  - Inconsistent volatility profiles
  - Sample size being counted as **number of maps**, not number of series

---

## 📉 Why This Causes Prediction Errors

Example:
- Player plays 2 maps in a series
  - Map 1: 2 kills
  - Map 2: 3 kills
- Sportsbook prop for “Map 1-2 Kills” = 4.5

**Correct prediction target** = 5  
**Incorrect model (per-map average)** = (2 + 3) / 2 = 2.5

This causes:
- Underestimated expected stat
- Inflated volatility (since map-level variance is higher)
- Lower confidence despite higher sample quality

---

## ✅ Correct Implementation Required

To align with betting logic:

1. **Group by `series_id`**
   - Use `game_number == 1` as anchor
   - Combine all maps in the specified range (e.g., Map 1 + Map 2)

2. **Aggregate player stats at the series level**
   - Example:  
     ```python
     df_series = df[df['game'].isin([1, 2])]
     df_series_grouped = df_series.groupby(['series_id', 'player'])['kills'].sum().reset_index()
     ```

3. **Then calculate expected_stat, std_dev, volatility, and bootstrap confidence**
   - On **series-level totals**, not individual maps

4. **Ensure sample size is counted in SERIES, not maps**
   - If you have 63 maps, but they're from 32 series, your sample size is 32

---

## 📌 Summary of Required Fix

| Area | Fix |
|------|-----|
| **Aggregation** | Sum stats across map range (Map 1 + 2), per series |
| **Grouping Key** | Use `series_id` not `map_id` |
| **Volatility** | Calculate based on series totals |
| **Expected Stat** | Use average of per-series totals |
| **Confidence** | Bootstrap from series-level sample |
| **Sample Size** | Count series, not maps |

---

## ✅ Why This Matters

- Prevents underestimation of expected performance
- Reduces unnecessary volatility due to per-map swing
- Ensures confidence intervals align with real-world payout logic
- Aligns machine learning output with **actual sportsbook rules**

---

Please verify whether the current `Map 1-2` logic is using per-map or per-series aggregation. If not already doing so, refactor the model’s data processing pipeline to treat `Map 1-2` as a **combined, per-series stat**, not a per-map average.
