"""
FastAPI server for the props dashboard.

Serves the model API and (when built) the frontend's static bundle.

Run from backend/:
  venv/bin/uvicorn app.props.server:app --port 8010
"""

import logging
import os
from functools import lru_cache

import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.props.data import (
    attach_series,
    build_series_totals,
    build_team_kill_environment,
    load_games,
)
from app.props.model import MIN_SERIES_FOR_PREDICTION, PropsModel

logger = logging.getLogger(__name__)

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
DATA_DIR = os.environ.get("PROPS_DATA_DIR", os.path.join(_REPO_ROOT, "data"))
LINES_LOG = os.path.join(DATA_DIR, "lines", "lines_log.csv")
LINES_GRADED = os.path.join(DATA_DIR, "lines", "lines_graded.csv")
CALIBRATION_FILE = os.path.join(DATA_DIR, "calibration.json")


def load_calibration() -> tuple[float, float] | None:
    """Read the opt-in Platt correction, if fit_calibration.py has written it."""
    if not os.path.exists(CALIBRATION_FILE):
        return None
    import json

    with open(CALIBRATION_FILE) as f:
        c = json.load(f)
    return (c["a"], c["b"])
FRONTEND_DIST = os.environ.get(
    "PROPS_FRONTEND_DIST", os.path.join(os.path.dirname(__file__), "../../../frontend/dist")
)

app = FastAPI(title="Outscaled Props API")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)


class _State:
    games: pd.DataFrame | None = None
    kill_env: pd.DataFrame | None = None
    player_index: pd.DataFrame | None = None


state = _State()


@app.on_event("startup")
def _load():
    games = load_games(DATA_DIR)
    state.games = attach_series(games)
    state.kill_env = build_team_kill_environment(state.games)
    recent = state.games.sort_values("date").groupby("playername").tail(1)
    state.player_index = recent[["playername", "teamname", "teamid", "position", "league", "date"]]
    logger.info("Server data loaded: %s rows", len(state.games))


@lru_cache(maxsize=12)
def get_model(prop_type: str, lo: int, hi: int) -> PropsModel:
    totals = build_series_totals(state.games, prop_type, (lo, hi))
    return PropsModel(
        totals, kill_env=state.kill_env, opponent_adjust=True,
        calibration=load_calibration(),
    )


def _parse_maps(maps: str) -> tuple[int, int]:
    try:
        lo, hi = (int(x) for x in maps.split("-"))
        return lo, hi
    except ValueError:
        raise HTTPException(400, f"Bad map range: {maps} (expected e.g. 1-2)")


@app.get("/api/players")
def players(q: str = Query("", min_length=0)):
    idx = state.player_index
    if q:
        idx = idx[idx["playername"].str.lower().str.contains(q.lower(), na=False)]
    idx = idx.sort_values("date", ascending=False).head(25)
    return [
        {
            "player": r.playername,
            "team": r.teamname,
            "position": r.position,
            "league": r.league,
            "last_played": str(pd.Timestamp(r.date).date()),
        }
        for r in idx.itertuples(index=False)
    ]


@app.get("/api/predict")
def predict(
    player: str,
    line: float,
    prop: str = "kills",
    maps: str = "1-2",
    opponent_team: str | None = None,
    position: str | None = None,
):
    lo, hi = _parse_maps(maps)
    model = get_model(prop, lo, hi)

    opponent_teamid = None
    if opponent_team:
        match = state.games[
            state.games["teamname"].str.lower() == opponent_team.lower()
        ]
        if not match.empty:
            opponent_teamid = match["teamid"].iloc[-1]

    pred = model.predict(
        player, line, opponent_teamid=opponent_teamid, position=position
    )
    if pred is None:
        raise HTTPException(
            404,
            f"Insufficient history for {player} ({prop} maps {maps}, "
            f"position={position or 'any'}): need {MIN_SERIES_FOR_PREDICTION}+ series",
        )

    # History for the charts, filtered the same way as the prediction sample.
    hist = model._players[player]
    mask = (
        hist.positions == position if position is not None
        else np.ones(len(hist.dates), dtype=bool)
    )
    order = np.argsort(hist.dates[mask])
    dates, totals = hist.dates[mask][order], hist.totals[mask][order]
    history = [
        {"date": str(pd.Timestamp(d).date()), "total": float(t)}
        for d, t in zip(dates, totals)
    ]

    # Probability curve across nearby lines.
    curve = []
    for offset in np.arange(-3.0, 3.5, 0.5):
        alt = line + offset
        if alt < 0.5:
            continue
        p = model.predict(
            player, alt, opponent_teamid=opponent_teamid,
            position=position, n_bootstrap=0,
        )
        if p:
            curve.append({"line": alt, "p_over": round(p.p_over, 4)})

    out = pred.to_dict()
    out["history"] = history
    out["curve"] = curve
    out["prop"] = prop
    out["maps"] = maps
    return out


BOARD_COLS = [
    "player_name", "matched_player", "own_team", "team_ok", "prop_type",
    "map_lo", "map_hi", "line", "payout_over", "payout_under", "book_p_over",
    "game_time", "match_title", "p_over", "expected_stat", "n_series",
    "opponent_factor", "breakeven_over", "breakeven_under", "edge_over",
    "edge_under", "best_side", "best_edge", "edge_vs_book", "snapshot_ts",
]


