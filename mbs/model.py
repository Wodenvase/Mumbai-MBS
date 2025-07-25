from typing import List, Dict
from mbs.loader import LoanRecord
from mbs.prepayment import monthly_prepayment_rate
import numpy as np

def amortization_schedule(loan: LoanRecord) -> List[Dict]:
    """Generate monthly principal, interest, and prepayment payments for the loan."""
    schedule = []
    balance = loan.amount
    r = loan.interest_rate / 12 / 100
    n = loan.term_months
    if r == 0:
        payment = balance / n
    else:
        payment = balance * r * (1 + r) ** n / ((1 + r) ** n - 1)
    for month in range(1, n + 1):
        interest = balance * r
        principal = payment - interest
        # Prepayment calculation
        cpr = monthly_prepayment_rate(loan, month)  # annualized CPR
        smm = 1 - (1 - cpr) ** (1 / 12)  # Convert annual CPR to monthly SMM
        prepayment = (balance - principal) * smm
        total_principal = principal + prepayment
        balance -= total_principal
        schedule.append({
            'month': month,
            'payment': payment,
            'principal': principal,
            'interest': interest,
            'prepayment': prepayment,
            'total_principal': total_principal,
            'remaining_balance': max(balance, 0)
        })
        if balance <= 0:
            break
    return schedule

def aggregate_cash_flows(loans: List[LoanRecord]) -> List[Dict]:
    """Aggregate monthly cash flows for all loans (with prepayment)."""
    # Find the max possible term
    max_term = max(loan.term_months for loan in loans)
    monthly_flows = [{'month': m, 'total_principal': 0, 'total_interest': 0, 'total_prepayment': 0, 'total_payment': 0} for m in range(1, max_term + 1)]
    for loan in loans:
        schedule = amortization_schedule(loan)
        for entry in schedule:
            m = entry['month'] - 1
            monthly_flows[m]['total_principal'] += entry['principal']
            monthly_flows[m]['total_interest'] += entry['interest']
            monthly_flows[m]['total_prepayment'] += entry['prepayment']
            monthly_flows[m]['total_payment'] += entry['payment']
    return monthly_flows

def compute_mbs_metrics(cash_flows: List[Dict], discount_rate: float = 0.07) -> Dict:
    """Compute average life, Macaulay duration, and convexity for the MBS pool."""
    total_principal = 0
    pv_total = 0
    pv_weighted_time = 0
    pv_weighted_time2 = 0
    for row in cash_flows:
        t = row['month']
        principal = row['total_principal'] + row.get('total_prepayment', 0)
        total_principal += principal
        # Present value factor
        pv_factor = 1 / (1 + discount_rate / 12) ** t
        pv = principal * pv_factor
        pv_total += pv
        pv_weighted_time += t * pv
        pv_weighted_time2 += t * (t + 1) * pv
    if total_principal == 0 or pv_total == 0:
        return {'average_life': 0, 'duration': 0, 'convexity': 0}
    average_life = sum((row['month'] * (row['total_principal'] + row.get('total_prepayment', 0))) for row in cash_flows) / total_principal / 12
    duration = pv_weighted_time / pv_total / 12
    convexity = pv_weighted_time2 / (pv_total * (1 + discount_rate / 12) ** 2) / 12 ** 2
    return {
        'average_life': average_life,
        'duration': duration,
        'convexity': convexity
    } 