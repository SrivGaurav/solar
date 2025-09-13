
"""Payout and expected loss calculations."""
from __future__ import annotations
import numpy as np
import pandas as pd

def calculate_payouts(df: pd.DataFrame, strike: float, exit: float, ppa: float) -> tuple[pd.DataFrame, float]:
    """Calculate capped payouts for both rescaled and detrended energy series."""
    limit = (strike - exit) * ppa
    df = df.copy()
    df['Payout_Untrended'] = np.minimum(limit, np.maximum(0.0, (strike - df['Rescaled_Energy_MWh'])) * ppa)
    df['Payout_Detrended'] = np.minimum(limit, np.maximum(0.0, (strike - df['User_Detrended'])) * ppa)
    return df, float(limit)

def expected_loss(values: np.ndarray, strike: float, exit: float, ppa: float, limit: float) -> float:
    """Compute average expected payout from simulated energy values (blown Sobol samples)."""
    payout = np.clip((strike - values), 0.0, strike - exit) * ppa
    return float(np.minimum(payout, limit).mean())
