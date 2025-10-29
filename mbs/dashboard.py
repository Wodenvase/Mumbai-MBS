import plotly.express as px
import plotly.graph_objects as go
import polars as pl
from typing import List, Dict, Union
from collections import defaultdict

def plot_cash_flows(cash_flows: Union[pl.DataFrame, List[Dict]], title: str = "MBS Aggregate Cash Flows"):
    """Plot cash flows from either Polars DataFrame or list of dicts."""
    if isinstance(cash_flows, pl.DataFrame):
        months = cash_flows['month'].to_list()
        principal = cash_flows['total_principal'].to_list()
        interest = cash_flows['total_interest'].to_list()
        prepayment = cash_flows['total_prepayment'].to_list()
    else:
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

def compare_scenarios(base: Union[pl.DataFrame, List[Dict]], 
                     stressed: Union[pl.DataFrame, List[Dict]], 
                     metric: str, 
                     title: str = "Scenario Comparison"):
    """Compare scenarios from either Polars DataFrames or list of dicts."""
    if isinstance(base, pl.DataFrame):
        months = base['month'].to_list()
        base_vals = base[metric].to_list()
        stressed_vals = stressed[metric].to_list()
    else:
        months = [row['month'] for row in base]
        base_vals = [row[metric] for row in base]
        stressed_vals = [row[metric] for row in stressed]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=months, y=base_vals, mode='lines', name='Base'))
    fig.add_trace(go.Scatter(x=months, y=stressed_vals, mode='lines', name='Stressed'))
    fig.update_layout(title=title, xaxis_title='Month', yaxis_title=metric)
    fig.show()

def plot_zone_wise_cash_flows(loans_df: pl.DataFrame, metric: str = 'total_prepayment'):
    """Plot cash flows by zone using the Rust engine."""
    from mbs.model import aggregate_cash_flows
    
    zones = loans_df['zone'].unique().to_list()
    fig = go.Figure()
    
    for zone in zones:
        zone_loans = loans_df.filter(pl.col('zone') == zone)
        if len(zone_loans) > 0:
            try:
                zone_flows = aggregate_cash_flows(zone_loans)
                months = zone_flows['month'].to_list()
                values = zone_flows[metric].to_list()
                fig.add_trace(go.Scatter(x=months, y=values, mode='lines', name=zone))
            except Exception as e:
                print(f"Warning: Could not compute flows for zone {zone}: {e}")
    
    fig.update_layout(
        title=f"{metric.replace('_', ' ').title()} by Zone", 
        xaxis_title='Month', 
        yaxis_title=metric
    )
    fig.show()

def plot_formalization_segmentation(loans_df: pl.DataFrame, metric: str = 'total_prepayment'):
    """Plot cash flows by formalization status using the Rust engine."""
    from mbs.model import aggregate_cash_flows
    
    segments = loans_df['formalization_status'].unique().to_list()
    fig = go.Figure()
    
    for segment in segments:
        seg_loans = loans_df.filter(pl.col('formalization_status') == segment)
        if len(seg_loans) > 0:
            try:
                seg_flows = aggregate_cash_flows(seg_loans)
                months = seg_flows['month'].to_list()
                values = seg_flows[metric].to_list()
                fig.add_trace(go.Scatter(x=months, y=values, mode='lines', name=segment))
            except Exception as e:
                print(f"Warning: Could not compute flows for segment {segment}: {e}")
    
    fig.update_layout(
        title=f"{metric.replace('_', ' ').title()} by Formalization Status", 
        xaxis_title='Month', 
        yaxis_title=metric
    )
    fig.show() 