"""Sobol-based stochastic sampling of gamma-distributed energy values (from CSV file)."""
from __future__ import annotations
import numpy as np
import pandas as pd
from scipy.stats import gamma as sgamma

def sobol_sim(shape: float, scale: float, csv_path: str) -> np.ndarray:
    """
    Load Sobol numbers from a CSV file and transform them using the gamma PPF.

    Args:
        shape: Gamma shape parameter (k)
        scale: Gamma scale parameter (θ)
        csv_path: Path to CSV file containing Sobol numbers (0–1) in the first column.

    Returns:
        np.ndarray: Gamma-distributed values corresponding to Sobol numbers.
    """
    sobol_df = pd.read_csv(csv_path)
    if sobol_df.shape[1] == 0:
        raise ValueError("Sobol CSV is empty or has no columns.")
    sobol_numbers = sobol_df.iloc[:, 0].dropna().astype(float).values
    if not ((sobol_numbers >= 0) & (sobol_numbers <= 1)).all():
        raise ValueError("Sobol CSV must contain values between 0 and 1.")
    return sgamma.ppf(sobol_numbers, a=shape, scale=scale)