
"""Main CLI entrypoint for the Solar energy modeling package."""
from __future__ import annotations
import argparse
import numpy as np
from .data_processing import read_solar_data, calculate_hourly_energy, calculate_monthly_energy, calculate_annual_energy
from .detrending import gaussian_detrend, linear_detrend
from .payouts import calculate_payouts, expected_loss
from .gamma_model import gamma_params, blow
from .sobol_sim import sobol_sim
from .plotting import (
    plot_annual_trend, plot_interactive_annual, plot_monthly_scatter, plot_monthly_seasonality,
    plot_detrended_comparison, plot_payout_bars, plot_gamma_distributions, plot_sobol_simulation
)
from .config import CLIENT_P50

def run(csv: str, method: str, start: int, end: int, bw: float,
        strike: float, exit: float, ppa: float, blow_point: float, blow_factor: float) -> None:
    """Run the full modeling workflow on the given CSV file."""
    # Data
    df = calculate_hourly_energy(read_solar_data(csv))
    monthly = calculate_monthly_energy(df)
    yearly = calculate_annual_energy(df)
    yearly['Rescaled_Energy_MWh'] = yearly['Energy_MWh_Hourly'] * (CLIENT_P50 / yearly['Energy_MWh_Hourly'].mean())

    # Detrend
    sub = yearly[(yearly['Year'] >= start) & (yearly['Year'] <= end)].copy()
    if method == 'kernel':
        _, detrended = gaussian_detrend(sub['Year'].values, sub['Rescaled_Energy_MWh'].values, bw)
    else:
        detrended = linear_detrend(sub['Year'].values, sub['Rescaled_Energy_MWh'].values)
    sub['User_Detrended'] = detrended

    # Payouts
    sub, limit = calculate_payouts(sub, strike, exit, ppa)

    # Gamma + Sobol
    _, _, shape, scale = gamma_params(sub['User_Detrended'].values)
    sobol_values = sobol_sim(shape, scale, "/Users/gaurav.srivastava/Downloads/solar/solar/sobol.csv")
    blown = blow(sobol_values, blow_point, blow_factor)
    eloss = expected_loss(blown, strike, exit, ppa, limit)
    print(f"Expected Loss from Sobol Simulation: {eloss:,.2f}")

    # Plots
    plot_annual_trend(yearly)
    plot_interactive_annual(yearly)
    plot_monthly_scatter(monthly)
    plot_monthly_seasonality(monthly)
    plot_detrended_comparison(sub)
    plot_payout_bars(sub)

    percentiles = np.arange(0.01, 1.00, 0.01)
    empirical = np.percentile(sub['User_Detrended'].values, percentiles * 100.0)
    from scipy.stats import gamma
    gamma_vals = gamma.ppf(percentiles, a=shape, scale=scale)
    blown_vals = blow(gamma_vals, blow_point, blow_factor)
    plot_gamma_distributions(percentiles, empirical, gamma_vals, blown_vals, strike, exit)

    plot_sobol_simulation(blown)

def main() -> None:
    p = argparse.ArgumentParser(description="Run the Solar energy modeling workflow")
    p.add_argument('csv', help="Path to CSV with 'Date' and 'SSRD' columns")
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
    run(a.csv, a.method, a.start, a.end, a.bw, a.strike, a.exit, a.ppa, a.blow_point, a.blow_factor)

if __name__ == "__main__":
    main()
