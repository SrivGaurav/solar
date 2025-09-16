# ssrd_zarr_adapter.py
from __future__ import annotations
from pathlib import Path
from functools import lru_cache
from typing import Tuple, Dict, Optional
import numpy as np
import pandas as pd
import xarray as xr

class SSRDStore:
    """
    Fast reader for ERA5 SSRD Zarr store chunked as (time=744, lat=1, lon=1).
    Returns a DataFrame with columns [Date, SSRD].
    """
    def __init__(self, zarr_path: str | Path):
        self.zarr_path = str(zarr_path)
        self.ds = xr.open_zarr(self.zarr_path, consolidated=True)
        self.var = "ssrd" if "ssrd" in self.ds.data_vars else (
            "surface_solar_radiation_downwards" if "surface_solar_radiation_downwards" in self.ds.data_vars
            else list(self.ds.data_vars)[0]
        )
        self.lats = self.ds["latitude"].values
        self.lons = self.ds["longitude"].values

    def _nearest_index(self, lat: float, lon: float) -> Tuple[int, int]:
        ilat = int(np.abs(self.lats - lat).argmin())
        ilon = int(np.abs(self.lons - lon).argmin())
        return ilat, ilon

    @lru_cache(maxsize=4096)
    def _series_at_index(self, ilat: int, ilon: int, unit: str) -> Tuple[np.ndarray, np.ndarray]:
        """Return (time_npdatetime64, values) for a grid index and unit."""
        da = self.ds[self.var].isel(latitude=ilat, longitude=ilon)
        if unit == "Wm2":
            da = da / 3600.0
        elif unit == "kWhm2":
            da = da / 3_600_000.0
        t = pd.to_datetime(da["time"].values).to_numpy()
        v = da.values
        return t, v

    def get_dataframe(
        self,
        lat: float,
        lon: float,
        unit: str = "kWhm2",
        tz: Optional[str] = "Asia/Kolkata",
        start: Optional[str] = None,
        end: Optional[str] = None,
    ) -> Tuple[pd.DataFrame, Dict]:
        """
        Extract nearest-grid hourly SSRD and return DataFrame [Date, SSRD].
        - unit: "Jm2" | "Wm2" | "kWhm2" (default)
        - tz: None for UTC, else timezone string (kept naive after conversion)
        - start/end: optional ISO date strings to clip (e.g., "2005-01-01")
        """
        ilat, ilon = self._nearest_index(lat, lon)
        t, v = self._series_at_index(ilat, ilon, unit)

        # Optional time clip (do before tz shift)
        if start or end:
            t0 = pd.to_datetime(start) if start else t[0]
            t1 = pd.to_datetime(end) if end else t[-1]
            mask = (t >= t0) & (t <= t1)
            t, v = t[mask], v[mask]

        # Optional timezone shift (UTC -> local, then drop tz)
        if tz:
            t = (pd.DatetimeIndex(t).tz_localize("UTC").tz_convert(tz).tz_localize(None)).to_numpy()

        df = pd.DataFrame({"Date": pd.to_datetime(t), "SSRD": v})
        meta = {"lat": float(self.lats[ilat]), "lon": float(self.lons[ilon]), "unit": unit, "rows": int(len(df))}
        return df, meta


# -------- Convenience one-liner for your pipeline --------
_GLOBAL_STORE: SSRDStore | None = None

def load_ssrd_from_zarr(
    zarr_path: str | Path,
    lat: float,
    lon: float,
    unit: str = "kWhm2",
    tz: Optional[str] = "Asia/Kolkata",
    start: Optional[str] = None,
    end: Optional[str] = None,
    out_csv: Optional[str | Path] = None,
) -> Tuple[pd.DataFrame, Dict]:
    """
    Open (or reuse) the Zarr store and return Date,SSRD.
    Optionally save to CSV with headers exactly 'Date,SSRD'.
    """
    global _GLOBAL_STORE
    if _GLOBAL_STORE is None or str(_GLOBAL_STORE.zarr_path) != str(zarr_path):
        _GLOBAL_STORE = SSRDStore(zarr_path)

    df, meta = _GLOBAL_STORE.get_dataframe(lat=lat, lon=lon, unit=unit, tz=tz, start=start, end=end)

    if out_csv:
        out = Path(out_csv)
        out.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(out, index=False)
        meta["csv"] = str(out)
    return df, meta
