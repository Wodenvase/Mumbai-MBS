import plotly.express as px
import plotly.graph_objects as go
from typing import List, Dict
from mbs.loader import LoanRecord
from mbs.model import amortization_schedule
from collections import defaultdict

def plot_cash_flows(cash_flows: List[Dict], title: str = "MBS Aggregate Cash Flows"):
    months = [row['month'] for row in cash_flows]
    principal = [row['total_principal'] for row in cash_flows]
    interest = [row['total_interest'] for row in cash_flows]
    prepayment = [row.get('total_prepayment', 0) for row in cash_flows]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=months, y=principal, name='Principal'))
    fig.add_trace(go.Bar(x=months, y=prepayment, name='Prepayment'))
    fig.add_trace(go.Bar(x=months, y=interest, name='Interest'))
    fig.update_layout(barmode='stack', title=title, xaxis_title='Month', yaxis_title='Amount')
    fig.show()

def compare_scenarios(base: List[Dict], stressed: List[Dict], metric: str, title: str = "Scenario Comparison"):
    months = [row['month'] for row in base]
    base_vals = [row[metric] for row in base]
    stressed_vals = [row[metric] for row in stressed]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=months, y=base_vals, mode='lines', name='Base'))
    fig.add_trace(go.Scatter(x=months, y=stressed_vals, mode='lines', name='Stressed'))
    fig.update_layout(title=title, xaxis_title='Month', yaxis_title=metric)
    fig.show()

def plot_zone_wise_cash_flows(loans: List[LoanRecord], metric: str = 'total_prepayment'):
    """Plot cash flows by zone (e.g., prepayment speed by zone)."""
    zone_groups = defaultdict(list)
    for loan in loans:
        zone_groups[loan.zone].append(loan)
    fig = go.Figure()
    for zone, zone_loans in zone_groups.items():
        # Aggregate flows for this zone
        flows = [amortization_schedule(loan) for loan in zone_loans]
        # Sum by month
        max_len = max(len(f) for f in flows)
        monthly = [0] * max_len
        for f in flows:
            for i, entry in enumerate(f):
                monthly[i] += entry.get(metric, 0)
        fig.add_trace(go.Scatter(x=list(range(1, max_len+1)), y=monthly, mode='lines', name=zone))
    fig.update_layout(title=f"{metric.replace('_', ' ').title()} by Zone", xaxis_title='Month', yaxis_title=metric)
    fig.show()

def plot_formalization_segmentation(loans: List[LoanRecord], metric: str = 'total_prepayment'):
    """Plot cash flows by formalization status (Formal vs. Informal)."""
    seg_groups = defaultdict(list)
    for loan in loans:
        seg_groups[loan.formalization_status].append(loan)
    fig = go.Figure()
    for seg, seg_loans in seg_groups.items():
        flows = [amortization_schedule(loan) for loan in seg_loans]
        max_len = max(len(f) for f in flows)
        monthly = [0] * max_len
        for f in flows:
            for i, entry in enumerate(f):
                monthly[i] += entry.get(metric, 0)
        fig.add_trace(go.Scatter(x=list(range(1, max_len+1)), y=monthly, mode='lines', name=seg))
    fig.update_layout(title=f"{metric.replace('_', ' ').title()} by Formalization Status", xaxis_title='Month', yaxis_title=metric)
    fig.show() 