"""Gamma distribution fitting and blown-distribution generation utilities."""
from __future__ import annotations
import numpy as np
from scipy.stats import gamma as sgamma

def calculate_gamma_parameters(values: np.ndarray) -> tuple[float, float]:
    """
    Estimate shape and scale parameters for a gamma distribution from data.
    """
    mean = values.mean()
    std = values.std(ddof=1)
    shape = (mean / std) ** 2
    scale = (std ** 2) / mean
    return shape, scale

def excel_style_percentiles(values: np.ndarray, percentiles: np.ndarray) -> np.ndarray:
    """
    Mimic Excel percentile behavior (nearest rank).
    """
    sorted_vals = np.sort(values)
    n = len(sorted_vals)
    result = []
    for p in percentiles:
        rank = int(np.ceil(p * n))
        rank = min(max(rank, 1), n)
        result.append(sorted_vals[rank - 1])
    return np.array(result)

def apply_exponential_blow(values: np.ndarray, blow_point: float, blow_factor: float, blow_dir: str, shift: float) -> np.ndarray:
    """
    Apply exponential blow-up/down transformation.
    """
    values = np.asarray(values)
    if blow_dir == 'D':
        mask = values < blow_point
        blown = np.where(mask, blow_point - (blow_point - values) * np.exp(-blow_factor / 100), values)
    elif blow_dir == 'U':
        mask = values > blow_point
        blown = np.where(mask, blow_point + (values - blow_point) * np.exp(-blow_factor / 100), values)
    else:
        blown = values
    return blown + shift

def generate_distributions(values: np.ndarray, shape: float, scale: float, percentiles: np.ndarray,
                           blow_point: float, blow_factor: float, blow_dir: str, shift: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Generate empirical, gamma, and blown-gamma percentile curves.
    """
    empirical = excel_style_percentiles(values, percentiles)
    gamma_vals = sgamma.ppf(percentiles, a=shape, scale=scale)
    blown_vals = apply_exponential_blow(gamma_vals, blow_point, blow_factor, blow_dir, shift)
    return empirical, gamma_vals, blown_vals
