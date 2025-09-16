"""Plotting utilities for visualizing solar energy modeling results."""
from __future__ import annotations
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from scipy.stats import linregress


def plot_annual_trend(df_yearly: pd.DataFrame):
    """Plot annual energy trend (matplotlib) -> fig."""
    x = df_yearly['Year']; y = df_yearly['Energy_MWh_Hourly']
    fig, ax = plt.subplots(figsize=(14, 6))
    scatter = ax.scatter(x, y, c=y, cmap="RdBu", edgecolors="black", s=70)
    ax.plot(x, y, '-o', color='gray')
    ax.set_title('Annual Energy Trend')
    ax.set_xlabel('Year'); ax.set_ylabel('Energy (MWh)')
    ax.grid(True, linestyle='--', alpha=0.5)
    fig.colorbar(scatter, ax=ax, label="MWh")
    fig.tight_layout()
    return fig


def plot_monthly_scatter(df_monthly: pd.DataFrame):
    """Interactive monthly scatter (plotly) -> fig."""
    fig = go.Figure(go.Scatter(
        x=df_monthly['Date'],
        y=df_monthly['Monthly_Energy_MWh'],
        mode='markers',
        marker=dict(
            size=8, color=df_monthly['Monthly_Energy_MWh'],
            colorscale='RdBu', line=dict(width=0.5, color='black'))
    ))
    fig.update_layout(
        title='Monthly Solar Energy Production',
        xaxis=dict(title='Date', rangeslider=dict(visible=True)),
        yaxis_title='Energy (MWh)',
        template='plotly_white'
    )
    return fig


def plot_interactive_annual(df_yearly: pd.DataFrame):
    """Interactive annual lines+markers (plotly) -> fig."""
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
    return fig


def plot_monthly_seasonality(df_monthly: pd.DataFrame):
    """Monthly seasonality (matplotlib) -> fig."""
    df = df_monthly.copy()
    df['Year'] = df['Date'].dt.year; df['Month'] = df['Date'].dt.month
    monthly_avg = df.groupby('Month')['Monthly_Energy_MWh'].mean()
    high_thresh = monthly_avg.median()
    colors = ['blue' if v >= high_thresh else 'red' for v in monthly_avg]

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.scatter(monthly_avg.index, monthly_avg.values, s=180, c=colors, edgecolor='black', zorder=3)
    ax.plot(monthly_avg.index, monthly_avg.values, color='gray', linewidth=2.5, zorder=1)
    ax.set_xticks(range(1, 13))
    ax.set_xticklabels(['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'])
    ax.set_title('Average Monthly Solar Energy Generation', fontsize=14, weight='bold')
    ax.set_xlabel('Month'); ax.set_ylabel('Avg Energy (MWh)')
    ax.grid(True, linestyle='--', alpha=0.4)
    fig.tight_layout()
    return fig


def plot_detrended_comparison(sub: pd.DataFrame):
    """Compare rescaled vs detrended series with trend lines (matplotlib) -> fig."""
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(sub['Year'], sub['Rescaled_Energy_MWh'], label='Rescaled Energy', color='blue', marker='o')
    ax.plot(sub['Year'], sub['User_Detrended'], label='Detrended', color='green', marker='s')

    res_slope, res_int, *_ = linregress(sub['Year'], sub['Rescaled_Energy_MWh'])
    det_slope, det_int, *_ = linregress(sub['Year'], sub['User_Detrended'])
    ax.plot(sub['Year'], res_int + res_slope * sub['Year'], '--', color='navy', label='Rescaled Trend')
    ax.plot(sub['Year'], det_int + det_slope * sub['Year'], '--', color='green', label='Detrended Trend')

    ax.set_title('Rescaled vs Detrended Energy Comparison')
    ax.set_xlabel('Year'); ax.set_ylabel('Energy (MWh)')
    ax.legend(); ax.grid(True, linestyle='--', alpha=0.5)
    fig.tight_layout()
    return fig


def plot_payout_bars(sub: pd.DataFrame):
    """Side-by-side bars for untrended vs detrended payouts (matplotlib) -> fig."""
    fig, ax = plt.subplots(figsize=(12, 5))
    bar_width = 0.4; idx = np.arange(len(sub))
    ax.bar(idx, sub['Payout_Untrended'], width=bar_width, label='Untrended Payout', color='steelblue')
    ax.bar(idx + bar_width, sub['Payout_Detrended'], width=bar_width, label='Detrended Payout', color='orange')
    ax.set_xticks(idx + bar_width / 2)
    ax.set_xticklabels(sub['Year'], rotation=45)
    ax.set_xlabel('Year'); ax.set_ylabel('Payout (INR)')
    ax.set_title('Annual Payout: Untrended vs Detrended')
    ax.legend(); ax.grid(True, linestyle='--', alpha=0.4)
    fig.tight_layout()
    return fig


def plot_gamma_distributions(percentiles: np.ndarray, empirical: np.ndarray,
                             gamma_vals: np.ndarray, blown_vals: np.ndarray,
                             strike: float, exit: float):
    """Empirical vs gamma vs blown gamma distributions -> fig."""
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(empirical, percentiles, label='Empirical', color='C0', linewidth=2,
            marker='o', markerfacecolor='C1', markersize=4)
    ax.plot(gamma_vals, percentiles, label='Gamma Model', color='green', linestyle='--', linewidth=2)
    ax.plot(blown_vals, percentiles, label='Blown Gamma', color='red', linestyle=':', linewidth=2)
    ax.axvline(x=strike, color='black', linestyle='--', linewidth=1.5, label='Strike')
    ax.axvline(x=exit, color='gray', linestyle='--', linewidth=1.5, label='Exit')
    ax.set_xlabel('Energy (MWh)'); ax.set_ylabel('Percentile')
    ax.set_title('Energy Distribution Comparison')
    ax.legend(); ax.grid(True, linestyle='--', alpha=0.5)
    fig.tight_layout()
    return fig


def plot_sobol_simulation(simulated_values: np.ndarray):
    """Histogram of blown Sobol simulation values (matplotlib) -> fig."""
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.hist(simulated_values, bins=40, color='purple', alpha=0.7, edgecolor='black')
    ax.set_title('Sobol Simulation Results Distribution')
    ax.set_xlabel('Simulated Energy (MWh)'); ax.set_ylabel('Frequency')
    ax.grid(True, linestyle='--', alpha=0.5)
    fig.tight_layout()
    return fig
