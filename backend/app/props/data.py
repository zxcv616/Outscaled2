"""
Data loading and series identification for Oracle's Elixir match data.

Series identification strategy (validated at ~98% clean game sequences):
  games between the same two teams on the same calendar day form one series;
  a reset in the game number (e.g. 1,2,3 then 1 again) splits a second series
  played by the same teams on the same day (rare: tiebreakers, double-headers).

Betting semantics (see Betting_Logic.md):
  "Maps 1-2 kills" = SUM of kills across game 1 and game 2 of a series.
  One data point per player per series. Sample size counts SERIES, not maps.
"""

import glob
import logging
import os

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

PLAYER_COLS = [
    "gameid", "datacompleteness", "league", "split", "playoffs", "date",
    "game", "patch", "position", "playername", "playerid", "teamname",
    "teamid", "kills", "deaths", "assists", "teamkills",
]

SUPPORTED_PROPS = ("kills", "assists", "deaths")


def load_games(data_dir: str) -> pd.DataFrame:
    """Load all Oracle's Elixir CSVs in data_dir into one player-level frame.

    Drops team aggregate rows and rows missing the fields needed for
    series identification or stat aggregation.
    """
    files = sorted(glob.glob(os.path.join(data_dir, "*LoL_esports_match_data*.csv")))
    if not files:
        raise FileNotFoundError(f"No Oracle's Elixir CSVs found in {data_dir}")

    frames = []
    for path in files:
        df = pd.read_csv(path, usecols=PLAYER_COLS, low_memory=False)
        frames.append(df)
        logger.info("Loaded %s rows from %s", len(df), os.path.basename(path))

    games = pd.concat(frames, ignore_index=True)
    games = games[games["position"] != "team"].copy()

    games["date"] = pd.to_datetime(games["date"], errors="coerce")
    games["game"] = pd.to_numeric(games["game"], errors="coerce")
    for col in SUPPORTED_PROPS:
        games[col] = pd.to_numeric(games[col], errors="coerce")
    games["teamkills"] = pd.to_numeric(games["teamkills"], errors="coerce")

    games = games.dropna(
        subset=["date", "game", "gameid", "playername", "teamid", "kills", "assists"]
    )
    games["game"] = games["game"].astype(int)
    logger.info("Total player-game rows after cleaning: %s", len(games))
    return games


def attach_series(games: pd.DataFrame) -> pd.DataFrame:
    """Assign a series_id and opponent teamid to every player-game row."""
    # One row per game: start time, game number, and the (sorted) team pair.
    game_teams = (
        games.groupby("gameid")
        .agg(date=("date", "min"), game_num=("game", "first"))
        .reset_index()
    )
    pair = (
        games.groupby("gameid")["teamid"]
        .agg(lambda t: tuple(sorted(pd.unique(t))))
        .rename("team_pair")
    )
    game_teams = game_teams.merge(pair, on="gameid")

    # Games with anything other than exactly 2 teams are malformed - drop them.
    valid = game_teams["team_pair"].str.len() == 2
    if (~valid).any():
        logger.warning("Dropping %s games without exactly 2 teams", (~valid).sum())
    game_teams = game_teams[valid].copy()

    game_teams["day"] = game_teams["date"].dt.strftime("%Y-%m-%d")
    game_teams = game_teams.sort_values("date").reset_index(drop=True)

    # Split same-day/same-pair groups whenever the game number does not increase.
    series_ids = []
    for (day, team_pair), grp in game_teams.groupby(["day", "team_pair"], sort=False):
        seq = 0
        prev_game = 0
        base = f"{day}|{team_pair[0]}|{team_pair[1]}"
        for _, row in grp.sort_values("date").iterrows():
            if row["game_num"] <= prev_game:
                seq += 1
            prev_game = row["game_num"]
            series_ids.append((row["gameid"], f"{base}|s{seq}"))

    sid = pd.DataFrame(series_ids, columns=["gameid", "series_id"])
    game_meta = game_teams.merge(sid, on="gameid")[["gameid", "series_id", "team_pair"]]

    out = games.merge(game_meta, on="gameid", how="inner")
    out["opponent_teamid"] = [
        p[1] if t == p[0] else p[0] for t, p in zip(out["teamid"], out["team_pair"])
    ]
    out = out.drop(columns=["team_pair"])

    n_series = out["series_id"].nunique()
    sizes = out.groupby("series_id")["game"].nunique()
    logger.info(
        "Identified %s series (%.1f%% multi-game)",
        n_series, 100.0 * (sizes > 1).mean(),
    )
    return out


def build_series_totals(
    games: pd.DataFrame, prop_type: str, map_range: tuple[int, int]
) -> pd.DataFrame:
    """Aggregate per-player combined totals for a map range, one row per series.

    A series only qualifies if the player has a row for EVERY map in the
    range (a "Maps 1-2" bet cannot exist for a Bo1, and a mid-series sub
    would corrupt the total).
    """
    if prop_type not in SUPPORTED_PROPS:
        raise ValueError(f"prop_type must be one of {SUPPORTED_PROPS}")
    lo, hi = map_range
    n_required = hi - lo + 1

    in_range = games[(games["game"] >= lo) & (games["game"] <= hi)]

    totals = (
        in_range.groupby(["playername", "series_id"])
        .agg(
            total=(prop_type, "sum"),
            n_maps=("gameid", "nunique"),
            date=("date", "min"),
            league=("league", "first"),
            position=("position", lambda p: p.mode().iat[0]),
            teamid=("teamid", "first"),
            opponent_teamid=("opponent_teamid", "first"),
            complete=("datacompleteness", lambda c: (c == "complete").all()),
        )
        .reset_index()
    )
    totals = totals[totals["n_maps"] == n_required].copy()
    totals = totals.sort_values("date").reset_index(drop=True)
    logger.info(
        "Built %s player-series totals for %s maps %s-%s",
        len(totals), prop_type, lo, hi,
    )
    return totals


def build_team_kill_environment(games: pd.DataFrame) -> pd.DataFrame:
    """Per team per game: total kills the team ALLOWED (opponent teamkills).

    Used for the opponent-adjustment feature: a player facing a team that
    bleeds kills should see a higher expected kill environment.
    Returns one row per (teamid, gameid) sorted by date.
    """
    per_team = (
        games.groupby(["gameid", "teamid"])
        .agg(date=("date", "min"), teamkills=("teamkills", "first"))
        .reset_index()
    )
    # Pair each team-game with the opposing team's kills in the same game.
    merged = per_team.merge(per_team, on="gameid", suffixes=("", "_opp"))
    merged = merged[merged["teamid"] != merged["teamid_opp"]]
    env = merged[["teamid", "gameid", "date", "teamkills_opp"]].rename(
        columns={"teamkills_opp": "kills_allowed"}
    )
    env = env.dropna(subset=["kills_allowed"]).sort_values("date").reset_index(drop=True)
    return env
