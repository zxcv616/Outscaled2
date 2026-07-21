"""
Fit the Platt recalibration that corrects the model's residual under-lean.

Runs a walk-forward over 2026, fits (a, b) on the first months and validates
on the held-out remainder, prints the before/after metrics, and — unless
--dry-run — writes data/calibration.json. The server and log_lines.py load
that file if it exists, so calibration is opt-in: it only takes effect once
you run this script.

Usage (from backend/):
  venv/bin/python scripts/fit_calibration.py            # fit + write
  venv/bin/python scripts/fit_calibration.py --dry-run  # report only
"""

import argparse
import json
import logging
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from app.props.data import (  # noqa: E402
    attach_series,
    build_series_totals,
    build_team_kill_environment,
    load_games,
)
from app.props.model import PropsModel, fit_calibration  # noqa: E402

logger = logging.getLogger(__name__)


def _collect(model, totals, eval_start):
    def snap(x):
        return float(np.floor(x) + 0.5)

    rows = []
    for t in totals[totals["date"] >= eval_start].itertuples(index=False):
        as_of = pd.Timestamp(t.date)
        qs = model.history_quantiles(
            t.playername, (0.35, 0.5, 0.65), as_of=as_of, position=t.position
        )
        if qs is None:
            continue
        for line in sorted({snap(q) for q in qs}):
            p = model.predict(
                t.playername, line, as_of=as_of,
                opponent_teamid=t.opponent_teamid, position=t.position,
                n_bootstrap=0,
            )
            if p:
                rows.append((as_of, p.components["p_raw"], int(t.total > line)))
    return pd.DataFrame(rows, columns=["date", "p", "y"])


def _metrics(p, y):
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return {
        "brier": round(float(np.mean((p - y) ** 2)), 4),
        "log_loss": round(float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p))), 4),
        "bias": round(float(p.mean() - y.mean()), 3),
        "tail_gap": round(float(p[p < 0.35].mean() - y[p < 0.35].mean()), 3),
    }


def main():
    ap = argparse.ArgumentParser(description="Fit the Platt recalibration")
    ap.add_argument("--data-dir", default="../data")
    ap.add_argument("--prop", default="kills")
    ap.add_argument("--maps", default="1-2")
    ap.add_argument("--eval-start", default="2026-01-01")
    ap.add_argument("--split", default="2026-05-01", help="train before / test after")
    ap.add_argument("--out", default="../data/calibration.json")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    lo, hi = (int(x) for x in args.maps.split("-"))

    games = attach_series(load_games(args.data_dir))
    env = build_team_kill_environment(games)
    totals = build_series_totals(games, args.prop, (lo, hi))
    model = PropsModel(totals, kill_env=env, opponent_adjust=True)

    df = _collect(model, totals, args.eval_start)
    tr, te = df[df["date"] < args.split], df[df["date"] >= args.split]
    logger.info("collected %s predictions (train %s / test %s)", len(df), len(tr), len(te))

    a, b = fit_calibration(tr["p"].to_numpy(), tr["y"].to_numpy())

    logit = np.log(np.clip(te["p"], 1e-6, 1 - 1e-6) / (1 - np.clip(te["p"], 1e-6, 1 - 1e-6)))
    cal = 1.0 / (1.0 + np.exp(-(a * logit + b)))
    raw_m = _metrics(te["p"].to_numpy(), te["y"].to_numpy())
    cal_m = _metrics(cal.to_numpy(), te["y"].to_numpy())

    print(f"\nHeld-out ({args.split}+) validation, {args.prop} maps {args.maps}:")
    print(f"  {'':10} {'brier':>7} {'logloss':>8} {'bias':>7} {'tail_gap':>8}")
    for tag, mvals in (("raw", raw_m), ("calibrated", cal_m)):
        print(f"  {tag:10} {mvals['brier']:>7} {mvals['log_loss']:>8} "
              f"{mvals['bias']:>+7} {mvals['tail_gap']:>+8}")

    # Refit on ALL data for production use (predicting strictly-future games).
    a_full, b_full = fit_calibration(df["p"].to_numpy(), df["y"].to_numpy())
    payload = {
        "a": round(a_full, 5), "b": round(b_full, 5),
        "fit_on": f"{args.prop}_maps_{args.maps}", "n": int(len(df)),
        "validation": {"raw": raw_m, "calibrated": cal_m},
    }
    if args.dry_run:
        print(f"\n[dry-run] would write {payload}")
        return
    with open(args.out, "w") as f:
        json.dump(payload, f, indent=2)
    print(f"\nWrote calibration (a={a_full:.4f}, b={b_full:.4f}) -> {args.out}")
    print("Server and log_lines.py will apply it on their next run.")


if __name__ == "__main__":
    main()
