"""
Fallback pure Python implementation for when Rust engine is not available.
This demonstrates the same API and functionality but runs in pure Python.
"""

import polars as pl
import numpy as np
from typing import Dict, List
import copy
import random

def psa_curve(month: int, psa_speed: float = 100.0) -> float:
    """Return the monthly prepayment rate as per the PSA standard (annualized, in %)."""
    base_cpr = min(0.002 * month, 0.06)
    cpr = base_cpr * (psa_speed / 100.0)
    return cpr

def mumbai_psa_multiplier(price_appreciation_rate: float, zone: str, formalization_status: str) -> float:
    """Return a multiplier for PSA based on Mumbai-specific factors."""
    # Price appreciation
    if price_appreciation_rate > 0.08:
        price_mult = 2.0
    elif price_appreciation_rate > 0.05:
        price_mult = 1.5
    else:
        price_mult = 1.0
    
    # Zone
    zone_map = {
        'South Mumbai': 1.5,
        'Mumbai Suburbs': 1.0,
        'Navi Mumbai': 0.5
    }
    zone_mult = zone_map.get(zone, 1.0)
    
    # Formalization status
    formal_mult = 1.2 if formalization_status == 'Formal' else 1.0
    
    return price_mult * zone_mult * formal_mult

def generate_loan_schedule(loan_row: dict) -> List[dict]:
    """Generate amortization schedule for a single loan."""
    amount = loan_row['amount']
    interest_rate = loan_row['interest_rate']
    term_months = loan_row['term_months']
    zone = loan_row['zone']
    price_appreciation_rate = loan_row['price_appreciation_rate']
    formalization_status = loan_row['formalization_status']
    loan_id = loan_row['loan_id']
    
    monthly_rate = interest_rate / 100.0 / 12.0
    monthly_payment = amount * monthly_rate * (1 + monthly_rate) ** term_months / ((1 + monthly_rate) ** term_months - 1) if monthly_rate > 0 else amount / term_months
    
    schedule = []
    remaining_balance = amount
    
    for month in range(1, term_months + 1):
        if remaining_balance <= 0.001:
            break
            
        interest = remaining_balance * monthly_rate
        principal = monthly_payment - interest
        
        # Calculate prepayment
        cpr = psa_curve(month, 100.0) * mumbai_psa_multiplier(price_appreciation_rate, zone, formalization_status)
        smm = 1 - (1 - cpr) ** (1/12)
        prepayment = (remaining_balance - principal) * smm
        
        total_principal = principal + prepayment
        remaining_balance = max(remaining_balance - total_principal, 0)
        
        schedule.append({
            'loan_id': loan_id,
            'month': month,
            'payment': monthly_payment,
            'principal': principal,
            'interest': interest,
            'prepayment': prepayment,
            'total_principal': total_principal,
            'remaining_balance': remaining_balance,
        })
    
    return schedule

def aggregate_cash_flows_py(loans_df: pl.DataFrame) -> pl.DataFrame:
    """Pure Python implementation of cash flow aggregation."""
    # Convert to list of dicts for processing
    loans_list = loans_df.to_dicts()
    
    all_schedules = []
    for loan in loans_list:
        schedule = generate_loan_schedule(loan)
        all_schedules.extend(schedule)
    
    if not all_schedules:
        return pl.DataFrame({
            'month': [],
            'total_principal': [],
            'total_interest': [],
            'total_prepayment': [],
            'total_payment': []
        })
    
    # Convert to DataFrame and aggregate
    schedules_df = pl.DataFrame(all_schedules)
    
    aggregated = schedules_df.group_by('month').agg([
        pl.col('principal').sum().alias('total_principal'),
        pl.col('interest').sum().alias('total_interest'), 
        pl.col('prepayment').sum().alias('total_prepayment'),
        pl.col('payment').sum().alias('total_payment'),
    ]).sort('month')
    
    return aggregated

def compute_mbs_metrics_py(cash_flows_df: pl.DataFrame, discount_rate: float = 0.07) -> Dict:
    """Pure Python implementation of MBS metrics calculation."""
    if len(cash_flows_df) == 0:
        return {'average_life': 0.0, 'duration': 0.0, 'convexity': 0.0}
    
    months = cash_flows_df['month'].to_numpy()
    total_principal = cash_flows_df['total_principal'].to_numpy()
    total_prepayment = cash_flows_df['total_prepayment'].to_numpy()
    
    total_principal_payments = total_principal + total_prepayment
    
    total_principal_sum = np.sum(total_principal_payments)
    if total_principal_sum == 0:
        return {'average_life': 0.0, 'duration': 0.0, 'convexity': 0.0}
    
    monthly_discount_rate = discount_rate / 12.0
    
    # Present value calculations
    pv_factors = 1 / (1 + monthly_discount_rate) ** months
    pvs = total_principal_payments * pv_factors
    pv_total = np.sum(pvs)
    
    if pv_total == 0:
        return {'average_life': 0.0, 'duration': 0.0, 'convexity': 0.0}
    
    # Calculate metrics
    average_life = np.sum(months * total_principal_payments) / total_principal_sum / 12.0
    duration = np.sum(months * pvs) / pv_total / 12.0
    convexity = np.sum(months * (months + 1) * pvs) / (pv_total * (1 + monthly_discount_rate) ** 2) / (12.0 ** 2)
    
    return {
        'average_life': float(average_life),
        'duration': float(duration),
        'convexity': float(convexity)
    }

def apply_rbi_rate_shift_py(loans_df: pl.DataFrame, rate_shift: float) -> pl.DataFrame:
    """Pure Python implementation of RBI rate shift."""
    return loans_df.with_columns([
        (pl.col('interest_rate') + rate_shift).clip(0.0, None).alias('interest_rate'),
        (pl.col('rbi_rate_at_origination') + rate_shift).clip(0.0, None).alias('rbi_rate_at_origination'),
    ])

def apply_price_shock_py(loans_df: pl.DataFrame, appreciation_shift: float) -> pl.DataFrame:
    """Pure Python implementation of price shock."""
    return loans_df.with_columns([
        (pl.col('price_appreciation_rate') + appreciation_shift).clip(0.0, None).alias('price_appreciation_rate'),
    ])

def apply_zone_default_surge_py(loans_df: pl.DataFrame, zone: str, default_rate: float) -> pl.DataFrame:
    """Pure Python implementation of zone default surge."""
    # Generate random numbers for filtering
    np.random.seed(42)  # For reproducibility
    loan_count = len(loans_df)
    random_numbers = np.random.random(loan_count)
    
    loans_with_random = loans_df.with_row_index().with_columns([
        pl.Series('random', random_numbers)
    ])
    
    # Filter loans based on zone and random threshold
    result = loans_with_random.filter(
        (pl.col('zone') != zone) | 
        ((pl.col('zone') == zone) & (pl.col('random') > default_rate))
    ).drop(['index', 'random'])
    
    return result
