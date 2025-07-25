import streamlit as st
import polars as pl
from mbs.loader import load_loans, LoanRecord
from mbs.model import aggregate_cash_flows, compute_mbs_metrics, amortization_schedule
from mbs.stress import apply_rbi_rate_shift, apply_price_shock, apply_zone_default_surge
import plotly.graph_objects as go
from collections import defaultdict

@st.cache_data
def get_loans():
    return load_loans("data/sheet1.csv")

st.title("🏘️ Mumbai MBS Simulator Dashboard")
st.markdown("""
This dashboard provides interactive insights into Mumbai's residential mortgage-backed securities (MBS) pool. 

- **Filter by zone, borrower type, and stress scenario**
- **Visualize cash flows, prepayment speeds, and key MBS metrics**
- **Compare base and stressed scenarios**
""")

loans = get_loans()

# Sidebar filters
zones = sorted(list(set(loan.zone for loan in loans)))
statuses = sorted(list(set(loan.formalization_status for loan in loans)))
metrics = ['total_principal', 'total_interest', 'total_prepayment']
metric_labels = {'total_principal': 'Principal', 'total_interest': 'Interest', 'total_prepayment': 'Prepayment'}

st.sidebar.header("Filters & Scenarios")
selected_zones = st.sidebar.multiselect("Zone", zones, default=zones)
selected_statuses = st.sidebar.multiselect("Formalization Status", statuses, default=statuses)
selected_metric = st.sidebar.selectbox("Metric to Plot", metrics, format_func=lambda x: metric_labels[x])

scenario = st.sidebar.selectbox(
    "Stress Scenario",
    ["Base", "RBI rate +1%", "Price appreciation -5%", "South Mumbai 20% default surge"]
)

# Filter loans
filtered_loans = [loan for loan in loans if loan.zone in selected_zones and loan.formalization_status in selected_statuses]

# Apply scenario
if scenario == "Base":
    scenario_loans = filtered_loans
elif scenario == "RBI rate +1%":
    scenario_loans = apply_rbi_rate_shift(filtered_loans, 1.0)
elif scenario == "Price appreciation -5%":
    scenario_loans = apply_price_shock(filtered_loans, -0.05)
elif scenario == "South Mumbai 20% default surge":
    scenario_loans = apply_zone_default_surge(filtered_loans, 'South Mumbai', 0.2)
else:
    scenario_loans = filtered_loans

# Aggregate cash flows
cash_flows = aggregate_cash_flows(scenario_loans)
metrics_dict = compute_mbs_metrics(cash_flows)

# --- Metrics Section ---
st.subheader("Key MBS Metrics")
col1, col2, col3 = st.columns(3)
col1.metric("Average Life (yrs)", f"{metrics_dict['average_life']:.2f}")
col2.metric("Duration (yrs)", f"{metrics_dict['duration']:.2f}")
col3.metric("Convexity", f"{metrics_dict['convexity']:.2f}")

st.markdown("""
**Average Life**: Weighted average time to principal repayment.  
**Duration**: Sensitivity of price to interest rate changes.  
**Convexity**: Sensitivity of duration to interest rate changes.
""")

# --- Main Chart ---
months = [row['month'] for row in cash_flows]
y_vals = [row[selected_metric] for row in cash_flows]
fig = go.Figure()
fig.add_trace(go.Bar(x=months, y=y_vals, name=metric_labels[selected_metric]))
fig.update_layout(title=f"{metric_labels[selected_metric]} Over Time", xaxis_title="Month", yaxis_title=metric_labels[selected_metric])
st.plotly_chart(fig, use_container_width=True)

# --- Zone-wise Chart ---
st.subheader("Zone-wise Cash Flows")
zone_groups = defaultdict(list)
for loan in scenario_loans:
    zone_groups[loan.zone].append(loan)
fig2 = go.Figure()
for zone, zone_loans in zone_groups.items():
    flows = [amortization_schedule(loan) for loan in zone_loans]
    max_len = max(len(f) for f in flows) if flows else 0
    monthly = [0] * max_len
    for f in flows:
        for i, entry in enumerate(f):
            monthly[i] += entry.get(selected_metric, 0)
    fig2.add_trace(go.Scatter(x=list(range(1, max_len+1)), y=monthly, mode='lines', name=zone))
fig2.update_layout(title=f"{metric_labels[selected_metric]} by Zone", xaxis_title='Month', yaxis_title=metric_labels[selected_metric])
st.plotly_chart(fig2, use_container_width=True)

# --- Formalization Segmentation Chart ---
st.subheader("Formalization Status Segmentation")
seg_groups = defaultdict(list)
for loan in scenario_loans:
    seg_groups[loan.formalization_status].append(loan)
fig3 = go.Figure()
for seg, seg_loans in seg_groups.items():
    flows = [amortization_schedule(loan) for loan in seg_loans]
    max_len = max(len(f) for f in flows) if flows else 0
    monthly = [0] * max_len
    for f in flows:
        for i, entry in enumerate(f):
            monthly[i] += entry.get(selected_metric, 0)
    fig3.add_trace(go.Scatter(x=list(range(1, max_len+1)), y=monthly, mode='lines', name=seg))
fig3.update_layout(title=f"{metric_labels[selected_metric]} by Formalization Status", xaxis_title='Month', yaxis_title=metric_labels[selected_metric])
st.plotly_chart(fig3, use_container_width=True)

st.markdown("""
---
**How to use this dashboard:**
- Use the sidebar to filter by zone, borrower type, and stress scenario.
- Select the metric (principal, interest, prepayment) to visualize.
- All charts and metrics update instantly based on your selections.
""") 