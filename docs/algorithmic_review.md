# Algorithmic Review — Outscaled.GG Props Model

Review date: 2026-07-19
Scope: prediction model and paper-trading pipeline (not security/privacy).

Overall verdict: the modeling math is careful and leak-free; the biggest flaw is
conceptual (how "edge" is defined), which inflates the Track Record headline number.

---

## 1. "Edge" is computed against parlay payouts, not the book's line-implied probability

**Severity: high (affects the core decision metric)**

`best_edge = p_over - breakeven` where `breakeven` comes from `breakeven_probability(payout_multiplier)` (`lines.py:158`, `log_lines.py:196`).

- `p_over` (from `model.py`) is a forward-looking probability of the *stat total*.
- The payout multiplier already encodes the book's probability **plus vig**, on a
  *parlay entry*, which is a different market from the single line `total > line`.
- We therefore compare our model's probability to the payout-implied odds, not to
  the book's probability implied by the *line* (e.g. 8.5).
- A "6% edge" here means "our model disagrees with payout-implied odds by 6%",
  not "the book is wrong by 6%".

Worst case: PrizePicks payout is hardcoded to `1.0` (`lines.py:146-147`), giving a
fixed `breakeven = 1/sqrt(3) ≈ 0.577` for *every* line. The "edge" then becomes
`p_over - 0.577` purely as a function of our model — it carries no market signal at
all. The Track Record's edge buckets and the "real-money threshold" (README) are
built on this number, so the go/no-go decision is measuring the wrong thing.

**Fix direction:** derive the book's `p_over` from the line itself (no-vig midpoint
of the market, or a market-implied model), and define edge as
`our_p_over - book_p_over`. Keep payouts only for stake sizing, not for edge.

---

## 2. Empirical vs NB blend mixes two different questions

**Severity: low-medium**

`model.py:242,245`:
- `p_emp = weighted fraction of (totals > line/factor)` — empirical exceedance
  evaluated at the *scaled line*.
- `p_nb = _nb_p_over(adj_mean, adj_var, line)` — NB probability at the *unscaled line*.

The empirical component answers "P(total > line/factor)"; the NB component answers
"P(total > line)". They are then linearly blended via `w_emp`. For the NB, the
adjustment is applied to the moments (mean/var) before computing `p_over`; for the
empirical, the adjustment is applied by transforming the threshold. These are not
strictly equivalent (the NB is a parametric family; the empirical is a step
function), so the blended quantity is a mix of two slightly different targets.

For small samples (`w_emp` near 0) NB dominates and the discrepancy is hidden; for
large samples the empirical dominates and the line-scaling is exact. Net effect is
small but the blend is not comparing like-for-like.

**Fix direction:** evaluate both components at the same target — either scale the
distribution for both, or scale the line for both, consistently.

---

## 3. Opponent adjustment is a team-level heuristic applied to an individual

**Severity: medium**

`model.py:164`: `factor = clip(sqrt(opp_mean / global_mean), 0.85, 1.2)`.

- Scales the player's *entire* kill distribution by how many kills the opponent
  allows on average.
- A team "bleeds kills" partly because *its opponents* are kill-heavy; your player's
  team may not be one of them. There is no player-position or role context — a
  supportive laner and a primary carry on the same team get the same bump.
- The square root is unjustified: no derivation says variance scales as the sqrt of
  the kill-environment ratio. Why not linear, or log? It is a heuristic presented as
  a derived quantity.

The clip (0.85–1.2) is a reasonable guardrail and prevents runaway values, but the
functional form is arbitrary.

**Fix direction:** justify or replace the transform; consider player-specific
opponent interaction (does *this* player overperform vs weak teams historically?),
or drop opponent adjustment until there is evidence it adds skill.

---

## 4. Backtest uses self-selected lines, not real market lines

**Severity: medium (overstates live performance)**

`backtest.py:38,83`: lines are placed at the player's own 35/50/65th weighted
percentiles, snapped to x.5. The model is then shown to be well-calibrated *at the
lines it chose for itself*.

- Calibration at self-selected percentiles ≠ calibration at market lines, which sit
  at psychologically round numbers (5.5, 6.5) where books deliberately shade.
- Brier 0.228 vs 0.25 coin flip is real but partly mechanical: a model near the
  median will beat coin flip at its own median lines.

This does not invalidate the backtest (it still tests leakage and ranking), but the
headline numbers should not be read as expected live performance.

**Fix direction:** backtest against real logged market lines (the same `lines_log.csv`
pipeline) so calibration is measured where the book actually prices.

---

## 5. Train/serve mismatch on `position`

**Severity: medium**

- Backtest restricts history by `position`: `model.predict(..., position=tgt.position)`
  (`backtest.py:79,100`).
- Live path never passes `position`: `server.py:114` and `log_lines.py:189` omit it.

A player who changed roles mid-window gets a *blended* history in production that the
backtest would have split. The validated model behavior and the served model
behavior differ, so backtest metrics don't transfer to production for role-switchers.

**Fix direction:** pass `position` consistently (or document why production ignores
it and re-validate without it).

---

## 6. Grading matches on date only, no series-integrity check

**Severity: low-medium (silent misgrade risk)**

`grade_lines.py:51`: matches a logged line to the player's first series within ±1 day
of `game_time`, disambiguating by opponent. It does **not** verify the matched
series has exactly `map_hi - map_lo + 1` games.

- If a scheduled Bo3 was actually a Bo5, or a game was forfeited, `build_series_totals`
  may have excluded the series at log time while grading now finds a *different*
  series for the same date/opponent.
- Result: a line graded against the wrong series total, silently.

**Fix direction:** assert `n_maps == hi - lo + 1` on the matched series; if not, leave
ungraded and log a warning (consistent with the existing ambiguity guard).

---

## Priorities

1. Fix edge definition (#1) — unblocks a meaningful Track Record and go-live decision.
2. Close train/serve `position` gap (#5).
3. Backtest on real lines (#4).
4. Harden grading (#6).
5. Re-examine opponent transform (#3) and blend consistency (#2).

## Out of scope (noted earlier, not algorithmic)
- `scipy` missing from `requirements.txt` (import crash on fresh env).
- `lru_cache` model never refreshes as new data lands (`server.py:63`).
- Stray DB artifacts at repo root (`ruvector.db`, `agentdb.rvf`).
