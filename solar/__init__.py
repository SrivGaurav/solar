# __init__.py

from .config import EFFICIENCY_RATIO, PERFORMANCE_FACTOR, AREA_CELLS, CONVERSION_RATIO
from .data_processing import calculate_hourly_energy, calculate_monthly_energy, calculate_annual_energy
from .detrending import linear_detrend, gaussian_detrend
from .payouts import calculate_payouts, expected_loss
from .plotting import plot_annual_trend, plot_monthly_scatter, plot_interactive_annual, plot_monthly_seasonality, plot_gamma_distributions
from .gamma_model import calculate_gamma_parameters, excel_style_percentiles, apply_exponential_blow, generate_distributions
from .sobol_sim import sobol_sim
from .data_input import load_ssrd

__all__ = [
    "load_ssrd",
    "calculate_hourly_energy",
    "calculate_monthly_energy",
    "calculate_annual_energy",
    "linear_detrend",
    "gaussian_detrend",
    "calculate_payouts",
    "expected_loss",
    "plot_annual_trend",
    "plot_monthly_scatter",
    "plot_interactive_annual",
    "plot_monthly_seasonality",
    "plot_gamma_distributions",
    "calculate_gamma_parameters",
    "excel_style_percentiles",
    "apply_exponential_blow",
    "generate_distributions",
    "sobol_sim",
    # config constants could also be exposed if desired
]
