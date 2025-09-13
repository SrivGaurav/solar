
"""Data loading and preprocessing utilities for the Solar package."""
from __future__ import annotations
import pandas as pd
from .config import EFFICIENCY_RATIO, PERFORMANCE_FACTOR, AREA_CELLS, CONVERSION_RATIO

def read_solar_data(path: str) -> pd.DataFrame:
    """Read solar SSRD CSV data with a 'Date' column (auto-detects tab or comma separator)."""
    for sep in ('\t', ','):
        try:
            return pd.read_csv(path, sep=sep, parse_dates=['Date'], dayfirst=True)
        except Exception:
            continue
    raise ValueError("Could not read CSV; ensure it has 'Date' and 'SSRD' columns.")

def calculate_hourly_energy(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate hourly energy from SSRD using configured panel specs (in kWh)."""
    df = df.copy()
    df['Hourly_Energy_kWh'] = df['SSRD'] * AREA_CELLS * EFFICIENCY_RATIO * PERFORMANCE_FACTOR * CONVERSION_RATIO
    return df

def calculate_monthly_energy(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate hourly energy to monthly totals (MWh)."""
    monthly = df.resample('ME', on='Date')['Hourly_Energy_kWh'].sum().reset_index()
    monthly['Monthly_Energy_MWh'] = monthly['Hourly_Energy_kWh'] / 1000.0
    return monthly

def calculate_annual_energy(df: pd.DataFrame) -> pd.DataFrame:
    df = df.sort_values('Date').copy()
    out = []
    for y in df['Date'].dt.year.unique():
        start = pd.Timestamp(y, 9, 1)
        end = start + pd.Timedelta(days=365)
        try:
            leap_check = pd.Timestamp(y, 2, 29)
            if leap_check >= start and leap_check <= end:
                end += pd.Timedelta(days=1)
        except ValueError:
            pass
        mask = (df['Date'] >= start) & (df['Date'] <= end)
        tot_kwh = df.loc[mask, 'Hourly_Energy_kWh'].sum()
        out.append({'Year': int(y), 'Energy_MWh_Hourly': tot_kwh / 1000.0})

    df_yearly = pd.DataFrame(out)
    # ✅ Only keep desired range
    return df_yearly[(df_yearly['Year'] >= 1980) & (df_yearly['Year'] <= 2024)]

