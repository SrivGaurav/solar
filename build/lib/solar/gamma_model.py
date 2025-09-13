
"""Gamma fitting and exponential blow transformation."""
from __future__ import annotations
import numpy as np
from scipy.stats import gamma

def gamma_params(vals: np.ndarray) -> tuple[float, float, float, float]:
    """Estimate mean, std, shape (k), and scale (theta) for the gamma distribution."""
    m = float(vals.mean())
    s = float(vals.std(ddof=1))
    shape = (m / s) ** 2 if s > 0 else 1.0
    scale = (s ** 2) / m if m > 0 else 1.0
    return m, s, shape, scale

def blow(vals: np.ndarray, pt: float, factor: float, dir: str = 'D', shift: float = 0.0) -> np.ndarray:
    """Apply exponential blow transformation down ('D') or up ('U')."""
    vals = np.asarray(vals, dtype=float)
    if dir == 'D':
        mask = vals < pt
        blown = np.where(mask, pt - (pt - vals) * np.exp(-factor / 100.0), vals)
    else:
        mask = vals > pt
        blown = np.where(mask, pt + (vals - pt) * np.exp(-factor / 100.0), vals)
    return blown + shift
