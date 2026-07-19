"""
Series-level player prop prediction for LoL esports.

Clean rebuild of the prediction pipeline:
- data.py     : load Oracle's Elixir CSVs, identify series, build series-level totals
- model.py    : PropsModel - calibrated P(over), expected stat, predictive intervals
- backtest.py : walk-forward backtest measuring calibration on held-out data
"""

from app.props.data import load_games, attach_series, build_series_totals
from app.props.model import PropsModel

__all__ = ["load_games", "attach_series", "build_series_totals", "PropsModel"]
