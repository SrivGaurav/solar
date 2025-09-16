"""Main CLI entrypoint for the Solar energy modeling package."""
from __future__ import annotations
import argparse
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt

from .data_input import load_ssrd
from .data_processing import calculate_hourly_energy, calculate_monthly_energy, calculate_annual_energy
from .detrending import gaussian_detrend, linear_detrend
from .payouts import calculate_payouts, expected_loss
from .gamma_model import calculate_gamma_parameters, apply_exponential_blow
from .sobol_sim import sobol_sim
from .plotting import (
    plot_annual_trend, plot_interactive_annual, plot_monthly_scatter, plot_monthly_seasonality,
    plot_detrended_comparison, plot_payout_bars, plot_gamma_distributions, plot_sobol_simulation
)

OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(exist_ok=True)

def save_fig(fig, name: str, is_plotly=False):
    out = OUTPUT_DIR / name
    if is_plotly:
        fig.write_html(str(out))
    else:
        fig.savefig(out, dpi=200, bbox_inches="tight")
        plt.close(fig)
    print(f"Saved → {out}")

def run(lat: float, lon: float, method: str, start: int, end: int, bw: float,
        strike: float, exit: float, ppa: float, blow_point: float, blow_factor: float) -> None:
    """Run the full modeling workflow on ERA5 SSRD data at (lat, lon)."""

    # --- Data ---
    df, meta = load_ssrd(lat, lon)
    df = calculate_hourly_energy(df)
    monthly = calculate_monthly_energy(df)
    yearly = calculate_annual_energy(df)
    rescale_factor = yearly['Energy_MWh_Hourly'].mean()
    yearly['Rescaled_Energy_MWh'] = yearly['Energy_MWh_Hourly'] * (rescale_factor / yearly['Energy_MWh_Hourly'].mean())

    # --- Detrend ---
    sub = yearly[(yearly['Year'] >= start) & (yearly['Year'] <= end)].copy()
    if method == 'kernel':
        _, detrended = gaussian_detrend(sub['Year'].values, sub['Rescaled_Energy_MWh'].values, bw)
    else:
        detrended = linear_detrend(sub['Year'].values, sub['Rescaled_Energy_MWh'].values)
    sub['User_Detrended'] = detrended

    # --- Payouts ---
    sub, limit = calculate_payouts(sub, strike, exit, ppa)

    # --- Gamma + Sobol ---
    shape, scale = calculate_gamma_parameters(sub['User_Detrended'].values)
    sobol_values = sobol_sim(shape, scale, "/Users/gaurav.srivastava/Downloads/solar/solar/sobol.csv")
    blown = apply_exponential_blow(sobol_values, blow_point, blow_factor, 'D', 0)
    eloss = expected_loss(blown, strike, exit, ppa, limit)
    print(f"\nExpected Loss from Sobol Simulation: ₹{eloss:,.2f}")

    # --- Plotting ---
    # Each plot now returns a fig object so we can save it
    f1 = plot_annual_trend(yearly)
    save_fig(f1, "annual_trend.png")

    f2 = plot_interactive_annual(yearly)
    save_fig(f2, "annual_interactive.html", is_plotly=True)

    f3 = plot_monthly_scatter(monthly)
    save_fig(f3, "monthly_scatter.html", is_plotly=True)

    f4 = plot_monthly_seasonality(monthly)
    save_fig(f4, "monthly_seasonality.png")

    f5 = plot_detrended_comparison(sub)
    save_fig(f5, "detrended_comparison.png")

    f6 = plot_payout_bars(sub)
    save_fig(f6, "payout_bars.png")

    percentiles = np.arange(0.01, 1.00, 0.01)
    empirical = np.percentile(sub['User_Detrended'].values, percentiles * 100.0)
    from scipy.stats import gamma
    gamma_vals = gamma.ppf(percentiles, a=shape, scale=scale)
    blown_vals = apply_exponential_blow(gamma_vals, blow_point, blow_factor, 'D', 0)
    f7 = plot_gamma_distributions(percentiles, empirical, gamma_vals, blown_vals, strike, exit)
    save_fig(f7, "gamma_distribution.png")

    f8 = plot_sobol_simulation(blown)
    save_fig(f8, "sobol_simulation.png")

    print("\n✅ All results saved in:", OUTPUT_DIR.resolve())

def main() -> None:
    p = argparse.ArgumentParser(description="Run the Solar energy modeling workflow")
    p.add_argument('--lat', type=float, required=True, help="Latitude for ERA5 SSRD extraction")
    p.add_argument('--lon', type=float, required=True, help="Longitude for ERA5 SSRD extraction")
    p.add_argument('--method', choices=['linear', 'kernel'], default='linear', help='Detrending method')
    p.add_argument('--start', type=int, default=2000, help='Start year for detrending')
    p.add_argument('--end', type=int, default=2024, help='End year for detrending')
    p.add_argument('--bw', type=float, default=3.0, help='Kernel bandwidth (if method=kernel)')
    p.add_argument('--strike', type=float, default=110_193, help='Strike threshold (MWh)')
    p.add_argument('--exit', type=float, default=100_000, help='Exit threshold (MWh)')
    p.add_argument('--ppa', type=float, default=5_000, help='PPA rate (INR/MWh)')
    p.add_argument('--blow-point', type=float, default=107_000, help='Blow transformation point (MWh)')
    p.add_argument('--blow-factor', type=float, default=-30.0, help='Blow factor (percent)')
    a = p.parse_args()
    run(a.lat, a.lon, a.method, a.start, a.end, a.bw, a.strike, a.exit, a.ppa, a.blow_point, a.blow_factor)

if __name__ == "__main__":
    main()
