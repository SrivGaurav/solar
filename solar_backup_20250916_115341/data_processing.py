"""Data loading and preprocessing utilities for the Solar package."""
from __future__ import annotations
import pandas as pd
from .config import EFFICIENCY_RATIO, PERFORMANCE_FACTOR, AREA_CELLS, CONVERSION_RATIO


def read_solar_data(path: str) -> pd.DataFrame:
    """
    Read solar SSRD CSV data with a 'Date' column (auto-detects tab or comma separator).
    """
    for sep in ('\t', ','):
        try:
            return pd.read_csv(path, sep=sep, parse_dates=['Date'], dayfirst=True)
        except Exception:
            continue
    raise ValueError("Could not read CSV; ensure it has 'Date' and 'SSRD' columns.")


def calculate_hourly_energy(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate hourly energy from SSRD using configured panel specs (in kWh).
    """
    df = df.copy()
    df['Hourly_Energy_kWh'] = (
        df['SSRD']
        * AREA_CELLS
        * EFFICIENCY_RATIO
        * PERFORMANCE_FACTOR
        * CONVERSION_RATIO
    )
    return df


def calculate_monthly_energy(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate hourly energy to monthly totals (MWh).
    """
    monthly = df.resample('ME', on='Date')['Hourly_Energy_kWh'].sum().reset_index()
    monthly['Monthly_Energy_MWh'] = monthly['Hourly_Energy_kWh'] / 1000.0
    return monthly


def calculate_annual_energy(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate annual energy (Sept 1 – Aug 31 blocks) from hourly data.

    This replicates the original script logic:
    - Year window: Sept Y to Aug Y+1 (365 days, add 1 if leap day inside)
    - Skips any year > 2024
    """
    if "Date" not in df.columns:
        raise ValueError("Input DataFrame must contain a 'Date' column.")

    df = df.copy()
    df["Date"] = pd.to_datetime(df["Date"], dayfirst=True, errors="coerce")
    df = df.dropna(subset=["Date"])
    if df.empty:
        raise ValueError("No valid dates found in 'Date' column.")

    df = df.sort_values("Date")
    out = []

    for y in df["Date"].dt.year.unique():
        if y > 2024:
            continue  # ✅ Ignore anything beyond 2024

        start = pd.Timestamp(y, 9, 1)
        end = start + pd.Timedelta(days=365)

        # ✅ Handle leap years: extend window if Feb 29 falls inside
        try:
            leap_check = pd.Timestamp(y, 2, 29)
            if start <= leap_check <= end:
                end += pd.Timedelta(days=1)
        except ValueError:
            pass

        mask = (df["Date"] >= start) & (df["Date"] <= end)
        total_kwh = df.loc[mask, "Hourly_Energy_kWh"].sum()

        out.append({
            "Year": int(y),
            "Energy_MWh_Hourly": total_kwh / 1000.0
        })

    return pd.DataFrame(out)
