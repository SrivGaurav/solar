"""Payout and expected loss calculations."""
from __future__ import annotations
import numpy as np
import pandas as pd


def calculate_payouts(df: pd.DataFrame, strike: float, exit: float, ppa: float):
    """
    Calculate payouts based on strike, exit, and PPA rate.
    If 'User_Detrended' is missing, it will be auto-created from 'Rescaled_Energy_MWh'.
    """
    # --- Safety fallback ---
    if "User_Detrended" not in df.columns:
        if "Rescaled_Energy_MWh" in df.columns:
            df["User_Detrended"] = df["Rescaled_Energy_MWh"].copy()
        else:
            raise KeyError(
                "Expected 'User_Detrended' or 'Rescaled_Energy_MWh' column not found in DataFrame"
            )

    if "Rescaled_Energy_MWh" not in df.columns:
        raise KeyError("Expected 'Rescaled_Energy_MWh' column not found in DataFrame")

    limit = (strike - exit) * ppa

    df["Payout_Untrended"] = np.minimum(
        limit,
        np.maximum(0.0, (strike - df["Rescaled_Energy_MWh"])) * ppa
    )

    df["Payout_Detrended"] = np.minimum(
        limit,
        np.maximum(0.0, (strike - df["User_Detrended"])) * ppa
    )

    return df, limit


def expected_loss(
    values: np.ndarray,
    strike: float,
    exit: float,
    ppa: float,
    limit: float
) -> float:
    """Compute average expected payout from simulated energy values (blown Sobol samples)."""
    payout = np.clip((strike - values), 0.0, strike - exit) * ppa
    return float(np.minimum(payout, limit).mean())
