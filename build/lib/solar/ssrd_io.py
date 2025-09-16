"""Utilities to extract SSRD time series from ERA5 NetCDF files."""
from __future__ import annotations
from pathlib import Path
from typing import Literal, Tuple, Dict
import pandas as pd
import xarray as xr

Unit = Literal["Jm2", "Wm2", "kWhm2"]

def _normalize_time(ds: xr.Dataset) -> xr.Dataset:
    """Ensure the time dimension is named 'time'."""
    if "time" in ds.dims:
        return ds
    if "valid_time" in ds.dims:
        return ds.rename({"valid_time": "time"})
    raise ValueError("No 'time' or 'valid_time' dimension found in dataset.")

def _find_var(ds: xr.Dataset) -> str:
    """Find the SSRD variable name in the file."""
    if "ssrd" in ds.variables:
        return "ssrd"
    if "surface_solar_radiation_downwards" in ds.variables:
        return "surface_solar_radiation_downwards"
    # Try any variable whose long_name mentions short-wave + down
    for cand in ds.data_vars:
        long_name = str(ds[cand].attrs.get("long_name", "")).lower()
        if "short-wave" in long_name and "down" in long_name:
            return cand
    raise ValueError("Could not find an SSRD variable (e.g., 'ssrd').")

def extract_ssrd_from_nc(
    nc_path: str | Path,
    lat: float,
    lon: float,
    unit: Unit = "Jm2",
    tz: str | None = None,
) -> Tuple[pd.DataFrame, Dict]:
    """
    Extract ERA5 SSRD at the nearest grid point to (lat, lon) from a NetCDF file.
    """
    nc_path = Path(nc_path)
    if not nc_path.exists():
        raise FileNotFoundError(nc_path)

    ds = xr.open_dataset(nc_path, decode_times=True)
    ds = _normalize_time(ds)
    var = _find_var(ds)

    # If longitudes are 0..360 and user passed a negative lon, wrap it.
    lon_vals = ds["longitude"].values
    if lon_vals.min() >= 0 and lon < 0:
        lon = lon + 360.0

    # Pick nearest grid point
    da = ds[var].sel(latitude=lat, longitude=lon, method="nearest")
    chosen_lat = float(da.coords["latitude"].values)
    chosen_lon = float(da.coords["longitude"].values)

    # Unit conversion (SSRD is hourly energy in J/m^2)
    if unit == "Wm2":
        da = da / 3600.0
        unit_str = "W m-2"
    elif unit == "kWhm2":
        da = da / 3_600_000.0
        unit_str = "kWh m-2"
    else:
        unit_str = "J m-2"

    # Build DataFrame
    time = pd.to_datetime(da["time"].values)
    if tz:
        time = (pd.DatetimeIndex(time)
                .tz_localize("UTC")
                .tz_convert(tz)
                .tz_localize(None))
    df = pd.DataFrame({"Date": time, "SSRD": da.values})
    if not df["Date"].is_monotonic_increasing:
        df = df.sort_values("Date", ignore_index=True)

    meta = {
        "lat": chosen_lat,
        "lon": chosen_lon,
        "unit": unit_str,
        "rows": int(len(df)),
        "source": str(nc_path),
    }
    return df, meta

def get_ssrd_series(
    source_path: str | Path,
    lat: float,
    lon: float,
    unit: Unit = "Jm2",
    tz: str | None = None,
):
    """
    Unified entrypoint to read SSRD from a NetCDF file.
    """
    p = Path(source_path)
    if p.suffix.lower() != ".nc":
        raise ValueError("Only .nc files are supported now (CSV removed).")

    df, meta = extract_ssrd_from_nc(p, lat, lon, unit=unit, tz=tz)
    return df, meta
