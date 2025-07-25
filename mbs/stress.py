from mbs.loader import LoanRecord
from typing import List
import copy

def apply_rbi_rate_shift(loans: List[LoanRecord], rate_shift: float) -> List[LoanRecord]:
    """Apply an RBI rate shift (in percentage points) to all loans' interest rates."""
    stressed_loans = []
    for loan in loans:
        new_loan = copy.deepcopy(loan)
        new_loan.interest_rate = max(0, loan.interest_rate + rate_shift)
        stressed_loans.append(new_loan)
    return stressed_loans

def apply_price_shock(loans: List[LoanRecord], appreciation_shift: float) -> List[LoanRecord]:
    """Apply a price appreciation shock (additive, e.g., -0.05 for -5%) to all loans."""
    stressed_loans = []
    for loan in loans:
        new_loan = copy.deepcopy(loan)
        new_loan.price_appreciation_rate = max(0, loan.price_appreciation_rate + appreciation_shift)
        stressed_loans.append(new_loan)
    return stressed_loans

def apply_zone_default_surge(loans: List[LoanRecord], zone: str, default_rate: float) -> List[LoanRecord]:
    """Simulate a default surge in a specific zone by removing a fraction of loans from that zone."""
    stressed_loans = []
    for loan in loans:
        if loan.zone == zone:
            # Remove a fraction of loans (simulate default)
            import random
            if random.random() > default_rate:
                stressed_loans.append(loan)
        else:
            stressed_loans.append(loan)
    return stressed_loans 