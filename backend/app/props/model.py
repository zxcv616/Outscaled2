"""
Series-level prop prediction model.

Core idea: the honest primitive for "Maps 1-2 kills 8.5" is the player's
distribution of series-level combined totals. We estimate P(total > line) by
blending:

  1. a recency-weighted EMPIRICAL distribution of the player's series totals
     (exact in the middle of the distribution, noisy in the tails), and
  2. a NEGATIVE BINOMIAL fit to the weighted mean/variance (smooth tails,
     correct for overdispersed count data - kills/assists are counts whose
     variance exceeds the mean).

The blend weight grows with effective sample size, so small samples lean on
the parametric model and large samples lean on the player's actual history.

Optional opponent adjustment scales the expected kill environment by how many
kills the upcoming opponent has been allowing relative to the global average
(dampened and clipped - matchup matters, but player identity matters more).

All quantities honor an `as_of` cutoff so backtests are leak-free.
"""

import logging
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from scipy import stats

logger = logging.getLogger(__name__)

MIN_SERIES_FOR_PREDICTION = 8


@dataclass
class PlayerHistory:
    dates: np.ndarray  # datetime64[ns], ascending
    totals: np.ndarray  # float
    positions: np.ndarray  # str


@dataclass
class Prediction:
    player: str
    line: float
    p_over: float
    prediction: str  # "OVER" | "UNDER"
    expected_stat: float
    predictive_interval: tuple[float, float]  # 5th-95th pct of outcome dist
    expected_stat_ci: tuple[float, float]  # bootstrap CI of the mean
    n_series: int
    n_effective: float
    opponent_factor: float
    components: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        side_prob = self.p_over if self.prediction == "OVER" else 1.0 - self.p_over
        return {
            "player": self.player,
            "line": self.line,
            "prediction": self.prediction,
            "p_over": round(self.p_over, 4),
            "side_probability": round(side_prob, 4),
            "expected_stat": round(self.expected_stat, 2),
            "predictive_interval": [round(x, 1) for x in self.predictive_interval],
            "expected_stat_ci": [round(x, 2) for x in self.expected_stat_ci],
            "n_series": self.n_series,
            "n_effective": round(self.n_effective, 1),
            "opponent_factor": round(self.opponent_factor, 3),
            "components": {k: round(v, 4) for k, v in self.components.items()},
        }


