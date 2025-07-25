from pydantic import BaseModel, ValidationError
import polars as pl
from typing import List, Optional

class LoanRecord(BaseModel):
    loan_id: str
    amount: float
    interest_rate: float
    term_months: int
    zone: str
    origination_date: str
    price_appreciation_rate: float
    formalization_status: str
    rbi_rate_at_origination: float


def load_loans(csv_path: str) -> List[LoanRecord]:
    """Load and validate loan records from a CSV file using Polars and pydantic."""
    df = pl.read_csv(csv_path)
    records = []
    for row in df.iter_rows(named=True):
        try:
            record = LoanRecord(**row)
            records.append(record)
        except ValidationError as e:
            # Optionally log or print the error and row
            pass
    return records 