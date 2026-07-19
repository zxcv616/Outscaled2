"""
CLI for series-level prop predictions.

Usage (from backend/):
  venv/bin/python scripts/props_predict.py --player Faker --prop kills --line 5.5
  venv/bin/python scripts/props_predict.py --player Chovy --prop assists \
      --line 9.5 --maps 1-2 --opponent-team "T1" --position mid

Note: side_probability is the probability of the printed prediction side.
On near-even payout platforms you generally need ~0.55+ to clear the vig.
"""

import argparse
import json
import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.props.data import (  # noqa: E402
    attach_series,
    build_series_totals,
    build_team_kill_environment,
    load_games,
)
from app.props.model import PropsModel  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description="Series-level prop prediction")
    parser.add_argument("--data-dir", default="../data")
    parser.add_argument("--player", required=True)
    parser.add_argument("--prop", default="kills", choices=["kills", "assists", "deaths"])
    parser.add_argument("--line", type=float, required=True)
    parser.add_argument("--maps", default="1-2", help="map range, e.g. 1-1 or 1-2")
    parser.add_argument("--position", default=None, help="restrict history to a role")
    parser.add_argument("--opponent-team", default=None, help="opponent team name")
    args = parser.parse_args()

    logging.basicConfig(level=logging.WARNING)
    lo, hi = (int(x) for x in args.maps.split("-"))

    games = load_games(args.data_dir)
    games = attach_series(games)
    totals = build_series_totals(games, args.prop, (lo, hi))
    kill_env = build_team_kill_environment(games)

    opponent_teamid = None
    if args.opponent_team:
        match = games[games["teamname"].str.lower() == args.opponent_team.lower()]
        if match.empty:
            print(f"Unknown team: {args.opponent_team}", file=sys.stderr)
            sys.exit(1)
        opponent_teamid = match["teamid"].iloc[-1]

    model = PropsModel(totals, kill_env=kill_env, opponent_adjust=opponent_teamid is not None)
    pred = model.predict(
        args.player,
        args.line,
        opponent_teamid=opponent_teamid,
        position=args.position,
    )
    if pred is None:
        print(
            f"Insufficient history for {args.player} "
            f"({args.prop} maps {lo}-{hi}, position={args.position})",
            file=sys.stderr,
        )
        sys.exit(1)

    print(json.dumps(pred.to_dict(), indent=2))


if __name__ == "__main__":
    main()
