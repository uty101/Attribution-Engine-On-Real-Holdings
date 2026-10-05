"""Stationary bootstrap interval for a mean (kickoff Section 5.9; D-20)."""

from __future__ import annotations

import numpy as np
from pc.stats import stationary_bootstrap_indices


def bootstrap_mean(x, mean_block: float, reps: int, seed: int, lo: float, hi: float) -> tuple[float, float, float]:
    """(mean of x, lo and hi quantiles of the resampled means), resampling with
    `pc.stats.stationary_bootstrap_indices(len(x), mean_block, reps, seed)`."""
    x = np.asarray(x, dtype="float64")
    means = x[stationary_bootstrap_indices(len(x), mean_block, reps, seed)].mean(axis=1)
    return float(x.mean()), float(np.quantile(means, lo)), float(np.quantile(means, hi))
