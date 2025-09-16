from pathlib import Path
from solar.ssrd_io import get_ssrd_series

NC_PATH = Path("/Users/gaurav.srivastava/Downloads/era5ssrd/era5ssrd.nc")

def load_ssrd(lat: float, lon: float):
    """
    Load SSRD time series from the fixed ERA5 NetCDF file
    for the given latitude and longitude.
    """
    if not NC_PATH.exists():
        raise FileNotFoundError(f"ERA5 SSRD file not found at {NC_PATH}")
    df, meta = get_ssrd_series(NC_PATH, lat, lon, unit="Jm2", tz=None)
    return df, meta
