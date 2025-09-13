
"""Plotting utilities for visualizing solar energy modeling results."""
from __future__ import annotations
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from scipy.stats import linregress

def plot_annual_trend(df_yearly: pd.DataFrame) -> None:
    """Plot annual energy trend (matplotlib)."""
    x = df_yearly['Year']; y = df_yearly['Energy_MWh_Hourly']
    plt.figure(figsize=(14, 6))
    plt.plot(x, y, '-o', color='gray')
    plt.title('Annual Energy Trend'); plt.xlabel('Year'); plt.ylabel('Energy (MWh)')
    plt.grid(True, linestyle='--', alpha=0.5); plt.tight_layout(); plt.show()

def plot_monthly_scatter(df_monthly: pd.DataFrame) -> None:
    """Interactive monthly scatter (plotly)."""
    fig = go.Figure(go.Scatter(
        x=df_monthly['Date'],
        y=df_monthly['Monthly_Energy_MWh'],
        mode='markers',
        marker=dict(size=8, color=df_monthly['Monthly_Energy_MWh'],
                    colorscale='RdBu', line=dict(width=0.5, color='black'))
    ))
    fig.update_layout(
        title='Monthly Solar Energy Production',
        xaxis=dict(title='Date', rangeslider=dict(visible=True)),
        yaxis_title='Energy (MWh)',
        template='plotly_white'
    )
    fig.show()

def plot_interactive_annual(df_yearly: pd.DataFrame) -> None:
    """Interactive annual lines+markers (plotly)."""
    fig = go.Figure(go.Scatter(
        x=df_yearly['Year'],
        y=df_yearly['Energy_MWh_Hourly'],
        mode='lines+markers',
        marker=dict(size=10, color=df_yearly['Energy_MWh_Hourly'],
                    colorscale='RdBu', colorbar=dict(title='MWh'),
                    line=dict(width=1, color='black'))
    ))
    fig.update_layout(
        title='Interactive Annual Solar Energy Production',
        xaxis=dict(title='Year', rangeslider=dict(visible=True)),
        yaxis_title='Energy (MWh)',
        template='plotly_white'
    )
    fig.show()

def plot_monthly_seasonality(df_monthly: pd.DataFrame) -> None:
    """Monthly seasonality (matplotlib)."""
    df = df_monthly.copy()
    df['Year'] = df['Date'].dt.year; df['Month'] = df['Date'].dt.month
    monthly_avg = df.groupby('Month')['Monthly_Energy_MWh'].mean()
    high_thresh = monthly_avg.median()
    colors = ['blue' if v >= high_thresh else 'red' for v in monthly_avg]
    plt.figure(figsize=(10, 5))
    plt.scatter(monthly_avg.index, monthly_avg.values, s=180, c=colors, edgecolor='black', zorder=3)
    plt.plot(monthly_avg.index, monthly_avg.values, color='gray', linewidth=2.5, zorder=1)
    plt.xticks(ticks=range(1,13), labels=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'])
    plt.title('Average Monthly Solar Energy Generation', fontsize=14, weight='bold')
    plt.xlabel('Month'); plt.ylabel('Avg Energy (MWh)')
    plt.grid(True, linestyle='--', alpha=0.4); plt.tight_layout(); plt.show()

def plot_detrended_comparison(sub: pd.DataFrame) -> None:
    """Compare rescaled vs detrended series with trend lines (matplotlib)."""
    plt.figure(figsize=(12, 5))
    plt.plot(sub['Year'], sub['Rescaled_Energy_MWh'], label='Rescaled Energy', color='blue', marker='o')
    plt.plot(sub['Year'], sub['User_Detrended'], label='Detrended', color='green', marker='s')
    res_slope, res_int, *_ = linregress(sub['Year'], sub['Rescaled_Energy_MWh'])
    det_slope, det_int, *_ = linregress(sub['Year'], sub['User_Detrended'])
    plt.plot(sub['Year'], res_int + res_slope * sub['Year'], '--', color='navy', label='Rescaled Trend')
    plt.plot(sub['Year'], det_int + det_slope * sub['Year'], '--', color='green', label='Detrended Trend')
    plt.title('Rescaled vs Detrended Energy Comparison')
    plt.xlabel('Year'); plt.ylabel('Energy (MWh)')
    plt.legend(); plt.grid(True, linestyle='--', alpha=0.5); plt.tight_layout(); plt.show()

def plot_payout_bars(sub: pd.DataFrame) -> None:
    """Side-by-side bars for untrended vs detrended payouts (matplotlib)."""
    bar_width = 0.4; idx = np.arange(len(sub))
    plt.figure(figsize=(12, 5))
    plt.bar(idx, sub['Payout_Untrended'], width=bar_width, label='Untrended Payout', color='steelblue')
    plt.bar(idx + bar_width, sub['Payout_Detrended'], width=bar_width, label='Detrended Payout', color='orange')
    plt.xticks(idx + bar_width / 2, sub['Year'], rotation=45)
    plt.xlabel('Year'); plt.ylabel('Payout (INR)')
    plt.title('Annual Payout: Untrended vs Detrended')
    plt.legend(); plt.grid(True, linestyle='--', alpha=0.4); plt.tight_layout(); plt.show()

def plot_gamma_distributions(percentiles: np.ndarray, empirical: np.ndarray,
                             gamma_vals: np.ndarray, blown_vals: np.ndarray,
                             strike: float, exit: float) -> None:
    """Empirical vs gamma vs blown gamma distributions with strike/exit lines (matplotlib)."""
    plt.figure(figsize=(10, 6))
    plt.plot(empirical, percentiles, label='Empirical', color='C0', linewidth=2,
             marker='o', markerfacecolor='C1', markersize=4)
    plt.plot(gamma_vals, percentiles, label='Gamma Model', color='green', linestyle='--', linewidth=2)
    plt.plot(blown_vals, percentiles, label='Blown Gamma', color='red', linestyle=':', linewidth=2)
    plt.axvline(x=strike, color='black', linestyle='--', linewidth=1.5, label='Strike')
    plt.axvline(x=exit, color='gray', linestyle='--', linewidth=1.5, label='Exit')
    plt.xlabel('Energy (MWh)'); plt.ylabel('Percentile')
    plt.title('Energy Distribution Comparison')
    plt.legend(); plt.grid(True, linestyle='--', alpha=0.5); plt.tight_layout(); plt.show()

def plot_sobol_simulation(simulated_values: np.ndarray) -> None:
    """Histogram of blown Sobol simulation values (matplotlib)."""
    plt.figure(figsize=(10, 6))
    plt.hist(simulated_values, bins=40, color='purple', alpha=0.7, edgecolor='black')
    plt.title('Sobol Simulation Results Distribution')
    plt.xlabel('Simulated Energy (MWh)'); plt.ylabel('Frequency')
    plt.grid(True, linestyle='--', alpha=0.5); plt.tight_layout(); plt.show()
