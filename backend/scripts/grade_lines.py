"""
Grade previously logged market lines against actual results.

Reads data/lines/lines_log.csv, looks up each player's actual combined total
for the matching series in the Oracle's Elixir data, and writes
data/lines/lines_graded.csv plus a running paper-trade report.

Notes:
- Oracle's Elixir CSVs must be refreshed (re-downloaded) to cover the match
  dates being graded; ungraded rows are kept and retried next run.
- A line is matched to the player's first series within +/-1 day of the
  scheduled game time.
"""

import argparse
import logging
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from app.props.data import attach_series, build_series_totals, load_games  # noqa: E402

logger = logging.getLogger(__name__)


def grade(lines: pd.DataFrame, games: pd.DataFrame) -> pd.DataFrame:
    """Attach actual totals/outcomes where a matching series exists."""
    lines = lines.copy()
    lines["game_time"] = pd.to_datetime(lines["game_time"], errors="coerce", utc=True)
    lines["actual_total"] = np.nan
    lines["outcome_over"] = np.nan

    for (prop_type, lo, hi), grp in lines.groupby(["prop_type", "map_lo", "map_hi"]):
        totals = build_series_totals(games, prop_type, (int(lo), int(hi)))
        totals = totals.assign(name_lower=totals["playername"].str.lower())
        by_player = {n: g for n, g in totals.groupby("name_lower")}

        for i in grp.index:
            row = lines.loc[i]
            if pd.isna(row["game_time"]) or pd.isna(row["matched_player"]):
                continue
            hist = by_player.get(str(row["matched_player"]).lower())
            if hist is None:
                continue
            target_day = row["game_time"].tz_localize(None)
            delta = (hist["date"] - target_day).abs()
            near = hist[delta <= pd.Timedelta(days=1)]
            if near.empty:
                continue
            # A team can play several series on one day: disambiguate by the
            # opponent resolved at log time. Never guess between candidates.
            if len(near) > 1:
                opp = row.get("opponent_teamid")
                if pd.notna(opp):
                    near = near[near["opponent_teamid"] == opp]
                if len(near) != 1:
                    logger.warning(
                        "Ambiguous series for %s on %s (%s candidates) - left ungraded",
                        row["matched_player"], target_day.date(), len(near),
                    )
                    continue
            match = near.loc[delta[near.index].idxmin()]
            lines.loc[i, "actual_total"] = match["total"]
            lines.loc[i, "outcome_over"] = float(match["total"] > row["line"])
    return lines


def report(graded: pd.DataFrame, min_edge: float) -> None:
    done = graded[graded["outcome_over"].notna() & graded["p_over"].notna()].copy()
    if done.empty:
        print("\nNo gradable lines yet - refresh the Oracle's Elixir CSVs once the "
              "matches are in the data, then rerun.")
        return

    # De-duplicate: keep the last snapshot before each game per line_id.
    done = done.sort_values("snapshot_ts").groupby(["source", "line_id"]).tail(1)

    p = done["p_over"].to_numpy(dtype=float)
    y = done["outcome_over"].to_numpy(dtype=float)
    brier = float(np.mean((p - y) ** 2))
    print(f"\n{'=' * 70}\nPAPER-TRADE REPORT ({len(done)} graded lines)\n{'=' * 70}")
    print(f"Brier vs market lines: {brier:.4f} (coin flip 0.25)")
    print(f"Actual over rate: {y.mean():.3f} | mean predicted: {p.mean():.3f}")

    bets = done[done["best_edge"] >= min_edge].copy()
    if bets.empty:
        print(f"No graded picks above edge threshold {min_edge:.0%} yet.")
        return
    bets["side_hit"] = np.where(
        bets["best_side"] == "OVER", bets["outcome_over"], 1 - bets["outcome_over"]
    )
    print(f"\nPicks with edge >= {min_edge:.0%}: n={len(bets)}  "
          f"hit rate={bets['side_hit'].mean():.1%}")
    for lo, hi in [(0.03, 0.06), (0.06, 0.10), (0.10, 1.0)]:
        sel = bets[(bets["best_edge"] >= lo) & (bets["best_edge"] < hi)]
        if len(sel) >= 5:
            print(f"  edge {lo:.0%}-{hi:.0%}: n={len(sel)}  "
                  f"hit rate={sel['side_hit'].mean():.1%}")


def main():
    parser = argparse.ArgumentParser(description="Grade logged lines vs actual results")
    parser.add_argument("--data-dir", default="../data")
    parser.add_argument("--log", default="../data/lines/lines_log.csv")
    parser.add_argument("--out", default="../data/lines/lines_graded.csv")
    parser.add_argument("--min-edge", type=float, default=0.03)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    if not os.path.exists(args.log):
        print(f"No line log at {args.log} - run log_lines.py first.")
        return

    lines = pd.read_csv(args.log)
    games = load_games(args.data_dir)
    games = attach_series(games)

    graded = grade(lines, games)
    graded.to_csv(args.out, index=False)
    n_graded = int(graded["outcome_over"].notna().sum())
    logger.info("Graded %s of %s logged lines -> %s", n_graded, len(graded), args.out)
    report(graded, args.min_edge)


if __name__ == "__main__":
    main()
