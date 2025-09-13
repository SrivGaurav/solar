
"""Detrending utilities for annual solar energy series."""
from __future__ import annotations
import numpy as np
from scipy.stats import linregress
from sklearn.metrics.pairwise import rbf_kernel

def gaussian_detrend(x: np.ndarray, y: np.ndarray, bw: float) -> tuple[np.ndarray, np.ndarray]:
    """Apply Gaussian RBF smoothing and return (smoothed, detrended) anchored to last point."""
    X = np.array(x).reshape(-1, 1)
    w = rbf_kernel(X, X, gamma=1.0 / (2.0 * bw ** 2))
    w = w / w.sum(axis=1, keepdims=True)
    smoothed = w @ y
    anchor = smoothed[-1]
    detrended = anchor + (y - smoothed)
    return smoothed, detrended

def linear_detrend(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    """Linear detrending via regression residuals, anchored to last point."""
    slope, intercept, *_ = linregress(x, y)
    anchor = x[-1] * slope + intercept
    return anchor + (y - (x * slope + intercept))
