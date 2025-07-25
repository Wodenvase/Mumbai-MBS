# 🏘️ Mumbai Real Estate: Mortgage Cash Flow & Prepayment Model

## 💡 Overview
A high-performance Mortgage-Backed Securities (MBS) simulator tailored to Mumbai’s residential housing market. Built using Polars, this model ingests granular loan-level data to generate realistic cash flows, model borrower prepayment behavior, and compute key bond metrics.

## ⚙️ Features
- Loan-level simulation with Mumbai housing loan data
- PSA-based prepayment modeling with local adjustments
- Computes cash flow waterfall, average life, duration, convexity
- Stress testing for RBI rate shifts, price shocks, and zone-specific risks
- Optional interactive dashboards (Plotly)

## 🛠️ Tech Stack
- Polars (data processing)
- pydantic (validation)
- Plotly (dashboard)

## 🚀 Getting Started
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Place your loan data CSV in the `data/` folder (already done).
3. Run the main script:
   ```bash
   python main.py
   ```

## 📁 Project Structure
- `data/` — Input CSV data
- `mbs/` — Core modules (loader, model, prepayment, stress, dashboard)
- `main.py` — Entrypoint

## 📊 Next Steps
- Implement cash flow and prepayment logic
- Add stress testing and dashboard modules 