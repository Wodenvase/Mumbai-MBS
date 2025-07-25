from mbs.loader import LoanRecord

def psa_curve(month: int, psa_speed: float = 100.0) -> float:
    """Return the monthly prepayment rate as per the PSA standard (annualized, in %)."""
    # Standard PSA: 0.2% CPR in month 1, increasing by 0.2% per month until month 30, then flat
    base_cpr = min(0.002 * month, 0.06)  # 0.2% * month, max 6% annualized
    cpr = base_cpr * (psa_speed / 100.0)
    return cpr

def mumbai_psa_multiplier(loan: LoanRecord) -> float:
    """Return a multiplier for PSA based on Mumbai-specific factors."""
    # Price appreciation
    if loan.price_appreciation_rate > 0.08:
        price_mult = 2.0
    elif loan.price_appreciation_rate > 0.05:
        price_mult = 1.5
    else:
        price_mult = 1.0
    # Zone
    zone_map = {
        'South Mumbai': 1.5,
        'Mumbai Suburbs': 1.0,
        'Navi Mumbai': 0.5
    }
    zone_mult = zone_map.get(loan.zone, 1.0)
    # Formalization status
    formal_mult = 1.2 if loan.formalization_status == 'Formal' else 1.0
    return price_mult * zone_mult * formal_mult

def monthly_prepayment_rate(loan: LoanRecord, month: int) -> float:
    """Compute the monthly prepayment rate (CPR, annualized) for a given loan and month."""
    psa_speed = 100.0  # Could be parameterized or inferred from zone
    base_cpr = psa_curve(month, psa_speed)
    multiplier = mumbai_psa_multiplier(loan)
    return base_cpr * multiplier 