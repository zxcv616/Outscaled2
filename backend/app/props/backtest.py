"""
Walk-forward backtest for the props model.

For every player-series in the evaluation window, we predict P(over) using
ONLY data strictly before that series started, against a grid of synthetic
lines placed at the player's prior 35th/50th/65th weighted percentiles
(rounded to x.5, mimicking where books hang lines). The outcome is graded
against the actual combined total.

Reported metrics:
  - Brier score / log loss (lower is better; 0.25 / 0.693 = coin flip)
  - Calibration table: predicted probability vs. realized frequency
  - Threshold table: hit rate when betting only above a side-probability cutoff

A reference "naive_normal" variant (unweighted mean/std + normal tail, i.e.
what the old pipeline implicitly did) is included for comparison.
"""

import argparse
import json
import logging
import os

import numpy as np
import pandas as pd
from scipy import stats

from app.props.data import (
    attach_series,
    build_series_totals,
    build_team_kill_environment,
    load_games,
)
from app.props.model import MIN_SERIES_FOR_PREDICTION, PropsModel

logger = logging.getLogger(__name__)

LINE_QUANTILES = (0.35, 0.50, 0.65)


def _snap_to_half(x: float) -> float:
    """Snap a value to the nearest x.5 so bets never push."""
    return float(np.floor(x) + 0.5)


def _naive_normal_p_over(totals: np.ndarray, line: float) -> float:
    """Reference model: unweighted mean/std, normal tail probability."""
    mean = totals.mean()
    std = totals.std(ddof=1)
    if std < 1e-6:
        return 0.99 if mean > line else 0.01
    return float(np.clip(stats.norm.sf(line, loc=mean, scale=std), 0.01, 0.99))


def run_backtest(
    series_totals: pd.DataFrame,
    kill_env: pd.DataFrame,
    eval_start: str,
    half_life_days: float = 120.0,
) -> pd.DataFrame:
    """Returns one row per (player-series, line, variant) with p_over and outcome."""
    eval_start_ts = pd.Timestamp(eval_start)

    base = PropsModel(series_totals, half_life_days=half_life_days)
    opp = PropsModel(
        series_totals,
        kill_env=kill_env,
        half_life_days=half_life_days,
        opponent_adjust=True,
    )

    targets = series_totals[series_totals["date"] >= eval_start_ts]
    logger.info("Evaluating %s player-series targets", len(targets))

    rows = []
    for tgt in targets.itertuples(index=False):
        as_of = pd.Timestamp(tgt.date)
        qs = base.history_quantiles(
            tgt.playername, LINE_QUANTILES, as_of=as_of, position=tgt.position
        )
        if qs is None:
            continue
        lines = sorted({_snap_to_half(q) for q in qs})

        # Naive reference uses the same history window, unweighted.
        hist = base._players[tgt.playername]
        mask = (hist.dates < np.datetime64(as_of.to_datetime64())) & (
            hist.positions == tgt.position
        )
        naive_totals = hist.totals[mask]

        for line in lines:
            outcome = int(tgt.total > line)
            for variant, model in (("empirical_nb", base), ("empirical_nb_opp", opp)):
                pred = model.predict(
                    tgt.playername,
                    line,
                    as_of=as_of,
                    opponent_teamid=tgt.opponent_teamid,
                    position=tgt.position,
                    n_bootstrap=0,
                )
                if pred is None:
                    continue
                rows.append(
                    {
                        "variant": variant,
                        "player": tgt.playername,
                        "date": tgt.date,
                        "league": tgt.league,
                        "line": line,
                        "p_over": pred.p_over,
                        "outcome": outcome,
                        "n_series": pred.n_series,
                    }
                )
            if len(naive_totals) >= MIN_SERIES_FOR_PREDICTION:
                rows.append(
                    {
                        "variant": "naive_normal",
                        "player": tgt.playername,
                        "date": tgt.date,
                        "league": tgt.league,
                        "line": line,
                        "p_over": _naive_normal_p_over(naive_totals, line),
                        "outcome": outcome,
                        "n_series": len(naive_totals),
                    }
                )

    return pd.DataFrame(rows)


