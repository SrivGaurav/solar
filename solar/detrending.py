"""Detrending utilities for annual solar energy series."""
from __future__ import annotations
import numpy as np
import pandas as pd
from scipy.stats import linregress
from sklearn.metrics.pairwise import rbf_kernel


def gaussian_detrend(x: np.ndarray, y: np.ndarray, bw: float) -> tuple[np.ndarray, np.ndarray]:
    """
    Apply Gaussian RBF smoothing and return (smoothed, detrended),
    anchoring the detrended series to the last smoothed point.
    """
    X = np.array(x).reshape(-1, 1)
    y = np.array(y, dtype=float)

    if len(X) == 0 or len(y) == 0:
        return np.array([]), np.array([])

    w = rbf_kernel(X, X, gamma=1.0 / (2.0 * bw ** 2))
    w = w / w.sum(axis=1, keepdims=True)

    smoothed = w @ y
    anchor = smoothed[-1]
    detrended = anchor + (y - smoothed)

    return smoothed, detrended


def linear_detrend(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    """
    Detrend a series linearly using regression residuals,
    anchoring the detrended series to the last fitted point.
    """
    # Ensure Series to support .iloc
    x = pd.Series(x).reset_index(drop=True)
    y = pd.Series(y, dtype=float).reset_index(drop=True)

    if x.empty or y.empty:
        return np.array([])

    slope, intercept, *_ = linregress(x, y)
    anchor = x.iloc[-1] * slope + intercept   # ✅ fixed (was x[-1])

    detrended = anchor + (y - (x * slope + intercept))
    return detrended.to_numpy()