class PropsModel:
    """Predicts P(over) for one (prop_type, map_range) configuration."""

    def __init__(
        self,
        series_totals: pd.DataFrame,
        kill_env: pd.DataFrame | None = None,
        half_life_days: float = 150.0,
        blend_k: float = 6.0,
        opponent_adjust: bool = False,
        opponent_window: int = 20,
        calibration: tuple[float, float] | None = None,
        rng_seed: int = 7,
    ):
        # calibration = (a, b): a Platt correction on the logit of p_over,
        # p_cal = sigmoid(a * logit(p_over) + b). None = identity (raw model).
        # Fit out-of-sample via fit_calibration(); corrects a small residual
        # under-lean in the confident-UNDER tail. See docs/algorithmic_review.md.
        self.half_life_days = half_life_days
        self.blend_k = blend_k
        self.opponent_adjust = opponent_adjust
        self.opponent_window = opponent_window
        self.calibration = calibration
        self.rng = np.random.default_rng(rng_seed)

        self._players: dict[str, PlayerHistory] = {}
        for name, grp in series_totals.groupby("playername", sort=False):
            self._players[name] = PlayerHistory(
                dates=grp["date"].to_numpy(),
                totals=grp["total"].to_numpy(dtype=float),
                positions=grp["position"].to_numpy(),
            )

        self._team_env: dict[str, tuple[np.ndarray, np.ndarray]] = {}
        self._global_env_dates: np.ndarray | None = None
        self._global_env_cumsum: np.ndarray | None = None
        if kill_env is not None:
            for tid, grp in kill_env.groupby("teamid", sort=False):
                allowed = grp["kills_allowed"].to_numpy(dtype=float)
                self._team_env[tid] = (grp["date"].to_numpy(), np.cumsum(allowed))
            env_sorted = kill_env.sort_values("date")
            self._global_env_dates = env_sorted["date"].to_numpy()
            self._global_env_cumsum = np.cumsum(
                env_sorted["kills_allowed"].to_numpy(dtype=float)
            )

    # ------------------------------------------------------------------ #
    # weighting
    # ------------------------------------------------------------------ #

    def _recency_weights(self, dates: np.ndarray, as_of: np.datetime64) -> np.ndarray:
        age_days = (as_of - dates) / np.timedelta64(1, "D")
        return np.power(0.5, age_days / self.half_life_days)

    @staticmethod
    def _effective_n(weights: np.ndarray) -> float:
        s = weights.sum()
        return float(s * s / np.square(weights).sum()) if s > 0 else 0.0

    # ------------------------------------------------------------------ #
    # opponent kill environment
    # ------------------------------------------------------------------ #

    def _opponent_factor(self, opponent_teamid: str | None, as_of: np.datetime64) -> float:
        """How kill-rich is this opponent vs. the global environment? Dampened."""
        if (
            not self.opponent_adjust
            or opponent_teamid is None
            or opponent_teamid not in self._team_env
            or self._global_env_dates is None
        ):
            return 1.0

        dates, cumsum = self._team_env[opponent_teamid]
        hi = int(np.searchsorted(dates, as_of, side="left"))
        if hi < 8:  # not enough opponent history
            return 1.0
        lo = max(0, hi - self.opponent_window)
        opp_mean = (cumsum[hi - 1] - (cumsum[lo - 1] if lo > 0 else 0.0)) / (hi - lo)

        g_hi = int(np.searchsorted(self._global_env_dates, as_of, side="left"))
        g_lo = int(
            np.searchsorted(
                self._global_env_dates, as_of - np.timedelta64(180, "D"), side="left"
            )
        )
        if g_hi - g_lo < 100:
            return 1.0
        global_mean = (
            self._global_env_cumsum[g_hi - 1]
            - (self._global_env_cumsum[g_lo - 1] if g_lo > 0 else 0.0)
        ) / (g_hi - g_lo)
        if global_mean <= 0 or opp_mean <= 0:
            return 1.0

        return float(np.clip(np.sqrt(opp_mean / global_mean), 0.85, 1.2))

    # ------------------------------------------------------------------ #
    # probability components
    # ------------------------------------------------------------------ #

    @staticmethod
    def _nb_p_over(mean: float, var: float, line: float) -> float:
        """P(X > line) for a Negative Binomial (Poisson fallback) count model."""
        k = int(np.floor(line))
        if var <= mean + 1e-9:  # NB requires overdispersion; fall back to Poisson
            return float(stats.poisson.sf(k, mu=max(mean, 1e-6)))
        # Method of moments: var = mean + mean^2/r
        r = mean * mean / (var - mean)
        p = r / (r + mean)
        return float(stats.nbinom.sf(k, r, p))

    @staticmethod
    def _nb_ppf(mean: float, var: float, q: float) -> float:
        if var <= mean + 1e-9:
            return float(stats.poisson.ppf(q, mu=max(mean, 1e-6)))
        r = mean * mean / (var - mean)
        p = r / (r + mean)
        return float(stats.nbinom.ppf(q, r, p))

    # ------------------------------------------------------------------ #
    # prediction
    # ------------------------------------------------------------------ #

    def predict(
        self,
        player: str,
        line: float,
        as_of: pd.Timestamp | None = None,
        opponent_teamid: str | None = None,
        position: str | None = None,
        n_bootstrap: int = 2000,
    ) -> Prediction | None:
        """Predict P(total > line). Returns None if history is insufficient.

        `as_of`: only series strictly before this timestamp are used.
        `position`: optionally restrict history to series played in that role.
        """
        hist = self._players.get(player)
        if hist is None:
            return None

        as_of64 = (
            np.datetime64(as_of.to_datetime64())
            if as_of is not None
            else hist.dates[-1] + np.timedelta64(1, "D")
        )
        mask = hist.dates < as_of64
        if position is not None:
            mask &= hist.positions == position
        totals = hist.totals[mask]
        dates = hist.dates[mask]
        if len(totals) < MIN_SERIES_FOR_PREDICTION:
            return None

        w = self._recency_weights(dates, as_of64)
        w_sum = w.sum()
        n_eff = self._effective_n(w)

        factor = self._opponent_factor(opponent_teamid, as_of64)

        # Weighted moments (opponent factor scales the expected environment).
        mean = float(np.dot(w, totals) / w_sum)
        var = float(np.dot(w, np.square(totals - mean)) / w_sum)
        # Unbiased-ish correction for weighted variance
        denom = 1.0 - float(np.square(w).sum()) / (w_sum * w_sum)
        if denom > 1e-9:
            var /= denom
        adj_mean = mean * factor
        adj_var = var * factor * factor

        # Component 1: weighted empirical exceedance. Scaling the distribution
        # by `factor` is equivalent to scaling the line by 1/factor.
        p_emp = float(np.dot(w, (totals > line / factor).astype(float)) / w_sum)

        # Component 2: negative binomial on adjusted moments.
        p_nb = self._nb_p_over(adj_mean, adj_var, line)

        # Blend: trust the empirical distribution as effective n grows.
        w_emp = n_eff / (n_eff + self.blend_k)
        p_over = w_emp * p_emp + (1.0 - w_emp) * p_nb
        p_over = float(np.clip(p_over, 0.01, 0.99))
        p_raw = p_over

        # Optional Platt recalibration on the logit (identity if unset).
        if self.calibration is not None:
            a, b = self.calibration
            logit = np.log(p_over / (1.0 - p_over))
            p_over = float(1.0 / (1.0 + np.exp(-(a * logit + b))))
            p_over = float(np.clip(p_over, 0.01, 0.99))

        # True bootstrap for the CI of the mean: resample actual series totals.
        # Skipped (NaN CI) when n_bootstrap=0, e.g. inside the backtest loop.
        if n_bootstrap > 0:
            probs = w / w_sum
            idx = self.rng.choice(len(totals), size=(n_bootstrap, len(totals)), p=probs)
            boot_means = totals[idx].mean(axis=1) * factor
            mean_ci = (
                float(np.percentile(boot_means, 5)),
                float(np.percentile(boot_means, 95)),
            )
        else:
            mean_ci = (float("nan"), float("nan"))

        # Predictive interval for a single upcoming series: blend empirical
        # weighted quantiles with NB quantiles using the same trust weight.
        emp_lo, emp_hi = _weighted_quantiles(totals * factor, w, (0.05, 0.95))
        nb_lo = self._nb_ppf(adj_mean, adj_var, 0.05)
        nb_hi = self._nb_ppf(adj_mean, adj_var, 0.95)
        pred_int = (
            max(0.0, w_emp * emp_lo + (1 - w_emp) * nb_lo),
            w_emp * emp_hi + (1 - w_emp) * nb_hi,
        )

        return Prediction(
            player=player,
            line=line,
            p_over=p_over,
            prediction="OVER" if p_over >= 0.5 else "UNDER",
            expected_stat=adj_mean,
            predictive_interval=pred_int,
            expected_stat_ci=mean_ci,
            n_series=int(len(totals)),
            n_effective=n_eff,
            opponent_factor=factor,
            components={
                "p_empirical": p_emp, "p_negbinom": p_nb,
                "w_empirical": w_emp, "p_raw": p_raw,
            },
        )

    def history_quantiles(
        self,
        player: str,
        qs: tuple[float, ...],
        as_of: pd.Timestamp | None = None,
        position: str | None = None,
    ) -> np.ndarray | None:
        """Recency-weighted quantiles of a player's series totals (for line grids)."""
        hist = self._players.get(player)
        if hist is None:
            return None
        as_of64 = (
            np.datetime64(as_of.to_datetime64())
            if as_of is not None
            else hist.dates[-1] + np.timedelta64(1, "D")
        )
        mask = hist.dates < as_of64
        if position is not None:
            mask &= hist.positions == position
        totals = hist.totals[mask]
        if len(totals) < MIN_SERIES_FOR_PREDICTION:
            return None
        w = self._recency_weights(hist.dates[mask], as_of64)
        return np.array(_weighted_quantiles(totals, w, qs))