def _deduped_log() -> pd.DataFrame | None:
    """Line log with one row per line: the most recent snapshot of it."""
    if not os.path.exists(LINES_LOG):
        return None
    log = pd.read_csv(LINES_LOG)
    for col in BOARD_COLS:
        if col not in log.columns:
            log[col] = np.nan
    log = log.sort_values("snapshot_ts").groupby(["source", "line_id"]).tail(1)
    log["game_dt"] = pd.to_datetime(log["game_time"], errors="coerce", utc=True)
    return log


@app.get("/api/board")
def board():
    """Upcoming lines only - past games roll off to the Track Record."""
    log = _deduped_log()
    if log is None or log.empty:
        return {"snapshot_ts": None, "n_lines": 0, "lines": []}
    now = pd.Timestamp.now(tz="UTC")
    upcoming = log[log["game_dt"].isna() | (log["game_dt"] >= now)].copy()
    latest_ts = log["snapshot_ts"].max()
    lines = upcoming[BOARD_COLS].replace({np.nan: None}).to_dict("records")
    lines.sort(key=lambda r: (r["best_edge"] is None, -(r["best_edge"] or 0)))
    return {"snapshot_ts": latest_ts, "n_lines": len(lines), "lines": lines}


PENDING_COLS = [
    "matched_player", "prop_type", "map_lo", "map_hi", "line", "best_side",
    "best_edge", "edge_vs_book", "p_over", "book_p_over", "game_time", "match_title",
]


def _resolved_ids() -> tuple[set, int]:
    """(line_ids that are graded or voided, count of DNP-voided)."""
    if not os.path.exists(LINES_GRADED):
        return set(), 0
    graded = pd.read_csv(LINES_GRADED)
    done_ids = set(graded.loc[graded["outcome_over"].notna(), "line_id"])
    if "voided" in graded.columns:
        void_ids = set(graded.loc[graded["voided"] == True, "line_id"])  # noqa: E712
    else:
        void_ids = set()
    return done_ids | void_ids, len(void_ids)


def _pending() -> list[dict]:
    """Past-game lines still awaiting an outcome (not yet graded or voided)."""
    log = _deduped_log()
    if log is None or log.empty:
        return []
    now = pd.Timestamp.now(tz="UTC")
    past = log[
        (log["game_dt"] < now) & log["matched_player"].notna() & log["p_over"].notna()
    ].copy()
    if past.empty:
        return []
    resolved_ids, _ = _resolved_ids()
    past = past[~past["line_id"].isin(resolved_ids)]
    past = past.sort_values("game_dt", ascending=False).head(100)
    return past[PENDING_COLS].replace({np.nan: None}).to_dict("records")


@app.get("/api/performance")
def performance():
    pending = _pending()
    _, n_voided = _resolved_ids()
    empty = {
        "n_graded": 0, "n_pending": len(pending), "n_voided": n_voided,
        "pending": pending, "buckets": [], "calibration": [], "recent": [],
    }
    if not os.path.exists(LINES_GRADED):
        return empty
    g = pd.read_csv(LINES_GRADED)
    done = g[g["outcome_over"].notna() & g["p_over"].notna()].copy()
    if done.empty:
        return empty

    done = done.sort_values("snapshot_ts").groupby(["source", "line_id"]).tail(1)
    p = done["p_over"].to_numpy(dtype=float)
    y = done["outcome_over"].to_numpy(dtype=float)
    done["side_hit"] = np.where(done["best_side"] == "OVER", y, 1 - y)

    buckets = []
    for lo, hi in [(0.0, 0.03), (0.03, 0.06), (0.06, 0.10), (0.10, 1.0)]:
        sel = done[(done["best_edge"] >= lo) & (done["best_edge"] < hi)]
        if len(sel):
            buckets.append(
                {
                    "bucket": f"{lo:.0%}-{hi:.0%}",
                    "n": int(len(sel)),
                    "hit_rate": round(float(sel["side_hit"].mean()), 3),
                }
            )

    calibration = []
    edges = np.array([0.0, 0.3, 0.4, 0.5, 0.6, 0.7, 1.0])
    for lo, hi in zip(edges[:-1], edges[1:]):
        sel = (p >= lo) & (p < hi)
        if sel.sum() >= 10:
            calibration.append(
                {
                    "bin": f"{lo:.1f}-{hi:.1f}",
                    "predicted": round(float(p[sel].mean()), 3),
                    "actual": round(float(y[sel].mean()), 3),
                    "n": int(sel.sum()),
                }
            )

    recent = done.sort_values("game_time", ascending=False).head(50)
    if "edge_vs_book" not in recent.columns:
        recent["edge_vs_book"] = np.nan
    recent = recent.replace({np.nan: None})
    return {
        "n_graded": int(len(done)),
        "n_pending": len(pending),
        "n_voided": n_voided,
        "pending": pending,
        "brier": round(float(np.mean((p - y) ** 2)), 4),
        "overall_hit_rate": round(float(done["side_hit"].mean()), 3),
        "buckets": buckets,
        "calibration": calibration,
        "recent": recent[
            ["matched_player", "prop_type", "map_lo", "map_hi", "line", "best_side",
             "best_edge", "edge_vs_book", "p_over", "actual_total", "outcome_over",
             "game_time"]
        ].to_dict("records"),
    }


if os.path.isdir(FRONTEND_DIST):
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")
