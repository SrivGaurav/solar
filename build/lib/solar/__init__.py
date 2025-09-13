
"""Solar Energy Modeling Package"""
from .data_processing import read_solar_data, calculate_hourly_energy, calculate_monthly_energy, calculate_annual_energy
from .detrending import gaussian_detrend, linear_detrend
from .payouts import calculate_payouts, expected_loss
from .gamma_model import gamma_params, blow
from .sobol_sim import sobol_sim
from .plotting import (
    plot_annual_trend, plot_monthly_scatter, plot_interactive_annual, plot_monthly_seasonality,
    plot_detrended_comparison, plot_payout_bars, plot_gamma_distributions, plot_sobol_simulation
)
from .main import run, main

__all__ = [
    'read_solar_data','calculate_hourly_energy','calculate_monthly_energy','calculate_annual_energy',
    'gaussian_detrend','linear_detrend',
    'calculate_payouts','expected_loss',
    'gamma_params','blow',
    'sobol_sim',
    'plot_annual_trend','plot_monthly_scatter','plot_interactive_annual','plot_monthly_seasonality',
    'plot_detrended_comparison','plot_payout_bars','plot_gamma_distributions','plot_sobol_simulation',
    'run','main'
]