def summarize(results: pd.DataFrame) -> dict:
    """Per-variant Brier/log-loss, calibration table, and threshold hit rates."""
    summary = {}
    for variant, grp in results.groupby("variant"):
        p = grp["p_over"].to_numpy()
        y = grp["outcome"].to_numpy()
        p_clip = np.clip(p, 1e-6, 1 - 1e-6)

        brier = float(np.mean(np.square(p - y)))
        logloss = float(-np.mean(y * np.log(p_clip) + (1 - y) * np.log(1 - p_clip)))

        bins = np.array([0.0, 0.3, 0.4, 0.45, 0.5, 0.55, 0.6, 0.7, 1.0])
        calibration = []
        for lo, hi in zip(bins[:-1], bins[1:]):
            in_bin = (p >= lo) & (p < hi)
            if in_bin.sum() >= 30:
                calibration.append(
                    {
                        "bin": f"{lo:.2f}-{hi:.2f}",
                        "n": int(in_bin.sum()),
                        "predicted": round(float(p[in_bin].mean()), 3),
                        "actual": round(float(y[in_bin].mean()), 3),
                    }
                )

        side_prob = np.maximum(p, 1 - p)
        side_hit = np.where(p >= 0.5, y, 1 - y)
        thresholds = []
        for t in (0.55, 0.60, 0.65, 0.70):
            sel = side_prob >= t
            if sel.sum() > 0:
                thresholds.append(
                    {
                        "min_side_prob": t,
                        "n_bets": int(sel.sum()),
                        "hit_rate": round(float(side_hit[sel].mean()), 3),
                    }
                )

        summary[variant] = {
            "n_predictions": int(len(grp)),
            "base_over_rate": round(float(y.mean()), 3),
            "brier": round(brier, 4),
            "brier_coinflip": 0.25,
            "log_loss": round(logloss, 4),
            "log_loss_coinflip": 0.6931,
            "calibration": calibration,
            "thresholds": thresholds,
        }
    return summary


def main():
    parser = argparse.ArgumentParser(description="Walk-forward props backtest")
    parser.add_argument("--data-dir", default="data")
    parser.add_argument("--eval-start", default="2026-01-01")
    parser.add_argument("--out-dir", default="results/props_backtest")
    parser.add_argument(
        "--configs",
        default="kills:1-2,kills:1-1,assists:1-2",
        help="comma-separated prop:lo-hi entries",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    os.makedirs(args.out_dir, exist_ok=True)

    games = load_games(args.data_dir)
    games = attach_series(games)
    kill_env = build_team_kill_environment(games)

    all_summaries = {}
    for entry in args.configs.split(","):
        prop_type, rng = entry.split(":")
        lo, hi = (int(x) for x in rng.split("-"))
        label = f"{prop_type}_maps_{lo}_{hi}"
        logger.info("=== Backtesting %s ===", label)

        totals = build_series_totals(games, prop_type, (lo, hi))
        results = run_backtest(totals, kill_env, args.eval_start)
        results.to_csv(os.path.join(args.out_dir, f"{label}_predictions.csv"), index=False)

        all_summaries[label] = summarize(results)

    summary_path = os.path.join(args.out_dir, "summary.json")
    with open(summary_path, "w") as f:
        json.dump(all_summaries, f, indent=2)

    for label, variants in all_summaries.items():
        print(f"\n{'=' * 60}\n{label}\n{'=' * 60}")
        for variant, s in variants.items():
            print(
                f"\n  {variant}: n={s['n_predictions']}  "
                f"brier={s['brier']} (coin flip 0.25)  "
                f"log_loss={s['log_loss']} (coin flip 0.693)"
            )
            for row in s["calibration"]:
                print(
                    f"    p in {row['bin']}: predicted {row['predicted']:.3f} "
                    f"vs actual {row['actual']:.3f}  (n={row['n']})"
                )
            for row in s["thresholds"]:
                print(
                    f"    side_prob >= {row['min_side_prob']}: "
                    f"{row['hit_rate']:.1%} hit rate over {row['n_bets']} bets"
                )
    print(f"\nFull summary written to {summary_path}")


if __name__ == "__main__":
    main()
