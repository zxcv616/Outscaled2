"""
Market line ingestion for paper-trading the props model.

Primary source: Underdog Fantasy's public pickem board (no auth required,
includes per-side payout multipliers). PrizePicks sits behind DataDome bot
protection, so direct fetch is not reliable; a JSON file captured from a
browser session can be ingested with parse_prizepicks_file().

Break-even math: entries are parlays. We normalize per-leg using a standard
2-pick power play (3.0x for two 1.0x legs): a leg with side multiplier m
needs p >= 1 / (sqrt(3) * m) to break even. This is an approximation - the
exact threshold depends on entry composition - but it ranks picks correctly.
"""

import json
import logging
import re
import urllib.request
from datetime import datetime, timezone

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

UNDERDOG_URL = "https://api.underdogfantasy.com/beta/v6/over_under_lines?sport_id=LOL"
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
)

# "Kills on Map 1" / "Assists on Maps 1+2" etc. -> (prop_type, map_range)
_STAT_RE = re.compile(
    r"^(?P<stat>Kills|Assists|Deaths)\s+on\s+Maps?\s+(?P<maps>[\d+]+)$", re.IGNORECASE
)


def parse_stat(display_stat: str) -> tuple[str, tuple[int, int]] | None:
    m = _STAT_RE.match(display_stat.strip())
    if not m:
        return None
    prop_type = m.group("stat").lower()
    nums = [int(x) for x in m.group("maps").split("+")]
    return prop_type, (min(nums), max(nums))


def fetch_underdog_lol(url: str = UNDERDOG_URL) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def parse_underdog(raw: dict, snapshot_ts: str | None = None) -> pd.DataFrame:
    """Flatten the Underdog board into one row per (line, side-pair)."""
    snapshot_ts = snapshot_ts or datetime.now(timezone.utc).isoformat(timespec="seconds")
    players = {p["id"]: p for p in raw.get("players", [])}
    apps = {a["id"]: a for a in raw.get("appearances", [])}
    games = {g["id"]: g for g in raw.get("games", [])}

    rows = []
    for line in raw.get("over_under_lines", []):
        ou = line.get("over_under", {})
        stat = ou.get("appearance_stat", {})
        parsed = parse_stat(stat.get("display_stat", ""))
        if parsed is None:
            continue
        prop_type, map_range = parsed

        app = apps.get(stat.get("appearance_id"), {})
        player = players.get(app.get("player_id"), {})
        name = " ".join(
            x for x in [player.get("first_name"), player.get("last_name")] if x
        ).strip()
        if not name:
            continue

        game = games.get(app.get("match_id"), {})
        payout = {"higher": np.nan, "lower": np.nan}
        for opt in line.get("options", []):
            choice = opt.get("choice")
            if choice in payout:
                payout[choice] = float(opt.get("payout_multiplier") or np.nan)

        rows.append(
            {
                "snapshot_ts": snapshot_ts,
                "source": "underdog",
                "line_id": line.get("id"),
                "player_name": name,
                "prop_type": prop_type,
                "map_lo": map_range[0],
                "map_hi": map_range[1],
                "line": float(line.get("stat_value")),
                "payout_over": payout["higher"],
                "payout_under": payout["lower"],
                "game_time": game.get("scheduled_at"),
                "match_title": game.get("title"),
                "status": line.get("status"),
            }
        )
    df = pd.DataFrame(rows)
    logger.info("Parsed %s prop lines from Underdog board", len(df))
    return df


def parse_prizepicks_file(path: str, snapshot_ts: str | None = None) -> pd.DataFrame:
    """Ingest a PrizePicks /projections JSON captured from a browser session."""
    snapshot_ts = snapshot_ts or datetime.now(timezone.utc).isoformat(timespec="seconds")
    with open(path) as f:
        raw = json.load(f)

    included = {
        (item["type"], item["id"]): item for item in raw.get("included", [])
    }
    rows = []
    for proj in raw.get("data", []):
        if proj.get("type") != "projection":
            continue
        attrs = proj.get("attributes", {})
        stat_type = attrs.get("stat_type", "")
        # PrizePicks style: "Kills on Maps 1+2" / "MAPS 1-2 Kills"
        parsed = parse_stat(stat_type)
        if parsed is None:
            m = re.match(r"MAPS?\s+(\d)-(\d)\s+(Kills|Assists|Deaths)", stat_type, re.I)
            if not m:
                continue
            parsed = (m.group(3).lower(), (int(m.group(1)), int(m.group(2))))
        prop_type, map_range = parsed

        player_rel = proj.get("relationships", {}).get("new_player", {}).get("data", {})
        player = included.get(("new_player", player_rel.get("id")), {})
        name = player.get("attributes", {}).get("name", "")
        if not name:
            continue

        rows.append(
            {
                "snapshot_ts": snapshot_ts,
                "source": "prizepicks",
                "line_id": proj.get("id"),
                "player_name": name,
                "prop_type": prop_type,
                "map_lo": map_range[0],
                "map_hi": map_range[1],
                "line": float(attrs.get("line_score")),
                "payout_over": 1.0,  # standard flex/power legs
                "payout_under": 1.0,
                "game_time": attrs.get("start_time"),
                "match_title": attrs.get("description", ""),
                "status": attrs.get("status", ""),
            }
        )
    df = pd.DataFrame(rows)
    logger.info("Parsed %s prop lines from PrizePicks capture", len(df))
    return df


def breakeven_probability(payout_multiplier: float) -> float:
    """Per-leg break-even under the standard 2-pick 3x normalization."""
    if not np.isfinite(payout_multiplier) or payout_multiplier <= 0:
        return np.nan
    return float(np.clip(1.0 / (np.sqrt(3.0) * payout_multiplier), 0.0, 1.0))
