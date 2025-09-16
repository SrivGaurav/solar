import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import gamma as sgamma

import solar
from solar.data_input import load_ssrd

# --- Sidebar Inputs ---
st.sidebar.header("📍 Site Details")
client_name = st.sidebar.text_input("Client Name", "Demo Client")
plant_name = st.sidebar.text_input("Plant Name", "Demo Plant")
latitude = st.sidebar.number_input("Latitude", value=28.6, format="%.4f")
longitude = st.sidebar.number_input("Longitude", value=77.2, format="%.4f")

area_cells = st.sidebar.number_input("Area Cells (m²)", value=348642)
efficiency = st.sidebar.number_input("Efficiency Ratio (%)", value=16.5) / 100.0
performance_factor = st.sidebar.number_input("Performance Factor (%)", value=79.69) / 100.0
client_p50 = st.sidebar.number_input("Client P50 (MWh)", value=112684)

strike = st.sidebar.number_input("Strike (MWh)", value=110193)
exit = st.sidebar.number_input("Exit (MWh)", value=100000)
ppa_rate = st.sidebar.number_input("PPA Rate (₹/MWh)", value=5000)

st.sidebar.header("📈 Blow Parameters")
blow_point = st.sidebar.number_input("Blow Point", value=107000)
blow_factor = st.sidebar.number_input("Blow Factor", value=-30)
blow_dir = st.sidebar.selectbox("Blow Direction", ["D", "U"])
shift = st.sidebar.number_input("Shift", value=0)

# --- Load data from NetCDF using lat/lon ---
nc_path = "/Users/gaurav.srivastava/Downloads/era5ssrd/era5ssrd.nc"
with st.spinner("Loading ERA5 SSRD data..."):
    df, meta = load_ssrd(latitude, longitude)

if df.empty:
    st.error("No data extracted from NetCDF for the given coordinates.")
    st.stop()

# --- Solar Energy Calculations ---
df = solar.calculate_hourly_energy(df)
df_monthly = solar.calculate_monthly_energy(df)
df_annual = solar.calculate_annual_energy(df)

# --- Rescale based on Client P50 ---
ref = df_annual[(df_annual["Year"] >= 1980) & (df_annual["Year"] <= 2023)]
p50 = ref["Energy_MWh_Hourly"].mean()
rescale_factor = client_p50 / p50 if p50 else np.nan
df_annual["Rescaled_Energy_MWh"] = df_annual["Energy_MWh_Hourly"] * rescale_factor

# --- Detrending choice ---
method = st.sidebar.selectbox("Detrending Method", ["Linear", "Kernel"])
start_year = st.sidebar.number_input("Start Year", value=int(df_annual["Year"].min()))
end_year = st.sidebar.number_input("End Year", value=int(df_annual["Year"].max()))

subset = df_annual[(df_annual["Year"] >= start_year) & (df_annual["Year"] <= end_year)].copy()
if method == "Kernel":
    bw = st.sidebar.number_input("Kernel Bandwidth", value=3.0)
    smoothed, detrended = solar.gaussian_detrend(subset["Year"].values, subset["Rescaled_Energy_MWh"].values, bw)
    subset["User_Detrended"] = detrended
else:
    subset["User_Detrended"] = solar.linear_detrend(subset["Year"].values, subset["Rescaled_Energy_MWh"].values)

# --- Burn Cost Calculations ---
subset, limit = solar.calculate_payouts(subset, strike, exit, ppa_rate)

def burn_cost(series: pd.Series): 
    return np.mean(series) if not series.empty else 0

bc_5 = burn_cost(subset.tail(5)["Payout_Detrended"])
bc_10 = burn_cost(subset.tail(10)["Payout_Detrended"])
bc_20 = burn_cost(subset.tail(20)["Payout_Detrended"])
bc_total = burn_cost(subset["Payout_Detrended"])

# --- Expected Loss using Sobol ---
try:
    sobol_path = "/Users/gaurav.srivastava/Downloads/solar/sobol.csv"
    sob = pd.read_csv(sobol_path).iloc[:, 0].values
    shape, scale = solar.gamma_params(subset["User_Detrended"].values)
    gamma_vals = sgamma.ppf(sob, a=shape, scale=scale)
    blown = solar.apply_exponential_blow(gamma_vals, blow_point, blow_factor, blow_dir, shift)
    payouts = np.clip((strike - blown), 0, strike - exit) * ppa_rate
    payouts = np.minimum(payouts, limit)
    expected_loss = payouts.mean()
except Exception as e:
    expected_loss = None

# --- Display Results ---
st.title("☀️ Solar Energy Analysis Dashboard")
st.subheader(f"{client_name} — {plant_name}")

st.markdown("### 📊 Burn Cost Summary")
cols = st.columns(5)
for c, label, val in zip(cols, ["5-Year", "10-Year", "20-Year", "Total", "Expected Loss"],
                          [bc_5, bc_10, bc_20, bc_total, expected_loss]):
    with c:
        st.markdown(
            f"<div style='background:#f5f5f5;padding:15px;border-radius:10px;text-align:center;'>"
            f"<h4 style='margin:0;color:#333'>{label}</h4>"
            f"<p style='font-size:18px;margin:0;color:#111'>₹{val:,.0f}</p>"
            f"</div>", unsafe_allow_html=True)

# --- Plots ---
st.markdown("### 📈 Interactive Annual Energy Generation")
solar.plot_interactive_annual(df_annual)

st.markdown("### 📅 Long-Term Monthly Average Generation")
solar.plot_monthly_seasonality(df_monthly)

st.markdown("### 📊 Energy Distribution Comparison")
percentiles = np.arange(0.01, 1.00, 0.01)
emp, gvals, blown = solar.generate_distributions(
    subset["User_Detrended"].values, shape, scale, percentiles, blow_point, blow_factor, blow_dir, shift
)
solar.plot_gamma_distributions(percentiles, emp, gvals, blown, strike, exit)
