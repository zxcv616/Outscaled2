"""
Daily market-line logger + paper trader.

Fetches the live Underdog LoL board (or a captured PrizePicks JSON), runs the
props model on every line, and appends everything - line, payouts, model
probability, edge - to data/lines/lines_log.csv. Grading happens later via
grade_lines.py once Oracle's Elixir data covers the match dates.

Usage (from backend/):
  venv/bin/python scripts/log_lines.py                     # fetch Underdog
  venv/bin/python scripts/log_lines.py --pp-file board.json  # PrizePicks capture
"""

import argparse
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
from app.props.lines import (  # noqa: E402
    breakeven_probability,
    fetch_underdog_lol,
    parse_prizepicks_file,
    parse_underdog,
)
from app.props.model import PropsModel  # noqa: E402

logger = logging.getLogger(__name__)

LOG_COLUMNS_KEY = ["snapshot_ts", "source", "line_id"]


def build_player_index(games: pd.DataFrame) -> pd.DataFrame:
    """Latest team/position per player, for name matching and opponent lookup."""
    recent = games.sort_values("date").groupby("playername").tail(1)
    idx = recent[["playername", "teamid", "teamname", "position", "date"]].copy()
    idx["name_lower"] = idx["playername"].str.lower()
    # If two players share a name, keep the most recently active one.
    idx = idx.sort_values("date").groupby("name_lower").tail(1)
    return idx.set_index("name_lower")


def build_team_index(games: pd.DataFrame) -> pd.DataFrame:
    recent = games.sort_values("date").groupby("teamid").tail(1)
    idx = recent[["teamid", "teamname"]].copy()
    idx["team_lower"] = idx["teamname"].str.lower()
    return idx


def _norm_team(s: str) -> str:
    return "".join(ch for ch in s.lower() if ch.isalnum())


def _match_team(name: str, team_index: pd.DataFrame) -> str | None:
    """Match a book's team name to an OE teamid, tolerant of typos, case, and
    tag drift ('Kiwoon DRX' for 'Kiwoom DRX', 'BFX FearX' for 'BNK FEARX').

    Accepts on whole-string similarity, or on a strong match between
    distinctive tokens (len >= 4) so sponsor-tag changes don't break the link.
    """
    from difflib import SequenceMatcher

    generic = {"team", "esports", "gaming", "club", "academy", "youth", "game"}

    def tokens(s: str) -> list[str]:
        return [t for t in s.lower().split() if len(t) >= 4 and t not in generic]

    target = _norm_team(name)
    target_tokens = tokens(name)
    if not target:
        return None
    # Rank by (combined, whole-string) so ties on a shared org token
    # ("FearX" appears in both "BNK FEARX" and "FEARX Youth") resolve to
    # the closest full name.
    best_id, best_key = None, (0.0, 0.0)
    for r in team_index.itertuples(index=False):
        score = SequenceMatcher(None, target, _norm_team(r.teamname)).ratio()
        cand_tokens = tokens(r.teamname)
        token_score = max(
            (
                SequenceMatcher(None, a, b).ratio()
                for a in target_tokens
                for b in cand_tokens
            ),
            default=0.0,
        )
        key = (max(score, 0.9 * token_score), score)
        if key > best_key:
            best_id, best_key = r.teamid, key
    return best_id if best_key[0] >= 0.75 else None


def split_title(match_title: str) -> list[str]:
    if not isinstance(match_title, str) or " vs" not in match_title.lower():
        return []
    parts = [p.strip() for p in match_title.replace("vs.", "vs").split(" vs ")]
    return parts if len(parts) == 2 else []


def resolve_opponent(
    match_title: str, own_teamid: str, team_index: pd.DataFrame
) -> str | None:
    """Map 'Team A vs. Team B' to the OE teamid that is not the player's own."""
    candidates = [_match_team(p, team_index) for p in split_title(match_title)]
    others = [c for c in candidates if c is not None and c != own_teamid]
    return others[0] if len(others) == 1 else None


def team_consistent(
    match_title: str, own_teamid: str, team_index: pd.DataFrame
) -> bool:
    """Does the matched player's current team actually appear in the match?
    Guards against name collisions (same handle, different league)."""
    return own_teamid in {
        _match_team(p, team_index) for p in split_title(match_title)
    }