def _weighted_quantiles(
    values: np.ndarray, weights: np.ndarray, qs: tuple[float, ...]
) -> tuple:
    order = np.argsort(values)
    v = values[order]
    cw = np.cumsum(weights[order])
    cw = cw / cw[-1]
    return tuple(float(np.interp(q, cw, v)) for q in qs)


def fit_calibration(
    raw_p: np.ndarray, outcomes: np.ndarray, iters: int = 400, lr: float = 0.3
) -> tuple[float, float]:
    """Fit a Platt (a, b) correction: p_cal = sigmoid(a*logit(p) + b).

    Minimizes log loss by gradient descent (no sklearn dependency). Fit this
    on data STRICTLY OLDER than what you predict on, then pass the result as
    PropsModel(calibration=(a, b)); otherwise the correction leaks.
    """
    p = np.clip(np.asarray(raw_p, dtype=float), 1e-6, 1 - 1e-6)
    y = np.asarray(outcomes, dtype=float)
    x = np.log(p / (1 - p))
    a, b = 1.0, 0.0
    n = len(x)
    for _ in range(iters):
        z = a * x + b
        pred = 1.0 / (1.0 + np.exp(-z))
        err = pred - y
        a -= lr * float(np.dot(err, x)) / n
        b -= lr * float(err.mean())
    return a, b
