
# Solar Model

A Python package for solar energy generation modeling, detrending, payout simulation, and risk analysis.

## 📦 Installation
```bash
# From the root directory (where pyproject.toml is present):
pip install .
```

## 🐍 Usage (as Python module)
```python
import solar

# Load and process data
df = solar.read_solar_data("data.csv")
df = solar.calculate_hourly_energy(df)

# Calculate monthly and annual totals
monthly = solar.calculate_monthly_energy(df)
annual = solar.calculate_annual_energy(df)

# Plot annual trend
solar.plot_annual_trend(annual)
```

## 💻 CLI Usage
```bash
solar data.csv --method kernel --start 2000 --end 2024 --bw 3 --strike 110193 --exit 100000 --ppa 5000 --blow-point 107000 --blow-factor -30
```