def main():
    parser = argparse.ArgumentParser(description="Log market lines + model predictions")
    parser.add_argument("--data-dir", default="../data")
    parser.add_argument("--out", default="../data/lines/lines_log.csv")
    parser.add_argument("--pp-file", default=None, help="captured PrizePicks JSON")
    parser.add_argument("--min-edge", type=float, default=0.03,
                        help="edge threshold for the printed picks table")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    board = (
        parse_prizepicks_file(args.pp_file)
        if args.pp_file
        else parse_underdog(fetch_underdog_lol())
    )
    if board.empty:
        logger.warning("No prop lines on the board - nothing to log")
        return

    games = load_games(args.data_dir)
    games = attach_series(games)
    kill_env = build_team_kill_environment(games)
    player_index = build_player_index(games)
    team_index = build_team_index(games)

    # One model per (prop_type, map_range) present on the board.
    models: dict[tuple, PropsModel] = {}
    for prop_type, lo, hi in board[["prop_type", "map_lo", "map_hi"]].drop_duplicates().itertuples(index=False):
        totals = build_series_totals(games, prop_type, (lo, hi))
        models[(prop_type, lo, hi)] = PropsModel(
            totals, kill_env=kill_env, opponent_adjust=True
        )

    records = []
    n_unmatched = 0
    for row in board.itertuples(index=False):
        key = row.player_name.lower()
        rec = row._asdict()
        rec.update(
            {
                "matched_player": None, "own_team": None, "opponent_teamid": None,
                "team_ok": False,
                "p_over": np.nan, "expected_stat": np.nan, "n_series": np.nan,
                "n_effective": np.nan, "opponent_factor": np.nan,
                "breakeven_over": breakeven_probability(row.payout_over),
                "breakeven_under": breakeven_probability(row.payout_under),
                "edge_over": np.nan, "edge_under": np.nan,
                "best_side": None, "best_edge": np.nan,
            }
        )
        if key not in player_index.index:
            n_unmatched += 1
            records.append(rec)
            continue

        info = player_index.loc[key]
        opponent = resolve_opponent(row.match_title, info["teamid"], team_index)
        rec["team_ok"] = team_consistent(row.match_title, info["teamid"], team_index)
        model = models[(row.prop_type, row.map_lo, row.map_hi)]
        pred = model.predict(
            info["playername"], row.line, opponent_teamid=opponent, n_bootstrap=0
        )
        if pred is None:
            records.append(rec)
            continue

        edge_over = pred.p_over - rec["breakeven_over"]
        edge_under = (1.0 - pred.p_over) - rec["breakeven_under"]
        best_side = "OVER" if edge_over >= edge_under else "UNDER"
        rec.update(
            {
                "matched_player": info["playername"],
                "own_team": info["teamname"],
                "opponent_teamid": opponent,
                "p_over": round(pred.p_over, 4),
                "expected_stat": round(pred.expected_stat, 2),
                "n_series": pred.n_series,
                "n_effective": round(pred.n_effective, 1),
                "opponent_factor": round(pred.opponent_factor, 3),
                "edge_over": round(edge_over, 4),
                "edge_under": round(edge_under, 4),
                "best_side": best_side,
                "best_edge": round(max(edge_over, edge_under), 4),
            }
        )
        records.append(rec)

    out = pd.DataFrame(records)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    # Append via read+concat so a schema change (new column) can never
    # corrupt the log; missing columns in old rows become NaN.
    if os.path.exists(args.out):
        existing = pd.read_csv(args.out)
        out = pd.concat([existing, out], ignore_index=True)
    out.to_csv(args.out, index=False)
    logger.info(
        "Logged %s new lines (%s matched to model, %s unmatched) -> %s (%s total)",
        len(records),
        pd.DataFrame(records)["matched_player"].notna().sum(),
        n_unmatched, args.out, len(out),
    )

    n_team_bad = int((out["matched_player"].notna() & ~out["team_ok"]).sum())
    if n_team_bad:
        logger.warning(
            "%s matched lines failed the team-consistency check (possible name "
            "collision) - excluded from picks", n_team_bad,
        )
    picks = out[
        (out["best_edge"] >= args.min_edge)
        & out["matched_player"].notna()
        & out["team_ok"]
    ]
    picks = picks.sort_values("best_edge", ascending=False)
    if picks.empty:
        print(f"\nNo picks with edge >= {args.min_edge:.0%} on this board.")
        return

    print(f"\n{'=' * 100}")
    print(f"PAPER-TRADE PICKS (edge >= {args.min_edge:.0%}) - {len(picks)} of {len(out)} lines")
    print(f"{'=' * 100}")
    for p in picks.itertuples(index=False):
        maps = f"{p.map_lo}-{p.map_hi}"
        p_side = p.p_over if p.best_side == "OVER" else 1 - p.p_over
        be = p.breakeven_over if p.best_side == "OVER" else p.breakeven_under
        print(
            f"  {p.best_side:<5} {p.matched_player:<14} {p.prop_type:<8} maps {maps} "
            f"line {p.line:<5} | model p={p_side:.3f} vs breakeven {be:.3f} "
            f"(edge {p.best_edge:+.1%}) | exp {p.expected_stat} n={p.n_series:.0f} "
            f"oppf={p.opponent_factor} | {p.match_title}"
        )


if __name__ == "__main__":
    main()
